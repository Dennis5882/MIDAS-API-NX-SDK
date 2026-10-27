import { describe, expect, it, vi } from "vitest";

import { MidasClient, defineDbResource, resources } from "../src";

/**
 * Contract-driven payload normalization.
 *
 * `/db/NMAS` is why this exists. Omitting `rmX`/`rmY`/`rmZ` hung the call and
 * killed the NX session across 15+ reproductions on both Gen NX and Civil NX,
 * while sending them as `0.0` - their own documented default - did not. Python
 * gained that workaround on 2026-07-29; this package shipped on 2026-08-26
 * without it, because the workaround was behaviour inside a method and the
 * generator only carried metadata and docstrings across. The rule now comes
 * from `contracts/endpoints/db-nmas.yaml` and reaches both SDKs the same way.
 */

const ok = () =>
  vi
    .fn<typeof globalThis.fetch>()
    .mockImplementation(async () => new Response(JSON.stringify({ message: "ok" }), { status: 200 }));

function sentBody(fetch: ReturnType<typeof ok>, call = 0): Record<string, unknown> {
  return JSON.parse(String(fetch.mock.calls[call]?.[1]?.body));
}

describe("nodalMass payload normalization", () => {
  it("fills rmX/rmY/rmZ on create when the caller omits them", async () => {
    const fetch = ok();
    const client = new MidasClient({ fetch });

    await resources.db.staticLoads.nodalMass.create({ 1: { mX: 1, mY: 1, mZ: 1 } }, client);

    expect(sentBody(fetch)).toEqual({
      Assign: { "1": { mX: 1, mY: 1, mZ: 1, rmX: 0, rmY: 0, rmZ: 0 } },
    });
  });

  it("fills rmX/rmY/rmZ on update too", async () => {
    const fetch = ok();
    const client = new MidasClient({ fetch });

    await resources.db.staticLoads.nodalMass.update({ 7: { mX: 2 } }, client);

    expect(sentBody(fetch)).toEqual({
      Assign: { "7": { mX: 2, rmX: 0, rmY: 0, rmZ: 0 } },
    });
  });

  it("never overwrites a rotational mass the caller supplied", async () => {
    const fetch = ok();
    const client = new MidasClient({ fetch });

    await resources.db.staticLoads.nodalMass.create({ 1: { mX: 1, rmZ: 500 } }, client);

    const assign = (sentBody(fetch).Assign as Record<string, Record<string, number>>)["1"];
    expect(assign).toEqual({ mX: 1, rmX: 0, rmY: 0, rmZ: 500 });
  });

  it("normalizes every record in one call, not only the first", async () => {
    const fetch = ok();
    const client = new MidasClient({ fetch });

    await resources.db.staticLoads.nodalMass.create({ 1: { mX: 1 }, 2: { mX: 2 } }, client);

    const assign = sentBody(fetch).Assign as Record<string, Record<string, number>>;
    for (const record of Object.values(assign)) {
      expect(record).toMatchObject({ rmX: 0, rmY: 0, rmZ: 0 });
    }
  });

  it("declares the defaults in its published metadata", () => {
    expect(resources.db.staticLoads.nodalMass.metadata.payloadDefaults).toEqual({
      rmX: 0,
      rmY: 0,
      rmZ: 0,
    });
  });

  it("leaves payloads untouched for resources with no contract rule", async () => {
    const fetch = ok();
    const client = new MidasClient({ fetch });

    await resources.db.nodeElement.node.create({ 1: { X: 0, Y: 0, Z: 0 } }, client);

    expect(sentBody(fetch)).toEqual({ Assign: { "1": { X: 0, Y: 0, Z: 0 } } });
    expect(resources.db.nodeElement.node.metadata.payloadDefaults).toBeUndefined();
  });

  it("applies defaults without mutating the caller's object", async () => {
    const fetch = ok();
    const client = new MidasClient({ fetch });
    const items = { 1: { mX: 1 } };

    await resources.db.staticLoads.nodalMass.create(items, client);

    expect(items).toEqual({ 1: { mX: 1 } });
  });

  it("does nothing when a resource declares no defaults", async () => {
    const fetch = ok();
    const client = new MidasClient({ fetch });
    const resource = defineDbResource({
      className: "Scratch",
      endpoint: "/db/SCRATCH",
      name: "Scratch",
      products: ["gen", "civil"] as const,
      methods: ["POST"] as const,
      manualChapter: "99_Synthetic.md",
    });

    await resource.create({ 1: { A: 1 } }, client);

    expect(sentBody(fetch)).toEqual({ Assign: { "1": { A: 1 } } });
  });
});

