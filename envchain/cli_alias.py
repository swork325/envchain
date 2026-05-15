"""CLI for the aliaser module."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envchain.loader import load_profile_env
from envchain.aliaser import alias_chain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-alias",
        description="Attach human-friendly aliases to environment variable keys.",
    )
    parser.add_argument("env_file", help="Path to .env file")
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name (default: dev)",
    )
    parser.add_argument(
        "--alias",
        metavar="KEY=ALIAS",
        action="append",
        default=[],
        dest="aliases",
        help="Alias mapping in KEY=ALIAS format (repeatable)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    return parser


def _parse_alias_args(raw: List[str]) -> dict:
    result = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Invalid alias spec {item!r}: expected KEY=ALIAS")
        key, alias = item.split("=", 1)
        result[key.strip()] = alias.strip()
    return result


def run_alias(args: argparse.Namespace) -> None:
    chain = load_profile_env(args.env_file, profile=args.profile)
    alias_map = _parse_alias_args(args.aliases)
    report = alias_chain(chain, alias_map)

    if args.fmt == "json":
        data = [
            {"key": e.var.key, "alias": e.alias, "display_key": e.display_key}
            for e in report.entries
        ]
        print(json.dumps({"profile": report.profile, "entries": data}, indent=2))
    else:
        print(f"Profile : {report.profile}")
        print(f"Aliased : {len(report.aliased_keys)} / {len(report.entries)} keys")
        print()
        for entry in report.entries:
            suffix = f"  -> {entry.alias}" if entry.alias else ""
            print(f"  {entry.var.key}{suffix}")


def main(argv=None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run_alias(args)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
