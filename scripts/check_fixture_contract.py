"""Check every live CRUD fixture against the contract for its endpoint.

The repository already compares contracts against both SDKs, against `/info`,
and against the manual.  Nothing compared them against the **fixtures**, which
is the fourth thing that claims to know an endpoint's shape -- and the one that
decides what a live run actually sends.  Its first run found 118 disagreements,
and they divide into two opposite kinds.

**54 across 8 endpoints are on cases nobody has watched pass**, where the
payload is the suspect: `/db/ACTL` sends `CLATS` on Gen, a field the contract
tags Civil-only; `/db/FBLA` sends `LOAD_ANGLE`, a name no contract records
anywhere; `/db/MVCT`, `/db/NLNK`, `/db/NLNK-M1` and `/db/TDMF` omit fields
their contracts mark **required**.  Every one had failed live for months under
a recorded reason that never mentioned the payload's own shape.

**64 across 18 endpoints are on `confirmed` cases**, and those read the other
way round.  The product accepted that exact payload, so the contract is what is
behind: a name it records nowhere is a field it is missing, and a `required`
field the accepted call omitted is a requirement the product does not enforce.
The second kind is the more valuable of the two -- only 119 of 4,916 fields
have a proven `safeToOmit`, and these are 64 live observations sitting unread.

Three things are checked per case, per product it declares:

1. a key the contract tags for the *other* product only;
2. a `required` key the payload omits;
3. a key no contract field records -- unless an `extraction.unmergedTables`
   entry lists it, which is the same per-name waiver `check_field_parity` uses.
   A declared gap is a gap; a name in neither place is a defect.

Only top-level keys are compared.  Most contracts do not itemise nested
members, so descending would report the contract's own known gaps as fixture
defects, which is the opposite of useful.

    python scripts/check_fixture_contract.py            # report
    python scripts/check_fixture_contract.py --check    # exit 1 on a new one

`--check` holds both lists as a recorded baseline.  A finding that goes away
fails too, so a fix has to be recorded rather than absorbed.  Fix the fixture
rather than widening the baseline; and closing a contract gap takes a permitted
source -- the manual, `/info`, or a recorded live observation.  **A fixture is
never a source for a contract**, which is why these are held here and not
merged.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Dict, List, Set, Tuple

import yaml

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "schema" / "live-cases.json"
CONTRACTS = ROOT / "contracts" / "endpoints"

#: What the first run found, endpoint -> sorted list of "kind: key" strings.
#: These are live-reproduced fixture defects, not exemptions: each one has a
#: failing case behind it and belongs to Task 4's write-coverage push. Removing
#: an entry is the goal; adding one needs the same standard of evidence.
#: What the current tree reports, split the way scan() splits it.
#:
#: KNOWN is the fixture side: cases nobody has watched pass whose payload the
#: contract does not license. Each is a lead for Task 4's write-coverage push,
#: not an exemption -- removing an entry is the goal.
#:
#: KNOWN_CONTRACT_GAPS is the other side, and reads the opposite way: the
#: product accepted these payloads, so the contract is what is behind. Closing
#: one takes a permitted source -- the manual, /info, or a recorded live
#: observation. A fixture is never a source for a contract, which is why these
#: are held here rather than merged.
KNOWN: Dict[str, List[str]] = {'/db/ACTL': ['gen: sends CLATS, tagged civil-only'],
 '/db/FBLA': ['civil: sends LOAD_ANGLE, recorded nowhere',
              'gen: sends LOAD_ANGLE, recorded nowhere'],
 '/db/GRDP': ['civil: omits required DAMPING_MODE_1_DEFAULT',
              'civil: omits required DAMPING_MODE_2_DEFAULT',
              'civil: omits required DIRECT_CALC_MODE_DEFAULT',
              'civil: omits required ELEM_GROUP_PRIORITY',
              'civil: omits required ELEM_VALUE_PRIORITY',
              'civil: omits required FREQ_MODE_1_DEFAULT',
              'civil: omits required FREQ_MODE_2_DEFAULT',
              'civil: omits required FREQ_PERIOD_MODE_DEFAULT',
              'civil: omits required GROUP_DAMPING_ITEMS',
              'civil: omits required PERIOD_MODE_1_DEFAULT',
              'civil: omits required PERIOD_MODE_2_DEFAULT',
              'civil: omits required STRAIN_GROUP_PRIORITY',
              'civil: omits required STRAIN_VALUE_PRIORITY',
              'civil: omits required bExistElement',
              'gen: omits required DAMPING_MODE_1_DEFAULT',
              'gen: omits required DAMPING_MODE_2_DEFAULT',
              'gen: omits required DIRECT_CALC_MODE_DEFAULT',
              'gen: omits required ELEM_GROUP_PRIORITY',
              'gen: omits required ELEM_VALUE_PRIORITY',
              'gen: omits required FREQ_MODE_1_DEFAULT',
              'gen: omits required FREQ_MODE_2_DEFAULT',
              'gen: omits required FREQ_PERIOD_MODE_DEFAULT',
              'gen: omits required GROUP_DAMPING_ITEMS',
              'gen: omits required PERIOD_MODE_1_DEFAULT',
              'gen: omits required PERIOD_MODE_2_DEFAULT',
              'gen: omits required STRAIN_GROUP_PRIORITY',
              'gen: omits required STRAIN_VALUE_PRIORITY',
              'gen: omits required bExistElement'],
 '/db/MVCT': ['civil: omits required DIST', 'gen: omits required DIST'],
 '/db/NLCT': ['civil: sends MAX_ITERATIONS, recorded nowhere',
              'civil: sends NEWTON_ITEMS, recorded nowhere',
              'civil: sends NUMBER_STEPS, recorded nowhere'],
 '/db/NLNK': ['civil: omits required ANGLE_VALUES',
              'civil: omits required INPUT_METHOD',
              'civil: omits required POINT_VALUES',
              'civil: omits required VECTOR_VALUES',
              'gen: omits required ANGLE_VALUES',
              'gen: omits required INPUT_METHOD',
              'gen: omits required POINT_VALUES',
              'gen: omits required VECTOR_VALUES'],
 '/db/NLNK-M1': ['civil: omits required ANGLE_VALUES',
                 'civil: omits required BETA_ANGLE',
                 'civil: omits required INPUT_METHOD',
                 'civil: omits required POINT_VALUES',
                 'civil: omits required REF_SYSTEM',
                 'civil: omits required VECTOR_VALUES'],
 '/db/TDMF': ['civil: omits required CTYPE',
              'civil: omits required RELAXATION',
              'gen: omits required CTYPE',
              'gen: omits required RELAXATION']}

KNOWN_CONTRACT_GAPS: Dict[str, List[str]] = {'/db/CCFC': ['civil: omits required ITEM',
              'civil: omits required SCALE_FACTOR',
              'gen: omits required ITEM',
              'gen: omits required SCALE_FACTOR'],
 '/db/EIGV': ['civil: sends FRMAX, recorded nowhere',
              'civil: sends FRMIN, recorded nowhere',
              'civil: sends bMINMAX, recorded nowhere',
              'civil: sends bSTRUM, recorded nowhere',
              'civil: sends iFREQ, recorded nowhere',
              'gen: sends FRMAX, recorded nowhere',
              'gen: sends FRMIN, recorded nowhere',
              'gen: sends bMINMAX, recorded nowhere',
              'gen: sends bSTRUM, recorded nowhere',
              'gen: sends iFREQ, recorded nowhere'],
 '/db/EIGV-M1': ['civil: sends FREQ_NO, recorded nowhere',
                 'civil: sends FREQ_RANGE, recorded nowhere'],
 '/db/ETFC': ['civil: omits required ITEM',
              'civil: omits required SCALE_FACTOR',
              'gen: omits required ITEM',
              'gen: omits required SCALE_FACTOR'],
 '/db/HHCT-M1': ['civil: omits required ITEM',
                 'civil: omits required SELF_WEIGHT_FACTOR',
                 'civil: omits required STAGE_NAME'],
 '/db/HSFC': ['civil: omits required ITEM',
              'civil: omits required SCALE_FACTOR',
              'gen: omits required ITEM',
              'gen: omits required SCALE_FACTOR'],
 '/db/NBOF': ['civil: sends KEY_NODE_ITEMS, recorded nowhere',
              'gen: sends KEY_NODE_ITEMS, recorded nowhere'],
 '/db/NLCT': ['gen: sends MAX_ITERATIONS, recorded nowhere',
              'gen: sends NEWTON_ITEMS, recorded nowhere',
              'gen: sends NUMBER_STEPS, recorded nowhere'],
 '/db/PNLA': ['civil: omits required LOAD_GROUP', 'gen: omits required LOAD_GROUP'],
 '/db/PNLD': ['civil: sends AREALOAD, recorded nowhere',
              'gen: sends AREALOAD, recorded nowhere'],
 '/db/SDIS': ['gen: omits required LRB', 'gen: omits required NRB'],
 '/db/SMLC': ['civil: omits required KEY', 'gen: omits required KEY'],
 '/db/STAG': ['civil: omits required INCRE_STEP', 'gen: omits required INCRE_STEP'],
 '/db/TDMT': ['civil: omits required VOL', 'gen: omits required VOL'],
 '/db/THFC': ['civil: omits required CONS_A',
              'civil: omits required CONS_C',
              'civil: omits required DAMP_FACTOR',
              'civil: omits required FREQUENCY',
              'civil: omits required PHASE_ANGLE',
              'gen: omits required CONS_A',
              'gen: omits required CONS_C',
              'gen: omits required DAMP_FACTOR',
              'gen: omits required FREQUENCY',
              'gen: omits required PHASE_ANGLE'],
 '/db/THIS': ['civil: sends DALL, recorded nowhere',
              'gen: sends DALL, recorded nowhere'],
 '/db/TSGR': ['civil: omits required YEXP',
              'civil: omits required ZEXP',
              'gen: omits required YEXP',
              'gen: omits required ZEXP'],
 '/db/ULFC': ['civil: omits required LB_VALUE',
              'civil: omits required UB_VALUE',
              'gen: omits required LB_VALUE',
              'gen: omits required UB_VALUE']}

BOTH = ("civil", "gen")


def _contracts() -> Dict[str, dict]:
    found: Dict[str, dict] = {}
    for path in sorted(CONTRACTS.glob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(document, dict) and document.get("endpoint"):
            found[document["endpoint"]] = document
    return found


def _waived_names(document: dict) -> Set[str]:
    """Names an `extraction.unmergedTables` entry accounts for."""
    waived: Set[str] = set()
    extraction = document.get("extraction") or {}
    for table in extraction.get("unmergedTables") or []:
        waived.update(table.get("fieldNames") or [])
    for field in document.get("fields") or []:
        if field.get("sdkOnly"):
            waived.add(field["key"])
    return waived


def _findings(case: dict, document: dict) -> List[str]:
    fields = document.get("fields") or []
    recorded = {field["key"] for field in fields}
    waived = _waived_names(document)
    keys = set(case["createPayload"]) | set(case["updatePayload"])
    out: List[str] = []

    for product in sorted(case["products"]):
        for field in fields:
            products = field.get("products") or list(BOTH)
            if product not in products and field["key"] in keys:
                other = "/".join(sorted(products))
                out.append(f"{product}: sends {field['key']}, tagged {other}-only")
            if (field.get("requirement") == "required"
                    and product in products and field["key"] not in keys):
                out.append(f"{product}: omits required {field['key']}")
        for key in sorted(keys - recorded - waived):
            out.append(f"{product}: sends {key}, recorded nowhere")
    return sorted(set(out))


def scan() -> Tuple[Dict[str, List[str]], Dict[str, List[str]], int]:
    """Findings split by whether the case has ever passed live.

    The same disagreement means opposite things on the two sides. On a case
    nobody has watched pass, a payload the contract does not license is a lead
    about the **fixture**. On a `confirmed` case, the product accepted that
    exact payload, so the disagreement is evidence about the **contract**: a
    name it records nowhere is a field it is missing, and a `required` field
    the call omitted is a requirement the product does not enforce -- which is
    exactly what `safeToOmit` wants and only 119 of 4,916 fields have.

    Neither list is actionable by itself. A contract is fixed from a permitted
    source, never from a fixture.
    """
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    documents = _contracts()
    unconfirmed: Dict[str, List[str]] = {}
    confirmed: Dict[str, List[str]] = {}
    checked = 0
    for case in fixture["cases"]:
        document = documents.get(case["endpoint"])
        if not document:
            continue
        checked += 1
        found = _findings(case, document)
        if not found:
            continue
        into = confirmed if case["confirmed"] else unconfirmed
        into[case["endpoint"]] = sorted(set(into.get(case["endpoint"], [])) | set(found))
    return unconfirmed, confirmed, checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if a finding is new or changed")
    args = parser.parse_args()

    findings, confirmed, checked = scan()
    print(f"Checked {checked} live cases against their contracts.\n")

    print("== Never passed live: a lead about the FIXTURE ==")
    for endpoint in sorted(findings):
        print(f"\n{endpoint}")
        for line in findings[endpoint]:
            print(f"  {line}")
    if not findings:
        print("  none")

    print("\n\n== Confirmed live: the product accepted this exact payload, so the")
    print("   disagreement is evidence about the CONTRACT, not the fixture ==")
    for endpoint in sorted(confirmed):
        print(f"\n{endpoint}")
        for line in confirmed[endpoint]:
            print(f"  {line}")
    if not confirmed:
        print("  none")

    if not args.check:
        return 0

    problems: List[str] = []
    for endpoint in sorted(set(findings) | set(KNOWN)):
        now, was = findings.get(endpoint, []), KNOWN.get(endpoint, [])
        problems += [f"NEW      {endpoint}: {line}" for line in sorted(set(now) - set(was))]
        problems += [f"RESOLVED {endpoint}: {line} -- drop it from KNOWN"
                     for line in sorted(set(was) - set(now))]
    for endpoint in sorted(set(confirmed) | set(KNOWN_CONTRACT_GAPS)):
        now, was = confirmed.get(endpoint, []), KNOWN_CONTRACT_GAPS.get(endpoint, [])
        problems += [f"NEW      {endpoint}: {line} (confirmed live)"
                     for line in sorted(set(now) - set(was))]
        problems += [f"RESOLVED {endpoint}: {line} -- drop it from KNOWN_CONTRACT_GAPS"
                     for line in sorted(set(was) - set(now))]
    if problems:
        print("\n\nBaseline moved:")
        for line in problems:
            print(f"  {line}")
        return 1
    print(f"\n\nBaseline holds: {sum(len(v) for v in KNOWN.values())} fixture leads "
          f"across {len(KNOWN)} endpoints, and "
          f"{sum(len(v) for v in KNOWN_CONTRACT_GAPS.values())} live-confirmed "
          f"contract gaps across {len(KNOWN_CONTRACT_GAPS)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
