"""Tests for the derivable npm live-replay coverage report."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "report_npm_replay_coverage_under_test",
        ROOT / "scripts" / "report_npm_replay_coverage.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_report_counts_only_confirmed_fixture_endpoints(tmp_path: Path) -> None:
    module = _module()
    cases = tmp_path / "cases.json"
    coverage = tmp_path / "coverage.json"
    cases.write_text(
        json.dumps({"cases": [
            {"endpoint": "/db/CONFIRMED", "confirmed": True},
            {"endpoint": "/db/UNCONFIRMED", "confirmed": False},
        ]}),
        encoding="utf-8",
    )
    coverage.write_text(
        json.dumps({"endpoints": [
            {
                "endpoint": "/db/CONFIRMED",
                "live_verified": {"method": module.REPLAY_MARKER},
            },
            {
                "endpoint": "/db/UNCONFIRMED",
                "live_verified": {"method": "Python only"},
            },
        ]}),
        encoding="utf-8",
    )

    assert module.report(cases, coverage) == (1, 1, 0, set(), set())


def test_report_rejects_replay_marker_without_confirmed_fixture(tmp_path: Path) -> None:
    module = _module()
    cases = tmp_path / "cases.json"
    coverage = tmp_path / "coverage.json"
    cases.write_text(json.dumps({"cases": []}), encoding="utf-8")
    coverage.write_text(
        json.dumps({"endpoints": [{
            "endpoint": "/db/NO-CASE",
            "live_verified": {"method": module.REPLAY_MARKER},
        }]}),
        encoding="utf-8",
    )

    assert module.report(cases, coverage) == (0, 0, 0, {"/db/NO-CASE"}, set())


def test_report_excludes_an_unconfirmed_case_from_the_gap_denominator(tmp_path: Path) -> None:
    module = _module()
    cases = tmp_path / "cases.json"
    coverage = tmp_path / "coverage.json"
    cases.write_text(
        json.dumps({"cases": [
            {"endpoint": "/db/CONFIRMED", "confirmed": True},
            {"endpoint": "/db/UNCONFIRMED", "confirmed": False},
        ]}),
        encoding="utf-8",
    )
    coverage.write_text(
        json.dumps({"endpoints": [{
            "endpoint": "/db/UNCONFIRMED",
            "live_verified": {"method": module.REPLAY_MARKER},
        }]}),
        encoding="utf-8",
    )

    assert module.report(cases, coverage) == (1, 0, 1, set(), set())


def test_report_flags_a_replay_claim_the_inventory_records_no_session_for(
    tmp_path: Path,
) -> None:
    """A ledger claim is not evidence on its own.

    The fixture check cannot see this: /db/RECORDED and /db/CLAIMED both have a
    confirmed case and both carry the marker. Only the session inventory tells
    them apart, which is how three 2026-09-16 claims went unnoticed until they
    were audited by hand.
    """
    module = _module()
    cases = tmp_path / "cases.json"
    coverage = tmp_path / "coverage.json"
    inventory = tmp_path / "inventory.md"
    cases.write_text(
        json.dumps({"cases": [
            {"endpoint": "/db/RECORDED", "confirmed": True},
            {"endpoint": "/db/CLAIMED", "confirmed": True},
        ]}),
        encoding="utf-8",
    )
    coverage.write_text(
        json.dumps({"endpoints": [
            {"endpoint": "/db/RECORDED",
             "live_verified": {"method": module.REPLAY_MARKER}},
            {"endpoint": "/db/CLAIMED",
             "live_verified": {"method": module.REPLAY_MARKER}},
        ]}),
        encoding="utf-8",
    )
    inventory.write_text(
        """
| Endpoint | Date | Products |
| --- | --- | --- |
| `/db/RECORDED` | 2026-09-16 | Gen, Civil |
""",
        encoding="utf-8",
    )

    assert module.report(cases, coverage, inventory) == (
        2, 2, 0, set(), {"/db/CLAIMED"},
    )
    assert module.main([
        "--cases", str(cases), "--coverage", str(coverage),
        "--inventory", str(inventory), "--check",
    ]) == 1


def test_report_leaves_the_inventory_out_when_it_is_not_given(tmp_path: Path) -> None:
    """report() without an inventory keeps its old meaning, so the fixture
    check stays usable on its own."""
    module = _module()
    cases = tmp_path / "cases.json"
    coverage = tmp_path / "coverage.json"
    cases.write_text(
        json.dumps({"cases": [{"endpoint": "/db/CLAIMED", "confirmed": True}]}),
        encoding="utf-8",
    )
    coverage.write_text(
        json.dumps({"endpoints": [{
            "endpoint": "/db/CLAIMED",
            "live_verified": {"method": module.REPLAY_MARKER},
        }]}),
        encoding="utf-8",
    )

    assert module.report(cases, coverage) == (1, 1, 0, set(), set())
