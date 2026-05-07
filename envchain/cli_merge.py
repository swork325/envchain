"""CLI entry point for merging env files using envchain."""

import argparse
import sys
from envchain.loader import load_profile_env
from envchain.merger import merge_chains, ConflictStrategy, MergeConflict
from envchain.exporter import export_chain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-merge",
        description="Merge multiple .env files into one with conflict resolution.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Paths to .env files to merge (in order of precedence).",
    )
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in ConflictStrategy],
        default=ConflictStrategy.LAST_WINS.value,
        help="Conflict resolution strategy (default: last_wins).",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["dotenv", "shell", "json"],
        default="dotenv",
        help="Output format (default: dotenv).",
    )
    return parser


def run_merge(files: list, strategy: ConflictStrategy, fmt: str) -> str:
    """Load, merge, and export env chains from the given files."""
    chains = []
    for filepath in files:
        try:
            chain = load_profile_env(filepath)
        except FileNotFoundError:
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        chains.append(chain)

    try:
        merged = merge_chains(chains, strategy=strategy)
    except MergeConflict as e:
        print(f"Merge conflict: {e}", file=sys.stderr)
        sys.exit(2)

    return export_chain(merged, fmt=fmt)


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    strategy = ConflictStrategy(args.strategy)
    output = run_merge(args.files, strategy=strategy, fmt=args.fmt)
    print(output)


if __name__ == "__main__":
    main()
