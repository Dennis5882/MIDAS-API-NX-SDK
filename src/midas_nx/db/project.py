"""Source: docs/manual/02_DB_Project_Structure.md, items 1-14 (all but STYP-M1,
the Hyper-S variant of STYP — itemized by URL in INDEX.md but not documented
with a Specifications table/schema in the chapter file, so left unimplemented).

UNIT/STYP are GET/PUT-only ("신규 파일의 필수 데이터: GET / PUT만 동작") — new-file
required data doesn't support POST/DELETE. CO_M/CO_S/CO_T/CO_F (visual color
defaults) are likewise GET/PUT-only. GRUP/BNGR (structure/boundary groups) omit
DELETE — presumably because groups are referenced elsewhere and must be removed
via their owning UI, not itemized here.
"""
from __future__ import annotations

from typing import List, TypedDict

from .base import DbResource, NO_DELETE_METHODS

_GET_PUT_ONLY = frozenset({"GET", "PUT"})


class UnitPayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #2 — /db/UNIT Specifications table."""

    FORCE: str  # "N"/"KN"/"KGF"/"TONF"/"LBF"/"KIPS"
    DIST: str  # "M"/"CM"/"MM"/"FT"/"IN"
    HEAT: str  # "CAL"/"KCAL"/"J"/"KJ"/"BTU"
    TEMPER: str  # "C"/"F"


class Unit(DbResource):
    ENDPOINT = "/db/UNIT"
    NAME = "Unit System"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = _GET_PUT_ONLY


class StructureTypePayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #3 — /db/STYP Specifications table."""

    STYP: int  # Structure Type
    MASS: int  # Mass Type
    bMASSOFFSET: bool  # Consider Offset
    bSELFWEIGHT: bool  # Convert Self Weight to Mass
    SMASS: int  # Structure Mass Type (when bSELFWEIGHT)
    GRAV: float  # Gravity
    TEMP: float  # Initial Temperature
    bALIGNBEAM: bool  # Align Top of Beam Section
    bALIGNSLAB: bool  # Align Top of Slab (Plate)
    bROTRIGID: bool  # Considering Rotational Rigid


class StructureType(DbResource):
    ENDPOINT = "/db/STYP"
    NAME = "Structure Type"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = _GET_PUT_ONLY


class ProjectInfoPayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #1 — /db/PJCF Specifications table."""

    PROJECT: str  # Project Name, optional
    REVISION: str  # Revision Info, optional
    USER: str  # Username, optional
    EMAIL: str  # E-mail, optional
    ADDRESS: str  # Address, optional
    TEL: str  # Telephone Numbers, optional
    FAX: str  # Fax Numbers, optional
    CLIENT: str  # Client, optional
    TITLE: str  # Title, optional
    ENGINEER: str  # Engineer (Review Name), optional
    EDATE: str  # Engineer Review Date, optional
    CHECK1: str  # Checker 1 Name, optional
    CDATE1: str  # Checker 1 Date, optional
    CHECK2: str  # Checker 2 Name, optional
    CDATE2: str  # Checker 2 Date, optional
    CHECK3: str  # Checker 3 Name, optional
    CDATE3: str  # Checker 3 Date, optional
    APPROVE: str  # Approver Name, optional
    ADATE: str  # Approver Date, optional
    COMMENT: str  # Comments, optional


class ProjectInfo(DbResource):
    ENDPOINT = "/db/PJCF"
    NAME = "Project Information"
    PRODUCTS = frozenset({"gen", "civil"})


class StructureGroupPayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #4 — /db/GRUP Specifications table."""

    NAME: str  # Structure Group Name, required
    P_TYPE: int  # Plane Type, default 0
    N_LIST: List[int]  # Node List, optional
    E_LIST: List[int]  # Element List, optional


class StructureGroup(DbResource):
    ENDPOINT = "/db/GRUP"
    NAME = "Structure Group"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = NO_DELETE_METHODS


class BoundaryGroupPayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #5 — /db/BNGR Specifications table."""

    NAME: str  # Boundary Group Name, required
    AUTOTYPE: int  # Auto-generated CR/SH groups for Composite Section: 0=Creep, 1=Shrinkage; default auto-assigned, optional


class BoundaryGroup(DbResource):
    ENDPOINT = "/db/BNGR"
    NAME = "Boundary Group"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = NO_DELETE_METHODS


class LoadGroupPayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #6 — /db/LDGR Specifications table."""

    NAME: str  # Load Group Name, required


class LoadGroup(DbResource):
    ENDPOINT = "/db/LDGR"
    NAME = "Load Group"
    PRODUCTS = frozenset({"gen", "civil"})


class TendonGroupPayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #7 — /db/TDGR Specifications table."""

    NAME: str  # Tendon Group Name, required


class TendonGroup(DbResource):
    ENDPOINT = "/db/TDGR"
    NAME = "Tendon Group"
    PRODUCTS = frozenset({"gen", "civil"})


class NamedPlanePointItem(TypedDict, total=False):
    ITEM: List[float]  # [X, Y, Z] point coordinate


class NamedPlanePayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #8 — /db/NPLN Specifications table."""

    NAME: str  # Plane Name, required
    TYPE: int  # 1=3 Points, 2=X-Y Plane, 3=X-Z Plane, 4=Y-Z Plane; required
    TOL: float  # Tolerance, optional
    POINT: List[NamedPlanePointItem]  # required if TYPE=1: 3 points, each {"ITEM": [X, Y, Z]}
    COORD: float  # required if TYPE!=1: Z/Y/X position depending on TYPE


