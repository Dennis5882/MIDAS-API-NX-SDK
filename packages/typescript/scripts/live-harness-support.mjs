/**
 * Pure helpers shared by the live harness and its unit tests.
 *
 * They live outside live-crud.mjs because that module runs `main()` on
 * import, so nothing there can be unit tested. What is here is exactly the
 * logic that decides how a live result is *read* -- which is worth a test of
 * its own, because getting it wrong turns a fixture problem into a reported
 * SDK regression.
 */

/** Verify only records created by this seed; existing names are not evidence. */
export function verifyRenumberedSeed(source, after, createdIds) {
  if (createdIds.length !== Object.keys(source.records).length) {
    throw new Error(`${source.endpoint}: setup POST did not store every seed record.`);
  }
  const remaining = new Set(createdIds);
  for (const payload of Object.values(source.records)) {
    const name = payload.NAME ?? payload.COMMON?.NAME;
    const id = [...remaining].find((key) =>
      (after[key].NAME ?? after[key].COMMON?.NAME) === name);
    if (typeof name !== "string" || id === undefined) {
      throw new Error(`${source.endpoint}: setup POST did not preserve the seed name.`);
    }
    remaining.delete(id);
  }
}

/**
 * Classify one case result the way scripts/live_crud_check.py classifies its
 * own rows, and for the same reason.
 *
 * A case whose *setup* failed says nothing about the endpoint under test, so
 * Python calls it BLOCKED and exits 3 -- "triage the fixture first". This
 * harness had no such class: any failure of a confirmed case read as REGRESS,
 * which is how a missing seed record was reported as a package regression.
 */
export function classifyResult(result) {
  if (result.ok) return "PASS";
  if (result.blocked) return "BLOCK";
  return result.confirmed ? "REGRESS" : "FAIL";
}

/**
 * Exit code for a whole run, mirroring live_crud_check.py: a regression is 1,
 * anything else unresolved is 3, and a blocked case never reaches 1 however
 * confirmed the case is.
 */
export function exitCodeFor(results) {
  const failed = results.filter((result) => !result.ok);
  if (!failed.length) return 0;
  return failed.some((result) => result.confirmed && !result.blocked) ? 1 : 3;
}
