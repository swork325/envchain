"""CLI entry point for the ``inspect`` sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envchain.loader import load_profile_env
from envchain.inspector import InspectReport, inspect_chain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-inspect",
        description="Inspect environment variable metadata for a profile.",
    )
    parser.add_argument("env_file", help="Path to the .env file to load.")
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name (default: dev).",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--missing-only",
        action="store_true",
        default=False,
        help="Only show variables that are missing (no value, no default).",
    )
    return parser


def _print_text(report: InspectReport, missing_only: bool) -> None:
    entries = report.missing if missing_only else report.entries
    if not entries:
        print("No entries to display.")
        return
    width = max(len(e.key) for e in entries)
    for entry in entries:
        flag = "[missing]" if entry.source == "missing" else f"[{entry.source}]"
        val = entry.value if entry.value is not None else "<none>"
        print(f"{entry.key:<{width}}  {flag:<10}  {val}")


def _print_json(report: InspectReport, missing_only: bool) -> None:
    entries = report.missing if missing_only else report.entries
    data = {
        "profile": report.profile,
        "entries": [
            {
                "key": e.key,
                "value": e.value,
                "default": e.default,
                "source": e.source,
                "has_value": e.has_value,
                "has_default": e.has_default,
                "is_empty": e.is_empty,
            }
            for e in entries
        ],
    }
    print(json.dumps(data, indent=2))


def run_inspect(args: argparse.Namespace) -> None:
    chain = load_profile_env(args.env_file, profile=args.profile)
    report = inspect_chain(chain)
    if args.fmt == "json":
        _print_json(report, args.missing_only)
    else:
        _print_text(report, args.missing_only)


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)
    run_inspect(args)


if __name__ == "__main__":  # pragma: no cover
    main()
