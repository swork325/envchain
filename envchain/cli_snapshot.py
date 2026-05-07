"""CLI entry point for snapshot capture and restore operations."""

from __future__ import annotations

import argparse
import sys

from envchain.loader import load_profile_env
from envchain.snapshot import capture, load_snapshot, restore_to_env, save_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-snapshot",
        description="Capture or restore EnvChain snapshots.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="Capture current env values to a snapshot file")
    cap.add_argument("env_file", help="Path to .env file")
    cap.add_argument("output", help="Path to write snapshot JSON")
    cap.add_argument("--profile", default="default", help="Profile label for the snapshot")

    res = sub.add_parser("restore", help="Print export commands from a snapshot")
    res.add_argument("snapshot_file", help="Path to snapshot JSON")
    res.add_argument(
        "--format",
        choices=["shell", "dotenv"],
        default="shell",
        help="Output format",
    )

    return parser


def run_capture(env_file: str, output: str, profile: str) -> None:
    chain = load_profile_env(env_file, profile)
    snap = capture(chain, profile=profile)
    save_snapshot(snap, output)
    print(f"Snapshot saved to {output}  ({len(snap.values)} keys, profile={profile!r})")


def run_restore(snapshot_file: str, fmt: str) -> None:
    snap = load_snapshot(snapshot_file)
    for key, value in snap.values.items():
        if value is None:
            continue
        if fmt == "shell":
            print(f'export {key}="{value}"')
        else:
            print(f"{key}={value}")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "capture":
        run_capture(args.env_file, args.output, args.profile)
    elif args.command == "restore":
        run_restore(args.snapshot_file, args.format)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
