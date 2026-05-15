"""CLI for archiving and restoring EnvChain snapshots."""

from __future__ import annotations

import argparse
import json
import sys

from envchain.archiver import Archive
from envchain.loader import load_profile_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-archive",
        description="Archive and restore EnvChain snapshots.",
    )
    sub = parser.add_subparsers(dest="subcommand")

    # capture
    cap = sub.add_parser("capture", help="Capture current env into archive.")
    cap.add_argument("env_file", help="Path to .env file.")
    cap.add_argument("archive_file", help="Path to archive (.gz) file.")
    cap.add_argument("--profile", default="default", help="Profile name.")

    # list
    lst = sub.add_parser("list", help="List entries in an archive.")
    lst.add_argument("archive_file", help="Path to archive (.gz) file.")
    lst.add_argument("--profile", default=None, help="Filter by profile.")

    # restore
    rst = sub.add_parser("restore", help="Print latest snapshot values.")
    rst.add_argument("archive_file", help="Path to archive (.gz) file.")
    rst.add_argument("--profile", default=None, help="Filter by profile.")
    rst.add_argument("--format", choices=["dotenv", "json"], default="dotenv")

    return parser


def run_capture(args: argparse.Namespace) -> None:
    chain = load_profile_env(args.env_file, profile=args.profile)
    try:
        archive = Archive.load(args.archive_file)
    except (FileNotFoundError, OSError):
        archive = Archive(path=args.archive_file)
    archive.add(chain, profile=args.profile)
    archive.save()
    print(f"Captured snapshot to {args.archive_file!r} (profile={args.profile!r}).")


def run_list(args: argparse.Namespace) -> None:
    archive = Archive.load(args.archive_file)
    entries = archive.entries
    if args.profile:
        entries = [e for e in entries if e.profile == args.profile]
    if not entries:
        print("No entries found.")
        return
    for e in entries:
        keys = list(e.snapshot.values.keys())
        print(f"{e.timestamp}  profile={e.profile!r}  keys={keys}")


def run_restore(args: argparse.Namespace) -> None:
    archive = Archive.load(args.archive_file)
    entry = archive.latest(profile=args.profile)
    if entry is None:
        print("No matching entry found.", file=sys.stderr)
        sys.exit(1)
    values = entry.snapshot.values
    if args.format == "json":
        print(json.dumps(values, indent=2))
    else:
        for k, v in values.items():
            print(f"{k}={v}" if v is not None else f"{k}=")


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.subcommand == "capture":
        run_capture(args)
    elif args.subcommand == "list":
        run_list(args)
    elif args.subcommand == "restore":
        run_restore(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
