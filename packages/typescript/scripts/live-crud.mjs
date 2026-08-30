#!/usr/bin/env node
/**
 * Live write verification for the npm package's public DB-resource surface.
 *
 * This deliberately lives beside the npm package and imports its built
 * `dist/index.js` entrypoint. It therefore exercises the API a package user
 * installs, rather than raw HTTP or Python implementation details. Case
 * payloads come only from schema/live-cases.json, emitted by Python's
 * scripts/live_crud_check.py; never copy a live payload into this file.
 *
 * Usage:
 *   MIDAS_MAPI_KEY=... npm run live:crud -- -- --product gen --endpoints /db/NODE,/db/NMAS
 *
 * This script intentionally requires an explicit endpoint selection. A broad
 * accidental run is not a useful substitute for reviewing fixtures in small
 * batches against an empty scratch document.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { MidasClient, post, resources } from "../dist/index.js";

const fixturePath = fileURLToPath(new URL("../../../schema/live-cases.json", import.meta.url));
const fixture = JSON.parse(readFileSync(fixturePath, "utf8"));

function usage(message) {
  if (message) console.error(message);
  console.error("Usage: npm run live:crud -- -- --product gen|civil --endpoints /db/NODE,/db/NMAS [--table-type MASS_SUMMARY_X] [--mapi-key key] [--timeout ms]");
  process.exit(2);
}

function parseArgs(argv) {
  const args = { timeout: 30_000 };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (flag === "--product" || flag === "--endpoints" || flag === "--table-type" || flag === "--mapi-key" || flag === "--timeout") {
      if (!value || value.startsWith("--")) usage(`${flag} needs a value.`);
      args[flag.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = value;
      index += 1;
    } else if (flag === "--help" || flag === "-h") {
      usage();
    } else {
      usage(`Unknown option: ${flag}`);
    }
  }
  if (args.product !== "gen" && args.product !== "civil") usage("--product must be gen or civil.");
  if (!args.endpoints) usage("--endpoints is required; select a reviewed small batch.");
  args.timeout = Number(args.timeout);
  if (!Number.isFinite(args.timeout) || args.timeout <= 0) usage("--timeout must be a positive number of milliseconds.");
  return args;
}

function isResource(value) {
  return typeof value === "object" && value !== null &&
    typeof value.create === "function" && typeof value.items === "function" &&
    typeof value.delete === "function" && typeof value.metadata?.endpoint === "string";
}

function findResource(value, endpoint, visited = new Set()) {
  if (typeof value !== "object" || value === null || visited.has(value)) return undefined;
  visited.add(value);
  if (isResource(value) && value.metadata.endpoint === endpoint) return value;
  for (const child of Object.values(value)) {
    const found = findResource(child, endpoint, visited);
    if (found) return found;
  }
  return undefined;
}

function caseFor(endpoint) {
  return fixture.cases.find((candidate) => candidate.endpoint === endpoint);
}

function resourceFor(endpoint) {
  const resource = findResource(resources.db, endpoint);
  if (!resource) throw new Error(`${endpoint}: no public resources.db entry exists in the built npm package.`);
  return resource;
}

function errorText(error) {
  return error instanceof Error ? error.message : String(error);
}

function requireStored(items, id, endpoint, step) {
  const stored = items[id];
  if (!stored) throw new Error(`${endpoint}: id ${id} missing after ${step}.`);
  return stored;
}

function newlyCreatedIds(before, after) {
  return Object.keys(after)
    .map(Number)
    .filter((id) => !Object.hasOwn(before, id));
}

function containsExpectedValue(value, expected) {
  if (Object.is(value, expected)) return true;
  if (typeof value !== "object" || value === null) return false;
  return Object.values(value).some((child) => containsExpectedValue(child, expected));
}

function requireExpectedValue(value, expected, endpoint, step) {
  if (expected === null || expected === undefined) return;
  if (!containsExpectedValue(value, expected)) {
  throw new Error(`${endpoint}: expected live value ${JSON.stringify(expected)} after ${step}.`);
  }
}

function assertPayloadDefaults(resource, stored, endpoint, step) {
  for (const [key, expected] of Object.entries(resource.metadata.payloadDefaults ?? {})) {
    if (!Object.is(stored[key], expected)) {
      throw new Error(`${endpoint}: payloadDefaults.${key} was not read back as ${JSON.stringify(expected)} after ${step}.`);
    }
  }
}

async function deleteAndVerify(resource, id, client, endpoint) {
  await resource.delete([id], client);
  if (Object.hasOwn(await resource.items(client), id)) {
    throw new Error(`${endpoint}: id ${id} remains after individual DELETE.`);
  }
}

async function runCase(liveCase, client) {
  const resource = resourceFor(liveCase.endpoint);
  if (!liveCase.methods.includes("DELETE") || !resource.metadata.methods.includes("DELETE")) {
    throw new Error(`${liveCase.endpoint}: this harness refuses a no-DELETE case so the scratch document stays empty.`);
  }
  const setup = [];
  const targetCreatedIds = new Set();
  let result;
  try {
    for (const prerequisite of liveCase.setup) {
      const source = caseFor(prerequisite.endpoint);
      if (!source) throw new Error(`${liveCase.endpoint}: fixture setup ${prerequisite.endpoint} has no source case.`);
      const sourceResource = resourceFor(prerequisite.endpoint);
      if (!sourceResource.metadata.methods.includes("DELETE")) {
        throw new Error(`${liveCase.endpoint}: setup ${prerequisite.endpoint} cannot be individually cleaned up.`);
      }
      const before = await sourceResource.items(client);
      if (Object.hasOwn(before, prerequisite.id)) {
        throw new Error(`${liveCase.endpoint}: setup ${prerequisite.endpoint}/${prerequisite.id} already exists; refusing to overwrite a scratch record.`);
      }
      await sourceResource.create({ [prerequisite.id]: source.createPayload }, client);
      const after = await sourceResource.items(client);
      const createdIds = newlyCreatedIds(before, after);
      setup.push({ resource: sourceResource, ids: createdIds, endpoint: prerequisite.endpoint });
      requireStored(after, prerequisite.id, prerequisite.endpoint, "setup POST");
    }

    const before = await resource.items(client);
    if (Object.hasOwn(before, liveCase.id)) {
      throw new Error(`${liveCase.endpoint}/${liveCase.id} already exists; refusing to overwrite a scratch record.`);
    }
    await resource.create({ [liveCase.id]: liveCase.createPayload }, client);
    const afterCreate = await resource.items(client);
    for (const id of newlyCreatedIds(before, afterCreate)) targetCreatedIds.add(id);
    const created = requireStored(afterCreate, liveCase.id, liveCase.endpoint, "POST");
    requireExpectedValue(created, liveCase.expected.created, liveCase.endpoint, "POST");
    assertPayloadDefaults(resource, created, liveCase.endpoint, "POST");

    await resource.update({ [liveCase.id]: liveCase.updatePayload }, client);
    const updated = requireStored(await resource.items(client), liveCase.id, liveCase.endpoint, "PUT");
    requireExpectedValue(updated, liveCase.expected.updated, liveCase.endpoint, "PUT");
    assertPayloadDefaults(resource, updated, liveCase.endpoint, "PUT");

    await deleteAndVerify(resource, liveCase.id, client, liveCase.endpoint);
    targetCreatedIds.delete(liveCase.id);
    result = { endpoint: liveCase.endpoint, ok: true, confirmed: liveCase.confirmed };
  } catch (error) {
    result = { endpoint: liveCase.endpoint, ok: false, confirmed: liveCase.confirmed, error: errorText(error) };
  } finally {
    const cleanupErrors = [];
    for (const id of targetCreatedIds) {
      try {
        await deleteAndVerify(resource, id, client, liveCase.endpoint);
      } catch (error) {
        cleanupErrors.push(`${liveCase.endpoint}/${id}: ${errorText(error)}`);
      }
    }
    for (const prerequisite of setup.reverse()) {
      for (const id of prerequisite.ids) {
        try {
          await deleteAndVerify(prerequisite.resource, id, client, prerequisite.endpoint);
        } catch (error) {
          cleanupErrors.push(`${prerequisite.endpoint}/${id}: ${errorText(error)}`);
        }
      }
    }
    if (cleanupErrors.length) {
      result = {
        ...result,
        ok: false,
        error: [result.error, `Cleanup failed: ${cleanupErrors.join("; ")}`].filter(Boolean).join("; "),
      };
    }
  }
  return result;
}

/**
 * Exercise the public /post/TABLE adapter with real data.  The records come
 * from the shared fixture, including the Nodal Mass omitted-default case;
 * do not add a second hand-written payload here.
 */
