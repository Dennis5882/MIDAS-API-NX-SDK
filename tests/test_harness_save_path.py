"""Every harness that calls `/doc/NEW` asks for a save location the same way.

Until 2026-09-21 the four disagreed: one required a directory, one required it
unless the caller waived the checkpoint, one had an optional path and one had
no flag at all -- and the weakest of them was the one that runs the longest.
`scripts/harness_save_path.py` is the single rule; these hold that each
harness actually applies it, and that the npm harness has not drifted from it.

Nothing here reaches a product: every case is refused while arguments are
parsed, which is the point of checking the path's shape there.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NPM_HARNESS = ROOT / "packages" / "typescript" / "scripts" / "live-crud.mjs"


def _module():
    spec = importlib.util.spec_from_file_location(
        "harness_save_path_under_test",
        ROOT / "scripts" / "harness_save_path.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # The real C:/temp is shared with other apps' live scripts; a test must not
    # depend on whether one of them ran in the last ten minutes.
    module.OTHER_APP_DIRECTORIES = ()
    return module


def _parsed(module, argv, *, waivable=True):
    parser = argparse.ArgumentParser(prog="harness")
    module.add_arguments(parser, waivable=waivable)
    return parser, parser.parse_args(argv)


@pytest.mark.parametrize("save_dir,absolute", [
    ("C:/temp", True),
    ("C:\\temp", True),
    ("c:/NX Scratch/checkpoints/", True),
    ("scratch", False),
    ("./scratch", False),
    ("/tmp/scratch", False),          # POSIX: this script's machine, not NX's
    ("\\\\server\\share", False),     # UNC: not a drive-letter path
])
def test_only_an_absolute_host_directory_is_a_usable_save_directory(
    save_dir, absolute
) -> None:
    """A path resolves on the NX host, which is a Windows machine.

    A relative one resolves against whatever that host's working directory
    happens to be, which is the guess this flag exists to prevent.
    """
    assert _module().is_absolute_host_directory(save_dir) is absolute


def test_naming_nothing_is_refused_before_any_call_goes_out() -> None:
    module = _module()
    parser, args = _parsed(module, [])
    with pytest.raises(SystemExit):
        module.require(parser, args)


def test_waiving_the_checkpoint_is_accepted_and_waives_the_shape_check_too() -> None:
    """--no-save-before removes the safety net, not the /doc/NEW."""
    module = _module()
    parser, args = _parsed(module, ["--no-save-before"])
    module.require(parser, args)  # does not raise


def test_an_exact_path_satisfies_the_requirement_in_place_of_a_directory() -> None:
    """live_crud_check.py's --save-as; its extension is the caller's to get right."""
    module = _module()
    parser, args = _parsed(module, [])
    module.require(parser, args, exact_path="C:/temp/scratch.mcbz")


def test_a_harness_with_no_waiver_has_no_waiver_flag_to_pass() -> None:
    """live_manual_feedback.py's per-probe saves are the run's evidence."""
    module = _module()
    parser, args = _parsed(module, [], waivable=False)
    assert not hasattr(args, "no_save_before")
    with pytest.raises(SystemExit):
        module.require(parser, args)


@pytest.mark.parametrize("product,extension", [("gen", "mgbx"), ("civil", "mcbz")])
def test_the_checkpoint_carries_the_product_s_own_nx_extension(
    product, extension
) -> None:
    """Deriving it is the point: this repo got the two pairs wrong twice.

    Gen NX writes `.mgbx` and Civil NX `.mcbz`; the pre-NX `.mgb`/`.mcb` pair
    is what `/doc/STAGAS` wants instead, and `/doc/SAVEAS` rejects the wrong
    spelling outright.
    """
    module = _module()
    path = module.checkpoint("C:\\temp\\", "run", product)
    assert path.startswith("C:/temp/run-" + product + "-")
    assert path.endswith("." + extension)
    assert module.checkpoint_prefix("C:/temp", "run", product) == path[: -len(extension) - 1]


@pytest.mark.parametrize("script,argv,expected", [
    ("scripts/live_smoke.py", ["--product", "gen"], "--no-save-before to waive"),
    ("scripts/live_smoke.py", ["--product", "gen", "--save-dir", "scratch"],
     "must be an absolute directory"),
    ("scripts/live_crud_check.py", ["--product", "gen", "--tier", "core"],
     "--no-save-before to waive"),
    ("scripts/live_crud_check.py",
     ["--product", "gen", "--tier", "core", "--save-dir", "scratch"],
     "must be an absolute directory"),
    ("scripts/live_manual_feedback.py", ["--product", "gen", "--out", "unused.json"],
     "no waiver for them"),
    ("scripts/live_design_functions.py", ["--report-dir", "C:/temp/unused"],
     "no waiver for them"),
    ("scripts/live_design_functions.py",
     ["--report-dir", "C:/temp/unused", "--save-dir", "scratch"],
     "must be an absolute directory"),
])
def test_each_destructive_harness_refuses_to_start_without_one(
    script, argv, expected
) -> None:
    """`live_crud_check.py` checks the selection first on purpose.

    A typo in `--tier` or `--endpoints` is reported as a typo rather than as a
    missing save directory, so the cases here name a selection that resolves.
    Both refusals still happen before a client exists.
    """
    result = subprocess.run(
        [sys.executable, script, *argv],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0, result.stdout
    assert expected in result.stderr, result.stderr


def test_the_npm_harness_still_applies_the_same_two_rules() -> None:
    """One fixture, two harnesses, and one save-path rule between them.

    live-crud.mjs cannot import the Python module, so the rule is duplicated
    there. Both halves of it are asserted rather than trusted: the
    drive-letter test and the product-to-extension mapping.
    """
    module = _module()
    source = NPM_HARNESS.read_text(encoding="utf-8")
    # The same pattern, written as a JS regex literal: `/` is escaped there.
    as_js_literal = module._ABSOLUTE_HOST_DIRECTORY.pattern.replace("/", r"\/")
    assert as_js_literal in source
    assert 'product === "civil" ? "mcbz" : "mgbx"' in source
    # And it refuses before connecting, the same as the Python three.
    assert "isAbsoluteHostDirectory(args.saveDir)" in source



def test_no_harness_analyses_an_unsaved_document() -> None:
    """`/doc/ANAL` on a never-saved document raises a blocking Save As dialog.

    Measured 2026-10-22 on Gen NX Build 10/17/2026, straight after `/doc/NEW`.
    Every Python harness goes through `analyze_saved`; a direct
    `doc.analyze(` anywhere else under scripts/ is the mistake that hit.
    """
    direct = [
        path.name for path in (ROOT / "scripts").glob("*.py")
        if path.name != "harness_save_path.py"
        and "doc.analyze(" in path.read_text(encoding="utf-8")
    ]
    assert direct == []
    analysis = (ROOT / "packages" / "typescript" / "scripts" / "live-analysis.mjs").read_text(
        encoding="utf-8")
    assert analysis.index("doc.saveAs(saved") < analysis.index("doc.analyze(")


def test_analyze_saved_saves_first_and_refuses_without_a_directory(monkeypatch) -> None:
    from midas_nx import doc

    module = _module()
    calls = []
    monkeypatch.setattr(doc, "save_as", lambda path, client=None: calls.append(("save", path)))
    monkeypatch.setattr(doc, "analyze", lambda client=None: calls.append(("analyze",)) or "ok")

    assert module.analyze_saved(object(), "C:/temp", "model", "gen") == "ok"
    assert calls[0][0] == "save" and calls[0][1].startswith("C:/temp/model-gen-")
    assert calls[0][1].endswith(".mgbx")
    assert calls[1] == ("analyze",)

    calls.clear()
    with pytest.raises(RuntimeError, match="Save As dialog"):
        module.analyze_saved(object(), None, "model", "civil")
    assert calls == []


def test_a_gen_run_waits_for_another_app_driving_the_same_gen(tmp_path) -> None:
    """On 2026-10-27 a run here overlapped smart-midas-steel's live script on
    the shared NX host and broke its restore. A recent sms_/sf_/gen_rc_temp_
    file refuses a Gen run before any call; Civil, an old file, our own files
    and the explicit override all pass."""
    import os
    import time

    module = _module()
    # --save-dir must look like a directory on the Windows NX host, which a
    # CI runner's tmp_path is not; the files are watched where the apps write.
    watched = str(tmp_path).replace("\\", "/")
    module.OTHER_APP_DIRECTORIES = (watched,)
    save_dir = "C:/nx-scratch"
    (tmp_path / "midas-nx-crud-gen-x.mgbx").write_text("")
    old = tmp_path / "sf_old.mgbx"
    old.write_text("")
    stale = time.time() - 11 * 60
    os.utime(old, (stale, stale))

    parser, args = _parsed(module, ["--save-dir", save_dir])
    module.require(parser, args)  # nothing recent from another app

    (tmp_path / "sms_guard_scratch_1.mgbx").write_text("")
    assert module.other_app_activity(watched) == ["sms_guard_scratch_1.mgbx"]
    parser, args = _parsed(module, ["--save-dir", save_dir])
    with pytest.raises(SystemExit):
        module.require(parser, args)

    parser, args = _parsed(module, ["--save-dir", save_dir, "--allow-concurrent-apps"])
    module.require(parser, args)
    parser, args = _parsed(module, ["--save-dir", save_dir])
    args.product = "civil"
    module.require(parser, args)


def test_the_guard_also_covers_runs_that_name_no_save_directory(tmp_path) -> None:
    """--save-as and --no-save-before still send /doc/NEW, so they are checked
    too: against the apps' own directory, and --save-as's directory."""
    module = _module()
    (tmp_path / "gen_rc_temp_1.mgbx").write_text("")
    watched = str(tmp_path).replace("\\", "/")

    module.OTHER_APP_DIRECTORIES = (watched,)
    parser, args = _parsed(module, ["--no-save-before"])
    with pytest.raises(SystemExit):
        module.require(parser, args)

    module.OTHER_APP_DIRECTORIES = ()
    parser, args = _parsed(module, [])
    with pytest.raises(SystemExit):
        module.require(parser, args, exact_path=f"{watched}/x.mgbx")


def test_a_file_that_vanishes_mid_scan_is_skipped_not_raised(tmp_path, monkeypatch) -> None:
    """The other app creates and deletes its scratch files while this looks."""
    module = _module()

    class Gone:
        name = "sms_gone.mgbx"

        def is_file(self) -> bool:
            return True

        def stat(self):
            raise FileNotFoundError(self.name)

    monkeypatch.setattr(module.os, "scandir", lambda path: iter([Gone()]))
    assert module.other_app_activity(str(tmp_path)) == []

    def locked(path):
        raise PermissionError(path)

    monkeypatch.setattr(module.os, "scandir", locked)
    assert module.other_app_activity(str(tmp_path)) == []


def test_both_languages_watch_the_same_apps_for_the_same_window() -> None:
    """The prefixes, window and directories exist once per language; a new
    consumer app added to one side only would leave the other running over it."""
    import re

    source = (ROOT / "scripts" / "harness_save_path.py").read_text(encoding="utf-8")
    js = (ROOT / "packages" / "typescript" / "scripts" / "live-harness-support.mjs").read_text(encoding="utf-8")
    py_prefixes = re.search(r"OTHER_APP_PREFIXES = \(([^)]*)\)", source).group(1)
    js_prefixes = re.search(r"OTHER_APP_PREFIXES = \[([^\]]*)\]", js).group(1)
    assert re.findall(r'"([^"]+)"', py_prefixes) == re.findall(r'"([^"]+)"', js_prefixes)
    py_dirs = re.search(r"OTHER_APP_DIRECTORIES = \(([^)]*)\)", source).group(1)
    js_dirs = re.search(r"OTHER_APP_DIRECTORIES = \[([^\]]*)\]", js).group(1)
    assert re.findall(r'"([^"]+)"', py_dirs) == re.findall(r'"([^"]+)"', js_dirs)
    assert "OTHER_APP_WINDOW_SECONDS = 10 * 60" in source
    assert "OTHER_APP_WINDOW_MS = 10 * 60 * 1000" in js
