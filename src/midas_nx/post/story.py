"""Source: docs/manual/21_POST_StoryTables.md, items 1-17.

All functions POST to the shared /post/TABLE endpoint — see post/base.py.

The manual declares one common Argument parameter table that applies
uniformly to all 17 story tables (TABLE_NAME, TABLE_TYPE, EXPORT_PATH, UNIT,
STYLES, COMPONENTS, NODE_ELEMS, LOAD_CASE_NAMES, OPT_CS, STAGE_STEP) rather
than documenting a per-table subset like ch18 did, so every wrapper below
exposes the full common kwarg set (mirroring get_table's own signature).
"""
from __future__ import annotations

from typing import List, Optional

from ..client import MidasClient
from .base import NodeElemsSelector, TableStyles, TableUnit, get_table

# 1. Story Drift
TABLE_TYPE_STORY_DRIFT_X = "STORY_DRIFT_X"
TABLE_TYPE_STORY_DRIFT_Y = "STORY_DRIFT_Y"
TABLE_TYPE_STORY_DRIFT_COMB = "STORY_DRIFT_COMB"

# 2. Story Displacement
TABLE_TYPE_STORY_DISPLACEMENT_X = "STORY_DISPLACEMENT_X"
TABLE_TYPE_STORY_DISPLACEMENT_Y = "STORY_DISPLACEMENT_Y"
TABLE_TYPE_STORY_DISPLACEMENT_COMB = "STORY_DISPLACEMENT_COMB"

# 3. Story Shear Force (R.S. Analysis)
TABLE_TYPE_STORY_SHEAR_FOR_RS = "STORY_SHEAR_FOR_RS"

# 4. Story Shear Force Coefficient (R.S. Analysis)
TABLE_TYPE_STORY_SHEAR_FORCE_COEFFICIENT = "STORY_SHEAR_FORCE_COEFFICIENT"

# 5. Story Mode Shape
TABLE_TYPE_STORY_MODE_SHAPE = "STORY_MODE_SHAPE"

# 6. Story Shear Force Ratio
TABLE_TYPE_STORY_SHEAR_FORCE_RATIO = "STORY_SHEAR_FORCE_RATIO"

# 7. Story Eccentricity
# NOTE: the API spec intentionally misspells this value — "Eccentricity"
# becomes "ECNTRICITY" (missing the second "e"). Use the string verbatim;
# it is not a transcription typo (see manual's explicit "철자 유의" callout).
TABLE_TYPE_STORY_ECCENTRICITY = "STORY_ECNTRICITY"

# 8. Overturning Moment
TABLE_TYPE_OVERTURNING_MOMENT = "OVERTURNING_MOMENT"

# 9. Story Axial Force Sum
TABLE_TYPE_STORY_AXIAL_FORCE_SUM = "STORY_AXIAL_FORCE_SUM"

# 10. Story Stability Coefficient
TABLE_TYPE_STORY_STABILITY_COEFFICIENT_X = "STORY_STABILITY_COEFFICIENT_X"
TABLE_TYPE_STORY_STABILITY_COEFFICIENT_Y = "STORY_STABILITY_COEFFICIENT_Y"

# 11. Torsional Irregularity Check
TABLE_TYPE_TORSIONAL_IRREGULARITY_X = "TORSIONAL_IRREGULARITY_X"
TABLE_TYPE_TORSIONAL_IRREGULARITY_Y = "TORSIONAL_IRREGULARITY_Y"

# 12. Torsional Amplification Factor
TABLE_TYPE_TORSIONAL_AMPLIFICATION_FACTOR_X = "TORSIONAL_AMPLIFICATION_FACTOR_X"
TABLE_TYPE_TORSIONAL_AMPLIFICATION_FACTOR_Y = "TORSIONAL_AMPLIFICATION_FACTOR_Y"

# 13. Stiffness Irregularity Check (Soft Story)
TABLE_TYPE_STIFFNESS_IRREGULARITY_X = "STIFFNESS_IRREGULARITY_X"
TABLE_TYPE_STIFFNESS_IRREGULARITY_Y = "STIFFNESS_IRREGULARITY_Y"

# 14. Capacity Irregularity Check (Weak Story)
TABLE_TYPE_CAPACITY_IRREGULARITY = "CAPACITY_IRREGULARITY"

# 15. Criteria for Regularity in Plan
TABLE_TYPE_CRITERIA_FOR_REGULARITY_IN_PLAN = "CRITERIA_FOR_REGULARITY_IN_PLAN"

# 16. Ultimate Story Shear For Check
TABLE_TYPE_ULTIMATE_STORY_SHEAR_FORCE_CHECK = "ULTIMATE_STORY_SHEAR_FORCE_CHECK"

# 17. Weight Irregularity Check
TABLE_TYPE_WEIGHT_IRREGULARITY_X = "WEIGHT_IRREGULARITY_X"
TABLE_TYPE_WEIGHT_IRREGULARITY_Y = "WEIGHT_IRREGULARITY_Y"


