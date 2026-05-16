"""Tests for envchain.cli_rotate."""

from __future__ import annotations

import io
import os
import tempfile
import unittest

from envchain.cli_rotate import build_parser, run_rotate


def _write_env(content: str) -> str:
    """Write *content* to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".env")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestBuildParser(unittest.TestCase):
    def test_env_file_required(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([])

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["file.env"])
        self.assertEqual(args.profile, "dev")
        self.assertEqual(args.token_length, 32)
        self.assertEqual(args.fmt, "dotenv")
        self.assertIsNone(args.keys)

    def test_custom_options(self):
        parser = build_parser()
        args = parser.parse_args(
            ["file.env", "--profile", "prod", "--token-length", "16", "--format", "json"]
        )
        self.assertEqual(args.profile, "prod")
        self.assertEqual(args.token_length, 16)
        self.assertEqual(args.fmt, "json")

    def test_keys_flag(self):
        parser = build_parser()
        args = parser.parse_args(["file.env", "--keys", "SECRET", "TOKEN"])
        self.assertEqual(args.keys, ["SECRET", "TOKEN"])


class TestRunRotate(unittest.TestCase):
    def setUp(self):
        self.env_path = _write_env("SECRET=old_value\nTOKEN=another\n")

    def tearDown(self):
        os.unlink(self.env_path)

    def test_dotenv_output_contains_keys(self):
        parser = build_parser()
        args = parser.parse_args([self.env_path])
        out = io.StringIO()
        code = run_rotate(args, out=out)
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("SECRET=", text)
        self.assertIn("TOKEN=", text)

    def test_values_are_replaced(self):
        parser = build_parser()
        args = parser.parse_args([self.env_path])
        out = io.StringIO()
        run_rotate(args, out=out)
        text = out.getvalue()
        self.assertNotIn("old_value", text)
        self.assertNotIn("another", text)

    def test_only_specified_key_rotated(self):
        parser = build_parser()
        args = parser.parse_args([self.env_path, "--keys", "SECRET"])
        out = io.StringIO()
        run_rotate(args, out=out)
        text = out.getvalue()
        self.assertIn("TOKEN=another", text)

    def test_json_format_includes_rotated_list(self):
        parser = build_parser()
        args = parser.parse_args([self.env_path, "--format", "json"])
        out = io.StringIO()
        run_rotate(args, out=out)
        import json
        payload = json.loads(out.getvalue())
        self.assertIn("rotated", payload)
        self.assertIn("skipped", payload)
