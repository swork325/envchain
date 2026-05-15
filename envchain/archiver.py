"""Archive and restore EnvChain snapshots to/from compressed JSON files."""

from __future__ import annotations

import gzip
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from envchain.chain import EnvChain
from envchain.snapshot import Snapshot, capture


@dataclass
class ArchiveEntry:
    timestamp: str
    profile: str
    snapshot: Snapshot

    def __repr__(self) -> str:  # pragma: no cover
        return f"ArchiveEntry(profile={self.profile!r}, timestamp={self.timestamp!r})"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "profile": self.profile,
            "snapshot": self.snapshot.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArchiveEntry":
        snap = Snapshot.from_dict(data["snapshot"])
        return cls(
            timestamp=data["timestamp"],
            profile=data["profile"],
            snapshot=snap,
        )


@dataclass
class Archive:
    path: str
    entries: List[ArchiveEntry] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Archive(path={self.path!r}, entries={len(self.entries)})"

    def add(self, chain: EnvChain, profile: str = "default") -> ArchiveEntry:
        ts = datetime.now(timezone.utc).isoformat()
        snap = capture(chain, profile=profile)
        entry = ArchiveEntry(timestamp=ts, profile=profile, snapshot=snap)
        self.entries.append(entry)
        return entry

    def save(self) -> None:
        data = {"entries": [e.to_dict() for e in self.entries]}
        payload = json.dumps(data, indent=2).encode()
        with gzip.open(self.path, "wb") as fh:
            fh.write(payload)

    @classmethod
    def load(cls, path: str) -> "Archive":
        with gzip.open(path, "rb") as fh:
            data = json.loads(fh.read())
        entries = [ArchiveEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(path=path, entries=entries)

    def latest(self, profile: Optional[str] = None) -> Optional[ArchiveEntry]:
        candidates = self.entries
        if profile is not None:
            candidates = [e for e in candidates if e.profile == profile]
        return candidates[-1] if candidates else None
