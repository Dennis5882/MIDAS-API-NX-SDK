"""Source: docs/manual/13_DB_Load_Combinations.md, items 1-8."""
from __future__ import annotations

from typing import List, TypedDict

from .base import DbResource


class LoadCombinationItem(TypedDict, total=False):
    """Shared "vCOMB" entry shape used by all six LCOM-* endpoints."""

    ANAL: str  # Analysis Type: "ST"/"CS"/"MV"/"SM"/"RS"/"TH"/"CB", required
    LCNAME: str  # Load Case Name, required
    FACTOR: float  # required


class LoadCombinationPayload(TypedDict, total=False):
    """Shared shape for /db/LCOM-GEN, LCOM-STEEL, LCOM-SRC, LCOM-STLCOMP,
    LCOM-SEISMIC — all five share this schema; only LCOM-CONC adds "bES"
    (see LoadCombinationConcretePayload). ACTIVE's valid values and
    whether iTYPE=2 (ABS) is supported vary per endpoint — see each
    DbResource subclass's docstring.
    """

    NO: int  # Combination Number, read-only
    NAME: str  # Combination Name, required
    ACTIVE: str  # Active Type (valid values vary per endpoint), default "ACTIVE", optional
    iTYPE: int  # Sum. Method: Add=0/Envelope=1/ABS=2/SRSS=3, default 0, optional
    DESC: str  # Description, default "", optional
    bCB: bool  # (Read-only) min/max cb type: false=General/true=Min/Max/All
    vCOMB: List[LoadCombinationItem]  # Combination List, required


class LoadCombinationConcretePayload(LoadCombinationPayload):
    """docs/manual/13_DB_Load_Combinations.md #2 — /db/LCOM-CONC Specifications table.

    ACTIVE: "INACTIVE"/"STRENGTH"/"SERVICE".
    """

    bES: bool  # Concrete design only option (E), default false, optional


class LoadCombinationGeneral(DbResource):
    """#1 — ACTIVE: "INACTIVE"/"ACTIVE". Supports iTYPE=2 (ABS)."""

    ENDPOINT = "/db/LCOM-GEN"
    NAME = "Load Combinations - General"


class LoadCombinationConcrete(DbResource):
    """#2 — ACTIVE: "INACTIVE"/"STRENGTH"/"SERVICE". Supports iTYPE=2 (ABS). Civil NX only."""

    ENDPOINT = "/db/LCOM-CONC"
    NAME = "Load Combinations - Concrete Design"
    PRODUCTS = frozenset({"civil"})


class LoadCombinationSteel(DbResource):
    """#3 — ACTIVE: "INACTIVE"/"STRENGTH"/"SERVICE". iTYPE=2 (ABS) not supported."""

    ENDPOINT = "/db/LCOM-STEEL"
    NAME = "Load Combinations - Steel Design"


class LoadCombinationSRC(DbResource):
    """#4 — ACTIVE: "INACTIVE"/"STRENGTH"/"SERVICE". iTYPE=2 (ABS) not supported."""

    ENDPOINT = "/db/LCOM-SRC"
    NAME = "Load Combinations - SRC Design"


class LoadCombinationCompositeSteelGirder(DbResource):
    """#5 — ACTIVE: "INACTIVE"/"STRENGTH"/"SERVICE". iTYPE=2 (ABS) not supported. Civil NX only (bridge design)."""

    ENDPOINT = "/db/LCOM-STLCOMP"
    NAME = "Load Combinations - Composite Steel Girder Design"
    PRODUCTS = frozenset({"civil"})


class LoadCombinationSeismic(DbResource):
    """#6 — ACTIVE: "INACTIVE"/"ACTIVE". iTYPE=2 (ABS) not supported."""

    ENDPOINT = "/db/LCOM-SEISMIC"
    NAME = "Load Combinations - Seismic Design"


# --- 7. /db/CUTL — Cutting Line ---------------------------------------------


class CuttingLinePayload(TypedDict, total=False):
    """docs/manual/13_DB_Load_Combinations.md #7 — /db/CUTL Specifications table."""

    NAME: str  # required
    DIR: str  # Direction: "NORMAL" (normal)/"DIR" (in-plane), required
    PT1X: float  # required
    PT1Y: float  # required
    PT1Z: float  # required
    PT2X: float  # required
    PT2Y: float  # required
    PT2Z: float  # required
    R: int  # Line color R (0-255), default 0, optional
    G: int  # Line color G (0-255), default 0, optional
    B: int  # Line color B (0-255), default 0, optional
    TYPE: int  # default 0, optional


class CuttingLine(DbResource):
    ENDPOINT = "/db/CUTL"
    NAME = "Cutting Line"


# --- 8. /db/CLWP — Plate Cutting Line Diagram -------------------------------


class PlateCuttingLineDiagramPayload(TypedDict, total=False):
    """docs/manual/13_DB_Load_Combinations.md #8 — /db/CLWP Specifications table.

    Unlike CUTL (2 points, 1D elements), CLWP defines a plane via 3 points
    for plate elements and has no "TYPE" field.
    """

    NAME: str  # required
    DIR: str  # Direction: "NORMAL"/"DIR"/"PLANE", required
    PT1X: float  # required
    PT1Y: float  # required
    PT1Z: float  # required
    PT2X: float  # required
    PT2Y: float  # required
    PT2Z: float  # required
    PT3X: float  # required
    PT3Y: float  # required
    PT3Z: float  # required
    R: int  # Line color R (0-255), default 0, optional
    G: int  # Line color G (0-255), default 0, optional
    B: int  # Line color B (0-255), default 0, optional


class PlateCuttingLineDiagram(DbResource):
    ENDPOINT = "/db/CLWP"
    NAME = "Plate Cutting Line Diagram"
