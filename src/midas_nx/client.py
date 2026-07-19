"""Core HTTP client for the MIDAS NX Open API.

Instance-based (no global mutable class-attribute state), raises exceptions on
error responses instead of exiting the process, and exposes a free-function
``MidasAPI(method, command, body)`` wrapper for parity with the calling
convention already documented in the MIDAS-API manual repo's README and
examples/python/basic_example.py.
"""
from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Any, Mapping, Optional

import requests

logger = logging.getLogger("midas_nx")

_HOST = "moa-engineers.midasit.com"


class Product(str, Enum):
    GEN = "gen"
    CIVIL = "civil"


def build_base_url(product: "Product | str") -> str:
    """Build the default global Base URL for a product.

    Regional variants (e.g. ``-in``/``-kr``/``-gb``/``-us``/``.cn`` hostnames,
    used by MIDASIT's official SDKs) are not documented in the MIDAS-API
    manual and are intentionally not guessed at here — pass ``base_url``
    explicitly to ``MidasClient`` if you need one. See docs/coverage.json.
    """
    product = Product(product)
    return f"https://{_HOST}:443/{product.value}"


class MidasAPIError(Exception):
    """Base class for all errors raised by this SDK."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        method: Optional[str] = None,
        endpoint: Optional[str] = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.method = method
        self.endpoint = endpoint
        self.response_body = response_body


class MidasAuthError(MidasAPIError):
    """401 / 403 — invalid or missing MAPI-Key."""


class MidasNotFoundError(MidasAPIError):
    """404 — model not connected, or resource/id not found."""


class MidasRequestError(MidasAPIError):
    """Other 4xx — malformed request."""


class MidasServerError(MidasAPIError):
    """5xx — server-side failure."""


class MidasConnectionError(MidasAPIError):
    """Network failure / timeout before a response was received."""


class ProductMismatchError(MidasAPIError):
    """Raised when a resource's PRODUCTS doesn't include the client's product."""


class UnsupportedMethodError(MidasAPIError):
    """Raised when a resource doesn't support the requested HTTP method
    (e.g. calling .create() on a GET/PUT-only endpoint like MATD)."""


_STATUS_EXCEPTIONS = {401: MidasAuthError, 403: MidasAuthError, 404: MidasNotFoundError}


class MidasClient:
    """A configured connection to one MIDAS NX Open API server.

    Example::

        client = MidasClient(mapi_key="...", product=Product.CIVIL)
        client.request("POST", "/doc/NEW", {"Argument": {}})
    """

    def __init__(
        self,
        mapi_key: Optional[str] = None,
        base_url: Optional[str] = None,
        product: "Product | str" = Product.GEN,
        timeout: float = 30.0,
        strict_product: bool = True,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.mapi_key = mapi_key or os.getenv("MIDAS_MAPI_KEY", "")
        self.product = Product(product)
        self.base_url = (base_url or os.getenv("MIDAS_BASE_URL") or build_base_url(self.product)).rstrip("/")
        self.timeout = timeout
        self.strict_product = strict_product
        self._session = session or requests.Session()

    def check_product(self, resource_products: frozenset, resource_name: str) -> None:
        if self.product.value not in resource_products:
            message = (
                f"{resource_name} supports {sorted(resource_products)}, "
                f"but this client is configured for product='{self.product.value}'"
            )
            if self.strict_product:
                raise ProductMismatchError(message)
            logger.warning(message)

    def request(self, method: str, command: str, body: Optional[Mapping[str, Any]] = None) -> dict:
        return self._send(method, self.base_url + command, body, endpoint=command)

    def verify_connection(self) -> dict:
        """GET {base url with the /gen or /civil product segment removed}/mapikey/verify.

        Docs: the MIDAS-API manual repo's docs/AUTHENTICATION.md, "연결 전 상태
        확인 — /mapikey/verify" — a health-check endpoint documented in the
        repo's auth guide rather than a per-chapter manual page (so it isn't
        tracked in docs/coverage.json/ROADMAP.md alongside the itemized
        endpoint surface). Distinguishes three cases: HTTP 200 with
        ``"status": "connected"``/``"keyVerified": True`` (healthy — the
        product process is alive and this MAPI-Key is valid for it); HTTP 200
        with ``"status": "disconnected"`` (product not connected — returned
        as-is, not raised, since it's a normal response shape, not an HTTP
        error); and HTTP 404 with a "client does not exist" message (the
        product process died after connecting — surfaced as
        ``MidasNotFoundError`` like any other 404). Useful as a sanity check
        right after constructing a client, or before a batch of calls that
        would otherwise each hit their own timeout if the product has
        silently died.
        """
        suffix = f"/{self.product.value}"
        root = self.base_url[: -len(suffix)] if self.base_url.endswith(suffix) else self.base_url
        return self._send("GET", f"{root}/mapikey/verify", None, endpoint="/mapikey/verify")

    def _send(
        self, method: str, url: str, body: Optional[Mapping[str, Any]], *, endpoint: str
    ) -> dict:
        headers = {"Content-Type": "application/json", "MAPI-Key": self.mapi_key}

        try:
            response = self._session.request(
                method.upper(), url, headers=headers, json=body, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise MidasConnectionError(
                f"{method.upper()} {endpoint} failed: {exc}", method=method, endpoint=endpoint
            ) from exc

        data: Any = response.json() if response.text else {}

        if response.ok:
            return data

        exc_cls = _STATUS_EXCEPTIONS.get(
            response.status_code,
            MidasServerError if response.status_code >= 500 else MidasRequestError,
        )
        message = response.reason
        if isinstance(data, dict):
            message = data.get("message") or (data.get("error") or {}).get("message") or message

        raise exc_cls(
            f"{method.upper()} {endpoint} -> {response.status_code}: {message}",
            status_code=response.status_code,
            method=method,
            endpoint=endpoint,
            response_body=data,
        )


_default_client: Optional[MidasClient] = None


def get_default_client() -> MidasClient:
    """Return the process-wide default client, constructing it lazily from
    MIDAS_MAPI_KEY / MIDAS_BASE_URL env vars on first use."""
    global _default_client
    if _default_client is None:
        _default_client = MidasClient()
    return _default_client


def configure(**kwargs: Any) -> MidasClient:
    """Reconfigure the process-wide default client.

    Example::

        configure(mapi_key="...", product=Product.CIVIL)
        MidasAPI("POST", "/doc/NEW", {"Argument": {}})
    """
    global _default_client
    _default_client = MidasClient(**kwargs)
    return _default_client


def MidasAPI(method: str, command: str, body: Optional[dict] = None) -> dict:
    """Free-function convenience wrapper around the default client.

    Matches the calling convention documented in the MIDAS-API manual repo's
    README.md and examples/python/basic_example.py.
    """
    return get_default_client().request(method, command, body)


def post_argument(command: str, argument, client: Optional[MidasClient] = None) -> dict:
    """Shared POST-with-``"Argument"``-wrapper helper for the non-ID-keyed
    endpoint families (``/doc/*``, ``/ope/*``, ``/view/*``, and the two plain
    ``/post/*`` endpoints in ``post/design.py``) — as opposed to the ID-keyed
    ``"Assign"`` wrapper used by ``db/base.py``'s ``DbResource``."""
    return (client or get_default_client()).request("POST", command, {"Argument": argument})


def get_result(command: str, client: Optional[MidasClient] = None) -> dict:
    """Shared GET helper (no request body) for the same non-ID-keyed
    endpoint families as :func:`post_argument`."""
    return (client or get_default_client()).request("GET", command)
