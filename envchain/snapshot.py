"""Snapshot support: capture and restore EnvChain states."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class Snapshot:
    """An immutable record of an EnvChain's resolved values at a point in time."""

    profile: str
    captured_at: str
    values: Dict[str, Optional[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "captured_at": self.captured_at,
            "values": self.values,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            profile=data["profile"],
            captured_at=data["captured_at"],
            values=data.get("values", {}),
        )

    def __repr__(self) -> str:
        return (
            f"Snapshot(profile={self.profile!r}, "
            f"captured_at={self.captured_at!r}, "
            f"keys={list(self.values.keys())})"
        )


def capture(chain: EnvChain, profile: str = "default") -> Snapshot:
    """Capture the current resolved state of an EnvChain."""
    values: Dict[str, Optional[str]] = {}
    for var in chain._vars:  # noqa: SLF001
        values[var.name] = var.resolve()
    captured_at = datetime.now(tz=timezone.utc).isoformat()
    return Snapshot(profile=profile, captured_at=captured_at, values=values)


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load_snapshot(path: str) -> Snapshot:
    """Load a snapshot from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Snapshot.from_dict(data)


def restore_to_env(snapshot: Snapshot) -> None:
    """Restore snapshot values into the current process environment."""
    for key, value in snapshot.values.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)
