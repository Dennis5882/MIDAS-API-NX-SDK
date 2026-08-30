# Contract migration open questions

## Settled decisions

- **Canonical labels are English.** Settled by the author 2026-08-30, closing
  the `/DESIGN/*` Korean-label question. `5b92881` took the manual's English
  label for all 27 affected resources, and the extractor now strips a
  parenthesised Korean gloss from a heading rather than adopting it, so the
  divergence cannot reappear silently. Measured after the change: **0 promoted
  contracts carry a Korean label.**

  One piece of that decision is left. The TypeScript generator's shadow gate
  still filters to `/db/*` — `scripts/generate_typescript_sdk.py:395` and
  `:530` — which was the right caution while the labels disagreed and is now
  just an unchecked surface. Widening it to `/DESIGN/*` is a small change that
  gates 63 more contracts; do it, and expect it to find something, because
  every one of the three gates widened on 2026-08-30 did.

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

## `/db/STYP-M1`: methods settled live, contract blocked on nesting

The manual repo wrote this endpoint's first chapter section on 2026-08-30
(`5c92efe`), closing the source gap, then removed its own unfounded reason for
the missing POST (`70a126b`) — a sentence copied from `/db/ACTL-M1`, where it
had also been invented.

The methods are now measured rather than argued. The official article tags
`GET, PUT, DELETE`; the server serves **GET and PUT only**. All three DELETE
forms, and POST, answer `{"message": "error status"}` and change nothing,
exactly as the classic `/db/STYP` does. Full evidence, including the control
that shows what a served DELETE returns, is in
`docs/live_verification_notes.md` (2026-08-30). `StructureTypeHyperS` keeps
`_GET_PUT_ONLY`; the manual repo has the article discrepancy to resolve.

The payload agrees exactly with `GET /info/db/STYP-M1`: the same six top-level
fields and the same four `MASS_CONTROL` members, on 2026-07-29, 2026-08-16 and
again on 2026-08-30.

The contract is still not promoted, for a reason that is not about this
endpoint:

- The Specifications table numbers `MASS_CONTROL`'s members `2-(1)` through
  `2-(4)`. `_NUMBER_CHILD` recognises a bare `(1)` and the `4-1` form, but not
  the `N-(M)` hybrid, so the draft emits `MASS_TYPE`, `MASS_POS`, `SELFWEIGHT`
  and `MASS_AXIS` as root fields beside their own parent — the `/db/RIGD`
  flattening defect again. `/info/db/STYP-M1` confirms the server nests them.
- Two conditional fields take their `enum` from the condition rather than the
  value list: `MASS_POS` gets `[LUMPED]` instead of `[CENTROID, OFFSET]`, and
  `MASS_AXIS` gets `[CONSISTENT]` instead of `[XYZ, XY, Z]`.
- `SELFWEIGHT`'s `appliesWhen` renders `equals: "true"` as a string where the
  field is boolean.

### The numbering fix is far smaller than this file used to claim

An earlier revision said the fix "reshapes 71 rows wherever they appear" and
deferred it into the reviewed contract-shape migration. **Measured 2026-08-30,
that is wrong**, and the deferral cost nothing but is not justified:

| | |
| --- | ---: |
| rows numbered `N-(M)` in the manual | 65 |
| ...that already nest by a dotted key (`DATA1.DESIGN.C_FC`) | 12 |
| ...that already carry a `└` tree marker in Description | 14 |
| ...with no other nesting signal, so they genuinely flatten | 45 |
| **promoted contracts affected** | **0** |
| **sections whose render changes when the fix is applied** | **1** |

The 45 signal-less rows are all `/db/SPFC`'s country-type tables in
`09_DB_Dynamic_Loads.md` — a draft, and blocked on the conditional-variant
decision anyway, not on numbering. `/ope/GSBG` and `/db/MATD` were saved by
their dotted keys; the key column wins over the No. column, and both were
already nested correctly. So the only draft the numbering blocks is this one.

Two edits are needed, not one, and missing the second is why widening the
regex alone measures as a no-op:

1. `_NUMBER_PATH` must match `2-(1)`.
2. `depth = len(re.findall(r"[-.]\d+", entry.number))` must count a
   parenthesised segment. `re.findall(r"[-.]\d+", "2-(1)")` returns `[]`
   because `(` follows the dash, so a matching number still yields depth 0 and
   the row stays at the root.

Re-rendering all 387 sections with both edits changes exactly one — this one —
and raises no new parse error. Reproduction script and diff:
`scratchpad/hybrid2.py` pattern in the 2026-08-30 session; re-derive it rather
than trusting this table, the same way this table replaced the one before it.

Promote `/db/STYP-M1` once the numbering and the two enum defects above are
fixed. It does not need the conditional-variant decision.

## Python surface drift introduced by promotion — closed, shipped in 2.7.1

Three changes reached `src/midas_nx/` after the `py-v2.7.0` release commit
(`c2a4599`). Recorded 2026-08-29 as unshipped; **all three shipped in 2.7.1 on
2026-08-30** and were verified present in the published wheel and tarball. Kept
below because each is a worked example of a different failure mode, not because
anything is outstanding.

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

- **`/db/DCTL`'s label regressed to Korean — fixed 2026-08-30.** `FrameDefinition.NAME` in
  `src/midas_nx/db/design.py` changed from `Definition of Frame` to the chapter
  heading at `24_DB_Design.md:823`. The manual's own `INDEX.md:410` uses the
  English label, and the chapter TOC row carries both. This is the first case of
  the `/DESIGN/*` Korean-label divergence above leaking into `src/`, so the
  canonical-label decision now has a shipped-surface consequence, not just a
  latent one behind the shadow gate.

- **`/ope/GSBG` now rejects conflicting BATCH payloads — shipped 2.7.1.** `3da6359` added a
  `reject_request` guard to `generate_bridge_girder_diagram()`
  (`src/midas_nx/ope.py`) raising `MidasRequestError` for `BATCH=true` with
  per-bridge fields, or `BATCH=false` with `BATCH_LIST`. This is the intended
  contract-driven pattern and is listed here only because it is new runtime
  behaviour that a release note must mention; it is not known to be wrong.

The remaining eleven `NAME` corrections in the same range are cosmetic and match
the manual.
