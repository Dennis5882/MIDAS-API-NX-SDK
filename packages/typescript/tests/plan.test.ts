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

  it("reports a delete against records already in the model", () => {
    const model = {
      ...MODEL,
      "/db/ELEM": { "7": { TYPE: "BEAM", MATL: 1, SECT: 1, NODE: [1, 2] } },
      "/db/STLD": { "1": { NAME: "DL" } },
      "/db/CNLD": { "2": { ITEMS: [{ ID: 1, LCNAME: "DL" }] } },
    };
    const ops = [del("/db/SECT", [1]), del("/db/STLD", [1])];
    const found = plan.validate(ops, model);
    expect(found.map((f) => [f.index, f.recordKey, f.reference.field, f.outcome])).toEqual([
      [0, "7", "SECT", "orphaned"],
      [1, "2", "ITEMS[].LCNAME", "deleted"],
    ]);
    expect(found[0]?.message).toContain("already in the model");
    ops.push(w("/db/CNLD", { "3": { ITEMS: [{ ID: 2, LCNAME: "DL" }] } }));
    const last = plan.validate(ops, model).at(-1);
    expect([last?.index, last?.kind]).toEqual([2, "missing"]);
    const rewrite: PlanOperation = { endpoint: "/db/ELEM", method: "PUT", records: { "7": { SECT: 2 } } };
    expect(plan.validate([rewrite, ops[0] as PlanOperation], { ...model, "/db/SECT": [1, 2] })).toEqual([]);
    expect(plan.validate(ops.slice(0, 1), { ...model, "/db/ELEM": [7] })).toEqual([]);
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
      del("/db/MATL", [1]),
      del("/db/NODE", [2]),
      del("/db/STLD", [1]),
    ];
    expect(plan.validate(ops, MODEL).map((f) => [f.index, f.kind, f.reference.field, f.outcome])).toEqual([
      [2, "deleted", "MATL", "orphaned"],
      [3, "deleted", "NODE", "deleted"],
    ]);
    // Deleting the node took the element with it, so a material delete after it finds nothing.
    const swapped = [ops[0], ops[1], ops[3], ops[2]] as PlanOperation[];
    expect(plan.validate(swapped, MODEL).map((f) => [f.index, f.reference.field])).toEqual([[2, "NODE"]]);
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

  it("reads an element section from the table its type names", () => {
    const ops = [
      w("/db/ELEM", {
        "1": { TYPE: "PLATE", MATL: 1, SECT: 1, NODE: [1, 2, 0, 0] },
        "2": { TYPE: "BEAM", MATL: 1, SECT: 1, NODE: [1, 2] },
        "3": { TYPE: "TRUSS", MATL: 1, SECT: 1, NODE: [1, 2] },
      }),
    ];
    const found = plan.validate(ops, MODEL);
    expect(found.map((f) => [f.recordKey, f.value, f.outcome])).toEqual([["1", 1, "stored"]]);
    expect(found[0]?.message).toContain("/db/THIK will not hold");
    const model = { ...MODEL, "/db/THIK": [1], "/db/ELEM": { "4": { TYPE: "PLATE", MATL: 1, SECT: 1, NODE: [1, 2] } } };
    const put: PlanOperation = { endpoint: "/db/ELEM", method: "PUT", records: { "4": { SECT: 7 } } };
    expect(plan.validate([put], { ...model, "/db/SECT": [1, 7] }).map((f) => [f.recordKey, f.value])).toEqual([["4", 7]]);
    expect(plan.validate([del("/db/SECT", [1])], model)).toEqual([]);
    expect(plan.validate([del("/db/THIK", [1])], model).map((f) => f.outcome)).toEqual(["orphaned"]);
  });

  it("follows a load case or group delete into each entry", () => {
    const model = {
      ...MODEL,
      "/db/STLD": { "1": { NAME: "DL" }, "2": { NAME: "LL" } },
      "/db/LDGR": { "1": { NAME: "G1" } },
      "/db/BMLD": { "1": { ITEMS: [{ ID: 1, LCNAME: "LL", GROUP_NAME: "G1" }] } },
      "/db/CNLD": { "2": { ITEMS: [{ ID: 1, LCNAME: "DL" }, { ID: 2, LCNAME: "LL", GROUP_NAME: "G1" }] } },
      "/db/LCOM-GEN": { "1": { NAME: "C1", vCOMB: [{ ANAL: "ST", LCNAME: "LL", FACTOR: 1.0 }] } },
    };
    const ops = [del("/db/STLD", [2]), del("/db/LDGR", [1])];
    expect(plan.validate(ops, model).map((f) => [f.index, f.reference.table, f.recordKey, f.outcome])).toEqual([
      [0, "/db/BMLD", "1", "deleted"],
      [0, "/db/CNLD", "2", "deleted"],
      [0, "/db/LCOM-GEN", "1", "deleted"],
    ]);
    ops.push(del("/db/STLD", [1]));
    const last = plan.validate(ops, model).at(-1);
    expect([last?.index, last?.recordKey]).toEqual([2, "2"]);
    expect(plan.validate([del("/db/LDGR", [1])], model).map((f) => [f.reference.table, f.outcome])).toEqual([
      ["/db/BMLD", "cleared"],
      ["/db/CNLD", "cleared"],
    ]);
  });

  it("follows a node or element delete into records keyed by it", () => {
    expect(plan.keyReferences().map((r) => r.table)).toEqual([
      "/db/BMLD", "/db/CNLD", "/db/CONS", "/db/FRLS", "/db/NMAS", "/db/PRES",
    ]);
    const model = {
      "/db/NODE": [1, 2, 3, 4],
      "/db/ELEM": {
        "1": { TYPE: "BEAM", NODE: [1, 2] },
        "2": { TYPE: "BEAM", NODE: [2, 3] },
        "3": { TYPE: "BEAM", NODE: [3, 4] },
      },
      "/db/CNLD": { "2": { ITEMS: [] }, "4": { ITEMS: [] } },
      "/db/NMAS": { "4": { mX: 1.0 } },
      "/db/BMLD": { "1": { ITEMS: [] }, "3": { ITEMS: [] } },
      "/db/FRLS": { "2": { ITEMS: [] } },
    };
    const found = plan.validate([del("/db/NODE", [4]), del("/db/ELEM", [2])], model);
    expect(found.map((f) => [f.index, f.reference.table, f.recordKey, f.outcome])).toEqual([
      [0, "/db/ELEM", "3", "deleted"],
      [0, "/db/CNLD", "4", "deleted"],
      [0, "/db/NMAS", "4", "deleted"],
      [0, "/db/BMLD", "3", "deleted"],
      [1, "/db/FRLS", "2", "deleted"],
    ]);
    expect(found[3]?.message).toContain('takes /db/ELEM "3" with it');
    const post = w("/db/CNLD", { "9": { ITEMS: [] } });
    expect(plan.validate([post], model).map((f) => [f.kind, f.value, f.outcome])).toEqual([["missing", "9", "refused"]]);
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

const loadModel = {
  "/db/STLD": { "1": { NAME: "DL" }, "2": { NAME: "LC" } },
  "/db/BMLD": { "2": { ITEMS: [{ ID: 1, LCNAME: "LC", P: [-5] }, { ID: 2, LCNAME: "DL", P: [-10] }] } },
};

describe("plan.itemRows and removeItems", () => {
  it("lists the three load tables", () => {
    expect(plan.itemRows().map((r) => r.table)).toEqual(["/db/BMLD", "/db/CNLD", "/db/PRES"]);
    expect(plan.itemRows("/db/NODE")).toEqual([]);
  });

  it("merges a PUT into ITEMS by id, as measured", () => {
    const ops: PlanOperation[] = [
      { endpoint: "/db/BMLD", method: "PUT", records: { "2": { ITEMS: [{ ID: 1, LCNAME: "LC", P: [-15] }] } } },
      { endpoint: "/db/STLD", method: "DELETE", ids: [1] },
    ];
    expect(plan.validate(ops, loadModel).map((f) => [f.kind, f.recordKey, f.value])).toEqual([["deleted", "2", "DL"]]);
    ops[0] = { endpoint: "/db/BMLD", method: "PUT", records: { "2": { ITEMS: [] } } };
    expect(plan.validate(ops, loadModel).map((f) => [f.kind, f.value])).toEqual([["deleted", "DL"]]);
  });

  it("reports each entry a load row delete takes", () => {
    const found = plan.validate([{ endpoint: "/db/BMLD", method: "DELETE", ids: [2] }], loadModel);
    expect(found.map((f) => [f.kind, f.value, f.outcome, f.reference.field])).toEqual([
      ["items", "LC", "deleted", "ITEMS[].LCNAME"],
      ["items", "DL", "deleted", "ITEMS[].LCNAME"],
    ]);
    expect(found[1]?.message).toContain('removes record 2 with every ITEMS entry, including ID 2 for "DL"');
    expect(plan.validate([{ endpoint: "/db/BMLD", method: "DELETE", ids: [7] }], loadModel)).toEqual([]);
  });

  it("deletes the row and posts back what is kept", () => {
    const record = loadModel["/db/BMLD"]["2"];
    const ops = plan.removeItems("/db/BMLD", 2, record, { case: "LC" });
    expect(ops).toEqual([
      { endpoint: "/db/BMLD", method: "DELETE", ids: [2] },
      { endpoint: "/db/BMLD", method: "POST", records: { "2": { ITEMS: [{ ID: 2, LCNAME: "DL", P: [-10] }] } } },
    ]);
    expect(plan.removeItems("/db/BMLD", 2, record, { ids: [1, 2] }).map((o) => o.method)).toEqual(["DELETE"]);
    expect(plan.removeItems("/db/BMLD", 2, record, { case: "WIND" })).toEqual([]);
    expect(() => plan.removeItems("/db/NODE", 2, record, { case: "LC" })).toThrow();
    expect(() => plan.removeItems("/db/BMLD", 2, record, {})).toThrow();
    expect(() => plan.removeItems("/db/BMLD", 2, record, { case: "LC", ids: [1] })).toThrow();
  });
});
