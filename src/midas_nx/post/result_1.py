"""Source: docs/manual/19_POST_AnalysisResult_1.md, items 1-12, and
docs/manual/20_POST_AnalysisResult_2.md, items 1-38.

All functions POST to the shared /post/TABLE endpoint — see post/base.py.
"""
from __future__ import annotations

from typing import List, Optional

from ..client import MidasClient
from .base import NodeElemsSelector, TableStyles, TableUnit, get_table

# --- from 19_POST_AnalysisResult_1.md ---

# 1. Reaction — OPT_CS/STAGE_STEP not supported for the Local Surface Spring variant
TABLE_TYPE_REACTION_GLOBAL = "REACTIONG"
TABLE_TYPE_REACTION_LOCAL = "REACTIONL"
TABLE_TYPE_REACTION_LOCAL_SURFACE_SPRING = "REACTIONSURFACESPRING"

# 2. Displacements
TABLE_TYPE_DISPLACEMENT_GLOBAL = "DISPLACEMENTG"
TABLE_TYPE_DISPLACEMENT_LOCAL = "DISPLACEMENTL"

# 3. Truss Force
TABLE_TYPE_TRUSS_FORCE = "TRUSSFORCE"

# 4. Truss Stress
TABLE_TYPE_TRUSS_STRESS = "TRUSSSTRESS"

# 5. Cable Force
TABLE_TYPE_CABLE_FORCE = "CABLEFORCE"

# 6. Cable Configuration
TABLE_TYPE_CABLE_CONFIG = "CABLECONFIG"

# 7. Cable Efficiency
TABLE_TYPE_CABLE_EFFICIENCY = "CABLEEFFIENCY"  # sic — API spec spells it "EFFIENCY", not "EFFICIENCY"

# 8. Beam Force
TABLE_TYPE_BEAM_FORCE = "BEAMFORCE"
TABLE_TYPE_BEAM_FORCE_BY_MAX = "BEAMFORCEBYMAX"

# 9. Beam Force (Static Prestress)
TABLE_TYPE_BEAM_FORCE_STATIC_PRESTRESS = "BEAMFORCESIP"

# 10. Beam Stress
TABLE_TYPE_BEAM_STRESS = "BEAMSTRESS"
TABLE_TYPE_BEAM_STRESS_7DOF = "BEAMSTRESS7DOF"

# 11. Beam Stress (Equivalent)
TABLE_TYPE_BEAM_STRESS_DETAIL = "BEAMSTRESSDETAIL"

# 12. Beam Stress (PSC)
TABLE_TYPE_BEAM_STRESS_PSC = "BEAMSTRESSPSC"
TABLE_TYPE_BEAM_STRESS_7DOF_PSC = "BEAMSTRESS7DOFPSC"

# --- from 20_POST_AnalysisResult_2.md ---

# 1. Plate Force (Local)
TABLE_TYPE_PLATE_FORCE_LOCAL = "PLATEFORCEL"

# 2. Plate Force (Global)
TABLE_TYPE_PLATE_FORCE_GLOBAL = "PLATEFORCEG"

# 3. Plate Force (Unit Length) — local/global, by-max, and Wood-Armer design moment variants
TABLE_TYPE_PLATE_FORCE_UNIT_LENGTH_LOCAL = "PLATEFORCEUL"
TABLE_TYPE_PLATE_FORCE_UNIT_LENGTH_GLOBAL = "PLATEFORCEUG"
TABLE_TYPE_PLATE_FORCE_UNIT_LENGTH_LOCAL_BY_MAX = "PLATEFORCEULVBM"
TABLE_TYPE_PLATE_FORCE_UNIT_LENGTH_GLOBAL_BY_MAX = "PLATEFORCEUGVBM"
TABLE_TYPE_PLATE_FORCE_UNIT_LENGTH_WOOD_ARMER = "PLATEFORCEWA"

# 4. Plate Stress (Local)
TABLE_TYPE_PLATE_STRESS_LOCAL = "PLATESTRESSL"

# 5. Plate Stress (Global)
TABLE_TYPE_PLATE_STRESS_GLOBAL = "PLATESTRESSG"

