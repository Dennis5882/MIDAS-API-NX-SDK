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

- `/db/STYP-M1` appears only in `docs/manual/INDEX.md` as “Structure Type
  (Hyper-S)”. No `docs/manual/*.md` endpoint section, parameter table, or
  method declaration describes it. The extractor therefore has no draft to
  promote; retain the missing contract until a manual section, live `/info`, or
  other permitted evidence is available.

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
