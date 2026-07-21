"""midas_nx — independent, unified Python SDK for the MIDAS NX Open API.

Covers both MIDAS Civil NX and MIDAS Gen NX (a "product" parameter selects
which). Built independently of MIDASIT's official midas-civil/midas-gen
packages against the schema documented at
https://github.com/Dennis5882/MIDAS-API/tree/main/docs/manual

See ROADMAP.md for endpoint coverage.
"""
from .client import (
    MidasAPI,
    MidasAPIError,
    MidasAuthError,
    MidasClient,
    MidasConnectionError,
    MidasNotFoundError,
    MidasRequestError,
    MidasServerError,
    Product,
    ProductMismatchError,
    UnsupportedMethodError,
    configure,
    get_default_client,
)

__version__ = "0.10.0"

__all__ = [
    "MidasAPI",
    "MidasClient",
    "Product",
    "configure",
    "get_default_client",
    "MidasAPIError",
    "MidasAuthError",
    "MidasNotFoundError",
    "MidasRequestError",
    "MidasServerError",
    "MidasConnectionError",
    "ProductMismatchError",
    "UnsupportedMethodError",
    "__version__",
]
