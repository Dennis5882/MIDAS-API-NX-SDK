"""Source: docs/manual/24_DB_Design.md, items 1-13.

Pre-design-calculation input records (both MIDAS Gen NX and Civil NX): RC/
steel design code selection, rebar-check input, unbraced length, design
member assignment, frame definition, slenderness limits, member-type/mark
overrides, and beam/column/wall/brace rebar-data overrides.

Note: this chapter's ``/db/MEMB`` (#5, Design Member Assignment) is a
distinct DB record from ``/ope/MEMB`` (an operation endpoint implemented in
``ope.py``) — the manual has an explicit callout about this; the two share a
URI suffix but are otherwise unrelated.
"""
from __future__ import annotations

from typing import List, TypedDict

from ..post.base import NodeElemsSelector
from .base import DbResource

# Shared KEYS/TO/STRUCTURE_GROUP_NAME "pick one" element-selector used when
# CREATE_SUB_SECTION=true (REBB/REBC/REBR "ELEMS") — identical shape to
# post/base.py's NodeElemsSelector, reused instead of redeclared.
SubSectionElems = NodeElemsSelector


class HoopShearBarSpec(TypedDict, total=False):
    """Shared {NAME, LEG_Y, LEG_Z, DIST} hoop/shear-bar spec used by REBC's
    and REBR's SHEAR_BAR_END/SHEAR_BAR_CEN."""

    NAME: str  # Hoop rebar size, D4~D57, required
    LEG_Y: int  # Number of legs (local Y dir.), required
    LEG_Z: int  # Number of legs (local Z dir.), required
    DIST: float  # Distance between rebars, required


class RebarNameDist(TypedDict, total=False):
    """Shared {NAME, DIST} pair used by REBW's VERTICAL_REBAR/
    HORIZONTAL_REBAR/BE_HORIZONTAL_REBAR."""

    NAME: str  # Rebar size, D4~D57, required
    DIST: float  # Rebar spacing, required


# --- 1. /db/DCON — RC Design Code -------------------------------------------


class RcDesignCodePayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #1 — /db/DCON Specifications table.

    DGNCODE is one of ~64 supported design-code strings (e.g. "KCI-USD12",
    "ACI318-19", "Eurocode2-2:05"); the manual lists only a representative
    subset, not an exhaustive enum.
    """

    DGNCODE: str  # RC Design Code name, required


class RcDesignCode(DbResource):
    ENDPOINT = "/db/DCON"
    NAME = "RC Design Code"


# --- 2. /db/DSTL — Steel Design Code ----------------------------------------


class SteelDesignCodePayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #2 — /db/DSTL Specifications table.

    DGNCODE is one of ~66 supported design-code strings (e.g.
    "AISC(16th)-LRFD22", "Eurocode3-2:05"); the manual lists only a
    representative subset, not an exhaustive enum.
    """

    DGNCODE: str  # Steel Design Code name, required


class SteelDesignCode(DbResource):
    ENDPOINT = "/db/DSTL"
    NAME = "Steel Design Code"


# --- 3. /db/RCHK — Rebar Check Input (Beam/Column) --------------------------


class BeamMainRebarLayerEntry(TypedDict, total=False):
    """POS_TOP_LAYERS / POS_BOT_LAYERS entry within a BEAM vMAIN sector."""

    LAYER: int  # Layer number, required
    dD: float  # Surface-to-rebar-center cover distance, required
    BAR_NUM: int  # Rebar count, required
    BAR_NAME1: str  # Rebar size 1, required
    BAR_NAME2: str  # Rebar size 2, default "", optional


class BeamMainRebarSectorItem(TypedDict, total=False):
    """vMAIN entry (one of I/M/J sectors)."""

    SECTOR: str  # "I"/"J"/"M", required
    POS_TOP_LAYERS: List[BeamMainRebarLayerEntry]  # required
    POS_BOT_LAYERS: List[BeamMainRebarLayerEntry]  # required


