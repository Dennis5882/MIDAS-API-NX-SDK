export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | JsonObject;
export interface JsonObject {
  [key: string]: JsonValue | undefined;
}

export type Product = "gen" | "civil";
export type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";
export type Timeout = number;
export type ItemId = string | number;
export type ItemMap<T extends object> = Record<ItemId, T>;
export type NumericItemMap<T extends object> = Record<number, T>;

export interface MidasClientOptions {
  mapiKey?: string;
  baseUrl?: string;
  product?: Product;
  timeout?: Timeout;
  strictProduct?: boolean;
  raiseOnResultError?: boolean;
  /**
   * Fetch implementation, `globalThis.fetch` by default. It is called as a
   * plain function, with no receiver, so a native browser fetch can be passed
   * as is; an implementation that relies on its own `this` must be bound first.
   */
  fetch?: typeof globalThis.fetch;
}

export interface RequestOptions {
  /**
   * Per-request timeout in milliseconds. A timeout stops waiting; it does not
   * roll back an operation that MIDAS NX has already accepted.
   */
  timeout?: Timeout;
  signal?: AbortSignal;
}
