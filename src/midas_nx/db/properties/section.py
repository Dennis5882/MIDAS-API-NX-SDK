"""Source: docs/manual/04_DB_Properties.md, item 12 (/db/SECT).

SECT is deeply conditional on SECTTYPE ("DBUSER"/"VALUE"/"SRC"/"COMBINED"/
"PSC"/"TAPERED"/"COMPOSITE"/"SOD") — only the common envelope (SECTTYPE,
SECT_NAME, SECT_BEFORE) is typed here; SECT_I (the SECTTYPE-specific body)
is left as a plain dict, matching the manual's own per-SECTTYPE subsections
(12-A DB/User, 12-B Value, ...) which are not all ported to this v1.
"""
from __future__ import annotations

from typing import Any, TypedDict

from ..base import DbResource


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
