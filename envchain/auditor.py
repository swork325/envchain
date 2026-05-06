"""Auditor: apply validation rules to an EnvChain and produce a report."""

from typing import Dict, List, Optional

from envchain.chain import EnvChain
from envchain.validator import Rule, ValidationReport, ValidationResult


class EnvAuditor:
    """Applies per-key rules to an EnvChain and collects results."""

    def __init__(self, chain: EnvChain) -> None:
        self._chain = chain
        self._rules: Dict[str, List[Rule]] = {}

    def add_rule(self, key: str, *rules: Rule) -> "EnvAuditor":
        """Register one or more rules for *key*. Returns self for chaining."""
        self._rules.setdefault(key, []).extend(rules)
        return self

    def audit(self) -> ValidationReport:
        """Run all registered rules and return a ValidationReport."""
        report = ValidationReport()
        for key, rules in self._rules.items():
            value: Optional[str] = self._chain.get(key)
            messages = [msg for rule in rules if (msg := rule(value)) is not None]
            if messages:
                report.results.append(
                    ValidationResult(key=key, passed=False, message="; ".join(messages))
                )
            else:
                report.results.append(ValidationResult(key=key, passed=True))
        return report

    def audit_or_raise(self) -> None:
        """Run audit and raise ValueError if any checks fail."""
        report = self.audit()
        if not report.passed:
            raise ValueError(f"EnvAuditor found issues:\n{report.summary()}")
