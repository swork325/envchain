"""CLI entry point for tagging and querying env var tags."""

from __future__ import annotations

import argparse
import json
import sys

from envchain.loader import load_profile_env
from envchain.tagger import EnvTagger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-tag",
        description="Tag environment variables and query by tag.",
    )
    parser.add_argument("env_file", help="Path to .env file to load")
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name to use when loading (default: dev)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    tag_p = sub.add_parser("tag", help="Assign tags to a key")
    tag_p.add_argument("key", help="Environment variable key")
    tag_p.add_argument("tags", nargs="+", help="One or more tags to assign")

    filter_p = sub.add_parser("filter", help="List keys carrying a specific tag")
    filter_p.add_argument("tag", help="Tag to filter by")
    filter_p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
    )

    sub.add_parser("list-tags", help="Show all tags in use across the chain")

    return parser


def run_tag(args: argparse.Namespace) -> None:
    chain = load_profile_env(args.env_file, profile=args.profile)
    tagger = EnvTagger(chain)

    if args.command == "tag":
        try:
            tagger.tag(args.key, *args.tags)
        except KeyError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Tagged {args.key!r} with: {', '.join(sorted(args.tags))}")

    elif args.command == "filter":
        matches = tagger.filter_by_tag(args.tag)
        if args.fmt == "json":
            output = [
                {"key": tv.var.key, "tags": sorted(tv.tags)} for tv in matches
            ]
            print(json.dumps(output, indent=2))
        else:
            if not matches:
                print(f"No variables tagged with {args.tag!r}")
            else:
                for tv in matches:
                    print(tv.var.key)

    elif args.command == "list-tags":
        tags = tagger.all_tags()
        if not tags:
            print("No tags assigned.")
        else:
            for t in sorted(tags):
                print(t)


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    run_tag(args)


if __name__ == "__main__":  # pragma: no cover
    main()
