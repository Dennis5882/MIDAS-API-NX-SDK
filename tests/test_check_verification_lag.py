from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _checker_module():
    spec = importlib.util.spec_from_file_location(
        "check_verification_lag_under_test",
        ROOT / "scripts" / "check_verification_lag.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_contract(directory: Path, name: str, endpoint: str, record_ref: str) -> None:
    (directory / name).write_text(
        "\n".join([
            f"endpoint: {endpoint}",
            "verification:",
            "  status: verified_both",
            "  records:",
            "    - product: gen",
            f"      ref: {record_ref}",
            "",
        ]),
        encoding="utf-8",
    )


def test_only_a_write_level_endpoint_citing_no_write_record_counts(tmp_path, monkeypatch) -> None:
    """Three contracts, one lagging: the read-citing one at write level.

    A read-level endpoint citing a read sweep is the truthful state, not drift,
    and a write-level endpoint already citing a write is what this check wants
    more of. Only the pair that disagrees is a finding.
    """
    checker = _checker_module()
    contracts = tmp_path / "endpoints"
    contracts.mkdir()
    _write_contract(contracts, "db-a.yaml", "/db/A", "db-read-sweep-2026-07-26")
    _write_contract(contracts, "db-b.yaml", "/db/B", "db-write-sweep-2026-07-29")
    _write_contract(contracts, "db-c.yaml", "/db/C", "db-read-sweep-2026-07-26")

    coverage = tmp_path / "coverage.json"
    coverage.write_text(json.dumps({"endpoints": [
        {"endpoint": "/db/A", "live_verified": {"level": "write"}},
        {"endpoint": "/db/B", "live_verified": {"level": "write"}},
        {"endpoint": "/db/C", "live_verified": {"level": "read"}},
    ]}), encoding="utf-8")

    monkeypatch.setattr(checker, "CONTRACTS", contracts)
    monkeypatch.setattr(checker, "COVERAGE", coverage)

    assert [endpoint for endpoint, _ in checker.lagging_contracts()] == ["/db/A"]


def test_the_repository_stays_at_or_below_its_recorded_ceiling() -> None:
    """The count may fall -- that is the point -- but never rise silently."""
    checker = _checker_module()
    assert len(checker.lagging_contracts()) <= checker.LAGGING_AT_MOST
