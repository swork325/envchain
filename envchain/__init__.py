"""envchain — Lightweight environment variable chain management."""

from envchain.auditor import EnvAuditor
from envchain.chain import EnvChain, EnvVar
from envchain.differ import diff_chains
from envchain.exporter import export_chain
from envchain.loader import load_profile_env
from envchain.merger import ConflictStrategy, merge_chains
from envchain.profiles import EnvProfile, ProfileRegistry
from envchain.snapshot import (
    Snapshot,
    capture,
    load_snapshot,
    restore_to_env,
    save_snapshot,
)
from envchain.validator import ValidationReport, ValidationResult

__all__ = [
    "EnvVar",
    "EnvChain",
    "EnvProfile",
    "ProfileRegistry",
    "ValidationResult",
    "ValidationReport",
    "EnvAuditor",
    "export_chain",
    "load_profile_env",
    "diff_chains",
    "merge_chains",
    "ConflictStrategy",
    "Snapshot",
    "capture",
    "save_snapshot",
    "load_snapshot",
    "restore_to_env",
]
