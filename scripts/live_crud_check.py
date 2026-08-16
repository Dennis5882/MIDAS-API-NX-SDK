"""Live create -> read -> update -> read -> delete -> read round trips for the
/db/* resources a real modelling script actually touches, against a real
Gen NX / Civil NX session.

The read-only counterpart, scripts/live_readonly_sweep.py, proves an endpoint
exists and answers. This proves the SDK's *write* shapes are the ones the
server actually accepts: that ``create()``'s "Assign" body lands, that a
``get()`` echoes back what was written, that ``update()`` changes it, and that
``delete()`` removes it. A TypedDict transcribed with a wrong field name will
pass every mocked test in tests/ and only fail here.

Cases are grouped into **tiers**, run in priority order — the order in which a
modelling script needs them, not the order the manual lists them:

    core       the proven baseline (groups, nodes, elements, load cases, loads)
    props      material / section sub-types (thickness, stiffness factors,
               time-dependent material)
    boundary   springs and links
    static     the rest of ch06's static loads, plus ch07 element/nodal
               temperature
    stage      construction stages and what attaches to them
    moving     moving-load chain (code -> lane -> vehicle -> case). Its
               fixtures are AASHTO LRFD/HL-93 (rebuilt 2026-07-30 from
               Korea-standard, cross-checked against a real production
               arch-bridge model's own data) and kept Civil-only here for
               now, pending an actual Gen run; the underlying routes answer
               on Gen too but per-CODE, not unconditionally (see the tier's
               own comment) — /db/CMCS in the stage tier is the one still
               genuinely Civil-only

``--tier`` runs a subset. Every tier declares its own seed, so a tier is
runnable on its own.

Fixture design
--------------
Most first-run failures in this checker have been bad fixtures, not SDK bugs
(4 of 4 on the first Civil run, 2026-07-26). Two rules keep it that way:

1. **Seed first, then take the next id.** Definition tables disagree about
   whether they honour the ``"Assign"`` key: /db/NODE does (posting under 77
   yields node 77), /db/STLD does not (it renumbers to the next free slot).
   So a seeded record goes in at the lowest free key and its case takes the
   *next sequential* key — under either behaviour both land on the same id.
   Where a record can be referenced by name (structure/boundary/load groups,
   spring types, lanes, vehicles) the fixtures reference it by name and the
   id question never arises.
2. **Nothing a case deletes may be another case's prerequisite.** Seeded
   records are suffixed ``_SEED`` and no case touches them.

Failure classification
----------------------
A checker that cries wolf gets ignored, so the report separates:

    regression   a case that has completed this round trip live before broke
                 -> treat as an SDK defect until proven otherwise
    unverified   a case that has never passed live failed -> triage the
                 fixture payload first; it is not yet evidence about the SDK
    blocked      a seed step this case declared a need for failed, so the
                 case never ran -> fixture
    skipped      quarantined: calling the endpoint is known to hang or kill
                 MIDAS NX, so it is not run unless --include-crashers

``Case.confirmed=True`` marks the cases that have actually passed against a
live server. Flip a case to ``confirmed=True`` only after you have watched it
pass, and say where in the comment. As of 2026-07-29, all 43 are confirmed
on Civil NX 2026 v2.2 (and 40 of them on v2.1 as well).

/db/NMAS was quarantined from 2026-07-26 until 2026-07-29: a POST omitting
its optional rmX/rmY/rmZ fields reliably killed both Civil NX and Gen NX
(15+ reproductions). The root cause turned out to be exactly that omission
- sending the fields explicitly (even as 0.0) doesn't crash it - so
NodalMass.create()/.update() now fill them in and this case runs
unquarantined. --include-crashers still exists for any future case that
needs it.

DESTRUCTIVE. It calls /doc/NEW and builds a throwaway model. Never point it at
a session holding work you care about.

⚠️ /doc/NEW on a document with unsaved changes raises MIDAS's own save-changes
dialog, and that dialog blocks the entire API session until a human clicks it -
the next call fails for reasons unrelated to itself. Have a human present, or
start from a saved document.

⚠️ --save-as exists to clear that dialog by saving first, but /doc/SAVEAS is
not safe to automate blind: given a path NX dislikes it raises a modal
"invalid path" error dialog, blocks the session until someone clicks it, and
then returns {"message": "... command complete"} anyway - the same string a
real save returns, with no file on disk. Verified 2026-07-26 on Civil NX.
Check the file exists yourself afterwards; do not trust the response.

Run with the dev environment active (``pip install -e ".[dev]"``), e.g.:
    python scripts/live_crud_check.py --product civil
    python scripts/live_crud_check.py --product civil --tier core,boundary
    python scripts/live_crud_check.py --product civil --save-as C:/tmp/scratch.mcb
    python scripts/live_crud_check.py --product civil --out crud.json

Exit code 0 -> every case that ran completed a full round trip.
Exit code 1 -> a previously-confirmed case regressed (SDK defect suspect).
Exit code 2 -> couldn't connect, or the server rejected the connection.
Exit code 3 -> only unverified failures / blocked cases (triage the fixtures).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence

from midas_nx import doc
from midas_nx.client import MidasAPIError, MidasClient
from midas_nx.db.boundary import (
    BeamEndOffset,
    BeamEndRelease,
    ChangeGeneralLinkProperty,
    Constraint,
    ConstraintLabelDirection,
    ElasticLink,
    ForceDeformationFunction,
    GeneralLink,
    GeneralLinkHyperS,
    GeneralLinkProperty,
    GeneralSpringSupport,
    GeneralSpringType,
    LinearConstraint,
    PanelZoneEffect,
    PlateEndRelease,
    PointSpring,
    RigidLink,
    SurfaceSpring,
)
from midas_nx.db.construction_stage import (
    CamberConstructionStage,
    ConstructionStage,
    CreepCoefficientConstructionStage,
    TimeLoadConstructionStage,
)
from midas_nx.db.moving_loads import (
    MovingLoadCase,
    MovingLoadCode,
    TrafficLineLanes,
    VehicleClasses,
    Vehicles,
)
from midas_nx.db.node_element import Element, Node, Skew
from midas_nx.db.project import (
    BoundaryGroup,
    FloorLoadColor,
    LoadGroup,
    MaterialColor,
    NamedPlane,
    ProjectInfo,
    SectionColor,
    Span,
    StructureGroup,
    StructureType,
    StructureTypeHyperS,
    TendonGroup,
    ThicknessColor,
    Unit,
)
from midas_nx.db.properties.material import (
    Material,
    TimeDependentMaterialCreepShrinkage,
    TimeDependentMaterialLink,
    TimeDependentMaterialStrength,
)
from midas_nx.db.properties.section import (
    ElementStiffnessScaleFactor,
    Section,
    SectionStiffness,
    TaperedGroup,
)
from midas_nx.db.properties.thickness import Thickness
from midas_nx.db.static_loads import (
    BeamLoad,
    FloorLoadType,
    LoadsToMass,
    NodalBodyForce,
    NodalLoad,
    NodalMass,
    PressureLoad,
    PressureLoadType,
    SelfWeight,
    SpecifiedDisplacement,
    StaticLoadCase,
)
from midas_nx.db.temperature_prestress import ElementTemperature, NodalTemperature

sys.stdout.reconfigure(encoding="utf-8")

SIZE, HEIGHT, BAY = 0.6, 3.2, 4.0

#: How a failed case is reported. See the module docstring.
OK, REGRESSION, UNVERIFIED, BLOCKED = "ok", "regression", "unverified", "blocked"
#: Quarantined: known to hang or kill the product, so not run by default.
SKIPPED = "skipped"


class Case:
    """One resource's round trip: what to write, what to change, what to check.

    ``probe`` pulls the single value the assertions compare on, so a case
    stays readable even when the payload is deeply nested. Where echoing a
    value back is itself uncertain (server-side reordering, unit conversion),
    probe something boring like NAME — the point of this checker is that the
    write lands and the delete removes it, not field-level fidelity.

    ``confirmed`` means this exact case has completed the round trip against a
    real server; only those count as regressions when they fail.
    """

    def __init__(
        self,
        resource,
        create_payload: dict,
        update_payload: dict,
        probe: Callable[[dict], Any],
        expect_created: Any,
        expect_updated: Any,
        item_id: int = 1,
        confirmed: bool = False,
        products: Optional[Sequence[str]] = None,
        needs: Sequence[str] = (),
        crashes: Optional[str] = None,
    ) -> None:
        self.resource = resource
        self.create_payload = create_payload
        self.update_payload = update_payload
        self.probe = probe
        self.expect_created = expect_created
        self.expect_updated = expect_updated
        self.item_id = item_id
        self.confirmed = confirmed
        self.products = tuple(products) if products else ("gen", "civil")
        #: Names of the seed steps this case genuinely depends on. A case that
        #: needs nothing still runs when a sibling's seed step fails — the
        #: first live run blocked 7 cases behind one unrelated /db/TDMT seed
        #: failure, which is exactly the false-positive noise that gets a
        #: checker ignored.
        self.needs = tuple(needs)
        #: Set when calling this endpoint is known to hang or kill MIDAS NX.
        #: Such a case is skipped unless --include-crashers is passed: the
        #: cost of running it is a forced restart plus the license-recovery
        #: dance, and it takes every case after it down with it.
        self.crashes = crashes


class SeedStep:
    """One named, independently-failing piece of a tier's fixture."""

    def __init__(self, name: str, run: Callable[[MidasClient], None]) -> None:
        self.name = name
        self.run = run


