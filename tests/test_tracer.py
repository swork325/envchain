"""Tests for envchain.tracer."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.tracer import TraceReport, TraceStep, trace_all, trace_key


def _make_chain(profile: str, **kwargs) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in kwargs.items():
        chain.add(EnvVar(key=key, default=value))
    return chain


class TestTraceStep:
    def test_repr_contains_key_and_source(self):
        step = TraceStep(profile="dev", key="FOO", value="bar", source="env")
        r = repr(step)
        assert "FOO" in r
        assert "env" in r
        assert "dev" in r


class TestTraceReport:
    def test_resolved_in_returns_matching_profiles(self):
        report = TraceReport(key="FOO", steps=[
            TraceStep(profile="dev", key="FOO", value="x", source="env"),
            TraceStep(profile="staging", key="FOO", value=None, source="missing"),
            TraceStep(profile="prod", key="FOO", value="y", source="default"),
        ])
        assert report.resolved_in() == ["dev", "prod"]

    def test_first_resolved_returns_first_non_missing(self):
        report = TraceReport(key="FOO", steps=[
            TraceStep(profile="dev", key="FOO", value=None, source="missing"),
            TraceStep(profile="staging", key="FOO", value="hello", source="env"),
        ])
        first = report.first_resolved()
        assert first is not None
        assert first.profile == "staging"

    def test_first_resolved_returns_none_when_all_missing(self):
        report = TraceReport(key="BAR", steps=[
            TraceStep(profile="dev", key="BAR", value=None, source="missing"),
        ])
        assert report.first_resolved() is None

    def test_repr_shows_unresolved(self):
        report = TraceReport(key="BAR", steps=[
            TraceStep(profile="dev", key="BAR", value=None, source="missing"),
        ])
        assert "unresolved" in repr(report)

    def test_repr_shows_first_profile(self):
        report = TraceReport(key="FOO", steps=[
            TraceStep(profile="dev", key="FOO", value="v", source="env"),
        ])
        assert "dev" in repr(report)


class TestTraceKey:
    def test_raises_for_empty_chains(self):
        with pytest.raises(ValueError, match="empty"):
            trace_key("FOO", [])

    def test_missing_key_produces_missing_step(self):
        chain = _make_chain("dev")
        report = trace_key("ABSENT", [chain])
        assert len(report.steps) == 1
        assert report.steps[0].source == "missing"

    def test_default_value_produces_default_step(self):
        chain = _make_chain("dev", DATABASE_URL="sqlite://")
        report = trace_key("DATABASE_URL", [chain])
        assert report.steps[0].source == "default"
        assert report.steps[0].value == "sqlite://"

    def test_multiple_chains_all_traced(self):
        dev = _make_chain("dev", API_KEY="dev-key")
        prod = _make_chain("prod", API_KEY="prod-key")
        report = trace_key("API_KEY", [dev, prod])
        assert len(report.steps) == 2
        assert report.steps[0].profile == "dev"
        assert report.steps[1].profile == "prod"

    def test_first_resolved_reflects_chain_order(self):
        dev = _make_chain("dev")
        staging = _make_chain("staging", SECRET="s3cr3t")
        report = trace_key("SECRET", [dev, staging])
        first = report.first_resolved()
        assert first is not None
        assert first.profile == "staging"


class TestTraceAll:
    def test_raises_for_empty_chains(self):
        with pytest.raises(ValueError, match="empty"):
            trace_all([])

    def test_collects_all_unique_keys(self):
        dev = _make_chain("dev", FOO="1", BAR="2")
        prod = _make_chain("prod", BAR="3", BAZ="4")
        reports = trace_all([dev, prod])
        keys = {r.key for r in reports}
        assert keys == {"FOO", "BAR", "BAZ"}

    def test_each_report_has_step_per_chain(self):
        dev = _make_chain("dev", X="a")
        prod = _make_chain("prod", X="b")
        reports = trace_all([dev, prod])
        assert all(len(r.steps) == 2 for r in reports)
