"""``/doc/*`` — document lifecycle.

Source: MIDAS-API manual repo, docs/manual/01_DOC.md (items 1-11).
POST-only; every body is wrapped in an ``"Argument"`` key (not ID-keyed, so
these are plain functions rather than DbResource subclasses).

⚠️ **Every path in this API belongs to the machine running NX.** Calls reach
the product through MIDASIT's relay, so it may be on a different computer than
the one running this code — that is a normal deployment, not an edge case. It
applies to ``open_project``/``save_as``/``import_*``/``export_*`` here, and
equally to ``EXPORT_PATH`` on result tables, design reports and view captures.
Derive the path from ``MidasClient.verify_connection()["user"]`` rather than
from your own environment; see :func:`save_as` for the pattern and the failure
mode, which is silent.
"""
from __future__ import annotations

from typing import Optional

from .client import MidasClient, MidasResultError, get_default_client
from .client import post_argument as _post

#: ``/doc/ANAL`` reports a solver failure as HTTP 200 with a plain
#: ``{"message": "MIDAS CIVIL NX Analysis failed."}`` — the *same* key it uses
#: for success (``"... command complete"``), and without the ``"error"`` object
#: that MidasClient checks for. Observed live 2026-07-26 on Civil NX 2026
#: (v2.1). Matched case-insensitively on the one stable word rather than on the
#: full string, since the sentence embeds the product name and has only been
#: seen under Civil.
_ANALYSIS_FAILURE_MARKER = "failed"


def _check_analysis_message(response: dict, client: Optional[MidasClient]) -> dict:
    """Raise if /doc/ANAL's 200 body says the analysis failed.

    Kept here rather than in ``MidasClient`` on purpose: ``"message"`` is the
    ordinary success carrier across the API, so a general "message containing
    'failed' means failure" rule would misfire (a design-check summary may well
    report how many members failed). ``analyze()`` is the call where a missed
    failure is most costly — every downstream result table comes back empty and
    the caller has nothing pointing at the cause.
    """
    active = client or get_default_client()
    if not active.raise_on_result_error:
        return response
    message = response.get("message") if isinstance(response, dict) else None
    if isinstance(message, str) and _ANALYSIS_FAILURE_MARKER in message.lower():
        raise MidasResultError(
            f"POST /doc/ANAL -> 200, but the analysis did not succeed: {message}",
            status_code=200,
            method="POST",
            endpoint="/doc/ANAL",
            response_body=response,
        )
    return response


def new_project(client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #1 — /doc/NEW — New Project.

    ⚠️ Live-tested 2026-07-26: this **can** raise MIDAS's own "save changes?"
    dialog, and any dialog **blocks the whole API session** until a human
    dismisses it — not just this call. Your next request then fails or times
    out for reasons that have nothing to do with it; a solve started behind
    that dialog came back ``{"message": "... Analysis failed."}``.

    It is not predictable from the API side. In one session it prompted on a
    document opened from disk and then did not prompt on any of the several
    scratch documents ``/doc/NEW`` had itself created. Assume it may prompt:
    don't run this unattended against a session you can't see.

    🛑 **This call has crashed Gen NX outright.** On 2026-07-26, one
    ``/doc/NEW`` against Gen NX 2026 (v2.1, build 06/23/2026) holding a real
    710-node analyzed model produced the *"Failed to disconnect the work
    session"* license dialog and killed the application; the API answered
    ``404 Client Disconnected``. The license stays checked out until the
    process is terminated properly, which affects other machines. The same
    call ran a dozen times that day against small scratch documents with no
    incident, so the open document's size or state looks like the factor —
    one occurrence, so that is a hypothesis, not a cause.

    Point this at a session whose contents you are willing to lose *and*
    whose process you are willing to restart. ``docs/live_verification_notes.md``
    has the full history, including the same crash signature under two other
    triggers.
    """
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
    """docs/manual/01_DOC.md #5 — /doc/SAVEAS — Save As.

    ⚠️ ``path`` is resolved **on the machine running NX**, which is not
    necessarily the machine running this code — calls go through MIDASIT's
    relay, so the product may be on another computer entirely. A path built
    from your own ``%USERPROFILE%`` or ``os.path.expanduser`` is a common way
    to get this wrong.

    Build it from the server instead::

        user = client.verify_connection()["user"]      # "someone@midasit.com"
        path = f"C:/Users/{user.split('@')[0]}/Documents/model.mgbx"

    A rejected path raises MIDAS's own "invalid path" dialog on that machine
    and blocks the session until a human dismisses it — while this call still
    answers ``{"message": "... command complete"}``, exactly as a successful
    save does. Live-tested 2026-07-26: the only difference visible from here
    was latency (58s blocked vs 0.4s saved). ``os.path.exists()`` locally
    proves nothing; :func:`open_project` on the same path is the check that
    asks the right filesystem.

    Note also that the manual's example still uses the pre-NX ``.mcb``
    extension; Gen NX 2026 writes ``.mgbx`` and Civil NX ``.mcbx``.
    """
    return _post("/doc/SAVEAS", path, client)


def stage_as(stage_step: str, export_path: Optional[str] = None, client: Optional[MidasClient] = None) -> dict:
    """docs/manual/01_DOC.md #6 — /doc/STAGAS — Save Current Stage As.

    stage_step (Required): the plain construction-stage NAME (e.g. "CS7",
    matching /db/STAG's own "NAME" field) — NOT the qualified
    "STAGE:step(last)" format used by post/TABLE's own STAGE_STEP
    parameter (e.g. "CS7:001(last)"). Live-tested 2026-07-31: the qualified
    format fails with "Please specify the correct stage name"; the plain
    stage name succeeds. Matches the manual's own worked example exactly
    (``STAGE_STEP: "Fase1"``) — this is a case of the SDK's own docstring
    inviting the wrong guess by naming the parameter the same as the
    differently-shaped post/TABLE one, not a manual/live discrepancy.

    export_path (Optional): file path to save to — must use the legacy
    ``.mcb`` extension (live-tested 2026-07-31: ``.mcbx`` fails with
    "Please check the file name or extension"), unlike save_as() which
    wants the current NX-native extension.
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

    ⚠️ Live-tested 2026-07-26: a *failed* solve is reported as HTTP 200 with
    ``{"message": "MIDAS CIVIL NX Analysis failed."}`` — the same key a
    successful call uses for ``"... command complete"``, and with no ``error``
    object. This function raises :class:`MidasResultError` on it rather than
    returning a dict that reads as success; every result table would otherwise
    come back empty with nothing pointing at the cause. A model the solver
    rejects up front (e.g. no boundary conditions) is reported the other way,
    as a normal ``{"error": ...}`` body, and raises from the client.

    ⚠️ Live-tested: on a large model (4000+ nodes), this call legitimately
    took longer than a 90s client timeout to solve — a
    ``MidasConnectionError``/read-timeout here does not necessarily mean the
    request failed, it can mean the solve is still running server-side.
    ``MidasClient(timeout=...)`` defaults to 30s; pass a larger value for
    big models rather than treating a timeout as a hard failure. See
    docs/live_verification_notes.md for the full context (this is a
    separate, milder finding from the confirmed `CC-ANAL` stuck-dialog
    bug — plain long-running analysis, not a stall).
    """
    argument = {"TYPE": analysis_type} if analysis_type else {}
    return _check_analysis_message(_post("/doc/ANAL", argument, client), client)
