"""Lint environment variable chains for common issues and style violations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envchain.chain import EnvChain


@dataclass
class LintViolation:
    key: str
    code: str
    message: str

    def __repr__(self) -> str:
        return f"LintViolation({self.key!r}, {self.code!r}: {self.message})"


@dataclass
class LintReport:
    profile: str
    violations: List[LintViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def __repr__(self) -> str:
        status = "PASS" if self.passed else f"{len(self.violations)} violation(s)"
        return f"LintReport(profile={self.profile!r}, status={status})"


def lint_chain(chain: EnvChain) -> LintReport:
    """Run all lint rules against *chain* and return a LintReport."""
    report = LintReport(profile=chain.profile.name)

    for var in chain._vars.values():
        value = var.resolve()

        # E001 — key must be uppercase
        if var.key != var.key.upper():
            report.violations.append(
                LintViolation(var.key, "E001", "Key should be uppercase")
            )

        # E002 — key must not contain spaces
        if " " in var.key:
            report.violations.append(
                LintViolation(var.key, "E002", "Key must not contain spaces")
            )

        # W001 — resolved value is an empty string
        if value is not None and value.strip() == "":
            report.violations.append(
                LintViolation(var.key, "W001", "Resolved value is blank")
            )

        # W002 — default value looks like an unset placeholder
        if var.default is not None and var.default.lower() in (
            "changeme",
            "todo",
            "fixme",
            "<your_value>",
            "your_value_here",
        ):
            report.violations.append(
                LintViolation(var.key, "W002", f"Default looks like a placeholder: {var.default!r}")
            )

    return report
