"""Run the design *functions* on a solved scratch model and check their files.

Live, destructive: saves the open document to ``--save-dir`` and then sends
``/doc/NEW``. Gen NX only. Civil refuses the RC and steel design-code
selections, and ``CD-ANAL`` with analysis results and no RC design code
killed Civil on 2026-09-29 (``design-rc-cd-anal-without-design-code-kills-civil``).

The model is the CRUD harness's base model with its unsupported plate removed,
plus a steel column built from the ``ltsr_material``/``ltsr_section`` seeds.
Every record comes from ``schema/live-cases.json`` - the base model, seeds and
confirmed case payloads - so nothing here is hand-written; the design-function
arguments are each manual article's own request example with the element
numbers and output path replaced.

Each ``*-REPORT`` (and each ``*-TABLE`` given an ``EXPORT_PATH``) is checked
by listing ``--report-dir`` before and after the call. That works only when
this script runs on the NX host, which ``--report-dir`` asserts: it must be a
local directory, and its path is sent as ``EXPORT_PATH``.

    python scripts/live_design_functions.py --save-dir C:/temp --report-dir C:/temp/midas-nx-design
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from harness_save_path import (  # noqa: E402
    add_arguments,
    analyze_saved,
    checkpoint,
    require,
)

from midas_nx import MidasClient, doc  # noqa: E402
from midas_nx.client import MidasAPIError  # noqa: E402
from midas_nx.design import steel_kds  # noqa: E402
from midas_nx.design.rc_kds import design_forces  # noqa: E402
from midas_nx.post.base import get_table  # noqa: E402

FIXTURE = ROOT / "schema" / "live-cases.json"
RC = "/DESIGN/RC/KDS-41-20-2022"
STEEL = "/DESIGN/STEEL/KDS-41-30-2022"

COLUMN, BEAM, BRACE, STEEL_COLUMN = 1, 2, 3, 11


def _fixture() -> Dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _case(fixture: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
    for case in fixture["cases"]:
        if case["endpoint"] == endpoint and "gen" in case["products"] and case["confirmed"]:
            return case
    raise SystemExit(f"no confirmed Gen case for {endpoint}")


def build_model(client: MidasClient, fixture: Dict[str, Any]) -> List[Tuple[str, Any]]:
    log: List[Tuple[str, Any]] = []

    def send(method: str, endpoint: str, records: Dict[Any, Any]) -> None:
        body = {"Assign": {str(k): v for k, v in records.items()}}
        log.append((f"{method} {endpoint}", client.request(method, endpoint, body)))

    for step in fixture["baseModel"]:
        send(step["method"], step["endpoint"], step["records"])
    # The plate's corners are unsupported; a solve needs it gone.
    log.append(("DELETE /db/ELEM/4", client.request("DELETE", "/db/ELEM/4")))
    seeds = fixture["seeds"]
    steel = copy.deepcopy(seeds["ltsr_material"]["records"]["1"])
    section = copy.deepcopy(seeds["ltsr_section"]["records"]["1"])
    send("POST", "/db/MATL", {STEEL_COLUMN: steel})
    send("POST", "/db/SECT", {STEEL_COLUMN: section})
    send("POST", "/db/NODE", {11: {"X": 0, "Y": 5, "Z": 0}, 12: {"X": 0, "Y": 5, "Z": 3.2}})
    send("POST", "/db/ELEM", {STEEL_COLUMN: {"TYPE": "BEAM", "MATL": STEEL_COLUMN,
                                             "SECT": STEEL_COLUMN, "NODE": [11, 12]}})
    base_cons = fixture["baseModel"][next(i for i, s in enumerate(fixture["baseModel"])
                                          if s["endpoint"] == "/db/CONS")]["records"]["1"]
    cons = copy.deepcopy(base_cons)
    send("POST", "/db/CONS", {11: cons})
    for endpoint in (f"{RC}/DCO", f"{STEEL}/DCO", "/db/LCOM-CONC", "/db/LCOM-STEEL"):
        case = _case(fixture, endpoint)
        method = "PUT" if "POST" not in case["methods"] else "POST"
        send(method, endpoint, {case["id"]: case["createPayload"]})
    rc_mbtp = _case(fixture, f"{RC}/MBTP")
    method = "PUT" if "POST" not in rc_mbtp["methods"] else "POST"
    send(method, f"{RC}/MBTP", {COLUMN: {"TYPE": "COLUMN"}, BEAM: {"TYPE": "BEAM"},
                                BRACE: {"TYPE": "BRACE"}})
    steel_mbtp = _case(fixture, f"{STEEL}/MBTP")
    method = "PUT" if "POST" not in steel_mbtp["methods"] else "POST"
    send(method, f"{STEEL}/MBTP", {STEEL_COLUMN: {"TYPE": "COLUMN"}})
    return log


def _listing(directory: Path) -> Dict[str, Tuple[int, float]]:
    return {p.name: (p.stat().st_size, p.stat().st_mtime) for p in directory.iterdir() if p.is_file()}


def _call(name: str, func: Callable[[], Any], report_dir: Path) -> Dict[str, Any]:
    before = _listing(report_dir)
    started = time.time()
    try:
        response: Any = func()
        error = None
    except MidasAPIError as exc:
        response, error = None, f"{type(exc).__name__}: {exc}"
    after = _listing(report_dir)
    new = {k: v[0] for k, v in after.items() if k not in before or v != before[k]}
    return {"call": name, "seconds": round(time.time() - started, 1),
            "response": response, "error": error, "new_files": new}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--mapi-key", default=os.getenv("MIDAS_MAPI_KEY"))
    # No waiver: the model is saved before its analysis whatever happens, so
    # a directory is needed either way (see harness_save_path).
    add_arguments(parser, waivable=False)
    parser.add_argument("--report-dir", required=True)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--out")
    args = parser.parse_args()
    require(parser, args)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    export = str(report_dir).replace("/", "\\").rstrip("\\") + "\\"

    client = MidasClient(mapi_key=args.mapi_key, product="gen", timeout=args.timeout)
    alive = lambda: client.request("GET", "/db/NODE", timeout=30)  # noqa: E731
    print("open document:", str(alive())[:80])
    print("checkpoint:", doc.save_as(checkpoint(args.save_dir, "midas-nx-design", "gen"), client=client))
    print("new:", doc.new_project(client=client))

    fixture = _fixture()
    results: List[Dict[str, Any]] = []
    for step, response in build_model(client, fixture):
        print(f"  {step}: {str(response)[:120]}")
    print("analysis:", analyze_saved(client, args.save_dir, "midas-nx-design-model", "gen"))
    print("alive:", str(alive())[:60])

    elems = lambda n: {"KEYS": [n]}  # noqa: E731
    calls: List[Tuple[str, Callable[[], Any]]] = [
        ("RC BD-ANAL", lambda: design_forces.perform_beam_design(
            {"PERFORM_TYPE": "ELEMS", "ELEMS": elems(BEAM)}, client=client)),
        ("RC CD-ANAL", lambda: design_forces.perform_column_design(
            {"PERFORM_TYPE": "ELEMS", "ELEMS": elems(COLUMN)}, client=client)),
        ("RC BRD-ANAL", lambda: design_forces.perform_brace_design(
            {"PERFORM_TYPE": "ELEMS", "ELEMS": elems(BRACE)}, client=client)),
        ("STEEL CODE-ANAL", lambda: steel_kds.perform_steel_code_check(
            {"PERFORM_TYPE": "ELEMS", "ELEMS": elems(STEEL_COLUMN)}, client=client)),
    ]
    for code, elem, table in (("BD", BEAM, design_forces.get_beam_design_table),
                              ("CD", COLUMN, design_forces.get_column_design_table),
                              ("BRD", BRACE, design_forces.get_brace_design_table)):
        calls.append((f"RC {code}-TABLE", lambda t=table, e=elem: t(
            {"TABLE_TYPE": "MEMB", "ELEMS": elems(e)}, client=client)))
        calls.append((f"RC {code}-TABLE +EXPORT_PATH", lambda t=table, e=elem, c=code: t(
            {"TABLE_TYPE": "MEMB", "ELEMS": elems(e),
             "EXPORT_PATH": f"{export}{c.lower()}-table.json"}, client=client)))
    calls.append(("STEEL CODE-TABLE", lambda: steel_kds.get_steel_code_check_table(
        {"TABLE_TYPE": "MEMB", "ELEMS": elems(STEEL_COLUMN)}, client=client)))
    calls.append(("STEEL CODE-TABLE +EXPORT_PATH", lambda: steel_kds.get_steel_code_check_table(
        {"TABLE_TYPE": "MEMB", "ELEMS": elems(STEEL_COLUMN),
         "EXPORT_PATH": f"{export}code-table.json"}, client=client)))
    calls += [
        ("POST TABLE MATERIAL +EXPORT_PATH", lambda: get_table(
            "MATERIAL", "Example", export_path=f"{export}material-table.json", client=client)),
        ("POST TABLE REACTIONG +EXPORT_PATH", lambda: get_table(
            "REACTIONG", "Example", export_path=f"{export}reaction-table.json",
            node_elems={"KEYS": [1]}, load_case_names=["DL(ST)"], client=client)),
        ("RC BD-REPORT", lambda: design_forces.export_beam_design_report(
            {"REPORT_TYPE": "MEMB", "CURRENT_MODE_MEMB": "Graphic", "EXPORT_PATH": export,
             "OUTPUT_NAME": "bd-report.jpg", "ELEMS": elems(BEAM)}, client=client)),
        ("RC CD-REPORT", lambda: design_forces.export_column_design_report(
            {"REPORT_TYPE": "MEMB", "CURRENT_MODE_MEMB": "Graphic", "EXPORT_PATH": export,
             "OUTPUT_NAME": "cd-report.jpg", "ELEMS": elems(COLUMN)}, client=client)),
        ("RC BRD-REPORT", lambda: design_forces.export_brace_design_report(
            {"REPORT_TYPE": "MEMB", "CURRENT_MODE_MEMB": "Graphic", "EXPORT_PATH": export,
             "OUTPUT_NAME": "brd-report.jpg", "ELEMS": elems(BRACE)}, client=client)),
        ("STEEL CODE-REPORT", lambda: steel_kds.export_steel_code_check_report(
            {"REPORT_TYPE": "MEMB", "CURRENT_MODE": "Graphic", "EXPORT_PATH": export,
             "OUTPUT_NAME": "code-report.jpg", "ELEMS": elems(STEEL_COLUMN)}, client=client)),
    ]
    for name, func in calls:
        result = _call(name, func, report_dir)
        results.append(result)
        print(f"{name}: {result['seconds']}s error={result['error']} "
              f"response={str(result['response'])[:160]} new_files={result['new_files']}")
        print("  alive:", str(alive())[:40])

    print("saved scratch:", doc.save_as(
        checkpoint(args.save_dir, "midas-nx-design-after", "gen"), client=client))
    print("new:", doc.new_project(client=client))
    if args.out:
        Path(args.out).write_text(json.dumps(results, ensure_ascii=False, indent=1, default=str),
                                  encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
