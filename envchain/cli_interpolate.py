"""CLI entry-point: expand ${VAR} references in an env file and print results."""

from __future__ import annotations

import argparse
import json
import sys

from envchain.interpolator import InterpolationError, interpolate_chain
from envchain.loader import load_profile_env
from envchain.exporter import export_chain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-interpolate",
        description="Expand \${VAR} references within an env file.",
    )
    parser.add_argument("env_file", help="Path to the .env file to process")
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name to load (default: dev)",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["dotenv", "shell", "json"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Leave unresolvable references as-is instead of raising an error",
    )
    return parser


def run_interpolate(args: argparse.Namespace) -> int:
    try:
        chain = load_profile_env(args.env_file, profile=args.profile)
    except FileNotFoundError:
        print(f"error: file not found: {args.env_file}", file=sys.stderr)
        return 1

    strict = not args.no_strict
    try:
        result = interpolate_chain(chain, strict=strict)
    except InterpolationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(export_chain(result, fmt=args.fmt))
    return 0


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_interpolate(args))


if __name__ == "__main__":  # pragma: no cover
    main()
