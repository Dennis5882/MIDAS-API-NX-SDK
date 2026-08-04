# Recipes

A recipe is a complete, runnable script for one structural-engineering task
— not a snippet. Each one states its risk level, which product it's proven
against, and whether that verification came from a live Gen NX/Civil NX
session or just a mocked test, so you know what you're actually trusting
before you run it against a real model.

Start with [Getting started](../en/quickstart.md) first if you haven't —
these assume you already have `midas-nx` installed and a MAPI-Key.

## Available recipes

| Recipe | Risk level | What it does |
| --- | --- | --- |
| [Inspect a project](inspect-project.md) | 1 — read-only | Connect and print a one-screen summary of the current model |
| [Read nodes and elements](read-nodes-and-elements.md) | 1 — read-only | List and filter the model's geometry |
| [Extract a result table](get-results.md) | 1 — read-only | Pull reaction forces out of an already-analyzed model |

All three are read-only (risk level 1 — see
[Risk levels](../safety.md#risk-levels)): none of them can create, change,
or delete anything, so they're safe to run against a real model.

## Recipe format

Every recipe follows the same structure so you can skim past what you
already know: purpose, a pre-run checklist, inputs, the full code, what it
does, expected output, how to verify the result, common errors, whether a
timeout is safe to retry, and a prompt you can hand an AI assistant to
adapt it. This mirrors the recipe standard in
[`docs/planning/onboarding_plan_active.md`](https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/planning/onboarding_plan_active.md#11-실무-recipe-표준).

More recipes (creating nodes/elements, assigning loads, construction
stages) will follow based on which of these three actually get used —
see `PLAN.md`'s Phase 8 note on why the list starts small.