class BeamSubRebarSectorItem(TypedDict, total=False):
    """vSUB_BAR entry (one of I/M/J sectors) — transverse (shear/torsion)
    reinforcement."""

    SECTOR: str  # "I"/"J"/"M", required
    dSUB_BARNUM: float  # Rebar count, required
    SUB_BARNAME: str  # Rebar size, required
    dSUB_BARDIST: float  # Rebar spacing, required
    dSUB_BARANGLE: float  # Angle to member, required
    bTORSIONAL_BAR: bool  # Use torsional rebar, optional
    sTRTORBARNA: str  # Torsional rebar size, optional
    dTORBAR_SPACING: float  # Torsional rebar spacing, optional
    bBUNDLEDBAR: bool  # Use bundled rebar, optional
    dBUNDLEDBARNUM: float  # Bundled rebar count, optional
    LONGIBARNA: str  # Longitudinal rebar size, optional
    dLONGIBARNUM: float  # Longitudinal rebar count, optional


class BeamCheckRebar(TypedDict, total=False):
    """"BEAM" object, present when MEMBTYPE="BEAM"."""

    vMAIN: List[BeamMainRebarSectorItem]  # Main (longitudinal) rebar, required
    vSUB_BAR: List[BeamSubRebarSectorItem]  # Sub (transverse) rebar, required


class ColumnRebarPositionEntry(TypedDict, total=False):
    """vPOSITION entry within a COLUMN vLAYER layer."""

    POSITION: str  # Surface position: circular "P1" / rectangular "P1","P2", required
    BAR_NUM: int  # Rebar count, required
    BAR_NAME1: str  # Rebar size 1, required
    BAR_NAME2: str  # Rebar size 2, default blank, optional


class ColumnRebarLayerEntry(TypedDict, total=False):
    """vLAYER entry."""

    INDEX: int  # Layer index (1~5), required
    dDc: float  # Surface-to-rebar-center cover distance, required
    vPOSITION: List[ColumnRebarPositionEntry]  # required


class ColumnSubBarSpec(TypedDict, total=False):
    """COLUMN "SUB_BAR" object — transverse (hoop) reinforcement."""

    SUBBAR_NAME: str  # Rebar size, required
    SUBBAR_DIST: float  # Rebar spacing, required
    SUBBAR_NUM: int  # Rebar count, required
    SUBBAR_NAME_Y: str  # Y-direction rebar size, required
    SUBBAR_NAME_Z: str  # Z-direction rebar size, required
    SUBBAR_NUM_Y: int  # Y-direction rebar count, required
    SUBBAR_NUM_Z: int  # Z-direction rebar count, required


class ColumnCheckRebar(TypedDict, total=False):
    """"COLM" object, present when MEMBTYPE="COLUMN"."""

    vLAYER: List[ColumnRebarLayerEntry]  # Main (longitudinal) rebar layers, required
    SUB_BAR: ColumnSubBarSpec  # required


class RebarCheckInputPayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #3 — /db/RCHK Specifications tables.

    MEMBTYPE selects between the BEAM field group (vMAIN/vSUB_BAR) and the
    COLUMN field group (vLAYER/SUB_BAR); flattened onto one payload (mirrors
    MaterialParam precedent).
    """

    MEMBTYPE: str  # "BEAM"/"COLUMN", required
    ENVTYPE: int  # Crack-check exposure class: Class 1=0/Class 2=1, required
    BEAM: BeamCheckRebar  # required if MEMBTYPE="BEAM"
    COLM: ColumnCheckRebar  # required if MEMBTYPE="COLUMN"


class RebarCheckInput(DbResource):
    ENDPOINT = "/db/RCHK"
    NAME = "Rebar Check Input (Beam/Column)"


# --- 4. /db/LENG — Unbraced Length ------------------------------------------


class UnbracedLengthPayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #4 — /db/LENG Specifications table."""

    LY: float  # Unbraced Length Ly (strong axis), default 0, optional
    LZ: float  # Unbraced Length Lz (weak axis), default 0, optional
    LB: float  # Laterally Unbraced Length, default 0, optional
    bNOTUSE: bool  # Do not consider lateral unbraced length, default false, optional
    bAUTOCALC: bool  # Calculate by Code, default false, optional
    LT: float  # Torsional Unbraced Length, default 0, optional


