"""Source: docs/manual/05_DB_Boundary.md, items 1-24."""
from __future__ import annotations

from typing import Any, List, TypedDict

from .base import DbResource, ItemGroupFields, NO_DELETE_METHODS


class ConstraintItem(ItemGroupFields, total=False):
    """One entry of the /db/CONS "ITEMS" array."""

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


class PointSpringItem(ItemGroupFields, total=False):
    """One entry of the /db/NSPR "ITEMS" array.

    LINEAR uses SDR/F_S/DAMPING; COMP/TENS/MULTI use DIR/DV/SK instead.
    """

    TYPE: str  # "LINEAR" / "COMP" / "TENS" / "MULTI", required
    FormType: int  # 0=Point spring function, 1=Surface spring function; default 0
    # LINEAR only
    SDR: List[float]  # Spring Stiffness [SDx,SDy,SDz,SRx,SRy,SRz], required
    F_S: List[bool]  # Fixed Option [SDx,SDy,SDz,SRx,SRy,SRz], default false
    DAMPING: bool  # Damping Constant, optional
    # COMP / TENS / MULTI only
    DIR: int  # 1=Dx, 2=Dy, 3=Dz, 4=Dy&Dz; required
    DV: List[float]  # Displacement Values [Disp_1, Disp_2, Disp_3], required
    SK: List[float]  # Spring Stiffness Values [K_1, K_2, K_3], required


class PointSpringPayload(TypedDict):
    """docs/manual/05_DB_Boundary.md #2 — /db/NSPR. Keyed by node id."""

    ITEMS: List[PointSpringItem]


class PointSpring(DbResource):
    ENDPOINT = "/db/NSPR"
    NAME = "Point Spring"
    PRODUCTS = frozenset({"gen", "civil"})


class GeneralSpringTypePayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #3 — /db/GSTP Specifications table.

    SPRING/MASS/DAMPING are 21-value upper-triangular matrices, each valid
    only when its matching OPT_* flag is true.
    """

    NAME: str  # General Spring Name, required
    OPT_STIFFNESS: bool  # default false, optional
    SPRING: List[float]  # Stiffness Matrix (21 values), default 0
    OPT_MASS: bool  # default false, optional
    MASS: List[float]  # Mass Matrix (21 values), default 0
    OPT_DAMPING: bool  # default false, optional
    DAMPING: List[float]  # Damping Matrix (21 values), default 0


class GeneralSpringType(DbResource):
    ENDPOINT = "/db/GSTP"
    NAME = "Define General Spring Type"
    PRODUCTS = frozenset({"gen", "civil"})


class GeneralSpringSupportItem(ItemGroupFields, total=False):
    TYPE_NAME: str  # Defined General Spring Name (from /db/GSTP), required


class GeneralSpringSupportPayload(TypedDict):
    """docs/manual/05_DB_Boundary.md #4 — /db/GSPR. Keyed by node id."""

    ITEMS: List[GeneralSpringSupportItem]


class GeneralSpringSupport(DbResource):
    ENDPOINT = "/db/GSPR"
    NAME = "Assign General Spring Supports"
    PRODUCTS = frozenset({"gen", "civil"})


class SurfaceSpringItem(ItemGroupFields, total=False):
    ELEM_TYPE: str  # "FRAME" / "PLANAR(FACE)" / "PLANAR(EDGE)" / "SOLID", required
    EDGE_FACE: int  # FRAME: Local x=2/y=0/z=1; PLANAR/SOLID: Edge#1-4=0-3; default 0
    WIDTH: float  # FRAME only: tributary width, optional (undocumented in table, seen in example)
    SPRING_TYPE: int  # 0=Linear, 1=Comp.-Only, 2=Tens.-Only; default 0
    MODULUS: float  # Modulus of Subgrade Reaction Ks, required


class SurfaceSpringPayload(TypedDict):
    """docs/manual/05_DB_Boundary.md #5 — /db/SSPS. Keyed by element id."""

    ITEMS: List[SurfaceSpringItem]


class SurfaceSpring(DbResource):
    ENDPOINT = "/db/SSPS"
    NAME = "Surface Spring"
    PRODUCTS = frozenset({"gen", "civil"})


class ElasticLinkPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #6 — /db/ELNK Specifications table.

    Extra keys depend on LINK: "GEN" (SDR/R_S/bSHEAR/DR), "RIGID"/"SADDLE"
    (none), "TENS"/"COMP" (SDR, Dx only), "MULTILINEAR" (DIR/MLFC/bSHEAR/
    DRENDI), "RAILINTERACT" (DIR/RLFC/bSHEAR/DRENDI).
    """

    NODE: List[int]  # [i-node, j-node], required
    BNGR_NAME: str  # Boundary Group Name, default "", optional
    ANGLE: float  # Beta Angle, default 0, optional
    LINK: str  # "GEN"/"RIGID"/"SADDLE"/"TENS"/"COMP"/"MULTILINEAR"/"RAILINTERACT", required
    SDR: List[float]  # LINK=GEN/TENS/COMP: Spring Stiffness [SDx,SDy,SDz,SRx,SRy,SRz]
    R_S: List[bool]  # LINK=GEN: Rigid-End Option, default false
    bSHEAR: bool  # LINK=GEN/MULTILINEAR/RAILINTERACT: Consider Shear, optional
    DR: List[float]  # LINK=GEN: [SDy Effective Length ratio, SDz Effective Length ratio]
    DIR: int  # LINK=MULTILINEAR/RAILINTERACT: local direction, required
    MLFC: int  # LINK=MULTILINEAR: Force-Deformation Function id (/db/MLFC), required
    RLFC: int  # LINK=RAILINTERACT: Rail function id, required
    DRENDI: float  # LINK=MULTILINEAR/RAILINTERACT: end-i distance ratio, optional


class ElasticLink(DbResource):
    ENDPOINT = "/db/ELNK"
    NAME = "Elastic Link"
    PRODUCTS = frozenset({"gen", "civil"})


class RigidLinkItem(ItemGroupFields, total=False):
    """ID here is the Master Node id (unlike the generic Serial Number
    elsewhere), but the field shape is the same as ItemGroupFields."""

    DOF: int  # 6-digit DOF flag, digit positions DX(6th)..RZ(1st), e.g. 110001; required
    S_NODE: List[int]  # Slave Node id list, required


class RigidLinkPayload(TypedDict):
    """docs/manual/05_DB_Boundary.md #7 — /db/RIGD. Keyed by master node id."""

    ITEMS: List[RigidLinkItem]


class RigidLink(DbResource):
    ENDPOINT = "/db/RIGD"
    NAME = "Rigid Link"
    PRODUCTS = frozenset({"gen", "civil"})


class GeneralLinkPropertyPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #8 — /db/NLLP Specifications table.

    Deeply conditional on (APPLICATION_TYPE, APPLICATION_TYPE_D) — e.g.
    "ELEMENT"/"SPG" (spring), "ELEMENT2"/"VI" (references /db/SDVI by name),
    "FORCE"/"LRBI" (lead rubber bearing isolator), etc.; only the common
    envelope is typed for v1, matching the SECT_I precedent. See the
    manual's APPLICATION_TYPE Combination Table for the full list of
    (APPLICATION_TYPE, APPLICATION_TYPE_D) pairs and their extra keys.
    """

    PROPERTY_NAME: str  # required
    DESC: str  # optional
    APPLICATION_TYPE: str  # "ELEMENT"/"ELEMENT2"/"FORCE", required
    APPLICATION_TYPE_D: str  # e.g. "SPG"/"DSP"/"SLD"/"VI"/"VE"/"ST"/"HY"/"IS"/"VD"/"GAP"/"HOOK"/"HS"/"LRBI"/"FPSI"/"TFPSI", required
    TOTAL_WEIGHT: float  # Self-Weight (Total), optional
    L_WEIGHT_RATIO: float  # Lumped Weight Ratio, optional
    OPT_USE_MASS: bool  # optional
    TOTAL_MASS: float  # optional
    L_MASS_RATIO: float  # Lumped Mass Ratio, optional
    OPT_SHEAR_SPR_LOC: bool  # Shear Spring Location Option, optional


class GeneralLinkProperty(DbResource):
    ENDPOINT = "/db/NLLP"
    NAME = "General Link Properties"
    PRODUCTS = frozenset({"gen", "civil"})


class GeneralLinkPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #9 — /db/NLNK Specifications table.

    REF_SYSTEM=0 (element CS) uses BETA_ANGLE; REF_SYSTEM=1 (global CS)
    uses INPUT_METHOD (0=Angle -> ANGLE_VALUES, 1=3 Points -> POINT_VALUES,
    2=Vector -> VECTOR_VALUES).
    """

    NODE1: int  # required
    NODE2: int  # required
    GROUP_NAME: str  # Boundary Group Name, default "", optional
    PROP_NAME: str  # General Link Property Name (/db/NLLP name), required
    IEHP_NAME: str  # Inelastic Hinge Property Name, default "", optional
    REF_SYSTEM: int  # 0=Element, 1=Global; required
    BETA_ANGLE: float  # REF_SYSTEM=0, default 0, optional
    INPUT_METHOD: int  # REF_SYSTEM=1: 0=Angle, 1=3 Points, 2=Vector; required
    ANGLE_VALUES: Any  # INPUT_METHOD=0: [{"VALUE": [about X, about y', about z'']}]
    POINT_VALUES: Any  # INPUT_METHOD=1: [P0[3], P1[3], P2[3]]
    VECTOR_VALUES: Any  # INPUT_METHOD=2: [V1[3], V2[3]]


