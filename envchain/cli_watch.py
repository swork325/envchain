"""CLI entry point for the envchain watch command."""

from __future__ import annotations

import argparse
import signal
import sys
from typing import List

from envchain.loader import load_profile_env
from envchain.watcher import ChangeEvent, EnvWatcher


def _format_events(events: List[ChangeEvent]) -> str:
    lines = []
    for e in events:
        if e.is_added:
            lines.append(f"  [+] {e.key} = {e.new_value!r}")
        elif e.is_removed:
            lines.append(f"  [-] {e.key} (was {e.old_value!r})")
        else:
            lines.append(f"  [~] {e.key}: {e.old_value!r} -> {e.new_value!r}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-watch",
        description="Watch an env file for variable changes.",
    )
    parser.add_argument("env_file", help="Path to the .env file to watch")
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name to load (default: dev)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Poll interval in seconds (default: 2.0)",
    )
    return parser


def run_watch(env_file: str, profile: str, interval: float) -> None:
    chain = load_profile_env(env_file, profile)
    watcher = EnvWatcher(chain, interval=interval)

    def _on_change(events: List[ChangeEvent]) -> None:
        print(f"[envchain-watch] {len(events)} change(s) detected:")
        print(_format_events(events))

    watcher.on_change(_on_change)
    print(f"[envchain-watch] Watching {env_file!r} (profile={profile!r}, interval={interval}s)")
    print("[envchain-watch] Press Ctrl+C to stop.")

    def _handle_sigint(sig, frame):  # noqa: ANN001
        print("\n[envchain-watch] Stopped.")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_sigint)
    watcher.start()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_watch(args.env_file, args.profile, args.interval)


if __name__ == "__main__":
    main()
