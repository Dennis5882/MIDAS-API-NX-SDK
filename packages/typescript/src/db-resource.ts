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

  async create(items: ItemMap<TPayload>, client: MidasClient = getDefaultClient()): Promise<JsonObject> {
    this.check(client, "POST");
    return client.request("POST", this.metadata.endpoint, { Assign: stringifyKeys(items) });
  }

  async update(items: ItemMap<TPayload>, client: MidasClient = getDefaultClient()): Promise<JsonObject> {
    this.check(client, "PUT");
    return client.request("PUT", this.metadata.endpoint, { Assign: stringifyKeys(items) });
  }

  async delete(ids: readonly ItemId[], client: MidasClient = getDefaultClient()): Promise<Record<string, JsonObject>> {
    this.check(client, "DELETE");
    const entries = await Promise.all(
      ids.map(async (id) => [String(id), await client.request<JsonObject>("DELETE", `${this.metadata.endpoint}/${id}`)] as const),
    );
    return Object.fromEntries(entries);
  }

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