class Tier:
    """A named group of cases plus the seed steps they need.

    The seed runs immediately before the tier's cases, not once up front, so
    a tier stays runnable on its own and so a tier can rebuild something an
    earlier tier's case deleted (``moving`` re-creates /db/MVCD, which the
    ``core`` tier's own case deletes).
    """

    def __init__(self, name: str, title: str, seeds: Callable[[], List[SeedStep]],
                 cases: Callable[[], List[Case]]) -> None:
        self.name = name
        self.title = title
        self.seeds = seeds
        self.cases = cases


# --------------------------------------------------------------------------
# Base model — everything every tier can assume exists.
# --------------------------------------------------------------------------


def _seed_model(client: MidasClient) -> None:
    """Minimum model the cases attach to.

    Ids are chosen so that nothing here collides with a case:
      nodes    1-2 frame, 3-4 beam chain, 5-8 plate corners, 21-22 free pair
      elements 1-3 beams, 4 plate
      material 1, section 1, thickness 1, load cases 1 (DL) and 2 (LC_SCRATCH)
    """
    Unit.update({1: {"DIST": "M", "FORCE": "KN"}}, client=client)
    Material.create(
        {1: {"TYPE": "CONC", "NAME": "C24",
             "PARAM": [{"P_TYPE": 1, "STANDARD": "KS01(RC)", "DB": "C24"}]}},
        client=client,
    )
    Section.create(
        {1: {"SECTTYPE": "DBUSER", "SECT_NAME": "Column",
             "SECT_BEFORE": {"USE_SHEAR_DEFORM": True, "SHAPE": "SB", "DATATYPE": 2,
                             "SECT_I": {"vSIZE": [SIZE, SIZE]}}}},
        client=client,
    )
    # Thickness 1 backs the plate element; the props tier's own THIK case
    # takes id 2 so it can be deleted without taking the plate with it.
    Thickness.create(
        {1: {"NAME": "T_SEED", "TYPE": "VALUE", "bINOUT": False,
             "T_IN": 0.20, "T_OUT": 0, "O_VALUE": 0}},
        client=client,
    )
    Node.create(
        {
            1: {"X": 0, "Y": 0, "Z": 0},
            2: {"X": 0, "Y": 0, "Z": HEIGHT},
            3: {"X": BAY, "Y": 0, "Z": HEIGHT},
            4: {"X": 2 * BAY, "Y": 0, "Z": HEIGHT},
            # Plate corners, offset in -Y so they can't be confused with the frame.
            5: {"X": 0, "Y": -BAY, "Z": 0},
            6: {"X": BAY, "Y": -BAY, "Z": 0},
            7: {"X": BAY, "Y": -2 * BAY, "Z": 0},
            8: {"X": 0, "Y": -2 * BAY, "Z": 0},
            # A free, unconnected pair for the link/constraint cases. Nothing
            # else attaches to these, so ELNK/RIGD/MCON can't collide with a
            # real element — but they do collide with *each other*, so those
            # three cases rely on each deleting itself before the next runs.
            21: {"X": 0, "Y": 2 * BAY, "Z": 0},
            22: {"X": 0, "Y": 2 * BAY, "Z": HEIGHT},
        },
        client=client,
    )
    Element.create(
        {
            1: {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [1, 2]},
            2: {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [2, 3]},
            3: {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [3, 4]},
            4: {"TYPE": "PLATE", "MATL": 1, "SECT": 1, "NODE": [5, 6, 7, 8]},
        },
        client=client,
    )
    Constraint.create({1: {"ITEMS": [{"ID": 1, "CONSTRAINT": "1111111"}]}}, client=client)
    StaticLoadCase.create({1: {"NAME": "DL", "TYPE": "D", "DESC": "Dead Load"}}, client=client)
    # A load case every load case below attaches to, that nothing deletes.
    StaticLoadCase.create({2: {"NAME": "LC_SCRATCH", "TYPE": "L", "DESC": "crud fixture"}},
                          client=client)
    SelfWeight.create({1: {"LCNAME": "DL", "FV": [0, 0, -1]}}, client=client)


def _no_seeds() -> List[SeedStep]:
    """Tiers that need nothing beyond the base model."""
    return []


# --------------------------------------------------------------------------
# Tier: core — the baseline proven live on 2026-07-26 (Civil 10/10, Gen 9/9).
# --------------------------------------------------------------------------


def _core_cases() -> List[Case]:
    return [
        Case(
            StructureGroup,
            {"NAME": "SG_CRUD"}, {"NAME": "SG_CRUD_2"},
            lambda p: p.get("NAME"), "SG_CRUD", "SG_CRUD_2",
            confirmed=True,
        ),
        Case(
            BoundaryGroup,
            {"NAME": "BG_CRUD"}, {"NAME": "BG_CRUD_2"},
            lambda p: p.get("NAME"), "BG_CRUD", "BG_CRUD_2",
            confirmed=True,
        ),
        Case(
            LoadGroup,
            {"NAME": "LG_CRUD"}, {"NAME": "LG_CRUD_2"},
            lambda p: p.get("NAME"), "LG_CRUD", "LG_CRUD_2",
            confirmed=True,
        ),
        Case(
            Node,
            {"X": 1.0, "Y": 2.0, "Z": 3.0}, {"X": 1.0, "Y": 2.0, "Z": 9.5},
            lambda p: p.get("Z"), 3.0, 9.5,
            item_id=101, confirmed=True,
        ),
        # Keyed by node id: node 2 is seeded and no case deletes it.
        Case(
            Skew,
            {"iMETHOD": 1, "ANGLE_X": 0, "ANGLE_Y": 0, "ANGLE_Z": 30},
            {"iMETHOD": 1, "ANGLE_X": 0, "ANGLE_Y": 0, "ANGLE_Z": 45},
            lambda p: p.get("ANGLE_Z"), 30, 45,
            item_id=2, confirmed=True,
        ),
        # /db/STLD renumbers: the server assigns NO sequentially rather than
        # honouring the "Assign" key, so this has to be the next free slot
        # after the two the seed creates.
        Case(
            StaticLoadCase,
            {"NAME": "CRUDCASE", "TYPE": "L", "DESC": "crud"},
            {"NAME": "CRUDCASE", "TYPE": "L", "DESC": "crud updated"},
            lambda p: p.get("DESC"), "crud", "crud updated",
            item_id=3, confirmed=True,
        ),
        # Loads reference LC_SCRATCH, which the seed creates and nothing deletes.
        Case(
            NodalLoad,
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "FZ": -10.0}]},
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "FZ": -25.0}]},
            lambda p: p["ITEMS"][0].get("FZ"), -10.0, -25.0,
            item_id=2, confirmed=True,
        ),
        Case(
            BeamLoad,
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "CMD": "BEAM", "TYPE": "UNILOAD",
                        "DIRECTION": "GZ", "D": [0, 1, 0, 0], "P": [-5.0, -5.0, 0, 0]}]},
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "CMD": "BEAM", "TYPE": "UNILOAD",
                        "DIRECTION": "GZ", "D": [0, 1, 0, 0], "P": [-8.0, -8.0, 0, 0]}]},
            lambda p: p["ITEMS"][0]["P"][0], -5.0, -8.0,
            confirmed=True,
        ),
        # CONSTRAINT must be exactly 7 characters (Dx Dy Dz Rx Ry Rz W). A
        # 6-character string is rejected with "[Error] Constraint Condition
        # has(have) been incorrectly entered." rather than being padded.
        Case(
            Constraint,
            {"ITEMS": [{"ID": 2, "CONSTRAINT": "1110000"}]},
            {"ITEMS": [{"ID": 2, "CONSTRAINT": "1111111"}]},
            lambda p: p["ITEMS"][0].get("CONSTRAINT"), "1110000", "1111111",
            item_id=2, confirmed=True,
        ),
        # Deletes itself, which is what lets the moving tier re-create the
        # code it needs. Framed by the manual as Civil-only; live-confirmed
        # 2026-07-29 to also answer on Gen NX — but per-CODE, not
        # unconditionally: "AASHTO STANDARD"/"AASHTO LRFD"/"EUROCODE"/"BS"
        # create fine on Gen, while "KOREA"/"CHINA"/"KSCE-LSD15" answer 201
        # with `[Error] ... Unavailable moving load code` there (confirmed
        # live; presumably a licensed-module gate per region code, not a
        # route-level restriction). Uses "AASHTO STANDARD"/"AASHTO LRFD" here
        # specifically so this case runs unmodified on both products — don't
        # swap back to a KR/CN code without re-splitting per product.
        Case(
            MovingLoadCode,
            {"CODE": "AASHTO STANDARD"}, {"CODE": "AASHTO LRFD"},
            lambda p: p.get("CODE"), "AASHTO STANDARD", "AASHTO LRFD",
            confirmed=True,
        ),
    ]


# --------------------------------------------------------------------------
# Tier: props — material / section sub-types.
# --------------------------------------------------------------------------


