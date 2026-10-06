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
| A-2 | `DELETE {endpoint}` with an ID-keyed `"Assign"` empties the whole table | **2026-10-06**, Build 09/24/2026, both products, on a dummy model |
| A-3 | 10 endpoints where a write is accepted, echoed back and not stored | **Build 09/24/2026**, all ten: CONS, MVHL, SECF, SPLC (Gen), STCT (both, Civil first measured) on 2026-10-06; MATD (Civil) 2026-10-04; SSEIS, SBDO, SINF, MVLDpl 2026-09-27 |
| A-4 | error bodies under HTTP 200 / 201 | **2026-10-06**: every refusal that day under 201, `/db/STCT`'s under 200 |
| A-5 | `/mapikey/verify` answers `connected` after the product is gone | **2026-09-21**, incidentally — it answered `connected` twice while Gen was held by a modal |
| A-6 | `"Wrong Field"` means a bad value, not a bad field name | **2026-10-06**, both products (`NOT-A-CODE` / `Russian`) |
| A-7 | a write to a path the account cannot write to blocks the session | Civil **2026-10-06** (same chain, absence checked on disk); Gen 2026-09-21 - not repeated, it blocks the session |
| A-8 | `/info` is not served for `/DESIGN/*` or the Hyper-S `IEHG` trio | **2026-10-06**, both products |
| A-9 | `/info` disagrees with the server in both directions | **2026-10-06**; see the correction below |
| A-10 | 9 endpoints + `/db/RPSC` + REBB/REBC/REBW whose write path has never passed — **an ask, not a defect claim** | **Build 09/24/2026** (2026-09-27; REB* 2026-10-04 on Gen), each on the product that declares it |
| B-1…B-3 | documentation items, each checked against the official article | 2026-07-27 |
| B-4, B-5 | REBW / REBC articles vs the server | **resolved by MIDASIT's 2026-09-28 revision**, read from the Help Center API on 2026-10-06; one residue each (REBW `vSTORY_KEY` vs `/info` `vSTORY_NAME`; REBC's Parameters row spelling `"DO"` beside the schema's `D0`) |

### Re-verification debt

Cleared on 2026-09-21 in two passes: the fixture replay, then a dummy model
built for the items a replay cannot reach. Two are left, and each needs
something a scratch model cannot supply:

- **A-5's original form** — the *crash* window still needs the product killed
  and then polled. The modal-block form was measured on 2026-09-21.
- ~~**`/db/STCT` on Civil**~~ — **cleared 2026-10-06** by a PUT of the record
  the first `POST /db/STAG` creates: `iITER`/`TOL` echoed, absent from the GET,
  with `iINC_NLA` 0 and 1 alike. The fixture case still POSTs on Civil and so
  still cannot measure it; that is a fixture change nobody has made.

**No build string was read on 2026-09-21.** The API reports none. A fresh
GET-only `/info` sweep of both products matched the Build 09/15/2026 surface
exactly (one already-recorded `/db/SECT` delta against the 2026-09-03
baseline), which says the surface is unchanged and nothing more — `/db/NMAS`
is the standing proof that behaviour moves while `/info` does not.

### Corrected by the 2026-09-21 re-measurement

- **A-7 was misread the same day it was measured, and is now settled.** The
  first Civil probe called `/doc/OPEN` on the Program Files path, caught no
  exception, and printed "the file exists" without printing the answer, which
  was `path is wrong (the file can't open)`. On that reading the report briefly
  said Civil's save *succeeded* and floated elevation or UAC virtualization as
  the reason. The author then found the file in neither `Program Files` nor the
  VirtualStore, and Windows refused a GUI Save As to that folder outright. So
  neither product wrote anything; they differ only in how they say so. Civil
  answers `command complete`, byte-identical to a real save, while the very
  next `/doc/OPEN` reports the file missing; Gen raises a modal and never
  answers. Same lesson as `/db/STCT` below: print the response, not a
  conclusion about it.
- **`/doc/SAVEAS`'s two failure shapes are per-product, not per-path.** A
  save that never happened answers `{"message": "... command complete"}`
  (2026-07-26, and Civil on 2026-09-21 for a folder it cannot write to). Gen,
  given that same folder, **does not answer at all** - the call hangs until the
  dialog is dismissed. This entry first drew the line by path; the Civil half
  of A-7 above is what moved it.

