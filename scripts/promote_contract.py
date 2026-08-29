"""Promote reviewed drafts from contracts/drafts/ into contracts/endpoints/.

A draft is a transcription of a manual section. Promoting it means answering the
questions the manual cannot: which products actually serve the route, what a
DELETE really does, and how far anyone has checked. This script types those
answers consistently; it does not invent them.

Where each answer comes from
----------------------------
``products``      ``docs/coverage.json``'s top-level product list - the manual's
                  framing narrowed by live 404 sweeps, and wrong for 32 of 47
                  endpoints the manual called Civil-only. Deliberately *not*
                  ``live_verified.products``, which answers a different question:
                  which products this was checked on. Deriving one from the other
                  declared seven endpoints Civil-only for no better reason than
                  that one August pass only had Civil open.
``methods``       the manual, cross-checked against both SDKs by
                  ``scripts/validate_contracts.py``. A draft whose methods the
                  manual never stated is refused rather than defaulted.
``verification``  ``docs/coverage.json``'s date, build and level, written into
                  ``contracts/verification/{gen,civil}-nx.yaml`` as a record the
                  contract then references.
``DELETE``        the measured two-operation shape. The manual's documented body
                  form empties the whole table regardless of the ids it names;
                  the per-id URL it does not document is the one that deletes a
                  selection.

What it refuses
---------------
An endpoint whose documented payload has already been measured wrong live is
left out. Bulk-promoting the manual's version of ``/db/SECF``'s key would put a
known-false statement into the source of truth, which is worse than having no
contract for it. Those need someone to encode the correction and the evidence by
hand, with ``provenance: live_corrected`` and a ``manualDefects`` entry.

Usage::

    python scripts/promote_contract.py db-grup db-rigd
    python scripts/promote_contract.py --all --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

import yaml
from function_endpoints import (
    FunctionEndpoint,
    ResourceEndpoint,
    function_endpoints,
    resource_endpoints,
)

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "contracts" / "drafts"
ENDPOINTS = ROOT / "contracts" / "endpoints"
VERIFICATION = ROOT / "contracts" / "verification"
COVERAGE = ROOT / "docs" / "coverage.json"

#: Endpoints whose documented payload has been measured wrong against a running
#: product. Each needs its correction and evidence written by hand; see
#: docs/live_verification_notes.md and CLAUDE.md's live-behaviour section.
NEEDS_HAND_REVIEW = {
    "/db/SECF": "its documented key is wrong live",
    "/db/PRES": "its documented default DIRECTION is wrong live",
    "/db/MVHL": "its documented VEHICLE_LOAD_NUM is wrong live",
    "/db/TDMT": "its whole code-name enum is wrong live - the server wants 'European'",
    "/db/TDME": "companion to /db/TDMT's enum finding",
    "/db/REBW": "every field name in its manual section is wrong live",
    "/db/REBC": "the official article itself is wrong about its array shape",
    "/db/REBB": "its write path is broken server-side, not a shape question",
}

# A JSON wire member may start with a digit.  The manual documents
# ``7TH_DOF_TYPE`` verbatim for /ope/GSBG, so the promotion gate must accept
# the same literal-key grammar as the extractor and contract schema.
_FIELD_KEY = re.compile(r"^[A-Za-z0-9_]+$")

_DELETE_OPS = """  - method: DELETE
    variant: per_id
    path: {endpoint}/{{id}}
    risk: destructive
    mitigation: none
    summary: Delete exactly the record named in the path.
    request:
      wrapper: none
    response:
      wrapper: table
      keyStability: stable
    notes: >-
      Undocumented route, and the only DELETE form that deletes a selection
      rather than the whole table - see risk db-delete-body-empties-table.
  - method: DELETE
    variant: whole_table
    risk: destructive
    mitigation: confirmation_required
    summary: Empty the entire table.
    request:
      wrapper: assign
      itemSchema: none
      description: >-
        The manual's documented form. The ids in that body are ignored.
    response:
      wrapper: message
