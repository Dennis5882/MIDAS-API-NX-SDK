# `contracts/` — the language-neutral source of truth

Everything in this directory describes the **MIDAS NX Open API itself**, not any
SDK that wraps it. The Python package and the npm package are two equal
implementations of what is written here. Neither one outranks the other, and
neither one is a source for the other.

## Why this exists

`POST /db/NMAS` crashes MIDAS NX when the optional `rmX`/`rmY`/`rmZ` fields are
omitted. That was root-caused on **2026-07-29** and worked around in
`NodalMass.create()` the same day. The npm package shipped on **2026-08-26** — a
month later, generated from that same Python source — **without the workaround**,
so any caller reaching `/db/NMAS` through it could still hang and kill a live NX
session.

That was not carelessness. The generator carried metadata and docstrings across;
the workaround was *behaviour* inside a method, and behaviour had nowhere to
live. A safety rule that exists only inside one implementation reaches only that
implementation's users.

So the rule moved here, where it is a fact about the endpoint rather than a
property of one language binding, and
[`scripts/validate_contracts.py`](../scripts/validate_contracts.py) fails CI when
an implementation does not honour it.

## Permitted sources

| Source | Use it for |
| --- | --- |
| [`Dennis5882/MIDAS-API`](https://github.com/Dennis5882/MIDAS-API) `docs/manual/*.md` | Field names, types, defaults, requiredness, enums, methods |
| `docs/live_verification_notes.md` | What a real Gen NX / Civil NX session actually did |
| `GET /info{endpoint}` | The server's own schema, for endpoints the manual describes poorly |

**Forbidden as a source: `src/midas_nx/` and `packages/typescript/src/`.** Not
because they are untrustworthy — much of what is recorded here was learned while
building them — but because a contract derived from an implementation cannot
detect that implementation being wrong. `validate_contracts.py` reads both SDKs,
and it reads them as *subjects under test*: when a contract and an SDK disagree,
the finding is an SDK defect. Fixing it by editing the contract defeats the whole
arrangement.

Every field records where it came from in `provenance`:

- `manual` — transcribed from the manual chapter
- `live_verified` — the manual's claim was checked against a running product
- `live_corrected` — the manual was wrong and a live check replaced it (record
  the mismatch under `manualDefects` so a manual re-sync cannot quietly restore
  the error)
- `info_schema` — taken from `GET /info{endpoint}`

There is deliberately no value meaning "read off an SDK". Do not guess a field or
a behaviour into existence: if the manual does not describe it and nobody has
observed it, it does not belong in a contract.

## `documentedOptional` versus `safeToOmit`

These are modelled separately, and the distinction is the single most important
thing in this schema.

- `documentedOptional` is a statement about **the documentation**.
- `safeToOmit` is a statement about **the product**.

`/db/NMAS`'s `rmX` is `documentedOptional: true` and `safeToOmit: false`. The
manual is correct that the field is optional, and following the manual kills the
session. Collapsing the two into one boolean loses exactly the case that hurts
people — the caller who read the documentation and did what it said.

`safeToOmit` has three values, and `unverified` is not a lesser one:

| Value | Means | Requires |
| --- | --- | --- |
| `true` | A live call omitted it and succeeded | `omissionEvidence` citing that call |
| `false` | Someone omitted it and something broke | `omissionEffect`, plus an `sdkRule` if the field is also documentedOptional |
| `unverified` | Nobody has omitted it against a running product | nothing |

Most fields are `unverified`, and saying so is the point. "The manual says
Optional" is **not** evidence for `true` — that is what `documentedOptional`
already records, and treating it as an answer is precisely the reasoning
`/db/NMAS` punishes. The first two contracts written by hand got this wrong and
were corrected: their coordinates and translational masses now read `unverified`,
because `scripts/live_crud_check.py`'s confirmed payloads send all of them.

Where evidence does exist, it is mechanical: 116 cases in that checker are marked
`confirmed=True`, meaning someone watched that exact payload complete a live
round trip. A documented field absent from such a payload was omitted and the
call still worked. `scripts/extract_contracts.py` reads those payloads and fills
in `safeToOmit: true` with the case cited — 437 fields across 72 endpoints.

## Risk and mitigation are separate axes

`risk` describes the endpoint. `mitigation` describes what the SDKs do about it.

`/db/NMAS`'s POST stays `risk: product_crash_risk` with
`mitigation: normalized`: the server defect is real and present on shipped
builds, while the SDK rule makes the crashing payload unreachable. Downgrading
the risk because it has been mitigated would erase the reason the rule exists,
and the next person to read the contract would delete the rule as ceremony.

Mitigations, in rough order of how much they cost the caller:

| `mitigation` | Meaning |
| --- | --- |
| `normalized` | The SDK fixes the payload silently. The caller needs to know nothing. |
| `confirmation_required` | The call is refused without an explicit confirmation flag. |
| `opt_in_required` | The call is refused unless the caller opts into a known hazard. |
| `warn_only` | Documented loudly; no behaviour change. |
| `none` | Nothing is done. |

Prefer `normalized` where a correct payload is knowable. Requiring a caller to
opt into a hazard the SDK could simply have avoided is a worse outcome, not a
safer one.

## Layout

```
contracts/
  README.md                          this file
  schema/
    endpoint-contract.schema.json    JSON Schema for contracts/endpoints/*.yaml
  endpoints/
    db-node.yaml                     one file per endpoint; file name == `id`
    db-nmas.yaml
    db-grup.yaml  db-rigd.yaml  db-offs.yaml  db-co-m.yaml
  drafts/                            git-ignored; `draft: true`, not contracts
  safety/
    known-product-risks.yaml         cross-endpoint client rules + product defects
  verification/
    gen-nx.yaml                      dated, build-specific live findings
    civil-nx.yaml
```

Verification records are split per product on purpose. Product support is an
observed fact rather than a manual claim, and the two products diverge: `/db/REBW`
answers on Gen only, the Hyper-S (`-M1`) family on Civil only, and 32 of 47
endpoints the manual frames as Civil-only answer on Gen too. A single shared
record cannot carry a per-product date and build.

## Working on a contract

```bash
pip install -e ".[dev]"          # brings in pyyaml + jsonschema
python scripts/validate_contracts.py
python scripts/validate_contracts.py --no-parity   # schema + refs only
pytest tests/test_contracts.py
```

`validate_contracts.py` checks, in order: schema conformance; that every
`riskRef` and verification `ref` resolves; that `product_crash_risk` operations
carry a mitigation, a rule and a risk reference; that unsafe-to-omit optional
fields are covered by a rule; that a normalization value equals the field's
documented default (a rule may make a default explicit, never invent one); and
that the endpoint, products, methods and normalization rules each contract
declares match both SDKs.

## Adding a contract for an endpoint

Start from a machine-drafted transcription rather than retyping a table:

```bash
python scripts/extract_contracts.py                       # what is parseable
python scripts/extract_contracts.py --emit /db/STLD       # draft one endpoint
python scripts/extract_contracts.py --check               # promoted vs. manual
```

`--emit` writes to `contracts/drafts/`, which is **git-ignored and ignored by the
validator**. Every draft carries `draft: true`, which the schema forbids, so a
file moved into `contracts/endpoints/` without being read fails CI with one
unambiguous message rather than passing as fact.

Of roughly 4,770 fields the extractor can read, about a third carry a review note
— no Default column, an enum whose values live elsewhere in the chapter, a row
naming two keys at once, a condition the manual gestures at but never states.
Those notes travel into the draft. Clear them; don't delete them.

Then:

1. Read the endpoint's chapter in the manual repo yourself. The draft is a
   starting point, not a review. Fields keep `provenance: manual`.
2. Check `docs/live_verification_notes.md` for anything observed about it. Where
   live behaviour contradicts the manual, the contract records live behaviour,
   `manualDefects` records the mismatch, and the field's `provenance` becomes
   `live_corrected`.
3. Set `verification.status` honestly. `manual_only` means transcribed but never
   called — it is not a lesser state, it is the truthful one.
4. Add `sdkRules` for anything a caller could reasonably do that breaks the
   product.
5. Run `npm run generate` from `packages/typescript/` and
   `python scripts/validate_contracts.py`. Both SDKs must satisfy the contract
   before it lands.

## Migration status

Six endpoints are contracted. The remaining ledger lives in `docs/coverage.json`
(399 endpoints) and is being migrated incrementally, so an endpoint without a
contract is expected rather than a defect. What is *not* optional is that a
contract, once written, is honoured by both SDKs.

What the extractor can currently reach, per `scripts/extract_contracts.py`:

| | |
| --- | --- |
| Endpoint sections found across chapters 01-17 and 24-27 | 386 |
| ...with a parameter table it can parse | 370 |
| ...whose methods the manual actually states | 110 |
| Fields transcribed | ~4,770, of which ~180 nested |
| Fields given `safeToOmit: true` from a confirmed live payload | 437, across 72 endpoints |
| Drafts with no review note and no unmerged variant table | 130 |
| Sections with conditional variant tables left unmerged | 58 |
| Sections belonging to the shared `/post/TABLE` family | 89 |

The 89 `/post/TABLE` sections (chapters 18-23) are one endpoint selected by a
`TABLE_TYPE` string, with response `HEAD` columns instead of a request payload.
They need a two-layer contract — endpoint plus table — which the schema does not
model yet, so the extractor reports them rather than flattening them into
endpoint contracts.

Still to come: that two-layer model; reversal of the remaining Python-to-npm
generation; and folding `docs/coverage.json` into `contracts/verification/` so
there is one ledger rather than two.
