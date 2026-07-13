"""Source: docs/manual/18_POST_PreProcess.md, items 1-10.

All functions POST to the shared /post/TABLE endpoint — see post/base.py.
"""
from __future__ import annotations

from typing import List, Optional

from ..client import MidasClient
from .base import NodeElemsSelector, TableStyles, TableUnit, get_table

# 1. Element Weight Table
TABLE_TYPE_ELEMENT_WEIGHT = "ELEMENTWEIGHT"

# 2. Nodal Body Force Table
TABLE_TYPE_NODAL_BODY_FORCE = "NODALBODYFORCE"

# 5. Material Table
TABLE_TYPE_MATERIAL = "MATERIAL"

# 6. Section Table — 10 section-kind variants
TABLE_TYPE_SECTION_ALL = "SECTIONALL"
TABLE_TYPE_SECTION_COMBINED = "SECTIONCOMBINED"
TABLE_TYPE_SECTION_COMPOSITE = "SECTIONCOMPOSITE"
TABLE_TYPE_SECTION_CONSTRUCTION = "SECTIONCONSTRUCTION"
TABLE_TYPE_SECTION_DB_USER = "SECTIONDB/USER"
TABLE_TYPE_SECTION_PSC = "SECTIONPSC"
TABLE_TYPE_SECTION_SRC = "SECTIONSRC"
TABLE_TYPE_SECTION_STEEL_GIRDER = "SECTIONSTEELGIRDER"
TABLE_TYPE_SECTION_TAPERED = "SECTIONTAPERED"
TABLE_TYPE_SECTION_VALUE = "SECTIONVALUE"

# 7. Restraint Supports Table
TABLE_TYPE_SUPPORTS = "SUPPORTS"

# 8. Story Mass Summary Table
TABLE_TYPE_STORY_MASS = "STORY_MASS"
TABLE_TYPE_STORY_MASS_X = "STORY_MASS_X"
TABLE_TYPE_STORY_MASS_Y = "STORY_MASS_Y"
TABLE_TYPE_STORY_MASS_Z = "STORY_MASS_Z"

# 10. Story Weight Table
TABLE_TYPE_STORY_WEIGHT = "STORYWEIGHT"


def get_element_weight_table(
    table_name: str = "",
    *,
    node_elems: Optional[NodeElemsSelector] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/18_POST_PreProcess.md #1 — Element Weight Table.

    node_elems: target scope (exactly one of KEYS/TO/STRUCTURE_GROUP_NAME);
    omit for all elements.
    """
    return get_table(TABLE_TYPE_ELEMENT_WEIGHT, table_name, node_elems=node_elems, client=client)


def get_nodal_body_force_table(table_name: str = "", *, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/18_POST_PreProcess.md #2 — Nodal Body Force Table."""
    return get_table(TABLE_TYPE_NODAL_BODY_FORCE, table_name, client=client)


def get_mass_summary_table(
    direction: str, table_name: str = "", *, client: Optional[MidasClient] = None
) -> dict:
    """docs/manual/18_POST_PreProcess.md #3 — Mass Summary Table.

    direction: "X"/"Y"/"Z".
    """
    return get_table(f"MASS_SUMMARY_{direction}", table_name, client=client)


def get_load_summary_table(
    direction: str, table_name: str = "", *, client: Optional[MidasClient] = None
) -> dict:
    """docs/manual/18_POST_PreProcess.md #4 — Load Summary Table.

    direction: "X"/"Y"/"Z".
    """
    return get_table(f"LOAD_SUMMARY_{direction}", table_name, client=client)


def get_material_table(table_name: str = "", *, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/18_POST_PreProcess.md #5 — Material Table."""
    return get_table(TABLE_TYPE_MATERIAL, table_name, client=client)


def get_section_table(
    table_type: str = TABLE_TYPE_SECTION_ALL, table_name: str = "", *, client: Optional[MidasClient] = None
) -> dict:
    """docs/manual/18_POST_PreProcess.md #6 — Section Table.

    table_type: one of the TABLE_TYPE_SECTION_* constants above.
    """
    return get_table(table_type, table_name, client=client)


def get_supports_table(table_name: str = "", *, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/18_POST_PreProcess.md #7 — Restraint Supports Table."""
    return get_table(TABLE_TYPE_SUPPORTS, table_name, client=client)


def get_story_mass_summary_table(
    table_type: str = TABLE_TYPE_STORY_MASS,
    table_name: str = "",
    *,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """docs/manual/18_POST_PreProcess.md #8 — Story Mass Summary Table.

    table_type: TABLE_TYPE_STORY_MASS (direction-summed) or
    TABLE_TYPE_STORY_MASS_X/_Y/_Z (per-direction).
    """
    return get_table(table_type, table_name, unit=unit, styles=styles, components=components, client=client)


def get_story_load_summary_table(
    direction: str, table_name: str = "", *, client: Optional[MidasClient] = None
) -> dict:
    """docs/manual/18_POST_PreProcess.md #9 — Story Load Summary Table.

    direction: "X"/"Y"/"Z".
    """
    return get_table(f"STORY_LOAD_SUMMARY_{direction}", table_name, client=client)


def get_story_weight_table(table_name: str = "", *, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/18_POST_PreProcess.md #10 — Story Weight Table."""
    return get_table(TABLE_TYPE_STORY_WEIGHT, table_name, client=client)
