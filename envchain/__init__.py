"""envchain — public API surface."""

from envchain.chain import EnvChain, EnvVar
from envchain.profiles import EnvProfile, ProfileRegistry
from envchain.loader import load_profile_env
from envchain.validator import (
    ValidationReport,
    ValidationResult,
    Rule,
    required,
    min_length,
    matches_prefix,
)
from envchain.auditor import EnvAuditor

__all__ = [
    # chain
    "EnvChain",
    "EnvVar",
    # profiles
    "EnvProfile",
    "ProfileRegistry",
    # loader
    "load_profile_env",
    # validator
    "ValidationReport",
    "ValidationResult",
    "Rule",
    "required",
    "min_length",
    "matches_prefix",
    # auditor
    "EnvAuditor",
]