def _props_seeds() -> List[SeedStep]:
    """/db/TMAT links a creep/shrinkage record to a strength record *by name*,
    so both have to outlive the cases that exercise those two tables.

    ⚠️ /db/TDMT and /db/TDME do **not** share a code-name enum, and the two
    spell the *same* code differently. This cost a whole session on
    2026-07-26, when /db/TDMT looked broken because it was being fed
    /db/TDME's spellings.

        code          /db/TDMT ``CODE``     /db/TDME ``CODENAME``
        CEB-FIP 2010  "CEB_FIP_2010"        "CEB-FIP(2010)"
        CEB-FIP 1990  "CEB"                 "CEB-FIP(1990)"
        KDS 2016      "KDS_2016"            "KDS-2016"
        European      "EUROPEAN"            "European"

    /db/TDMT takes UNDERSCORED_UPPERCASE tokens; /db/TDME takes the
    human-readable display string. Both are documented correctly and in full
    by the official articles (see docs/live_verification_notes.md for the
    URLs) — the values we were probing with came from a bad transcription in
    the vendored manual copy, not from MIDASIT.

    ``"European"`` is accepted here and reads back as ``"EUROPEAN"``, so the
    match is case-insensitive; that is why this seed works despite not being
    spelled the official way.

    The two error strings are still diagnostic: "Wrong Field" means the code
    name is unknown, while "[Error] Time Dependent Material(...) input data
    contain errors" means the name was recognised but the code's companion
    fields are missing. Vary the *value* before the field names.
    """
    return [
        # Two records, because /db/TMAT's update has to switch TDMT_NAME to a
        # *different* creep/shrinkage record and both have to outlive the
        # /db/TDMT case, which deletes its own. Pointing the update at
        # TDMT_CRUD instead earned a "Wrong DB Name" on 2026-07-26 - a
        # self-inflicted violation of the "nothing a case deletes is another
        # case's prerequisite" rule three functions above.
        SeedStep("tdmt_seed", lambda c: TimeDependentMaterialCreepShrinkage.create(
            {1: {"NAME": "TD_SEED", "CODE": "European", "STR": 24000, "HU": 70,
                 "MSIZE": 0.2, "CTYPE": "RS", "AGE": 28},
             2: {"NAME": "TD_SEED_2", "CODE": "European", "STR": 30000, "HU": 65,
                 "MSIZE": 0.25, "CTYPE": "RS", "AGE": 28}}, client=c)),
        SeedStep("tdme_seed", lambda c: TimeDependentMaterialStrength.create(
            {1: {"NAME": "TD_SEED", "TYPE": "CODE", "CODENAME": "CEB-FIP(2010)",
                 "STRENGTH": 24000}}, client=c)),
    ]


def _props_cases() -> List[Case]:
    return [
        # id 2: thickness 1 is the seeded one the plate element uses.
        Case(
            Thickness,
            {"NAME": "THK_CRUD", "TYPE": "VALUE", "bINOUT": False,
             "T_IN": 0.25, "T_OUT": 0, "O_VALUE": 0},
            {"NAME": "THK_CRUD", "TYPE": "VALUE", "bINOUT": False,
             "T_IN": 0.30, "T_OUT": 0, "O_VALUE": 0},
            lambda p: p.get("T_IN"), 0.25, 0.30,
            item_id=2, confirmed=True,
        ),
        # Keyed by element id.
        Case(
            ElementStiffnessScaleFactor,
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "AREA_SF": 0.5, "ASY_SF": 1.0,
                        "ASZ_SF": 1.0, "IXX_SF": 1.0, "IYY_SF": 1.0, "IZZ_SF": 1.0,
                        "WGT_SF": 1.0}]},
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "AREA_SF": 0.75, "ASY_SF": 1.0,
                        "ASZ_SF": 1.0, "IXX_SF": 1.0, "IYY_SF": 1.0, "IZZ_SF": 1.0,
                        "WGT_SF": 1.0}]},
            lambda p: p["ITEMS"][0].get("AREA_SF"), 0.5, 0.75,
            item_id=2, confirmed=True,
        ),
        # Resolved live 2026-07-26: /db/SECF is keyed by **section** id, not
        # element id. Posting under element 3 returned 200 with no error and
        # silently stored nothing; the identical body under section 1 round-
        # tripped. db/properties/section.py said "element id" and was wrong.
        Case(
            SectionStiffness,
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "AREA_SF": 1.2, "IYY_SF": 1.0,
                        "IZZ_SF": 1.0, "WGT_SF": 1.0}]},
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "AREA_SF": 1.4, "IYY_SF": 1.0,
                        "IZZ_SF": 1.0, "WGT_SF": 1.0}]},
            lambda p: p["ITEMS"][0].get("AREA_SF"), 1.2, 1.4,
            item_id=1, confirmed=True,
        ),
        Case(
            TaperedGroup,
            {"NAME": "TG_CRUD", "ELEMLIST": [2, 3], "ZVAR": "LINEAR", "YVAR": "LINEAR"},
            {"NAME": "TG_CRUD_2", "ELEMLIST": [2, 3], "ZVAR": "LINEAR", "YVAR": "LINEAR"},
            lambda p: p.get("NAME"), "TG_CRUD", "TG_CRUD_2",
            confirmed=True,
        ),
        # id 3: ids 1-2 are TD_SEED/TD_SEED_2, which /db/TMAT references by name.
        Case(
            TimeDependentMaterialCreepShrinkage,
            {"NAME": "TDMT_CRUD", "CODE": "European", "STR": 24000, "HU": 70,
             "MSIZE": 0.2, "CTYPE": "RS", "AGE": 28},
            {"NAME": "TDMT_CRUD", "CODE": "European", "STR": 24000, "HU": 60,
             "MSIZE": 0.2, "CTYPE": "RS", "AGE": 28},
            lambda p: p.get("HU"), 70, 60,
            item_id=3, confirmed=True,
        ),
        Case(
            TimeDependentMaterialStrength,
            {"NAME": "TDME_CRUD", "TYPE": "CODE", "CODENAME": "CEB-FIP(2010)",
             "STRENGTH": 24000},
            {"NAME": "TDME_CRUD", "TYPE": "CODE", "CODENAME": "CEB-FIP(2010)",
             "STRENGTH": 30000},
            lambda p: p.get("STRENGTH"), 24000, 30000,
            item_id=2, confirmed=True,
        ),
        # Keyed by material id (the manual's example keys it "2", a material
        # number, not a running id). Material 1 is the seeded C24.
        Case(
            TimeDependentMaterialLink,
            {"TDMT_NAME": "TD_SEED", "TDME_NAME": "TD_SEED"},
            {"TDMT_NAME": "TD_SEED_2", "TDME_NAME": "TD_SEED"},
            lambda p: p.get("TDMT_NAME"), "TD_SEED", "TD_SEED_2",
            item_id=1, confirmed=True, needs=("tdmt_seed", "tdme_seed"),
        ),
    ]


# --------------------------------------------------------------------------
# Tier: boundary — springs and links.
# --------------------------------------------------------------------------


def _boundary_seeds() -> List[SeedStep]:
    """/db/GSPR assigns a general spring *type* by name, and the update step
    has to switch to a second one, so two survive the tier."""
    return [
        SeedStep("spring_types", lambda c: GeneralSpringType.create(
            {
                1: {"NAME": "GS_SEED", "OPT_STIFFNESS": True,
                    "SPRING": [1000, 0, 0, 0, 0, 0, 500, 0, 0, 0, 0, 500,
                               0, 0, 0, 0, 0, 0, 0, 0, 0]},
                2: {"NAME": "GS_SEED_2", "OPT_STIFFNESS": True,
                    "SPRING": [2000, 0, 0, 0, 0, 0, 800, 0, 0, 0, 0, 800,
                               0, 0, 0, 0, 0, 0, 0, 0, 0]},
            },
            client=c)),
    ]