async function runPopulatedTable(tableType, client) {
  const nodeCase = caseFor("/db/NODE");
  const massCase = caseFor("/db/NMAS");
  if (!nodeCase || !massCase) throw new Error("The shared fixture must contain /db/NODE and /db/NMAS cases.");

  const node = resourceFor(nodeCase.endpoint);
  const mass = resourceFor(massCase.endpoint);
  const id = 900_301;
  let nodeCreated = false;
  let massCreated = false;
  let result;
  try {
    await node.create({ [id]: nodeCase.createPayload }, client);
    nodeCreated = true;
    requireStored(await node.items(client), id, nodeCase.endpoint, "table seed POST");

    await mass.create({ [id]: massCase.createPayload }, client);
    massCreated = true;
    const storedMass = requireStored(await mass.items(client), id, massCase.endpoint, "table seed POST");
    assertPayloadDefaults(mass, storedMass, massCase.endpoint, "table seed POST");

    const raw = await post.getTable(tableType, {
      client,
      nodeElements: { keys: [id] },
    });
    const table = post.unwrapTable(raw);
    if (!Array.isArray(table.HEAD) || !Array.isArray(table.DATA) || table.DATA.length === 0) {
      throw new Error(`/post/TABLE ${tableType}: expected populated HEAD/DATA table, received ${JSON.stringify(raw)}.`);
    }
    result = {
      endpoint: `/post/TABLE ${tableType}`,
      ok: true,
      // This is the documented table whose populated shape was observed on
      // both products on 2026-08-31. Other caller-selected table types still
      // need fixture/ledger triage before a failure can be called regression.
      confirmed: tableType === "MASS_SUMMARY_X",
      keys: Object.keys(raw),
      rows: table.DATA.length,
    };
  } catch (error) {
    result = {
      endpoint: `/post/TABLE ${tableType}`,
      ok: false,
      confirmed: tableType === "MASS_SUMMARY_X",
      error: errorText(error),
    };
  } finally {
    const cleanupErrors = [];
    if (massCreated) {
      try {
        await deleteAndVerify(mass, id, client, massCase.endpoint);
      } catch (error) {
        cleanupErrors.push(`${massCase.endpoint}: ${errorText(error)}`);
      }
    }
    if (nodeCreated) {
      try {
        await deleteAndVerify(node, id, client, nodeCase.endpoint);
      } catch (error) {
        cleanupErrors.push(`${nodeCase.endpoint}: ${errorText(error)}`);
      }
    }
    if (cleanupErrors.length) {
      result = {
        ...result,
        ok: false,
        error: [result.error, `Cleanup failed: ${cleanupErrors.join("; ")}`].filter(Boolean).join("; "),
      };
    }
  }
  return result;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const selected = args.endpoints.split(",").map((endpoint) => endpoint.trim()).filter(Boolean);
  const cases = selected.map((endpoint) => caseFor(endpoint) ?? usage(`${endpoint}: no case in ${fixturePath}.`));
  const client = new MidasClient({ mapiKey: args.mapiKey, product: args.product, timeout: args.timeout });
  const health = await client.verifyConnection();
  if (health.status !== "connected") throw new Error(`Server reachable but not connected: ${JSON.stringify(health)}`);

  const results = [];
  for (const liveCase of cases) {
    if (!liveCase.products.includes(args.product)) {
      console.log(`SKIP ${liveCase.endpoint} does not support ${args.product}.`);
      continue;
    }
    const result = await runCase(liveCase, client);
    results.push(result);
    console.log(`${result.ok ? "PASS" : result.confirmed ? "REGRESS" : "FAIL"} ${result.endpoint}${result.error ? ` ${result.error}` : ""}`);
  }
  if (args.tableType) {
    const result = await runPopulatedTable(args.tableType, client);
    results.push(result);
    console.log(`${result.ok ? "PASS" : result.confirmed ? "REGRESS" : "FAIL"} ${result.endpoint}${result.ok ? ` keys=${result.keys.join(",")} rows=${result.rows}` : ` ${result.error}`}`);
  }
  const failed = results.filter((result) => !result.ok);
  if (!failed.length) return 0;
  return failed.some((result) => result.confirmed) ? 1 : 3;
}

main().then((code) => {
  process.exitCode = code;
}).catch((error) => {
  console.error(errorText(error));
  process.exitCode = 2;
});