# 6. Plate Strain (Local) — nonlinear/construction-stage Step results; use opt_cs/stage_step
TABLE_TYPE_PLATE_STRAIN_LOCAL_PLASTIC = "PLATESTRAINPL"
TABLE_TYPE_PLATE_STRAIN_LOCAL_TOTAL = "PLATESTRAINTL"

# 7. Plate Strain (Global) — nonlinear/construction-stage Step results; use opt_cs/stage_step
TABLE_TYPE_PLATE_STRAIN_GLOBAL_PLASTIC = "PLATESTRAINPG"
TABLE_TYPE_PLATE_STRAIN_GLOBAL_TOTAL = "PLATESTRAINTG"

# 8. Plane Stress Force (Local)
TABLE_TYPE_PLANE_STRESS_FORCE_LOCAL = "PLANESTRESSFL"

# 9. Plane Stress Force (Global)
TABLE_TYPE_PLANE_STRESS_FORCE_GLOBAL = "PLANESTRESSFG"

# 10. Plane Stress (Local)
TABLE_TYPE_PLANE_STRESS_LOCAL = "PLANESTRESSSL"

# 11. Plane Stress (Global)
TABLE_TYPE_PLANE_STRESS_GLOBAL = "PLANESTRESSSG"

# 12. Plane Strain Force (Local)
TABLE_TYPE_PLANE_STRAIN_FORCE_LOCAL = "PLANESTRAINFL"

# 13. Plane Strain Force (Global)
TABLE_TYPE_PLANE_STRAIN_FORCE_GLOBAL = "PLANESTRAINFG"

# 14. Plane Strain Stress (Local)
TABLE_TYPE_PLANE_STRAIN_STRESS_LOCAL = "PLANESTRAINSL"

# 15. Plane Strain Stress (Global)
TABLE_TYPE_PLANE_STRAIN_STRESS_GLOBAL = "PLANESTRAINSG"

# 16. Axisymmetric Force (Local)
TABLE_TYPE_AXISYMMETRIC_FORCE_LOCAL = "AXISYMMETRICFL"

# 17. Axisymmetric Force (Global)
TABLE_TYPE_AXISYMMETRIC_FORCE_GLOBAL = "AXISYMMETRICFG"

# 18. Axisymmetric Stress (Local)
TABLE_TYPE_AXISYMMETRIC_STRESS_LOCAL = "AXISYMMETRICSL"

# 19. Axisymmetric Stress (Global)
TABLE_TYPE_AXISYMMETRIC_STRESS_GLOBAL = "AXISYMMETRICSG"

# 20. Solid Force (Local)
TABLE_TYPE_SOLID_FORCE_LOCAL = "SOLIDFL"

# 21. Solid Force (Global)
TABLE_TYPE_SOLID_FORCE_GLOBAL = "SOLIDFG"

# 22. Solid Stress (Local)
TABLE_TYPE_SOLID_STRESS_LOCAL = "SOLIDSL"

# 23. Solid Stress (Global)
TABLE_TYPE_SOLID_STRESS_GLOBAL = "SOLIDSG"

# 24. Solid Strain (Local) — nonlinear/construction-stage Step results; use opt_cs/stage_step
TABLE_TYPE_SOLID_STRAIN_LOCAL_PLASTIC = "SOLID_LOCA_PLAST_STRAIN"
TABLE_TYPE_SOLID_STRAIN_LOCAL_TOTAL = "SOLID_LOCA_TOTAL_STRAIN"

# 25. Solid Strain (Global) — nonlinear/construction-stage Step results; use opt_cs/stage_step
TABLE_TYPE_SOLID_STRAIN_GLOBAL_PLASTIC = "SOLID_GLOB_PLAST_STRAIN"
TABLE_TYPE_SOLID_STRAIN_GLOBAL_TOTAL = "SOLID_GLOB_TOTAL_STRAIN"

# 26. Elastic Link
TABLE_TYPE_ELASTIC_LINK = "ELASTICLINK"
TABLE_TYPE_ELASTIC_LINK_BY_MAX = "ELASTICLINKVBM"

