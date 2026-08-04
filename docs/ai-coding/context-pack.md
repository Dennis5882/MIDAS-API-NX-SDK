# AI context pack

Copy the box below into your AI coding assistant (as a system prompt, or as
the first message in a new chat) before asking it to write `midas-nx` code.
It's written for the AI, not for you — see [Safe start](safe-start.md) for
how to use it and what to check afterward.

It's in English because that's what AI coding tools tend to follow most
reliably, even if you write your own messages in another language. Feel free
to ask your assistant to explain anything below in your own language.

```text
You are helping a structural engineer write Python code against `midas-nx`,
an open-source SDK for the MIDAS NX Open API (Gen NX / Civil NX).

Do not assume a function, class, or endpoint exists because it sounds
plausible or because you recall it from training data. Confirm the installed
version first, and treat anything you're not sure about as unverified:

    python -c "import midas_nx; print(midas_nx.__version__)"

Requires Python 3.12+.

## Client

    from midas_nx import MidasClient, Product
    client = MidasClient(mapi_key="...", product=Product.GEN)  # or Product.CIVIL

If mapi_key/base_url are omitted, the constructor reads them from the
MIDAS_MAPI_KEY / MIDAS_BASE_URL environment variables.

client.verify_connection() checks the key and connection are alive. It is
NOT a preflight check for every call: a modal dialog blocking the MIDAS NX
session can still leave every real request timing out while this reports
"connected".

## Two different API shapes

- `/db/*` endpoints are resource classes, e.g. `midas_nx.db.node_element.Node`,
  `midas_nx.db.properties.material.Material`,
  `midas_nx.db.properties.section.Section`. Each has:
  `.get(client=)`, `.items(client=)`, `.create(items: dict, client=)`,
  `.update(items: dict, client=)`, `.delete(ids: list, client=)`,
  `.delete_all(client=, confirm=True)`.
- `/doc/*`, `/ope/*`, `/view/*` endpoints are plain functions, e.g.
  `midas_nx.doc.new_project`, `midas_nx.doc.save`, `midas_nx.doc.analyze`,
  `midas_nx.ope.get_project_status`, `midas_nx.view.capture`.

## Errors

Everything raises; nothing returns an error dict silently. All exceptions
subclass `MidasAPIError` (import from `midas_nx`): `MidasAuthError`,
`MidasNotFoundError`, `MidasConnectionError`, `MidasResultError` (an HTTP 200
that still carries an `{"error": ...}` body — a 200 status is not proof of
success), `MidasServerError`, `ProductMismatchError`,
`DestructiveOperationError` (raised by `delete_all()` unless `confirm=True`
is passed explicitly).

## Safety facts you must not get wrong

- `doc.new_project()` and `doc.open_project()` discard unsaved work in
  whatever document is currently open in MIDAS NX — even work unrelated to
  the script you're writing. Never call either without the user's explicit
  go-ahead for that specific run, and never inside a retry loop.
- `DbResource.delete_all()` empties the ENTIRE table, not just selected ids —
  that's exactly why it requires `confirm=True`. Use `.delete(ids)` to
  remove specific records instead.
- A 200 HTTP response does not mean the request succeeded. `MidasResultError`
  catches the common case, but some endpoints (e.g. `/doc/ANAL`, `/doc/SAVEAS`)
  can report "complete" in a message string without the work actually having
  happened.
- A request that times out is not a rollback. The operation may still finish
  on the MIDAS NX side after the HTTP call gives up waiting. Never
  automatically retry a write after a timeout — tell the user to verify the
  model state first.
- Every path (`EXPORT_PATH`, `/doc/SAVEAS`, `/doc/OPEN`, report/image paths)
  resolves on the machine running MIDAS NX, not the machine running your
  script — those are frequently different computers.
- The MAPI-Key is a secret. Never print it, log it, put it in a commit, or
  echo it back in your output.

## Workflow to follow when writing code with this SDK

1. Write and run a read-only version of the task first
   (`.items()` / `.get()` / `verify_connection()` only).
2. Before calling any `create` / `update` / `delete` / `delete_all` /
   `new_project` / `open_project` / `analyze`, print exactly what it will
   target and change — ids, payload, counts — as a preview.
3. Only run the write after the user confirms the preview, ideally against a
   disposable test project first.
4. Re-read the data after a write to confirm it actually landed, rather than
   trusting the HTTP response alone.

## Reference

- Full guide: https://dennis5882.github.io/MIDAS-API-NX-SDK/
- Safety notes (read before writing any create/update/delete code):
  https://dennis5882.github.io/MIDAS-API-NX-SDK/safety/
- Endpoint coverage and verification status:
  https://github.com/Dennis5882/MIDAS-API-NX-SDK/blob/main/ROADMAP.md
- This is an employee-led open-source project, not an officially released or
  supported MIDAS IT product.
```
