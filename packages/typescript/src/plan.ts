import {
  itemRows,
  keyPolicies,
  keyReferences,
  type ItemRow,
  referenceFields,
  referenceGraph,
  type ReferenceField,
} from "./generated/references";
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
  /**
   * missing: names a record that will not exist when sent. deleted: a later
   * DELETE removes what it names. items: a DELETE of an `itemRows` record
   * removes this entry with it (one per entry; `value` is the load case,
   * `reference` the case field's).
   */
  kind: "missing" | "deleted" | "items";
  /** `reference.onMissing` for a missing value, `reference.onTargetDelete` for a deleted one,
   * "deleted" for an entry, else "unverified". */
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

/** The table(s) keyed by node or element ids, or the one for `table`; `field` is "". */
function keyRefs(table?: string): ReferenceField[] {
  return keyReferences.filter((ref) => table === undefined || ref.table === table);
}

function allReferences(table: string): ReferenceField[] {
  return [...references(table), ...keyRefs(table)];
}

function rows(table?: string): ItemRow[] {
  return itemRows.filter((row) => table === undefined || row.table === table);
}

/** What a PUT of `record` leaves over `previous`: fields replaced, and an
 * `itemRows` list merged entry by entry on `by` (as measured). */
function mergePut(endpoint: string, previous: unknown, record: unknown): unknown {
  if (!isObject(previous) || !isObject(record)) return record;
  const merged: Record<string, unknown> = { ...previous, ...record };
  for (const row of rows(endpoint)) {
    const old = previous[row.path];
    const next = record[row.path];
    if (!Array.isArray(old) || !Array.isArray(next)) continue;
    const entries = [...old];
    const at = new Map<string, number>();
    entries.forEach((entry, i) => {
      if (isObject(entry)) at.set(String(entry[row.by]), i);
    });
    for (const entry of next) {
      const key = isObject(entry) ? String(entry[row.by]) : undefined;
      const i = key === undefined ? undefined : at.get(key);
      if (i !== undefined) {
        entries[i] = { ...(entries[i] as Record<string, unknown>), ...(entry as Record<string, unknown>) };
      } else {
        if (key !== undefined) at.set(key, entries.length);
        entries.push(entry);
      }
    }
    merged[row.path] = entries;
  }
  return merged;
}

