"""One save-path contract for every harness that calls ``/doc/NEW``.

Four harnesses discard the open document, and until 2026-09-21 each asked for
somewhere to put a checkpoint in its own way: ``live_manual_feedback.py``
required ``--save-dir``, ``packages/typescript/scripts/live-crud.mjs`` required
it unless the caller waived the checkpoint, ``live_crud_check.py``'s
``--save-as`` was optional, and ``live_smoke.py`` had no such flag at all. Four
destructive tools, four rules, and the weakest of them was the one that runs
the longest.

The rule is now the same in all four, and it is the npm harness's:

    --save-dir DIR       where this run's checkpoints go, **on the NX machine**
    --no-save-before     waive the checkpoint. It removes the safety net, not
                         the /doc/NEW.

Neither one given is refused before a single call goes out.

Two stated departures, both about what a checkpoint *is* for that harness:
``live_crud_check.py`` also takes ``--save-as``, an exact path, because it had
one and callers have it in their fingers; and ``live_manual_feedback.py`` has
no waiver, because its per-probe saves are the evidence the run produces
rather than a safety net. A departure with a reason is a different thing from
the four rules this replaced, which differed for none.

Why a directory and not a path: the checkpoint's **extension** decides whether
the product accepts the save at all, and this repo got that wrong twice. The
NX pair is Gen ``.mgbx`` / Civil ``.mcbz``, and the pre-NX pair (``.mgb`` /
``.mcb``) is the one ``/doc/STAGAS`` wants instead. Deriving the name from the
product removes that choice from the caller.

Why it is required rather than guessed: every path resolves on the machine
running NX, not the one running the script. A directory that does not exist
there raises a modal dialog *there* while the HTTP call still answers
``{"message": "... command complete"}``, and the whole API session blocks
until a human dismisses it. Deriving one from ``verify_connection()["user"]``
was tried and disproved on 2026-08-31: that field is the MAPI account's email,
not the host's Windows profile.

The shape check runs while arguments are parsed rather than at the save, so a
malformed path costs nothing -- not even a connection.

**A harness saves the model before it analyses it.** ``/doc/ANAL`` on a
document that was never saved - which is every document right after
``/doc/NEW`` - raised Gen NX's "Save As" dialog on 2026-10-22 (Build
10/17/2026), and the call never answered until the dialog was closed. Every
harness analyses through ``analyze_saved``, which writes a checkpoint into the
same ``--save-dir`` first and refuses when there is none to write into;
``tests/test_harness_save_path.py`` fails if a script calls ``doc.analyze``
directly. The npm ``live-analysis.mjs`` saves before its analysis too.

**A Gen harness does not start while another app is driving the same Gen.**
The NX host is shared: smart-midas-steel, Steel-Frame and a Gen RC app run
their own live scripts against it and leave ``sms_*``, ``sf_*`` and
``gen_rc_temp_*`` files in ``C:/temp``. On 2026-10-27 a ``live_crud_check.py``
run here overlapped one of theirs, and its ``/doc/NEW`` broke that app's
restore of the user's document. ``require`` now refuses a Gen run when any such
file in ``C:/temp`` or the run's own save directory changed in the last ten
minutes - with ``--save-as`` or ``--no-save-before`` too, since both still
send ``/doc/NEW`` - which is the rule those
apps apply to ``midas-nx-*gen*`` files from this side. ``--allow-concurrent-apps``
overrides it once someone has checked the other run is finished. It can only
see the directory when the script runs on the NX host itself; Civil NX is
another process with another key and is not checked.
"""

from __future__ import annotations

import argparse
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional

#: Product-native NX extensions, author-confirmed 2026-08-31.
PRODUCT_EXTENSION = {"gen": "mgbx", "civil": "mcbz"}

#: An absolute Windows directory, which is what a path on the NX host is.
#: Same rule as `isAbsoluteHostDirectory` in live-crud.mjs.
_ABSOLUTE_HOST_DIRECTORY = re.compile(r"^[A-Za-z]:/[^\0]*$")

#: File-name prefixes other apps' Gen live scripts leave in the shared save
#: directory, and how recent one must be to mean that app is still running.
OTHER_APP_PREFIXES = ("sms_", "sf_", "gen_rc_temp_")
OTHER_APP_WINDOW_SECONDS = 10 * 60
#: Where those apps write, looked at whatever --save-dir says: their files
#: land here even when this run saves somewhere else.
OTHER_APP_DIRECTORIES = ("C:/temp",)

_CONCURRENT_HELP = (
    "start even though another app's Gen live files in --save-dir changed in "
    "the last ten minutes. Check that run has finished first: two scripts "
    "driving one Gen session break each other's /doc/NEW and restores."
)

_SAVE_DIR_HELP = (
    "directory ON THE NX MACHINE for this run's checkpoints, e.g. C:/temp. "
    "Every path here resolves on the host running NX, not on this one, and a "
    "directory that does not exist there raises a blocking dialog while the "
    "HTTP call still answers like a success -- so it is named, never guessed."
)
_NO_SAVE_HELP = (
    "skip the checkpoint of the currently open document. This removes the "
    "safety net, not the /doc/NEW: the open document is still discarded."
)
MISSING_SAVE_DIR = (
    "this harness calls /doc/NEW and writes a checkpoint per probe. Give "
    "--save-dir a writable directory on the NX machine; those files are the "
    "run's evidence, so there is no waiver for them."
)
UNSAVED_ANALYSIS = (
    "this harness analyses the model it built, and /doc/ANAL on a document "
    "that was never saved raises a Save As dialog that blocks the session. "
    "Give --save-dir so the model can be saved there first."
)
MISSING_SAVE_TARGET = (
    "this harness calls /doc/NEW and discards the open document. Give "
    "--save-dir a writable directory on the NX machine, or pass "
    "--no-save-before to waive the checkpoint (which does not waive the "
    "/doc/NEW)."
)


