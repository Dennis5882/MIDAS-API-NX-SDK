"""Shared plumbing for ``/post/TABLE`` — extracts pre-process, analysis-result,
and story summary tables. Source: docs/manual/18_POST_PreProcess.md through
21_POST_StoryTables.md.

Every ``/post/TABLE`` call shares one endpoint and one POST-only wrapper
(``"Argument"``, not ID-keyed ``"Assign"`` like ``/db/*``) — a ``TABLE_TYPE``
string selects which table is extracted, so this is one generic function
rather than a DbResource-per-table-type. The response shape
(``{FORCE, DIST, HEAD, DATA}``) is identical across every table type; HEAD's
column names vary per table and are only knowable from TABLE_TYPE, so the
response is returned as a plain dict rather than typed further.
"""
from __future__ import annotations

from typing import List, Optional, TypedDict

from ..client import MidasClient, get_default_client


class NodeElemsSelector(TypedDict, total=False):
    """Target-scope selector accepted by a handful of table types (e.g.
    Element Weight) — set exactly one of KEYS/TO/STRUCTURE_GROUP_NAME;
    omitting NODE_ELEMS entirely selects all nodes/elements."""

    KEYS: List[int]  # explicit ID list, e.g. [101, 102, 103]
    TO: str  # ID range, e.g. "101 to 105"
    STRUCTURE_GROUP_NAME: str  # structure group name, e.g. "SG1"


class TableUnit(TypedDict, total=False):
    """Response unit override, accepted by the Story-series table types."""

    FORCE: str  # e.g. "KN"
    DIST: str  # e.g. "M"
    HEAT: str
    TEMP: str


class TableStyles(TypedDict, total=False):
    """Response number-format override, accepted by the Story-series table types."""

    FORMAT: str  # "Default"/"Fixed"/"Scientific"/"General"
    PLACE: int  # decimal places, 0-15


def get_table(
    table_type: str,
    table_name: str = "",
    *,
    export_path: Optional[str] = None,
    node_elems: Optional[NodeElemsSelector] = None,
    unit: Optional[TableUnit] = None,
    styles: Optional[TableStyles] = None,
    components: Optional[List[str]] = None,
    load_case_names: Optional[List[str]] = None,
    opt_cs: Optional[bool] = None,
    stage_step: Optional[List[str]] = None,
    parts: Optional[List[str]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """POST /post/TABLE — extract one result table.

    table_type: the table's TABLE_TYPE value (see pre_process.py/result_1.py/
    story.py/design.py for the documented constants).
    table_name: response table title; also becomes the response's top-level
    key, e.g. {table_name: {"FORCE": ..., "DIST": ..., "HEAD": [...], "DATA": [...]}}.
    node_elems/unit/styles/components: only meaningful for the specific table
    types documented as supporting them — see each caller's docstring.
    load_case_names: analysis-result tables only (ch19-21) — load/combination
    names with a type suffix, e.g. "DL(ST)", "COMB1(CB)", "CS1(CS)".
    opt_cs/stage_step: analysis-result tables only (ch19-21) — enable and
    select construction-stage steps, e.g. ["CS1:001(first)", "CS1:002(last)"].
    parts: design-force tables only (ch23) — member end/location selection,
    e.g. ["PartI", "PartJ"].
    """
    argument: dict = {"TABLE_NAME": table_name, "TABLE_TYPE": table_type}
    if export_path is not None:
        argument["EXPORT_PATH"] = export_path
    if node_elems is not None:
        argument["NODE_ELEMS"] = node_elems
    if unit is not None:
        argument["UNIT"] = unit
    if styles is not None:
        argument["STYLES"] = styles
    if components is not None:
        argument["COMPONENTS"] = components
    if load_case_names is not None:
        argument["LOAD_CASE_NAMES"] = load_case_names
    if opt_cs is not None:
        argument["OPT_CS"] = opt_cs
    if stage_step is not None:
        argument["STAGE_STEP"] = stage_step
    if parts is not None:
        argument["PARTS"] = parts
    client = client or get_default_client()
    return client.request("POST", "/post/TABLE", {"Argument": argument})
