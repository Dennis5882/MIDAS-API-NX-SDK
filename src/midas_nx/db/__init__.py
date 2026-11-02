"""``/db/*`` endpoints as :class:`~midas_nx.db.base.DbResource` subclasses.

The resources live in topic modules (``node_element``, ``properties.material``,
``static_loads``, ...) and the design-code chapters in :mod:`midas_nx.design`.
:func:`all_resources` lists every one of them without the caller having to know
where each is defined.
"""

from __future__ import annotations

import functools
import importlib
import inspect
import pkgutil
from typing import Dict, Type

from midas_nx.db.base import DbResource

__all__ = ["all_resources"]


@functools.lru_cache(maxsize=None)
def _collect() -> Dict[str, Type[DbResource]]:
    import midas_nx.db
    import midas_nx.design

    found: Dict[str, Type[DbResource]] = {}
    for package in (midas_nx.db, midas_nx.design):
        for info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            module = importlib.import_module(info.name)
            for _, cls in inspect.getmembers(module, inspect.isclass):
                endpoint = getattr(cls, "ENDPOINT", None)
                if issubclass(cls, DbResource) and cls is not DbResource and endpoint:
                    found.setdefault(endpoint, cls)
    return dict(sorted(found.items()))


def all_resources() -> Dict[str, Type[DbResource]]:
    """Every resource class this package defines, keyed by endpoint.

    That is the ``/db/*`` tables and the ``/DESIGN/*`` design-code records,
    sorted by endpoint. Filter by prefix for one family::

        tables = {e: c for e, c in all_resources().items() if e.startswith("/db/")}

    Each class carries ``NAME``, ``PRODUCTS`` and ``METHODS``; see
    :class:`~midas_nx.db.base.DbResource` for what ``METHODS`` does and does
    not promise. A new dict is returned on every call.
    """
    return dict(_collect())
