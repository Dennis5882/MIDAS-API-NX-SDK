# midas-nx 2.10.5

A shared PyPI/npm version release: `analyze()` now raises on two refusal
messages it used to return as success.

> **Behaviour change.** If your code calls `doc.analyze()` on a model the
> product will not analyse, it now raises (`MidasResultError` in Python, a
> rejected promise in npm) instead of returning the message. Nothing else at
> runtime changed.

| surface | what actually changed |
| --- | --- |
| Python | `doc.analyze()` raises on `"... Analysis is not allowed."` and `"error status"` as well as `"... Analysis failed."`. Docstrings of `import_mxt`, `export_mxt` and `analyze` gain the measurements below |
| npm | `doc.analyze()` does the same; `doc.importMxt()` and `doc.exportMxt()` gain JSDoc. No type or export is added, removed or changed |

## Why: a refused analysis answered like a success

Both products answer HTTP 200 with no `error` key when they refuse to run an
analysis, so neither SDK raised:

- **Gen NX** answers `{"message": "MIDAS GEN NX Analysis is not allowed."}`
- **Civil NX** answers `{"message": "error status"}`, with no product name.

Seen on a model with time-history load cases and no mass or eigenvalue
control. Both products still save the open document before refusing (Gen
keeps the previous file as `.bak`), so a refused analysis is not free of
side effects either.

## Also recorded (no code change)

Measured on Gen NX 2026-10-29/30 and Civil NX 2026-10-30, on empty documents:

- **`/doc/IMPORTMXT` replaces the whole model** - it does not add to it -
  and the document keeps its previous path, so a later save (including the
  one `analyze()` makes) overwrites the previous file. Call `save_as` /
  `saveAs` first. An import that failed on one bad line answered
  `"... command complete"` and left an empty model: read the model back.
- **Export and re-import changes `bKEEP` on Gen NX**: `/db/THIS` cases come
  back with `bKEEP: true`, because the exported line omits it. Civil NX
  keeps it.
- **`/db/THGA` is keyed by its `/db/THIS` case id.** A `NAME` that disagrees
  with the key is echoed in the response but not stored. `/db/THMS` and
  `/db/THNL` are keyed by node.
- **Time-history result tables** need case names of the form
  `"NAME(TH:max)"`, `"(TH:min)"` or `"(TH:all)"`; plain `"NAME"` or
  `"NAME(max)"` returns no rows. On Civil NX two such requests timed out and
  the open document grew to tens of GB during them; that is not yet
  understood, so try it on a copy first. See
  https://dennis5882.github.io/MIDAS-API-NX-SDK/recipes/get-results/

The full measurements are in
https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md.
