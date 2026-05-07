"""Filtering utilities for EnvWatcher change events."""

from __future__ import annotations

from typing import Callable, List, Optional, Sequence

from envchain.watcher import ChangeEvent

EventFilter = Callable[[List[ChangeEvent]], List[ChangeEvent]]


def key_filter(keys: Sequence[str]) -> EventFilter:
    """Return only events whose key is in the provided list."""
    key_set = set(keys)

    def _filter(events: List[ChangeEvent]) -> List[ChangeEvent]:
        return [e for e in events if e.key in key_set]

    return _filter


def prefix_filter(prefix: str) -> EventFilter:
    """Return only events whose key starts with the given prefix."""

    def _filter(events: List[ChangeEvent]) -> List[ChangeEvent]:
        return [e for e in events if e.key.startswith(prefix)]

    return _filter


def kind_filter(added: bool = True, removed: bool = True, modified: bool = True) -> EventFilter:
    """Return only events matching the requested change kinds."""

    def _filter(events: List[ChangeEvent]) -> List[ChangeEvent]:
        result = []
        for e in events:
            if e.is_added and added:
                result.append(e)
            elif e.is_removed and removed:
                result.append(e)
            elif e.is_modified and modified:
                result.append(e)
        return result

    return _filter


def compose_filters(*filters: EventFilter) -> EventFilter:
    """Chain multiple filters — each receives the output of the previous."""

    def _filter(events: List[ChangeEvent]) -> List[ChangeEvent]:
        result = events
        for f in filters:
            result = f(result)
        return result

    return _filter


def filtered_handler(
    handler: Callable[[List[ChangeEvent]], None],
    *filters: EventFilter,
) -> Callable[[List[ChangeEvent]], None]:
    """Wrap a handler so it only receives events passing all filters."""
    combined = compose_filters(*filters)

    def _wrapped(events: List[ChangeEvent]) -> None:
        filtered = combined(events)
        if filtered:
            handler(filtered)

    return _wrapped
