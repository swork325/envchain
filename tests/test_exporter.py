"""Tests for envchain.exporter module."""

import json
import pytest
from unittest.mock import patch

from envchain.chain import EnvChain, EnvVar
from envchain.exporter import export_chain, SUPPORTED_FORMATS


def _make_chain(*pairs):
    """Build an EnvChain pre-populated with EnvVar instances."""
    chain = EnvChain()
    for name, default in pairs:
        chain.add(EnvVar(name, default=default))
    return chain


class TestExportFormats:
    def test_supported_formats_constant(self):
        assert "dotenv" in SUPPORTED_FORMATS
        assert "shell" in SUPPORTED_FORMATS
        assert "json" in SUPPORTED_FORMATS

    def test_raises_for_unsupported_format(self):
        chain = _make_chain(("FOO", "bar"))
        with pytest.raises(ValueError, match="Unsupported format"):
            export_chain(chain, fmt="yaml")


class TestDotenvExport:
    def test_exports_key_value_pairs(self):
        chain = _make_chain(("APP_ENV", "development"), ("DEBUG", "true"))
        output = export_chain(chain, fmt="dotenv")
        assert 'APP_ENV="development"' in output
        assert 'DEBUG="true"' in output

    def test_comments_out_missing_values(self):
        chain = _make_chain(("SECRET_KEY", None))
        output = export_chain(chain, fmt="dotenv")
        assert "# SECRET_KEY=" in output

    def test_includes_profile_comment(self):
        chain = _make_chain(("APP_ENV", "staging"))
        output = export_chain(chain, fmt="dotenv", profile="staging")
        assert "# profile: staging" in output

    def test_escapes_double_quotes_in_values(self):
        chain = _make_chain(("GREETING", 'say "hello"'))
        output = export_chain(chain, fmt="dotenv")
        assert '\\"hello\\"' in output


class TestShellExport:
    def test_exports_with_export_prefix(self):
        chain = _make_chain(("PATH_EXTRA", "/usr/local/bin"))
        output = export_chain(chain, fmt="shell")
        assert 'export PATH_EXTRA="/usr/local/bin"' in output

    def test_comments_out_missing_values(self):
        chain = _make_chain(("MISSING_VAR", None))
        output = export_chain(chain, fmt="shell")
        assert "# export MISSING_VAR=" in output

    def test_includes_profile_comment(self):
        chain = _make_chain(("APP_ENV", "prod"))
        output = export_chain(chain, fmt="shell", profile="prod")
        assert "# profile: prod" in output


class TestJsonExport:
    def test_exports_valid_json(self):
        chain = _make_chain(("APP_ENV", "test"), ("PORT", "8080"))
        output = export_chain(chain, fmt="json")
        data = json.loads(output)
        assert data["vars"]["APP_ENV"] == "test"
        assert data["vars"]["PORT"] == "8080"

    def test_includes_profile_key_when_given(self):
        chain = _make_chain(("APP_ENV", "dev"))
        output = export_chain(chain, fmt="json", profile="dev")
        data = json.loads(output)
        assert data["profile"] == "dev"

    def test_none_values_serialized_as_null(self):
        chain = _make_chain(("OPTIONAL", None))
        output = export_chain(chain, fmt="json")
        data = json.loads(output)
        assert data["vars"]["OPTIONAL"] is None
