import { describe, expect, it } from "vitest";
import { plan, type PlanOperation } from "../src";

const op = (endpoint: string, method: PlanOperation["method"], label: string): PlanOperation => ({
  endpoint,
  method,
  label,
});

describe("plan.order", () => {
  it("sends writes after what they name and keeps the caller's order otherwise", () => {
    const ops = [
      op("/db/BMLD", "POST", "load"),
      op("/db/ELEM", "POST", "elem"),
      op("/db/UNIT", "PUT", "unit"),
      op("/db/STLD", "POST", "case"),
      op("/db/NODE", "POST", "node"),
      op("/db/MATL", "POST", "matl"),
    ];
    expect(plan.order(ops).map((o) => o.label)).toEqual(["unit", "case", "node", "matl", "elem", "load"]);
  });

  it("sends deletes first, dependents before what they name", () => {
    const ops = [
      op("/db/NODE", "POST", "node+"),
      op("/db/NODE", "DELETE", "node-"),
      op("/db/ELEM", "DELETE", "elem-"),
      op("/db/BMLD", "DELETE", "load-"),
    ];
    expect(plan.order(ops).map((o) => o.label)).toEqual(["load-", "elem-", "node-", "node+"]);
  });

  it("ranks by the deepest chain", () => {
    expect(plan.rank("/db/NODE")).toBe(0);
    expect(plan.rank("/db/ELEM")).toBe(1);
    expect(plan.rank("/db/BMLD")).toBe(2);
    expect(plan.rank("/db/NOT-A-TABLE")).toBe(0);
  });

  it("refuses a GET", () => {
    expect(() => plan.order([{ endpoint: "/db/NODE", method: "GET" as never }])).toThrow();
  });
});

// One scenario, twinned in tests/test_plan.py.
const MODEL = { "/db/NODE": [1, 2], "/db/MATL": [1], "/db/SECT": [1], "/db/THIK": [], "/db/STLD": ["DL"], "/db/LDGR": [] };
const w = (endpoint: string, records: Record<string, unknown>): PlanOperation => ({
  endpoint,
  method: "POST",
  records: records as NonNullable<PlanOperation["records"]>,
});
const del = (endpoint: string, ids: number[]): PlanOperation => ({ endpoint, method: "DELETE", ids });

describe("plan.references", () => {
  it("lists the contracts' field references, by table", () => {
    expect(plan.references().length).toBe(16);
    expect(plan.references("/db/ELEM").map((r) => r.field).sort()).toEqual(["MATL", "NODE", "SECT"]);
    expect(plan.references("/db/CNLD").find((r) => r.field === "ITEMS[].LCNAME")?.onTargetDelete).toBe("deleted");
  });
});

describe("plan.validate", () => {
  it("reports what the product will do with a missing reference", () => {
    const ops = [
      w("/db/ELEM", { "1": { TYPE: "BEAM", MATL: 9, SECT: 1, NODE: [1, 2, 0, 0] } }),
      w("/db/ELEM", { "2": { TYPE: "BEAM", MATL: 1, SECT: 1, NODE: [1, 3] } }),
      w("/db/CNLD", { "1": { ITEMS: [{ ID: 1, LCNAME: "LL", FZ: -1 }] } }),
      w("/db/STLD", { "2": { NAME: "LL", TYPE: "L" } }),
      w("/db/GRUP", { "1": { NAME: "G", N_LIST: [1, 3] } }),
    ];
    const found = plan.validate(ops, MODEL);
    expect(found.map((f) => [f.index, f.reference.field, f.value, f.outcome])).toEqual([
      [0, "MATL", 9, "stored"],
      [1, "NODE", 3, "refused"],
      [2, "ITEMS[].LCNAME", "LL", "refused"],
      [4, "N_LIST", 3, "dropped"],
    ]);
    expect(found[2]?.message).toContain("operation 3 writes it later");
    expect(plan.validate(plan.order(ops), MODEL).map((f) => f.reference.field)).toEqual(["MATL", "NODE", "N_LIST"]);
  });

  it("reports nothing for a table it was not told about", () => {
    const ops = [w("/db/ELEM", { "1": { MATL: 9, SECT: 9, NODE: [7, 8] } })];
    expect(plan.validate(ops)).toEqual([]);
    expect(plan.validate(ops, { "/db/NODE": [] }).map((f) => f.reference.field)).toEqual(["NODE", "NODE"]);
  });

  it("reports what a delete does to records written before it", () => {
    const ops = [
      w("/db/ELEM", { "1": { MATL: 1, SECT: 1, NODE: [1, 2] } }),
      w("/db/CNLD", { "1": { ITEMS: [{ ID: 1, LCNAME: "DL" }] } }),
      del("/db/NODE", [2]),
      del("/db/MATL", [1]),
      del("/db/STLD", [1]),
    ];
    expect(plan.validate(ops, MODEL).map((f) => [f.index, f.kind, f.reference.field, f.outcome])).toEqual([
      [2, "deleted", "NODE", "deleted"],
      [3, "deleted", "MATL", "orphaned"],
    ]);
    const withCase = [w("/db/STLD", { "1": { NAME: "DL" } }), ...ops];
    const last = plan.validate(withCase, MODEL).at(-1);
    expect([last?.kind, last?.reference.field, last?.outcome]).toEqual(["deleted", "ITEMS[].LCNAME", "deleted"]);
    withCase.push(w("/db/ELEM", { "2": { MATL: 1, SECT: 1, NODE: [1, 2] } }));
    expect(
      plan.validate(withCase, MODEL).filter((f) => f.kind === "missing").map((f) => [f.index, f.reference.field, f.value]),
    ).toEqual([
      [6, "MATL", 1],
      [6, "NODE", 2],
    ]);
  });

  it("refuses a GET", () => {
    expect(() => plan.validate([{ endpoint: "/db/NODE", method: "GET" as never }])).toThrow();
  });
});

describe("plan.keyPolicy", () => {
  it("says where a POST key lands, per product", () => {
    expect(plan.keyPolicy("/db/STLD", "gen")).toBe("assigned");
    expect(plan.keyPolicy("/db/NODE", "civil")).toBe("honoured");
    expect([plan.keyPolicy("/db/GSTP", "gen"), plan.keyPolicy("/db/GSTP", "civil")]).toEqual(["assigned", "honoured"]);
    expect(plan.keyPolicy("/db/NOT-A-TABLE", "gen")).toBeUndefined();
  });
});
