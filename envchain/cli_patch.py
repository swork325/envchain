"""CLI entry-point: apply an override patch to an env file."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envchain.loader import load_profile_env
from envchain.patcher import patch_chain
from envchain.exporter import export_chain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-patch",
        description="Patch an env file with key=value overrides or removals.",
    )
    parser.add_argument("env_file", help="Path to the .env file to patch")
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name to load (default: dev)",
    )
    parser.add_argument(
        "--set",
        dest="sets",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Override a key (repeatable). Use KEY= to clear the value.",
    )
    parser.add_argument(
        "--remove",
        dest="removals",
        metavar="KEY",
        action="append",
        default=[],
        help="Remove a key from the chain (repeatable).",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        default="dotenv",
        choices=["dotenv", "shell", "json"],
        help="Output format (default: dotenv)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a change summary to stderr instead of the patched output.",
    )
    return parser


def run_patch(args: argparse.Namespace) -> int:
    chain = load_profile_env(args.env_file, profile=args.profile)

    overrides: dict[str, Optional[str]] = {}
    for pair in args.sets:
        if "=" not in pair:
            print(f"error: --set requires KEY=VALUE format, got: {pair!r}", file=sys.stderr)
            return 2
        key, _, value = pair.partition("=")
        overrides[key.strip()] = value if value else None

    patched, result = patch_chain(chain, overrides=overrides, removals=args.removals)

    if args.summary:
        summary = {
            "added": result.added,
            "updated": result.updated,
            "removed": result.removed,
        }
        print(json.dumps(summary, indent=2), file=sys.stderr)

    print(export_chain(patched, fmt=args.fmt))
    return 0


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_patch(args))


if __name__ == "__main__":  # pragma: no cover
    main()