class UnbracedLength(DbResource):
    ENDPOINT = "/db/LENG"
    NAME = "Unbraced Length"


# --- 5. /db/MEMB — Design Member Assignment ---------------------------------


class DesignMemberAssignmentPayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #5 — /db/MEMB Specifications table.

    DB record only — distinct from the /ope/MEMB operation endpoint (ch15)
    that actually performs member assignment on elements.
    """

    AELEM: List[int]  # Element IDs to group into this design member, required
    bREVERSE: bool  # Reverse local-axis direction, default false, optional


class DesignMemberAssignment(DbResource):
    ENDPOINT = "/db/MEMB"
    NAME = "Design Member Assignment"


# --- 6. /db/DCTL — Definition of Frame --------------------------------------


class FrameDefinitionPayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #6 — /db/DCTL Specifications table."""

    FRAMEX: str  # X-Direction: "Unbraced Sway"/"Braced Non-sway", default "Braced Non-sway", optional
    FRAMEY: str  # Y-Direction: "Unbraced Sway"/"Braced Non-sway", default "Braced Non-sway", optional
    bAUTOKF: bool  # Auto Calculate Effective Length Factor, default false, optional
    DT: str  # Design Type: "3D"/"XZ"/"YZ"/"XY", default "3D", optional


class FrameDefinition(DbResource):
    ENDPOINT = "/db/DCTL"
    NAME = "Definition of Frame"


# --- 7. /db/LTSR — Limiting Slenderness Ratio -------------------------------


class LimitingSlendernessRatioPayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #7 — /db/LTSR Specifications table."""

    bNOTCHECK: bool  # Do not check slenderness, default false, optional
    COMP: float  # Compression limiting slenderness ratio, required
    TENS: float  # Tension limiting slenderness ratio, required


class LimitingSlendernessRatio(DbResource):
    ENDPOINT = "/db/LTSR"
    NAME = "Limiting Slenderness Ratio"


# --- 8. /db/MBTP — Modify Member Type ---------------------------------------


class ModifyMemberTypePayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #8 — /db/MBTP Specifications table."""

    TYPE: str  # Member Type: "COLUMN"/"BEAM"/"BRACE", required


class ModifyMemberType(DbResource):
    ENDPOINT = "/db/MBTP"
    NAME = "Modify Member Type"


# --- 9. /db/WMAK — Modify Wall Mark -----------------------------------------


class ModifyWallMarkPayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #9 — /db/WMAK Specifications table."""

    MARKNAME: str  # Wall Mark Name, required
    WID_LIST: List[int]  # Wall ID List belonging to this mark, required


class ModifyWallMark(DbResource):
    ENDPOINT = "/db/WMAK"
    NAME = "Modify Wall Mark"


# --- 10. /db/REBB — Modify Beam Rebar ---------------------------------------


class BeamMainBarLayerEntry(TypedDict, total=False):
    """Item shape for BAR_SECTOR_*.vMAIN_BAR_TOP / vMAIN_BAR_BOT.

    The manual's own Specifications summary describes MAIN_BAR_TOP/BOT as a
    {LAYER1, LAYER2} object each holding {NAME, NUM}, but the worked
    Request/Response examples show these as "vMAIN_BAR_TOP"/"vMAIN_BAR_BOT"
    *arrays* (always empty in the example, so the item shape isn't directly
    observed there); following the manual's own guidance to prefer the
    example's array-of-layers shape, and inferring per-item fields {LAYER,
    NAME, NUM} from the layer-object Parameters table plus the sibling
    RCHK POS_TOP_LAYERS/POS_BOT_LAYERS array-of-layer-object precedent.
    """

    LAYER: int  # Layer number (1 or 2), required
    NAME: str  # Rebar size, D4~D57, required
    NUM: int  # Rebar count, required


