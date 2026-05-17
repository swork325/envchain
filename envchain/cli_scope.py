"""CLI entry-point for the *scope* sub-command."""

from __future__ import annotations

import argparse
import json
import sys

from envchain.exporter import export_chain
from envchain.loader import load_profile_env
from envchain.scoper import scope_chain


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envchain-scope",
        description="Restrict an env file to a named scope (key prefix).",
    )
    p.add_argument("env_file", help="Path to .env file")
    p.add_argument("scope", help="Key prefix to keep, e.g. DB")
    p.add_argument("--profile", default="dev", help="Profile name (default: dev)")
    p.add_argument(
        "--separator", default="_", help="Separator after prefix (default: _)"
    )
    p.add_argument(
        "--strip-prefix",
        action="store_true",
        default=False,
        help="Remove the scope prefix from resulting keys",
    )
    p.add_argument(
        "--format",
        choices=["dotenv", "shell", "json"],
        default="dotenv",
        dest="fmt",
        help="Output format (default: dotenv)",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a summary instead of exporting",
    )
    return p


def run_scope(args: argparse.Namespace, *, out=sys.stdout) -> int:
    chain = load_profile_env(args.env_file, profile=args.profile)
    scoped, result = scope_chain(
        chain,
        args.scope,
        separator=args.separator,
        strip_prefix=args.strip_prefix,
    )

    if args.summary:
        summary = {
            "profile": result.profile,
            "scope": result.scope,
            "included": len(result.included),
            "excluded": len(result.excluded),
        }
        out.write(json.dumps(summary, indent=2) + "\n")
        return 0

    if result.is_empty:
        out.write(f"# No variables matched scope '{args.scope}'\n")
        return 0

    out.write(export_chain(scoped, fmt=args.fmt))
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_scope(args))


if __name__ == "__main__":  # pragma: no cover
    main()
