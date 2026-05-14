"""Tests for envchain.tagger."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.tagger import EnvTagger, TaggedVar


def _make_chain(*keys: str) -> EnvChain:
    chain = EnvChain(profile="test")
    for key in keys:
        chain.add(EnvVar(key=key, default=f"val_{key.lower()}"))
    return chain


class TestTaggedVar:
    def test_repr_contains_key_and_tags(self):
        var = EnvVar(key="FOO", default="bar")
        tv = TaggedVar(var=var, tags=frozenset({"secret", "prod"}))
        r = repr(tv)
        assert "FOO" in r
        assert "prod" in r
        assert "secret" in r

    def test_has_tag_true(self):
        var = EnvVar(key="X", default="1")
        tv = TaggedVar(var=var, tags=frozenset({"required"}))
        assert tv.has_tag("required") is True

    def test_has_tag_false(self):
        var = EnvVar(key="X", default="1")
        tv = TaggedVar(var=var, tags=frozenset({"required"}))
        assert tv.has_tag("optional") is False


class TestEnvTagger:
    def test_tag_single_key(self):
        chain = _make_chain("DB_HOST", "DB_PORT")
        tagger = EnvTagger(chain)
        tagger.tag("DB_HOST", "database", "required")
        assert "database" in tagger.get_tags("DB_HOST")
        assert "required" in tagger.get_tags("DB_HOST")

    def test_tag_does_not_affect_other_keys(self):
        chain = _make_chain("A", "B")
        tagger = EnvTagger(chain)
        tagger.tag("A", "secret")
        assert tagger.get_tags("B") == frozenset()

    def test_tag_unknown_key_raises(self):
        chain = _make_chain("KNOWN")
        tagger = EnvTagger(chain)
        with pytest.raises(KeyError, match="UNKNOWN"):
            tagger.tag("UNKNOWN", "some-tag")

    def test_tag_all_applies_to_each_key(self):
        chain = _make_chain("X", "Y", "Z")
        tagger = EnvTagger(chain)
        tagger.tag_all(["X", "Y"], "shared")
        assert "shared" in tagger.get_tags("X")
        assert "shared" in tagger.get_tags("Y")
        assert "shared" not in tagger.get_tags("Z")

    def test_filter_by_tag_returns_matching(self):
        chain = _make_chain("API_KEY", "DB_URL", "LOG_LEVEL")
        tagger = EnvTagger(chain)
        tagger.tag("API_KEY", "secret")
        tagger.tag("DB_URL", "secret", "database")
        results = tagger.filter_by_tag("secret")
        keys = {tv.var.key for tv in results}
        assert keys == {"API_KEY", "DB_URL"}

    def test_filter_by_tag_empty_when_none_match(self):
        chain = _make_chain("FOO")
        tagger = EnvTagger(chain)
        assert tagger.filter_by_tag("nonexistent") == []

    def test_all_tags_aggregates_across_vars(self):
        chain = _make_chain("A", "B", "C")
        tagger = EnvTagger(chain)
        tagger.tag("A", "alpha")
        tagger.tag("B", "beta")
        tagger.tag("C", "alpha", "gamma")
        assert tagger.all_tags() == frozenset({"alpha", "beta", "gamma"})

    def test_all_tags_empty_when_no_tags_assigned(self):
        chain = _make_chain("A", "B")
        tagger = EnvTagger(chain)
        assert tagger.all_tags() == frozenset()

    def test_tagged_vars_length_matches_chain(self):
        chain = _make_chain("P", "Q", "R")
        tagger = EnvTagger(chain)
        assert len(tagger.tagged_vars()) == 3

    def test_chained_tag_calls(self):
        chain = _make_chain("K")
        tagger = EnvTagger(chain)
        result = tagger.tag("K", "x").tag("K", "y")
        assert result is tagger
        assert tagger.get_tags("K") == frozenset({"x", "y"})
