import { describe, expect, it, vi } from "vitest";

import { MidasClient, getTable, tables, unwrapTable } from "../src";

const LIVE_TABLE = {
  HEAD: ["Node", "FX", "FY"],
  DATA: [["1", "0", "-10"]],
};

describe("unwrapTable", () => {
  it("finds a table returned under the caller's TABLE_NAME", () => {
    expect(unwrapTable({ "Reaction results": LIVE_TABLE })).toEqual(LIVE_TABLE);
  });

  it('finds a table returned under the live "Result Table" key', () => {
    expect(unwrapTable({ "Result Table": LIVE_TABLE })).toEqual(LIVE_TABLE);
  });

  it('treats the live "empty" key as a table key, not as no data', () => {
    expect(unwrapTable({ empty: LIVE_TABLE })).toEqual(LIVE_TABLE);
  });

  it("returns an empty object when no value has a table shape", () => {
    expect(unwrapTable({ message: "", metadata: { requestId: "abc" } })).toEqual({});
    expect(unwrapTable({})).toEqual({});
  });

  it("accepts a response that is already a table", () => {
    expect(unwrapTable(LIVE_TABLE)).toEqual(LIVE_TABLE);
  });

  it("composes with getTable when the server uses the empty default key", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      new Response(JSON.stringify({ empty: LIVE_TABLE }), { status: 200 }),
    );
    const client = new MidasClient({ fetch });

    const response = await getTable("REACTION", { client });

    expect(unwrapTable(response)).toEqual(LIVE_TABLE);
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toEqual({
      Argument: { TABLE_NAME: "", TABLE_TYPE: "REACTION" },
    });
  });
});

describe("EIGENVALUEMODE components", () => {
  const sent = async (call: (client: MidasClient) => Promise<unknown>) => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      new Response(JSON.stringify({}), { status: 200 }),
    );
    await call(new MidasClient({ fetch }));
    return JSON.parse(String(fetch.mock.calls[0]?.[1]?.body)).Argument;
  };
  // Gen NX answers EIGENVALUEMODE with Unknown Error without COMPONENTS
  // (2026-10-20), so the manual example's list is sent when none is named.
  const DEFAULT = ["Node", "Mode", "UX", "UY", "UZ", "RX", "RY", "RZ"];

  it("sends the manual example's list when the caller names none", async () => {
    expect(
      (await sent((client) => tables.result1.getVibrationModeShapeTable({ client }))).COMPONENTS,
    ).toEqual(DEFAULT);
    expect((await sent((client) => getTable("EIGENVALUEMODE", { client }))).COMPONENTS).toEqual(
      DEFAULT,
    );
  });

  it("keeps the caller's components", async () => {
    const argument = await sent((client) =>
      tables.result1.getVibrationModeShapeTable({ client, components: ["Node", "Mode", "UZ"] }),
    );
    expect(argument.COMPONENTS).toEqual(["Node", "Mode", "UZ"]);
  });

  it("adds nothing for PARTICIPATIONVECTORMODE, which answers without it", async () => {
    const argument = await sent((client) =>
      tables.result1.getVibrationModeShapeTable({ client, tableType: "PARTICIPATIONVECTORMODE" }),
    );
    expect(argument.TABLE_TYPE).toBe("PARTICIPATIONVECTORMODE");
    expect(argument).not.toHaveProperty("COMPONENTS");
  });
});
