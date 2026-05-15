"""CLI entry point for the `envchain promote` command."""

from __future__ import annotations

import argparse
import sys

from envchain.loader import load_profile_env
from envchain.promoter import next_profile, promote_chain
from envchain.exporter import export_chain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-promote",
        description="Promote environment variables from one profile to the next.",
    )
    parser.add_argument("env_file", help="Path to the .env file to load")
    parser.add_argument(
        "--source",
        default="dev",
        choices=["dev", "staging", "prod"],
        help="Source profile (default: dev)",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Target profile (default: next in chain after source)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys in target profile",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        default=None,
        metavar="KEY",
        help="Explicit list of keys to promote (default: all)",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        default="dotenv",
        choices=["dotenv", "shell", "json"],
        help="Output format for the resulting chain (default: dotenv)",
    )
    return parser


def run_promote(args: argparse.Namespace, *, out=sys.stdout, err=sys.stderr) -> int:
    source_profile = args.source

    if args.target is not None:
        target_profile = args.target
    else:
        target_profile = next_profile(source_profile)
        if target_profile is None:
            err.write(
                f"error: '{source_profile}' is already the final profile in the chain.\n"
            )
            return 1

    try:
        src_chain = load_profile_env(args.env_file, profile=source_profile)
        tgt_chain = load_profile_env(args.env_file, profile=target_profile)
    except FileNotFoundError as exc:
        err.write(f"error: {exc}\n")
        return 1

    new_chain, result = promote_chain(
        src_chain,
        tgt_chain,
        overwrite=args.overwrite,
        keys=args.keys,
    )

    err.write(
        f"Promoted {len(result.promoted_keys)} key(s) from '{source_profile}' "
        f"to '{target_profile}'.\n"
    )
    if result.skipped_keys:
        err.write(f"Skipped: {', '.join(result.skipped_keys)}\n")

    out.write(export_chain(new_chain, fmt=args.fmt))
    out.write("\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_promote(args))


if __name__ == "__main__":  # pragma: no cover
    main()