# 27. General Link
TABLE_TYPE_GENERAL_LINK_FORCE = "GENERAL_LINK_FORCE"
TABLE_TYPE_GENERAL_LINK_FORCE_BY_MAX = "GENERAL_LINK_FORCEVBM"
TABLE_TYPE_GENERAL_LINK_DEFORM = "GENERAL_LINK_DEFORM"

# 28. Vibration Mode Shape
TABLE_TYPE_EIGENVALUE_MODE = "EIGENVALUEMODE"
TABLE_TYPE_PARTICIPATION_VECTOR_MODE = "PARTICIPATIONVECTORMODE"

# 29. Buckling Mode Shape
TABLE_TYPE_BUCKLING_MODE = "BUCKLINGMODE"

# 30. Tendon Coordinates
TABLE_TYPE_TENDON_COORDINATES = "TNDN_COORDINATES"

# 31. Tendon Elongation — Stage/Step results; use opt_cs/stage_step
TABLE_TYPE_TENDON_ELONGATION = "TNDN_ELONGATION"

# 32. Tendon Arrangement
TABLE_TYPE_TENDON_ARRANGEMENT = "TNDN_ARRANGEMENT"

# 33. Tendon Loss
TABLE_TYPE_TENDON_LOSS_FORCE = "TNDN_LOSS_FORCE"
TABLE_TYPE_TENDON_LOSS_STRESS = "TNDN_LOSS_STRESS"

# 34. Tendon Weight
TABLE_TYPE_TENDON_WEIGHT_GROUP = "TNDN_WEIGHT_GROUP"
TABLE_TYPE_TENDON_WEIGHT_PROFILE = "TNDN_WEIGHT_PROFILE"
TABLE_TYPE_TENDON_WEIGHT_PROPERTY = "TNDN_WEIGHT_PROPERTY"

# 35. Tendon Stress Limit Check — manual documents an extra optional ADDITIONAL.REDUCTION_FACTOR
# object ({"AT_ANCH", "AWAY_FROM_ANCH", "AT_SERVICE"}, all Number); get_table() has no ADDITIONAL
# passthrough, so it is not exposed here — see final report.
TABLE_TYPE_TENDON_STRESS_LIMIT_CHECK = "TNDN_STRS_LIMIT_CHECK"

# 36. Tendon Approximate Loss
TABLE_TYPE_TENDON_APPROX_LOSS_FORCE = "TNDN_APPROX_LOSS_FORCE"
TABLE_TYPE_TENDON_APPROX_LOSS_STRESS = "TNDN_APPROX_LOSS_STRESS"

# 37. Composite Section for C.S. (Force and Stress)
TABLE_TYPE_COMPOSITE_SECTION_BEAM_FORCE = "COMPSECTBEAMFORCE"
TABLE_TYPE_COMPOSITE_SECTION_BEAM_STRESS = "COMPSECTBEAMSTRESS"

# 38. Composite Section for C.S. (Self-Constraint Force and Stress)
TABLE_TYPE_SELF_CONSTRAINT_BEAM_FORCE = "SELF_CONST_BEAM_FORCE"
TABLE_TYPE_SELF_CONSTRAINT_BEAM_STRESS = "SELF_CONST_BEAM_STRESS"


# --- 19_POST_AnalysisResult_1.md ---