def _boundary_cases() -> List[Case]:
    # All nine confirmed live on Civil NX 2026 v2.1 (build 06/05/2026),
    # 2026-07-26 — 9/9 full round trips in the first run that exercised them.
    return [
        # Keyed by node id. LINEAR uses SDR/F_S; COMP/TENS/MULTI would use
        # DIR/DV/SK instead.
        Case(
            PointSpring,
            {"ITEMS": [{"ID": 1, "TYPE": "LINEAR", "GROUP_NAME": "",
                        "SDR": [1000, 500, 500, 0, 0, 0],
                        "F_S": [False, False, False, False, False, False]}]},
            {"ITEMS": [{"ID": 1, "TYPE": "LINEAR", "GROUP_NAME": "",
                        "SDR": [2000, 500, 500, 0, 0, 0],
                        "F_S": [False, False, False, False, False, False]}]},
            lambda p: p["ITEMS"][0]["SDR"][0], 1000, 2000,
            item_id=2, confirmed=True,
        ),
        # id 3: ids 1-2 are the seeded types /db/GSPR references by name.
        Case(
            GeneralSpringType,
            {"NAME": "GS_CRUD", "OPT_STIFFNESS": True,
             "SPRING": [1500, 0, 0, 0, 0, 0, 600, 0, 0, 0, 0, 600,
                        0, 0, 0, 0, 0, 0, 0, 0, 0]},
            {"NAME": "GS_CRUD_2", "OPT_STIFFNESS": True,
             "SPRING": [1500, 0, 0, 0, 0, 0, 600, 0, 0, 0, 0, 600,
                        0, 0, 0, 0, 0, 0, 0, 0, 0]},
            lambda p: p.get("NAME"), "GS_CRUD", "GS_CRUD_2",
            item_id=3, confirmed=True,
        ),
        Case(
            GeneralSpringSupport,
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "TYPE_NAME": "GS_SEED"}]},
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "TYPE_NAME": "GS_SEED_2"}]},
            lambda p: p["ITEMS"][0].get("TYPE_NAME"), "GS_SEED", "GS_SEED_2",
            item_id=3, confirmed=True, needs=("spring_types",),
        ),
        # The next three all use the free 21/22 node pair and each deletes
        # itself before the next runs — a node can't carry an elastic link, a
        # rigid link and a linear constraint at once.
        Case(
            ElasticLink,
            {"NODE": [21, 22], "LINK": "GEN", "ANGLE": 0,
             "SDR": [1000, 500, 500, 0, 0, 0],
             "R_S": [False, False, False, False, False, False],
             "bSHEAR": False, "DR": [0, 0]},
            {"NODE": [21, 22], "LINK": "GEN", "ANGLE": 0,
             "SDR": [2000, 500, 500, 0, 0, 0],
             "R_S": [False, False, False, False, False, False],
             "bSHEAR": False, "DR": [0, 0]},
            lambda p: p["SDR"][0], 1000, 2000,
            confirmed=True,
        ),
        # Keyed by *master* node id, not a running serial.
        Case(
            RigidLink,
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "DOF": 111111, "S_NODE": [22]}]},
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "DOF": 110001, "S_NODE": [22]}]},
            lambda p: p["ITEMS"][0].get("DOF"), 111111, 110001,
            item_id=21, confirmed=True,
        ),
        Case(
            LinearConstraint,
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "SLAVE_TYPE": "111000", "TYPE": "EX",
                        "SLAVES": [{"NODE_KEY": 21, "COEFF": 1.0}]}]},
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "SLAVE_TYPE": "111000", "TYPE": "EX",
                        "SLAVES": [{"NODE_KEY": 21, "COEFF": 0.5}]}]},
            lambda p: p["ITEMS"][0]["SLAVES"][0].get("COEFF"), 1.0, 0.5,
            item_id=22, confirmed=True,
        ),
        # Keyed by element id. FLAG_I/FLAG_J are 7-char [Fx,Fy,Fz,Mx,My,Mz,Mb].
        Case(
            BeamEndRelease,
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "bVALUE": False,
                        "FLAG_I": "0000100", "VALUE_I": [0, 0, 0, 0, 0, 0, 0],
                        "FLAG_J": "0000000", "VALUE_J": [0, 0, 0, 0, 0, 0, 0]}]},
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "bVALUE": False,
                        "FLAG_I": "0000100", "VALUE_I": [0, 0, 0, 0, 0, 0, 0],
                        "FLAG_J": "0000100", "VALUE_J": [0, 0, 0, 0, 0, 0, 0]}]},
            lambda p: p["ITEMS"][0].get("FLAG_J"), "0000000", "0000100",
            item_id=2, confirmed=True,
        ),
        # TYPE="ELEMENT" is the ECS form: no RGDXi/RGDXj.
        Case(
            BeamEndOffset,
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "TYPE": "ELEMENT",
                        "RGDYi": 0.11, "RGDZi": 0.12, "RGDYj": 0.21, "RGDZj": 0.22}]},
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "TYPE": "ELEMENT",
                        "RGDYi": 0.15, "RGDZi": 0.12, "RGDYj": 0.21, "RGDZj": 0.22}]},
            lambda p: p["ITEMS"][0].get("RGDYi"), 0.11, 0.15,
            item_id=3, confirmed=True,
        ),
        # Element 4 is the seeded plate; ELEM_TYPE has to match it.
        Case(
            SurfaceSpring,
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "ELEM_TYPE": "PLANAR(FACE)",
                        "SPRING_TYPE": 0, "MODULUS": 500}]},
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "", "ELEM_TYPE": "PLANAR(FACE)",
                        "SPRING_TYPE": 0, "MODULUS": 800}]},
            lambda p: p["ITEMS"][0].get("MODULUS"), 500, 800,
            item_id=4, confirmed=True,
        ),
    ]


# --------------------------------------------------------------------------
# Tier: static — the rest of ch06, plus ch07 element/nodal temperature.
# --------------------------------------------------------------------------


def _static_cases() -> List[Case]:
    return [
        # Node 1 is the constrained support, which is what a specified
        # displacement needs. VALUES is [Dx,Dy,Dz,Rx,Ry,Rz] in the local CS.
        Case(
            SpecifiedDisplacement,
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "GROUP_NAME": "",
                        "VALUES": [{"OPT_FLAG": True, "DISPLACEMENT": 0.01},
                                   {"OPT_FLAG": False, "DISPLACEMENT": 0},
                                   {"OPT_FLAG": False, "DISPLACEMENT": 0},
                                   {"OPT_FLAG": False, "DISPLACEMENT": 0},
                                   {"OPT_FLAG": False, "DISPLACEMENT": 0},
                                   {"OPT_FLAG": False, "DISPLACEMENT": 0}]}]},
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "GROUP_NAME": "",
                        "VALUES": [{"OPT_FLAG": True, "DISPLACEMENT": 0.02},
                                   {"OPT_FLAG": False, "DISPLACEMENT": 0},
                                   {"OPT_FLAG": False, "DISPLACEMENT": 0},
                                   {"OPT_FLAG": False, "DISPLACEMENT": 0},
                                   {"OPT_FLAG": False, "DISPLACEMENT": 0},
                                   {"OPT_FLAG": False, "DISPLACEMENT": 0}]}]},
            lambda p: p["ITEMS"][0]["VALUES"][0].get("DISPLACEMENT"), 0.01, 0.02,
            item_id=1, confirmed=True,
        ),
        Case(
            LoadsToMass,
            {"DIR": "XYZ", "bNODAL": True, "bBEAM": True, "bFLOOR": False,
             "bPRES": False, "GRAV": 9.806,
             "vLC": [{"LCNAME": "LC_SCRATCH", "FACTOR": 1.0}]},
            {"DIR": "XYZ", "bNODAL": True, "bBEAM": True, "bFLOOR": False,
             "bPRES": False, "GRAV": 9.806,
             "vLC": [{"LCNAME": "LC_SCRATCH", "FACTOR": 0.5}]},
            lambda p: p["vLC"][0].get("FACTOR"), 1.0, 0.5,
            confirmed=True,
        ),
        Case(
            NodalBodyForce,
            {"LCNAME": "LC_SCRATCH", "OPT_USE_GROUP": False, "KEY_NODE_ITEMS": [2, 3],
             "OPT_NODAL_MASS": True, "OPT_LOAD_TO_MASS": False, "OPT_STRUCT_MASS": True,
             "X": 1.0, "Y": 0, "Z": 0},
            {"LCNAME": "LC_SCRATCH", "OPT_USE_GROUP": False, "KEY_NODE_ITEMS": [2, 3],
             "OPT_NODAL_MASS": True, "OPT_LOAD_TO_MASS": False, "OPT_STRUCT_MASS": True,
             "X": 2.0, "Y": 0, "Z": 0},
            lambda p: p.get("X"), 1.0, 2.0,
            confirmed=True,
        ),
        Case(
            FloorLoadType,
            {"NAME": "FL_CRUD", "DESC": "",
             "ITEM": [{"LCNAME": "LC_SCRATCH", "FLOOR_LOAD": -5.0,
                       "OPT_SUB_BEAM_WEIGHT": False}]},
            {"NAME": "FL_CRUD", "DESC": "",
             "ITEM": [{"LCNAME": "LC_SCRATCH", "FLOOR_LOAD": -8.0,
                       "OPT_SUB_BEAM_WEIGHT": False}]},
            lambda p: p["ITEM"][0].get("FLOOR_LOAD"), -5.0, -8.0,
            confirmed=True,
        ),
        # The manual spells ELEM_TYPE "Plate/PlaneStress(Face)" in its worked
        # example and "Plate/Plane Stress (Face)" in its Specifications prose.
        # Both are accepted (checked 2026-07-26 on v2.2), so the inconsistency
        # is cosmetic. An earlier note here claimed the unspaced form was "the
        # one the server accepts" - that was inferred from this case passing,
        # without ever sending the spaced form. Don't infer an enum from one
        # value working.
        Case(
            PressureLoadType,
            {"NAME": "PL_CRUD", "DESC": "", "ELEM_TYPE": "Plate/PlaneStress(Face)",
             "PRESSURE_LOAD_ITEMS": [{"LOADCASENAME": "LC_SCRATCH",
                                      "LOADTYPE": "Uniform", "LOAD_P1": -20}]},
            {"NAME": "PL_CRUD", "DESC": "", "ELEM_TYPE": "Plate/PlaneStress(Face)",
             "PRESSURE_LOAD_ITEMS": [{"LOADCASENAME": "LC_SCRATCH",
                                      "LOADTYPE": "Uniform", "LOAD_P1": -30}]},
            lambda p: p["PRESSURE_LOAD_ITEMS"][0].get("LOAD_P1"), -20, -30,
            confirmed=True,
        ),
        # Keyed by element id — 4 is the seeded plate.
        #
        # ⚠️ DIRECTION is "LZ", not the documented default "NORMAL". On a PLATE
        # with FACE_EDGE_TYPE="FACE", "NORMAL" is rejected ("[Error] Errors
        # detected in Pressure Loads Data.(Item:Load Direction)") and omitting
        # DIRECTION fails the same way, so the default is a trap. Verified
        # 2026-07-26: LZ / LX / GZ / VECTOR all work.
        Case(
            PressureLoad,
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "GROUP_NAME": "",
                        "CMD": "PRES", "ELEM_TYPE": "PLATE",
                        "FACE_EDGE_TYPE": "FACE", "DIRECTION": "LZ",
                        "EDGE_FACE": 1,
                        "FORCES": [-10.0, -10.0, -10.0, -10.0]}]},
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "GROUP_NAME": "",
                        "CMD": "PRES", "ELEM_TYPE": "PLATE",
                        "FACE_EDGE_TYPE": "FACE", "DIRECTION": "LZ",
                        "EDGE_FACE": 1,
                        "FORCES": [-20.0, -20.0, -20.0, -20.0]}]},
            lambda p: p["ITEMS"][0]["FORCES"][0], -10.0, -20.0,
            item_id=4, confirmed=True,
        ),
        # ch07: element and nodal temperature, the two temperature loads a
        # normal modelling script actually writes.
        Case(
            ElementTemperature,
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "GROUP_NAME": "", "TEMP": 35}]},
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "GROUP_NAME": "", "TEMP": 20}]},
            lambda p: p["ITEMS"][0].get("TEMP"), 35, 20,
            item_id=1, confirmed=True,
        ),
        Case(
            NodalTemperature,
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "GROUP_NAME": "", "TEMPER": -3}]},
            {"ITEMS": [{"ID": 1, "LCNAME": "LC_SCRATCH", "GROUP_NAME": "", "TEMPER": 5}]},
            lambda p: p["ITEMS"][0].get("TEMPER"), -3, 5,
            item_id=3, confirmed=True,
        ),
        # Un-quarantined 2026-07-29 after 15+ crash reproductions across both
        # products led to the actual root cause: the server crashes when
        # NMAS's optional rmX/rmY/rmZ fields are omitted, and doesn't when
        # they're sent explicitly (even as 0.0). NodalMass.create()/.update()
        # now fill them in automatically, so this case - which posts through
        # those methods without ever setting them - exercises the fix
        # directly instead of triggering the defect. Confirmed as a clean
        # 9/9 static-tier round trip on Gen NX the same day. See
        # docs/live_verification_notes.md for the full reproduction history.
        Case(
            NodalMass,
            {"mX": 1.0, "mY": 1.0, "mZ": 1.0},
            {"mX": 1.0, "mY": 1.0, "mZ": 2.0},
            lambda p: p.get("mZ"), 1.0, 2.0,
            item_id=3, confirmed=True,
        ),
    ]