class BeamShearBarSpec(TypedDict, total=False):
    """BAR_SECTOR_*.SHEAR_BAR (stirrup) spec."""

    NAME: str  # Stirrup rebar size, D4~D57, required
    LEG: int  # Number of legs, required
    DIST: float  # Stirrup spacing, required


class BeamRebarSector(TypedDict, total=False):
    """BAR_SECTOR_I / BAR_SECTOR_M / BAR_SECTOR_J object.

    The Parameters table shows a nested "SKIN_BAR": {NAME, NUM} object, but
    the worked example flattens this to "SKIN_BAR_NAME"/"SKIN_BAR_NUM";
    following the example.
    """

    vMAIN_BAR_TOP: List[BeamMainBarLayerEntry]  # required
    vMAIN_BAR_BOT: List[BeamMainBarLayerEntry]  # required
    SHEAR_BAR: BeamShearBarSpec  # required
    SKIN_BAR_NAME: str  # Skin bar rebar size, optional
    SKIN_BAR_NUM: int  # Skin bar count, optional


class BeamRebarItem(TypedDict, total=False):
    """ITEMS entry.

    The Parameters table names the cover-distance fields "DT"/"DB", but the
    worked example uses "MAIN_BAR_DC_TOP"/"MAIN_BAR_DC_BOT" (matching the
    JSON-Schema's own field names); following the example/schema.
    """

    CREATE_SUB_SECTION: bool  # default false, optional
    ID: int  # Sub Section ID, read-only, optional
    ELEMS: SubSectionElems  # required if CREATE_SUB_SECTION=true
    BAR_SECTOR_I: BeamRebarSector  # required
    BAR_SECTOR_M: BeamRebarSector  # required
    BAR_SECTOR_J: BeamRebarSector  # required
    MAIN_BAR_DC_TOP: float  # Top cover distance dT, required
    MAIN_BAR_DC_BOT: float  # Bottom cover distance dB, required
    bSAME_SIZE_TOP_BOT: bool  # optional
    bSAME_SIZE_IMJ: bool  # optional
    bSAME_SIZE_LAYER: bool  # optional


class BeamRebarPayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #10 — /db/REBB Specifications tables."""

    ITEMS: List[BeamRebarItem]  # min 1, required


class BeamRebar(DbResource):
    ENDPOINT = "/db/REBB"
    NAME = "Modify Beam Rebar"


# --- 11. /db/REBC — Modify Column Rebar (POST only) -------------------------


class ColumnMainBarSpec(TypedDict, total=False):
    """REBC ITEMS.MAIN_BAR."""

    NAME: str  # Main rebar size, D4~D57, required
    NUM: int  # Total rebar count, required
    ROW: int  # Number of rows, required
    USE_CORNER: bool  # required
    NAME_CORNER: str  # Corner rebar size, required if USE_CORNER=true


class ColumnRebarItem(TypedDict, total=False):
    """ITEMS entry."""

    CREATE_SUB_SECTION: bool  # default false, optional
    ID: int  # Sub Section ID, read-only, optional
    ELEMS: SubSectionElems  # required if CREATE_SUB_SECTION=true
    MAIN_BAR: ColumnMainBarSpec  # required
    SHEAR_BAR_END: HoopShearBarSpec  # required
    SHEAR_BAR_CEN: HoopShearBarSpec  # required
    DO: float  # Concrete-face-to-rebar-center distance (do), required
    HOOP_TYPE: str  # "Ties"/"Spirals", default "Ties", optional
    HOOK_TYPE: int  # 90+(135 or 180)=0 / Both(135 or 180)=1, default 0, optional


class ColumnRebarPayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #11 — /db/REBC Specifications tables."""

    ITEMS: List[ColumnRebarItem]  # min 1, required


