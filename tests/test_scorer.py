"""Tests for envchain.scorer."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.scorer import ScoreReport, score_chain, SCORE_KEYS


def _make_chain(profile="dev", **kwargs) -> EnvChain:
    chain = EnvChain(profile=profile)
    for name, value in kwargs.items():
        chain.add(EnvVar(name=name, value=value))
    return chain


class TestScoreReport:
    def test_repr_contains_profile(self):
        r = ScoreReport(profile="dev", total=2, resolved=2, defaulted=0, empty=0,
                        scores={"completeness": 1.0})
        assert "dev" in repr(r)

    def test_overall_averages_scores(self):
        r = ScoreReport(profile="dev", total=2, resolved=2, defaulted=0, empty=0,
                        scores={"completeness": 1.0, "defaults_ratio": 0.5, "non_empty_ratio": 0.75})
        assert r.overall == round((1.0 + 0.5 + 0.75) / 3, 4)

    def test_overall_empty_scores_returns_zero(self):
        r = ScoreReport(profile="dev", total=0, resolved=0, defaulted=0, empty=0)
        assert r.overall == 0.0


class TestScoreChain:
    def test_empty_chain_returns_zero_scores(self):
        chain = EnvChain(profile="dev")
        report = score_chain(chain)
        assert report.total == 0
        assert report.overall == 0.0
        for k in SCORE_KEYS:
            assert report.scores[k] == 0.0

    def test_all_resolved_no_defaults_no_empty(self):
        chain = _make_chain(dev="1", DB="postgres", SECRET="abc")
        report = score_chain(chain)
        assert report.total == 3
        assert report.resolved == 3
        assert report.empty == 0
        assert report.scores["completeness"] == 1.0

    def test_missing_values_lower_completeness(self):
        chain = EnvChain(profile="dev")
        chain.add(EnvVar(name="PRESENT", value="yes"))
        chain.add(EnvVar(name="MISSING", value=None))
        report = score_chain(chain)
        assert report.resolved == 1
        assert report.scores["completeness"] == 0.5

    def test_empty_string_values_counted(self):
        chain = _make_chain(BLANK="", FILLED="ok")
        report = score_chain(chain)
        assert report.empty == 1
        assert report.scores["non_empty_ratio"] < 1.0

    def test_defaulted_lowers_defaults_ratio(self):
        chain = EnvChain(profile="staging")
        chain.add(EnvVar(name="X", value="fallback", default="fallback"))
        chain.add(EnvVar(name="Y", value="real", default=None))
        report = score_chain(chain)
        assert report.defaulted == 1
        assert report.scores["defaults_ratio"] < 1.0

    def test_profile_preserved_in_report(self):
        chain = _make_chain(profile="prod", KEY="val")
        report = score_chain(chain)
        assert report.profile == "prod"

    def test_score_keys_all_present(self):
        chain = _make_chain(A="1", B="2")
        report = score_chain(chain)
        for k in SCORE_KEYS:
            assert k in report.scores
