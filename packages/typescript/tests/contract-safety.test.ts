import { describe, expect, it, vi } from "vitest";

import {
  DestructiveOperationError,
  MidasClient,
  MidasServerError,
  defineDbResource,
  resources,
  unwrapTable,
} from "../src";

const metadata = {
  className: "ContractSafetyProbe",
  endpoint: "/db/CONTRACT-SAFETY-PROBE",
  name: "Contract safety probe",
  products: ["gen", "civil"] as const,
  methods: ["POST", "GET", "PUT", "DELETE"] as const,
  manualChapter: "not-a-manual-source.ts",
};

function response(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

type UnwrapResponseCase = "table_name" | "result_table" | "empty_with_table" | "no_table";

function unwrapResponseCases(): UnwrapResponseCase[] {
  const processLike = globalThis as typeof globalThis & {
    process?: { env?: Record<string, string | undefined> };
  };
  const raw = processLike.process?.env?.MIDAS_UNWRAP_TABLE_RESPONSE_CASES;
  if (!raw) return ["table_name", "result_table", "empty_with_table", "no_table"];
  return JSON.parse(raw) as UnwrapResponseCase[];
}

function unwrapFixture(caseName: UnwrapResponseCase) {
  const table = { HEAD: ["Node", "FX"], DATA: [["1", "-10"]] };
  switch (caseName) {
    case "table_name":
      return { response: { "Requested table": table }, expected: table };
    case "result_table":
      return { response: { "Result Table": table }, expected: table };
    case "empty_with_table":
      return { response: { empty: table }, expected: table };
    case "no_table":
      return { response: { message: "" }, expected: {} };
  }
}

describe("contract safety probes", () => {
  it("normalize_defaults: sends required explicit defaults through the npm resource", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(response({ message: "ok" }));
    const client = new MidasClient({ fetch });

    await resources.db.staticLoads.nodalMass.create({ 1: { mX: 1 } }, client);

    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toEqual({
      Assign: { "1": { mX: 1, rmX: 0, rmY: 0, rmZ: 0 } },
    });
  });

  it("per_id_request: sends one DELETE URL per id and stops after the first failure", async () => {
    const resource = defineDbResource(metadata);
    const successfulFetch = vi
      .fn<typeof globalThis.fetch>()
      .mockImplementation(async () => response({ message: "ok" }));
    const successfulClient = new MidasClient({ fetch: successfulFetch });

    await resource.delete([7, 9], successfulClient);

    expect(successfulFetch.mock.calls.map(([url]) => url)).toEqual([
      "https://moa-engineers.midasit.com:443/gen/db/CONTRACT-SAFETY-PROBE/7",
      "https://moa-engineers.midasit.com:443/gen/db/CONTRACT-SAFETY-PROBE/9",
    ]);

    const failingFetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(response({ message: "failed" }, 500))
      .mockResolvedValue(response({ message: "ok" }));
    const failingClient = new MidasClient({ fetch: failingFetch });

    await expect(resource.delete([7, 9], failingClient)).rejects.toBeInstanceOf(MidasServerError);
    expect(failingFetch).toHaveBeenCalledTimes(1);
    expect(failingFetch.mock.calls[0]?.[0]).toBe(
      "https://moa-engineers.midasit.com:443/gen/db/CONTRACT-SAFETY-PROBE/7",
    );
  });

  it("require_confirmation: rejects a whole-table DELETE before sending it", async () => {
    const resource = defineDbResource(metadata);
    const fetch = vi.fn<typeof globalThis.fetch>();
    const client = new MidasClient({ fetch });

    await expect(resource.deleteAll({ client })).rejects.toBeInstanceOf(DestructiveOperationError);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("unwrap_table_by_shape: decodes every response case declared by the contract", () => {
    const cases = unwrapResponseCases();
    expect(cases).toEqual(
      expect.arrayContaining(["table_name", "result_table", "empty_with_table", "no_table"]),
    );

    for (const caseName of cases) {
      const { response, expected } = unwrapFixture(caseName);
      expect(unwrapTable(response)).toEqual(expected);
    }
  });
});
