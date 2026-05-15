"""CLI entry point for comparing two .env files as EnvChains."""

from __future__ import annotations

import argparse
import json
import sys

from envchain.loader import load_profile_env
from envchain.comparator import compare_chains


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-compare",
        description="Compare two .env files key-by-key.",
    )
    parser.add_argument("left", help="Path to the left .env file")
    parser.add_argument("right", help="Path to the right .env file")
    parser.add_argument(
        "--left-profile",
        default="dev",
        metavar="PROFILE",
        help="Profile name for the left file (default: dev)",
    )
    parser.add_argument(
        "--right-profile",
        default="prod",
        metavar="PROFILE",
        help="Profile name for the right file (default: prod)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return parser


def run_compare(args: argparse.Namespace, out=sys.stdout) -> int:
    left_chain = load_profile_env(args.left, profile=args.left_profile)
    right_chain = load_profile_env(args.right, profile=args.right_profile)
    report = compare_chains(left_chain, right_chain)

    if args.format == "json":
        data = {
            "left_profile": report.left_profile,
            "right_profile": report.right_profile,
            "is_identical": report.is_identical,
            "equal": report.equal_keys,
            "diverged": report.diverged_keys,
            "only_in_left": report.only_in_left,
            "only_in_right": report.only_in_right,
        }
        out.write(json.dumps(data, indent=2) + "\n")
    else:
        out.write(
            f"Comparing {report.left_profile!r} vs {report.right_profile!r}\n"
        )
        if report.is_identical:
            out.write("  Chains are identical.\n")
        else:
            for key in report.diverged_keys:
                out.write(f"  ~ {key} (diverged)\n")
            for key in report.only_in_left:
                out.write(f"  < {key} (only in left)\n")
            for key in report.only_in_right:
                out.write(f"  > {key} (only in right)\n")
        out.write(
            f"  equal={len(report.equal_keys)}, "
            f"diverged={len(report.diverged_keys)}, "
            f"only_left={len(report.only_in_left)}, "
            f"only_right={len(report.only_in_right)}\n"
        )

    return 0 if report.is_identical else 1


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_compare(args))


if __name__ == "__main__":  # pragma: no cover
    main()