# --------------------------------------------------------------------------
# Tier: stage — construction stages and what attaches to them.
# --------------------------------------------------------------------------


def _stage_seeds() -> List[SeedStep]:
    """Groups are referenced by *name* by /db/STAG, so their ids don't matter
    and the core tier's group cases can't interfere.

    The seeded stage deliberately activates nothing: a structure group can
    only be activated once across the whole stage sequence, so leaving it
    empty keeps SG_SEED free for the /db/STAG case below.
    """
    def _groups(c: MidasClient) -> None:
        StructureGroup.create({2: {"NAME": "SG_SEED"}}, client=c)
        BoundaryGroup.create({2: {"NAME": "BG_SEED"}}, client=c)
        LoadGroup.create({1: {"NAME": "LG_SEED"}}, client=c)

    return [
        SeedStep("groups", _groups),
        SeedStep("stage_1", lambda c: ConstructionStage.create(
            {1: {"NAME": "CS_SEED", "DURATION": 5, "bSV_RSLT": True,
                 "bSV_STEP": False, "bLOAD_STEP": False, "ADD_STEP": []}}, client=c)),
    ]


def _stage_cases() -> List[Case]:
    return [
        # id 2: stage 1 is CS_SEED, which /db/TMLD and /db/CRPC attach to.
        Case(
            ConstructionStage,
            {"NAME": "CS_CRUD", "DURATION": 10, "bSV_RSLT": True, "bSV_STEP": False,
             "bLOAD_STEP": False, "ADD_STEP": [],
             "ACT_ELEM": [{"GRUP_NAME": "SG_SEED", "AGE": 10}],
             "ACT_BNGR": [{"BNGR_NAME": "BG_SEED", "POS": "DEFORMED"}],
             "ACT_LOAD": [{"LOAD_NAME": "LG_SEED", "DAY": "FIRST"}]},
            {"NAME": "CS_CRUD", "DURATION": 20, "bSV_RSLT": True, "bSV_STEP": False,
             "bLOAD_STEP": False, "ADD_STEP": [],
             "ACT_ELEM": [{"GRUP_NAME": "SG_SEED", "AGE": 10}],
             "ACT_BNGR": [{"BNGR_NAME": "BG_SEED", "POS": "DEFORMED"}],
             "ACT_LOAD": [{"LOAD_NAME": "LG_SEED", "DAY": "FIRST"}]},
            lambda p: p.get("DURATION"), 10, 20,
            item_id=2, confirmed=True, needs=("groups",),
        ),
        # Keyed by construction stage id.
        Case(
            TimeLoadConstructionStage,
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "LG_SEED", "DAY": 35}]},
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "LG_SEED", "DAY": 25}]},
            lambda p: p["ITEMS"][0].get("DAY"), 35, 25,
            item_id=1, confirmed=True, needs=("groups", "stage_1"),
        ),
        Case(
            CreepCoefficientConstructionStage,
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "LG_SEED", "CREEP": 1.2}]},
            {"ITEMS": [{"ID": 1, "GROUP_NAME": "LG_SEED", "CREEP": 1.5}]},
            lambda p: p["ITEMS"][0].get("CREEP"), 1.2, 1.5,
            item_id=1, confirmed=True, needs=("groups", "stage_1"),
        ),
        # Keyed by node id. Civil NX only as of 2026-07-29 — see
        # CamberConstructionStage's docstring.
        Case(
            CamberConstructionStage,
            {"DEFORM": 0.0, "USER": 0.17},
            {"DEFORM": 0.0, "USER": 0.28},
            lambda p: p.get("USER"), 0.17, 0.28,
            item_id=3, products=("civil",), confirmed=True, needs=("stage_1",),
        ),
    ]


# --------------------------------------------------------------------------
# Tier: moving — the moving-load chain, now AASHTO LRFD fixtures throughout
# (MVCD "AASHTO LRFD", vehicles keyed to "AASHTO-LRFD"/HL-93). Was
# Korea-standard (MVCD "KOREA", vehicles keyed to "KS-RB") through
# 2026-07-29: live-tested that day, /db/MVCD itself creates fine on Gen for
# "AASHTO STANDARD"/"AASHTO LRFD"/"EUROCODE"/"BS" but answers `[Error] ...
# Unavailable moving load code` for "KOREA"/"CHINA"/"KSCE-LSD15" —
# presumably a licensed-module gate per region code, not a route-level
# restriction. Rebuilt 2026-07-30 around AASHTO LRFD/HL-93 after
# cross-checking this exact fixture shape against a real production Civil
# NX arch-bridge model's live AASHTO LRFD data (see
# docs/live_verification_notes.md) — field-for-field identical to what a
# real bridge project stores, not an invented example. Still `products=civil`
# here: the chain answers on Gen too per the 32-endpoint mirror finding (all
# of ch08 does), and AASHTO codes are the ones confirmed *not* gated by the
# region-code lock, so this should now pass unchanged on Gen — but that is
# an expectation, not yet something watched pass live. Widen `products` and
# flip `confirmed` only once someone actually runs this against a Gen
# session.
# --------------------------------------------------------------------------


def _moving_seeds() -> List[SeedStep]:
    """Rebuilds the code the core tier's /db/MVCD case deleted, then the lane
    and vehicle that /db/MVLD and /db/MVHC reference by name.

    ⚠️ Do not send ``VEH_DEFAULT: {}``. Every one of its fields is documented
    as optional, but an empty object makes ``/db/MVHL`` silently no-op —
    ``{"message": ""}``, no error, and a following GET shows nothing was
    saved. Verified live; see docs/live_verification_notes.md.

    ⚠️ With ``MVCD.CODE="AASHTO LRFD"``, ``LineLaneItem``'s ``CENT_F`` must be
    a nonzero value in (0, 1) — omitting it (or leaving the field's own
    documented default of 0) is rejected server-side with "Centrifugal
    Force ( 0.0 < Value < 1.0)". See ``LineLaneItem``'s docstring in
    ``db/moving_loads.py``, independently reconfirmed against a real
    production model's own data (``CENT_F: 0.5``) on 2026-07-30.
    """
    return [
        SeedStep("mvcd", lambda c: MovingLoadCode.create({1: {"CODE": "AASHTO LRFD"}}, client=c)),
        SeedStep("lane", lambda c: TrafficLineLanes.create(
            {1: {"COMMON": {"LL_NAME": "LL_SEED", "LOAD_DIST": "LANE", "GROUP_NAME": "",
                            "SKEW_START": 0, "SKEW_END": 0, "MOVING": "BOTH",
                            "WHEEL_SPACE": 1.8, "WIDTH": 3, "OPT_AUTO_LANE": False},
                 "LANE_ITEMS": [{"ELEM": 2, "ECC": 0, "CENT_F": 0.5},
                                {"ELEM": 3, "ECC": 0, "CENT_F": 0.5}]}},
            client=c)),
        SeedStep("vehicle", lambda c: Vehicles.create(
            {1: {"MVLD_CODE": 2, "VEHICLE_LOAD_NAME": "HL93TRK_SEED",
                 "VEHICLE_LOAD_NUM": 1, "VEHICLE_TYPE_NAME": "HL-93TRK",
                 "STANDARD_CODE": "AASHTO-LRFD",
                 "VEH_DEFAULT": {"DYN_LOAD_ALLOWANCE": 33, "CENT_F": False}}},
            client=c)),
    ]


