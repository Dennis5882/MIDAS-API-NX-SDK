import {
  DestructiveOperationError,
  UnsupportedMethodError,
} from "./errors";
import { getDefaultClient, type MidasClient } from "./client";
import type {
  HttpMethod,
  ItemId,
  ItemMap,
  JsonObject,
  NumericItemMap,
  Product,
} from "./types";

export interface DbResourceMetadata {
  className: string;
  endpoint: string;
  name: string;
  products: readonly Product[];
  methods: readonly HttpMethod[];
  pythonModule: string;
  /**
   * Field values this endpoint's contract requires be sent explicitly, filled
   * in on `create()` and `update()` for any record that omits them.
   *
   * These are never invented defaults. Each one is the value the official
   * manual already documents, made explicit on the wire because omitting it
   * has been observed to break the product. `/db/NMAS` is the case that
   * motivated it: leaving `rmX`/`rmY`/`rmZ` out of the payload hung the call
   * and killed the NX session across 15+ reproductions on both Gen NX and
   * Civil NX, while sending them as `0.0` - their own documented default - did
   * not. A caller should not have to know that to use the endpoint safely.
   *
   * Generated from `contracts/endpoints/*.yaml`; see `contracts/README.md`.
   */
  payloadDefaults?: Readonly<Record<string, unknown>>;
}

export class DbResource<TPayload extends object = JsonObject> {
  readonly metadata: DbResourceMetadata;

  constructor(metadata: DbResourceMetadata) {
    this.metadata = metadata;
  }

  private check(client: MidasClient, method: HttpMethod): void {
    client.checkProduct(this.metadata.products, this.metadata.name || this.metadata.className);
    if (!this.metadata.methods.includes(method)) {
      throw new UnsupportedMethodError(
        `${this.metadata.name || this.metadata.className} (${this.metadata.endpoint}) does not support ${method}; supported methods: ${this.metadata.methods.join(", ")}`,
        { method, endpoint: this.metadata.endpoint },
      );
    }
  }

  async get(client: MidasClient = getDefaultClient()): Promise<JsonObject> {
    this.check(client, "GET");
    return client.request("GET", this.metadata.endpoint);
  }

  async items(client: MidasClient = getDefaultClient()): Promise<NumericItemMap<TPayload>> {
    const response = await this.get(client);
    const table = Object.values(response).find(
      (value): value is JsonObject => typeof value === "object" && value !== null && !Array.isArray(value),
    );
    if (!table) return {};
    return Object.fromEntries(
      Object.entries(table).map(([key, value]) => [Number(key), value as TPayload]),
    ) as NumericItemMap<TPayload>;
  }

  async info(client: MidasClient = getDefaultClient()): Promise<JsonObject> {
    client.checkProduct(this.metadata.products, this.metadata.name || this.metadata.className);
    return client.request("GET", `/info${this.metadata.endpoint}`);
  }

  /**
   * Apply the contract's required-explicit field values to every record,
   * without overriding anything the caller supplied.
   */
  private normalize(items: ItemMap<TPayload>): ItemMap<TPayload> {
    const defaults = this.metadata.payloadDefaults;
    if (!defaults) return items;
    return Object.fromEntries(
      Object.entries(items).map(([id, payload]) => [id, { ...defaults, ...payload }]),
    ) as ItemMap<TPayload>;
  }

  async create(items: ItemMap<TPayload>, client: MidasClient = getDefaultClient()): Promise<JsonObject> {
    this.check(client, "POST");
    return client.request("POST", this.metadata.endpoint, {
      Assign: stringifyKeys(this.normalize(items)),
    });
  }

  async update(items: ItemMap<TPayload>, client: MidasClient = getDefaultClient()): Promise<JsonObject> {
    this.check(client, "PUT");
    return client.request("PUT", this.metadata.endpoint, {
      Assign: stringifyKeys(this.normalize(items)),
    });
  }

  /**
   * Delete only the requested IDs, one request at a time. Processing stops at
   * the first error so later destructive requests are never left running in
   * the background after this promise rejects.
   */
  async delete(ids: readonly ItemId[], client: MidasClient = getDefaultClient()): Promise<Record<string, JsonObject>> {
    this.check(client, "DELETE");
    const responses: Record<string, JsonObject> = {};
    // MIDAS NX sessions are stateful and several operations can block the
    // product UI. Keep destructive calls ordered and stop at the first error;
    // launching every DELETE with Promise.all would let later mutations keep
    // running after the caller has already received a rejection.
    for (const id of ids) {
      responses[String(id)] = await client.request<JsonObject>(
        "DELETE",
        `${this.metadata.endpoint}/${id}`,
      );
    }
    return responses;
  }

  /**
   * Empty the entire resource table.
   *
   * @warning This cannot be undone through the API. For `/db/NODE`, attached
   * elements are removed as well. Use `delete(ids)` for selected records.
   */
  async deleteAll(
    options: { confirm: true; client?: MidasClient } | { confirm?: false; client?: MidasClient },
  ): Promise<JsonObject> {
    if (options.confirm !== true) {
      throw new DestructiveOperationError(
        `${this.metadata.name || this.metadata.className} (${this.metadata.endpoint}): deleteAll() would delete every record in this table and cannot be undone.`,
        { method: "DELETE", endpoint: this.metadata.endpoint },
      );
    }
    const client = options.client ?? getDefaultClient();
    this.check(client, "DELETE");
    return client.request("DELETE", this.metadata.endpoint, { Assign: {} });
  }
}

function stringifyKeys<T extends object>(items: ItemMap<T>): JsonObject {
  return Object.fromEntries(Object.entries(items)) as JsonObject;
}

export function defineDbResource<TPayload extends object = JsonObject>(
  metadata: DbResourceMetadata,
): DbResource<TPayload> {
  return new DbResource<TPayload>(metadata);
}