def get_story_drift_table(
    table_type: str = TABLE_TYPE_STORY_DRIFT_COMB,
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #1 — Story Drift.

    table_type: TABLE_TYPE_STORY_DRIFT_X/_Y (single-direction) or
    TABLE_TYPE_STORY_DRIFT_COMB (combined, adds shear-weighted/selected-node
    detail columns).
    """
    return get_table(
        table_type,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_story_displacement_table(
    table_type: str = TABLE_TYPE_STORY_DISPLACEMENT_COMB,
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #2 — Story Displacement.

    table_type: TABLE_TYPE_STORY_DISPLACEMENT_X/_Y (single-direction) or
    TABLE_TYPE_STORY_DISPLACEMENT_COMB (combined).
    """
    return get_table(
        table_type,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_story_shear_force_rs_table(
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #3 — Story Shear Force (R.S. Analysis).

    Requires a defined and analyzed response-spectrum (RS) load case in
    load_case_names — DATA is returned empty otherwise.
    """
    return get_table(
        TABLE_TYPE_STORY_SHEAR_FOR_RS,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_story_shear_force_coefficient_table(
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #4 — Story Shear Force Coefficient (R.S. Analysis).

    Requires a defined and analyzed response-spectrum (RS) load case in
    load_case_names — DATA is returned empty otherwise.
    """
    return get_table(
        TABLE_TYPE_STORY_SHEAR_FORCE_COEFFICIENT,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_story_mode_shape_table(
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #5 — Story Mode Shape.

    Requires mode/response-spectrum analysis results.
    """
    return get_table(
        TABLE_TYPE_STORY_MODE_SHAPE,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_story_shear_force_ratio_table(
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #6 — Story Shear Force Ratio.

    Per-story shear force and share ratio by vertical-member type
    (Frame/Wall), for two angles (Angle1/Angle2).
    """
    return get_table(
        TABLE_TYPE_STORY_SHEAR_FORCE_RATIO,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_story_eccentricity_table(
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #7 — Story Eccentricity.

    Weight/stiffness center coordinates, eccentricity distance, torsional
    stiffness, elastic radius, and eccentricity ratio per story.
    """
    return get_table(
        TABLE_TYPE_STORY_ECCENTRICITY,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_overturning_moment_table(
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #8 — Overturning Moment.

    Per-story overturning moment split by vertical-member type
    (Frame/Wall), for two angles (Angle1/Angle2).
    """
    return get_table(
        TABLE_TYPE_OVERTURNING_MOMENT,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_story_axial_force_sum_table(
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #9 — Story Axial Force Sum.

    Sum of vertical-element axial force per story, plus the axial-force
    centroid (X/Y coordinates).
    """
    return get_table(
        TABLE_TYPE_STORY_AXIAL_FORCE_SUM,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_story_stability_coefficient_table(
    table_type: str = TABLE_TYPE_STORY_STABILITY_COEFFICIENT_X,
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #10 — Story Stability Coefficient.

    table_type: TABLE_TYPE_STORY_STABILITY_COEFFICIENT_X or _Y.
    """
    return get_table(
        table_type,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_torsional_irregularity_table(
    table_type: str = TABLE_TYPE_TORSIONAL_IRREGULARITY_X,
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #11 — Torsional Irregularity Check.

    table_type: TABLE_TYPE_TORSIONAL_IRREGULARITY_X or _Y.
    """
    return get_table(
        table_type,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_torsional_amplification_factor_table(
    table_type: str = TABLE_TYPE_TORSIONAL_AMPLIFICATION_FACTOR_X,
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #12 — Torsional Amplification Factor.

    table_type: TABLE_TYPE_TORSIONAL_AMPLIFICATION_FACTOR_X or _Y.
    """
    return get_table(
        table_type,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_stiffness_irregularity_table(
    table_type: str = TABLE_TYPE_STIFFNESS_IRREGULARITY_X,
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #13 — Stiffness Irregularity Check (Soft Story).

    table_type: TABLE_TYPE_STIFFNESS_IRREGULARITY_X or _Y.
    """
    return get_table(
        table_type,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_capacity_irregularity_table(
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #14 — Capacity Irregularity Check (Weak Story).

    Per-story shear strength vs. upper-story shear strength, for two angles
    (Angle1/Angle2).
    """
    return get_table(
        TABLE_TYPE_CAPACITY_IRREGULARITY,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_criteria_for_regularity_in_plan_table(
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #15 — Criteria for Regularity in Plan."""
    return get_table(
        TABLE_TYPE_CRITERIA_FOR_REGULARITY_IN_PLAN,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_ultimate_story_shear_force_check_table(
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #16 — Ultimate Story Shear For Check.

    Applied shear force (Ve) vs. clockwise/counter-clockwise ultimate shear
    force (Vp) by column/wall, with a final OK/NG remark.
    """
    return get_table(
        TABLE_TYPE_ULTIMATE_STORY_SHEAR_FORCE_CHECK,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )


def get_weight_irregularity_table(
    table_type: str = TABLE_TYPE_WEIGHT_IRREGULARITY_X,
    table_name: str = "",
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/21_POST_StoryTables.md #17 — Weight Irregularity Check.

    table_type: TABLE_TYPE_WEIGHT_IRREGULARITY_X or _Y.
    """
    return get_table(
        table_type,
        table_name,
        unit=unit,
        styles=styles,
        components=components,
        node_elems=node_elems,
        load_case_names=load_case_names,
        opt_cs=opt_cs,
        stage_step=stage_step,
        client=client,
    )
