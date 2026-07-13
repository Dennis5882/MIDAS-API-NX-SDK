"""``/ope/*`` — GUI/preprocessing operations not persisted to the DB.

Source: docs/manual/15_OPE.md, items 1-19. Request bodies are wrapped in an
``"Argument"`` key like doc.py (not ID-keyed ``"Assign"``), but most of these
endpoints have deeply-nested, highly-optional bodies (10+ levels in places),
so each POST function takes one TypedDict ``argument`` parameter instead of
doc.py's style of exploding fields into many kwargs. GET-only endpoints
(PROJECTSTATUS, SECTPROP) take no argument at all.
"""
from __future__ import annotations

from typing import List, Optional, TypedDict, Union

from .client import MidasClient, get_default_client


def _post(command: str, argument, client: Optional[MidasClient] = None) -> dict:
    return (client or get_default_client()).request("POST", command, {"Argument": argument})


# --- 1. /ope/PROJECTSTATUS — Project Status ---------------------------------


def get_project_status(client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #1 — /ope/PROJECTSTATUS — Project Status.

    GET-only, no request body; returns live counts of model/load data.
    """
    return (client or get_default_client()).request("GET", "/ope/PROJECTSTATUS")


# --- 2. /ope/DIVIDEELEM — Divide Elements ------------------------------------


class NumberOption(TypedDict, total=False):
    """Shared {NUMBER_OPTION, USER_NUM} shape for DIVIDEELEM's
    START_NUMBER.NODE_NUMBER / START_NUMBER.ELEM_NUMBER."""

    NUMBER_OPTION: str  # "Smallest"/"Largest"/"User", optional
    USER_NUM: int  # user-specified number, required if NUMBER_OPTION="User"


class DivideStartNumber(TypedDict, total=False):
    NODE_NUMBER: NumberOption  # optional
    ELEM_NUMBER: NumberOption  # optional


class DivideEqualOption(TypedDict, total=False):
    """DIV_METHOD="Equal": which axes are required depends on ELEM_TYPE
    (Frame=X only, Planar=X+Y, Wall=X+Z, Solid=X+Y+Z)."""

    NUM_X: int  # division count in X, required
    NUM_Y: int  # division count in Y, required for Planar/Solid
    NUM_Z: int  # division count in Z, required for Wall/Solid


class DivideUnequalOption(TypedDict, total=False):
    """DIV_METHOD="Unequal": distance strings, e.g. "3@2.0" (3 segments of 2.0)."""

    DIST_X: str  # required
    DIST_Y: str  # required
    DIST_Z: str  # required


class DivideParametricOption(TypedDict, total=False):
    """DIV_METHOD="ParametricUnequal": ratio strings, e.g. "3@0.3"."""

    RATIO_X: str  # required
    RATIO_Y: str  # required
    RATIO_Z: str  # required


class DivideParallelOption(TypedDict, total=False):
    """DIV_METHOD="ParallelBracing"."""

    NUM_OF_DIVISIONS: int  # required
    MAIN_POST_ELEM: List[int]  # reference post/column elements, required


class DivideByNodeOption(TypedDict, total=False):
    """DIV_METHOD="DividebyNode"."""

    ELEM_NUM: int  # target element, required
    NODE_NUM: int  # split reference node, required


class DivideOption(TypedDict, total=False):
    """Only the sub-object matching DIVIDE.DIV_METHOD is used."""

    EQUAL_OPTION: DivideEqualOption  # required if DIV_METHOD="Equal"
    UNEQUAL_OPTION: DivideUnequalOption  # required if DIV_METHOD="Unequal"
    PARAMETRIC_OPTION: DivideParametricOption  # required if DIV_METHOD="ParametricUnequal"
    PARALLEL_OPTION: DivideParallelOption  # required if DIV_METHOD="ParallelBracing"
    BY_NODE_OPTION: DivideByNodeOption  # required if DIV_METHOD="DividebyNode"


class MergeDuplicateNodesOption(TypedDict, total=False):
    OPT_CHECK: bool  # optional
    TOLERANCE: float  # merge tolerance, optional


class DivideSettings(TypedDict, total=False):
    ELEM_TYPE: str  # "Frame"/"Wall"/"Planar"/"Solid", required
    DIV_METHOD: str  # "Equal"/"Unequal"/"ParametricUnequal"/"ParallelBracing"/"DividebyNode", required
    OPTION: DivideOption  # required
    SUBDIVIDE_ELEM: bool  # re-subdivide line elements, optional
    MERGE_DUPLICATE_NODES: MergeDuplicateNodesOption  # optional


class DivideElementsArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #2 — /ope/DIVIDEELEM — Divide Elements.

    DIVIDE.DIV_METHOD selects which single sub-object of DIVIDE.OPTION
    (EQUAL_OPTION/UNEQUAL_OPTION/PARAMETRIC_OPTION/PARALLEL_OPTION/
    BY_NODE_OPTION) is required (mirrors the MaterialParam precedent in
    properties/material.py).
    """

    TARGETS: List[int]  # elements to divide, optional
    START_NUMBER: DivideStartNumber  # starting node/element numbering, optional
    DIVIDE: DivideSettings  # required


def divide_elements(argument: DivideElementsArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #2 — /ope/DIVIDEELEM — Divide Elements."""
    return _post("/ope/DIVIDEELEM", argument, client)


# --- 3. /ope/SECTPROP — Section Properties Calculation Results --------------


def get_section_properties(client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #3 — /ope/SECTPROP — Section Properties Calculation Results.

    GET-only, no request body; response is keyed by section ID.
    """
    return (client or get_default_client()).request("GET", "/ope/SECTPROP")


# --- 4. /ope/USLC — Using Load Combinations ----------------------------------


class LoadCombinationRef(TypedDict, total=False):
    TYPE: str  # "GEN"/"STEEL"/"CONC"/"SRC"/"STLCOMP"/"SEISMIC", required
    NAME: str  # load combination name, required


class UsingLoadTypes(TypedDict, total=False):
    """Which load categories to include when generating design combinations
    from the LCOM_LIST entries; each defaults to true if omitted."""

    SELF_WEIGHT: bool  # default true, optional
    NODAL_BODY_FROCE: bool  # [sic, matches manual's "FROCE" spelling] Nodal Body Force, default true, optional
    NODAL_LOAD: bool  # default true, optional
    SPECIFIED_DISPLACEMENT: bool  # default true, optional
    BEAM_LOAD: bool  # default true, optional
    FLOOR_LOAD: bool  # default true, optional
    FINISHING_MATERIAL_LOAD: bool  # default true, optional
    PRESSURE_LOAD: bool  # default true, optional
    PLANE_LOAD: bool  # default true, optional
    SYSTEM_TEMPERATURE: bool  # default true, optional
    NODAL_TEMPERATURE: bool  # default true, optional
    ELEMENT_TEMPERATURE: bool  # default true, optional
    TEMPERATURE_GRADIENT: bool  # default true, optional
    BEAM_SECTION_TEMPERATURE: bool  # default true, optional
    PRESTRESS_LOAD: bool  # default true, optional
    PRETENSION_LOAD: bool  # default true, optional
    TENDON_PRESTRESS_LOAD: bool  # default true, optional


class UsingLoadCombinationsArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #4 — /ope/USLC — Using Load Combinations."""

    PREFIX: str  # load case/design combination name prefix, default System, optional
    POSITION: str  # design target: "STEEL"/"CONC"/"SRC", required
    LCOM_LIST: List[LoadCombinationRef]  # selected combinations, required
    LOADS: UsingLoadTypes  # load categories to include, optional


def use_load_combinations(argument: UsingLoadCombinationsArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #4 — /ope/USLC — Using Load Combinations."""
    return _post("/ope/USLC", argument, client)


# --- 5. /ope/LINEBMLD — Line Beam Load ---------------------------------------


class LineLoadTarget(TypedDict, total=False):
    METHOD: int  # on load line=0 / selected elements=1, required
    ELEM: List[int]  # target elements, required if METHOD=1
    NODE: List[int]  # 2 nodes defining the load line, required if METHOD=0


class LineLoadEccentricity(TypedDict, total=False):
    """Only usable when TYPE is CONLOAD/UNILOAD/TRALOAD/CURVED."""

    USE: bool  # default false
    TYPE: int  # centroid=0 / offset=1
    DIR: str  # "LY"/"LZ"/"GX"/"GY"/"GZ"
    I_END: float  # I-end eccentricity
    J_END: float  # J-end eccentricity, required if USE_J_END true
    USE_J_END: bool


class LineLoadAdditionalHeight(TypedDict, total=False):
    """Only usable when TYPE is UNIPRESSURE/TRAPRESSURE."""

    USE: bool  # default false
    I_END: float  # I-end value
    J_END: float  # J-end value, required if USE_J_END true
    USE_J_END: bool


class LineLoadValue(TypedDict, total=False):
    DIR: str  # local/global direction; UNIPRESSURE/TRAPRESSURE limited to LY/LZ per ADD_H, required
    USE_PROJECTION: bool  # default depends on TARGET.METHOD (0->false, 1->true), optional
    TYPE: int  # relative=0/absolute=1, required except for TYPE="CURVED"
    D: List[float]  # distances [x1,x2,x3,x4], required except for TYPE="CURVED"
    P: List[float]  # magnitudes [P1,P2,P3,P4], required except for TYPE="CURVED"
    A: float  # curve coefficient a, required only for TYPE="CURVED"
    B: float  # curve coefficient b, required only for TYPE="CURVED"
    C: float  # curve coefficient c, required only for TYPE="CURVED"


class LineLoadCopy(TypedDict, total=False):
    USE: bool  # default false
    AXIS: str  # "X"/"Y"/"Z"
    DIST: str  # e.g. "10@3.0"


class LineBeamLoadArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #5 — /ope/LINEBMLD — Line Beam Load."""

    LCNAME: str  # load case name, required
    GROUP_NAME: str  # load group name, optional
    TYPE: str  # "CONLOAD"/"CONMOMENT"/"UNILOAD"/"UNIMOMENT"/"TRALOAD"/"TRAMOMENT"/"UNIPRESSURE"/"TRAPRESSURE"/"CURVED", required
    TARGET: LineLoadTarget  # required
    ECCEN: LineLoadEccentricity  # eccentricity option, optional (CONLOAD/UNILOAD/TRALOAD/CURVED only)
    ADD_H: LineLoadAdditionalHeight  # additional top height option, optional (UNIPRESSURE/TRAPRESSURE only)
    LOAD: LineLoadValue  # required
    COPY: LineLoadCopy  # copy option, optional


def create_line_beam_load(argument: LineBeamLoadArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #5 — /ope/LINEBMLD — Line Beam Load."""
    return _post("/ope/LINEBMLD", argument, client)


# --- 6. /ope/AUTOMESH — Auto-Mesh Planar Area --------------------------------


class InteriorInclusionOption(TypedDict, total=False):
    """Shared shape for MESHER.INCLUDE_INTERIOR_NODES / INCLUDE_INTERIOR_LINES."""

    OPT_CHECK: bool  # default true, optional
    OPTION: str  # "Auto"/"User", default "Auto", optional
    VALUE: List[int]  # included node/line IDs, required if OPTION="User"


class AutoMesher(TypedDict, total=False):
    METHOD: str  # "Nodes"/"Line Elements"/"Planar Elements", default "Line Elements", optional
    TARGETS: List[int]  # nodes/elements bounding the mesh area, required
    TYPE: str  # "Quadrilateral"/"Quad and Triangle"/"Triangle", default "Quadrilateral", optional
    MESH_INNER_DOMAIN: bool  # default false, optional
    INCLUDE_INTERIOR_NODES: InteriorInclusionOption  # optional
    INCLUDE_INTERIOR_LINES: InteriorInclusionOption  # optional
    INCLUDE_BOUNDARY_CONNECTIVITY: bool  # default true, optional


class AutoMeshSize(TypedDict, total=False):
    """LENGTH and DIV are mutually exclusive; exactly one is required."""

    LENGTH: float  # target element edge length, required unless DIV given
    DIV: int  # target division count, required unless LENGTH given


class AutoMeshElementSubType(TypedDict, total=False):
    TYPE: str  # "Thick"/"Thin", used when PROPERTY.ELEMENT_TYPE="Plate", default "Thick", optional
    WITH_DRILLING_DOF: bool  # used when ELEMENT_TYPE is "Plate"/"Plane Stress", default true, optional


class AutoMeshProperty(TypedDict, total=False):
    ELEMENT_TYPE: str  # "Plate"/"Plane Stress"/"Plane Strain"/"Axisymmetric", default "Plate", optional
    ELEMENT_SUB_TYPE: AutoMeshElementSubType  # optional
    MATERIAL: int  # material ID, required
    THICKNESS: int  # thickness ID, optional (Plate/Plane Stress only)


class AutoMeshDomainName(TypedDict, total=False):
    NAME: str  # mesh domain/group name, required


class AutoMeshAdditionalOption(TypedDict, total=False):
    DELETE_LINE_ELEM: bool  # delete original line/boundary elements, default false, optional
    SUBDIVIDE_LINE_ELEM: bool  # re-subdivide original line/boundary elements, default true, optional


class AutoMeshArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #6 — /ope/AUTOMESH — Auto-Mesh Planar Area."""

    MESHER: AutoMesher  # required
    MESH_SIZE: AutoMeshSize  # required
    PROPERTY: AutoMeshProperty  # required
    DOMAIN_NAME: AutoMeshDomainName  # required
    ADDITIONAL_OPTION: AutoMeshAdditionalOption  # optional


def auto_mesh(argument: AutoMeshArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #6 — /ope/AUTOMESH — Auto-Mesh Planar Area."""
    return _post("/ope/AUTOMESH", argument, client)


# --- 7. /ope/SSPS — Surface Spring -------------------------------------------


class SurfaceSpringTargetKeys(TypedDict, total=False):
    KEYS: List[int]  # target node/element numbers, required


class SurfaceSpringElement(TypedDict, total=False):
    TYPE: str  # "FRAME"/"PLANAR"/"SOLID_FACE"/"SOLID_NODE", required
    FACE: int  # face number 1-6, required if TYPE="SOLID_FACE"
    WIDTH: float  # required if TYPE="FRAME"


class SurfaceSpringBoundary(TypedDict, total=False):
    """Required-ness of each field depends on the CONVERT_TO x TYPE combo —
    see the manual's Parameters table note (mirrors MaterialParam precedent)."""

    TYPE: str  # "LINEAR"/"COMP"/"TENS"/"MULTI", required
    STIFF: List[float]  # [Kx,Ky,Kz], required for LINEAR/MULTI
    bDAMP: bool  # consider damping, required for LINEAR/MULTI
    DAMP: List[float]  # [Cx,Cy,Cz], required for LINEAR/MULTI
    DIR: int  # boundary direction 0-7 (Normal+/-, UCS-x/y/z +/-), required for COMP/TENS and most other cases
    SUBGRADE: float  # subgrade reaction modulus, required for COMP/TENS and all ELASTIC_LINK types
    PHU: float  # ultimate strength, required for MULTI (point spring and elastic link)
    LENGTH: float  # elastic link length, required when CONVERT_TO="ELASTIC_LINK"


class SurfaceSpringArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #7 — /ope/SSPS — Surface Spring."""

    CONVERT_TO: str  # "POINT_SPRING"/"ELASTIC_LINK", required
    GROUP_NAME: str  # boundary group name, default "", optional
    NODE_ELEMS: SurfaceSpringTargetKeys  # required
    ELEMENT: SurfaceSpringElement  # required
    BOUNDARY: SurfaceSpringBoundary  # required


def convert_surface_spring(argument: SurfaceSpringArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #7 — /ope/SSPS — Surface Spring."""
    return _post("/ope/SSPS", argument, client)


# --- 8. /ope/EDMP — Change Property ------------------------------------------


class ChangePropertyTargetKeys(TypedDict, total=False):
    KEYS: List[int]  # target node/element numbers, e.g. [101, 102, 103], required


class ChangePropertyArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #8 — /ope/EDMP — Change Property.

    Used to set the Notional Size of Member / Volume Surface Ratio needed for
    creep & shrinkage calculations.
    """

    NODE_ELEMS: ChangePropertyTargetKeys  # required
    TYPE: str  # "NSM" (notional size)/"VSR" (volume surface ratio), default "NSM", optional
    AUTO: bool  # auto-calculate; VSR only allows false, default false, optional
    CODE: str  # "Korean Standard"/"CEB-FIP(1990)"/"Japanese Standard"/"Chinese Standard"; used when AUTO=true and TYPE="NSM", default "Korean Standard", optional
    PARAMETER: float  # parameter value (a), required if AUTO=false
    H_VS: float  # change value: NSM->h / VSR->v/s, required


def change_property(argument: ChangePropertyArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #8 — /ope/EDMP — Change Property."""
    return _post("/ope/EDMP", argument, client)


# --- 9. /ope/STOR — Story Calculation ----------------------------------------


class SeismicAccidentalEccentricity(TypedDict, total=False):
    INC_SEIS_ECC: bool  # include seismic accidental eccentricity, required
    SEIS_ECC_VALUE: float  # eccentricity value (%), required


class WindAccidentalEccentricity(TypedDict, total=False):
    INC_WIND_ECC: bool  # include wind eccentricity, required
    WIND_ECC_VALUE: float  # eccentricity value (%), required


class StoryCalculationArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #9 — /ope/STOR — Story Calculation."""

    SEIS_ECC: SeismicAccidentalEccentricity  # required
    WIND_ECC: WindAccidentalEccentricity  # required


def calculate_story(argument: StoryCalculationArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #9 — /ope/STOR — Story Calculation."""
    return _post("/ope/STOR", argument, client)


# --- 10. /ope/STORY_PARAM — Story Check Parameter ----------------------------


class StoryCheckParameterArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #10 — /ope/STORY_PARAM — Story Check Parameter."""

    COUNTRY_CODE: str  # "NTC2012"/"NTC2008"/"KBC2009"/"NSR-10"/"NTC2018"/"NTCS2020"/"IS1893(2016)"/"IS16700(2023)", required


def get_story_check_parameter(client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #10 — /ope/STORY_PARAM — Story Check Parameter (GET)."""
    return (client or get_default_client()).request("GET", "/ope/STORY_PARAM")


def set_story_check_parameter(argument: StoryCheckParameterArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #10 — /ope/STORY_PARAM — Story Check Parameter (POST)."""
    return _post("/ope/STORY_PARAM", argument, client)


# --- 11. /ope/STORY_IRR_PARAM — Story Irregularity Check Parameter ----------


class StoryIrregularityCheckParameterArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #11 — /ope/STORY_IRR_PARAM — Story Irregularity Check Parameter.

    Doc inconsistency: the Parameters table renders STORY_DRIFT_METHOD /
    STORY_STIFFNESS_METHOD / SEISMIC_BEHAVIOR_FACTOR values with spaces (e.g.
    "Max. Drift of Outer Extreme Points", "1 / Story Drift Ratio",
    "3 or below"), but the worked POST-request/response JSON examples send
    the space-stripped form (e.g. "Max.DriftofOuterExtremePoints",
    "1/StoryDriftRatio", "3orbelow"). We follow the worked examples as the
    more concrete source (same precedent as EigenvalueRitzLoadCaseItem in
    db/analysis_control.py). The table's first STORY_DRIFT_METHOD option,
    "Drift at the Center of Mass", never appears in a worked example, so its
    space-stripped form ("DriftattheCenterofMass") below is an inference by
    the same pattern, not independently confirmed.
    """

    COUNTRY_CODE: str  # "NTC2018"/"NTC2012"/"NTC2008"/"KBC2009"/"NSR-10"/"NTCS2020"/"NTCS2023"/"NSCP2015"/"IS1893(2016)"/"IS16700(2023)", required
    STORY_DRIFT_METHOD: str  # "DriftattheCenterofMass"/"Max.DriftofOuterExtremePoints"/"Max.DriftofAllVerticalElements", required
    STORY_STIFFNESS_METHOD: str  # "1/StoryDriftRatio"/"StoryShear/StoryDrift", required
    SEISMIC_BEHAVIOR_FACTOR: str  # "4"/"3orbelow", required if COUNTRY_CODE in {"NTCS2023", "NTCS2020"}


def get_story_irregularity_check_parameter(client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #11 — /ope/STORY_IRR_PARAM — Story Irregularity Check Parameter (GET)."""
    return (client or get_default_client()).request("GET", "/ope/STORY_IRR_PARAM")


def set_story_irregularity_check_parameter(
    argument: StoryIrregularityCheckParameterArgument, client: Optional[MidasClient] = None
) -> dict:
    """docs/manual/15_OPE.md #11 — /ope/STORY_IRR_PARAM — Story Irregularity Check Parameter (POST)."""
    return _post("/ope/STORY_IRR_PARAM", argument, client)


# --- 12. /ope/STORPROP — Story Properties ------------------------------------


class StoryPropertiesArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #12 — /ope/STORPROP — Story Properties.

    Doc inconsistencies: the Parameters table types FORMAT as an enum of
    "Fixed"/"Scientific", but the worked request example sends "Default"
    (not in that enum) — likely an undocumented third option. The table also
    types PLACE as String, but the worked example sends an integer (4); we
    follow the worked example (int) for PLACE.
    """

    FORCE_UNIT: str  # "N"/"KN"/"KGF"/"TONF"/"LBF"/"KIPS", default System, optional
    LENGTH_UNIT: str  # "M"/"CM"/"MM"/"FT"/"IN", default System, optional
    FORMAT: str  # doc table: "Fixed"/"Scientific"; worked example sends "Default" — see docstring, default System, optional
    PLACE: int  # decimal places 0-15; doc table says String but example sends an int, default System, optional


def get_story_properties(argument: StoryPropertiesArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #12 — /ope/STORPROP — Story Properties.

    POST-only but functions as a query (unit/format-controlled report of
    per-story weight, elevation, loaded height/width).
    """
    return _post("/ope/STORPROP", argument, client)


# --- 13. /ope/MEMB — Member Assignment ---------------------------------------


class MemberAssignmentArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #13 — /ope/MEMB — Member Assignment."""

    ASSIGN_TYPE: str  # "MANUAL"/"AUTO", required
    SELECTION_TYPE: str  # "ALL"/"SELECTION", required
    ELEM_LIST: List[int]  # target elements; ignored if SELECTION_TYPE="ALL", required if "SELECTION"
    ALLOW_SINGLE: bool  # allow single-element members, required


def assign_members(argument: MemberAssignmentArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #13 — /ope/MEMB — Member Assignment."""
    return _post("/ope/MEMB", argument, client)


# --- 14. /ope/GUSTFACTOR — Gust Factor Calculator ----------------------------


class TopographicEffect(TypedDict, total=False):
    OPT_USE: bool  # default false, optional (omitted = not used)
    KZT: float  # topographic factor Kzt, required if OPT_USE true


class RigidGustFactorParam(TypedDict, total=False):
    EXP_CATEGORY: str  # exposure category, required
    ROOF_HEIGHT: float  # >=0, required
    BREADTH_X: float  # plan breadth in global X, >=0, required
    BREADTH_Y: float  # plan breadth in global Y, >=0, required


class FlexibleGustFactorParam(TypedDict, total=False):
    EXP_CATEGORY: str  # exposure category, required
    BASIC_WIND_SPEED: float  # >=0, required
    IMPORTANCE_FACTOR: float  # >=0, required
    TOPOGRAPHIC_EFFECT: TopographicEffect  # optional, treated as OPT_USE=false if omitted
    DIRECTION_FACTOR_X: float  # >=0, required
    DIRECTION_FACTOR_Y: float  # >=0, required
    BREADTH_X: float  # plan breadth in global X, >=0, required
    BREADTH_Y: float  # plan breadth in global Y, >=0, required
    STORY_HEIGHT_MAX: float  # max story/roof height, >=0, required
    FREQUENCY_X: float  # fundamental frequency X, >=0, required
    FREQUENCY_Y: float  # fundamental frequency Y, >=0, required
    DAMPING: float  # damping ratio, e.g. 0.03, >=0, required
    TOTAL_MASS: float  # >=0, required
    MX: float  # mass term X, >=0, required
    MY: float  # mass term Y, >=0, required
    VIBRATION: float  # vibration-related factor/flag, >=0, required


class GustFactorArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #14 — /ope/GUSTFACTOR — Gust Factor Calculator.

    STRUCTURE_TYPE selects which of RIGID_PARAM/FLEXIBLE_PARAM is required
    (mirrors the MaterialParam precedent in properties/material.py). Response
    is returned under a distinct "OPE_GUSTFACTOR_RESPONSE" key (not "GUSTFACTOR").
    """

    WIND_CODE: str  # "KDS(41-12:2022)", required
    STRUCTURE_TYPE: str  # "RIGID"/"FLEXIBLE", required
    RIGID_PARAM: RigidGustFactorParam  # required if STRUCTURE_TYPE="RIGID"
    FLEXIBLE_PARAM: FlexibleGustFactorParam  # required if STRUCTURE_TYPE="FLEXIBLE"


def calculate_gust_factor(argument: GustFactorArgument, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/15_OPE.md #14 — /ope/GUSTFACTOR — Gust Factor Calculator."""
    return _post("/ope/GUSTFACTOR", argument, client)


# --- Shared LCOM-* nested shapes (items 15-18) -------------------------------
# /ope/LCOM-GEN, LCOM-CONC, LCOM-STEEL and LCOM-SRC share almost all of their
# request-body structure (only DGNCODE/CS_ANALYSIS/PRESTRESS_LOSS/the
# WIND_LOAD_COMB & UNDERGROUND_LOAD required-ness differ) — factored here
# instead of repeating per endpoint.


class LoadCombScaleFactorItem(TypedDict, total=False):
    """Shared {LOAD_CASE, FACTOR} pair used by RS_SCALE_FACTOR,
    ADDITIONAL_LOAD.SPECIAL_LOAD.OVER_STRENGTH_FACTOR,
    UNDERGROUND_LOAD.SCALE_FACTOR and UNDERGROUND_LOAD.SPECIAL_LOAD.OVER_STRENGTH_FACTOR."""

    LOAD_CASE: str  # load case name (static: "NAME(ST)", response spectrum: "NAME(RS)"), required
    FACTOR: float  # scale factor, required


class WindLoadCase(TypedDict, total=False):
    ALONG: str  # along-wind load case, optional
    ACROSS: str  # across-wind load case, optional
    TORSION: str  # torsional-wind load case, optional


class WindLoadCombParameter(TypedDict, total=False):
    BUILDING_TYPE: str  # "MIDDLE"/"HIGH", required
    WIND_LOAD_CASE: WindLoadCase  # required
    GUST_FACTOR: float  # GD, >=0, optional
    KAPPA_FACTOR: float  # kappa, >=0, optional


class WindLoadComb(TypedDict, total=False):
    PARAMETERS: List[WindLoadCombParameter]  # required
    TORSION_DIR: str  # "BOTH"/"POSITIVE"/"NEGATIVE", default "BOTH", optional


class OrthoEffect(TypedDict, total=False):
    OPT_USE: bool  # consider orthogonal effect, default false, required
    TYPE: str  # "100_30"/"SRSS", required if OPT_USE true
    LOAD_GROUP: List[str]  # [Load Case1, Load Case2], length 2, required if OPT_USE true


class SpecialSeismicLoad(TypedDict, total=False):
    OPT_USE: bool  # required
    VERTICAL_LOAD_FACTOR: float  # >=0, required if OPT_USE true
    SDS: float  # >=0, required if OPT_USE true
    OVER_STRENGTH_FACTOR: List[LoadCombScaleFactorItem]  # required if OPT_USE true


class VerticalSeismicLoad(TypedDict, total=False):
    OPT_USE: bool  # required
    FORCE_FACTOR: float  # >=0, required if OPT_USE true


class AdditionalLoad(TypedDict, total=False):
    SPECIAL_LOAD: SpecialSeismicLoad  # required
    VERTICAL_LOAD: VerticalSeismicLoad  # required


class UndergroundLoadCaseItem(TypedDict, total=False):
    LOAD_CASE: str  # seismic load case name, required
    DIRECTION: str  # "POSITIVE"/"NEGATIVE", required
    LOAD_CASE_SEISMIC: List[str]  # earth-pressure load cases (seismic component), required
    LOAD_CASE_STATIC: List[str]  # earth-pressure load cases (static component), required


class UndergroundSpecialLoad(TypedDict, total=False):
    """Distinct from the top-level ADDITIONAL_LOAD.SPECIAL_LOAD — this one
    lives inside UNDERGROUND_LOAD and applies special-seismic-load handling
    to underground load generation specifically."""

    OPT_USE: bool  # required
    VERTICAL_LOAD_FACTOR: float  # >=0, required if OPT_USE true
    SDS: float  # >=0, required if OPT_USE true
    OVER_STRENGTH_FACTOR: List[LoadCombScaleFactorItem]  # required if OPT_USE true


class UndergroundLoad(TypedDict, total=False):
    OPT_USE: bool  # required
    SCALE_FACTOR: List[LoadCombScaleFactorItem]  # required if OPT_USE true
    LOAD_CASE_LIST: List[UndergroundLoadCaseItem]  # required if OPT_USE true
    SPECIAL_LOAD: UndergroundSpecialLoad  # optional


# --- 15. /ope/LCOM-GEN — Load Combination (General) – KDS:2022 / AIK-SRC2K --


class LoadCombinationGeneralKdsArgument(TypedDict, total=False):
    """KDS:2022 variant of /ope/LCOM-GEN. CODE_SELECTION selects the design
    body (CONCRETE/STEEL/SRC); fields are flattened onto one payload with
    comments noting which body each applies to (mirrors the MaterialParam
    precedent in properties/material.py)."""

    OPTION: str  # "ADD"/"REPLACE", required
    CODE_SELECTION: str  # "CONCRETE"/"STEEL"/"SRC" — selects the DGNCODE const/required-field set below, required
    DGNCODE: str  # const per CODE_SELECTION: "KDS 41 20 : 2022"(CONCRETE) / "KDS 41 30 : 2022"(STEEL) / "KDS 41 SRC : 2022"(SRC), required
    ADD_ENVELOPE: bool  # default true, optional (CONCRETE/STEEL bodies only; absent from SRC body)
    RS_SCALE_FACTOR: List[LoadCombScaleFactorItem]  # required (all bodies)
    WIND_LOAD_COMB: WindLoadComb  # required for SRC body; optional for CONCRETE/STEEL
    ORTHO_EFFECT: OrthoEffect  # required (all bodies)
    ADDITIONAL_LOAD: AdditionalLoad  # required (all bodies)
    UNDERGROUND_LOAD: UndergroundLoad  # required for SRC body; optional for CONCRETE/STEEL
    CS_ANALYSIS: bool  # reflect construction-stage analysis results, required (CONCRETE body only)
    PRESTRESS_LOSS: bool  # reflect prestress loss, required (CONCRETE body only)


class LoadCombinationAikSrc2kArgument(TypedDict, total=False):
    """AIK-SRC2K simplified schema shared by /ope/LCOM-GEN and /ope/LCOM-SRC
    when DGNCODE="AIK-SRC2K" (manual's "LCOM-GEN/SRC AIK-SRC2K 변형 스키마"
    section) — a completely different, much smaller shape than the KDS:2022
    variants above/below, selected purely by the DGNCODE value."""

    OPTION: str  # "ADD"/"REPLACE", required
    DGNCODE: str  # "AIK-SRC2K", required
    RS_SCALE_FACTOR: List[LoadCombScaleFactorItem]  # required for LCOM-GEN, optional for LCOM-SRC


def generate_load_combination_general(
    argument: Union[LoadCombinationGeneralKdsArgument, LoadCombinationAikSrc2kArgument],
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/15_OPE.md #15 — /ope/LCOM-GEN — Load Combination (General) – KDS:2022 / AIK-SRC2K.

    DGNCODE selects the schema: KDS:2022 (LoadCombinationGeneralKdsArgument,
    CODE_SELECTION-flattened) vs AIK-SRC2K (LoadCombinationAikSrc2kArgument).
    """
    return _post("/ope/LCOM-GEN", argument, client)


# --- 16. /ope/LCOM-CONC — Load Combination (Concrete) – KDS 41 20:2022 ------


class LoadCombinationConcreteArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #16 — /ope/LCOM-CONC — Load Combination (Concrete) – KDS 41 20:2022."""

    OPTION: str  # "ADD"/"REPLACE", required
    DGNCODE: str  # "KDS 41 20 : 2022", required
    RS_SCALE_FACTOR: List[LoadCombScaleFactorItem]  # optional
    WIND_LOAD_COMB: WindLoadComb  # optional
    ORTHO_EFFECT: OrthoEffect  # optional
    ADDITIONAL_LOAD: AdditionalLoad  # optional
    UNDERGROUND_LOAD: UndergroundLoad  # optional
    CS_ANALYSIS: bool  # reflect construction-stage analysis results, default false, optional
    PRESTRESS_LOSS: bool  # reflect prestress loss, default false, optional


def generate_load_combination_concrete(
    argument: LoadCombinationConcreteArgument, client: Optional[MidasClient] = None
) -> dict:
    """docs/manual/15_OPE.md #16 — /ope/LCOM-CONC — Load Combination (Concrete) – KDS 41 20:2022."""
    return _post("/ope/LCOM-CONC", argument, client)


# --- 17. /ope/LCOM-STEEL — Load Combination (Steel) – KDS 41 30:2022 -------


class LoadCombinationSteelArgument(TypedDict, total=False):
    """docs/manual/15_OPE.md #17 — /ope/LCOM-STEEL — Load Combination (Steel) – KDS 41 30:2022.

    Same schema as LCOM-CONC except CS_ANALYSIS/PRESTRESS_LOSS don't exist.
    """

    OPTION: str  # "ADD"/"REPLACE", required
    DGNCODE: str  # "KDS 41 30 : 2022", required
    RS_SCALE_FACTOR: List[LoadCombScaleFactorItem]  # optional
    WIND_LOAD_COMB: WindLoadComb  # optional
    ORTHO_EFFECT: OrthoEffect  # optional
    ADDITIONAL_LOAD: AdditionalLoad  # optional
    UNDERGROUND_LOAD: UndergroundLoad  # optional


def generate_load_combination_steel(
    argument: LoadCombinationSteelArgument, client: Optional[MidasClient] = None
) -> dict:
    """docs/manual/15_OPE.md #17 — /ope/LCOM-STEEL — Load Combination (Steel) – KDS 41 30:2022."""
    return _post("/ope/LCOM-STEEL", argument, client)


# --- 18. /ope/LCOM-SRC — Load Combination (SRC) – KDS 41 SRC:2022 / AIK-SRC2K


class LoadCombinationSrcKdsArgument(TypedDict, total=False):
    """KDS 41 SRC:2022 variant of /ope/LCOM-SRC. Same schema as
    LCOM-CONC/LCOM-STEEL (no CS_ANALYSIS/PRESTRESS_LOSS)."""

    OPTION: str  # "ADD"/"REPLACE", required
    DGNCODE: str  # "KDS 41 SRC : 2022", required
    RS_SCALE_FACTOR: List[LoadCombScaleFactorItem]  # optional
    WIND_LOAD_COMB: WindLoadComb  # optional
    ORTHO_EFFECT: OrthoEffect  # optional
    ADDITIONAL_LOAD: AdditionalLoad  # optional
    UNDERGROUND_LOAD: UndergroundLoad  # optional


def generate_load_combination_src(
    argument: Union[LoadCombinationSrcKdsArgument, LoadCombinationAikSrc2kArgument],
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/15_OPE.md #18 — /ope/LCOM-SRC — Load Combination (SRC) – KDS 41 SRC:2022 / AIK-SRC2K.

    DGNCODE selects the schema: KDS 41 SRC:2022 (LoadCombinationSrcKdsArgument)
    vs AIK-SRC2K (LoadCombinationAikSrc2kArgument, RS_SCALE_FACTOR optional here).
    """
    return _post("/ope/LCOM-SRC", argument, client)


# --- 19. /ope/GSBG — Bridge Girder Diagram Image Generation -----------------


class AllowableStressLine(TypedDict, total=False):
    OPT_USE: bool  # draw allowable stress line, default false, optional
    COMP: int  # allowable compression stress (follows current system unit setting), required if OPT_USE true
    TENS: int  # allowable tension stress (follows current system unit setting), required if OPT_USE true


class BridgeGirderBatchItem(TypedDict, total=False):
    BRDG_GROUP: str  # bridge girder element group, required
    SF: int  # scale factor, default 1, optional
    GROUP: str  # output group name, required


#: docs/manual/15_OPE.md #19 — /ope/GSBG — Bridge Girder Diagram Image Generation.
#:
#: Manual flags this endpoint "확인 필요" (unconfirmed) as of 2026-07-12: it is
#: published as a standalone Zendesk article (id 59870138081177) but not yet
#: linked from the official MIDAS API Online Manual TOC's OPE section.
#: Transcribed as-is; verify against the production API before relying on it.
#:
#: DGRM_TYPE selects Stress(0)/Force(1) (governs which COMPONENTS values are
#: valid); BATCH selects whether BATCH_LIST or BRDG_GROUP is used. Fields
#: flattened onto one payload with comments noting which mode each applies to
#: (mirrors the MaterialParam precedent). Uses functional TypedDict syntax
#: because "7TH_DOF_TYPE" is not a valid Python identifier (leading digit).
BridgeGirderDiagramArgument = TypedDict(
    "BridgeGirderDiagramArgument",
    {
        "LC_NAME": str,  # load case/combination name, required
        "LC_TYPE": str,  # "ST" (static)/"CS" (construction stage)/"CB" (combination), required
        "DGRM_TYPE": int,  # Stress=0/Force=1, required
        "BATCH": bool,  # default true, optional
        "X_AXIS_TYPE": int,  # Distance=0/Node=1, default 0, optional
        "COMPONENTS": int,  # Stress(DGRM_TYPE=0): Sax=0/+Sby=1/-Sby=2/+Sbz=3/-Sbz=4/Combined=5/7thDOF=6; Force(DGRM_TYPE=1): Fx=0/Fy=1/Fz=2/Mx=3/My=4/Mz=5/Mb=6/Mt=7/Mw=8; default 0, optional
        "7TH_DOF_TYPE": int,  # 0-6, used when DGRM_TYPE=0 and COMPONENTS=6 (7th DOF), default 0, optional
        "COMBINED_COMP": int,  # 0-4, used when DGRM_TYPE=0 and COMPONENTS=5 (Combined), default 0, optional
        "STRESS_LINE": AllowableStressLine,  # optional
        "BATCH_LIST": List[BridgeGirderBatchItem],  # bridge-girder-group/scale-factor/group-name sets, required if BATCH=true
        "BRDG_GROUP": str,  # bridge girder element group, required if BATCH=false
        "STAGE_LIST": List[str],  # construction stages to generate diagrams for (minItems 1), required
        "EXPORT_PATH": str,  # image save path, required
        "EXTENSION": str,  # "bmp"/"jpg"/"emf", required
    },
    total=False,
)


def generate_bridge_girder_diagram(
    argument: BridgeGirderDiagramArgument, client: Optional[MidasClient] = None
) -> dict:
    """docs/manual/15_OPE.md #19 — /ope/GSBG — Bridge Girder Diagram Image Generation.

    See BridgeGirderDiagramArgument's docstring re: the manual's own
    "확인 필요" (unconfirmed) flag on this endpoint.
    """
    return _post("/ope/GSBG", argument, client)
