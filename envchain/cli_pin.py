"""CLI for envchain pin/check commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envchain.loader import load_profile_env
from envchain.pinner import check_pins, pin_chain, pins_from_json, pins_to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-pin",
        description="Pin and drift-check environment variable values.",
    )
    parser.add_argument("--env-file", required=True, help="Path to .env file")
    parser.add_argument(
        "--profile",
        default="default",
        help="Profile name (default: default)",
    )

    sub = parser.add_subparsers(dest="subcommand")

    capture_p = sub.add_parser("capture", help="Capture current values to a pin file")
    capture_p.add_argument("--output", required=True, help="Path to write pin JSON")

    check_p = sub.add_parser("check", help="Check current values against a pin file")
    check_p.add_argument("--pins", required=True, help="Path to existing pin JSON")
    check_p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any drift is detected",
    )

    return parser


def run_capture(args: argparse.Namespace) -> None:
    chain = load_profile_env(args.env_file, profile=args.profile)
    pins = pin_chain(chain)
    output_path = Path(args.output)
    output_path.write_text(pins_to_json(pins))
    print(f"Pinned {len(pins)} variable(s) to {output_path}")


def run_check(args: argparse.Namespace) -> None:
    chain = load_profile_env(args.env_file, profile=args.profile)
    raw = Path(args.pins).read_text()
    pins = pins_from_json(raw)
    report = check_pins(chain, pins, profile=args.profile)

    if report.passed:
        print(f"[OK] No drift detected across {len(report.entries)} variable(s).")
    else:
        print(f"[DRIFT] {len(report.drifted)} variable(s) have drifted:")
        for entry in report.drifted:
            print(
                f"  {entry.key}: pinned={entry.pinned_value!r} "
                f"current={entry.current_value!r}"
            )

    if args.strict and not report.passed:
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "capture":
        run_capture(args)
    elif args.subcommand == "check":
        run_check(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
