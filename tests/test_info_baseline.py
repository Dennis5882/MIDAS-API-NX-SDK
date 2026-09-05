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


def _established_divergence() -> tuple[int, int, dict[str, int], dict[str, int]]:
    expected = info_baseline.EXPECTED_DIVERGENCE
    return (
        expected["endpointsAnsweringBothAtLeast"],
        expected["divergentSchemasAtMost"],
        {},
        dict(expected["absentFieldsAtMost"]),
    )


def _run_divergence_check(
    counts: tuple[int, int, dict[str, int], dict[str, int]],
) -> int:
    both, different, untagged, absent = counts
    return info_baseline._check_divergence(
        both=both,
        different=different,
        untagged=untagged,
        absent=absent,
    )


def test_divergence_check_accepts_established_counts() -> None:
    assert _run_divergence_check(_established_divergence()) == 0


def test_divergence_check_accepts_repaired_absent_fields() -> None:
    both, different, untagged, absent = _established_divergence()
    absent["/db/SPLC"] -= 1

    assert _run_divergence_check((both, different, untagged, absent)) == 0


def test_divergence_check_rejects_an_untagged_field(
    capsys: pytest.CaptureFixture[str],
) -> None:
    both, different, untagged, absent = _established_divergence()
    untagged["/db/ACTL"] = 1

    assert _run_divergence_check((both, different, untagged, absent)) == 1
    captured = capsys.readouterr()
    assert "untagged product-specific fields for /db/ACTL must be 0, found 1" in captured.err
