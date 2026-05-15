"""CLI entry-point for the `envchain clone` command."""

from __future__ import annotations

import argparse
import json
import sys

from .loader import load_profile_env
from .cloner import clone_chain
from .exporter import export_chain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-clone",
        description="Clone an env file's chain into a different profile.",
    )
    parser.add_argument("env_file", help="Path to the source .env file.")
    parser.add_argument(
        "--source-profile",
        default="dev",
        choices=["dev", "staging", "prod"],
        help="Profile of the source chain (default: dev).",
    )
    parser.add_argument(
        "--target-profile",
        default="staging",
        choices=["dev", "staging", "prod"],
        help="Profile for the cloned chain (default: staging).",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        metavar="KEY",
        help="Keys to exclude from the clone.",
    )
    parser.add_argument(
        "--uppercase-keys",
        action="store_true",
        help="Transform all keys to uppercase in the clone.",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        default="dotenv",
        choices=["dotenv", "shell", "json"],
        help="Output format (default: dotenv).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a JSON summary of the clone operation instead of the chain.",
    )
    return parser


def run_clone(args: argparse.Namespace, *, out=sys.stdout, err=sys.stderr) -> int:
    try:
        source = load_profile_env(args.env_file, profile=args.source_profile)
    except Exception as exc:  # pragma: no cover
        err.write(f"error: {exc}\n")
        return 1

    key_transform = str.upper if args.uppercase_keys else None

    try:
        cloned, result = clone_chain(
            source,
            args.target_profile,
            key_transform=key_transform,
            exclude=args.exclude or [],
        )
    except ValueError as exc:
        err.write(f"error: {exc}\n")
        return 1

    if args.summary:
        summary = {
            "source_profile": result.source_profile,
            "target_profile": result.target_profile,
            "cloned": result.cloned,
            "skipped": result.skipped,
        }
        out.write(json.dumps(summary, indent=2) + "\n")
    else:
        out.write(export_chain(cloned, fmt=args.fmt))

    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_clone(args))
