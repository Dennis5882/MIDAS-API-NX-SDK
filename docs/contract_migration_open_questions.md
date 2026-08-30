# Contract migration open questions

## Existing unresolved decision

- The 63 `/DESIGN/*` contracts carry Korean labels from the manual while both
  SDKs use English labels. The TypeScript generator's shadow gate currently
  compares only `/db/*`; do not widen that filter until the author selects the
  canonical labels.

## Conditional payload transcription

- `/db/FBLA` documents four fields for `FLOOR_DIST_TYPE = 1 or 2`.
  `appliesWhen` currently represents an array as logical AND and each condition
  supports one scalar `equals`, so the manual's OR cannot be transcribed without
  changing the schema (for example, an explicitly reviewed `oneOf`/`in`
  predicate) or duplicating wire fields. Duplicating fields would make the
  contract ambiguous, so this table remains unmerged pending an author decision.

## Manual-source gaps

- ~~`/db/STYP-M1` appears only in `docs/manual/INDEX.md`.~~ Closed 2026-08-30:
  the manual repo wrote the section (`5c92efe`), and
  `npm resource manual-section coverage` is now 0 without a parsed section. The
  contract still is not promoted, for the separate reason below.

## `/db/STYP-M1` declares a DELETE nothing has verified

The manual repo wrote this endpoint's first chapter section on 2026-08-30
(`5c92efe`), closing the gap recorded above. Its payload agrees with the SDK
exactly: the same six top-level fields and the same four `MASS_CONTROL`
members that `GET /info/db/STYP-M1` returned on 2026-07-29 and again on
2026-08-16. Two independent derivations landing on the same shape is the best
evidence this repo has for any Hyper-S endpoint.

The methods do not agree, and the contract is therefore not promoted.

- The new section states `GET`, `PUT`, `DELETE`, and explains the missing POST
  as `기본 레코드가 자동 생성됨`.
- `StructureTypeHyperS` serves `GET`/`PUT` only.
- The same chapter says required new-file data is GET/PUT only, in its preamble
  (`02_DB_Project_Structure.md:15`) and for the classic `/db/STYP` in both its
  contents table and its own Methods row.

The section's own reason for dropping POST — the record is auto-created —
is the chapter's reason for `/db/STYP` having no DELETE either. A record that
must exist for the document to be valid has nothing to delete to.

No live call has settled it. `docs/coverage.json` records a `write`-level
verification for this endpoint, but `live_crud_check.py`'s case passes an empty
create payload and a `None` expected-created value, and the sibling
`StructureType` case above it is commented `GET/PUT only, no POST/DELETE`. The
tier's summary sentence in coverage.json describes the tier, not this case: the
POST and DELETE legs never ran here.

So this is a documentation question, not an SDK one, and one line of the manual
settles it. Until then the SDK keeps the narrower surface, which cannot destroy
a record the product needs.

## Python surface drift introduced by promotion (revisit after the Codex run)

Three changes reached `src/midas_nx/` after the `py-v2.7.0` release commit
(`c2a4599`), so none of them has shipped yet. Recorded 2026-08-29. The first is
fixed; the other two are still open.

- **`/db/POLC-M1` gained POST — fixed 2026-08-30.** `656f386` dropped
  `METHODS = GET_PUT_DELETE_METHODS` from `PushoverLoadCaseHyperS`, following a
  contract that declared a `POST` operation, and `resources.ts` carried the same
  widening. The manual states `GET`/`PUT`/`DELETE` and says twice that Hyper-S
  serves no POST. The extractor was reading the chapter's closing
  general-vs-Hyper-S comparison table — three columns, and it took the first
  value column, which describes the *general* endpoint. Two independent defects
  produced it, and each alone was enough:

  1. `_METHODS_TABLE_ROW` accepted a row of any width, so a comparison row
     counted as a declaration. It is now anchored to the documented two-column
     form. A section body runs to the next heading that *names an endpoint*, so
     a chapter's trailing summary always lands inside the last endpoint's body —
     this is not specific to chapter 14.
  2. The `### Active Methods` fallback scan swept every line to the next
     heading, including the `> ⚠️` callout that quotes the rejected verb list in
     order to reject it. Blockquotes are now skipped.

  Measured across all 386 manual sections, the two fixes together change exactly
  one section's verbs — this one — and lose none.

  `--check` could not have caught it: it never compared methods at all, though
  `manualDefects.describes` has carried a `method` value the whole time. It does
  now, and 277 of the 278 promoted contracts already agreed. A live-proved verb
  the manual denies is recorded under `manualDefects`, not silently matched.

- **`/db/DCTL`'s label regressed to Korean.** `FrameDefinition.NAME` in
  `src/midas_nx/db/design.py` changed from `Definition of Frame` to the chapter
  heading at `24_DB_Design.md:823`. The manual's own `INDEX.md:410` uses the
  English label, and the chapter TOC row carries both. This is the first case of
  the `/DESIGN/*` Korean-label divergence above leaking into `src/`, so the
  canonical-label decision now has a shipped-surface consequence, not just a
  latent one behind the shadow gate.

- **`/ope/GSBG` now rejects conflicting BATCH payloads.** `3da6359` added a
  `reject_request` guard to `generate_bridge_girder_diagram()`
  (`src/midas_nx/ope.py`) raising `MidasRequestError` for `BATCH=true` with
  per-bridge fields, or `BATCH=false` with `BATCH_LIST`. This is the intended
  contract-driven pattern and is listed here only because it is new runtime
  behaviour that a release note must mention; it is not known to be wrong.

The remaining eleven `NAME` corrections in the same range are cosmetic and match
the manual.
