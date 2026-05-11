"""CLI entry point for scoring an EnvChain from a .env file."""

import argparse
import json
import sys

from envchain.loader import load_profile_env
from envchain.scorer import score_chain, SCORE_KEYS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-score",
        description="Score environment variable chain health.",
    )
    parser.add_argument("env_file", help="Path to .env file")
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name (default: dev)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-below",
        type=float,
        default=None,
        metavar="THRESHOLD",
        help="Exit with code 1 if overall score is below this value (0.0–1.0)",
    )
    return parser


def run_score(args: argparse.Namespace, out=sys.stdout) -> int:
    chain = load_profile_env(args.env_file, profile=args.profile)
    report = score_chain(chain)

    if args.fmt == "json":
        data = {
            "profile": report.profile,
            "total": report.total,
            "resolved": report.resolved,
            "defaulted": report.defaulted,
            "empty": report.empty,
            "scores": report.scores,
            "overall": report.overall,
        }
        out.write(json.dumps(data, indent=2) + "\n")
    else:
        out.write(f"Profile : {report.profile}\n")
        out.write(f"Total   : {report.total}\n")
        out.write(f"Resolved: {report.resolved}\n")
        out.write(f"Defaulted: {report.defaulted}\n")
        out.write(f"Empty   : {report.empty}\n")
        for key in SCORE_KEYS:
            out.write(f"  {key}: {report.scores[key]:.4f}\n")
        out.write(f"Overall : {report.overall:.4f}\n")

    if args.fail_below is not None and report.overall < args.fail_below:
        return 1
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(run_score(args))


if __name__ == "__main__":
    main()
