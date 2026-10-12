# midas-nx 2.10.1

A shared PyPI/npm version release that fixes **the npm package in a
browser**. Python is unchanged: `src/midas_nx/` is identical to 2.10.0 apart
from its version string, so PyPI gets the same code under the aligned number.

| surface | what actually changed |
| --- | --- |
| Python | nothing but the version string. The code in the wheel is otherwise identical to 2.10.0 |
| npm | `MidasClient` calls its fetch implementation without a receiver, so a browser's native `fetch` works. The `fetch` option gains documentation. No type or export changes |

## `MidasClient` failed in every browser

The client stored the fetch implementation on itself and called it as
`this.fetch(url, init)`. A browser's native `fetch` throws
`TypeError: Illegal invocation` when its receiver is anything other than the
global object or `undefined`, and a method call makes the receiver the client.
The SDK wrapped that error as `MidasConnectionError("GET /mapikey/verify
failed")`, which hid the cause - the very first call failed with what looked
like a connection problem.

Node's `fetch` does not check its receiver, so no test and no live run (all of
which use Node) could see it.

The client now takes the implementation into a local and calls it as a plain
function. That fixes both the default (`globalThis.fetch`) and an explicit
`fetch: window.fetch` option; binding only the default in the constructor would
have left the second broken. The public `fetch` property is unchanged.

**One thing to know if you pass your own fetch:** it is now called with no
`this`. A wrapper that depends on its own `this` has to be bound before it is
passed in (`fetch: myClient.fetch.bind(myClient)`).

A regression test mimics the browser's receiver check for both the default and
the option path; it fails against 2.10.0 with `Illegal invocation`.
