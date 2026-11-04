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
