"""Watch environment variable chains for changes and emit events."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envchain.chain import EnvChain, resolve


@dataclass
class ChangeEvent:
    """Represents a detected change in an environment variable."""

    key: str
    old_value: Optional[str]
    new_value: Optional[str]

    @property
    def is_added(self) -> bool:
        return self.old_value is None and self.new_value is not None

    @property
    def is_removed(self) -> bool:
        return self.old_value is not None and self.new_value is None

    @property
    def is_modified(self) -> bool:
        return self.old_value is not None and self.new_value is not None

    def __repr__(self) -> str:
        if self.is_added:
            return f"ChangeEvent(key={self.key!r}, added={self.new_value!r})"
        if self.is_removed:
            return f"ChangeEvent(key={self.key!r}, removed={self.old_value!r})"
        return f"ChangeEvent(key={self.key!r}, {self.old_value!r} -> {self.new_value!r})"


class EnvWatcher:
    """Polls an EnvChain for value changes and dispatches callbacks."""

    def __init__(self, chain: EnvChain, interval: float = 1.0) -> None:
        self._chain = chain
        self._interval = interval
        self._snapshot: Dict[str, Optional[str]] = {}
        self._handlers: List[Callable[[List[ChangeEvent]], None]] = []
        self._running = False

    def on_change(self, handler: Callable[[List[ChangeEvent]], None]) -> None:
        """Register a callback invoked with a list of ChangeEvents."""
        self._handlers.append(handler)

    def _current_values(self) -> Dict[str, Optional[str]]:
        return {var.name: resolve(var) for var in self._chain._vars}

    def _detect_changes(self, current: Dict[str, Optional[str]]) -> List[ChangeEvent]:
        events: List[ChangeEvent] = []
        all_keys = set(self._snapshot) | set(current)
        for key in all_keys:
            old = self._snapshot.get(key)
            new = current.get(key)
            if old != new:
                events.append(ChangeEvent(key=key, old_value=old, new_value=new))
        return events

    def poll_once(self) -> List[ChangeEvent]:
        """Check for changes once and dispatch handlers. Returns detected events."""
        current = self._current_values()
        events = self._detect_changes(current)
        if events:
            for handler in self._handlers:
                handler(events)
        self._snapshot = current
        return events

    def start(self, iterations: Optional[int] = None) -> None:
        """Begin polling loop. If iterations is set, stops after N polls."""
        self._snapshot = self._current_values()
        self._running = True
        count = 0
        while self._running:
            time.sleep(self._interval)
            self.poll_once()
            count += 1
            if iterations is not None and count >= iterations:
                break

    def stop(self) -> None:
        """Signal the polling loop to stop."""
        self._running = False
