"""Redact sensitive environment variable values based on key patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envchain.chain import EnvChain, EnvVar

_DEFAULT_PATTERNS: List[str] = [
    r"(?i)password",
    r"(?i)secret",
    r"(?i)token",
    r"(?i)api[_]?key",
    r"(?i)private[_]?key",
    r"(?i)auth",
    r"(?i)credential",
]

REDACTED_PLACEHOLDER = "***REDACTED***"


@dataclass
class RedactedVar:
    key: str
    original: Optional[str]
    redacted: bool

    @property
    def display_value(self) -> Optional[str]:
        return REDACTED_PLACEHOLDER if self.redacted else self.original

    def __repr__(self) -> str:  # pragma: no cover
        status = "redacted" if self.redacted else "plain"
        return f"RedactedVar(key={self.key!r}, status={status})"


@dataclass
class RedactReport:
    profile: str
    vars: List[RedactedVar] = field(default_factory=list)

    @property
    def redacted_keys(self) -> List[str]:
        return [v.key for v in self.vars if v.redacted]

    @property
    def plain_keys(self) -> List[str]:
        return [v.key for v in self.vars if not v.redacted]

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RedactReport(profile={self.profile!r}, "
            f"redacted={len(self.redacted_keys)}, plain={len(self.plain_keys)})"
        )


def redact_chain(
    chain: EnvChain,
    patterns: Optional[List[str]] = None,
) -> RedactReport:
    """Return a RedactReport marking sensitive vars as redacted."""
    compiled = [
        re.compile(p) for p in (patterns if patterns is not None else _DEFAULT_PATTERNS)
    ]

    report = RedactReport(profile=chain.profile)
    for var in chain.vars:
        is_sensitive = any(rx.search(var.key) for rx in compiled)
        report.vars.append(
            RedactedVar(key=var.key, original=var.resolve(), redacted=is_sensitive)
        )
    return report
