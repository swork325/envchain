"""CLI entry-point for running scheduled env validation."""

from __future__ import annotations

import argparse
import signal
import sys
import time

from envchain.auditor import EnvAuditor
from envchain.chain import EnvChain
from envchain.loader import load_profile_env
from envchain.scheduler import EnvScheduler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envchain-schedule",
        description="Run periodic audits against an env file.",
    )
    parser.add_argument("env_file", help="Path to .env file")
    parser.add_argument("--profile", default="dev", help="Profile name (default: dev)")
    parser.add_argument(
        "--interval",
        type=float,
        default=30.0,
        help="Audit interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--require",
        nargs="+",
        metavar="KEY",
        default=[],
        help="Keys that must be present and non-empty",
    )
    return parser


def _make_audit_callback(required: list[str]) -> object:
    def _callback(chain: EnvChain) -> None:
        auditor = EnvAuditor(chain)
        for key in required:
            auditor.add_rule(
                f"{key}_present",
                lambda c, k=key: c.resolve(k) not in (None, ""),
                f"{key} must be present and non-empty",
            )
        report = auditor.audit()
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        status = "PASS" if report.passed else "FAIL"
        print(f"[{ts}] audit={status} profile={chain.profile}")
        if not report.passed:
            for msg in report.failures:
                print(f"  - {msg}")

    return _callback


def run_schedule(args: argparse.Namespace) -> None:
    chain = load_profile_env(args.env_file, args.profile)
    scheduler = EnvScheduler(chain)
    scheduler.add("audit", args.interval, _make_audit_callback(args.require))

    stop = [False]

    def _handle_sigint(sig, frame):  # noqa: ANN001
        stop[0] = True

    signal.signal(signal.SIGINT, _handle_sigint)
    print(f"Scheduler started (interval={args.interval}s). Press Ctrl+C to stop.")
    scheduler.start()
    while not stop[0]:
        time.sleep(0.2)
    scheduler.stop()
    print("Scheduler stopped.")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_schedule(args)


if __name__ == "__main__":
    main()
