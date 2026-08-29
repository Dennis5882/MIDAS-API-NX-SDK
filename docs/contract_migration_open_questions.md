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
(`c2a4599`), so none of them has shipped yet. Recorded 2026-08-29; hold until
the contract migration work in progress is finished, then fix together.

- **`/db/POLC-M1` gained POST.** `656f386` dropped
  `METHODS = GET_PUT_DELETE_METHODS` from `PushoverLoadCaseHyperS`
  (`src/midas_nx/db/pushover.py`), so the class now falls back to
  `_ALL_METHODS` and `create()` is allowed. The source is
  `contracts/endpoints/db-polc-m1.yaml`, which declares a `POST` operation;
  `packages/typescript/src/generated/resources.ts` carries the same widening.
  The manual disagrees: `14_DB_Pushover.md:1727` lists `GET / PUT / DELETE` and
  the callout at `:1729` says the upstream article's `POST, GET, PUT, DELETE`
  table is untrusted — every other Hyper-S (`-M1`) endpoint and the chapter
  preamble state that POST is unsupported — and instructs that the trimmed form
  be kept until live confirmation. This is the normalized-form rule in
  CLAUDE.md: the extractor appears to have read the raw article table rather
  than the normalization. Decide whether to correct the contract or to live-check
  POST on a Civil NX session first; do not "fix" it by editing the SDK alone.

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
