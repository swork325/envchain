"""CLI entry point for the envchain trace command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from .loader import load_profile_env
from .tracer import TraceReport, trace_all, trace_key


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-trace",
        description="Trace environment variable resolution across profiles.",
    )
    parser.add_argument(
        "env_files",
        nargs="+",
        metavar="ENV_FILE",
        help="One or more .env files to trace across (in order).",
    )
    parser.add_argument(
        "--key",
        metavar="KEY",
        help="Trace a single key instead of all keys.",
    )
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name to use when loading each file (default: dev).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def _report_to_dict(report: TraceReport) -> dict:
    return {
        "key": report.key,
        "first_resolved": (
            report.first_resolved().profile if report.first_resolved() else None
        ),
        "steps": [
            {
                "profile": s.profile,
                "source": s.source,
                "value": s.value,
            }
            for s in report.steps
        ],
    }


def _print_text(reports: List[TraceReport]) -> None:
    for report in reports:
        first = report.first_resolved()
        status = f"first resolved in '{first.profile}'" if first else "UNRESOLVED"
        print(f"{report.key}: {status}")
        for step in report.steps:
            marker = "*" if step.source != "missing" else " "
            print(f"  [{marker}] {step.profile}: {step.source} = {step.value!r}")


def run_trace(args: argparse.Namespace) -> None:
    chains = []
    for i, path in enumerate(args.env_files):
        profile = f"{args.profile}-{i}" if len(args.env_files) > 1 else args.profile
        chain = load_profile_env(path, profile=profile)
        chains.append(chain)

    if args.key:
        reports = [trace_key(args.key, chains)]
    else:
        reports = trace_all(chains)

    if args.format == "json":
        print(json.dumps([_report_to_dict(r) for r in reports], indent=2))
    else:
        _print_text(reports)


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run_trace(args)
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
