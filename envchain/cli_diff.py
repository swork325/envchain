"""CLI helper for the `envchain diff` sub-command.

Usage (standalone):
    python -m envchain.cli_diff <left.env> <right.env> [--values] [--names A B]
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envchain.chain import EnvChain, EnvVar
from envchain.differ import diff_chains
from envchain.loader import load_profile_env


def _chain_from_file(path: str) -> EnvChain:
    """Load a .env file into an EnvChain using static defaults (no os.environ lookup)."""
    mapping = load_profile_env(path)
    chain = EnvChain()
    for key, value in mapping.items():
        chain.add(EnvVar(name=key, default=value))
    return chain


def run_diff(
    left_path: str,
    right_path: str,
    left_name: Optional[str] = None,
    right_name: Optional[str] = None,
    compare_values: bool = False,
    stream=None,
) -> int:
    """Execute the diff and write the summary to *stream* (defaults to stdout).

    Returns:
        0 if no differences were found, 1 otherwise.
    """
    if stream is None:
        stream = sys.stdout

    left_label = left_name or left_path
    right_label = right_name or right_path

    try:
        left_chain = _chain_from_file(left_path)
        right_chain = _chain_from_file(right_path)
    except FileNotFoundError as exc:
        stream.write(f"Error: {exc}\n")
        return 2

    result = diff_chains(
        left_chain,
        right_chain,
        left_name=left_label,
        right_name=right_label,
        compare_values=compare_values,
    )

    stream.write(result.summary() + "\n")
    return 1 if result.has_differences else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain diff",
        description="Compare two .env files and report key/value differences.",
    )
    parser.add_argument("left", help="Path to the first .env file (e.g. .env.dev)")
    parser.add_argument("right", help="Path to the second .env file (e.g. .env.prod)")
    parser.add_argument(
        "--values",
        action="store_true",
        default=False,
        help="Also report keys present in both files but with differing values.",
    )
    parser.add_argument(
        "--names",
        nargs=2,
        metavar=("LEFT_NAME", "RIGHT_NAME"),
        help="Human-readable labels for the two files.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    left_name, right_name = (args.names or [None, None])
    exit_code = run_diff(
        left_path=args.left,
        right_path=args.right,
        left_name=left_name,
        right_name=right_name,
        compare_values=args.values,
    )
    sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
