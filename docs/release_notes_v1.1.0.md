## Manual sync

The sibling `MIDAS-API` manual repo had drifted 3 commits (`aeca675` → `7167365`)
since this SDK last vendored it. `scripts/check_manual_drift.py` flagged 3
changed chapters; all three turned out to affect shipped behavior, not just
prose. `docs/coverage.json`'s `vendored_at_commit` is now current
(`has_diff: false`).

## ⚠️ Breaking

### Wall Force no longer accepts `sect_position`/`parts`

`get_table()` drops its `sect_position` parameter entirely, and
`get_wall_force_table()` drops both `sect_position` and `parts`. MIDASIT
confirmed (internal Jira `MAPI-2012`) that the Wall Force table type
(`WALL_FORCE_MOMENT`) never actually supported either field — this SDK's
fields were inferred from the official article's JSON Schema alone, since
neither the Specifications table nor the worked example ever described them,
and the official article has since dropped both. If you were passing either
argument to `get_wall_force_table()`, remove it — the server was never acting
on it either way.

## Fixed

- **`STORY_DRIFT_METHOD`'s first enum value, for Story Stability Coefficient
  specifically, is `"Drift on the Center of Mass"`, not `"...at..."`.** An
  earlier release (v0.11.2) normalized a manual typo (`"Drfit on..."`) by
  assuming this table shared the same enum wording as Stiffness Irregularity
  Check (#13) and Weight Irregularity Check (#17), both of which do use
  `"at"`. MIDASIT confirmed via internal Jira (`MAPI-2009`) that assumption
  was wrong for this specific table — the product screen genuinely says
  `"on"`. Only the spelling was ever a real typo; the preposition was correct
  as originally written.

## Added

- **`VehicleKsceLsd15Params`** (`db/moving_loads.py`) — the `VEH_KSCE_LSD15`
  schema KSCE-LSD15 vehicles actually use instead of `VEH_DEFAULT`. Previously
  only known to exist via `GET /info/db/MVHL` and left as an untyped extra
  key. Also documents that `MVLD_CODE` should be `13` for this shape, not `1`
  — an older manual worked example used `1`, which the official article has
  since corrected.
- **`ADDITIONAL.SET_ANGLE`** on Ultimate Story Shear Force Check (`post/story.py`
  `get_ultimate_story_shear_force_check_table()`) — newly documented by
  MIDASIT, previously undocumented entirely. Optional, defaults to `ANGLE=0`.

## Maintenance

- Fixed a bug in `scripts/check_manual_drift.py`: ledger entries whose
  `chapter_file` spans multiple chapters (e.g.
  `"19_....md / 20_....md"`) never matched an individual changed filename,
  producing a false "not yet implemented" report. It now splits on `" / "`
  before matching.
- `PLAN.md` was 4 days stale (still describing the pre-v1.0.0 state) because
  the release checklist in `CLAUDE.md` never actually included a step to
  update it. Both are now synced, and the checklist folds the PLAN.md update
  into the same commit as the code changes going forward.