class ColumnRebar(DbResource):
    ENDPOINT = "/db/REBC"
    NAME = "Modify Column Rebar"
    #: This endpoint documents Active Methods as POST only (confirmed by
    #: both the TOC table and this section's own "Active Methods" line) —
    #: a one-off override, not promoted to a shared db/base.py constant
    #: since no other chapter needs POST-only.
    METHODS = frozenset({"POST"})


# --- 12. /db/REBW — Modify Wall Rebar ---------------------------------------


class StoryRange(TypedDict, total=False):
    FROM: str  # Start story, required
    TO: str  # End story, required


class WallEndRebarSpec(TypedDict, total=False):
    NAME: str  # Rebar size, D4~D57, required
    NUM: int  # Rebar count, required
    DIST: float  # Rebar spacing, required


class ConcreteFaceToCenterOfRebar(TypedDict, total=False):
    DW: float  # required
    DE: float  # required


class WallRebarItem(TypedDict, total=False):
    """ITEMS entry.

    SUB_WALL_ID is labeled both "read only" and "Required" by the manual's
    own Parameters table when CREATE_SUB_WALL_ID=true — a self-contradiction
    in the source; the worked Request/Response example sends it as real
    client input (SUB_WALL_ID=1), so it is documented here as required,
    matching the example rather than the "read only" label.
    """

    CREATE_SUB_WALL_ID: bool  # default false, optional
    SUB_WALL_ID: int  # Sub Wall ID, "read only" per manual but sent as required input in the worked example, required if CREATE_SUB_WALL_ID=true
    STORY: StoryRange  # required if CREATE_SUB_WALL_ID=true
    VERTICAL_REBAR: RebarNameDist  # required
    HORIZONTAL_REBAR: RebarNameDist  # required
    USE_END_REBAR: bool  # default false, optional
    END_REBAR: WallEndRebarSpec  # required if USE_END_REBAR=true
    BE_HORIZONTAL_REBAR: RebarNameDist  # Boundary Element horizontal rebar, optional
    BOUNDARY_ELEMENT_LENGTH: float  # default 0, optional
    CONCRETE_FACE_TO_CENTER_OF_REBAR: ConcreteFaceToCenterOfRebar  # dw/de, required
    USE_MODEL_THICKNESS: bool  # default true, optional
    THICKNESS: float  # required if USE_MODEL_THICKNESS=false


class WallRebarPayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #12 — /db/REBW Specifications tables."""

    ITEMS: List[WallRebarItem]  # min 1, required


class WallRebar(DbResource):
    ENDPOINT = "/db/REBW"
    NAME = "Modify Wall Rebar"


# --- 13. /db/REBR — Modify Brace Rebar --------------------------------------


class BraceMainBarSpec(TypedDict, total=False):
    """REBR ITEMS.MAIN_BAR."""

    NAME: str  # Main rebar size, D4~D57, required
    NUM: int  # Rebar count (min 4), required
    ROW: int  # Number of rows, required


class BraceRebarItem(TypedDict, total=False):
    """ITEMS entry."""

    CREATE_SUB_SECTION: bool  # default false, optional
    ID: int  # Sub Section ID, read-only, optional
    ELEMS: SubSectionElems  # required if CREATE_SUB_SECTION=true
    MAIN_BAR: BraceMainBarSpec  # required
    SHEAR_BAR_END: HoopShearBarSpec  # required
    SHEAR_BAR_CEN: HoopShearBarSpec  # required
    DO: float  # Concrete-face-to-rebar-center distance, required
    HOOP_TYPE: str  # "Ties"/"Spirals", default "Ties", optional


class BraceRebarPayload(TypedDict, total=False):
    """docs/manual/24_DB_Design.md #13 — /db/REBR Specifications tables."""

    ITEMS: List[BraceRebarItem]  # min 1, required


class BraceRebar(DbResource):
    ENDPOINT = "/db/REBR"
    NAME = "Modify Brace Rebar"
