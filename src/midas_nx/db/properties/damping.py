"""Source: docs/manual/04_DB_Properties.md, item 30 (/db/GRDP)."""
from __future__ import annotations

from typing import Any, List, TypedDict

from ..base import DbResource


class GroupDampingItem(TypedDict, total=False):
    GROUP_TYPE: str  # "MATERIAL" / "STRUCTURE" / "BOUNDARY", required
    GROUP_NAME: str  # Damping Ratio Name, required
    DAMPING_RATIO: float  # required


class GroupDampingPayload(TypedDict, total=False):
    """docs/manual/04_DB_Properties.md #30 — /db/GRDP Specifications table.

    The manual's worked example includes several coefficient/default-option
    fields (STIFF_COEF_DEFAULT, MASS_COEF_DEFAULT, OPT_MASS_PROP_DEFAULT,
    OPT_STIFF_PROP_DEFAULT) not itemized in its own Specifications table;
    included here as Any since the example is the more concrete source but
    their full shape isn't documented.
    """

    bExistStrain: bool  # Strain Energy Proportional, required
    STRAIN_GROUP_ITEMS: List[GroupDampingItem]  # required
    OPT_CALC_WHEN_USED: bool  # Calculate Only When Used, required
    STIFF_COEF_DEFAULT: Any  # optional, undocumented in table
    MASS_COEF_DEFAULT: Any  # optional, undocumented in table
    OPT_MASS_PROP_DEFAULT: Any  # optional, undocumented in table
    OPT_STIFF_PROP_DEFAULT: Any  # optional, undocumented in table


class GroupDamping(DbResource):
    ENDPOINT = "/db/GRDP"
    NAME = "Group Damping"
    PRODUCTS = frozenset({"gen", "civil"})
