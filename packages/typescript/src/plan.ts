import { keyPolicies, referenceFields, referenceGraph, type ReferenceField } from "./generated/references";
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

/** What `plan.validate` expects the product to do with one value. */
export interface PlanFinding<T extends PlanOperation = PlanOperation> {
  /** Position of the operation in the list given. */
  index: number;
  operation: T;
  recordKey: string;
  reference: ReferenceField;
  value: unknown;
  /** missing: names a record that will not exist when sent. deleted: a later DELETE removes what it names. */
  kind: "missing" | "deleted";
  /** `reference.onMissing` for a missing value, `reference.onTargetDelete` for a deleted one, else "unverified". */
  outcome: ReferenceField["onMissing"] | NonNullable<ReferenceField["onTargetDelete"]>;
  message: string;
}

function rank(endpoint: string, seen: Map<string, number> = new Map()): number {
  const known = seen.get(endpoint);
  if (known !== undefined) return known;
  const targets = referenceGraph[endpoint] ?? [];
  const depth = targets.length ? 1 + Math.max(...targets.map((t) => rank(t, seen))) : 0;
  seen.set(endpoint, depth);
  return depth;
}

function checkMethods(operations: readonly PlanOperation[]): void {
  for (const op of operations) {
    const method = String(op.method).toUpperCase();
    if (method !== "POST" && method !== "PUT" && method !== "DELETE") {
      throw new Error(`${op.endpoint}: cannot order a ${op.method} (POST, PUT or DELETE only)`);
    }
  }
}

