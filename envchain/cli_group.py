"""CLI entry point for grouping environment variables by prefix."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envchain.grouper import group_by_prefix
from envchain.loader import load_profile_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-group",
        description="Group environment variables from a .env file by key prefix.",
    )
    parser.add_argument("env_file", help="Path to the .env file to load.")
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name to use when loading (default: dev).",
    )
    parser.add_argument(
        "--separator",
        default="_",
        help="Separator used to split key prefixes (default: '_').",
    )
    parser.add_argument(
        "--ungrouped-label",
        default="__other__",
        dest="ungrouped_label",
        help="Label for keys that have no separator (default: __other__).",
    )
    return parser


def run_group(args: argparse.Namespace, out=sys.stdout) -> None:
    chain = load_profile_env(args.env_file, profile=args.profile)
    groups = group_by_prefix(
        chain,
        separator=args.separator,
        ungrouped_label=args.ungrouped_label,
    )

    if not groups:
        out.write("(no variables found)\n")
        return

    for group_name, group in groups.items():
        out.write(f"[{group_name}]\n")
        for var in sorted(group.vars, key=lambda v: v.key):
            value = var.resolve()
            display = value if value is not None else "<unset>"
            out.write(f"  {var.key} = {display}\n")
        out.write("\n")


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)
    run_group(args)


if __name__ == "__main__":  # pragma: no cover
    main()
