"""Source: docs/manual/06_DB_Static_Loads.md, items 1-4, 10
(/db/STLD, /db/BODF, /db/CNLD, /db/BMLD, /db/PRES)."""
from __future__ import annotations

from typing import List, TypedDict

from .base import DbResource


class StaticLoadCasePayload(TypedDict, total=False):
    """docs/manual/06_DB_Static_Loads.md #1 — /db/STLD Specifications table.

    TYPE is one of ~67 documented load-type codes (e.g. "D" Dead Load,
    "L" Live Load, "W" Wind Load, "E" Earthquake, "PS" Prestress, ...) —
    see the manual's full Load Type table for the complete list.
    """

    NAME: str  # Load Case Name, required
    TYPE: str  # Load Type code, required
    DESC: str  # Description, default "", optional


class StaticLoadCase(DbResource):
    ENDPOINT = "/db/STLD"
    NAME = "Static Load Cases"
    PRODUCTS = frozenset({"gen", "civil"})


class SelfWeightPayload(TypedDict, total=False):
    """docs/manual/06_DB_Static_Loads.md #2 — /db/BODF Specifications table."""

    LCNAME: str  # Load Case Name, required
    GROUP_NAME: str  # Load Group Name, default "", optional
    FV: List[float]  # Self-Weight Factor [X, Y, Z], required, e.g. [0, 0, -1]


class SelfWeight(DbResource):
    ENDPOINT = "/db/BODF"
    NAME = "Self-Weight"
    PRODUCTS = frozenset({"gen", "civil"})


class NodalLoadItem(TypedDict, total=False):
    """One entry of the /db/CNLD "ITEMS" array."""

    ID: int  # Serial Number, default 0, optional
    LCNAME: str  # Load Case Name, required
    GROUP_NAME: str  # Load Group Name, default "", optional
    FX: float
    FY: float
    FZ: float
    MX: float
    MY: float
    MZ: float


class NodalLoadPayload(TypedDict):
    """docs/manual/06_DB_Static_Loads.md #3 — /db/CNLD. Keyed by node id."""

    ITEMS: List[NodalLoadItem]


class NodalLoad(DbResource):
    ENDPOINT = "/db/CNLD"
    NAME = "Nodal Loads"
    PRODUCTS = frozenset({"gen", "civil"})


class BeamLoadItem(TypedDict, total=False):
    """One entry of the /db/BMLD "ITEMS" array.

    D/P are 4-value distance/load arrays; see docs/manual/06_DB_Static_Loads.md
    #4 for the eccentricity-related fields (ECCEN_*, *_END, ADDITIONAL_*),
    not all of which are typed here for v1.
    """

    ID: int  # Serial Number, default 0, optional
    LCNAME: str  # Load Case Name, required
    GROUP_NAME: str  # Load Group Name, default "", optional
    CMD: str  # "BEAM" / "LINE" / "TYPICAL", required
    TYPE: str  # "CONLOAD"/"CONMOMENT"/"UNILOAD"/"UNIMOMENT"/"PRESSURE", required
    DIRECTION: str  # "LX"/"LY"/"LZ"/"GX"/"GY"/"GZ", required
    USE_PROJECTION: bool  # default false, optional
    D: List[float]  # Distance [x1,x2,x3,x4], default 0, optional
    P: List[float]  # Load [v1,v2,v3,v4], default 0, optional
    USE_ECCEN: bool  # default false, optional


class BeamLoadPayload(TypedDict):
    """docs/manual/06_DB_Static_Loads.md #4 — /db/BMLD. Keyed by element id."""

    ITEMS: List[BeamLoadItem]


class BeamLoad(DbResource):
    ENDPOINT = "/db/BMLD"
    NAME = "Beam Loads"
    PRODUCTS = frozenset({"gen", "civil"})


class PressureLoadItem(TypedDict, total=False):
    """One entry of the /db/PRES "ITEMS" array.

    FORCES is required when FACE_EDGE_TYPE is "FACE"/"PRES"; EDGE_LOADS is
    required when FACE_EDGE_TYPE is "EDGE" — the two are mutually exclusive
    per docs/manual/06_DB_Static_Loads.md #10, not enforced at runtime here.
    """

    ID: int  # Serial Number, default 0, optional
    LCNAME: str  # Load Case Name, required
    GROUP_NAME: str  # Load Group Name, default "", optional
    CMD: str  # default "PRES", optional
    ELEM_TYPE: str  # "PLATE"/"SOLID"/"PLANE", default "PLATE", optional
    FACE_EDGE_TYPE: str  # "FACE"/"EDGE"/"PRES", required
    DIRECTION: str  # "NORMAL"/"LX"/"LY"/"LZ"/"GX"/"GY"/"GZ"/"VECTOR", default "NORMAL"
    VECTORS: List[float]  # [X,Y,Z], required if DIRECTION="VECTOR"
    OPT_PROJECTION: bool  # default false, optional (GX/GY/GZ only)
    EDGE_FACE: int  # Solid: 1-6, Plate/Plane: 1-4, required
    FORCES: List[float]  # required if FACE_EDGE_TYPE is FACE/PRES
    EDGE_LOADS: List[float]  # required if FACE_EDGE_TYPE is EDGE


class PressureLoadPayload(TypedDict):
    """docs/manual/06_DB_Static_Loads.md #10 — /db/PRES. Keyed by element id."""

    ITEMS: List[PressureLoadItem]


class PressureLoad(DbResource):
    ENDPOINT = "/db/PRES"
    NAME = "Assign Pressure Loads"
    PRODUCTS = frozenset({"gen", "civil"})
