"""Schedule periodic validation or audit runs against an EnvChain."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from envchain.chain import EnvChain


@dataclass
class ScheduleEntry:
    name: str
    interval: float  # seconds
    callback: Callable[[EnvChain], None]
    _last_run: float = field(default=0.0, repr=False)

    def is_due(self, now: float) -> bool:
        return (now - self._last_run) >= self.interval

    def mark_ran(self, now: float) -> None:
        self._last_run = now

    def __repr__(self) -> str:
        return f"ScheduleEntry(name={self.name!r}, interval={self.interval}s)"


class EnvScheduler:
    """Run registered callbacks against a chain on a fixed interval."""

    def __init__(self, chain: EnvChain, tick: float = 1.0) -> None:
        self._chain = chain
        self._tick = tick
        self._entries: List[ScheduleEntry] = []
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def add(self, name: str, interval: float, callback: Callable[[EnvChain], None]) -> None:
        self._entries.append(ScheduleEntry(name=name, interval=interval, callback=callback))

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Scheduler is already running")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            now = time.monotonic()
            for entry in self._entries:
                if entry.is_due(now):
                    try:
                        entry.callback(self._chain)
                    except Exception:  # noqa: BLE001
                        pass
                    entry.mark_ran(now)
            self._stop_event.wait(timeout=self._tick)

    @property
    def entries(self) -> List[ScheduleEntry]:
        return list(self._entries)