def get_reaction_table(
    table_type: str = TABLE_TYPE_REACTION_GLOBAL,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #1 — Reaction.

    table_type: TABLE_TYPE_REACTION_GLOBAL (default), _LOCAL, or
    _LOCAL_SURFACE_SPRING. opt_cs/stage_step are not supported for the Local
    Surface Spring variant per the manual.
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_displacement_table(
    table_type: str = TABLE_TYPE_DISPLACEMENT_GLOBAL,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #2 — Displacements.

    table_type: TABLE_TYPE_DISPLACEMENT_GLOBAL (default) or _LOCAL.
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_truss_force_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #3 — Truss Force."""
    return get_table(
        TABLE_TYPE_TRUSS_FORCE,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_truss_stress_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #4 — Truss Stress."""
    return get_table(
        TABLE_TYPE_TRUSS_STRESS,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_cable_force_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #5 — Cable Force.

    Typically queried with opt_cs=True and stage_step for a construction-stage
    step, e.g. stage_step=["nl_001"].
    """
    return get_table(
        TABLE_TYPE_CABLE_FORCE,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_cable_config_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #6 — Cable Configuration."""
    return get_table(
        TABLE_TYPE_CABLE_CONFIG,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_cable_efficiency_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #7 — Cable Efficiency."""
    return get_table(
        TABLE_TYPE_CABLE_EFFICIENCY,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_beam_force_table(
    table_type: str = TABLE_TYPE_BEAM_FORCE,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #8 — Beam Force.

    table_type: TABLE_TYPE_BEAM_FORCE (default, per-Part) or
    TABLE_TYPE_BEAM_FORCE_BY_MAX (max-value basis).
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_beam_force_static_prestress_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #9 — Beam Force (Static Prestress)."""
    return get_table(
        TABLE_TYPE_BEAM_FORCE_STATIC_PRESTRESS,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_beam_stress_table(
    table_type: str = TABLE_TYPE_BEAM_STRESS,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #10 — Beam Stress.

    table_type: TABLE_TYPE_BEAM_STRESS (default) or TABLE_TYPE_BEAM_STRESS_7DOF
    (includes warping/7th-DOF components).
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_beam_stress_detail_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #11 — Beam Stress (Equivalent)."""
    return get_table(
        TABLE_TYPE_BEAM_STRESS_DETAIL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_beam_stress_psc_table(
    table_type: str = TABLE_TYPE_BEAM_STRESS_PSC,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/19_POST_AnalysisResult_1.md #12 — Beam Stress (PSC).

    table_type: TABLE_TYPE_BEAM_STRESS_PSC (default) or
    TABLE_TYPE_BEAM_STRESS_7DOF_PSC (includes warping/7th-DOF components).
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


# --- 20_POST_AnalysisResult_2.md ---


def get_plate_force_local_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #1 — Plate Force (Local)."""
    return get_table(
        TABLE_TYPE_PLATE_FORCE_LOCAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plate_force_global_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #2 — Plate Force (Global)."""
    return get_table(
        TABLE_TYPE_PLATE_FORCE_GLOBAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plate_force_unit_length_table(
    table_type: str = TABLE_TYPE_PLATE_FORCE_UNIT_LENGTH_LOCAL,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #3 — Plate Force (Unit Length).

    table_type: one of TABLE_TYPE_PLATE_FORCE_UNIT_LENGTH_LOCAL (default),
    _GLOBAL, _LOCAL_BY_MAX, _GLOBAL_BY_MAX, or _WOOD_ARMER (design moment).
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plate_stress_local_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #4 — Plate Stress (Local)."""
    return get_table(
        TABLE_TYPE_PLATE_STRESS_LOCAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plate_stress_global_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #5 — Plate Stress (Global)."""
    return get_table(
        TABLE_TYPE_PLATE_STRESS_GLOBAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plate_strain_local_table(
    table_type: str = TABLE_TYPE_PLATE_STRAIN_LOCAL_PLASTIC,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #6 — Plate Strain (Local).

    table_type: TABLE_TYPE_PLATE_STRAIN_LOCAL_PLASTIC (default) or _TOTAL.
    Nonlinear/construction-stage results — pass opt_cs=True and stage_step,
    e.g. stage_step=["nl_001"].
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plate_strain_global_table(
    table_type: str = TABLE_TYPE_PLATE_STRAIN_GLOBAL_PLASTIC,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #7 — Plate Strain (Global).

    table_type: TABLE_TYPE_PLATE_STRAIN_GLOBAL_PLASTIC (default) or _TOTAL.
    Nonlinear/construction-stage results — pass opt_cs=True and stage_step,
    e.g. stage_step=["nl_001"].
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plane_stress_force_local_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #8 — Plane Stress Force (Local)."""
    return get_table(
        TABLE_TYPE_PLANE_STRESS_FORCE_LOCAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plane_stress_force_global_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #9 — Plane Stress Force (Global)."""
    return get_table(
        TABLE_TYPE_PLANE_STRESS_FORCE_GLOBAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plane_stress_local_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #10 — Plane Stress (Local)."""
    return get_table(
        TABLE_TYPE_PLANE_STRESS_LOCAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plane_stress_global_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #11 — Plane Stress (Global)."""
    return get_table(
        TABLE_TYPE_PLANE_STRESS_GLOBAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plane_strain_force_local_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #12 — Plane Strain Force (Local)."""
    return get_table(
        TABLE_TYPE_PLANE_STRAIN_FORCE_LOCAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plane_strain_force_global_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #13 — Plane Strain Force (Global)."""
    return get_table(
        TABLE_TYPE_PLANE_STRAIN_FORCE_GLOBAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plane_strain_stress_local_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #14 — Plane Strain Stress (Local)."""
    return get_table(
        TABLE_TYPE_PLANE_STRAIN_STRESS_LOCAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_plane_strain_stress_global_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #15 — Plane Strain Stress (Global)."""
    return get_table(
        TABLE_TYPE_PLANE_STRAIN_STRESS_GLOBAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_axisymmetric_force_local_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #16 — Axisymmetric Force (Local)."""
    return get_table(
        TABLE_TYPE_AXISYMMETRIC_FORCE_LOCAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_axisymmetric_force_global_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #17 — Axisymmetric Force (Global)."""
    return get_table(
        TABLE_TYPE_AXISYMMETRIC_FORCE_GLOBAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_axisymmetric_stress_local_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #18 — Axisymmetric Stress (Local)."""
    return get_table(
        TABLE_TYPE_AXISYMMETRIC_STRESS_LOCAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_axisymmetric_stress_global_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #19 — Axisymmetric Stress (Global)."""
    return get_table(
        TABLE_TYPE_AXISYMMETRIC_STRESS_GLOBAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_solid_force_local_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #20 — Solid Force (Local)."""
    return get_table(
        TABLE_TYPE_SOLID_FORCE_LOCAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_solid_force_global_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #21 — Solid Force (Global)."""
    return get_table(
        TABLE_TYPE_SOLID_FORCE_GLOBAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_solid_stress_local_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #22 — Solid Stress (Local)."""
    return get_table(
        TABLE_TYPE_SOLID_STRESS_LOCAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_solid_stress_global_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #23 — Solid Stress (Global)."""
    return get_table(
        TABLE_TYPE_SOLID_STRESS_GLOBAL,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_solid_strain_local_table(
    table_type: str = TABLE_TYPE_SOLID_STRAIN_LOCAL_PLASTIC,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #24 — Solid Strain (Local).

    table_type: TABLE_TYPE_SOLID_STRAIN_LOCAL_PLASTIC (default) or _TOTAL.
    Nonlinear/construction-stage results — pass opt_cs=True and stage_step,
    e.g. stage_step=["nl_001"].
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_solid_strain_global_table(
    table_type: str = TABLE_TYPE_SOLID_STRAIN_GLOBAL_PLASTIC,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #25 — Solid Strain (Global).

    table_type: TABLE_TYPE_SOLID_STRAIN_GLOBAL_PLASTIC (default) or _TOTAL.
    Nonlinear/construction-stage results — pass opt_cs=True and stage_step,
    e.g. stage_step=["nl_001"].
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_elastic_link_table(
    table_type: str = TABLE_TYPE_ELASTIC_LINK,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #26 — Elastic Link.

    table_type: TABLE_TYPE_ELASTIC_LINK (default) or TABLE_TYPE_ELASTIC_LINK_BY_MAX
    (max-value basis).
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_general_link_table(
    table_type: str = TABLE_TYPE_GENERAL_LINK_FORCE,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #27 — General Link.

    table_type: TABLE_TYPE_GENERAL_LINK_FORCE (default),
    TABLE_TYPE_GENERAL_LINK_FORCE_BY_MAX (max-value basis), or
    TABLE_TYPE_GENERAL_LINK_DEFORM (deformation instead of force).
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_vibration_mode_shape_table(
    table_type: str = TABLE_TYPE_EIGENVALUE_MODE,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #28 — Vibration Mode Shape.

    table_type: TABLE_TYPE_EIGENVALUE_MODE (default) or
    TABLE_TYPE_PARTICIPATION_VECTOR_MODE. Mode shapes are not load-case scoped,
    so LOAD_CASE_NAMES/OPT_CS/STAGE_STEP are not exposed here.
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_buckling_mode_shape_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #29 — Buckling Mode Shape.

    Mode shapes are not load-case scoped, so LOAD_CASE_NAMES/OPT_CS/STAGE_STEP
    are not exposed here.
    """
    return get_table(
        TABLE_TYPE_BUCKLING_MODE,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_tendon_coordinates_table(
    table_name: str = "",
    *,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #30 — Tendon Coordinates.

    Keyed by tendon/profile position, not by node/element, so NODE_ELEMS is
    not exposed here; the table is a static geometry listing (no load case).
    """
    return get_table(
        TABLE_TYPE_TENDON_COORDINATES,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_tendon_elongation_table(
    table_name: str = "",
    *,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #31 — Tendon Elongation.

    Keyed by tendon/Stage/Step, not by node/element or load case, so NODE_ELEMS
    and LOAD_CASE_NAMES are not exposed here. Stage/Step results — pass
    opt_cs=True and stage_step to select construction-stage steps.
    """
    return get_table(
        TABLE_TYPE_TENDON_ELONGATION,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_tendon_arrangement_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #32 — Tendon Arrangement."""
    return get_table(
        TABLE_TYPE_TENDON_ARRANGEMENT,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_tendon_loss_table(
    table_type: str = TABLE_TYPE_TENDON_LOSS_FORCE,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #33 — Tendon Loss.

    table_type: TABLE_TYPE_TENDON_LOSS_FORCE (default) or
    TABLE_TYPE_TENDON_LOSS_STRESS.
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_tendon_weight_table(
    table_type: str = TABLE_TYPE_TENDON_WEIGHT_GROUP,
    table_name: str = "",
    *,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #34 — Tendon Weight.

    table_type: TABLE_TYPE_TENDON_WEIGHT_GROUP (default), _PROFILE, or
    _PROPERTY. A group/profile/property summary, not node/element-scoped, so
    NODE_ELEMS is not exposed here.
    """
    return get_table(
        table_type,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_tendon_stress_limit_check_table(
    table_name: str = "",
    *,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #35 — Tendon Stress Limit Check.

    Not node/element-scoped (per-tendon), so NODE_ELEMS is not exposed here.
    NOTE: the manual documents an additional optional
    ``ADDITIONAL.REDUCTION_FACTOR`` object (keys "AT_ANCH", "AWAY_FROM_ANCH",
    "AT_SERVICE", each a Number reduction factor applied to the corresponding
    stress limit; defaults 0.7/0.74/0.8) that is NOT part of get_table()'s
    common Argument shape and is therefore not exposed by this wrapper.
    """
    return get_table(
        TABLE_TYPE_TENDON_STRESS_LIMIT_CHECK,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_tendon_approx_loss_table(
    table_type: str = TABLE_TYPE_TENDON_APPROX_LOSS_FORCE,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #36 — Tendon Approximate Loss.

    table_type: TABLE_TYPE_TENDON_APPROX_LOSS_FORCE (default) or
    TABLE_TYPE_TENDON_APPROX_LOSS_STRESS.
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_composite_section_beam_table(
    table_type: str = TABLE_TYPE_COMPOSITE_SECTION_BEAM_FORCE,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #37 — Composite Section for C.S.
    (Force and Stress).

    table_type: TABLE_TYPE_COMPOSITE_SECTION_BEAM_FORCE (default) or
    TABLE_TYPE_COMPOSITE_SECTION_BEAM_STRESS.
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_composite_section_self_constraint_beam_table(
    table_type: str = TABLE_TYPE_SELF_CONSTRAINT_BEAM_FORCE,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/20_POST_AnalysisResult_2.md #38 — Composite Section for C.S.
    (Self-Constraint Force and Stress).

    table_type: TABLE_TYPE_SELF_CONSTRAINT_BEAM_FORCE (default) or
    TABLE_TYPE_SELF_CONSTRAINT_BEAM_STRESS.
    """
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )
