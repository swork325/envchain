"""Migrate env chains between profiles by mapping, renaming, or dropping keys."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class MigrationResult:
    source_profile: str
    target_profile: str
    added: List[str] = field(default_factory=list)
    renamed: Dict[str, str] = field(default_factory=dict)  # old_key -> new_key
    dropped: List[str] = field(default_factory=list)
    chain: Optional[EnvChain] = None

    def __repr__(self) -> str:
        return (
            f"MigrationResult(source={self.source_profile!r}, "
            f"target={self.target_profile!r}, "
            f"added={len(self.added)}, "
            f"renamed={len(self.renamed)}, "
            f"dropped={len(self.dropped)})"
        )

    def is_clean(self) -> bool:
        """Return True if no structural changes were made."""
        return not self.added and not self.renamed and not self.dropped


def migrate_chain(
    chain: EnvChain,
    target_profile: str,
    *,
    rename: Optional[Dict[str, str]] = None,
    drop: Optional[List[str]] = None,
    add: Optional[Dict[str, Optional[str]]] = None,
    transform: Optional[Callable[[str, Optional[str]], Optional[str]]] = None,
) -> MigrationResult:
    """Produce a new EnvChain migrated to *target_profile*.

    Args:
        chain: Source EnvChain.
        target_profile: Profile name for the resulting chain.
        rename: Mapping of {old_key: new_key} to apply.
        drop: Keys to exclude from the result.
        add: Keys to inject with the given values.
        transform: Optional callable(key, value) -> value applied to every
            retained variable *after* renaming.

    Returns:
        A MigrationResult containing the new chain and a change summary.
    """
    rename = rename or {}
    drop_set = set(drop or [])
    add = add or {}

    result_added: List[str] = []
    result_renamed: Dict[str, str] = {}
    result_dropped: List[str] = []
    new_vars: List[EnvVar] = []

    for var in chain._vars:  # type: ignore[attr-defined]
        if var.key in drop_set:
            result_dropped.append(var.key)
            continue
        new_key = rename.get(var.key, var.key)
        if new_key != var.key:
            result_renamed[var.key] = new_key
        value = var.value
        if transform is not None:
            value = transform(new_key, value)
        new_vars.append(EnvVar(key=new_key, value=value, default=var.default))

    for key, value in add.items():
        new_vars.append(EnvVar(key=key, value=value))
        result_added.append(key)

    new_chain = EnvChain(profile=target_profile)
    for v in new_vars:
        new_chain.add(v)

    return MigrationResult(
        source_profile=chain.profile,
        target_profile=target_profile,
        added=result_added,
        renamed=result_renamed,
        dropped=result_dropped,
        chain=new_chain,
    )
