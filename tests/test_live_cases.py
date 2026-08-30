"""The npm live harness must consume the current Python case fixture."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "schema" / "live-cases.json"


def test_live_case_fixture_matches_python_source() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/live_crud_check.py", "--check-cases"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_live_case_fixture_carries_confirmed_nmas_setup() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    nmas = next(case for case in cases if case["endpoint"] == "/db/NMAS")

    assert nmas["confirmed"] is True
    assert nmas["createPayload"] == {"mX": 1.0, "mY": 1.0, "mZ": 1.0}
    assert nmas["setup"] == [{"endpoint": "/db/NODE", "id": 3}]
