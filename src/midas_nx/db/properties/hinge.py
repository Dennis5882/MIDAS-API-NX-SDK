"""Source: docs/manual/04_DB_Properties.md, items 22-23 (/db/IEHC, /db/IEHG).

The Hyper-S hinge-assignment variants (IEHG-BEAM-M1, IEHG-TRUSS-M1,
IEHG-GL-M1, IEHG-PSS-M1) are itemized by URL in INDEX.md but documented as
thin stubs with no Specifications table in the chapter file, so left
unimplemented.
"""
from __future__ import annotations

from typing import TypedDict

from ..base import DbResource


class InelasticHingeControlPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #22 — /db/IEHC Specifications table.

    The manual's worked example includes several Wall/Cover-division fields
    (WallConsOut, WallDivNumZ, WallDivNumY, dR, WAreaSize,
    OPT_ConsiderRebarAreaWall, CoverDivNumNy, CoverDivNumNz) not itemized in
    its own Specifications table; included here since the example is the
    more concrete source.
    """

    BEAM_LOC: int  # Reference Location for Distributed Hinges: I-End=0, Center=1, J-End=2; required
    OPT_ConsiderRebarArea1D: bool  # Consider Reinforcement Area, required
    FAreaSizeCore: int  # Fiber Beam Areas Core: Auto Size=0, Equal-Size=1; required
    BeamDivNumNy: int  # Number of Divisions (Beam-Column) Ny, required
    BeamDivNumNz: int  # Number of Divisions (Beam-Column) Nz, required
    FAreaSizeCover: int  # Fiber Beam Areas Cover: Auto=0, Equal=1; required
    WallConsOut: bool  # optional, undocumented in table
    WallDivNumZ: int  # optional, undocumented in table
    WallDivNumY: int  # optional, undocumented in table
    dR: float  # optional, undocumented in table
    WAreaSize: str  # optional, undocumented in table
    OPT_ConsiderRebarAreaWall: bool  # optional, undocumented in table
    CoverDivNumNy: int  # optional, undocumented in table
    CoverDivNumNz: int  # optional, undocumented in table


class InelasticHingeControl(DbResource):
    ENDPOINT = "/db/IEHC"
    NAME = "Inelastic Hinge Control Data"
    PRODUCTS = frozenset({"gen", "civil"})


class InelasticHingePropertyPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #23 — /db/IEHG. Keyed by element id."""

    PROP_NAME: str  # Name of Inelastic Hinge Property, required
    FIBER_NAME: str  # Name of Fiber Division (/db/FIBR name), required


class InelasticHingeProperty(DbResource):
    ENDPOINT = "/db/IEHG"
    NAME = "Assign Inelastic Hinge Properties"
    PRODUCTS = frozenset({"gen", "civil"})
