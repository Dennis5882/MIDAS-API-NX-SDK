# midas-nx 2.10.4

A shared PyPI/npm version release that changes what two load resources send.

> **Behaviour change.** Nodal loads and beam loads now fill documented
> defaults into every `ITEMS` entry that omits them, on `create()` and
> `update()`. If your code relied on a PUT keeping a field it left out, that
> field is now set to its default. The product never kept it either: it copied
> the value from the record's first entry.

| surface | what actually changed |
| --- | --- |
| Python | `NodalLoad` (`/db/CNLD`) and `BeamLoad` (`/db/BMLD`) fill entry defaults in `create()` and `update()`. No other module changed |
| npm | `nodalLoad` and `beamLoad` do the same. `DbResourceMetadata.payloadDefaults` keys can now be paths such as `ITEMS[].FX`. No type or export is added, removed or changed |

## Why: a PUT copies omitted fields from the first entry

Measured on Gen NX (Build 10/17/2026). A PUT onto a load record that already
has entries does not replace its `ITEMS` list. It merges by `ID`: entries you
don't name stay, a named one is rewritten, a new one is added. Every field the
new or rewritten entry leaves out takes the value of the record's **first**
entry, and the response reports no error:

- a nodal load sent with `FY` only was stored with the first entry's `FZ`;
- a uniform beam load added beside an eccentric one was stored eccentric,
  with the first entry's eccentricity direction, type and distances;
- a new load on either endpoint joined the first entry's load group.

On a record with no entries the same omission stores the documented default.

What the SDKs now send when you leave a field out:

- **`/db/CNLD`**: `GROUP_NAME` as `""`, and `FX`, `FY`, `FZ`, `MX`, `MY`, `MZ`
  as `0`.
- **`/db/BMLD`**: every documented-optional member at its documented default,
  except `D` and `P`, which carry the load itself. That is `GROUP_NAME`,
  `USE_PROJECTION`, the eccentricity fields and the `ADDITIONAL` fields.

A value you send is never replaced. A raw `client.request()` is not changed:
send every field of every entry yourself.

If your app updates loads through the raw `request()`, it is still exposed.
Send every field of every entry. Two entries for the same load case on one
node are summed into one by the product, so send one per case.

## Also recorded (no code change)

- A per-id `DELETE` of a section or material succeeds while elements still
  use it, and leaves those elements pointing at an id that no longer exists.
  Read the elements first and delete only unused ids.
- A section with `USE_WARPING_EFFECT: true` can only be used by BEAM
  elements. A TRUSS on one is refused with a "7th DOF" error. When changing an
  element's type and its section together, change the element first.
- For large models, the results recipe now shows how to read load-case tables
  and add up combinations yourself, measured to match the product's own
  combination table within rounding:
  https://dennis5882.github.io/MIDAS-API-NX-SDK/recipes/get-results/

The full measurements are in
https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/docs/live_verification_notes.md.
Civil NX was not connected for these sessions, so nothing here was measured
there.
