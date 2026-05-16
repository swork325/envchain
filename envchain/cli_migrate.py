"""CLI entry-point for the migrate command."""

from __future__ import annotations

import argparse
import json
import sys

from envchain.exporter import export_chain
from envchain.loader import load_profile_env
from envchain.migrator import migrate_chain


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envchain-migrate",
        description="Migrate an env file to a new profile with optional renames, drops, and additions.",
    )
    p.add_argument("env_file", help="Path to source .env file")
    p.add_argument("target_profile", help="Target profile name (e.g. staging, prod)")
    p.add_argument(
        "--source-profile",
        default="dev",
        metavar="PROFILE",
        help="Source profile name (default: dev)",
    )
    p.add_argument(
        "--rename",
        nargs="+",
        metavar="OLD=NEW",
        default=[],
        help="Key renames in OLD=NEW format",
    )
    p.add_argument(
        "--drop",
        nargs="+",
        metavar="KEY",
        default=[],
        help="Keys to drop from the result",
    )
    p.add_argument(
        "--add",
        nargs="+",
        metavar="KEY=VALUE",
        default=[],
        help="Keys to inject in KEY=VALUE format",
    )
    p.add_argument(
        "--format",
        choices=["dotenv", "shell", "json"],
        default="dotenv",
        dest="fmt",
        help="Output format (default: dotenv)",
    )
    return p


def _parse_pairs(pairs: list[str]) -> dict[str, str]:
    result = {}
    for item in pairs:
        if "=" not in item:
            print(f"[error] invalid KEY=VALUE pair: {item!r}", file=sys.stderr)
            sys.exit(1)
        k, _, v = item.partition("=")
        result[k.strip()] = v.strip()
    return result


def run_migrate(args: argparse.Namespace) -> None:
    chain = load_profile_env(args.env_file, profile=args.source_profile)
    rename = _parse_pairs(args.rename)
    add = _parse_pairs(args.add) if args.add else {}

    result = migrate_chain(
        chain,
        args.target_profile,
        rename=rename or None,
        drop=args.drop or None,
        add=add or None,
    )

    summary = {
        "source": result.source_profile,
        "target": result.target_profile,
        "added": result.added,
        "renamed": result.renamed,
        "dropped": result.dropped,
        "clean": result.is_clean(),
    }
    print(json.dumps(summary, indent=2), file=sys.stderr)
    print(export_chain(result.chain, fmt=args.fmt))


def main() -> None:  # pragma: no cover
    run_migrate(build_parser().parse_args())


if __name__ == "__main__":  # pragma: no cover
    main()
