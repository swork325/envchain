"""Validation rules and result types for EnvChain variables."""

from dataclasses import dataclass, field
from typing import Callable, List, Optional
import re


@dataclass
class ValidationResult:
    """Holds the outcome of a single validation check."""

    key: str
    passed: bool
    message: Optional[str] = None

    def __repr__(self) -> str:
        status = "OK" if self.passed else "FAIL"
        detail = f": {self.message}" if self.message else ""
        return f"ValidationResult({self.key} [{status}]{detail})"


@dataclass
class ValidationReport:
    """Aggregates multiple ValidationResult objects."""

    results: List[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failures(self) -> List[ValidationResult]:
        return [r for r in self.results if not r.passed]

    def summary(self) -> str:
        total = len(self.results)
        failed = len(self.failures)
        if self.passed:
            return f"All {total} checks passed."
        lines = [f"{failed}/{total} checks failed:"]
        for f_ in self.failures:
            lines.append(f"  - {f_.key}: {f_.message}")
        return "\n".join(lines)


Rule = Callable[[Optional[str]], Optional[str]]


def required() -> Rule:
    """Fails if the value is None or empty."""
    def _rule(value: Optional[str]) -> Optional[str]:
        if not value:
            return "value is required but missing or empty"
        return None
    return _rule


def min_length(n: int) -> Rule:
    """Fails if the value is shorter than *n* characters."""
    def _rule(value: Optional[str]) -> Optional[str]:
        if value is not None and len(value) < n:
            return f"value must be at least {n} characters long"
        return None
    return _rule


def matches_prefix(prefix: str) -> Rule:
    """Fails if the value does not start with *prefix*."""
    def _rule(value: Optional[str]) -> Optional[str]:
        if value is not None and not value.startswith(prefix):
            return f"value must start with '{prefix}'"
        return None
    return _rule


def matches_pattern(pattern: str) -> Rule:
    """Fails if the value does not match the given regular expression *pattern*.

    The pattern is matched against the full value using ``re.fullmatch``.
    Values of ``None`` are silently skipped (combine with :func:`required`
    if the value must be present).
    """
    compiled = re.compile(pattern)

    def _rule(value: Optional[str]) -> Optional[str]:
        if value is not None and not compiled.fullmatch(value):
            return f"value does not match pattern '{pattern}'"
        return None

    return _rule
