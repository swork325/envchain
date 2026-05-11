"""Integration tests: scorer + cli_score working end-to-end."""

import io
import json
import tempfile
from pathlib import Path

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.scorer import score_chain
from envchain.cli_score import build_parser, run_score


def _make_chain(profile="dev", **kwargs) -> EnvChain:
    chain = EnvChain(profile=profile)
    for name, value in kwargs.items():
        chain.add(EnvVar(name=name, value=value))
    return chain


class TestScorerCliIntegration:
    def test_full_chain_scores_1_overall(self):
        chain = _make_chain(A="x", B="y", C="z")
        report = score_chain(chain)
        assert report.overall == pytest.approx(1.0, abs=0.01)

    def test_partial_chain_overall_below_1(self):
        chain = EnvChain(profile="staging")
        chain.add(EnvVar(name="PRESENT", value="yes"))
        chain.add(EnvVar(name="ABSENT", value=None))
        report = score_chain(chain)
        assert report.overall < 1.0

    def test_cli_json_matches_scorer_output(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=val1\nKEY2=val2\n")
        parser = build_parser()
        args = parser.parse_args([str(env_file), "--format", "json", "--profile", "dev"])
        out = io.StringIO()
        run_score(args, out=out)
        data = json.loads(out.getvalue())
        assert data["resolved"] == data["total"]
        assert data["overall"] > 0.0

    def test_empty_env_file_gives_zero_overall_via_cli(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("")
        parser = build_parser()
        args = parser.parse_args([str(env_file), "--format", "json"])
        out = io.StringIO()
        run_score(args, out=out)
        data = json.loads(out.getvalue())
        assert data["overall"] == 0.0
        assert data["total"] == 0
