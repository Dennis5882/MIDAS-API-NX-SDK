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

## `/db/STYP-M1`: DELETE settled, contract still blocked on nesting

The manual repo wrote this endpoint's first chapter section on 2026-08-30
(`5c92efe`), closing the source gap recorded above, then corrected its own
unfounded explanation for the missing POST (`70a126b`) — a sentence copied from
`/db/ACTL-M1`, where it had also been invented. The methods themselves are
confirmed: the official article tags `GET, PUT, DELETE` under its own
`activeMethods` field, read from the source HTML on 2026-08-30. Not inference.

`StructureTypeHyperS` served `GET`/`PUT`, by analogy to the classic `/db/STYP`,
which is documented GET/PUT-only because new-file required data has nothing to
POST or DELETE to. The analogy was wrong here and nothing had checked it. The
SDK now serves DELETE and says in the class docstring that its *behaviour* is
unverified — reset to defaults, or an empty record the document cannot be valid
without. `live_crud_check.py` drives this case through PUT only.

The payload agrees exactly with `GET /info/db/STYP-M1` from 2026-07-29 and
2026-08-16: the same six top-level fields and the same four `MASS_CONTROL`
members. A transcription from the official article and a live schema probe
arriving independently at one shape is the strongest evidence this repo holds
for any Hyper-S endpoint.

The contract is still not promoted, for a reason that is not about this
endpoint:

- The Specifications table numbers `MASS_CONTROL`'s members `2-(1)` through
  `2-(4)`. `_NUMBER_CHILD` recognises a bare `(1)` and the `4-1` form, but not
  the `N-(M)` hybrid, so the draft emits `MASS_TYPE`, `MASS_POS`, `SELFWEIGHT`
  and `MASS_AXIS` as root fields beside their own parent — the `/db/RIGD`
  flattening defect again. **71 rows across the manual use this form.**
- Two conditional fields take their `enum` from the condition rather than the
  value list: `MASS_POS` gets `[LUMPED]` (its condition) instead of
  `[CENTROID, OFFSET]`, and `MASS_AXIS` gets `[CONSISTENT]` instead of
  `[XYZ, XY, Z]`.
- `SELFWEIGHT`'s `appliesWhen` renders `equals: "true"` as a string where the
  field is boolean.

Fixing the numbering reshapes those 71 rows wherever they appear, which is the
reviewed contract-shape migration `contract_migration_brief.md` already refuses
to do as an extractor-only change. Promote this endpoint as part of that work,
not ahead of it.

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
