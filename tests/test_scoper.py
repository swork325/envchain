"""Tests for envchain.scoper."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.scoper import ScopeResult, scope_chain


def _make_chain(profile: str = "dev", **vars_: str | None) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in vars_.items():
        chain.add(EnvVar(key=key, default=value))
    return chain


# ---------------------------------------------------------------------------
# ScopeResult
# ---------------------------------------------------------------------------

class TestScopeResult:
    def test_is_empty_when_no_included(self):
        r = ScopeResult(profile="dev", scope="DB", included=[], excluded=[])
        assert r.is_empty is True

    def test_not_empty_when_included(self):
        var = EnvVar(key="DB_HOST", default="localhost")
        r = ScopeResult(profile="dev", scope="DB", included=[var], excluded=[])
        assert r.is_empty is False

    def test_repr_contains_scope(self):
        r = ScopeResult(profile="dev", scope="DB", included=[], excluded=[])
        assert "DB" in repr(r)


# ---------------------------------------------------------------------------
# scope_chain
# ---------------------------------------------------------------------------

class TestScopeChain:
    def test_includes_matching_prefix(self):
        chain = _make_chain(DB_HOST="localhost", DB_PORT="5432", APP_NAME="myapp")
        scoped, result = scope_chain(chain, "DB")
        assert {v.key for v in result.included} == {"DB_HOST", "DB_PORT"}

    def test_excludes_non_matching(self):
        chain = _make_chain(DB_HOST="localhost", APP_NAME="myapp")
        _, result = scope_chain(chain, "DB")
        assert {v.key for v in result.excluded} == {"APP_NAME"}

    def test_scoped_chain_contains_only_matching(self):
        chain = _make_chain(DB_HOST="localhost", DB_PORT="5432", APP_NAME="myapp")
        scoped, _ = scope_chain(chain, "DB")
        assert set(scoped._vars.keys()) == {"DB_HOST", "DB_PORT"}

    def test_strip_prefix_renames_keys(self):
        chain = _make_chain(DB_HOST="localhost", DB_PORT="5432")
        scoped, result = scope_chain(chain, "DB", strip_prefix=True)
        assert set(scoped._vars.keys()) == {"HOST", "PORT"}

    def test_strip_prefix_result_included_keys(self):
        chain = _make_chain(DB_HOST="localhost", DB_PORT="5432")
        _, result = scope_chain(chain, "DB", strip_prefix=True)
        assert {v.key for v in result.included} == {"HOST", "PORT"}

    def test_case_insensitive_scope_match(self):
        chain = _make_chain(DB_HOST="localhost", db_port="5432", APP_NAME="x")
        _, result = scope_chain(chain, "db")
        assert {v.key.upper() for v in result.included} == {"DB_HOST", "DB_PORT"}

    def test_empty_chain_returns_empty_scope(self):
        chain = EnvChain(profile="dev")
        scoped, result = scope_chain(chain, "DB")
        assert result.is_empty
        assert len(scoped._vars) == 0

    def test_profile_preserved(self):
        chain = _make_chain(profile="prod", DB_HOST="h")
        scoped, result = scope_chain(chain, "DB")
        assert scoped.profile == "prod"
        assert result.profile == "prod"

    def test_custom_separator(self):
        chain = _make_chain(**{"DB.HOST": "localhost", "APP.NAME": "x"})
        scoped, result = scope_chain(chain, "DB", separator=".")
        assert {v.key for v in result.included} == {"DB.HOST"}
