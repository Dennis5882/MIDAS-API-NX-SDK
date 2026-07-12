"""Source: docs/manual/05_DB_Boundary.md, item 1 (/db/CONS)."""
from __future__ import annotations

from typing import List, TypedDict

from .base import DbResource


class ConstraintItem(TypedDict, total=False):
    """One entry of the /db/CONS "ITEMS" array."""

    ID: int  # Serial Number, default 0, optional
    GROUP_NAME: str  # Boundary Group Name, default "", optional
    CONSTRAINT: str  # [DX,DY,DZ,RX,RY,RZ,RW] 7-char string, "1"=fixed "0"=free, required


class ConstraintPayload(TypedDict):
    """docs/manual/05_DB_Boundary.md #1 — /db/CONS Specifications table.

    Keyed by node id, e.g. {"1": {"ITEMS": [{"ID": 1, "CONSTRAINT": "1111111"}]}}.
    """

    ITEMS: List[ConstraintItem]


class Constraint(DbResource):
    ENDPOINT = "/db/CONS"
    NAME = "Constraint Support"
    PRODUCTS = frozenset({"gen", "civil"})
