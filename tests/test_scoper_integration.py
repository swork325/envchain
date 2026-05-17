"""Integration tests: scoper + exporter round-trip."""

from __future__ import annotations

import json

from envchain.chain import EnvChain, EnvVar
from envchain.exporter import export_chain
from envchain.scoper import scope_chain


def _make_chain(profile: str = "dev", **vars_: str | None) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in vars_.items():
        chain.add(EnvVar(key=key, default=value))
    return chain


class TestScopeExporterIntegration:
    def test_scoped_dotenv_contains_only_scoped_keys(self):
        chain = _make_chain(
            DB_HOST="localhost",
            DB_PORT="5432",
            REDIS_URL="redis://localhost",
            APP_ENV="dev",
        )
        scoped, _ = scope_chain(chain, "DB")
        dotenv = export_chain(scoped, fmt="dotenv")
        assert "DB_HOST" in dotenv
        assert "DB_PORT" in dotenv
        assert "REDIS_URL" not in dotenv
        assert "APP_ENV" not in dotenv

    def test_scoped_json_is_valid_and_contains_expected_keys(self):
        chain = _make_chain(DB_HOST="localhost", DB_PORT="5432", APP_ENV="dev")
        scoped, _ = scope_chain(chain, "DB")
        raw = export_chain(scoped, fmt="json")
        data = json.loads(raw)
        assert set(data.keys()) == {"DB_HOST", "DB_PORT"}

    def test_strip_prefix_then_export_has_short_keys(self):
        chain = _make_chain(DB_HOST="localhost", DB_PORT="5432")
        scoped, _ = scope_chain(chain, "DB", strip_prefix=True)
        raw = export_chain(scoped, fmt="json")
        data = json.loads(raw)
        assert "HOST" in data
        assert "PORT" in data
        assert "DB_HOST" not in data

    def test_scope_result_counts_match_chain(self):
        chain = _make_chain(
            DB_HOST="h", DB_PORT="p", APP_NAME="n", APP_ENV="e", REDIS_URL="r"
        )
        scoped, result = scope_chain(chain, "APP")
        assert len(result.included) == len(scoped._vars)
        assert len(result.included) + len(result.excluded) == len(chain._vars)
