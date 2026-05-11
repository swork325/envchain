"""Tests for envchain.grouper."""

from __future__ import annotations

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.grouper import EnvGroup, group_by_classifier, group_by_prefix


def _make_chain(**kwargs: str) -> EnvChain:
    chain = EnvChain(profile="test")
    for key, value in kwargs.items():
        chain.add(EnvVar(key=key, default=value))
    return chain


# ---------------------------------------------------------------------------
# EnvGroup
# ---------------------------------------------------------------------------

class TestEnvGroup:
    def test_name_and_vars_stored(self):
        var = EnvVar(key="DB_HOST", default="localhost")
        group = EnvGroup(name="DB", vars=[var])
        assert group.name == "DB"
        assert group.vars == [var]

    def test_equality(self):
        var = EnvVar(key="X", default="1")
        assert EnvGroup("G", [var]) == EnvGroup("G", [var])

    def test_inequality_different_name(self):
        var = EnvVar(key="X", default="1")
        assert EnvGroup("A", [var]) != EnvGroup("B", [var])


# ---------------------------------------------------------------------------
# group_by_prefix
# ---------------------------------------------------------------------------

class TestGroupByPrefix:
    def test_groups_by_first_segment(self):
        chain = _make_chain(DB_HOST="localhost", DB_PORT="5432", APP_NAME="myapp")
        groups = group_by_prefix(chain)
        assert set(groups.keys()) == {"DB", "APP"}
        db_keys = {v.key for v in groups["DB"].vars}
        assert db_keys == {"DB_HOST", "DB_PORT"}

    def test_ungrouped_label_used_when_no_separator(self):
        chain = _make_chain(SIMPLE="value", DB_HOST="localhost")
        groups = group_by_prefix(chain)
        assert "__other__" in groups
        assert groups["__other__"].vars[0].key == "SIMPLE"

    def test_custom_ungrouped_label(self):
        chain = _make_chain(PLAIN="x")
        groups = group_by_prefix(chain, ungrouped_label="misc")
        assert "misc" in groups

    def test_custom_separator(self):
        chain = _make_chain(**{"DB.HOST": "h", "DB.PORT": "5432"})
        groups = group_by_prefix(chain, separator=".")
        assert "DB" in groups
        assert len(groups["DB"].vars) == 2

    def test_empty_chain_returns_empty_dict(self):
        chain = EnvChain(profile="test")
        assert group_by_prefix(chain) == {}

    def test_result_keys_sorted(self):
        chain = _make_chain(Z_KEY="z", A_KEY="a", M_KEY="m")
        keys = list(group_by_prefix(chain).keys())
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# group_by_classifier
# ---------------------------------------------------------------------------

class TestGroupByClassifier:
    def test_classifier_called_per_var(self):
        chain = _make_chain(SECRET_KEY="s", PUBLIC_URL="u", SECRET_TOKEN="t")

        def classify(var: EnvVar):
            return "secret" if "SECRET" in var.key else "public"

        groups = group_by_classifier(chain, classify)
        assert set(groups.keys()) == {"secret", "public"}
        secret_keys = {v.key for v in groups["secret"].vars}
        assert secret_keys == {"SECRET_KEY", "SECRET_TOKEN"}

    def test_none_return_goes_to_ungrouped(self):
        chain = _make_chain(FOO="bar")
        groups = group_by_classifier(chain, lambda v: None)
        assert "__other__" in groups

    def test_custom_ungrouped_label_classifier(self):
        chain = _make_chain(FOO="bar")
        groups = group_by_classifier(chain, lambda v: None, ungrouped_label="rest")
        assert "rest" in groups

    def test_empty_chain_returns_empty_dict(self):
        chain = EnvChain(profile="test")
        assert group_by_classifier(chain, lambda v: "x") == {}
