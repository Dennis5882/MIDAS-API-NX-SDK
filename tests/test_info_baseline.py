from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import info_baseline  # noqa: E402


def _established_counts() -> tuple[int, int, int, dict[str, int], dict[str, int]]:
    expected = info_baseline.EXPECTED_AGAINST_CONTRACTS
    return (
        expected["contractsComparedAtLeast"],
        expected["unmergedTablesSkippedAtMost"],
        expected["infoOnlyWaiversAtMost"],
        dict(expected["unrecordedInfoPropertiesAtMost"]),
        dict(expected["contractOnlyNamesAtMost"]),
    )


def _run_check(
    counts: tuple[int, int, int, dict[str, int], dict[str, int]],
) -> int:
    compared, skipped, waived, unrecorded, contract_only = counts
    return info_baseline._check_against_contracts(
        compared=compared,
        skipped=skipped,
        waived=waived,
        unrecorded=unrecorded,
        contract_only=contract_only,
    )


def test_against_contracts_check_accepts_established_counts() -> None:
    assert _run_check(_established_counts()) == 0


def test_against_contracts_check_accepts_a_repaired_difference() -> None:
    compared, skipped, waived, unrecorded, contract_only = _established_counts()
    unrecorded["/db/SECT"] -= 1
    contract_only.pop("/db/STBK")

    assert _run_check((compared, skipped, waived, unrecorded, contract_only)) == 0


def test_against_contracts_check_rejects_growth_per_endpoint(
    capsys: pytest.CaptureFixture[str],
) -> None:
    compared, skipped, waived, unrecorded, contract_only = _established_counts()
    unrecorded["/db/NEW"] = 1

    counts = (compared, skipped, waived, unrecorded, contract_only)
    assert _run_check(counts) == 1
    captured = capsys.readouterr()
    assert "unrecorded /info properties for /db/NEW grew from 0 to 1" in captured.err
