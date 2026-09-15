import { describe, expect, it } from "vitest";
import {
  caseCleanupMode, classifyResult, containsExpectedValue, exitCodeFor, setupCleanupMode,
  supportedCaseWrites,
  verifyRenumberedSeed,
} from "../scripts/live-harness-support.mjs";

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

describe("live expected-value matching", () => {
  it("finds a scalar nested in a live response", () => {
    expect(containsExpectedValue({ record: { mode: 1 } }, 1)).toBe(true);
  });

  it("compares an expected object by value rather than reference identity", () => {
    expect(containsExpectedValue(
      { OUT_OPT: { HINGE_OUT: 1, COMMON_OPT: false, FIBER_OUT: 1 } },
      { HINGE_OUT: 1, COMMON_OPT: false, FIBER_OUT: 1 },
    )).toBe(true);
  });

  it("does not accept a different object or array", () => {
    expect(containsExpectedValue({ OUT_OPT: { HINGE_OUT: 0 } }, { HINGE_OUT: 1 })).toBe(false);
    expect(containsExpectedValue({ values: [1, 2] }, [1, 3])).toBe(false);
  });
});

describe("live write-method selection", () => {
  it("runs PUT without inventing a POST step for a PUT-only resource", () => {
    expect(supportedCaseWrites(
      ["DELETE", "GET", "PUT"], ["DELETE", "GET", "PUT"],
    )).toEqual({ supportsPost: false, supportsPut: true });
  });

  it("runs both writes when the case and resource support both", () => {
    expect(supportedCaseWrites(
      ["DELETE", "GET", "POST", "PUT"], ["DELETE", "GET", "POST", "PUT"],
    )).toEqual({ supportsPost: true, supportsPut: true });
  });
});

describe("live case cleanup selection", () => {
  it("uses per-id DELETE whenever both fixture and resource support it", () => {
    expect(caseCleanupMode(
      ["DELETE", "GET", "PUT"], ["DELETE", "GET", "PUT"],
      { finalCase: false, resetDocument: false },
    )).toBe("per-id");
  });

  it("allows a no-DELETE case only as the final case before a document reset", () => {
    const methods = ["GET", "PUT"];
    expect(caseCleanupMode(
      methods, methods, { finalCase: true, resetDocument: true },
    )).toBe("document-reset");
    expect(caseCleanupMode(
      methods, methods, { finalCase: false, resetDocument: true },
    )).toBe("unsafe");
    expect(caseCleanupMode(
      methods, methods, { finalCase: true, resetDocument: false },
    )).toBe("unsafe");
  });

  it("allows a no-DELETE setup only when the final document reset owns cleanup", () => {
    const methods = ["GET", "POST", "PUT"];
    expect(setupCleanupMode(
      methods, { finalCase: true, resetDocument: true },
    )).toBe("document-reset");
    expect(setupCleanupMode(
      methods, { finalCase: false, resetDocument: true },
    )).toBe("unsafe");
    expect(setupCleanupMode(
      methods, { finalCase: true, resetDocument: false },
    )).toBe("unsafe");
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