def add_arguments(parser: argparse.ArgumentParser, *, waivable: bool = True) -> None:
    """Add the shared ``--save-dir`` / ``--no-save-before`` pair.

    ``waivable=False`` leaves ``--no-save-before`` off, for a harness whose
    checkpoints are not only a safety net. ``live_manual_feedback.py`` is the
    one: each probe saves the document it built, and those files *are* the
    evidence the run exists to produce, so there is nothing there to waive.
    An exception that is stated is a different thing from the four rules this
    module replaced, which differed for no recorded reason.
    """
    parser.add_argument("--save-dir", help=_SAVE_DIR_HELP)
    if waivable:
        parser.add_argument("--no-save-before", action="store_true", help=_NO_SAVE_HELP)
    parser.add_argument("--allow-concurrent-apps", action="store_true", help=_CONCURRENT_HELP)


def normalize_directory(save_dir: str) -> str:
    """A host directory with separators and trailing slashes settled."""
    return save_dir.replace("\\", "/").rstrip("/")


def is_absolute_host_directory(save_dir: str) -> bool:
    return bool(_ABSOLUTE_HOST_DIRECTORY.match(normalize_directory(save_dir)))


def require(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    *,
    exact_path: str | None = None,
) -> None:
    """Refuse the run unless a save target is named or explicitly waived.

    ``exact_path`` is for a harness that also accepts a full file path of its
    own (``live_crud_check.py``'s ``--save-as``); naming one satisfies the
    requirement, and its extension is the caller's to get right.
    """
    if not getattr(args, "no_save_before", False):
        if not args.save_dir and not exact_path:
            parser.error(
                MISSING_SAVE_TARGET if hasattr(args, "no_save_before")
                else MISSING_SAVE_DIR
            )
        if args.save_dir and not is_absolute_host_directory(args.save_dir):
            parser.error(
                f"--save-dir must be an absolute directory on the NX machine, "
                f"got {args.save_dir!r}."
            )
    # Last, and whatever was named or waived: a run with --save-as or
    # --no-save-before still sends /doc/NEW.
    _refuse_concurrent_apps(parser, args, exact_path)


def other_app_activity(directory: str, *, now: Optional[float] = None) -> list[str]:
    """Other apps' Gen live files in ``directory`` changed within the window.

    Empty when the directory is not visible from here, which is the case
    whenever the script is not running on the NX host. A file the other app
    removes while this looks, or a directory it cannot list, is skipped rather
    than raised: this check must never be the thing that crashes a run.
    """
    directory = normalize_directory(directory)
    cutoff = (time.time() if now is None else now) - OTHER_APP_WINDOW_SECONDS
    recent = []
    try:
        entries = list(os.scandir(directory))
    except OSError:
        return []
    for entry in entries:
        if not entry.name.startswith(OTHER_APP_PREFIXES):
            continue
        try:
            if entry.is_file() and entry.stat().st_mtime >= cutoff:
                recent.append(entry.name)
        except OSError:
            continue
    return sorted(recent)


def _watched_directories(args: argparse.Namespace, exact_path: str | None) -> list[str]:
    """Where to look: the directories the other apps write to, plus wherever
    this run was told to save."""
    named = [getattr(args, "save_dir", None)]
    if exact_path:
        named.append(os.path.dirname(exact_path.replace("\\", "/")))
    seen: list[str] = []
    for directory in [*OTHER_APP_DIRECTORIES, *named]:
        if directory and normalize_directory(directory).lower() not in [d.lower() for d in seen]:
            seen.append(normalize_directory(directory))
    return seen


def _refuse_concurrent_apps(
    parser: argparse.ArgumentParser, args: argparse.Namespace, exact_path: str | None = None
) -> None:
    if getattr(args, "allow_concurrent_apps", False) or getattr(args, "product", None) == "civil":
        return
    for directory in _watched_directories(args, exact_path):
        recent = other_app_activity(directory)
        if recent:
            shown = ", ".join(recent[:5]) + (" ..." if len(recent) > 5 else "")
            parser.error(
                f"another app is driving Gen NX: {len(recent)} of its live files in "
                f"{directory} changed in the last {OTHER_APP_WINDOW_SECONDS // 60} "
                f"minutes ({shown}). Wait for it to finish, or pass "
                f"--allow-concurrent-apps once you have checked it has."
            )


def checkpoint_prefix(save_dir: str, label: str, product: str) -> str:
    """A unique, extension-less checkpoint stem inside ``save_dir``.

    Stamped so a re-run never lands on an existing file: an overwrite prompt
    on the NX host is another modal dialog blocking the session.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{normalize_directory(save_dir)}/{label}-{product}-{stamp}"


def checkpoint(save_dir: str, label: str, product: str) -> str:
    """``checkpoint_prefix`` with the product's own NX extension."""
    return f"{checkpoint_prefix(save_dir, label, product)}.{PRODUCT_EXTENSION[product]}"


def analyze_saved(client: Any, save_dir: Optional[str], label: str, product: str) -> Any:
    """Save the open document under ``save_dir``, then run ``/doc/ANAL``.

    The only way a harness analyses. Without a directory there is nowhere to
    save, and analysing unsaved raises the blocking "Save As" dialog, so it
    refuses rather than send the call.
    """
    from midas_nx import doc  # noqa: PLC0415 - keep this module import-light

    if not save_dir:
        raise RuntimeError(UNSAVED_ANALYSIS)
    doc.save_as(checkpoint(save_dir, label, product), client=client)
    return doc.analyze(client=client)
