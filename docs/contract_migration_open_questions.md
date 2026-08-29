# Contract migration open questions

## Existing unresolved decision

- The 63 `/DESIGN/*` contracts carry Korean labels from the manual while both
  SDKs use English labels. The TypeScript generator's shadow gate currently
  compares only `/db/*`; do not widen that filter until the author selects the
  canonical labels.

## Conditional payload transcription

- `/db/FBLA` documents four fields for `FLOOR_DIST_TYPE = 1 or 2`.
  `appliesWhen` currently represents an array as logical AND and each condition
  supports one scalar `equals`, so the manual's OR cannot be transcribed without
  changing the schema (for example, an explicitly reviewed `oneOf`/`in`
  predicate) or duplicating wire fields. Duplicating fields would make the
  contract ambiguous, so this table remains unmerged pending an author decision.
