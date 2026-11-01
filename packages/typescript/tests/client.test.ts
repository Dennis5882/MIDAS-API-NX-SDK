import { describe, expect, it, vi } from "vitest";

import {
  DestructiveOperationError,
  MidasAuthError,
  MidasClient,
  MidasConnectionError,
  MidasResultError,
  MidasServerError,
  ProductMismatchError,
} from "../src";

function response(body: unknown, init: ResponseInit = {}): Response {
  return new Response(body === undefined ? undefined : JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

describe("MidasClient", () => {
  it("builds the product URL and sends the MAPI key", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(response({ NODE: {} }));
    const client = new MidasClient({ mapiKey: "secret", product: "civil", fetch });

    await client.request("GET", "/db/NODE");

    expect(fetch).toHaveBeenCalledWith(
      "https://moa-engineers.midasit.com:443/civil/db/NODE",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ "MAPI-Key": "secret" }),
      }),
    );
  });

  it("raises for a 2xx error body", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      response({ error: { message: "Please perform analysis." } }),
    );
    const client = new MidasClient({ fetch });

    await expect(client.request("POST", "/post/TABLE", {})).rejects.toBeInstanceOf(
      MidasResultError,
    );
  });

  it("can return a 2xx error body when explicitly configured", async () => {
    const body = { error: { message: "Please perform analysis." } };
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(response(body));
    const client = new MidasClient({ fetch, raiseOnResultError: false });

    await expect(client.request("POST", "/post/TABLE", {})).resolves.toEqual(body);
  });

  it("maps authentication failures", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      response({ message: "invalid key" }, { status: 401 }),
    );
    const client = new MidasClient({ fetch });

    await expect(client.request("GET", "/db/NODE")).rejects.toBeInstanceOf(MidasAuthError);
  });

  it("keeps non-JSON responses inside the SDK error hierarchy", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      new Response("<html>proxy</html>", { status: 200 }),
    );
    const client = new MidasClient({ fetch });

    await expect(client.request("GET", "/db/NODE")).rejects.toBeInstanceOf(MidasServerError);
  });

  it("calls fetch with no receiver, as a browser's native fetch requires", async () => {
    // A browser's fetch throws "Illegal invocation" unless `this` is the
    // global object or undefined; Node's does not check, so mimic the browser.
    const strictFetch = function (this: unknown) {
      if (this !== undefined && this !== globalThis) {
        throw new TypeError("Illegal invocation");
      }
      return Promise.resolve(response({ status: "connected" }));
    } as typeof globalThis.fetch;
    const original = globalThis.fetch;
    globalThis.fetch = strictFetch;
    try {
      await expect(new MidasClient({ mapiKey: "k" }).verifyConnection()).resolves.toEqual({
        status: "connected",
      });
      await expect(
        new MidasClient({ mapiKey: "k", fetch: strictFetch }).verifyConnection(),
      ).resolves.toEqual({ status: "connected" });
    } finally {
      globalThis.fetch = original;
    }
  });

  it("applies the timeout while the body is read, and wraps a stalled body", async () => {
    // Headers arrive, the body never finishes: the abort signal must still end it.
    const fetch = vi.fn<typeof globalThis.fetch>().mockImplementation(async (_url, init) => {
      const body = new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode('{"a":'));
          init?.signal?.addEventListener("abort", () => controller.error(init.signal?.reason));
        },
      });
      return new Response(body, { status: 200 });
    });
    const client = new MidasClient({ fetch, timeout: 20 });

    await expect(client.request("GET", "/db/NODE")).rejects.toBeInstanceOf(MidasConnectionError);
  });

  it("does not let an empty message hide error.message", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      response({ message: "", error: { message: "Wrong Field" } }, { status: 400 }),
    );
    await expect(new MidasClient({ fetch }).request("GET", "/db/NODE")).rejects.toThrow(
      /-> 400: Wrong Field$/,
    );
  });

  it("shows an error object without a message as JSON", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(response({ error: { code: 3 } }));
    await expect(new MidasClient({ fetch }).request("GET", "/db/NODE")).rejects.toThrow(
      'with an error body: {"code":3}',
    );
  });

  it("enforces product compatibility", () => {
    const client = new MidasClient({ product: "gen", fetch: vi.fn() });
    expect(() => client.checkProduct(["civil"], "Civil-only resource")).toThrow(
      ProductMismatchError,
    );
  });
});

describe("whole-table DELETE guard", () => {
  // DELETE /db/<NAME> empties the table whatever ids its body names - two apps
  // on the raw request lost every material and 324 elements to it.
  it.each(["/db/MATL", "/db/matl/", "/db/NODE?confirm=no"])(
    "refuses %s before sending anything",
    async (command) => {
      const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(response({}));
      const client = new MidasClient({ fetch });

      await expect(client.request("DELETE", command, { Assign: { 9: {} } })).rejects.toBeInstanceOf(
        DestructiveOperationError,
      );
      expect(fetch).not.toHaveBeenCalled();
    },
  );

  it("refuses a lowercase method too, which fetch sends as DELETE", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(response({}));
    const client = new MidasClient({ fetch });

    await expect(client.request("delete" as never, "/db/MATL")).rejects.toBeInstanceOf(
      DestructiveOperationError,
    );
    expect(fetch).not.toHaveBeenCalled();
  });

  it("sends it once confirmed, and leaves a per-id DELETE alone", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockImplementation(async () => response({}));
    const client = new MidasClient({ fetch });

    await client.request("DELETE", "/db/MATL", { Assign: {} }, { confirm: true });
    await client.request("DELETE", "/db/MATL/9");

    expect(fetch.mock.calls.map(([url]) => String(url))).toEqual([
      "https://moa-engineers.midasit.com:443/gen/db/MATL",
      "https://moa-engineers.midasit.com:443/gen/db/MATL/9",
    ]);
  });
});
