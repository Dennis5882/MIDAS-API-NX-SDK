"""Source: docs/manual/04_DB_Properties.md, items 1, 3, 5-10, 28, 32.

MATL-M1 (Hyper-S material) and IMFM-M1 (Hyper-S auto-generation link) are
itemized by URL in INDEX.md but documented as thin stubs with no
Specifications table in the chapter file, so left unimplemented.
"""
from __future__ import annotations

from typing import Any, List, TypedDict

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


class InelasticFiberMaterialLinkPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #3 — /db/IMFM Specifications table.

    Concrete entries use CONC_NAME/CONFINED_CONC_NAME/REBAR_NAME; Steel
    entries use STEEL_NAME — pass only the fields relevant to the material.
    """

    CONC_NAME: str  # Inelastic Material of Concrete (/db/FIMP name), default "", optional
    CONFINED_CONC_NAME: str  # Confined Concrete for Columns (/db/FIMP name), default "", optional
    REBAR_NAME: str  # Inelastic Material of Rebar (/db/FIMP name), default "", optional
    STEEL_NAME: str  # Inelastic Material of Steel (/db/FIMP name), default "", optional


class InelasticFiberMaterialLink(DbResource):
    ENDPOINT = "/db/IMFM"
    NAME = "Inelastic Material Properties for Fiber Model"
    PRODUCTS = frozenset({"gen", "civil"})


class TimeDependentMaterialFunctionValue(TypedDict, total=False):
    DAY: float  # Time, required
    VALUE: float  # required


class TimeDependentMaterialFunctionPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #5 — /db/TDMF Specifications table."""

    NAME: str  # Material Function Name, required
    FTYPE: str  # "CREEP" / "SHRINK" / "RELAX", required
    SCALE: float  # Scale Factor, required
    DESC: str  # default "", optional
    vDAY: List[TimeDependentMaterialFunctionValue]  # required
    CTYPE: str  # FTYPE=CREEP only: "SC"=Specific Creep, "CF"=Creep Function, "CC"=Creep Coefficient; required
    RELAXATION: int  # FTYPE=RELAX only: Hour=0, Day=1; required


class TimeDependentMaterialFunction(DbResource):
    ENDPOINT = "/db/TDMF"
    NAME = "Time Dependent Material - User Defined"
    PRODUCTS = frozenset({"gen", "civil"})


class TimeDependentMaterialCreepShrinkagePayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #6 — /db/TDMT Specifications table.

    Fields 5-8 are conditional on CODE (CEB-FIP uses MSIZE/TYPEOFAFFR, ACI
    uses VOL/CMETHOD); pass only the ones matching the selected code.
    """

    NAME: str  # Time Dependent Material Name, required
    CODE: str  # Code Name, required
    STR: float  # Compression Strength, required
    HU: float  # Relative Humidity, required
    MSIZE: float  # CEB-FIP: Notional Size of Member, required
    CTYPE: str  # Type of Cement, default "RS", optional
    AGE: float  # Concrete Age, required
    TYPEOFAFFR: int  # CEB-FIP 2010: Aggregate type 0=Basalt/dense limestone, 1=Quartzite, 2=Limestone, 3=Sandstone; default 0
    VOL: float  # ACI: Volume/Surface Ratio, required
    CMETHOD: str  # ACI: "MOIST" / "STEAM", default "MOIST", optional


class TimeDependentMaterialCreepShrinkage(DbResource):
    ENDPOINT = "/db/TDMT"
    NAME = "Time Dependent Material - Creep/Shrinkage"
    PRODUCTS = frozenset({"gen", "civil"})


class TimeDependentMaterialStrengthPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #7 — /db/TDME Specifications table."""

    NAME: str  # Material Name, required
    TYPE: str  # "CODE" / "USER", required
    CODENAME: str  # TYPE=CODE, required
    STRENGTH: float  # TYPE=CODE, required
    A: float  # TYPE=USER (ACI/KDS): Factor a, required
    B: float  # TYPE=USER (ACI/KDS): Factor b, required
    iCTYPE: int  # TYPE=USER (CEB-FIP 1990/Ohzagi): Cement Type, required


