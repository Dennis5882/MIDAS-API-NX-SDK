# npm release checklist

The npm and PyPI packages share the `midas-nx` name but have independent
versions. This checklist is only for the JavaScript/TypeScript package.

## Before publishing

1. Confirm the change affects npm-packaged behavior, declarations, metadata,
   or documentation. Repository-only CI/docs changes do not require a bump.
2. Move the entries under `CHANGELOG.md`'s `Unreleased` heading into a new
   `X.Y.Z - YYYY-MM-DD` section. Keep an empty `Unreleased` heading at the top.
3. Update both npm version files:

   ```bash
   cd packages/typescript
   npm version X.Y.Z --no-git-tag-version
   ```

4. Regenerate and verify the package:

   ```bash
   npm run generate
   npm run prepack
   npm pack --dry-run
   ```

5. Review the generated files, package contents, `package.json`,
   `package-lock.json`, and `CHANGELOG.md`, then commit and push to `main`.

## GitHub Release

Create a GitHub Release with tag `js-vX.Y.Z`. When GitHub asks for the
previous tag, select the preceding `js-v*` tag explicitly; automatic selection
can choose a `py-v*` release from the independent Python stream.

Use this release-note template:

````markdown
## Highlights

- <The most important customer-visible improvement>

## Added

- <New APIs, types, or supported workflows>

## Changed

- <Behavior or developer-experience changes>

## Fixed

- <Corrected behavior or typings>

## Safety and compatibility

- Breaking changes: None
- Safety notes: <Relevant warning, or "No new safety warnings">
- Runtime: Node.js 18 or newer

## Install

```bash
npm install midas-nx@X.Y.Z
```

Full npm changelog: `packages/typescript/CHANGELOG.md`
````

Remove empty sections before publishing. Publishing the `js-v*` GitHub
Release triggers `.github/workflows/publish-npm.yml`; do not run
`npm publish` manually.

## After publishing

1. Confirm the workflow completed successfully.
2. Run `npm view midas-nx version dist-tags --json`.
3. Install the exact version in a clean temporary project and verify both ESM
   import and CommonJS `require()`.
4. Confirm the npm package page shows the expected README, changelog file in
   the tarball, and provenance information.
