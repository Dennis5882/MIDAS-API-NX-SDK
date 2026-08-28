"""Source: docs/manual/04_DB_Properties.md, items 22-23 (/db/IEHC, /db/IEHG),
plus the Hyper-S hinge-assignment variants IEHG-BEAM-M1, IEHG-TRUSS-M1,
IEHG-GL-M1, IEHG-PSS-M1 (one per element type). None have a Specifications
table in the chapter file. IEHG-BEAM-M1's shape is confirmed live via `GET
/info/db/IEHG-BEAM-M1` (2026-07-29, Civil NX Hyper-S); the other three have
no `/info` route at all (404 there, even though GET on the endpoint itself
works) — their classes assume the identical single-field shape by sibling
analogy, not independent server confirmation. See
InelasticHingePropertyHyperSPayload's docstring.
"""
from __future__ import annotations

from typing import TypedDict

from ..base import HYPER_S_ONLY, DbResource


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
    NAME = "/db/IEHG"
    PRODUCTS = frozenset({"gen", "civil"})


class InelasticHingePropertyHyperSPayload(TypedDict, total=False):
    """Shape confirmed live for IEHG-BEAM-M1 via `GET /info/db/IEHG-BEAM-M1`
    (2026-07-29, Civil NX Hyper-S). IEHG-TRUSS-M1/IEHG-GL-M1/IEHG-PSS-M1
    have no `/info` route (404, even though GET on the endpoint itself
    works) — the identical shape is assumed for them by sibling analogy
    (same IEHG-*-M1 family, differing only by element-type suffix), not
    independently server-confirmed the way BEAM-M1's is.
    """

    INEL_PROP_NAME: str  # Inelastic Hinge Property Name


class InelasticHingePropertyHyperSBeam(DbResource):
    ENDPOINT = "/db/IEHG-BEAM-M1"
    NAME = "Assign Inelastic Hinge Properties (Beam, Hyper-S)"
    PRODUCTS = HYPER_S_ONLY


class InelasticHingePropertyHyperSTruss(DbResource):
    """⚠️ Field shape assumed from IEHG-BEAM-M1 by sibling analogy — this
    endpoint's own `/info/db/...` route 404s, so it isn't independently
    server-confirmed. See InelasticHingePropertyHyperSPayload.
    """

    ENDPOINT = "/db/IEHG-TRUSS-M1"
    NAME = "Assign Inelastic Hinge Properties (Truss, Hyper-S)"
    PRODUCTS = HYPER_S_ONLY


class InelasticHingePropertyHyperSGeneralLink(DbResource):
    """⚠️ See InelasticHingePropertyHyperSTruss — same caveat."""

    ENDPOINT = "/db/IEHG-GL-M1"
    NAME = "Assign Inelastic Hinge Properties (General Link, Hyper-S)"
    PRODUCTS = HYPER_S_ONLY


class InelasticHingePropertyHyperSPss(DbResource):
    """⚠️ Field shape caveat: see InelasticHingePropertyHyperSTruss — this
    endpoint's own `/info/db/...` route also 404s.

    "PSS" is not a mystery: the manual repo's `docs/manual/INDEX.md` titles
    this endpoint "Assign Inelastic Hinges — Point Spring Support (Hyper-S)",
    and `04_DB_Properties.md`'s own chapter TOC calls it "... Point Spring
    (Hyper-S)" — a minor inconsistency within the manual itself ("Support"
    present in one title, absent in the other), but "Point Spring" either
    way. An earlier version of this docstring wrongly claimed the meaning
    "isn't stated in any available source" — it is, just not alongside a
    Specifications table, which is the only thing actually missing here.
    """

    ENDPOINT = "/db/IEHG-PSS-M1"
    NAME = "Assign Inelastic Hinge Properties (Point Spring, Hyper-S)"
    PRODUCTS = HYPER_S_ONLY
