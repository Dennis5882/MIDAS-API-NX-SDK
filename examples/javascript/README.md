# JavaScript examples

Runnable scripts for the npm package. Each one is the twin of the file with
the same name in [`../python/`](../python/), so you can compare the two SDKs
line for line.

| Script | Risk level | What it does |
| --- | --- | --- |
| [`verify-and-read.mjs`](verify-and-read.mjs) | **1 — read-only** | Checks the connection and counts the nodes in the open model. Safe against a real project. |
| [`quickstart.mjs`](quickstart.mjs) | **4 — high** | Builds a one-column model from scratch. **Discards unsaved work in the open document.** |

Risk levels are explained in
[the safety guide](https://dennis5882.github.io/MIDAS-API-NX-SDK/safety/#risk-levels).
Start with the read-only one.

## Running them

You need Node.js 18 or newer, MIDAS Gen NX or Civil NX running with the Open
API connected, and a MAPI key. If you do not have a key yet, step 3 of the
[quickstart guide](https://dennis5882.github.io/MIDAS-API-NX-SDK/en/quickstart/#step-3-get-a-mapi-key)
shows where to find it in the product.

```bash
npm install midas-nx
```

```bash
# macOS / Linux
export MIDAS_MAPI_KEY="your-mapi-key-here"
node verify-and-read.mjs
```

```powershell
# Windows PowerShell
$env:MIDAS_MAPI_KEY = "your-mapi-key-here"
node verify-and-read.mjs
```

Both scripts default to Gen NX. For Civil NX, change `product: "gen"` to
`product: "civil"` at the top of the file.

`MIDAS_BASE_URL` is optional and only needed if your relay is not the default.

## Before you run the second one

`quickstart.mjs` calls `doc.newProject()`, which discards unsaved work in
whatever document is currently open — including work that has nothing to do
with this script. Open a blank project first, or one you do not mind losing
changes in. The HTTP call answers the same either way, so there is no error to
catch afterwards.