class GeneralLink(DbResource):
    ENDPOINT = "/db/NLNK"
    NAME = "General Link"
    PRODUCTS = frozenset({"gen", "civil"})


class GeneralLinkHyperSPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #10 — /db/NLNK-M1 (Hyper-S solver only).

    Manual notes no official JSON schema example is published; parameter
    shape follows /db/NLNK per the vendored chapter's own description.
    """

    PROP_NAME: str  # General Link Property Name (/db/NLLP name), required
    NODE1: int  # required
    NODE2: int  # required


class GeneralLinkHyperS(DbResource):
    ENDPOINT = "/db/NLNK-M1"
    NAME = "General Link (Hyper-S)"
    PRODUCTS = frozenset({"gen", "civil"})


class ChangeGeneralLinkPropertyPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #11 — /db/CGLP Specifications table."""

    GLINK_KEY: int  # General Link element id, required
    CHANGE_PROPERTY_NAME: str  # Property name defined in /db/NLLP, required
    GROUP_NAME: str  # Boundary Group Name, default "", optional


class ChangeGeneralLinkProperty(DbResource):
    ENDPOINT = "/db/CGLP"
    NAME = "Change General Link Property"
    PRODUCTS = frozenset({"gen", "civil"})


class BeamEndReleaseItem(ItemGroupFields, total=False):
    bVALUE: bool  # false=Relative, true=Value; default false
    FLAG_I: str  # 7-char release flags [Fx,Fy,Fz,Mx,My,Mz,Mb] for i-node, required
    VALUE_I: List[float]  # Partial Fixity for i-node, default 0
    FLAG_J: str  # 7-char release flags [Fx,Fy,Fz,Mx,My,Mz,Mb] for j-node, required
    VALUE_J: List[float]  # Partial Fixity for j-node, default 0


class BeamEndReleasePayload(TypedDict):
    """docs/manual/05_DB_Boundary.md #12 — /db/FRLS. Keyed by element id."""

    ITEMS: List[BeamEndReleaseItem]


class BeamEndRelease(DbResource):
    ENDPOINT = "/db/FRLS"
    NAME = "Beam End Release"
    PRODUCTS = frozenset({"gen", "civil"})


class BeamEndOffsetItem(ItemGroupFields, total=False):
    """TYPE="GLOBAL" uses RGDXi/RGDYi/RGDZi/RGDXj/RGDYj/RGDZj (GCS);
    TYPE="ELEMENT" reuses RGDYi/RGDZi/RGDYj/RGDZj but in ECS (no X component).
    """

    TYPE: str  # "GLOBAL" / "ELEMENT", required
    RGDXi: float  # TYPE=GLOBAL only, default 0, optional
    RGDYi: float  # default 0, optional
    RGDZi: float  # default 0, optional
    RGDXj: float  # TYPE=GLOBAL only, default 0, optional
    RGDYj: float  # default 0, optional
    RGDZj: float  # default 0, optional


class BeamEndOffsetPayload(TypedDict):
    """docs/manual/05_DB_Boundary.md #13 — /db/OFFS. Keyed by element id."""

    ITEMS: List[BeamEndOffsetItem]


