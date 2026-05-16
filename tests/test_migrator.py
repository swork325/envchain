"""Tests for envchain.migrator."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.migrator import MigrationResult, migrate_chain


def _make_chain(profile: str, **kwargs) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in kwargs.items():
        chain.add(EnvVar(key=key, value=value))
    return chain


# ---------------------------------------------------------------------------
# TestMigrationResult
# ---------------------------------------------------------------------------

class TestMigrationResult:
    def test_repr_contains_profiles(self):
        r = MigrationResult(source_profile="dev", target_profile="staging")
        assert "dev" in repr(r)
        assert "staging" in repr(r)

    def test_repr_shows_counts(self):
        r = MigrationResult(
            source_profile="dev",
            target_profile="staging",
            added=["NEW_KEY"],
            renamed={"OLD": "NEW"},
            dropped=["GONE"],
        )
        assert "added=1" in repr(r)
        assert "renamed=1" in repr(r)
        assert "dropped=1" in repr(r)

    def test_is_clean_when_no_changes(self):
        r = MigrationResult(source_profile="dev", target_profile="staging")
        assert r.is_clean() is True

    def test_not_clean_when_renamed(self):
        r = MigrationResult(
            source_profile="dev", target_profile="staging", renamed={"A": "B"}
        )
        assert r.is_clean() is False

    def test_not_clean_when_dropped(self):
        r = MigrationResult(
            source_profile="dev", target_profile="staging", dropped=["X"]
        )
        assert r.is_clean() is False

    def test_not_clean_when_added(self):
        r = MigrationResult(
            source_profile="dev", target_profile="staging", added=["Y"]
        )
        assert r.is_clean() is False


# ---------------------------------------------------------------------------
# TestMigrateChain
# ---------------------------------------------------------------------------

class TestMigrateChain:
    def test_target_profile_applied(self):
        chain = _make_chain("dev", DB_URL="sqlite://")
        result = migrate_chain(chain, "staging")
        assert result.chain.profile == "staging"

    def test_source_profile_preserved_in_result(self):
        chain = _make_chain("dev", KEY="val")
        result = migrate_chain(chain, "staging")
        assert result.source_profile == "dev"

    def test_all_keys_carried_over_by_default(self):
        chain = _make_chain("dev", A="1", B="2")
        result = migrate_chain(chain, "staging")
        keys = [v.key for v in result.chain._vars]
        assert sorted(keys) == ["A", "B"]

    def test_rename_changes_key(self):
        chain = _make_chain("dev", OLD_KEY="hello")
        result = migrate_chain(chain, "staging", rename={"OLD_KEY": "NEW_KEY"})
        keys = [v.key for v in result.chain._vars]
        assert "NEW_KEY" in keys
        assert "OLD_KEY" not in keys
        assert result.renamed == {"OLD_KEY": "NEW_KEY"}

    def test_drop_removes_key(self):
        chain = _make_chain("dev", KEEP="yes", REMOVE="no")
        result = migrate_chain(chain, "staging", drop=["REMOVE"])
        keys = [v.key for v in result.chain._vars]
        assert "REMOVE" not in keys
        assert "KEEP" in keys
        assert "REMOVE" in result.dropped

    def test_add_injects_new_key(self):
        chain = _make_chain("dev", EXISTING="v")
        result = migrate_chain(chain, "staging", add={"INJECTED": "new_val"})
        keys = [v.key for v in result.chain._vars]
        assert "INJECTED" in keys
        assert "INJECTED" in result.added

    def test_transform_applied_to_values(self):
        chain = _make_chain("dev", HOST="localhost")
        result = migrate_chain(
            chain, "prod", transform=lambda k, v: v.upper() if v else v
        )
        vals = {v.key: v.value for v in result.chain._vars}
        assert vals["HOST"] == "LOCALHOST"

    def test_is_clean_for_plain_migration(self):
        chain = _make_chain("dev", X="1")
        result = migrate_chain(chain, "staging")
        assert result.is_clean() is True

    def test_combined_rename_drop_add(self):
        chain = _make_chain("dev", OLD="v", GONE="x", STAY="s")
        result = migrate_chain(
            chain,
            "prod",
            rename={"OLD": "NEW"},
            drop=["GONE"],
            add={"EXTRA": "e"},
        )
        keys = [v.key for v in result.chain._vars]
        assert "NEW" in keys
        assert "STAY" in keys
        assert "EXTRA" in keys
        assert "OLD" not in keys
        assert "GONE" not in keys
