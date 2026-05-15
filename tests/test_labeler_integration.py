"""Integration tests: labeler + exporter + tagger round-trip."""

from __future__ import annotations

import json

from envchain.chain import EnvChain, EnvVar
from envchain.exporter import export_chain
from envchain.labeler import label_chain


def _make_chain(*pairs, profile="dev") -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in pairs:
        chain.add(EnvVar(key=key, default=value))
    return chain


class TestLabelerExporterIntegration:
    def test_labeled_keys_match_exported_keys(self):
        chain = _make_chain(
            ("DB_URL", "postgres://localhost"),
            ("CACHE_URL", "redis://localhost"),
            ("LOG_LEVEL", "info"),
        )
        rules = {
            "DB_URL": {"tier": "storage"},
            "CACHE_URL": {"tier": "storage"},
        }
        report = label_chain(chain, rules)
        storage_keys = {e.var.key for e in report.where("tier", "storage")}

        exported = json.loads(export_chain(chain, fmt="json"))
        exported_keys = set(exported.keys())

        assert storage_keys.issubset(exported_keys)

    def test_all_vars_labeled_even_without_rules(self):
        chain = _make_chain(("A", "1"), ("B", "2"), ("C", "3"))
        report = label_chain(chain, {})
        assert len(report.entries) == 3
        for entry in report.entries:
            assert entry.labels == {}

    def test_filter_then_export_subset(self):
        chain = _make_chain(
            ("SECRET_KEY", "s3cr3t"),
            ("PUBLIC_URL", "https://example.com"),
        )
        rules = {
            "SECRET_KEY": {"visibility": "private"},
            "PUBLIC_URL": {"visibility": "public"},
        }
        report = label_chain(chain, rules)
        public_entries = report.where("visibility", "public")
        assert len(public_entries) == 1
        assert public_entries[0].var.key == "PUBLIC_URL"

    def test_keys_with_across_multiple_labels(self):
        chain = _make_chain(
            ("TOKEN", "abc"),
            ("DB_PASS", "xyz"),
            ("HOST", "localhost"),
        )
        rules = {
            "TOKEN": {"rotate": "true", "sensitive": "true"},
            "DB_PASS": {"rotate": "true", "sensitive": "true"},
            "HOST": {"sensitive": "false"},
        }
        report = label_chain(chain, rules)
        rotate_keys = set(report.keys_with("rotate"))
        assert rotate_keys == {"TOKEN", "DB_PASS"}
        sensitive_keys = set(report.keys_with("sensitive"))
        assert sensitive_keys == {"TOKEN", "DB_PASS", "HOST"}
