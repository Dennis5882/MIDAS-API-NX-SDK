# midas-nx 2.10.0

A shared PyPI/npm version release. **Civil NX can now use Soil Properties
(`/db/POSP`)**, and npm's types stop asking one product for fields only the
other one has. Everything is additive or a loosening: nothing that worked
with 2.9.3 stops working, and no export is added, removed or renamed.

| surface | what actually changed |
| --- | --- |
| Python | `SoilProperty` (`/db/POSP`) answers on Civil NX as well as Gen NX; `SoilPropertyPayload` gains `STR_HEIGHT` and `STR_WIDTH` and `SoilPropertyItem` gains `POISSON` (Civil NX only). Docstrings on `ColumnRebar` and `GEN_ONLY`. The README (the PyPI page) now says what a MAPI key is and where the quickstart shows how to get one |
| npm | `soilProperty` answers on Civil NX, with the same three optional fields. 27 members that only one product declares become optional; `SectionPayload`'s `USE_HAMBLY_EQ` and `SectionReinforcementPayload`'s `CONTRIBUTION_FACTOR` (Civil NX only) are added. JSDoc for `/db/MATD`'s three ratio fields; README links point at the npm quickstart |

## Civil NX gained `/db/POSP`

MIDAS Civil NX 2026 v2.2 **Build 10/10/2026** answers Soil Properties, which
until Build 09/24/2026 returned 404 on Civil. Civil's record is not Gen's:

| Only on Civil NX | Only on Gen NX |
| --- | --- |
| `STR_HEIGHT`, `STR_WIDTH`, `ITEMS[].POISSON` | `OPT_USE_N`, `ITEMS[].ANGLE_OR_N` |

Civil refuses Gen's record with `Wrong Field`. A Civil create / read /
update / delete round trip passed through both SDKs on 2026-10-11. None of
the three Civil fields is in MIDAS IT's manual; they come from Civil's own
`/info` schema. Upgrade both products to Build 10/10/2026 or later before
calling it on Civil - an older Civil build still answers 404.

## npm: fields one product cannot send are no longer required

A field the manual marks required but only one product declares was typed
required on a resource both products answer, so a caller on the other product
had to send a field their product refuses - a Civil NX caller of
`soilProperty` had to send `ANGLE_OR_N`. 26 such fields across eight
endpoints (`/db/ELEM`, `/db/EPSE`, `/db/IEHC`, `/db/POLC`, `/db/POSL`,
`/db/POSP`, `/db/SBDO`, `/db/SPLC`), 27 type members, are now optional and
say "Gen NX only; required there." (or Civil NX) in their documentation. If
you target that product, still send them.

## Verified on the new build

Every confirmed live case - 419 endpoint-product pairs over 236 endpoints -
was replayed on Build 10/10/2026 through both SDKs on both products on
2026-10-11. Nothing regressed.

## Not in either package

The vendor issue report moved to v1.5 (unsent), the manual sync is at
MIDAS-API `0b27438`, and the live-verification records gained the 2026-10-04
to 2026-10-11 sessions, including one `/doc/NEW` that ended Gen NX on an empty
document (one occurrence, cause unknown).
