"""Pin environment variable values to a named snapshot for drift detection."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.chain import EnvChain


@dataclass
class PinEntry:
    key: str
    pinned_value: Optional[str]
    current_value: Optional[str]

    @property
    def is_drifted(self) -> bool:
        return self.pinned_value != self.current_value

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PinEntry(key={self.key!r}, pinned={self.pinned_value!r}, "
            f"current={self.current_value!r}, drifted={self.is_drifted})"
        )


@dataclass
class PinReport:
    profile: str
    entries: List[PinEntry] = field(default_factory=list)

    @property
    def drifted(self) -> List[PinEntry]:
        return [e for e in self.entries if e.is_drifted]

    @property
    def stable(self) -> List[PinEntry]:
        return [e for e in self.entries if not e.is_drifted]

    @property
    def passed(self) -> bool:
        return len(self.drifted) == 0

    def __repr__(self) -> str:  # pragma: no cover
        status = "OK" if self.passed else f"{len(self.drifted)} drifted"
        return f"PinReport(profile={self.profile!r}, status={status!r})"


def pin_chain(chain: EnvChain) -> Dict[str, Optional[str]]:
    """Capture the current resolved values of all vars in *chain* as a pin dict."""
    return {var.key: var.resolve() for var in chain._vars}


def check_pins(
    chain: EnvChain,
    pins: Dict[str, Optional[str]],
    profile: str = "default",
) -> PinReport:
    """Compare *chain*'s current values against previously captured *pins*."""
    entries: List[PinEntry] = []
    all_keys = {var.key for var in chain._vars} | set(pins.keys())
    current: Dict[str, Optional[str]] = {var.key: var.resolve() for var in chain._vars}

    for key in sorted(all_keys):
        entries.append(
            PinEntry(
                key=key,
                pinned_value=pins.get(key),
                current_value=current.get(key),
            )
        )
    return PinReport(profile=profile, entries=entries)


def pins_to_json(pins: Dict[str, Optional[str]]) -> str:
    return json.dumps(pins, indent=2, sort_keys=True)


def pins_from_json(raw: str) -> Dict[str, Optional[str]]:
    return json.loads(raw)
