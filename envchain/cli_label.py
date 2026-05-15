"""CLI entry-point for the *label* sub-system."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envchain.labeler import label_chain
from envchain.loader import load_profile_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-label",
        description="Attach and query metadata labels on environment variables.",
    )
    parser.add_argument("env_file", help="Path to the .env file to load.")
    parser.add_argument(
        "--profile",
        default="dev",
        help="Profile name (default: dev).",
    )
    parser.add_argument(
        "--label",
        dest="labels",
        metavar="KEY=LABEL:VALUE",
        action="append",
        default=[],
        help=(
            "Assign a label to a variable.  "
            "Format: VAR_KEY=label_name:label_value  "
            "(repeatable)"
        ),
    )
    parser.add_argument(
        "--filter-label",
        metavar="LABEL:VALUE",
        default=None,
        help="Print only variables whose LABEL equals VALUE.",
    )
    return parser


def _parse_label_args(raw: List[str]) -> dict:
    """Convert ``["DB_URL=tier:database", ...]`` into a nested rules dict."""
    rules: dict = {}
    for item in raw:
        var_key, rest = item.split("=", 1)
        label_name, label_value = rest.split(":", 1)
        rules.setdefault(var_key, {})[label_name] = label_value
    return rules


def run_label(args: argparse.Namespace) -> None:
    chain = load_profile_env(args.env_file, args.profile)
    rules = _parse_label_args(args.labels)
    report = label_chain(chain, rules)

    entries = report.entries
    if args.filter_label:
        label_name, label_value = args.filter_label.split(":", 1)
        entries = report.where(label_name, label_value)

    output = [
        {"key": e.var.key, "value": e.var.default, "labels": e.labels}
        for e in entries
    ]
    print(json.dumps(output, indent=2))


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)
    run_label(args)


if __name__ == "__main__":  # pragma: no cover
    main()