"""

_DELETE_RULES = """
sdkRules:
  - id: {id}-delete-per-id
    kind: per_id_request
    appliesTo: [DELETE]
    variant: per_id
    reason: >-
      The manual's DELETE body form empties the whole table regardless of the
      ids it names. Measured on /db/NODE, /db/STLD, /db/LDGR and /db/MATL and
      treated as a property of /db/* DELETE, so an SDK's ordinary "delete these
      ids" call must use the undocumented per-id URL. Requests go one at a time
      and stop at the first failure.
    riskRef: db-delete-body-empties-table
    alternative: Emptying the table on purpose is the separate whole_table operation.
  - id: {id}-delete-all-confirmation
    kind: require_confirmation
    appliesTo: [DELETE]
    variant: whole_table
    reason: >-
      Emptying the table cannot be undone through the API and raises no
      product-side dialog.
    riskRef: db-delete-body-empties-table
    alternative: Use the per_id DELETE operation to remove selected records.

knownDefects:
  - ref: db-delete-body-empties-table
"""

_HEADER = """# {endpoint}
#
# Drafted by scripts/extract_contracts.py from the official manual, then promoted
# by scripts/promote_contract.py: products and verification status come from
# docs/coverage.json's live record, not from the manual's framing. For /db/*
# endpoints, the DELETE shape comes from measured /db/* DELETE behaviour.
# safeToOmit is answered `true` only where a confirmed live payload actually
# omitted the field.
"""


def _coverage() -> dict[str, dict]:
    data = json.loads(COVERAGE.read_text(encoding="utf-8"))
    return {entry["endpoint"]: entry for entry in data["endpoints"]}


def _record_id(entry: dict) -> str:
    """One shared record per (date, level, outcome), not one per endpoint."""
    live = entry["live_verified"]
    return f"db-{live['level']}-sweep-{live['date']}"


def _verification_block(entry: dict, product: str) -> str:
    live = entry["live_verified"]
    version = live.get("nx_versions", {}).get(product, f"MIDAS {product.title()} NX 2026")
    method = " ".join(live.get("method", "").split())[:400]
    return f"""
  - id: {_record_id(entry)}
    endpoints: []
    date: "{live['date']}"
    nxVersion: {version}
    level: {live['level']}
    outcome: {live.get('outcome', 'success')}
    method: >-
      {method}
    finding: >-
      A shared record for every endpoint checked in this pass. Endpoint-specific
      findings stay in docs/live_verification_notes.md; this entry exists so a
      contract's verification claim points at a dated, build-specific source
      rather than at nothing.
    evidence:
      - docs/live_verification_notes.md
"""


def _draft_methods(text: str) -> set[str]:
    """Read only the manual-transcribed operation verbs from a draft."""
    return set(re.findall(r"^  - method: ([A-Z]+)$", text, re.MULTILINE))


def _ambiguous_draft_key(text: str) -> str | None:
    """Return a non-wire field key that must not be promoted as a contract fact."""

    import yaml

    document = yaml.safe_load(text)

    def walk(fields: list[dict]) -> str | None:
        for field in fields:
            key = field.get("key")
            if not isinstance(key, str) or not _FIELD_KEY.fullmatch(key):
                return str(key)
            nested = walk(field.get("properties", []))
            if nested is not None:
                return nested
        return None

    return walk(document.get("fields", []))


def _endpoint_name_is_fallback(document: object, endpoint: str) -> bool:
    """Whether a draft used its endpoint as a missing manual label fallback."""
    return isinstance(document, dict) and document.get("name") == endpoint


def _plain_function_is_modelled(
    endpoint: str,
    methods: set[str],
    functions: dict[str, FunctionEndpoint],
) -> str | None:
    """Return why a plain route cannot yet receive a green parity contract."""
    surface = functions.get(endpoint)
    if surface is None:
        return "no generic plain-function parity surface was discovered"
    if surface.python is None:
        return "no Python plain function exposes the route"
    if surface.typescript is None:
        return "no npm plain function exposes the route"
    if surface.python.methods != methods:
        return (
            f"Python plain functions serve {sorted(surface.python.methods)}, "
            f"but the manual draft declares {sorted(methods)}"
        )
    if surface.typescript.methods != methods:
        return (
            f"npm plain functions serve {sorted(surface.typescript.methods)}, "
            f"but the manual draft declares {sorted(methods)}"
        )
    return None


def _non_db_resource_is_modelled(
    endpoint: str,
    methods: set[str],
    products: set[str],
    resources: dict[str, ResourceEndpoint],
) -> str | None:
    """Describe the safe next step for a non-/db ``DbResource`` draft.

    This is a parity classification, not a source of contract facts.  In
    particular, the measured ``/db/*`` DELETE body behaviour is not evidence
    for a similarly-shaped ``/DESIGN/*`` resource.
    """
    surface = resources[endpoint]
    if surface.python is None:
        return "no Python resource exposes the route"
    if surface.typescript is None:
        return "no npm resource exposes the route"
    if surface.python.methods != methods:
        return (
            f"Python resource serves {sorted(surface.python.methods)}, "
            f"but the manual draft declares {sorted(methods)}"
        )
    if surface.typescript.methods != methods:
        return (
            f"npm resource serves {sorted(surface.typescript.methods)}, "
            f"but the manual draft declares {sorted(methods)}"
        )
    if surface.python.products != products:
        return (
            f"Python resource declares products {sorted(surface.python.products)}, "
            f"but live/manual ledger declares {sorted(products)}"
        )
    if surface.typescript.products != products:
        return (
            f"npm resource declares products {sorted(surface.typescript.products)}, "
            f"but live/manual ledger declares {sorted(products)}"
        )
    return None


_DELETE_BLOCK = re.compile(r"(?ms)^(  - method: DELETE\n)(.*?)(?=^  - method:|\Z)")


def _non_db_delete_response_unknown(text: str) -> str:
    """Keep a documented bodiless DELETE without inventing its response shape."""

    def replace(match: re.Match[str]) -> str:
        block = match.group(2)
        if "    request:\n      wrapper: none\n" not in block:
            return match.group(0)
        response = "    response:\n      wrapper: table\n      keyStability: stable\n"
        if response not in block:
            return match.group(0)
        block = block.replace(
            response,
            "    response:\n      wrapper: unknown\n"
            "    notes: >-\n"
            "      The manual shows a bodyless DELETE at this endpoint, but does not\n"
            "      state the deletion scope or response shape.\n",
            1,
        )
        return match.group(1) + block

    return _DELETE_BLOCK.sub(replace, text)


def promote(
    slug: str,
    coverage: dict[str, dict],
    functions: dict[str, FunctionEndpoint],
    resources: dict[str, ResourceEndpoint],
    dry_run: bool,
    candidate: Optional[str] = None,
) -> Optional[str]:
    """Return the record id this promotion needs, or None if it was refused."""
    draft_path = DRAFTS / f"{slug}.yaml"
    if candidate is None and not draft_path.exists():
        print(f"  {slug}: no draft - run scripts/extract_contracts.py --emit first")
        return None

    # ``--from-manual`` supplies this exact text in memory. It lets a parser
    # improvement feed the promotion gate without rewriting contracts/drafts:
    # those files are review artifacts, never generator cache.
    text = candidate if candidate is not None else draft_path.read_text(encoding="utf-8")
    endpoint_match = re.search(r"^endpoint: (\S+)$", text, re.MULTILINE)
    if endpoint_match is None:
        print(f"  {slug}: draft has no endpoint")
        return None
    endpoint = endpoint_match.group(1)

    # An endpoint string is the extractor's explicit fallback, not a label
    # stated by the manual. Refuse it here so a missing label cannot quietly
    # become permanent contract metadata when a draft is promoted in bulk.
    draft_data = yaml.safe_load(text)
    if _endpoint_name_is_fallback(draft_data, endpoint):
        print(f"  {slug}: refused - the manual does not state a human-readable endpoint label")
        return None

    if endpoint in NEEDS_HAND_REVIEW:
        print(f"  {slug}: refused - {NEEDS_HAND_REVIEW[endpoint]}")
        return None
    if "TODO(review): the chapter did not state its methods" in text:
        print(f"  {slug}: refused - the manual never states this endpoint's methods")
        return None
    if key := _ambiguous_draft_key(text):
        print(f"  {slug}: refused - {key!r} is not one literal wire-property name")
        return None

    # A draft still carrying review notes is incomplete by its own admission.
    # Promoting it in bulk would put "the manual left this blank" into the source
    # of truth as though it were settled. The nesting notes are the exception:
    # they record how a structure was reconstructed, not something unresolved.
    notes = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith("# NOTE:") and "nests this under" not in line
    ]
    if notes:
        print(f"  {slug}: refused - {len(notes)} unresolved review note(s), e.g. {notes[0][8:60]}")
        return None
    # ``structuralTables`` is an extractor record that each supplementary
    # table was placed under a named object/array path.  It is not a blanket
    # exemption: only the still-unresolved ``unmergedTables`` population is
    # the conditional-variant blocker.  Parsing YAML avoids a comment or a
    # prose mention accidentally changing promotion behaviour.
    extraction = draft_data.get("extraction", {}) if isinstance(draft_data, dict) else {}
    if extraction.get("unmergedTables"):
        print(f"  {slug}: refused - the section has conditional variant tables nobody has merged")
        return None
    if "TODO(review): the manual did not" in text:
        print(f"  {slug}: refused - the manual leaves a field's type or requiredness unstated")
        return None
    if re.search(r"^fields: \[\]$", text, re.MULTILINE):
        print(f"  {slug}: refused - no payload fields could be parsed")
        return None
    entry = coverage.get(endpoint)
    if entry is None or not entry.get("live_verified"):
        print(f"  {slug}: refused - no live-verification record in docs/coverage.json")
        return None

    methods = _draft_methods(text)
    non_db_resource = False
    if not endpoint.startswith("/db/"):
        if endpoint in resources:
            reason = _non_db_resource_is_modelled(endpoint, methods, set(entry["products"]), resources)
            if reason is not None:
                print(f"  {slug}: refused - non-db resource parity: {reason}")
                return None
            non_db_resource = True
        function_reason = _plain_function_is_modelled(endpoint, methods, functions)
        if not non_db_resource and function_reason is not None:
            print(f"  {slug}: refused - plain-function parity: {function_reason}")
            return None

    live = entry["live_verified"]
    # Two different questions, and conflating them was worth one round of the
    # parity check shouting. `products` asks which products serve the route -
    # narrowed from the manual only where a live sweep measured a 404. The
    # ledger's top-level `products` carries that. `live_verified.products` asks
    # something else entirely: which products this was checked on. Seven
    # endpoints checked only against Civil in one August pass are not
    # Civil-only, and deriving `products` from the tested set said they were.
    products = sorted(entry["products"])
    tested = sorted(live["products"])
    status = {
        ("civil", "gen"): "verified_both",
        ("gen",): "verified_gen",
        ("civil",): "verified_civil",
    }.get(tuple(tested), "manual_only")
    record = _record_id(entry)

    text = re.sub(r"^# DRAFT contract for .*?\n(#.*\n)*\n", "", text, flags=re.MULTILINE)
    text = text.replace("draft: true   # reviewing this file is what removes this line\n", "")
    text = _HEADER.format(endpoint=endpoint) + text
    if non_db_resource:
        text = _non_db_delete_response_unknown(text)

    text = text.replace("# TODO(review): confirm against live evidence, not the manual's framing.\n", "")
    text = text.replace(
        "# TODO(review): manual_only is the honest state for a contract nobody has\n"
        "# called yet. Raise it only with a record in contracts/verification/.\n",
        "",
    )
    text = re.sub(
        r"^[ ]*# TODO\(review\): nobody has omitted this against a live product\.\n"
        r"[ ]*# Leave it unverified, or find out - do not read the manual's\n"
        r"[ ]*# 'Optional' as an answer; that is what documentedOptional records\.\n",
        "",
        text,
        flags=re.MULTILINE,
    )
    text = text.replace("   # TODO(review): product_crash_risk if it has ever ended a session", "")
    delete_mitigation_todo = (
        "    mitigation: none   # TODO(review): see /db/NODE's contract for the two DELETE forms\n"
    )
    # The draft comment points at the measured /db/* delete forms.  That
    # evidence is applicable only to /db/* resources; for other documented
    # resources, retain the honest current mitigation instead of erasing the
    # required destructive-operation field.
    if endpoint.startswith("/db/"):
        text = text.replace(delete_mitigation_todo, "")
    else:
        text = text.replace(delete_mitigation_todo, "    mitigation: none\n")

    text = re.sub(
        r"^products: \[.*\]$",
        "products: [" + ", ".join(products) + "]",
        text,
        flags=re.MULTILINE,
    )

    block = f"verification:\n  status: {status}\n"
    if status != "manual_only":
        block += "  records:\n" + "".join(
            f"    - product: {p}\n      ref: {record}\n" for p in tested
        )
    text = re.sub(r"verification:\n  status: manual_only\n", block, text)

    plain_delete = re.search(r"  - method: DELETE\n(?:    (?!- method).*\n)+", text)
    if endpoint.startswith("/db/") and plain_delete:
        text = text.replace(plain_delete.group(0), _DELETE_OPS.format(endpoint=endpoint))
        text = text.replace("\nextraction:", _DELETE_RULES.format(id=slug) + "\nextraction:")

    text = re.sub(r"\n{3,}", "\n\n", text)
    if not dry_run:
        (ENDPOINTS / f"{slug}.yaml").write_text(text, encoding="utf-8")
    print(f"  {slug}: {endpoint} -> served by {products}, {status}")
    return record


def ensure_records(needed: dict[str, dict], dry_run: bool) -> None:
    """Append any verification record a promotion referenced but did not exist."""
    for product in ("gen", "civil"):
        path = VERIFICATION / f"{product}-nx.yaml"
        text = path.read_text(encoding="utf-8")
        additions = [
            _verification_block(entry, product)
            for record, entry in sorted(needed.items())
            if f"id: {record}\n" not in text and product in entry["live_verified"]["products"]
        ]
        if not additions:
            continue
        print(f"  {path.name}: adding {len(additions)} record(s)")
        if not dry_run:
            path.write_text(text.rstrip("\n") + "\n" + "".join(additions), encoding="utf-8")


def _manual_selection_error(
    slugs: list[str], candidates: dict[str, str], existing: set[str], replace_existing: bool
) -> str | None:
    """Return a refusal reason for unsafe ``--from-manual`` selections."""
    missing = sorted(set(slugs) - candidates.keys())
    if missing:
        return "--from-manual found no manual section for: " + ", ".join(missing) + "; refusing draft fallback"
    overwritten = sorted(set(slugs) & existing)
    if overwritten and not replace_existing:
        return "--from-manual refuses to replace existing contract(s): " + ", ".join(
            overwritten
        ) + "; pass --replace-existing after review"
    return None


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slugs", nargs="*", help="draft ids, e.g. db-grup")
    parser.add_argument("--all", action="store_true", help="promote every draft that qualifies")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--from-manual",
        action="store_true",
        help="render named sections in memory from the manual; never update contracts/drafts",
    )
    parser.add_argument("--manual-api-repo", type=Path, help="manual repository used with --from-manual")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="with --from-manual, explicitly allow reviewed replacement of existing contracts",
    )
    args = parser.parse_args(argv)

    coverage = _coverage()
    functions = function_endpoints()
    resources = resource_endpoints()
    candidates: dict[str, str] = {}
    if args.from_manual:
        if args.manual_api_repo is None:
            parser.error("--from-manual requires --manual-api-repo")
        # Import only the manual extractor, never either SDK. This is kept
        # opt-in so the ordinary draft-review workflow remains unchanged.
        from extract_contracts import live_omission_evidence, load_manual, render_draft

        evidence = live_omission_evidence()
        sections, _ = load_manual(args.manual_api_repo)
        candidates = {
            section.id: render_draft(section, evidence.get(section.endpoint))
            for section in sections
        }
    elif args.replace_existing:
        parser.error("--replace-existing requires --from-manual")
    existing = {path.stem for path in ENDPOINTS.glob("*.yaml")}
    slugs = args.slugs or (
        sorted(slug for slug in candidates if slug not in existing)
        if args.all and args.from_manual
        else [p.stem for p in sorted(DRAFTS.glob("*.yaml")) if p.stem not in existing]
        if args.all
        else []
    )
    if not slugs:
        parser.error("name at least one draft, or pass --all")
    if args.from_manual:
        selection_error = _manual_selection_error(slugs, candidates, existing, args.replace_existing)
        if selection_error:
            parser.error(selection_error)

    needed: dict[str, dict] = {}
    promoted = 0
    for slug in slugs:
        candidate = candidates.get(slug)
        record = promote(slug, coverage, functions, resources, args.dry_run, candidate)
        if record is None:
            continue
        promoted += 1
        endpoint_text = candidate if candidate is not None else (DRAFTS / f"{slug}.yaml").read_text(encoding="utf-8")
        endpoint_match = re.search(r"^endpoint: (\S+)$", endpoint_text, re.MULTILINE)
        if endpoint_match is None:  # promote() already verified this draft.
            raise RuntimeError(f"{slug}: draft endpoint disappeared during promotion")
        endpoint = endpoint_match.group(1)
        needed[record] = coverage[endpoint]

    ensure_records(needed, args.dry_run)
    print(f"\n{promoted} promoted, {len(slugs) - promoted} refused{' (dry run)' if args.dry_run else ''}")
    print("Now run: python scripts/validate_contracts.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