function itemFindings<T extends PlanOperation>(index: number, op: T, key: string, record: unknown): PlanFinding<T>[] {
  const findings: PlanFinding<T>[] = [];
  for (const row of rows(op.endpoint)) {
    const ref = referenceFields.find((r) => r.table === op.endpoint && r.field === `${row.path}[].${row.caseField}`);
    const entries = isObject(record) ? record[row.path] : undefined;
    if (!ref || !Array.isArray(entries)) continue;
    for (const entry of entries) {
      if (!isObject(entry)) continue;
      const value = entry[row.caseField];
      findings.push({
        index, operation: op, recordKey: key, reference: ref, value, kind: "items", outcome: "deleted",
        message:
          `${op.endpoint} DELETE removes record ${key} with every ${row.path} entry, ` +
          `including ${row.by} ${JSON.stringify(entry[row.by])} for ${JSON.stringify(value)}: deleted`,
      });
    }
  }
  return findings;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** `[value, the object holding it]` at `path` in one record; empty slots (null, 0, "") skipped. */
function values(record: unknown, path: string, each: boolean): [unknown, Record<string, unknown>][] {
  const parts = path.split(".");
  const leaf = parts.pop() as string;
  let nodes: unknown[] = [record];
  for (const part of parts) {
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
  const out: [unknown, Record<string, unknown>][] = [];
  for (const node of nodes) {
    if (!isObject(node) || !(leaf in node)) continue;
    const value = node[leaf];
    for (const item of each && Array.isArray(value) ? value : [value]) {
      if (item === null || item === undefined || item === 0 || item === "" || typeof item === "object") continue;
      out.push([item, node]);
    }
  }
  return out;
}

/** What `ref` reads from one record: its key for a key reference, else the field. */
function refValues(ref: ReferenceField, recordKey: string, record: unknown): [unknown, Record<string, unknown>][] {
  if (!ref.field) return [[recordKey, isObject(record) ? record : {}]];
  return values(record, ref.field, ref.each);
}

/** The table(s) a value names, given the object that holds the field (`targetsBy`). */
function targetsFor(ref: ReferenceField, holder: Record<string, unknown>): readonly string[] {
  if (ref.targetsBy) {
    const picked = ref.targetsBy.cases[String(holder[ref.targetsBy.path])];
    if (picked && holder[ref.targetsBy.path] !== undefined) return picked;
  }
  return ref.targets;
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

function isIterable(value: unknown): value is Iterable<number | string> {
  return typeof value === "object" && value !== null && Symbol.iterator in value;
}

/** The records still present that name something `op` removes, and what the
 * measured `onTargetDelete` then does to them in `state`. A record that goes
 * with it is followed in turn: a node takes its elements, and an element the
 * loads keyed by it. */
function deletedFindings<T extends PlanOperation>(
  index: number,
  op: T,
  gone: Set<string>,
  state: Map<string, Map<string, [number | null, unknown]>>,
  known: Map<string, Set<string>>,
): PlanFinding<T>[] {
  const findings: PlanFinding<T>[] = [];
  const queue: [string, Set<string>][] = [[op.endpoint, gone]];
  while (queue.length) {
    const [target, removed] = queue.shift() as [string, Set<string>];
    const effects = new Map<string, { table: string; recordKey: string; hits: [ReferenceField, Record<string, unknown>][] }>();
    for (const [table, records] of state) {
      const refs = allReferences(table).filter((ref) => ref.targets.includes(target));
      for (const [recordKey, [origin, record]] of records) {
        const where = origin === null ? "already in the model" : `operation ${origin}`;
        for (const ref of refs) {
          for (const [value, holder] of refValues(ref, recordKey, record)) {
            if (!removed.has(String(value)) || !targetsFor(ref, holder).includes(target)) continue;
            const outcome = ref.onTargetDelete ?? "unverified";
            const what = target === op.endpoint ? `removes ${JSON.stringify(value)}` : `takes ${target} ${JSON.stringify(value)} with it`;
            findings.push({
              index, operation: op, recordKey, reference: ref, value, kind: "deleted", outcome,
              message:
                `${op.endpoint} DELETE ${what}, which ${table} record ${recordKey} ` +
                `(${where}) names in ${ref.field || "its key"}: ${outcome}`,
            });
            const id = JSON.stringify([table, recordKey]);
            const entry = effects.get(id) ?? { table, recordKey, hits: [] };
            entry.hits.push([ref, holder]);
            effects.set(id, entry);
          }
        }
      }
    }
    for (const { table, recordKey, hits } of effects.values()) {
      const dropped = applyDeleteEffects(state, known, table, recordKey, hits);
      if (dropped) queue.push([table, dropped]);
    }
  }
  return findings;
}

/**
 * Change one record in `state` as the product does: drop it or the list entries
 * ("deleted"), or empty the fields ("cleared"). The record is replaced by a
 * changed copy, never changed in place, since it may be the caller's. A path
 * deeper than one list is left as it was. Returns the key and names of the
 * record when it is dropped.
 */
function applyDeleteEffects(
  state: Map<string, Map<string, [number | null, unknown]>>,
  known: Map<string, Set<string>>,
  table: string,
  recordKey: string,
  hits: [ReferenceField, Record<string, unknown>][],
): Set<string> | undefined {
  const tableState = state.get(table);
  const current = tableState?.get(recordKey);
  if (!tableState || !current) return undefined;
  const [origin, record] = current;
  let dropRecord = false;
  const cleared: [string | null, number, string][] = [];
  const dropped = new Map<string, Set<number>>();
  for (const [ref, holder] of hits) {
    const leaf = ref.field.split(".").pop() as string;
    if (ref.onTargetDelete !== "deleted" && ref.onTargetDelete !== "cleared") continue;
    if (!ref.field.includes("[]")) {
      if (ref.onTargetDelete === "deleted") dropRecord = true;
      else cleared.push([null, -1, leaf]);
      continue;
    }
    const cut = ref.field.indexOf("[].");
    const listName = ref.field.slice(0, cut);
    const rest = ref.field.slice(cut + 3);
    const entries = isObject(record) ? record[listName] : undefined;
    if (rest.includes(".") || !Array.isArray(entries)) continue;
    const position = entries.findIndex((entry) => entry === holder);
    if (position < 0) continue;
    if (ref.onTargetDelete === "deleted") {
      const set = dropped.get(listName) ?? new Set<number>();
      set.add(position);
      dropped.set(listName, set);
    } else cleared.push([listName, position, leaf]);
  }
  if (!dropRecord && !cleared.length && !dropped.size) return undefined;
  if (!dropRecord && isObject(record)) {
    const changed = JSON.parse(JSON.stringify(record)) as Record<string, unknown>;
    for (const [listName, position, leaf] of cleared) {
      const target = listName === null ? changed : ((changed[listName] as unknown[])[position] as Record<string, unknown>);
      target[leaf] = "";
    }
    for (const [listName, positions] of dropped) {
      const kept = (changed[listName] as unknown[]).filter((_, i) => !positions.has(i));
      changed[listName] = kept;
      if (!kept.length) dropRecord = true;
    }
    if (!dropRecord) {
      tableState.set(recordKey, [origin, changed]);
      return undefined;
    }
  }
  const names = namesWritten(table, { [recordKey]: record });
  const knownSet = known.get(table);
  if (knownSet) for (const name of names) knownSet.delete(name);
  tableState.delete(recordKey);
  return names;
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
 * per-id DELETE of a node removes the elements on it; of a load case, each load
 * entry and combination entry naming it, and a record left with none; of a
 * group, only the name, which is emptied; of a material, section or thickness,
 * nothing - the elements stay as orphans. A plate's `SECT` is a `/db/THIK`
 * number and a beam's a `/db/SECT` one (told apart by analysis). A record keyed
 * by a node or element (`keyReferences()`: loads, supports, masses, end
 * releases) goes when that node or element does, and a node takes the element
 * loads with its elements.
 */
export const plan = {
  /** Table -> the tables its records name. */
  dependencies: (): Readonly<Record<string, readonly string[]>> => referenceGraph,
  /** Every field reference the contracts record, or the ones whose records live in `table`. */
  references,
  /**
   * The tables whose Assign key is a node or element id, as rows with `field`
   * "" (the record key), or the one for `table`. A key naming no node or
   * element is refused, and deleting it deletes the record (measured).
   */
  keyReferences: keyRefs,
  /**
   * The tables whose record holds a list of load-case entries that a PUT merges
   * by `by`, or the one for `table`. A PUT cannot remove an entry and an empty
   * list changes nothing; a per-id DELETE removes the record with every entry
   * (measured on both products, 2026-11-06).
   */
  itemRows: rows,
  /**
   * The operations that leave one `itemRows` record without some entries.
   * `record` is the record as read (a GET of the table, keyed by `key`); give
   * exactly one of `case` (drop that load case's entries) or `ids` (drop the
   * entries with those `ID` values). A PUT cannot remove an entry, so this is a
   * per-id DELETE of the record, then a POST of the entries kept, as they were
   * read - measured to leave just those, under their own `ID`. Empty when no
   * entry matches; the DELETE alone when none is kept. Between the two the
   * record is gone: if the POST is refused, the kept entries are only in
   * `record`. Throws for a table not in `itemRows`.
   */
  removeItems: (
    endpoint: string,
    key: number | string,
    record: Readonly<Record<string, unknown>>,
    select: { case?: string; ids?: readonly (number | string)[] },
  ): PlanOperation[] => {
    const row = rows(endpoint)[0];
    if (!row) throw new Error(`${endpoint}: not a table of load-case entries merged by id (see itemRows)`);
    if ((select.case === undefined) === (select.ids === undefined)) {
      throw new Error("removeItems: give exactly one of case or ids");
    }
    const entries = record[row.path];
    if (!Array.isArray(entries)) throw new Error(`${endpoint} record ${key}: no ${row.path} list`);
    const wanted = new Set((select.ids ?? []).map(String));
    const drop = (entry: unknown): boolean =>
      isObject(entry) &&
      (select.case !== undefined ? entry[row.caseField] === select.case : wanted.has(String(entry[row.by])));
    const kept = entries.filter((entry) => !drop(entry)).map((entry) => structuredClone(entry));
    if (kept.length === entries.length) return [];
    const operations: PlanOperation[] = [{ endpoint, method: "DELETE", ids: [key] }];
    if (kept.length) {
      operations.push({ endpoint, method: "POST", records: { [String(key)]: { ...record, [row.path]: kept } } as JsonObject });
    }
    return operations;
  },
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
   * `existing` describes what is already in the model, per table, as either the
   * ids or names in it (an array or other iterable: ids for a table named by id,
   * `NAME` values for one named by name) or its records keyed by id, as a GET of
   * the table returns them. A target table absent from it is unknown, and a
   * value naming it is never reported missing; pass `{"/db/NODE": []}` to say a
   * table is empty. `0`, `""` and `null` are empty slots (`/db/ELEM` pads `NODE`
   * with zeros) and are skipped.
   *
   * A DELETE reports every record that names what it removes and is still there
   * when it is sent: one written earlier in the list, or one passed as a record
   * in `existing`. A table given only as ids has no records to look in. Where
   * the measured `onTargetDelete` is "deleted", the records it takes with it are
   * gone from then on.
   *
   * A PUT merges into the record it names, and an `itemRows` list entry by entry
   * on its `ID`, as the product does. A DELETE of such a record that is known
   * (earlier in the list, or a record in `existing`) reports each entry it
   * takes, kind "items": deleting the row removes every load case in it, not
   * only the one a caller may mean. See `removeItems`.
   */
  validate: <T extends PlanOperation>(
    operations: readonly T[],
    existing: Readonly<Record<string, Iterable<number | string> | Readonly<Record<string, unknown>>>> = {},
  ): PlanFinding<T>[] => {
    checkMethods(operations);
    const known = new Map<string, Set<string>>();
    /** table -> key -> [operation index or null, record] */
    const state = new Map<string, Map<string, [number | null, unknown]>>();
    for (const [table, given] of Object.entries(existing)) {
      if (isIterable(given)) {
        known.set(table, new Set([...given].map(String)));
      } else {
        const records = Object.fromEntries(Object.entries(given));
        known.set(table, namesWritten(table, records));
        state.set(table, new Map(Object.entries(records).map(([key, record]) => [key, [null, record]])));
      }
    }
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
    operations.forEach((op, index) => {
      const method = String(op.method).toUpperCase();
      if (method === "DELETE") {
        const tableState = state.get(op.endpoint);
        const gone = new Set<string>();
        for (const key of (op.ids ?? []).map(String)) {
          gone.add(key);
          const entry = tableState?.get(key);
          if (entry) {
            findings.push(...itemFindings(index, op, key, entry[1]));
            for (const name of namesWritten(op.endpoint, { [key]: entry[1] })) gone.add(name);
            tableState?.delete(key);
          }
        }
        const knownSet = known.get(op.endpoint);
        if (knownSet) for (const name of gone) knownSet.delete(name);
        findings.push(...deletedFindings(index, op, gone, state, known));
        return;
      }
      for (const [recordKey, written] of Object.entries(op.records ?? {})) {
        // A PUT merges, so a field it leaves out still decides targetsBy.
        const previous = method === "PUT" ? state.get(op.endpoint)?.get(recordKey)?.[1] : undefined;
        const record = previous === undefined ? written : mergePut(op.endpoint, previous, written);
        for (const ref of allReferences(op.endpoint)) {
          for (const [value, holder] of refValues(ref, recordKey, record)) {
            const targets = targetsFor(ref, holder);
            if (!targets.every((t) => known.has(t)) || targets.some((t) => known.get(t)?.has(String(value)))) continue;
            const createdLater = targets.flatMap((t) =>
              (later.get(t) ?? []).filter(([i, names]) => i > index && names.has(String(value))).map(([i]) => i),
            );
            const hint = createdLater.length ? `; operation ${createdLater[0]} writes it later, see order()` : "";
            findings.push({
              index, operation: op, recordKey, reference: ref, value, kind: "missing", outcome: ref.onMissing,
              message:
                `${op.endpoint} record ${recordKey} names ${JSON.stringify(value)} in ${ref.field || "its key"}, ` +
                `which ${targets.join("/")} will not hold: ${ref.onMissing}${hint}`,
            });
          }
        }
      }
      if (op.records) {
        const knownSet = known.get(op.endpoint);
        if (knownSet) for (const name of namesWritten(op.endpoint, op.records)) knownSet.add(name);
        const tableState = state.get(op.endpoint) ?? new Map<string, [number | null, unknown]>();
        state.set(op.endpoint, tableState);
        for (const [key, record] of Object.entries(op.records)) {
          const previous = tableState.get(key)?.[1];
          const merged = method === "PUT" && previous !== undefined ? mergePut(op.endpoint, previous, record) : record;
          tableState.set(key, [index, merged]);
        }
      }
    });
    return findings;
  },
};
