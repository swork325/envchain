"""CLI entry-point for freeze / thaw operations on EnvChain profiles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envchain.loader import load_profile_env
from envchain.freezer import freeze, thaw, diff_frozen, FrozenChain
from envchain.exporter import export_chain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-freeze",
        description="Freeze, thaw, or diff EnvChain profile snapshots.",
    )
    sub = parser.add_subparsers(dest="subcommand")

    # freeze sub-command
    p_freeze = sub.add_parser("freeze", help="Capture chain state to a JSON file.")
    p_freeze.add_argument("env_file", help="Path to .env file")
    p_freeze.add_argument("output", help="Destination JSON file")
    p_freeze.add_argument("--profile", default="default")

    # thaw sub-command
    p_thaw = sub.add_parser("thaw", help="Restore a frozen chain and export it.")
    p_thaw.add_argument("frozen_file", help="Path to frozen JSON file")
    p_thaw.add_argument("--format", default="dotenv", dest="fmt")

    # diff sub-command
    p_diff = sub.add_parser("diff", help="Diff two frozen chain JSON files.")
    p_diff.add_argument("before", help="Before frozen JSON file")
    p_diff.add_argument("after", help="After frozen JSON file")

    return parser


def run_freeze(args: argparse.Namespace) -> None:
    chain = load_profile_env(args.env_file, profile=args.profile)
    fc = freeze(chain, profile=args.profile)
    Path(args.output).write_text(fc.to_json())
    print(f"Frozen {len(fc.values)} variable(s) to {args.output}")


def run_thaw(args: argparse.Namespace) -> None:
    fc = FrozenChain.from_json(Path(args.frozen_file).read_text())
    chain = thaw(fc)
    print(export_chain(chain, fmt=args.fmt))


def run_diff(args: argparse.Namespace) -> None:
    before = FrozenChain.from_json(Path(args.before).read_text())
    after = FrozenChain.from_json(Path(args.after).read_text())
    entries = diff_frozen(before, after)
    if not entries:
        print("No differences found.")
        return
    for entry in entries:
        print(entry)


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.subcommand == "freeze":
        run_freeze(args)
    elif args.subcommand == "thaw":
        run_thaw(args)
    elif args.subcommand == "diff":
        run_diff(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
