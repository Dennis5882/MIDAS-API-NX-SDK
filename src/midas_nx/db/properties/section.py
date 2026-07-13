"""Source: docs/manual/04_DB_Properties.md, items 12, 14-21, 29, 31.

SECT is deeply conditional on SECTTYPE ("DBUSER"/"VALUE"/"SRC"/"COMBINED"/
"PSC"/"TAPERED"/"COMPOSITE"/"SOD") — only the common envelope (SECTTYPE,
SECT_NAME, SECT_BEFORE) is typed here; SECT_I (the SECTTYPE-specific body)
is left as a plain dict, matching the manual's own per-SECTTYPE subsections
(12-A DB/User, 12-B Value, ...) which are not all ported to this v1.
"""
from __future__ import annotations

from typing import Any, List, TypedDict

from ..base import DbResource, ItemGroupFields


class SectBefore(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #12 — common "SECT_BEFORE" fields."""

    SHAPE: str  # Section Shape, required
    OFFSET_PT: str  # e.g. "CC", default "CC", optional
    OFFSET_CENTER: int  # 0=Centroid, 1=Center of Section; default 0
    HORZ_OFFSET_OPT: int  # 0=Extreme Fiber, 1=User; default 0
    USERDEF_OFFSET_YI: float  # default 0
    VERT_OFFSET_OPT: int  # default 0
    USERDEF_OFFSET_ZI: float  # default 0
    USER_OFFSET_REF: int  # 0=Centroid, 1=Extreme Fiber; default 0
    USE_SHEAR_DEFORM: bool  # default false
    USE_WARPING_EFFECT: bool  # default false
    DATATYPE: int  # 12-A DB/User only: DB=1, User=2; required for SECTTYPE="DBUSER"
    SECT_I: Any  # SECTTYPE-specific body, e.g. (DBUSER) {"DB_NAME": "KS21", "SECT_NAME": "H300x150x6.5/9"}


class SectionPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #12 — /db/SECT common Specifications table."""

    SECTTYPE: str  # "DBUSER"/"VALUE"/"SRC"/"COMBINED"/"PSC"/"TAPERED"/"COMPOSITE"/"SOD", required
    SECT_NAME: str  # Section Name, required
    SECT_BEFORE: SectBefore  # required


class Section(DbResource):
    ENDPOINT = "/db/SECT"
    NAME = "Section Properties"
    PRODUCTS = frozenset({"gen", "civil"})


class TaperedGroupPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #14 — /db/TSGR Specifications table."""

    NAME: str  # Tapered Group Name, required
    ELEMLIST: List[int]  # Element No. list, required
    ZVAR: str  # Z-axis Section Shape Variation: "LINEAR" / "POLY", required
    YVAR: str  # Y-axis Section Shape Variation: "LINEAR" / "POLY", required
    ZEXP: float  # ZVAR=POLY only: Z axis Exponent, required
    ZFROM: str  # ZVAR=POLY only: Z axis Symmetric Plane from "i" or "j", default "i", optional
    ZDIST: float  # ZVAR=POLY only: Z axis Symmetric Plane Distance (m), default 0, optional


class TaperedGroup(DbResource):
    ENDPOINT = "/db/TSGR"
    NAME = "Tapered Group"
    PRODUCTS = frozenset({"gen", "civil"})


class SectionStiffnessItem(ItemGroupFields, total=False):
    AREA_SF: float  # Area Scale Factor, default 1, optional
    ASY_SF: float  # Asy Scale Factor, default 1, optional
    ASZ_SF: float  # Asz Scale Factor, default 1, optional
    IXX_SF: float  # Ixx Scale Factor, default 1, optional
    IYY_SF: float  # Iyy Scale Factor, default 1, optional
    IZZ_SF: float  # Izz Scale Factor, default 1, optional
    WGT_SF: float  # Weight Scale Factor, default 1, optional


class SectionStiffnessPayload(TypedDict):
    """docs/manual/04_DB_Properties.md #15 — /db/SECF. Keyed by element id."""

    ITEMS: List[SectionStiffnessItem]


class SectionStiffness(DbResource):
    ENDPOINT = "/db/SECF"
    NAME = "Section Manager - Stiffness"
    PRODUCTS = frozenset({"gen", "civil"})


class SectionReinforcementShearItem(TypedDict, total=False):
    OPT_DR: bool  # Diagonal Reinforcement, default false, optional
    DR_PITCH: float  # optional
    DR_THETA: float  # optional
    DR_AW: float  # optional


class SectionReinforcementPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #16 — /db/RPSC. Keyed by section id."""

    OPT_MBAR_J: bool  # Same Rebar Data at i and j-end (Longitudinal), required
    OPT_SBAR_J: bool  # Same Shear Rebar Data at i and j-end, required
    OPT_CRACKED: bool  # Cracked Section, required
    SBAR_ITEMS: List[SectionReinforcementShearItem]  # [i-section, j-section], required


class SectionReinforcement(DbResource):
    ENDPOINT = "/db/RPSC"
    NAME = "Section Manager - Reinforcements"
    PRODUCTS = frozenset({"gen", "civil"})


class StressPoint(TypedDict, total=False):
    PY: float  # Point Y, required
    PZ: float  # Point Z, required


class SectionStressPointsPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #17 — /db/STRPSSM. Keyed by section id."""

    OPT_SAME_J: bool  # Same Stress Points at i and j-end, default true, optional
    POINT_SIZE_1: int  # Number of Stress Points (I), required
    POINT_SIZE_2: int  # Number of Stress Points (J), required
    POINT1: List[StressPoint]  # Stress Point Coordinates (I), required
    POINT2: List[StressPoint]  # Stress Point Coordinates (J), required


class SectionStressPoints(DbResource):
    ENDPOINT = "/db/STRPSSM"
    NAME = "Section Manager - Stress Points"
    PRODUCTS = frozenset({"gen", "civil"})


class PlateStiffnessScaleFactorItem(ItemGroupFields, total=False):
    AXIAL_X: float  # Axial Fxx Scale Factor, default 1, optional
    AXIAL_Y: float  # Axial Fyy Scale Factor, default 1, optional
    SHEAR: float  # Shear Fxy Scale Factor, default 1, optional
    OUT_BENDING_X: float  # Bending Mxx Scale Factor, default 1, optional
    OUT_BENDING_Y: float  # Bending Myy Scale Factor, default 1, optional
    OUT_TORSION: float  # Bending Mxy Scale Factor, default 1, optional
    OUT_SHEAR_X: float  # Shear Vxx Scale Factor, default 1, optional
    OUT_SHEAR_Y: float  # Shear Vyy Scale Factor, default 1, optional


class PlateStiffnessScaleFactorPayload(TypedDict):
    """docs/manual/04_DB_Properties.md #18 — /db/PSSF. Keyed by element id."""

    ITEMS: List[PlateStiffnessScaleFactorItem]


class PlateStiffnessScaleFactor(DbResource):
    ENDPOINT = "/db/PSSF"
    NAME = "Section Manager - Plate Stiffness Scale Factor"
    PRODUCTS = frozenset({"gen", "civil"})


class VirtualBeamPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #19 — /db/VBEM. Keyed by element id."""

    VSEC1: int  # Virtual Section 1 (/db/VSEC id), required
    VSEC2: int  # Virtual Section 2 (/db/VSEC id), required


class VirtualBeam(DbResource):
    ENDPOINT = "/db/VBEM"
    NAME = "Virtual Beam"
    PRODUCTS = frozenset({"gen", "civil"})


class VirtualSectionPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #20 — /db/VSEC Specifications table."""

    NAME: str  # required
    CENT_CALC_TYPE: int  # Centroid Calculation Type, required
    CEN_PT_X: float  # Centroid X (Global), required
    CEN_PT_Y: float  # Centroid Y (Global), required
    CEN_PT_Z: float  # Centroid Z (Global), required
    NORMAL_X: float  # Direction Normal Vector (X), required
    NORMAL_Y: float  # Direction Normal Vector (Y), required
    NORMAL_Z: float  # Direction Normal Vector (Z), required
    NODE_LIST: List[int]  # required
    ELEM_LIST: List[int]  # required


class VirtualSection(DbResource):
    ENDPOINT = "/db/VSEC"
    NAME = "Virtual Section"
    PRODUCTS = frozenset({"gen", "civil"})


class EffectiveWidthScaleFactorItem(ItemGroupFields, total=False):
    """J-End fields are only meaningful when bJ is true."""

    LYSCALE: float  # ly Scale Factor for Sbz (I-End), default 1, required
    ZTSCALE: float  # z_top Scale Factor (I-End), default 1, required
    ZBSCALE: float  # z_bot Scale Factor (I-End), default 1, required
    bJ: bool  # J-End Option, default false, required
    LYSCALE_J: float  # ly Scale Factor (J-End), default 1, optional
    ZTSCALE_J: float  # z_top Scale Factor (J-End), default 1, optional
    ZBSCALE_J: float  # z_bot Scale Factor (J-End), default 1, optional


class EffectiveWidthScaleFactorPayload(TypedDict):
    """docs/manual/04_DB_Properties.md #21 — /db/EWSF. Keyed by element id."""

    ITEMS: List[EffectiveWidthScaleFactorItem]


class EffectiveWidthScaleFactor(DbResource):
    ENDPOINT = "/db/EWSF"
    NAME = "Effective Width Scale Factor"
    PRODUCTS = frozenset({"gen", "civil"})


class ElementStiffnessScaleFactorItem(ItemGroupFields, total=False):
    AREA_SF: float  # Area (Cross-sectional area), default 1.0, optional
    ASY_SF: float  # Asy (Shear area, local y), default 1.0, optional
    ASZ_SF: float  # Asz (Shear area, local z), default 1.0, optional
    IXX_SF: float  # Ixx (Torsional resistance), default 1.0, optional
    IYY_SF: float  # Iyy (Moment of Inertia, y-axis), default 1.0, optional
    IZZ_SF: float  # Izz (Moment of Inertia, z-axis), default 1.0, optional
    WGT_SF: float  # Weight, default 1.0, optional


class ElementStiffnessScaleFactorPayload(TypedDict):
    """docs/manual/04_DB_Properties.md #31 — /db/ESSF. Keyed by element id."""

    ITEMS: List[ElementStiffnessScaleFactorItem]


class ElementStiffnessScaleFactor(DbResource):
    ENDPOINT = "/db/ESSF"
    NAME = "Element Stiffness Scale Factor"
    PRODUCTS = frozenset({"gen", "civil"})


class FiberDivisionColor(TypedDict, total=False):
    R: int  # default 0, optional
    G: int  # default 0, optional
    B: int  # default 0, optional


class FiberDivisionBaseItem(TypedDict, total=False):
    FIBR_BASE_KEY: bool  # required


class FiberDivisionPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #29 — /db/FIBR Specifications table."""

    NAME: str  # Fiber Division Name, required
    SECT_KEY: int  # Assigned Section ID (/db/SECT id), required
    ASSIGN_TYPE: int  # required
    FIMP_NAME: List[str]  # Inelastic Material Properties Name, 6 entries (/db/FIMP names), required
    FIMP_COLOR: List[FiberDivisionColor]  # 6 entries, optional
    FIBR_BASE: List[FiberDivisionBaseItem]  # Fiber Division Base Data, required


class FiberDivision(DbResource):
    ENDPOINT = "/db/FIBR"
    NAME = "Fiber Division of Section"
    PRODUCTS = frozenset({"gen", "civil"})
