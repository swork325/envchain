"""CLI entry point for the summarize command."""

from __future__ import annotations

import argparse
import json
import sys

from envchain.loader import load_profile_env
from envchain.summarizer import summarize_chain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-summarize",
        description="Summarize the state of environment variables in a profile.",
    )
    parser.add_argument("env_file", help="Path to the .env file to load")
    parser.add_argument(
        "--profile",
        default="default",
        help="Profile name to use (default: 'default')",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text)",
    )
    return parser


def run_summarize(args: argparse.Namespace, out=sys.stdout) -> None:
    chain = load_profile_env(args.env_file, profile=args.profile)
    report = summarize_chain(chain)

    if args.output_format == "json":
        out.write(json.dumps(report.to_dict(), indent=2))
        out.write("\n")
    else:
        out.write(f"Profile : {report.profile}\n")
        out.write(f"Total   : {report.total}\n")
        out.write(f"Resolved: {report.resolved}\n")
        out.write(f"Defaulted: {report.defaulted}\n")
        out.write(f"Missing : {report.missing}\n")
        if report.missing_keys:
            out.write("Missing keys:\n")
            for key in report.missing_keys:
                out.write(f"  - {key}\n")


def main(argv=None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)
    run_summarize(args)


if __name__ == "__main__":  # pragma: no cover
    main()
