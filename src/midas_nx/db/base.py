"""Generic ``/db/*`` CRUD base class.

Source convention: MIDAS-API manual repo, e.g. docs/manual/03_DB_Node_Element.md
#1 (/db/NODE). Every /db/* endpoint is ID-keyed under an "Assign" wrapper for
POST/PUT/DELETE; GET returns the full set (no documented per-ID URL filtering
across the manual, so we don't invent one).

DELETE payload is inconsistent across the manual itself (some chapters send
``None`` per id, e.g. 03_DB_Node_Element.md; others send ``{}``, e.g.
06_DB_Static_Loads.md). We standardize on ``None`` (matches the NODE example,
the most-referenced endpoint in the manual) — both have been observed as
accepted by the server in the source docs.
"""
from __future__ import annotations

from typing import ClassVar, Optional, TypedDict

from ..client import MidasClient, UnsupportedMethodError, get_default_client

_ALL_METHODS = frozenset({"POST", "GET", "PUT", "DELETE"})

#: Shared METHODS override for endpoints that support everything but DELETE
#: (e.g. named-group definitions like /db/GRUP, /db/BNGR; single-record
#: settings like /db/PZEF, /db/CLDR) — import instead of redefining locally.
NO_DELETE_METHODS = frozenset({"POST", "GET", "PUT"})

#: Shared METHODS override for singleton Hyper-S-only settings endpoints that
#: don't support POST (e.g. /db/THGC-M1, /db/THOO-M1) — only GET/PUT/DELETE.
GET_PUT_DELETE_METHODS = frozenset({"GET", "PUT", "DELETE"})

#: Shared METHODS override for derived/read-only-input design-code records
#: that support neither POST nor PUT (e.g. ch24-27's LCTB "Load Contribution
#: for Nonlinear Load Case" endpoints) — only GET/DELETE.
GET_DELETE_METHODS = frozenset({"GET", "DELETE"})

#: Shared METHODS override for write-only/no-read design-code records that
#: don't support GET (e.g. ch27's DSRC "SRC Design Code" endpoint) — only
#: PUT/DELETE.
PUT_DELETE_METHODS = frozenset({"PUT", "DELETE"})

#: Shared PRODUCTS override for Civil-NX-only endpoints (e.g. /db/LCOM-CONC,
#: the entire ch08/ch17 bridge/moving-load chapters) — import instead of
#: redefining a local frozenset({"civil"}) per chapter.
CIVIL_ONLY = frozenset({"civil"})


class ItemGroupFields(TypedDict, total=False):
    """Shared ID/GROUP_NAME preamble for a /db/* "ITEMS" array entry — extend
    this instead of re-declaring ID/GROUP_NAME on every new Item TypedDict."""

    ID: int  # Serial Number, default 0, optional
    GROUP_NAME: str  # Group Name (Boundary/Load, depending on endpoint), default "", optional


class TimeValuePoint(TypedDict, total=False):
    """Shared {TIME, VALUE} pair used by several time-function "ITEM"/
    "aFUNCDATA" arrays (e.g. /db/THFC, /db/ETFC, /db/CCFC, /db/HSFC) —
    import this instead of re-declaring the same two fields per chapter."""

    TIME: float  # required
    VALUE: float  # required


class OptUseToleranceValue(TypedDict, total=False):
    """Shared {OPT_USE, VALUE} convergence-criterion pair used by several
    Hyper-S nested convergence objects (e.g. /db/ACTL-M1's TCELEM.CONVERGENCE,
    /db/NLCT-M1's CONV_CRITERIA, /db/POGD-M1's ITER_CTRL.NORM_CTRL — each of
    DISPL/LOAD/WORK or DISP/FORCE/ENERGY) — import this instead of
    re-declaring the same two fields per chapter."""

    OPT_USE: bool  # optional
    VALUE: float  # required if OPT_USE is true


class InitialLoadCaseItem(TypedDict, total=False):
    """Shared {LC_NAME, LC_TYPE, SF} pushover/pushover-Hyper-S initial-load
    entry (e.g. /db/POGD's "INITLOAD", /db/POGD-M1's "INIT_LOAD_LIST",
    /db/THGC-M1's "INIT_LOAD_LIST") — import this instead of re-declaring the
    same three fields per chapter."""

    LC_NAME: str  # Load Case Name, required
    LC_TYPE: str  # Load Case Type (e.g. "STATIC"/"STAGE"), required
    SF: float  # Scale Factor, required


class DbResource:
    """Base class for a single ``/db/*`` endpoint.

    Subclasses set:
        ENDPOINT: e.g. "/db/NODE"
        NAME: human-readable name (manual "기능" column), for error messages
        PRODUCTS: {"gen"}, {"civil"}, or {"gen", "civil"}
        METHODS: subset of {"POST", "GET", "PUT", "DELETE"} the endpoint
            actually supports (defaults to all four; override for
            GET/PUT-only endpoints like MATD).
    """

    ENDPOINT: ClassVar[str]
    NAME: ClassVar[str] = ""
    PRODUCTS: ClassVar[frozenset] = frozenset({"gen", "civil"})
    METHODS: ClassVar[frozenset] = _ALL_METHODS

    @classmethod
    def _check(cls, client: MidasClient, method: str) -> None:
        client.check_product(cls.PRODUCTS, cls.NAME or cls.__name__)
        if method not in cls.METHODS:
            raise UnsupportedMethodError(
                f"{cls.NAME or cls.__name__} ({cls.ENDPOINT}) does not support {method}; "
                f"supported methods: {sorted(cls.METHODS)}",
                method=method,
                endpoint=cls.ENDPOINT,
            )

    @classmethod
    def get(cls, client: Optional[MidasClient] = None) -> dict:
        """Fetch all items. Response is nested under the endpoint's key,
        e.g. ``{"NODE": {"1": {...}, "2": {...}}}``."""
        client = client or get_default_client()
        cls._check(client, "GET")
        return client.request("GET", cls.ENDPOINT)

    @classmethod
    def create(cls, items: dict, client: Optional[MidasClient] = None) -> dict:
        """items: {id: payload_dict}, e.g. {1: {"X": 0, "Y": 0, "Z": 0}}."""
        client = client or get_default_client()
        cls._check(client, "POST")
        return client.request("POST", cls.ENDPOINT, {"Assign": {str(k): v for k, v in items.items()}})

    @classmethod
    def update(cls, items: dict, client: Optional[MidasClient] = None) -> dict:
        """items: {id: payload_dict} — same shape as create()."""
        client = client or get_default_client()
        cls._check(client, "PUT")
        return client.request("PUT", cls.ENDPOINT, {"Assign": {str(k): v for k, v in items.items()}})

    @classmethod
    def delete(cls, ids: list, client: Optional[MidasClient] = None) -> dict:
        """ids: list of item ids to delete, e.g. [1, 2, 3]."""
        client = client or get_default_client()
        cls._check(client, "DELETE")
        return client.request("DELETE", cls.ENDPOINT, {"Assign": {str(i): None for i in ids}})