class BeamEndOffset(DbResource):
    ENDPOINT = "/db/OFFS"
    NAME = "Beam End Offsets"
    PRODUCTS = frozenset({"gen", "civil"})


class PlateEndReleaseItem(ItemGroupFields, total=False):
    N1: List[int]  # Position N1 [Fx,Fy,Fz,Mx,My], 1=released, required
    N2: List[int]  # Position N2 [Fx,Fy,Fz,Mx,My], required
    N3: List[int]  # Position N3 [Fx,Fy,Fz,Mx,My], required
    N4: List[int]  # Position N4 [Fx,Fy,Fz,Mx,My], required


class PlateEndReleasePayload(TypedDict):
    """docs/manual/05_DB_Boundary.md #14 — /db/PRLS. Keyed by element id."""

    ITEMS: List[PlateEndReleaseItem]


class PlateEndRelease(DbResource):
    ENDPOINT = "/db/PRLS"
    NAME = "Plate End Release"
    PRODUCTS = frozenset({"gen", "civil"})


class ForceDeformationFunctionItem(TypedDict, total=False):
    X: float  # Displacement (m) or Rotation (rad), required
    Y: float  # Force (kN) or Moment (kN.m), required


class ForceDeformationFunctionPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #15 — /db/MLFC Specifications table."""

    NAME: str  # Function Name, required
    TYPE: str  # "FORCE" / "MOMENT", default "MOMENT", optional
    SYMM: bool  # Symmetric, default false, optional
    FUNC_ID: int  # default 0, optional
    ITEMS: List[ForceDeformationFunctionItem]  # required


class ForceDeformationFunction(DbResource):
    ENDPOINT = "/db/MLFC"
    NAME = "Force-Deformation Function"
    PRODUCTS = frozenset({"gen", "civil"})


class SeismicDeviceCommon(TypedDict, total=False):
    """Shared "COMMON" sub-object of the SDVI/SDVE/SDST/SDHY/SDIS seismic
    device endpoints."""

    NAME: str  # required
    DESC: str  # optional
    INPUT_METHOD: int  # 0=User Input, 1=Reference DB; required
    COMPANY: str  # required
    PRODUCT_NAME: str  # required
    TYPE_NUMBER: str  # required


class SeismicDeviceViscousDamperItem(TypedDict, total=False):
    OPT_DOF: bool  # DOF enabled, required
    CE: float  # Initial Damping Coefficient, required
    P1: float  # Max Damping Force, required
    C1: float  # Secondary Damping Coefficient, required
    ALPHA1: float  # Damping Exponent, required
    K0: float  # Initial Stiffness, required


class SeismicDeviceViscousDamperPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #16 — /db/SDVI Specifications table."""

    COMMON: SeismicDeviceCommon  # required
    DEVICE_TYPE: str  # optional
    DAMPER_TYPE: int  # 0=Single Dashpot, 1=Kelvin(Voigt), 2=Maxwell; required
    DASHPOT_TYPE: int  # 0=Linear Elastic, 1=Bilinear, 2=Exponential; required
    INPUT_TYPE: int  # 0=Damping ratio alpha1, 1=Damping constant C1; required
    ITEM: List[SeismicDeviceViscousDamperItem]  # 6 entries, one per DOF; required


class SeismicDeviceViscousDamper(DbResource):
    ENDPOINT = "/db/SDVI"
    NAME = "Seismic Device - Viscous/Oil Damper"
    PRODUCTS = frozenset({"gen", "civil"})


class SeismicDeviceViscoelasticDamperPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #17 — /db/SDVE Specifications table."""

    COMMON: SeismicDeviceCommon  # required
    MATERIAL_TYPE: str  # "GR100"/"GR300"/"SR05"/"GR400"/"CST"/"TRC", required
    SHEAR_AREA: float  # required


class SeismicDeviceViscoelasticDamper(DbResource):
    ENDPOINT = "/db/SDVE"
    NAME = "Seismic Device - Viscoelastic Damper"
    PRODUCTS = frozenset({"gen", "civil"})


class SeismicDeviceSteelDamperPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #18 — /db/SDST Specifications table."""

    COMMON: SeismicDeviceCommon  # required
    DIR: str  # Direction, e.g. "Dx", required
    SDST_HYS_MODEL: str  # Hysteresis Model, e.g. "BL2", required


