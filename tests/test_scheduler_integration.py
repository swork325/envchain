"""Integration tests combining EnvScheduler with auditor and exporter."""

from __future__ import annotations

import threading
import time

from envchain.auditor import EnvAuditor
from envchain.chain import EnvChain
from envchain.exporter import export_chain
from envchain.scheduler import EnvScheduler


def _make_chain(**kwargs: str) -> EnvChain:
    chain = EnvChain(profile="integration")
    for k, v in kwargs.items():
        chain.add(k, v)
    return chain


class TestSchedulerAuditorIntegration:
    def test_audit_results_collected_over_time(self):
        chain = _make_chain(DB_URL="postgres://localhost/db", SECRET="abc")
        results: list[bool] = []
        done = threading.Event()

        def audit_cb(c: EnvChain) -> None:
            auditor = EnvAuditor(c)
            auditor.add_rule(
                "db_present",
                lambda ch: ch.resolve("DB_URL") is not None,
                "DB_URL required",
            )
            report = auditor.audit()
            results.append(report.passed)
            if len(results) >= 2:
                done.set()

        scheduler = EnvScheduler(chain, tick=0.02)
        scheduler.add("audit", 0.05, audit_cb)
        scheduler.start()
        done.wait(timeout=3.0)
        scheduler.stop()

        assert len(results) >= 2
        assert all(results)

    def test_export_called_on_schedule(self):
        chain = _make_chain(PORT="8080")
        exports: list[str] = []
        done = threading.Event()

        def export_cb(c: EnvChain) -> None:
            out = export_chain(c, fmt="dotenv")
            exports.append(out)
            done.set()

        scheduler = EnvScheduler(chain, tick=0.02)
        scheduler.add("export", 0.05, export_cb)
        scheduler.start()
        done.wait(timeout=2.0)
        scheduler.stop()

        assert exports
        assert "PORT" in exports[0]
        assert "8080" in exports[0]

    def test_multiple_entries_run_independently(self):
        chain = _make_chain(A="1", B="2")
        hits: dict[str, int] = {"fast": 0, "slow": 0}
        fast_done = threading.Event()

        def fast_cb(c: EnvChain) -> None:
            hits["fast"] += 1
            if hits["fast"] >= 3:
                fast_done.set()

        def slow_cb(c: EnvChain) -> None:
            hits["slow"] += 1

        scheduler = EnvScheduler(chain, tick=0.02)
        scheduler.add("fast", 0.05, fast_cb)
        scheduler.add("slow", 5.0, slow_cb)
        scheduler.start()
        fast_done.wait(timeout=3.0)
        scheduler.stop()

        assert hits["fast"] >= 3
        assert hits["slow"] <= 1
