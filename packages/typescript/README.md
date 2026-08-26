# midas-nx

Typed JavaScript/TypeScript SDK for the MIDAS NX Open API, covering MIDAS
Civil NX and MIDAS Gen NX. The npm and Python packages are maintained from the
same reviewed endpoint inventory in the
[MIDAS-API-NX-SDK repository](https://github.com/Dennis5882/MIDAS-API-NX-SDK).

## Setup

Node.js 18 or newer is required:

```bash
npm install midas-nx
```

```ts
import { MidasClient } from "midas-nx";

const client = new MidasClient({
  mapiKey: process.env.MIDAS_MAPI_KEY,
  product: "gen", // "gen" or "civil"
});

console.log(await client.verifyConnection());
```

`MIDAS_MAPI_KEY` and `MIDAS_BASE_URL` may also be supplied as environment
variables in Node.js. Browser applications should pass credentials explicitly
and must not expose a long-lived API key in public client code.

## API

DB endpoints are grouped by the same domain structure as the official manual.
Payloads and supported products/methods are typed and attached to each
resource.

```ts
import { MidasClient, resources } from "midas-nx";

const client = new MidasClient({ mapiKey: "...", product: "civil" });
const node = resources.db.nodeElement.node;

await node.create({ 1: { X: 0, Y: 0, Z: 0 } }, client);
const nodes = await node.items(client);
await node.delete([1], client); // one DELETE request per ID
```

Whole-table deletion requires an explicit confirmation:

```ts
await resources.db.nodeElement.node.deleteAll({ confirm: true, client });
```

Document, operation, and view endpoints use camelCase names while preserving
the official request field names inside their typed argument objects.

```ts
import { doc, operations } from "midas-nx";

await doc.save({ client });
await operations.view.setAngle({ HORIZONTAL: 30, VERTICAL: 15 }, { client });
```

Result tables use an options object. The SDK translates its camelCase option
names into MIDAS's uppercase wire keys and does not rely on the unstable
top-level response key.

```ts
import { tables, unwrapTable } from "midas-nx";

const raw = await tables.result1.getReactionTable({
  loadCaseNames: ["DL(ST)"],
  nodeElements: { keys: [1, 2] },
  client,
});
const table = unwrapTable(raw);
```

Advanced users can call any command directly with `client.request(...)` or
the default-client helper `midasApi(...)`.

## Project status

This is an employee-led open-source project built from the official MIDAS API
manual and hands-on verification against real MIDAS NX sessions. It is not an
officially released or supported MIDAS IT product. Report SDK issues through
the repository's GitHub Issues; use MIDAS IT's official support channels for
product, licensing, and Open API service questions.

Licensed under the MIT License.
