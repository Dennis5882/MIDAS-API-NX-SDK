# Changelog

This file records changes to the JavaScript/TypeScript package published on
npm as `midas-nx`. Python package history is tracked separately in the
repository's `docs/release_notes_v*.md` files and `py-v*` GitHub Releases.

## Unreleased

## 2.4.0 - 2026-08-27

### Fixed

- **`db.staticLoads.nodalMass` could crash a live MIDAS NX session.** Creating or
  updating a nodal mass without `rmX`/`rmY`/`rmZ` sent the payload to the product
  unchanged. Omitting those three fields has been observed to hang the call and
  end the NX session across both Gen NX and Civil NX; the Python package has
  filled them with their documented default of `0` since 2026-07-29, and this
  package shipped without that protection. `create()` and `update()` now apply the
  same defaults, without overriding any value the caller supplied.

### Added

- `DbResourceMetadata.payloadDefaults`, generated from the new language-neutral
  endpoint contracts in `contracts/`, so an endpoint's safety rules reach both the
  npm and PyPI packages instead of only whichever one they were written in. CI
  fails when either package stops honouring a contract.

## 2.3.4 - 2026-08-27

### Added

- Package-local changelog and an npm release checklist for the independent
  `js-v*` release stream.

### Changed

- Added separate npm trusted-publishing automation for `js-v*` GitHub
  Releases, independent from the Python `py-v*` release stream.

## 2.3.3 - 2026-08-26

### Changed

- Hardened destructive-operation safeguards and kept per-ID deletion
  deliberately sequential.
- Expanded result-table option types and generated operation/table typings.
- Propagated live-verification safety warnings into the published TypeScript
  declarations and added CI checks for those warnings.
- Added packed-artifact smoke tests for both CommonJS and ESM consumers on
  Node.js 18 and 22.

## 2.3.2 - 2026-08-26

### Added

- Initial typed JavaScript/TypeScript SDK for MIDAS Civil NX and MIDAS Gen NX.
- Generated DB resources, operations, result-table wrappers, and payload types
  from the reviewed Python endpoint inventory.
- ESM, CommonJS, and TypeScript declaration outputs.
- Client, document, operation, table, error, and safety APIs with Vitest and
  TypeScript validation.