class NamedPlane(DbResource):
    ENDPOINT = "/db/NPLN"
    NAME = "Named Plane"
    PRODUCTS = frozenset({"gen", "civil"})


class _ColorPayload(TypedDict, total=False):
    """Shared shape of the CO_M/CO_S/CO_T display-color endpoints."""

    W_R: int  # Wire Frame Red, 0-255, optional
    W_G: int  # Wire Frame Green, 0-255, optional
    W_B: int  # Wire Frame Blue, 0-255, optional
    HF_R: int  # Hidden Fill Red, 0-255, optional
    HF_G: int  # Hidden Fill Green, 0-255, optional
    HF_B: int  # Hidden Fill Blue, 0-255, optional
    HE_R: int  # Hidden Edge Red, 0-255, optional
    HE_G: int  # Hidden Edge Green, 0-255, optional
    HE_B: int  # Hidden Edge Blue, 0-255, optional
    bBLEMD: bool  # Opacity Boolean, optional
    FACT: float  # Opacity Value, 0.0-1.0, optional


class MaterialColorPayload(_ColorPayload):
    """docs/manual/02_DB_Project_Structure.md #9 — /db/CO_M Specifications table."""


class MaterialColor(DbResource):
    ENDPOINT = "/db/CO_M"
    NAME = "Material Color"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = _GET_PUT_ONLY


class SectionColorPayload(_ColorPayload):
    """docs/manual/02_DB_Project_Structure.md #10 — /db/CO_S Specifications table."""


class SectionColor(DbResource):
    ENDPOINT = "/db/CO_S"
    NAME = "Section Color"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = _GET_PUT_ONLY


class ThicknessColorPayload(_ColorPayload):
    """docs/manual/02_DB_Project_Structure.md #11 — /db/CO_T Specifications table."""


class ThicknessColor(DbResource):
    ENDPOINT = "/db/CO_T"
    NAME = "Thickness Color"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = _GET_PUT_ONLY


class FloorLoadColorPayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #12 — /db/CO_F Specifications table."""

    NAME: str  # Floor Load Type Name, required
    WF_R: int  # Wire Frame Red, 0-255, optional
    WF_G: int  # Wire Frame Green, 0-255, optional
    WF_B: int  # Wire Frame Blue, 0-255, optional
    HF_R: int  # Hidden Fill Red, 0-255, optional
    HF_G: int  # Hidden Fill Green, 0-255, optional
    HF_B: int  # Hidden Fill Blue, 0-255, optional
    HE_R: int  # Hidden Edge Red, 0-255, optional
    HE_G: int  # Hidden Edge Green, 0-255, optional
    HE_B: int  # Hidden Edge Blue, 0-255, optional
    OPT_BLEND: bool  # Blending, optional
    BLEND_FACTOR: float  # Blending Factor, 0.0-1.0, optional


class FloorLoadColor(DbResource):
    ENDPOINT = "/db/CO_F"
    NAME = "Floor Load Color"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = _GET_PUT_ONLY


class SpanBaseItem(TypedDict, total=False):
    ELEM_KEY: int  # Element No.
    SUPPORT: int  # 0=None, 1=Start, 2=End


class SpanPayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #13 — /db/SPAN Specifications table."""

    NAME: str  # Span Name, required
    bEXACTSPAN: bool  # Exact Span Option, required
    DIRECTION: int  # Inner direction of multiple girders: (-)Local y=0, (+)Local y=1, Both=2, None=3; required
    SECTTYPE: int  # Assign Elements: By Selection=0, Number=1; required
    SPAN_LIST: List[float]  # required if bEXACTSPAN=true
    SPAN_BASE_ITEMS: List[SpanBaseItem]  # required if bEXACTSPAN=true


class Span(DbResource):
    ENDPOINT = "/db/SPAN"
    NAME = "Span Information"
    PRODUCTS = frozenset({"gen", "civil"})


class StoryPayload(TypedDict, total=False):
    """docs/manual/02_DB_Project_Structure.md #14 — /db/STOR Specifications table."""

    STORY_NAME: str  # Story Name, required
    STORY_LEVEL: float  # Story Height (elevation), required
    bFLOOR_DIAPHRAGM: bool  # Rigid Floor Diaphragm assumption, default false, required
    WIND_FLOOR_WIDTH_X: float  # Wind Floor Width X-Dir, required
    WIND_FLOOR_WIDTH_Y: float  # Wind Floor Width Y-Dir, required
    WIND_CENTER_X: float  # Wind Floor Center Xc, required
    WIND_CENTER_Y: float  # Wind Floor Center Yc, required
    WIND_ECCENT_X: float  # Wind Eccentricity X-Dir, required
    WIND_ECCENT_Y: float  # Wind Eccentricity Y-Dir, required
    SEIS_ACC_ECCENT_X: float  # Seismic Accidental Eccentricity X-Dir, required
    SEIS_ACC_ECCENT_Y: float  # Seismic Accidental Eccentricity Y-Dir, required
    SEIS_INHERENT_ECCENT_X: float  # Seismic Inherent Eccentricity X-Dir, required
    SEIS_INHERENT_ECCENT_Y: float  # Seismic Inherent Eccentricity Y-Dir, required
    SEIS_TORSIONAL_AMP_FACTOR_X: float  # Seismic Torsional Amplification Factor X-Dir, required
    SEIS_TORSIONAL_AMP_FACTOR_Y: float  # Seismic Torsional Amplification Factor Y-Dir, required


class Story(DbResource):
    ENDPOINT = "/db/STOR"
    NAME = "Story Data"
    PRODUCTS = frozenset({"gen", "civil"})
