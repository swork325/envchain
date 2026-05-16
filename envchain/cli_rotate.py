"""CLI entry point for the *rotate* command."""

from __future__ import annotations

import argparse
import json
import secrets
import sys

from envchain.loader import load_profile_env
from envchain.exporter import export_chain
from envchain.rotator import rotate_chain


def _token_generator(length: int):
    """Return a generator that produces a hex token of *length* characters."""

    def _gen(key: str, value):
        return secrets.token_hex(length // 2)

    return _gen


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-rotate",
        description="Rotate environment variable values in a profile.",
    )
    parser.add_argument("env_file", help="Path to the .env file to load.")
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name (default: dev).",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific keys to rotate (default: all).",
    )
    parser.add_argument(
        "--token-length",
        type=int,
        default=32,
        dest="token_length",
        help="Length of generated hex token (default: 32).",
    )
    parser.add_argument(
        "--format",
        choices=["dotenv", "shell", "json"],
        default="dotenv",
        dest="fmt",
        help="Output format (default: dotenv).",
    )
    return parser


def run_rotate(args: argparse.Namespace, out=sys.stdout) -> int:
    chain = load_profile_env(args.env_file, profile=args.profile)
    generator = _token_generator(args.token_length)
    new_chain, result = rotate_chain(chain, generator, keys=args.keys)

    if args.fmt == "json":
        payload = {
            "profile": result.profile,
            "rotated": list(result.rotated.keys()),
            "skipped": result.skipped,
            "output": export_chain(new_chain, fmt="json"),
        }
        out.write(json.dumps(payload, indent=2))
    else:
        out.write(export_chain(new_chain, fmt=args.fmt))

    out.write("\n")
    return 0


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_rotate(args))


if __name__ == "__main__":
    main()