def _moving_cases() -> List[Case]:
    civil = ("civil",)
    return [
        # id 2: lane 1 is LL_SEED, which the /db/MVLD case references.
        Case(
            TrafficLineLanes,
            {"COMMON": {"LL_NAME": "LL_CRUD", "LOAD_DIST": "LANE", "GROUP_NAME": "",
                        "SKEW_START": 0, "SKEW_END": 0, "MOVING": "BOTH",
                        "WHEEL_SPACE": 1.8, "WIDTH": 3, "OPT_AUTO_LANE": False},
             "LANE_ITEMS": [{"ELEM": 2, "ECC": 0.0, "CENT_F": 0.5},
                            {"ELEM": 3, "ECC": 0.0, "CENT_F": 0.5}]},
            {"COMMON": {"LL_NAME": "LL_CRUD", "LOAD_DIST": "LANE", "GROUP_NAME": "",
                        "SKEW_START": 0, "SKEW_END": 0, "MOVING": "BOTH",
                        "WHEEL_SPACE": 1.8, "WIDTH": 3, "OPT_AUTO_LANE": False},
             "LANE_ITEMS": [{"ELEM": 2, "ECC": 0.5, "CENT_F": 0.5},
                            {"ELEM": 3, "ECC": 0.5, "CENT_F": 0.5}]},
            lambda p: p["LANE_ITEMS"][0].get("ECC"), 0.0, 0.5,
            item_id=2, products=civil, confirmed=True, needs=("mvcd",),
        ),
        # id 2: vehicle 1 is the seeded HL-93TRK the class/case reference.
        #
        # ⚠️ VEHICLE_LOAD_NUM must be 1 for a standard vehicle. Sending 2
        # (verified live 2026-07-26, on the Korea-standard fixture this
        # replaced) makes NX **silently discard** VEHICLE_TYPE_NAME and
        # STANDARD_CODE and store the record as a user-defined "Truck/Lane"
        # vehicle instead — 200, no error, and the only way to notice is to
        # read the record back. Same failure shape as /db/CONS truncating an
        # 8-character CONSTRAINT.
        Case(
            Vehicles,
            {"MVLD_CODE": 2, "VEHICLE_LOAD_NAME": "HL93TDM_CRUD",
             "VEHICLE_LOAD_NUM": 1, "VEHICLE_TYPE_NAME": "HL-93TDM",
             "STANDARD_CODE": "AASHTO-LRFD",
             "VEH_DEFAULT": {"DYN_LOAD_ALLOWANCE": 33, "CENT_F": False}},
            {"MVLD_CODE": 2, "VEHICLE_LOAD_NAME": "HL93TDM_CRUD",
             "VEHICLE_LOAD_NUM": 1, "VEHICLE_TYPE_NAME": "HL-93TDM",
             "STANDARD_CODE": "AASHTO-LRFD",
             "VEH_DEFAULT": {"DYN_LOAD_ALLOWANCE": 20, "CENT_F": False}},
            lambda p: p["VEH_DEFAULT"].get("DYN_LOAD_ALLOWANCE"), 33, 20,
            item_id=2, products=civil, confirmed=True, needs=("mvcd",),
        ),
        # VEHICLE_LD_NAMES takes the vehicle's VEHICLE_LOAD_NAME, not the
        # type name the manual's worked example shows — confirmed live
        # 2026-07-26 on the Korea-standard fixture this replaced.
        Case(
            VehicleClasses,
            {"VEHICLE_CLS_NAME": "VC_CRUD", "VEHICLE_LD_NAMES": ["HL93TRK_SEED"]},
            {"VEHICLE_CLS_NAME": "VC_CRUD_2", "VEHICLE_LD_NAMES": ["HL93TRK_SEED"]},
            lambda p: p.get("VEHICLE_CLS_NAME"), "VC_CRUD", "VC_CRUD_2",
            products=civil, confirmed=True, needs=("mvcd", "vehicle"),
        ),
        Case(
            MovingLoadCase,
            {"LCNAME": "MV_CRUD", "DESC": "", "TYPE": 0,
             "DEFAULT": {"LANE_FACTOR_TYPE": 1,
                         "SCALE_FACTORS": [1.2, 1, 0.85, 0.65, 0.65, 0.65],
                         "COMB_OPTION": "INDEPENDENT",
                         "SUB_LOAD_DATAS": [{"VEHICLE_TYPE": "VL",
                                             "VEHICLE_NAME": "HL93TRK_SEED",
                                             "SCALE_FACTOR": 1.0,
                                             "MIN_LOADED_LANE": 1,
                                             "MAX_LOADED_LANE": 1,
                                             "LANE_NAMES": ["LL_SEED"]}]}},
            {"LCNAME": "MV_CRUD", "DESC": "", "TYPE": 0,
             "DEFAULT": {"LANE_FACTOR_TYPE": 1,
                         "SCALE_FACTORS": [1.2, 1, 0.85, 0.65, 0.65, 0.65],
                         "COMB_OPTION": "INDEPENDENT",
                         "SUB_LOAD_DATAS": [{"VEHICLE_TYPE": "VL",
                                             "VEHICLE_NAME": "HL93TRK_SEED",
                                             "SCALE_FACTOR": 0.8,
                                             "MIN_LOADED_LANE": 1,
                                             "MAX_LOADED_LANE": 1,
                                             "LANE_NAMES": ["LL_SEED"]}]}},
            lambda p: p["DEFAULT"]["SUB_LOAD_DATAS"][0].get("SCALE_FACTOR"), 1.0, 0.8,
            products=civil, confirmed=True, needs=("mvcd", "lane", "vehicle"),
        ),
    ]


# --------------------------------------------------------------------------
# Tier: extras1 — batch 1 of the read-only-verified db.project/db.boundary
# endpoints (2026-08-16): project-wide singleton settings, name-only groups,
# and the general-link family. Deliberately excludes the 5 seismic-device
# endpoints (SDVI/SDVE/SDST/SDHY/SDIS) and DRLS — nested COMMON payloads and
# an empty-object payload respectively need their own fixture work first.
# --------------------------------------------------------------------------


def _extras1_seeds() -> List[SeedStep]:
    """Isolated from the core/boundary tiers' own nodes: a fresh 23-26 node
    quartet so this tier is runnable standalone. 23/24 back the NLNK/NLNK-M1
    *cases* (each overwrites the same pair, different element ids); 25/26
    back a general-link *seed* record that outlives those cases, for CGLP.

    ``pjcf_unlock``: a fresh document already carries a /db/PJCF record at
    id 1 (confirmed live 2026-08-16, Civil NX v2.2 build 08/14/2026 —
    ``ProjectInfo.items()`` returns a non-empty placeholder before any case
    runs). Its POST/DELETE are documented, but POST answers "Key Already
    Exist" for *any* id, not just 1, until that pre-existing record is
    deleted first -- a real singleton, same family as UNIT/STYP, just with
    DELETE as the unlock instead of being GET/PUT-only.

    ``fbld_seed``: /db/CO_F is keyed by a Floor Load Type id, and the base
    model seeds none, so a bare PUT 404s ("id 1 missing after update" --
    confirmed live 2026-08-16). /db/FBLD also renumbers to the next free
    slot rather than honouring the "Assign" key (same behaviour as
    /db/STLD, see the props tier's own note) -- it lands at id 1 in a
    fresh document regardless of the id requested here, so the CO_F case
    below targets id 1 to match.
    """
    return [
        SeedStep("extras1_nodes", lambda c: Node.create(
            {23: {"X": 0, "Y": 3 * BAY, "Z": 0}, 24: {"X": 0, "Y": 3 * BAY, "Z": HEIGHT},
             25: {"X": BAY, "Y": 3 * BAY, "Z": 0}, 26: {"X": BAY, "Y": 3 * BAY, "Z": HEIGHT}},
            client=c)),
        SeedStep("pjcf_unlock", lambda c: ProjectInfo.delete([1], client=c)),
        SeedStep("fbld_seed", lambda c: FloorLoadType.create(
            {1: {"NAME": "FL_SEED", "DESC": "",
                 "ITEM": [{"LCNAME": "LC_SCRATCH", "FLOOR_LOAD": -5.0,
                           "OPT_SUB_BEAM_WEIGHT": False}]}},
            client=c)),
        # ⚠️ Confirmed failing live 2026-08-16 (Civil NX v2.2, build
        # 08/14/2026) with the manual's own request-example payload
        # reproduced verbatim (PROPERTY_NAME/DESC/APPLICATION_TYPE=ELEMENT/
        # APPLICATION_TYPE_D=SPG/TOTAL_WEIGHT/OPT_USE_MASS), on both a
        # partially-seeded and a completely fresh /doc/NEW document -- same
        # generic "Unknown Error" both times. Not a fixture bug this
        # checker can iterate past; something about /db/NLLP's own
        # preconditions is undocumented. Left in (unconfirmed) so this
        # blocks NLNK/NLNK-M1/CGLP visibly rather than silently.
        SeedStep("nllp_seed", lambda c: GeneralLinkProperty.create(
            {90: {"PROPERTY_NAME": "NLLP_SEED", "APPLICATION_TYPE": "ELEMENT",
                  "APPLICATION_TYPE_D": "SPG"},
             91: {"PROPERTY_NAME": "NLLP_SEED_2", "APPLICATION_TYPE": "ELEMENT",
                  "APPLICATION_TYPE_D": "SPG"}},
            client=c)),
        SeedStep("glink_seed", lambda c: GeneralLink.create(
            {90: {"NODE1": 25, "NODE2": 26, "PROP_NAME": "NLLP_SEED",
                  "REF_SYSTEM": 0, "BETA_ANGLE": 0}},
            client=c)),
    ]


