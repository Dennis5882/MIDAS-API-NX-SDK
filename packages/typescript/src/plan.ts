import { referenceGraph } from "./generated/references";
import type { JsonObject } from "./types";

/** One request to one table. `records` for POST/PUT, `ids` for DELETE. */
export interface PlanOperation {
  /** e.g. "/db/NODE" */
  endpoint: string;
  method: "POST" | "PUT" | "DELETE";
  records?: JsonObject;
  ids?: readonly (number | string)[];
  /** The caller's name for it. */
  label?: string;
}

function rank(endpoint: string, seen: Map<string, number> = new Map()): number {
  const known = seen.get(endpoint);
  if (known !== undefined) return known;
  const targets = referenceGraph[endpoint] ?? [];
  const depth = targets.length ? 1 + Math.max(...targets.map((t) => rank(t, seen))) : 0;
  seen.set(endpoint, depth);
  return depth;
}

/**
 * Order `/db/*` writes so a record is sent after the records it names.
 *
 * Offline and pure: nothing here calls NX. The graph is the contracts'
 * `references` and node/element record keys, the same one Python's
 * `midas_nx.plan` holds. Only measured references are in it (2026-11-04, Gen NX
 * and Civil NX); a table no contract gives a reference to ranks with the tables
 * that name nothing.
 *
 * When the order is wrong, a missing node, load case or group name is refused,
 * but an element naming a material or section that does not exist is stored as
 * an orphan, and `/db/GRUP` and `/db/ELNK` drop a missing entry silently. A
 * per-id DELETE of a node removes the elements on it, and of a load case the
 * loads in it.
 */
export const plan = {
  /** Table -> the tables its records name. */
  dependencies: (): Readonly<Record<string, readonly string[]>> => referenceGraph,
  /** 0 for a table that names nothing, else one more than its deepest target. */
  rank: (endpoint: string): number => rank(endpoint),
  /**
   * Deletes first, dependents before what they name; then writes, the reverse.
   * Stable: operations of equal rank keep the caller's order, so a `/db/UNIT`
   * change placed first stays first. Throws on a method other than POST, PUT or
   * DELETE.
   */
  order: <T extends PlanOperation>(operations: readonly T[]): T[] => {
    for (const op of operations) {
      const method = String(op.method).toUpperCase();
      if (method !== "POST" && method !== "PUT" && method !== "DELETE") {
        throw new Error(`${op.endpoint}: cannot order a ${op.method} (POST, PUT or DELETE only)`);
      }
    }
    const seen = new Map<string, number>();
    const keyed = operations.map((op, index) => {
      const r = rank(op.endpoint, seen);
      const isDelete = String(op.method).toUpperCase() === "DELETE";
      return { op, key: [isDelete ? 0 : 1, isDelete ? -r : r, index] as const };
    });
    keyed.sort((a, b) => a.key[0] - b.key[0] || a.key[1] - b.key[1] || a.key[2] - b.key[2]);
    return keyed.map((item) => item.op);
  },
};