- **`/db/SECF` got sharper.** The report recorded a 200 with no error. The
  product actually **echoes the whole record back** while `GET` answers
  `{"message": ""}` — the same signature as `/db/CONS` and `/db/MATD`.
- **`/db/STCT`'s Civil block was misattributed, twice within a day.** The
  batch recorded it as Civil pre-populating the record; the harness's own
  message said `a seed in this selection owns it`, and a direct measurement
  showed neither product pre-populates it. Recorded because the correction
  matters more than the finding: both of the day's wrong readings came from
  taking a harness result without reading what the harness said about it.
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

### Corrected in v1.5 (2026-10-06)

- **A-3 `/db/STCT` and `/db/MVLDpl` were stated as both-product.** STCT's
  Civil half had never been measured - it was then, on 2026-10-06, and it
  reproduces, so the both-product wording is right now and was unearned in
  v1.4. MVLDpl's case exists on Civil only. v1.4's explanation for STCT
  (`iNLA_TYPE` 1, Accumulative) is withdrawn: the fixture payload sends 0 and
  loses the same two fields.
  Same lesson as the 2026-09-21 corrections: a product scope in the report has
  to come from a ledger or case record, not from the batch it arrived with.
- **A-10 said "identical on both products"** for a list that includes
  Gen-only `/db/EPST`/`/db/EPSE` and Civil-only `/db/WVLD`.

## Held, with the reason

### Civil `CD-ANAL` ending the session — one reproduction, trigger not isolated

2026-09-29, Build 09/24/2026: `/DESIGN/RC/KDS-41-20-2022/CD-ANAL` on a solved
Civil model with no RC design code (Civil refuses RC `DCO`) never answered, and
Civil NX had to be restarted. Recorded as the known risk
`design-rc-cd-anal-without-design-code-kills-civil`. It is a crash, which is
the class of finding this report exists for, but it rests on **one run**, and
whether the missing design code is the trigger is a guess. A-1 went in with 15
reproductions and a root cause. Reproducing it means killing Civil again, so
whether to spend that is the author's call; until then it stays out.


### `/db/FIMP`'s printed example — closed, not a vendor item

The chapter prints `ECU=0.003`, `Z=100`, `EC0=0.002` and the product refuses
the POST with its own rule, `Epsilon_cu > 0.8 / Z + Epsilon_co`. This was held
until the official article had been read, and on 2026-09-28 it was: article
35944335180569 prints a different Kent & Park body (`EC1_METHOD: 0`,
`EC1: 0.0025`, `STRENGTH_AFTER: 1`, no `Z`), which both products accept, as
they accept the article's other 18 examples. The defect is the vendored
chapter's transcription (**MD-54**, re-attributed), so there is nothing to
send. The hold did its job: this would have been a false B-item.

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

### Two observations from 2026-10-06, not yet claims

- **`/db/POSL` on Civil stores `FA` 1.4 / `FV` 1.5 for a POST of 1.0 / 1.4**,
  and the POST response echoes 1.0 / 1.4. The stored values look like the
  site coefficients a code table gives for `SC: "S2"` with `SRF: 0.22`, so the
  server may be deriving them by design. That would still be the A-3
  signature (the response says what was not stored), but whether the user
  value is meant to be honoured has not been asked of any source.
- **`/db/STCT` on Gen reads back only ten keys** for the fixture payload -
  `bCONV`, `bTRUSS`, `bBEAM`, `bCAMBER`, `bCHANGE_CABLE` sent `true` are
  absent as well as `iITER`/`TOL` - where Civil keeps all five, and where Gen
  kept them on 2026-09-18 with the manual's payload (`iNLA_TYPE` 1). Looks
  mode-dependent; not isolated. Gen also refuses `iINC_NLA: 1` without
  `iLSTEP` (`Item:Number of Load Steps`), which Civil fills in itself.

## Not candidates

These look like findings in the coverage tables and are not ours to report,
or not through this report.

- **`/db/MATD`'s `bSERVCHECK` default.** The manual's 2026-10-04 table says
  `true`; a fresh Gen material reads `false`. A documentation finding, and
  since v1.4 those go through the manual channel rather than this report. It
  is recorded under the contract's `manualDefects`.

The rest are not ours to report at all.
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