def _extras1_cases() -> List[Case]:
    civil = ("civil",)
    return [
        Case(
            ProjectInfo,
            {"PROJECT": "CRUD_TEST", "USER": "crud"},
            {"PROJECT": "CRUD_TEST_2", "USER": "crud"},
            lambda p: p.get("PROJECT"), "CRUD_TEST", "CRUD_TEST_2",
            needs=("pjcf_unlock",), confirmed=True,
        ),
        # GET/PUT only, no POST/DELETE — the record already exists at id 1
        # in a fresh document (same pattern _seed_model relies on for Unit).
        # MASS must be 1 (Lumped) or 2 (Consistent) -- 0 answers "Wrong
        # Field" (confirmed live 2026-08-16; the manual's own Specifications
        # table calls it Optional with no stated default, but doesn't list 0
        # as a valid value either, only 1/2).
        Case(
            StructureType,
            {}, {"STYP": 0, "MASS": 1, "bMASSOFFSET": False, "bSELFWEIGHT": True,
                 "SMASS": 2, "GRAV": 9.806, "TEMP": 20, "bALIGNBEAM": False,
                 "bALIGNSLAB": False, "bROTRIGID": True},
            lambda p: p.get("TEMP"), None, 20,
            confirmed=True,
        ),
        Case(
            StructureTypeHyperS,
            {}, {"STYPE": "3D", "GRAV": 9.806, "TEMP": 0, "ALIGNBEAM": False,
                 "ALIGNSLAB": False,
                 "MASS_CONTROL": {"MASS_TYPE": "LUMPED", "MASS_POS": "CENTROID",
                                  "SELFWEIGHT": False}},
            lambda p: p.get("STYPE"), None, "3D",
            products=civil, confirmed=True,
        ),
        Case(
            TendonGroup,
            {"NAME": "TG_CRUD"}, {"NAME": "TG_CRUD_2"},
            lambda p: p.get("NAME"), "TG_CRUD", "TG_CRUD_2",
            confirmed=True,
        ),
        Case(
            NamedPlane,
            {"NAME": "NP_CRUD", "TYPE": 2, "COORD": 5.0},
            {"NAME": "NP_CRUD", "TYPE": 2, "COORD": 10.0},
            lambda p: p.get("COORD"), 5.0, 10.0,
            confirmed=True,
        ),
        # CO_M/CO_S/CO_T keyed by the material/section/thickness id they
        # colour — reuse the base seed's id-1 material/section/thickness.
        Case(
            MaterialColor,
            {}, {"W_R": 111, "W_G": 142, "W_B": 91, "bBLEMD": False, "FACT": 0.5},
            lambda p: p.get("W_R"), None, 111,
            item_id=1, confirmed=True,
        ),
        Case(
            SectionColor,
            {}, {"W_R": 111, "W_G": 142, "W_B": 91, "bBLEMD": False, "FACT": 0.5},
            lambda p: p.get("W_R"), None, 111,
            item_id=1, confirmed=True,
        ),
        Case(
            ThicknessColor,
            {}, {"W_R": 111, "W_G": 142, "W_B": 91, "bBLEMD": False, "FACT": 0.5},
            lambda p: p.get("W_R"), None, 111,
            item_id=1, confirmed=True,
        ),
        # CO_F is keyed by a Floor Load Type (/db/FBLD) id -- the fbld_seed
        # step provides one, landing at id 1 (FBLD renumbers, see the seed
        # docstring above). Its own "NAME" field is read-only, mirroring
        # the linked FBLD record's name (confirmed live 2026-08-16: a PUT
        # with NAME="FL_CRUD" echoed back "FL_SEED" unchanged) -- probe a
        # colour field instead, like CO_M/CO_S/CO_T.
        Case(
            FloorLoadColor,
            {}, {"NAME": "FL_CRUD", "WF_R": 166, "OPT_BLEND": True, "BLEND_FACTOR": 0.25},
            lambda p: p.get("WF_R"), None, 166,
            item_id=1, needs=("fbld_seed",), confirmed=True,
        ),
        # SPAN_BASE_ITEMS.length must be SPAN_LIST.length + 1 (one support
        # point per span boundary) -- confirmed live 2026-08-16 after a
        # 2-items/3-list mismatch answered "[Error] ... (Item:Number of
        # Spans)"; the manual's own Specifications table doesn't state this
        # relationship, only its JSON Schema shows two independently-typed
        # arrays.
        Case(
            Span,
            {"NAME": "SPAN_CRUD", "bEXACTSPAN": True, "DIRECTION": 0, "SECTTYPE": 0,
             "SPAN_LIST": [2.5, 5],
             "SPAN_BASE_ITEMS": [{"ELEM_KEY": 1, "SUPPORT": 1}, {"ELEM_KEY": 2, "SUPPORT": 1},
                                  {"ELEM_KEY": 3, "SUPPORT": 2}]},
            {"NAME": "SPAN_CRUD_2", "bEXACTSPAN": True, "DIRECTION": 0, "SECTTYPE": 0,
             "SPAN_LIST": [2.5, 5],
             "SPAN_BASE_ITEMS": [{"ELEM_KEY": 1, "SUPPORT": 1}, {"ELEM_KEY": 2, "SUPPORT": 1},
                                  {"ELEM_KEY": 3, "SUPPORT": 2}]},
            lambda p: p.get("NAME"), "SPAN_CRUD", "SPAN_CRUD_2",
            products=civil, confirmed=True,
        ),
        Case(
            GeneralLinkProperty,
            {"PROPERTY_NAME": "NLLP_CRUD", "APPLICATION_TYPE": "ELEMENT", "APPLICATION_TYPE_D": "SPG"},
            {"PROPERTY_NAME": "NLLP_CRUD_2", "APPLICATION_TYPE": "ELEMENT", "APPLICATION_TYPE_D": "SPG"},
            lambda p: p.get("PROPERTY_NAME"), "NLLP_CRUD", "NLLP_CRUD_2",
        ),
        Case(
            GeneralLink,
            {"NODE1": 23, "NODE2": 24, "PROP_NAME": "NLLP_SEED", "REF_SYSTEM": 0, "BETA_ANGLE": 0},
            {"NODE1": 23, "NODE2": 24, "PROP_NAME": "NLLP_SEED", "REF_SYSTEM": 0, "BETA_ANGLE": 15},
            lambda p: p.get("BETA_ANGLE"), 0, 15,
            needs=("nllp_seed", "extras1_nodes"),
        ),
        Case(
            GeneralLinkHyperS,
            {"PROP_NAME": "NLLP_SEED", "NODE1": 23, "NODE2": 24},
            {"PROP_NAME": "NLLP_SEED_2", "NODE1": 23, "NODE2": 24},
            lambda p: p.get("PROP_NAME"), "NLLP_SEED", "NLLP_SEED_2",
            item_id=2, products=civil, needs=("nllp_seed", "extras1_nodes"),
        ),
        Case(
            ChangeGeneralLinkProperty,
            {"GLINK_KEY": 90, "CHANGE_PROPERTY_NAME": "NLLP_SEED"},
            {"GLINK_KEY": 90, "CHANGE_PROPERTY_NAME": "NLLP_SEED_2"},
            lambda p: p.get("CHANGE_PROPERTY_NAME"), "NLLP_SEED", "NLLP_SEED_2",
            needs=("nllp_seed", "glink_seed"),
        ),
        # Element 4 is the base seed's plate.
        Case(
            PlateEndRelease,
            {"ITEMS": [{"ID": 1, "N1": [1, 1, 1, 0, 0], "N2": [0, 0, 0, 0, 0],
                        "N3": [0, 0, 0, 0, 0], "N4": [0, 0, 0, 0, 0]}]},
            {"ITEMS": [{"ID": 1, "N1": [1, 1, 1, 1, 0], "N2": [0, 0, 0, 0, 0],
                        "N3": [0, 0, 0, 0, 0], "N4": [0, 0, 0, 0, 0]}]},
            lambda p: p["ITEMS"][0].get("N1"), [1, 1, 1, 0, 0], [1, 1, 1, 1, 0],
            item_id=4, confirmed=True,
        ),
        Case(
            ForceDeformationFunction,
            {"NAME": "MLFC_CRUD", "TYPE": "FORCE", "SYMM": False,
             "ITEMS": [{"X": 0.0, "Y": 0.0}, {"X": 0.01, "Y": 100.0}, {"X": 0.02, "Y": 150.0}]},
            {"NAME": "MLFC_CRUD_2", "TYPE": "FORCE", "SYMM": False,
             "ITEMS": [{"X": 0.0, "Y": 0.0}, {"X": 0.01, "Y": 100.0}, {"X": 0.02, "Y": 150.0}]},
            lambda p: p.get("NAME"), "MLFC_CRUD", "MLFC_CRUD_2",
            confirmed=True,
        ),
        Case(
            PanelZoneEffect,
            {"OPT_OFFSET": False, "OFFS_FACTOR": 0.5, "OUTPUT_POSITION": 0},
            {"OPT_OFFSET": True, "OFFS_FACTOR": 0.75, "OUTPUT_POSITION": 0},
            lambda p: p.get("OFFS_FACTOR"), 0.5, 0.75,
            confirmed=True,
        ),
        # No DELETE (NO_DELETE_METHODS), keyed by node id — node 1 already
        # has a /db/CONS record, an unrelated table, so no collision.
        Case(
            ConstraintLabelDirection,
            {"DIR": 0}, {"DIR": 2},
            lambda p: p.get("DIR"), 0, 2,
            confirmed=True,
        ),
    ]