function references(table?: string): ReferenceField[] {
  return referenceFields.filter((ref) => table === undefined || ref.table === table);
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** The values at `path` in one record; empty slots (null, 0, "") skipped. */
function values(record: unknown, path: string, each: boolean): unknown[] {
  let nodes: unknown[] = [record];
  for (const part of path.split(".")) {
    const isList = part.endsWith("[]");
    const name = isList ? part.slice(0, -2) : part;
    const found: unknown[] = [];
    for (const node of nodes) {
      if (!isObject(node) || !(name in node)) continue;
      const value = node[name];
      if (isList) found.push(...(Array.isArray(value) ? value : []));
      else found.push(value);
    }
    nodes = found;
  }
  const out: unknown[] = [];
  for (const value of nodes) {
    for (const item of each && Array.isArray(value) ? value : [value]) {
      if (item === null || item === undefined || item === 0 || item === "" || typeof item === "object") continue;
      out.push(item);
    }
  }
  return out;
}

/** Every key and name a write to `endpoint` makes available as a target. */
function namesWritten(endpoint: string, records: Record<string, unknown>): Set<string> {
  const nameFields = new Set(
    referenceFields.filter((ref) => ref.targets.includes(endpoint) && ref.nameField).map((ref) => ref.nameField as string),
  );
  const out = new Set<string>();
  for (const [key, record] of Object.entries(records)) {
    out.add(String(key));
    if (!isObject(record)) continue;
    for (const field of nameFields) {
      const name = record[field];
      if (name !== undefined && name !== null && name !== "") out.add(String(name));
    }
  }
  return out;
}

/**
 * Order `/db/*` writes so a record is sent after the records it names.
 *
 * Offline and pure: nothing here calls NX. The graph is the contracts'
 * `references` and node/element record keys, the same one Python's
 * `midas_nx.plan` holds, and `references()` is the field-level list behind it.
 * Only measured references are in it (2026-11-04, Gen NX and Civil NX); a table
 * no contract gives a reference to ranks with the tables that name nothing.
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
  /** Every field reference the contracts record, or the ones whose records live in `table`. */
  references,
  /**
   * Where a POST to `endpoint` lands when its Assign key is not the next free
   * one: "honoured" (the requested key), "assigned" (the product picks one past
   * the highest - read the table back), or undefined where not measured.
   */
  keyPolicy: (endpoint: string, product: "gen" | "civil"): "honoured" | "assigned" | undefined =>
    keyPolicies[endpoint]?.[product],
  /** 0 for a table that names nothing, else one more than its deepest target. */
  rank: (endpoint: string): number => rank(endpoint),
  /**
   * Deletes first, dependents before what they name; then writes, the reverse.
   * Stable: operations of equal rank keep the caller's order, so a `/db/UNIT`
   * change placed first stays first. Throws on a method other than POST, PUT or
   * DELETE.
   */
  order: <T extends PlanOperation>(operations: readonly T[]): T[] => {
    checkMethods(operations);
    const seen = new Map<string, number>();
    const keyed = operations.map((op, index) => {
      const r = rank(op.endpoint, seen);
      const isDelete = String(op.method).toUpperCase() === "DELETE";
      return { op, key: [isDelete ? 0 : 1, isDelete ? -r : r, index] as const };
    });
    keyed.sort((a, b) => a.key[0] - b.key[0] || a.key[1] - b.key[1] || a.key[2] - b.key[2]);
    return keyed.map((item) => item.op);
  },
  /**
   * Report each reference the product will answer by refusing, orphaning or
   * dropping. Offline and pure; never throws for a finding. Operations are read
   * **in the order given** - run `order()` first to check what will be sent.
   *
   * `existing` maps a table to the ids or names already in the model (ids for a
   * table named by id, `NAME` values for one named by name). A target table
   * absent from it is unknown, and a value naming it is never reported missing;
   * pass `{"/db/NODE": []}` to say a table is empty. `0`, `""` and `null` are
   * empty slots (`/db/ELEM` pads `NODE` with zeros) and are skipped.
   *
   * A DELETE reports the records written earlier in the list that name what it
   * removes, with the measured `onTargetDelete`. Records already in the model
   * cannot be seen from here, and a name-keyed target removed by a DELETE is
   * tracked only when the list wrote it.
   */
  validate: <T extends PlanOperation>(
    operations: readonly T[],
    existing: Readonly<Record<string, Iterable<number | string>>> = {},
  ): PlanFinding<T>[] => {
    checkMethods(operations);
    const known = new Map<string, Set<string>>(
      Object.entries(existing).map(([table, ids]) => [table, new Set([...ids].map(String))]),
    );
    const byId = new Map<string, Map<string, Set<string>>>();
    const later = new Map<string, [number, Set<string>][]>();
    operations.forEach((op, index) => {
      const method = String(op.method).toUpperCase();
      if ((method === "POST" || method === "PUT") && op.records) {
        const list = later.get(op.endpoint) ?? [];
        list.push([index, namesWritten(op.endpoint, op.records)]);
        later.set(op.endpoint, list);
      }
    });

    const findings: PlanFinding<T>[] = [];
    const written: [number, T][] = [];
    operations.forEach((op, index) => {
      if (String(op.method).toUpperCase() === "DELETE") {
        const gone = new Set((op.ids ?? []).map(String));
        const table = byId.get(op.endpoint);
        for (const key of [...gone]) {
          for (const name of table?.get(key) ?? []) gone.add(name);
          table?.delete(key);
        }
        const knownSet = known.get(op.endpoint);
        if (knownSet) for (const name of gone) knownSet.delete(name);
        for (const [earlierIndex, earlier] of written) {
          for (const ref of references(earlier.endpoint)) {
            if (!ref.targets.includes(op.endpoint)) continue;
            for (const [recordKey, record] of Object.entries(earlier.records ?? {})) {
              for (const value of values(record, ref.field, ref.each)) {
                if (!gone.has(String(value))) continue;
                const outcome = ref.onTargetDelete ?? "unverified";
                findings.push({
                  index, operation: op, recordKey, reference: ref, value, kind: "deleted", outcome,
                  message:
                    `${op.endpoint} DELETE removes ${JSON.stringify(value)}, which ${earlier.endpoint} ` +
                    `record ${recordKey} (operation ${earlierIndex}) names in ${ref.field}: ${outcome}`,
                });
              }
            }
          }
        }
        return;
      }
      for (const [recordKey, record] of Object.entries(op.records ?? {})) {
        for (const ref of references(op.endpoint)) {
          if (!ref.targets.every((t) => known.has(t))) continue;
          for (const value of values(record, ref.field, ref.each)) {
            if (ref.targets.some((t) => known.get(t)?.has(String(value)))) continue;
            const createdLater = ref.targets.flatMap((t) =>
              (later.get(t) ?? []).filter(([i, names]) => i > index && names.has(String(value))).map(([i]) => i),
            );
            const hint = createdLater.length ? `; operation ${createdLater[0]} writes it later, see order()` : "";
            findings.push({
              index, operation: op, recordKey, reference: ref, value, kind: "missing", outcome: ref.onMissing,
              message:
                `${op.endpoint} record ${recordKey} names ${JSON.stringify(value)} in ${ref.field}, ` +
                `which ${ref.targets.join("/")} will not hold: ${ref.onMissing}${hint}`,
            });
          }
        }
      }
      if (op.records) {
        const names = namesWritten(op.endpoint, op.records);
        const knownSet = known.get(op.endpoint);
        if (knownSet) for (const name of names) knownSet.add(name);
        const table = byId.get(op.endpoint) ?? new Map<string, Set<string>>();
        byId.set(op.endpoint, table);
        for (const [key, record] of Object.entries(op.records)) {
          const entry = table.get(key) ?? new Set<string>();
          for (const name of namesWritten(op.endpoint, { [key]: record })) if (name !== key) entry.add(name);
          table.set(key, entry);
        }
        written.push([index, op]);
      }
    });
    return findings;
  },
};
