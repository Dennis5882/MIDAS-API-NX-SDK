# How endpoints are verified

This project distinguishes four different claims. They are not degrees of the
same thing — they answer different questions, and conflating them is how an
SDK ends up confidently sending a request shape no server accepts.

| Claim | What it proves | What it does **not** prove |
| --- | --- | --- |
| **Implemented** | The endpoint is wrapped, typed, and unit-tested against a mocked server. | That the real server accepts it. |
| **Live read** | The route exists on a real product, answers, and the response parses. | That this SDK's *request* shape is right. |
| **Live write** | A create / update / delete round trip was watched succeeding, and the change was read back. | That it behaves the same on the other product, or another build. |
| **Not verified** | — | Nothing either way. It is not "broken", it is unmeasured. |

Current counts are in
[ROADMAP.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/ROADMAP.md),
regenerated from `docs/coverage.json`.

## Why read and write are counted separately

A GET that answers tells you the route is real. It tells you almost nothing
about whether the payload this SDK *sends* is correct, because a GET has no
payload.

Nearly every substantive defect found in this project was invisible to reads:

- `/db/REBW` — **every field name** in the manual's specification table was
  wrong. Found by reading real populated data back from a production model and
  confirming with a live PUT round trip.
- `/db/TDMT` — the documented code-name enum was wrong; the server wants
  `"European"`, not any CEB-FIP spelling.
- `/db/SECF` — documented as keyed by element id; it is keyed by section id.
- `/db/PRES` — the documented default `DIRECTION` is rejected.
- `/db/MVHL` — silently downgrades a standard vehicle to a user-defined one
  when `VEHICLE_LOAD_NUM` isn't 1, and answers as if it succeeded.

Every one of those endpoints answered a GET perfectly well the whole time.

## How the evidence is recorded

Each endpoint in `docs/coverage.json` carries what was actually observed:

```json
"live_verified": {
  "date": "2026-08-02",
  "products": ["gen"],
  "level": "write",
  "method": "scripts/live_crud_check.py (full CRUD round trip)",
  "nx_versions": { "gen": "MIDAS Gen NX 2026 (v2.1), build 07/30/2026" }
}
```

`level` is `"write"` only when something was actually mutated — model data, or
a file on the NX host. A POST that the server refused before doing anything is
`"read"`; the HTTP verb does not decide this. `/post/TABLE` is a POST and a
read.

Product and build are recorded because they matter: the same endpoint has been
seen present on one product and 404 on the other, and behaviour has changed
between builds of the same version.

## Where the write evidence comes from

`scripts/live_crud_check.py` runs create → read → update → read → delete →
read against real resources, in dependency-ordered tiers. A case is marked
`confirmed` only after somebody has watched it pass.

It separates a **regression** (a previously-confirmed case now failing — treat
as an SDK defect, exit 1) from an **unverified failure** (a case that has
never passed, so triage the fixture first, exit 3). That distinction exists
because on the first run, *every* failure turned out to be a bad fixture or a
wrong documented value rather than an SDK bug.

## What these numbers do not claim

- Evidence comes from a small number of accounts, licence tiers and builds.
  An endpoint marked verified on Civil NX may behave differently on Gen NX,
  and vice versa.
- A verified endpoint can still break when MIDAS IT ships a product update.
  Nothing here is a continuous check — CI never touches a live product.
- Verification records what happened once, under one model state. Endpoints
  whose behaviour depends on model contents (design checks, result tables) can
  behave differently against a model with real analysis results than against
  an empty one, and the entry says which was used.

Negative results are kept, not deleted. An endpoint that 404s on one product,
or a call that crashed a session, is recorded as such — a documentation set
that only records successes is not evidence.
