"""Source: docs/manual/02_DB_Project_Structure.md, items 2-3 (/db/UNIT, /db/STYP).

Both are GET/PUT-only ("신규 파일의 필수 데이터: GET / PUT만 동작") — new-file
required data doesn't support POST/DELETE.
"""
from __future__ import annotations

from typing import TypedDict

from .base import DbResource

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