class TimeDependentMaterialStrength(DbResource):
    ENDPOINT = "/db/TDME"
    NAME = "Time Dependent Material - Compressive Strength"
    PRODUCTS = frozenset({"gen", "civil"})


class ChangePropertyPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #8 — /db/EDMP Specifications table."""

    TYPE: str  # "NSM"=Notional Size, "VSR"=Volume/Surface Ratio; required
    H_VS: float  # h for NSM, v/s for VSR, required


class ChangeProperty(DbResource):
    ENDPOINT = "/db/EDMP"
    NAME = "Change Property"
    PRODUCTS = frozenset({"gen", "civil"})


class TimeDependentMaterialLinkPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #9 — /db/TMAT Specifications table."""

    TDMT_NAME: str  # Creep/Shrinkage Name (/db/TDMT name), required
    TDME_NAME: str  # Comp. Strength Name (/db/TDME name), required


class TimeDependentMaterialLink(DbResource):
    ENDPOINT = "/db/TMAT"
    NAME = "Time Dependent Material Link"
    PRODUCTS = frozenset({"gen", "civil"})


class PlasticMaterialPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #10 — /db/EPMT Specifications table.

    Deeply conditional on MODEL_TYPE ("TR"/"VM"=Tresca/Von-Mises common
    params under TRESCA/VMISES, "MC"=Mohr-Coulomb under MOHRCL, "DP"/"MA"/
    "DM" undocumented in the chapter) — only common Tresca/Von-Mises and
    Mohr-Coulomb sub-objects are typed for v1.
    """

    NAME: str  # Plastic Material Name, required
    MODEL_TYPE: str  # "TR"/"VM"/"MC"/"DP"/"MA"/"DM", required
    TRESCA: Any  # MODEL_TYPE=TR: {"INIT_YIELD_STRESS", "OPT_HARDENING", "HARDENING_TYPE", "HARDENING_COEF", "BACK_STRESS_COEF"}
    VMISES: Any  # MODEL_TYPE=VM: same shape as TRESCA
    MOHRCL: Any  # MODEL_TYPE=MC: {"INIT_COHESION", "INIT_FRIC_ANGLE", "OPT_HARDENING"}


class PlasticMaterial(DbResource):
    ENDPOINT = "/db/EPMT"
    NAME = "Plastic Material"
    PRODUCTS = frozenset({"gen", "civil"})


class InelasticMaterialKentParkParam(TypedDict, total=False):
    FC: float  # Concrete Strength (fc'), required
    EC0: float  # Peak Strain, required
    K: float  # Strength/Strain Factor, required
    ECU: float  # Ultimate Strain, required
    PARTIAL_FACT: float  # Partial Safety Factor, required


class InelasticMaterialPropertyPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #28 — /db/FIMP Specifications table.

    Deeply conditional on (MATL_TYPE, HYS_MODEL) — only the Concrete
    Kent & Park model ("CONC"/"KPM") is typed for v1; other hysteresis
    models (documented per footnote 1 in the manual) go under the same
    CONC/STEEL keys with a different HYS_MODEL-specific sub-object.
    """

    NAME: str  # Material Name, required
    MATL_TYPE: str  # "CONC" / "STEEL", required
    HYS_MODEL: str  # e.g. "KPM" (Kent & Park), required
    CONC: Any  # MATL_TYPE=CONC, e.g. {"KENPAR": {...InelasticMaterialKentParkParam}}
    STEEL: Any  # MATL_TYPE=STEEL, model-specific body


class InelasticMaterialProperty(DbResource):
    ENDPOINT = "/db/FIMP"
    NAME = "Inelastic Material Properties"
    PRODUCTS = frozenset({"gen", "civil"})
