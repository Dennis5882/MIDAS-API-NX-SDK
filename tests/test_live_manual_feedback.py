"""Regression checks for the manual-maintainer live probe payloads."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manual_feedback_variants_change_only_the_requested_fields() -> None:
    """Import the live runner out-of-process so its fixture classes cannot leak."""
    code = r'''
import copy
import sys
sys.path.insert(0, "scripts")
import live_manual_feedback as feedback

cases = {label: payload for label, _, payload in feedback._tdna_radius_cases()}
two_d_expected = copy.deepcopy(cases["2d-number"])
two_d_expected["PROFY"][1]["RADIUS"] = False
assert cases["2d-boolean"] == two_d_expected
three_d_expected = copy.deepcopy(cases["3d-number"])
three_d_expected["PROF"][1]["RADIUS"] = [0, 20]
assert cases["3d-array"] == three_d_expected
assert [item["RADIUS"] for item in cases["2d-number"]["PROFY"]] == [0, 20, 0]
assert [item["RADIUS"] for item in cases["2d-number"]["PROFZ"]] == [0, 20, 0]
assert [item["RADIUS"] for item in cases["3d-number"]["PROF"]] == [0, 20, 0]

baseline = feedback._matd_payload()
for key, value in (("bSERVCHECK", True), ("dSHORTTERM", 1.25),
                   ("dLONGTERM", 1.5)):
    assert feedback._matd_payload(**{key: value}) == dict(baseline, **{key: value})

assert feedback._splc_along_payload(2.5)["aACCECC_ECCEN_LIST"] == [
    {"STORY": "2F", "CROSS": 1.5, "ALONG": 2.5},
]
'''
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
