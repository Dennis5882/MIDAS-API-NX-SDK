"""Source: docs/manual/03_DB_Node_Element.md, items 1-2 (/db/NODE, /db/ELEM)."""
from __future__ import annotations

from typing import List, TypedDict

from .base import DbResource


class NodePayload(TypedDict, total=False):
    """docs/manual/03_DB_Node_Element.md #1 — /db/NODE Specifications table."""

    X: float  # Coordinates - x, default 0, optional
    Y: float  # Coordinates - y, default 0, optional
    Z: float  # Coordinates - z, default 0, optional


class Node(DbResource):
    ENDPOINT = "/db/NODE"
    NAME = "Node"
    PRODUCTS = frozenset({"gen", "civil"})


class ElementPayload(TypedDict, total=False):
    """docs/manual/03_DB_Node_Element.md #2 — /db/ELEM Specifications table.

    Only the common + Beam/Truss fields are typed here for v1. ELEM has many
    more STYPE-conditional fields (Cable/Compression-only Truss, Wall,
    Plate, Solid, ...) documented in the manual's per-subtype tables —
    pass them as extra dict keys; DbResource does not validate payloads.
    """

    TYPE: str  # Element Type, default "BEAM", optional. e.g. "BEAM","TRUSS","PLATE","WALL","SOLID"
    MATL: int  # Material No., required
    SECT: int  # Section / Thickness No., required
    NODE: List[int]  # Node No. list, required
    ANGLE: float  # Beta Angle (Beam/Truss/Plane Strain/Axisymmetric), default 0, optional
    STYPE: int  # Element Subtype (meaning depends on TYPE), optional


class Element(DbResource):
    ENDPOINT = "/db/ELEM"
    NAME = "Element"
    PRODUCTS = frozenset({"gen", "civil"})
