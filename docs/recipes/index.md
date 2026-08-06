# Recipes

A recipe is a complete, runnable script for one structural-engineering task
— not a snippet. Each one states its risk level, which product it's proven
against, and whether that verification came from a live Gen NX/Civil NX
session or just a mocked test, so you know what you're actually trusting
before you run it against a real model.

Start with [Getting started](../en/quickstart.md) first if you haven't —
these assume you already have `midas-nx` installed and a MAPI-Key.

## Find your task

Organized the way a MIDAS Gen NX/Civil NX model actually gets built — model
setup, then geometry, properties, boundary, loads, analysis, results. Every
category below is real (it matches an actual `midas_nx` module and a real
manual chapter), but not every category has a recipe yet. Where one doesn't
exist, the entry below still links to the closest real material —
[Reference](../reference/client.md) for the Python API, or
[ROADMAP.md](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/ROADMAP.md)
for the full endpoint list — rather than leaving a dead end.

| Task | Recipe | Reference / endpoint list |
| --- | --- | --- |
| Model setup | [Inspect a project](inspect-project.md) — Level 1 | [Document lifecycle](../reference/document.md), ch01/ch02 in ROADMAP.md |
| Nodes and elements | [Read nodes and elements](read-nodes-and-elements.md) — Level 1 | [DB resources](../reference/db.md), ch03 in ROADMAP.md |
| Materials and sections | *none yet* | `midas_nx.db.properties`, ch04 in ROADMAP.md |
| Groups and boundary conditions | *none yet* | `midas_nx.db.project` (groups), `midas_nx.db.boundary`, ch02/ch05 in ROADMAP.md |
| Static loads | *none yet* | `midas_nx.db.static_loads`, ch06 in ROADMAP.md |
| Dynamic and seismic loads | *none yet* | `midas_nx.db.dynamic_loads`, ch09 in ROADMAP.md |
| Temperature and moving loads | *none yet* | `midas_nx.db.temperature_prestress`, `midas_nx.db.moving_loads` (Civil NX only), ch07/ch08 in ROADMAP.md |
| Construction stages | *none yet* | `midas_nx.db.construction_stage`, ch10 in ROADMAP.md |
| Analysis | *none yet* | [Document lifecycle](../reference/document.md) (`doc.analyze()`), `midas_nx.db.analysis_control`, ch12 in ROADMAP.md |
| Results | [Extract a result table](get-results.md) — Level 1 | [Post and result extraction](../reference/post.md), ch18-23 in ROADMAP.md |

The three that exist are all read-only (risk level 1 — see
[Risk levels](../safety.md#risk-levels)): none of them can create, change,
or delete anything, so they're safe to run against a real model. Which of
the *none yet* rows gets a recipe next depends on which of these three
actually get used — see `PLAN.md`'s Phase 8 note.

## Recipe format

Every recipe follows the same structure so you can skim past what you
already know: purpose, a pre-run checklist, inputs, the full code, what it
does, expected output, how to verify the result, common errors, whether a
timeout is safe to retry, and a prompt you can hand an AI assistant to
adapt it. This mirrors the recipe standard in
[`docs/planning/onboarding_plan_active.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/planning/onboarding_plan_active.md#11-실무-recipe-표준).
