import {
  DestructiveOperationError,
  MidasConnectionError,
  MidasResultError,
  MidasServerError,
  ProductMismatchError,
  errorForStatus,
} from "./errors";
import type {
  HttpMethod,
  JsonObject,
  JsonValue,
  MidasClientOptions,
  Product,
  RequestOptions,
} from "./types";

const HOST = "moa-engineers.midasit.com";

export function buildBaseUrl(product: Product): string {
  return `https://${HOST}:443/${product}`;
}

function readEnvironment(name: string): string | undefined {
  const processLike = globalThis as typeof globalThis & {
    process?: { env?: Record<string, string | undefined> };
  };
  return processLike.process?.env?.[name];
}

/**
 * `/db/<NAME>` with no id after it - the URL whose DELETE empties the whole
 * table, whatever ids the body names. `/db/<NAME>/<id>` deletes one record.
 */
const WHOLE_TABLE_DELETE = /^\/db\/[^/]+\/?$/i;

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export class MidasClient {
  readonly mapiKey: string;
  readonly product: Product;
  readonly baseUrl: string;
  readonly timeout: number;
  readonly strictProduct: boolean;
  readonly raiseOnResultError: boolean;
  readonly fetch: typeof globalThis.fetch;

  constructor(options: MidasClientOptions = {}) {
    this.mapiKey = options.mapiKey ?? readEnvironment("MIDAS_MAPI_KEY") ?? "";
    this.product = options.product ?? "gen";
    this.baseUrl = (
      options.baseUrl ?? readEnvironment("MIDAS_BASE_URL") ?? buildBaseUrl(this.product)
    ).replace(/\/$/, "");
    this.timeout = options.timeout ?? 30_000;
    this.strictProduct = options.strictProduct ?? true;
    this.raiseOnResultError = options.raiseOnResultError ?? true;
    this.fetch = options.fetch ?? globalThis.fetch;
    if (typeof this.fetch !== "function") {
      throw new TypeError("A Fetch API implementation is required.");
    }
  }

  checkProduct(products: readonly Product[], resourceName: string): void {
    if (products.includes(this.product)) return;
    const message = `${resourceName} supports ${products.join(", ")}, but this client uses ${this.product}`;
    if (this.strictProduct) throw new ProductMismatchError(message);
    console.warn(message);
  }

  /**
   * Send one request.
   *
   * A `DELETE` to a bare `/db/<NAME>` - no id after it - throws
   * `DestructiveOperationError` before anything is sent unless
   * `options.confirm` is `true`. That is the manual's documented delete call,
   * and it empties the whole table whatever ids its `{ Assign: {...} }` body
   * names; for `/db/NODE` it takes the attached elements too. Two apps built on
   * this raw request lost every material, and every element of a 324-element
   * model, to it. `DELETE /db/<NAME>/<id>` removes one record and is not
   * affected; a resource's `delete(ids)` sends exactly that.
   */
  async request<T extends JsonValue = JsonObject>(
    method: HttpMethod,
    command: string,
    body?: JsonObject,
    options: RequestOptions & { confirm?: boolean } = {},
  ): Promise<T> {
    const path = command.split(/[?#]/, 1)[0] ?? command;
    if (method === "DELETE" && WHOLE_TABLE_DELETE.test(path) && options.confirm !== true) {
      throw new DestructiveOperationError(
        `DELETE ${path} empties the whole table, whatever ids the body names, and cannot be undone; DELETE ${path.replace(/\/$/, "")}/<id> removes one record. Pass { confirm: true } if emptying the table is intended.`,
        { method: "DELETE", endpoint: path },
      );
    }
    return this.send<T>(method, `${this.baseUrl}${command}`, command, body, options);
  }

  /**
   * Verify the key and product connection through the relay.
   *
   * A connected response does not prove the next model call will work: a
   * modal dialog in MIDAS NX can leave this endpoint healthy while `/db/*`
   * calls block. Use a cheap real GET when that distinction matters.
   */
  async verifyConnection<T extends JsonValue = JsonObject>(options: RequestOptions = {}): Promise<T> {
    const suffix = `/${this.product}`;
    const root = this.baseUrl.endsWith(suffix) ? this.baseUrl.slice(0, -suffix.length) : this.baseUrl;
    return this.send<T>("GET", `${root}/mapikey/verify`, "/mapikey/verify", undefined, options);
  }

  private async send<T extends JsonValue>(
    method: HttpMethod,
    url: string,
    endpoint: string,
    body: JsonObject | undefined,
    options: RequestOptions,
  ): Promise<T> {
    const controller = new AbortController();
    const timeout = options.timeout ?? this.timeout;
    const timer = setTimeout(() => controller.abort(new Error(`Timed out after ${timeout}ms`)), timeout);
    const onAbort = () => controller.abort(options.signal?.reason);
    options.signal?.addEventListener("abort", onAbort, { once: true });
    if (options.signal?.aborted) onAbort();

    let response: Response;
    try {
      const init: RequestInit = {
        method,
        headers: { "Content-Type": "application/json", "MAPI-Key": this.mapiKey },
        signal: controller.signal,
      };
      if (body !== undefined) init.body = JSON.stringify(body);
      // Called detached, never as `this.fetch(...)`: a browser's native fetch
      // throws "Illegal invocation" when its receiver is anything but the
      // global object or undefined, and a method call makes it this client.
      // Node does not check, so only a browser ever saw it. Detaching covers
      // the default and a `fetch: window.fetch` option alike.
      const fetchImpl = this.fetch;
      response = await fetchImpl(url, init);
    } catch (cause) {
      throw new MidasConnectionError(`${method} ${endpoint} failed`, { method, endpoint, cause });
    } finally {
      clearTimeout(timer);
      options.signal?.removeEventListener("abort", onAbort);
    }

    const text = await response.text();
    let data: JsonValue = {};
    if (text) {
      try {
        data = JSON.parse(text) as JsonValue;
      } catch (cause) {
        const ErrorClass = response.ok ? MidasServerError : errorForStatus(response.status);
        throw new ErrorClass(
          `${method} ${endpoint} -> ${response.status}: response body is not JSON: ${JSON.stringify(text.replace(/\s+/g, " ").slice(0, 200))}`,
          { statusCode: response.status, method, endpoint, responseBody: text, cause },
        );
      }
    }

    if (response.ok) {
      if (this.raiseOnResultError && isJsonObject(data) && data.error) {
        const detail = isJsonObject(data.error) ? data.error.message ?? data.error : data.error;
        throw new MidasResultError(
          `${method} ${endpoint} -> ${response.status} with an error body: ${String(detail)}`,
          { statusCode: response.status, method, endpoint, responseBody: data },
        );
      }
      return data as T;
    }

    const ErrorClass = errorForStatus(response.status);
    let detail: JsonValue | undefined;
    if (isJsonObject(data)) {
      const error = data.error;
      detail = data.message ?? (isJsonObject(error) ? error.message ?? error : error);
    }
    throw new ErrorClass(`${method} ${endpoint} -> ${response.status}: ${String(detail ?? response.statusText)}`, {
      statusCode: response.status,
      method,
      endpoint,
      responseBody: data,
    });
  }
}

let defaultClient: MidasClient | undefined;

export function getDefaultClient(): MidasClient {
  defaultClient ??= new MidasClient();
  return defaultClient;
}

export function configure(options: MidasClientOptions): MidasClient {
  defaultClient = new MidasClient(options);
  return defaultClient;
}

export async function midasApi<T extends JsonValue = JsonObject>(
  method: HttpMethod,
  command: string,
  body?: JsonObject,
  options?: RequestOptions & { confirm?: boolean },
): Promise<T> {
  return getDefaultClient().request<T>(method, command, body, options);
}
