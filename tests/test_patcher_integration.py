"""Integration tests: patcher + exporter round-trip."""

from __future__ import annotations

import json

from envchain.chain import EnvChain, EnvVar
from envchain.exporter import export_chain
from envchain.patcher import patch_chain


def _make_chain(**kv: str) -> EnvChain:
    chain = EnvChain(profile="dev")
    for key, value in kv.items():
        chain.add(EnvVar(key=key, value=value))
    return chain


class TestPatcherExporterIntegration:
    def test_patched_dotenv_contains_new_value(self):
        chain = _make_chain(DB_HOST="localhost", DB_PORT="5432")
        patched, _ = patch_chain(chain, overrides={"DB_HOST": "prod.db"})
        output = export_chain(patched, fmt="dotenv")
        assert "DB_HOST=prod.db" in output
        assert "DB_PORT=5432" in output

    def test_patched_json_missing_removed_key(self):
        chain = _make_chain(SECRET="abc", SAFE="xyz")
        patched, _ = patch_chain(chain, removals=["SECRET"])
        output = export_chain(patched, fmt="json")
        data = json.loads(output)
        assert "SECRET" not in data
        assert data.get("SAFE") == "xyz"

    def test_patch_result_counts_match_chain_delta(self):
        chain = _make_chain(A="1", B="2", C="3")
        patched, result = patch_chain(
            chain,
            overrides={"A": "10", "D": "new"},
            removals=["C"],
        )
        patched_keys = [v.key for v in patched._vars]
        assert len(result.updated) == 1
        assert len(result.added) == 1
        assert len(result.removed) == 1
        assert "C" not in patched_keys
        assert "D" in patched_keys

    def test_empty_patch_preserves_all_keys(self):
        chain = _make_chain(X="1", Y="2")
        patched, result = patch_chain(chain)
        assert result.is_empty
        assert [v.key for v in patched._vars] == ["X", "Y"]
