"""CLI entry point for rendering an env file as a formatted table or summary."""

from __future__ import annotations

import argparse
import sys

from envchain.loader import load_profile_env
from envchain.renderer import SUPPORTED_FORMATS, render_chain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-render",
        description="Render environment variables from a .env file.",
    )
    parser.add_argument(
        "env_file",
        help="Path to the .env file to render.",
    )
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name to assign to the loaded chain (default: dev).",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=list(SUPPORTED_FORMATS),
        default="table",
        help="Output format (default: table).",
    )
    parser.add_argument(
        "--redact",
        action="store_true",
        default=False,
        help="Mask variable values in the output.",
    )
    return parser


def run_render(args: argparse.Namespace, out=sys.stdout) -> int:
    """Execute the render command. Returns exit code."""
    try:
        chain = load_profile_env(args.env_file, profile=args.profile)
    except FileNotFoundError:
        out.write(f"Error: file not found: {args.env_file}\n")
        return 1
    except Exception as exc:  # noqa: BLE001
        out.write(f"Error loading env file: {exc}\n")
        return 1

    output = render_chain(chain, fmt=args.fmt, redact=args.redact)
    out.write(output + "\n")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run_render(args))


if __name__ == "__main__":
    main()
