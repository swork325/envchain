"""Tests for envchain.deduplicator."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.deduplicator import DedupeResult, deduplicate_chain


def _make_chain(profile: str = "dev", **kwargs: str) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in kwargs.items():
        chain.add(EnvVar(key=key, default=value))
    return chain


class TestDedupeResult:
    def test_repr_contains_profile_and_counts(self):
        chain = _make_chain()
        result = DedupeResult(
            profile="dev",
            duplicates={"x": ["A", "B"]},
            kept=["A"],
            dropped=["B"],
            chain=chain,
        )
        r = repr(result)
        assert "dev" in r
        assert "duplicate_groups=1" in r
        assert "kept=1" in r
        assert "dropped=1" in r

    def test_is_clean_when_nothing_dropped(self):
        chain = _make_chain()
        result = DedupeResult(
            profile="dev", duplicates={}, kept=["A"], dropped=[], chain=chain
        )
        assert result.is_clean is True

    def test_not_clean_when_something_dropped(self):
        chain = _make_chain()
        result = DedupeResult(
            profile="dev",
            duplicates={"v": ["A", "B"]},
            kept=["A"],
            dropped=["B"],
            chain=chain,
        )
        assert result.is_clean is False


class TestDeduplicateChain:
    def test_no_duplicates_returns_clean_result(self):
        chain = _make_chain(A="alpha", B="beta", C="gamma")
        result = deduplicate_chain(chain)
        assert result.is_clean
        assert result.dropped == []
        assert set(result.kept) == {"A", "B", "C"}

    def test_duplicate_value_drops_second_by_default(self):
        chain = _make_chain(A="same", B="other", C="same")
        result = deduplicate_chain(chain)
        assert "C" in result.dropped
        assert "A" in result.kept
        assert "C" not in result.kept

    def test_keep_last_drops_first_occurrence(self):
        chain = _make_chain(A="same", B="other", C="same")
        result = deduplicate_chain(chain, keep="last")
        assert "A" in result.dropped
        assert "C" in result.kept

    def test_output_chain_excludes_dropped_keys(self):
        chain = _make_chain(X="dup", Y="dup", Z="unique")
        result = deduplicate_chain(chain)
        output_keys = [v.key for v in result.chain.vars]
        assert "Y" not in output_keys
        assert "X" in output_keys
        assert "Z" in output_keys

    def test_none_values_never_considered_duplicates(self):
        chain = EnvChain(profile="dev")
        chain.add(EnvVar(key="A"))  # no default -> resolves to None
        chain.add(EnvVar(key="B"))  # same
        result = deduplicate_chain(chain)
        assert result.is_clean
        assert set(result.kept) == {"A", "B"}

    def test_duplicates_dict_lists_all_sharing_keys(self):
        chain = _make_chain(P="v", Q="v", R="v")
        result = deduplicate_chain(chain)
        assert "v" in result.duplicates
        assert set(result.duplicates["v"]) == {"P", "Q", "R"}

    def test_invalid_keep_raises_value_error(self):
        chain = _make_chain(A="x")
        with pytest.raises(ValueError, match="keep must be"):
            deduplicate_chain(chain, keep="middle")

    def test_profile_preserved_in_result(self):
        chain = _make_chain(profile="staging", A="val")
        result = deduplicate_chain(chain)
        assert result.profile == "staging"
        assert result.chain.profile == "staging"
