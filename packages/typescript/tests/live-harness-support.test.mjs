import { describe, expect, it } from "vitest";
import { classifyResult, exitCodeFor, verifyRenumberedSeed } from "../scripts/live-harness-support.mjs";

describe("renumbered live seed verification", () => {
  it.each([
    ["root NAME", { NAME: "seed" }],
    ["COMMON.NAME", { COMMON: { NAME: "seed" } }],
  ])("accepts a new server-assigned ID with %s", (_, payload) => {
    expect(() => verifyRenumberedSeed(
      { endpoint: "/db/TEST", records: { 90: payload } }, { 1: payload }, [1],
    )).not.toThrow();
  });

  it("rejects a silent no-op", () => {
    expect(() => verifyRenumberedSeed(
      { endpoint: "/db/TEST", records: { 90: { NAME: "seed" } } }, {}, [],
    )).toThrow("did not store every seed record");
  });

  it("does not count an existing matching name as the new seed", () => {
    expect(() => verifyRenumberedSeed(
      { endpoint: "/db/TEST", records: { 90: { NAME: "seed" } } },
      { 1: { NAME: "seed" }, 2: { NAME: "other" } }, [2],
    )).toThrow("did not preserve the seed name");
  });

  it("matches each seed to a distinct new record", () => {
    expect(() => verifyRenumberedSeed(
      { endpoint: "/db/TEST", records: { 90: { NAME: "seed" }, 91: { NAME: "seed" } } },
      { 1: { NAME: "seed" }, 2: { NAME: "other" } }, [1, 2],
    )).toThrow("did not preserve the seed name");
  });
});

// The classes and exit codes are scripts/live_crud_check.py's, deliberately.
// Two harnesses reading the same fixture must also read the same result, or a
// comparison between them measures the harnesses instead of the SDKs.
describe("live result classification", () => {
  it("reads a failure before the endpoint is touched as blocked, not a regression", () => {
    const blocked = { ok: false, confirmed: true, blocked: true };
    expect(classifyResult(blocked)).toBe("BLOCK");
    expect(exitCodeFor([blocked])).toBe(3);
  });

  it("still reports a confirmed case that failed on its own endpoint", () => {
    const regressed = { ok: false, confirmed: true };
    expect(classifyResult(regressed)).toBe("REGRESS");
    expect(exitCodeFor([regressed])).toBe(1);
  });

  it("separates an unconfirmed failure from a regression", () => {
    const unverified = { ok: false, confirmed: false };
    expect(classifyResult(unverified)).toBe("FAIL");
    expect(exitCodeFor([unverified])).toBe(3);
  });

  it("does not let a blocked case mask a real regression in the same run", () => {
    expect(exitCodeFor([
      { ok: false, confirmed: true, blocked: true },
      { ok: false, confirmed: true },
      { ok: true, confirmed: true },
    ])).toBe(1);
  });

  it("passes a clean run", () => {
    expect(classifyResult({ ok: true })).toBe("PASS");
    expect(exitCodeFor([{ ok: true }, { ok: true }])).toBe(0);
  });
});