#: Priority order — what a modelling script needs, not the manual's order.
TIERS: List[Tier] = [
    Tier("core", "baseline model, groups and static loads", _no_seeds, _core_cases),
    Tier("props", "material / section sub-types", _props_seeds, _props_cases),
    Tier("boundary", "springs and links", _boundary_seeds, _boundary_cases),
    Tier("static", "remaining static loads + temperature", _no_seeds, _static_cases),
    Tier("stage", "construction stages", _stage_seeds, _stage_cases),
    Tier("moving", "moving loads (AASHTO LRFD fixtures; Civil-confirmed, Gen not yet watched live)", _moving_seeds, _moving_cases),
    Tier("extras1", "batch 1 of read-only-verified db.project/db.boundary endpoints", _extras1_seeds, _extras1_cases),
]


def _run_case(case: Case, client: MidasClient) -> Dict[str, Any]:
    res = case.resource
    row: Dict[str, Any] = {
        "endpoint": res.ENDPOINT,
        "name": res.NAME,
        "id": case.item_id,
        "confirmed": case.confirmed,
        "steps": {},
    }

    def record(step: str, fn) -> Any:
        try:
            value = fn()
        except MidasAPIError as exc:
            row["steps"][step] = {"ok": False, "error": str(exc)[:200]}
            raise
        row["steps"][step] = {"ok": True}
        return value

    def read_probe(expected, label):
        got = res.items(client=client).get(case.item_id)
        if got is None:
            raise MidasAPIError(f"{res.ENDPOINT}: id {case.item_id} missing after {label}")
        actual = case.probe(got)
        if actual != expected:
            raise MidasAPIError(
                f"{res.ENDPOINT}: {label} {expected!r}, read back {actual!r}"
            )
        return actual

    try:
        if "POST" in res.METHODS:
            record("create", lambda: res.create({case.item_id: case.create_payload},
                                                client=client))
            record("read_back", lambda: read_probe(case.expect_created, "wrote"))
        else:
            row["steps"]["create"] = {"ok": True, "skipped": "endpoint has no POST"}

        if "PUT" in res.METHODS:
            record("update", lambda: res.update({case.item_id: case.update_payload},
                                                client=client))
            record("read_updated", lambda: read_probe(case.expect_updated, "updated to"))
        else:
            row["steps"]["update"] = {"ok": True, "skipped": "endpoint has no PUT"}

        if "DELETE" in res.METHODS:
            record("delete", lambda: res.delete([case.item_id], client=client))

            def check_deleted():
                if case.item_id in res.items(client=client):
                    raise MidasAPIError(
                        f"{res.ENDPOINT}: id {case.item_id} still present after delete"
                    )
                return True

            record("read_deleted", check_deleted)
        else:
            row["steps"]["delete"] = {"ok": True, "skipped": "endpoint has no DELETE"}
    except MidasAPIError:
        pass

    row["ok"] = all(step.get("ok") for step in row["steps"].values())
    row["classification"] = OK if row["ok"] else (REGRESSION if case.confirmed
                                                  else UNVERIFIED)
    return row


def _session_lost(row: Dict[str, Any]) -> bool:
    """Did this failure mean the product is gone, rather than that the call
    was rejected?

    Learned the hard way on 2026-07-26: Civil NX died mid-run, and the run
    then spent two 30s timeouts and six 404s grinding through cases that
    never had a chance. The relay answers ``404 client does not exist`` once
    the process is gone, and a read timeout is what you get while it is
    dying. Either way there is nothing left to test, so stop and say so —
    reporting 8 "failures" against a corpse is exactly the false-positive
    noise this report is built to avoid.
    """
    for step in row["steps"].values():
        error = str(step.get("error", ""))
        if "client does not exist" in error or "Read timed out" in error:
            return True
    return False


def _stub_row(case: Case, classification: str, reason: str) -> Dict[str, Any]:
    return {
        "endpoint": case.resource.ENDPOINT,
        "name": case.resource.NAME,
        "id": case.item_id,
        "confirmed": case.confirmed,
        "steps": {},
        "ok": False,
        "classification": classification,
        "blocked_by": reason,
    }


def _mark(row: Dict[str, Any]) -> str:
    return {OK: "PASS", REGRESSION: "REGRESS", UNVERIFIED: "FAIL",
            BLOCKED: "BLOCK", SKIPPED: "SKIP"}[row["classification"]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=["gen", "civil"], required=True)
    parser.add_argument("--mapi-key", help="defaults to MIDAS_MAPI_KEY env var")
    parser.add_argument("--base-url", help="defaults to MIDAS_BASE_URL env var")
    parser.add_argument(
        "--tier",
        help="comma-separated tiers to run, in priority order: "
        + ", ".join(t.name for t in TIERS) + " (default: all)",
    )
    parser.add_argument(
        "--save-as",
        help="save the currently open document here before /doc/NEW, so a "
        "save-changes dialog can't block the session",
    )
    parser.add_argument(
        "--include-crashers",
        action="store_true",
        help="also run cases quarantined for hanging or killing MIDAS NX "
        "(currently /db/NMAS). Expect to restart the product and to redo the "
        "license-recovery steps afterwards.",
    )
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--out", help="path to write the report JSON (optional)")
    args = parser.parse_args()

    tiers = TIERS
    if args.tier:
        wanted = [n.strip() for n in args.tier.split(",") if n.strip()]
        unknown = [n for n in wanted if n not in {t.name for t in TIERS}]
        if unknown:
            print(f"Unknown tier(s): {', '.join(unknown)}", file=sys.stderr)
            return 2
        tiers = [t for t in TIERS if t.name in wanted]

    client = MidasClient(
        mapi_key=args.mapi_key, base_url=args.base_url,
        product=args.product, timeout=args.timeout,
    )
    try:
        health = client.verify_connection()
    except MidasAPIError as exc:
        print(f"Could not reach the MIDAS NX Open API server: {exc}", file=sys.stderr)
        return 2
    if health.get("status") != "connected":
        print(f"Server reachable but not connected: {health}", file=sys.stderr)
        return 2

    if args.save_as:
        print(f"Saving the open document to {args.save_as} first...")
        doc.save_as(args.save_as, client=client)

    print("Creating a throwaway document and seeding a minimal model...")
    doc.new_project(client=client)
    try:
        _seed_model(client)
    except MidasAPIError as exc:
        print(f"Base seed failed, so nothing below it can be trusted: {exc}",
              file=sys.stderr)
        return 3

    product = client.product.value
    results: List[Dict[str, Any]] = []
    aborted = None
    for tier in tiers:
        if aborted:
            break
        cases = [c for c in tier.cases() if product in c.products]
        if not cases:
            continue
        print(f"\n[{tier.name}] {tier.title}")
        # Seed steps fail independently, and a case is only blocked by the
        # step it actually declared a need for.
        failed_seeds: Dict[str, str] = {}
        for step in tier.seeds():
            try:
                step.run(client)
            except MidasAPIError as exc:
                failed_seeds[step.name] = str(exc)[:160]
                print(f"  seed '{step.name}' failed: {failed_seeds[step.name]}")
        for case in cases:
            missing = [n for n in case.needs if n in failed_seeds]
            if case.crashes and not args.include_crashers:
                row = _stub_row(case, SKIPPED, case.crashes)
            elif missing:
                row = _stub_row(case, BLOCKED,
                                f"seed '{missing[0]}': {failed_seeds[missing[0]]}")
            else:
                row = _run_case(case, client)
            results.append(row)
            marks = " ".join(
                f"{name}={'ok' if step.get('ok') else 'FAIL'}"
                for name, step in row["steps"].items()
            )
            print(f"  {_mark(row):8}{row['endpoint']:12} {marks}")
            if _session_lost(row):
                aborted = (f"the product stopped answering at {row['endpoint']} — "
                           f"MIDAS NX is hung or gone, so nothing after this "
                           f"point was tested")
                print(f"\n!! ABORTED: {aborted}")
                break

    by_class = {k: [r for r in results if r["classification"] == k]
                for k in (OK, REGRESSION, UNVERIFIED, BLOCKED, SKIPPED)}
    report = {
        "product": product,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "connection": {k: health.get(k) for k in ("user", "program", "connectionID")},
        "tiers": [t.name for t in tiers],
        "aborted": aborted,
        "cases": len(results),
        "passed": len(by_class[OK]),
        "regressions": len(by_class[REGRESSION]),
        "unverified_failures": len(by_class[UNVERIFIED]),
        "blocked": len(by_class[BLOCKED]),
        "skipped": len(by_class[SKIPPED]),
        "results": results,
    }

    print()
    print(f"{len(by_class[OK])}/{len(results)} resources completed a full round trip.")
    if by_class[REGRESSION]:
        print(f"  {len(by_class[REGRESSION])} REGRESSION - a case that passed live "
              f"before now fails; treat as an SDK defect:")
        for r in by_class[REGRESSION]:
            print(f"      {r['endpoint']}")
    if by_class[UNVERIFIED]:
        print(f"  {len(by_class[UNVERIFIED])} unverified failure(s) - never passed "
              f"live; triage the fixture payload before blaming the SDK:")
        for r in by_class[UNVERIFIED]:
            print(f"      {r['endpoint']}")
    if by_class[BLOCKED]:
        print(f"  {len(by_class[BLOCKED])} blocked by a failed seed (fixture problem):")
        for r in by_class[BLOCKED]:
            print(f"      {r['endpoint']}")
    if by_class[SKIPPED]:
        print(f"  {len(by_class[SKIPPED])} quarantined, not run "
              f"(pass --include-crashers to run anyway):")
        for r in by_class[SKIPPED]:
            print(f"      {r['endpoint']} - {r['blocked_by']}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
        print(f"Report written to {args.out}")

    if by_class[REGRESSION]:
        return 1
    if by_class[UNVERIFIED] or by_class[BLOCKED]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