class SeismicDeviceSteelDamper(DbResource):
    ENDPOINT = "/db/SDST"
    NAME = "Seismic Device - Steel Damper"
    PRODUCTS = frozenset({"gen", "civil"})


class SeismicDeviceHystereticIsolatorPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #19 — /db/SDHY Specifications table."""

    COMMON: SeismicDeviceCommon  # required
    SDHY_HYS_MODEL: str  # e.g. "DegradingBiLinear", required
    MSS: int  # Number of Shear Springs, required
    K0: float  # Initial Stiffness, required


class SeismicDeviceHystereticIsolator(DbResource):
    ENDPOINT = "/db/SDHY"
    NAME = "Seismic Device - Hysteretic Isolator (MSS)"
    PRODUCTS = frozenset({"gen", "civil"})


class SeismicDeviceIsolatorPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #20 — /db/SDIS Specifications table.

    Exactly one of LRB/NRB/SB is present, matching SDIS_DEV_TYPE
    ("LRB"/"NRB"/"SB") — left as Any for v1, matching SECT_I precedent.
    """

    COMMON: SeismicDeviceCommon  # required
    SDIS_DEV_TYPE: str  # "LRB" / "NRB" / "SB", required
    MSS: int  # Number of Shear Springs, required
    TAU_K: float  # Adjustment Parameter tau_k, required
    TAU_Q: float  # Adjustment Parameter tau_q, required
    KV: float  # Vertical Stiffness, required
    LRB: Any  # SDIS_DEV_TYPE="LRB": {"SDIS_HYS_MODEL","AR","TR","KE","K2","QD",...}
    NRB: Any  # SDIS_DEV_TYPE="NRB": {"KH": ...}
    SB: Any  # SDIS_DEV_TYPE="SB": {"AS","K0","MU0"}


class SeismicDeviceIsolator(DbResource):
    ENDPOINT = "/db/SDIS"
    NAME = "Seismic Device - Isolator (MSS)"
    PRODUCTS = frozenset({"gen", "civil"})


class LinearConstraintSlave(TypedDict, total=False):
    NODE_KEY: int  # required
    COEFF: float  # required


class LinearConstraintItem(ItemGroupFields, total=False):
    SLAVE_TYPE: str  # 6-char DOF flag (DX..RZ) of the constrained node, required
    TYPE: str  # "EX"=Explicit, "WD"=Weighted Displacement; required
    SLAVES: List[LinearConstraintSlave]  # Independent Nodes, required


class LinearConstraintPayload(TypedDict):
    """docs/manual/05_DB_Boundary.md #21 — /db/MCON. Keyed by (slave) node id."""

    ITEMS: List[LinearConstraintItem]


class LinearConstraint(DbResource):
    ENDPOINT = "/db/MCON"
    NAME = "Linear Constraints"
    PRODUCTS = frozenset({"gen", "civil"})


class PanelZoneEffectPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #22 — /db/PZEF Specifications table."""

    OPT_OFFSET: bool  # Auto Calculate Panel Zone Offset Distances, required
    OFFS_FACTOR: float  # Offset Factor, required
    OUTPUT_POSITION: int  # required


class PanelZoneEffect(DbResource):
    ENDPOINT = "/db/PZEF"
    NAME = "Panel Zone Effects"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = NO_DELETE_METHODS


class ConstraintLabelDirectionPayload(TypedDict, total=False):
    """docs/manual/05_DB_Boundary.md #23 — /db/CLDR. Keyed by node id.

    DIR: Local x(+)=0, Local x(-)=1, Local y(+)=2, Local y(-)=3,
    Local z(+)=4, Local z(-)=5.
    """

    DIR: int  # required


class ConstraintLabelDirection(DbResource):
    ENDPOINT = "/db/CLDR"
    NAME = "Define Constraints Label Direction"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = NO_DELETE_METHODS


class DiaphragmDisconnect(DbResource):
    """docs/manual/05_DB_Boundary.md #24 — /db/DRLS.

    Excludes nodes from an active diaphragm constraint; payload is an empty
    object per node id, e.g. ``DiaphragmDisconnect.create({1: {}, 2: {}})``.
    """

    ENDPOINT = "/db/DRLS"
    NAME = "Diaphragm Disconnect"
    PRODUCTS = frozenset({"gen", "civil"})
