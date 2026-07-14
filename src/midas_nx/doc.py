"""``/doc/*`` — document lifecycle.

Source: MIDAS-API manual repo, docs/manual/01_DOC.md (items 1-11).
POST-only; every body is wrapped in an ``"Argument"`` key (not ID-keyed, so
these are plain functions rather than DbResource subclasses).
"""
from __future__ import annotations

from typing import Optional

from .client import MidasClient, post_argument as _post


def new_project(client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #1 — /doc/NEW — New Project."""
    return _post("/doc/NEW", {}, client)


def open_project(path: str, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #2 — /doc/OPEN — Open Project."""
    return _post("/doc/OPEN", path, client)


def close_project(client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #3 — /doc/CLOSE — Close Project."""
    return _post("/doc/CLOSE", {}, client)


def save(client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #4 — /doc/SAVE — Save."""
    return _post("/doc/SAVE", {}, client)


def save_as(path: str, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #5 — /doc/SAVEAS — Save As."""
    return _post("/doc/SAVEAS", path, client)


def stage_as(stage_step: str, export_path: Optional[str] = None, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #6 — /doc/STAGAS — Save Current Stage As.

    stage_step (Required): construction-stage step name to save.
    export_path (Optional): file path to save to.
    """
    argument = {"STAGE_STEP": stage_step}
    if export_path is not None:
        argument["EXPORT_PATH"] = export_path
    return _post("/doc/STAGAS", argument, client)


def import_json(path: str, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #7 — /doc/IMPORT — Import to JSON."""
    return _post("/doc/IMPORT", path, client)


def import_mxt(path: str, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #8 — /doc/IMPORTMXT — Import to mct/mgt."""
    return _post("/doc/IMPORTMXT", path, client)


def export_json(path: str, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #9 — /doc/EXPORT — Export to JSON."""
    return _post("/doc/EXPORT", path, client)


def export_mxt(path: str, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #10 — /doc/EXPORTMXT — Export to mct/mgt."""
    return _post("/doc/EXPORTMXT", path, client)


def analyze(analysis_type: Optional[str] = None, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #11 — /doc/ANAL — Perform Analysis.

    analysis_type (Optional): e.g. "PUSHOVER" for a pushover run; omit for a
    general analysis run.
    """
    argument = {"TYPE": analysis_type} if analysis_type else {}
    return _post("/doc/ANAL", argument, client)
