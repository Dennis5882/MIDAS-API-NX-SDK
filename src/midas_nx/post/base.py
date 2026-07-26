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

from typing import Any, Dict, List, Mapping, Optional, TypedDict

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
    story_names: Optional[List[str]] = None,
    sect_position: Optional[str] = None,
    modes: Optional[List[str]] = None,
    additional: Optional[Dict[str, Any]] = None,
    set_calculation_method: Optional[Dict[str, Any]] = None,
    client: Optional[MidasClient] = None,
) -> dict:
    """POST /post/TABLE — extract one result table.

    table_type: the table's TABLE_TYPE value (see pre_process.py/result_1.py/
    story.py/design.py for the documented constants).
    table_name: response table title. The manual documents it as also becoming
    the response's top-level key, e.g.
    {table_name: {"FORCE": ..., "DIST": ..., "HEAD": [...], "DATA": [...]}} —
    but live sessions have returned other keys for the same call ("Result
    Table", "empty"), so don't index the response by name. Use
    :func:`unwrap_table` below, which finds the table by shape instead.
    node_elems/unit/styles/components: only meaningful for the specific table
    types documented as supporting them — see each caller's docstring.
    load_case_names: analysis-result tables only (ch19-21) — load/combination
    names with a type suffix, e.g. "DL(ST)", "COMB1(CB)", "CS1(CS)".
    opt_cs/stage_step: analysis-result tables only (ch19-21) — enable and
    select construction-stage steps, e.g. ["CS1:001(first)", "CS1:002(last)"].
    parts: design-force tables (ch23) and Wall Force (ch20) — member
    end/location or top/bot part selection, e.g. ["PartI", "PartJ"].
    story_names: Story-series (ch21) and Wall Force (ch20) tables only —
    restrict to specific story names; omitting it selects all stories.
    sect_position: Wall Force (ch20) only — section position selector.
    modes: Story Mode Shape (ch21) only — mode filter, e.g. ["Mode1", "Mode2"];
    omitting it returns all modes.
    additional: Story-series tables (ch21) only — the table-type-specific
    "ADDITIONAL" object (angle/Beta/node-selection/... settings); see each
    story.py caller's docstring and TypedDict for its shape.
    set_calculation_method: Weight Irregularity Check (ch21) only — unlike
    every other story table, the manual places this field directly under
    "Argument" rather than nesting it in "ADDITIONAL".
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
    if story_names is not None:
        argument["STORY_NAMES"] = story_names
    if sect_position is not None:
        argument["SECT_POSITION"] = sect_position
    if modes is not None:
        argument["MODES"] = modes
    if additional is not None:
        argument["ADDITIONAL"] = additional
    if set_calculation_method is not None:
        argument["SET_CALCULATION_METHOD"] = set_calculation_method
    client = client or get_default_client()
    return client.request("POST", "/post/TABLE", {"Argument": argument})


#: Keys that identify the actual table object inside a /post/TABLE response.
_TABLE_MARKERS = ("HEAD", "DATA")


def unwrap_table(response: Mapping[str, Any]) -> dict:
    """Pull the ``{FORCE, DIST, HEAD, DATA}`` table out of a ``get_table()``
    response, whatever its top-level key happens to be.

    The DbResource-side counterpart is ``DbResource.items()``. Matching on
    shape rather than on the key name is deliberate: the same call has been
    seen returning ``"Result Table"`` and ``"empty"`` as its top-level key
    across sessions, in addition to the ``TABLE_NAME`` the manual documents,
    so ``response[table_name]`` is not safe. Returns ``{}`` when the response
    carries no table (e.g. a zero-row ``{"message": ""}``).

    Example::

        raw = get_reaction_table(load_case_names=["DL(ST)"])
        table = unwrap_table(raw)
        for row in table.get("DATA", []):
            ...
    """
    if not isinstance(response, Mapping):
        return {}
    if any(marker in response for marker in _TABLE_MARKERS):
        return dict(response)
    for value in response.values():
        if isinstance(value, Mapping) and any(marker in value for marker in _TABLE_MARKERS):
            return dict(value)
    return {}
