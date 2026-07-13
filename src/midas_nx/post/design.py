"""Source: docs/manual/23_POST_Design.md, items 1-10.

Design results use three URI patterns: /post/PM and /post/STEELCODECHECK are
POST-only with an empty "Argument" body (plain functions, like doc.py); the
remaining 8 "design forces" tables share the /post/TABLE endpoint used by
chapters 18-21 (see post/base.py's get_table()).
"""
from __future__ import annotations

from typing import List, Optional

from ..client import MidasClient, get_default_client
from .base import NodeElemsSelector, TableStyles, TableUnit, get_table


def _post(command: str, client: Optional[MidasClient] = None) -> dict:
    return (client or get_default_client()).request("POST", command, {"Argument": {}})


def get_pm_interaction_diagram(client: Optional[MidasClient] = None) -> dict:
    """docs/manual/23_POST_Design.md #1 — /post/PM — P-M Interaction Diagram.

    Takes no arguments; returns the current model's full P-M interaction
    (axial force-moment) curve dataset for RC/SRC columns and members. The
    manual doesn't publish a fixed response HEAD/DATA shape for this one —
    the response keys depend on the active design code configuration.
    """
    return _post("/post/PM", client)


def get_steel_code_check(client: Optional[MidasClient] = None) -> dict:
    """docs/manual/23_POST_Design.md #2 — /post/STEELCODECHECK — Steel Code Check.

    Takes no arguments; returns ``{"vSECT": [...], "vELEM": [...]}`` — each
    entry has SECT/ELEM id, RAT (combined strength ratio), SLN (slenderness
    ratio), DEF (deflection), DEFA (allowable deflection).
    """
    return _post("/post/STEELCODECHECK", client)


# 3. Concrete Design - Beam Design Forces
TABLE_TYPE_BEAM_DESIGN_FORCES = "BEAMDESIGNFORCES"

# 4. Concrete Design - Column Design Forces
TABLE_TYPE_COLUMN_DESIGN_FORCES = "COLUMNDESIGNFORCES"

# 5. Concrete Design - Brace Design Forces
TABLE_TYPE_BRACE_DESIGN_FORCES = "BRACEDESIGNFORCES"

# 6. Concrete Design - Wall Design Forces
TABLE_TYPE_WALL_DESIGN_FORCES = "WALLDESIGNFORCES"

# 7. Steel Design - Steel Member Design Forces
TABLE_TYPE_STEEL_MEMBER_DESIGN_FORCES = "STEELMEMBERDESIGNFORCES"

# 8. SRC Design - SRC Beam Design Forces
TABLE_TYPE_SRC_BEAM_DESIGN_FORCES = "SRCBEAMDESIGNFORCES"

# 9. SRC Design - SRC Column Design Forces
TABLE_TYPE_SRC_COLUMN_DESIGN_FORCES = "SRCCOLUMNDESIGNFORCES"

# 10. Cold Formed Design - Cold Formed Steel Member Design Forces
TABLE_TYPE_COLD_FORMED_STEEL_MEMBER_DESIGN_FORCES = "COLDFORMEDSTEELMEMBERDESIGNFORCES"


def _get_design_forces_table(
    table_type: str,
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    parts: Optional[List[str]] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    return get_table(
        table_type,
        table_name,
        node_elems=node_elems,
        parts=parts,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_beam_design_forces_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    parts: Optional[List[str]] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/23_POST_Design.md #3 — Concrete Design - Beam Design Forces.

    Requires analysis and design to already be complete (see 24_DB_Design.md
    for design-code/member setup). parts: member end selection, e.g.
    ["PartI", "PartJ"].
    """
    return _get_design_forces_table(
        TABLE_TYPE_BEAM_DESIGN_FORCES,
        table_name,
        node_elems=node_elems,
        parts=parts,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_column_design_forces_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    parts: Optional[List[str]] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/23_POST_Design.md #4 — Concrete Design - Column Design Forces."""
    return _get_design_forces_table(
        TABLE_TYPE_COLUMN_DESIGN_FORCES,
        table_name,
        node_elems=node_elems,
        parts=parts,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_brace_design_forces_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    parts: Optional[List[str]] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/23_POST_Design.md #5 — Concrete Design - Brace Design Forces.

    Response shape matches Column Design Forces.
    """
    return _get_design_forces_table(
        TABLE_TYPE_BRACE_DESIGN_FORCES,
        table_name,
        node_elems=node_elems,
        parts=parts,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_wall_design_forces_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/23_POST_Design.md #6 — Concrete Design - Wall Design Forces.

    Adds WID (wall id) and Story columns instead of a "Memb" column; no
    PARTS filter documented (uses Part values "Top"/"Bottom" from the wall's
    own geometry instead of member-end selection).
    """
    return _get_design_forces_table(
        TABLE_TYPE_WALL_DESIGN_FORCES,
        table_name,
        node_elems=node_elems,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_steel_member_design_forces_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    parts: Optional[List[str]] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/23_POST_Design.md #7 — Steel Design - Steel Member Design Forces."""
    return _get_design_forces_table(
        TABLE_TYPE_STEEL_MEMBER_DESIGN_FORCES,
        table_name,
        node_elems=node_elems,
        parts=parts,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_src_beam_design_forces_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    parts: Optional[List[str]] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/23_POST_Design.md #8 — SRC Design - SRC Beam Design Forces.

    Column order differs from RC Beam Design Forces: "My(+)" precedes
    "My(-)" here (RC beam forces list "My(-)" first).
    """
    return _get_design_forces_table(
        TABLE_TYPE_SRC_BEAM_DESIGN_FORCES,
        table_name,
        node_elems=node_elems,
        parts=parts,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_src_column_design_forces_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    parts: Optional[List[str]] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/23_POST_Design.md #9 — SRC Design - SRC Column Design Forces."""
    return _get_design_forces_table(
        TABLE_TYPE_SRC_COLUMN_DESIGN_FORCES,
        table_name,
        node_elems=node_elems,
        parts=parts,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )


def get_cold_formed_steel_member_design_forces_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    parts: Optional[List[str]] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/23_POST_Design.md #10 — Cold Formed Design - Cold Formed Steel Member Design Forces."""
    return _get_design_forces_table(
        TABLE_TYPE_COLD_FORMED_STEEL_MEMBER_DESIGN_FORCES,
        table_name,
        node_elems=node_elems,
        parts=parts,
        unit=unit,
        styles=styles,
        components=components,
        client=client,
    )
