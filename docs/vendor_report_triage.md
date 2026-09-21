# Vendor report triage

Which live findings belong in `docs/vendor_report_ko.md`, which do not, and
why. The report is what goes to MIDASIT; this is the working file behind it.

**This file collects; it does not act.** Nothing here has been sent. Sending
the report, filing a Jira issue and contacting MIDASIT are all the author's
calls, and none of them follows from an entry being added here.

It exists because the reasoning kept living in commit messages. On 2026-09-21
three candidates were considered and set aside for three different reasons,
and none of those reasons was written anywhere a later audit would find them —
so the next audit would have re-derived all three from scratch and possibly
reached a different answer.

`docs/manual_defects_register.md` is the counterpart for the **manual**. A
finding about MIDASIT's documentation goes there as an `MD-nn`; a finding about
the product's behaviour goes here. Several are both, and then both files carry
their own half.

## The rule that governs section B

**Never cite the vendored manual as "the documentation" in anything sent
outside.** `E:\AI Study\MIDAS-API` is a curated transcription that deliberately
normalizes official typos. It is the right source for an internal decision and
the wrong one for a claim *about what MIDASIT published*. For that, fetch the
Zendesk article and quote it.

This is not a precaution, it is a scar. On 2026-07-27 all seven B-items were
re-checked against the official articles before sending and **four did not
survive** — `/db/TDMT`'s enum (a `NAME` column read as `CODE`), `/db/TDME`'s
`"KDS2016"` (a transcription error in the vendored copy), `/db/SECF`'s key
("keyed by element id" was this SDK's own docstring) and `/db/PRES`'s `FORCES`
length. The two that survived got weaker. The retractions are in the report's
own appendix rather than deleted, because a report that shows what it withdrew
is easier to trust on what it kept.

## In the report

| id | what | last measured |
| --- | --- | --- |
| A-2 | `DELETE {endpoint}` with an ID-keyed `"Assign"` empties the whole table | Civil v2.2 build 06/18/2026 |
| A-3 | 10 endpoints where a write is accepted, echoed back and not stored | **2026-09-21**, except `/db/STCT` on Civil, `/db/MATD` and `/db/SSEIS` |
| A-4 | error bodies under HTTP 200 / 201 | **2026-09-21**, seventeen observations in one batch |
| A-5 | `/mapikey/verify` answers `connected` after the product is gone | 2026-07 |
| A-6 | `"Wrong Field"` means a bad value, not a bad field name | **2026-09-21** |
| A-7 | writes under `Program Files` fail with access denied, including on a GET | 2026-07-29 |
| A-8 | `/info` is not served for `/DESIGN/*` or the Hyper-S `IEHG` trio | **2026-09-21** |
| A-9 | `/info` disagrees with the server in both directions | **2026-09-21**; see the correction below |
| A-10 | 9 endpoints + `/db/RPSC` whose write path has never passed — **an ask, not a defect claim** | **2026-09-21**, each on the product that declares it |
| B-1…B-5 | documentation items, each checked against the official article | 2026-07-27 / 2026-08-27 |

### Re-verification debt

Mostly cleared on 2026-09-21, when the author had both products open and chose
the fixture-replay scope. What is still outstanding, and why:

- **A-2** — its reproduction empties a table. It needs a document confirmed
  disposable, the same bar as any `/doc/NEW` harness, and the author declined
  it for that session.
- **A-5** — needs the product to be killed and then polled.
- **A-7** — needs a document opened from under `Program Files` and, if it
  reproduces, a human to dismiss a modal on the NX machine.
- **`/db/STCT` on Civil** — the case reports `BLOCKED` rather than a result:
  Civil pre-populates the stage-control record, so the POST answers `Key
  Already Exist`. Reaching the drop there takes a PUT the fixture does not
  carry. The Gen half reproduced (`wrote 30, read back None`).
- **`/db/MATD`, `/db/SSEIS`** — measured through
  `scripts/live_manual_feedback.py`'s probes rather than the CRUD fixture, and
  not re-run.
- **`/db/SPLC`** — the round trip passes; the `ALONG`-ignored-on-update half
  was not probed separately.

**No build string was read on 2026-09-21.** The API reports none. A fresh
GET-only `/info` sweep of both products matched the Build 09/15/2026 surface
exactly (one already-recorded `/db/SECT` delta against the 2026-09-03
baseline), which says the surface is unchanged and nothing more — `/db/NMAS`
is the standing proof that behaviour moves while `/info` does not.

### Corrected by the 2026-09-21 re-measurement

- **`/db/SECF` got sharper.** The report recorded a 200 with no error. The
  product actually **echoes the whole record back** while `GET` answers
  `{"message": ""}` — the same signature as `/db/CONS` and `/db/MATD`.
- **`/db/STBK` got weaker.** A-9's "declared nowhere, accepted anyway"
  direction rested partly on it. The call is accepted without error on both
  products, but the record read back does not carry `LCNAME`, so what is
  established is that the server *tolerates* the field, not that it stores it.
  `/db/POSL` carries that direction; `/db/STBK` is now stated as the weaker
  observation it is, here, in the report and in CLAUDE.md.

## Removed

### A-1 `/db/NMAS` — fixed, and confirmed fixed (removed 2026-09-21)

Omitting `rmX`/`rmY`/`rmZ` ended the session, 15 reproductions out of 15. It
was the report's headline for two months.

`docs/vendor_repro_nmas.py` — the standalone reproduction that bypasses the
SDK — now answers 201 in under half a second on both products on Build
09/15/2026, the session stays alive, and the following GET shows the server
filling all three fields with the documented default of `0` **itself**. That is
stronger than "it no longer crashes": the default is applied. Three consecutive
clean results across four builds since the first confirmation on 2026-07-30.

The remaining ids were **not renumbered** — A-2 is still A-2. An issue id is
how a report is referred to, and closing the gap would make every earlier
reference wrong. A note in the report's change log records that it was
reported, fixed and verified, which is worth the vendor's attention in a way a
silent deletion is not.

## Held, with the reason

### `/db/FIMP`'s printed example is internally invalid — needs the official article

The chapter prints `ECU=0.003`, `Z=100`, `EC0=0.002` and the product refuses
the POST with its own rule, `Epsilon_cu > 0.8 / Z + Epsilon_co`; `0.8/100 +
0.002 = 0.010` is greater than `0.003`, and the second example repeats the same
three numbers. Measured through both SDKs on both products.

Already recorded as **MD-54** in `docs/manual_defects_register.md`. It is a
strong B-item candidate and **it is not in the report yet**, because the
measurement was made against the vendored chapter. See the rule above: fetch
the official article, confirm it prints the same three values, then add it.

### `/post/TABLE`'s response key — mostly explained, too thin to send

Recorded as the known risk `post-table-unstable-response-key` and in
`CLAUDE.md`. Earlier sessions saw the top-level key vary between the
`TABLE_NAME` passed, `"Result Table"` and `"empty"` with no known trigger.

Most of it dissolved on 2026-07-26: **blank or omit `TABLE_NAME` and the server
keys the response `"empty"`; pass a name and you get that name back.** Same
call, same 78 rows of real data, both ways. `"empty"` is not an error marker —
it carried a full table.

What is left is one old unexplained `"Result Table"` sighting. Sending a
complaint that rests on a single stale observation is how a claim dies on
contact with the source. The SDKs match on shape (`unwrap_table()`), which is
the right answer regardless.

### `/TEMP/DESIGN/SRC/AIK-SRC2K/OCHECK` — the author's call, not a drafting one

Reproduced across four builds and both products, most recently on Build
09/15/2026 where the product had just answered eleven historically-crashing
calls cleanly. **MIDASIT has closed it as not a defect, with no fix timeline.**

Re-raising a closed item in an external report is a relationship decision, not
a technical one. It is left out until the author says otherwise. If it ever
goes in, the internal tracker id does not: no `MAPI-nnnn` and no mention of
MIDASIT's internal Jira belongs in anything shipped.

## Not candidates

These look like findings in the coverage tables and are not ours to report.
`docs/live_verification_playbook.md`'s "What is left, and why" has the full
list with per-endpoint reasons; the classes are:

- **A precondition we have not built.** `/db/TDNA`'s `Not Registered String`,
  `/db/CSCS` needing a `COMPOSITE` section, everything blocked behind
  `/db/FIMP` or `nllp_seed`. The product is saying no for a reason it states.
- **A documented value nobody has written down.** `/db/EPMT-M1`,
  `/db/MVLDbs`'s mutually exclusive objects, `/db/NLCT`'s
  `LINE_SEARCH_OPTION`. Inventing one would break this report's own rule that
  no live payload is ever hand-written.
- **A product capability, not a defect.** Gen answering `Unavailable moving
  load code` for `CHINA`/`INDIA`/`KOREA`, which decides most of the lane table.
- **Our own fixture.** `/db/ACTL` sending `CLATS` on Gen, where that field is
  Civil-only — `check_fixture_contract.py` reports it as a fixture lead and it
  is one.
- **Same symptom, cause not isolated.** `/db/MADO` (id 92) and `/db/DOEL`
  (id 4) drop writes like the three in A-3, but on **populated** tables, so a
  server-side renumber is not ruled out. They are named in A-3's prose as
  unexplained rather than claimed as the same defect.