/**
 * `/db/CNLD` and `/db/BMLD`: defaults inside every `ITEMS` entry.
 *
 * A PUT that adds or rewrites an entry on a record that already has entries
 * stores each field the entry leaves out with the value of the record's first
 * entry, not its documented default (Gen NX, 2026-10-27): an entry sent with
 * `FY` only took the first entry's `FZ` of -20, and a plain beam load added
 * beside an eccentric one was stored eccentric. No error is returned.
 */
describe("ITEMS entry normalization", () => {
  it("fills every force and moment component of every nodalLoad entry", async () => {
    const fetch = ok();
    const client = new MidasClient({ fetch });

    await resources.db.staticLoads.nodalLoad.update(
      { 4: { ITEMS: [{ ID: 2, LCNAME: "DL", FY: 1.5 }, { ID: 3, LCNAME: "L", MZ: 2 }] } },
      client,
    );

    expect(sentBody(fetch)).toEqual({
      Assign: {
        "4": {
          ITEMS: [
            { ID: 2, LCNAME: "DL", GROUP_NAME: "", FX: 0, FY: 1.5, FZ: 0, MX: 0, MY: 0, MZ: 0 },
            { ID: 3, LCNAME: "L", GROUP_NAME: "", FX: 0, FY: 0, FZ: 0, MX: 0, MY: 0, MZ: 2 },
          ],
        },
      },
    });
  });

  it("sends beamLoad's option flags as false unless the caller set them", async () => {
    const fetch = ok();
    const client = new MidasClient({ fetch });

    await resources.db.staticLoads.beamLoad.create(
      {
        1: {
          ITEMS: [
            { ID: 2, LCNAME: "DL", CMD: "BEAM", TYPE: "UNILOAD", DIRECTION: "GZ", USE_PROJECTION: true, ECCEN_DIR: "GZ", D: [0, 1, 0, 0], P: [-2, -2, 0, 0] },
          ],
        },
      },
      client,
    );

    const entry = (sentBody(fetch).Assign as Record<string, { ITEMS: Record<string, unknown>[] }>)["1"]!.ITEMS[0]!;
    expect([entry.USE_PROJECTION, entry.USE_ECCEN, entry.USE_ADDITIONAL]).toEqual([true, false, false]);
    expect([entry.GROUP_NAME, entry.ECCEN_TYPE, entry.USE_J_END, entry.J_END]).toEqual(["", 0, false, 0]);
    expect(entry.P).toEqual([-2, -2, 0, 0]);
  });

  it("publishes the defaults as paths into ITEMS", () => {
    expect(resources.db.staticLoads.nodalLoad.metadata.payloadDefaults).toEqual({
      "ITEMS[].GROUP_NAME": "",
      "ITEMS[].FX": 0,
      "ITEMS[].FY": 0,
      "ITEMS[].FZ": 0,
      "ITEMS[].MX": 0,
      "ITEMS[].MY": 0,
      "ITEMS[].MZ": 0,
    });
  });

  it("does not mutate the caller's entries, and leaves a record without ITEMS alone", async () => {
    const fetch = ok();
    const client = new MidasClient({ fetch });
    const items = { 4: { ITEMS: [{ ID: 1, LCNAME: "DL", FZ: -1 }] }, 5: {} };

    await resources.db.staticLoads.nodalLoad.create(items as never, client);

    expect(items).toEqual({ 4: { ITEMS: [{ ID: 1, LCNAME: "DL", FZ: -1 }] }, 5: {} });
    expect((sentBody(fetch).Assign as Record<string, unknown>)["5"]).toEqual({});
  });
});
