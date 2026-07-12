"""Source: docs/manual/04_DB_Properties.md, items 1 and 32 (/db/MATL, /db/MATD)."""
from __future__ import annotations

from typing import List, TypedDict

from ..base import DbResource


class MaterialParam(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #1 — one entry of MATL's "PARAM" array.

    Shape depends on P_TYPE: 1=Standard/DB (STANDARD/CODE/DB/bELAST),
    2=Isotropic/User (ELAST/POISN/THERMAL/DEN/MASS), 3=Orthotropic/User
    (ELAST_M/POISN_M/THERMAL_M/SHEAR_M/DEN/MASS) — all three variants'
    fields are optional here since only one variant applies per P_TYPE.
    """

    P_TYPE: int  # 1=Standard/DB, 2=Isotropic/User, 3=Orthotropic/User; required
    # P_TYPE = 1
    STANDARD: str
    CODE: str
    DB: str
    bELAST: bool
    # P_TYPE = 2
    ELAST: float
    POISN: float
    THERMAL: float
    DEN: float
    MASS: float
    # P_TYPE = 3
    ELAST_M: List[float]
    POISN_M: List[float]
    THERMAL_M: List[float]
    SHEAR_M: List[float]


class MaterialPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #1 — /db/MATL Specifications table."""

    TYPE: str  # "CONC"/"STEEL"/"SRC"/"ALUMINUM"/"USER", required
    NAME: str  # Material Name, required
    HE_SPEC: float  # Specific Heat, default 0, optional
    HE_COND: float  # Heat Conduction, default 0, optional
    PLMT: int  # Plastic Material No., default 0, optional
    P_NAME: str  # Plastic Material Name, default "", optional
    bMASS_DENS: bool  # Use Mass Density, default false, optional
    DAMP_RAT: float  # Damping Ratio, default 0, optional
    PARAM: List[MaterialParam]  # required


class Material(DbResource):
    ENDPOINT = "/db/MATL"
    NAME = "Material Properties"
    PRODUCTS = frozenset({"gen", "civil"})


class MaterialModifyConcreteDesign(TypedDict, total=False):
    C_FC: float  # Strength — GET only (computed), see manual
    C_FCI: float  # Strength (initial) — GET only (computed), see manual


class MaterialModifyConcreteData1(TypedDict, total=False):
    CODENAME: str  # Material Code Name, required
    CODEMATLNAME: str  # Material Grade, required
    DESIGN: MaterialModifyConcreteDesign  # required


class MaterialModifyConcretePayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #32 — /db/MATD Specifications table.

    GET/PUT only — used to modify design values/rebar grade of an existing
    TYPE="CONC" material created via Material (/db/MATL).
    """

    TYPE: str  # "CONC", required
    NAME: str  # Material Name (matches an existing MATL entry), required
    DATA1: MaterialModifyConcreteData1  # required
    REBAR_CODENAME: str  # required
    MAINREBAR_REBARNAME: str  # required
    SUBREBAR_REBARNAME: str  # default "", optional
    MAINREBAR_B_FY: float  # GET only (computed), default 0
    SUBREBAR_B_FY: float  # GET only (computed), default 0


class MaterialModifyConcrete(DbResource):
    ENDPOINT = "/db/MATD"
    NAME = "Modify Concrete Materials"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = frozenset({"GET", "PUT"})
