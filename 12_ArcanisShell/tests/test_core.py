"""Unit tests for ArcanisShell core layers."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from arcanis_shell import (
    PermissionPolicy,
    RiskLevel,
    ShellConfig,
    ShellEngine,
)
from arcanis_shell.parser import CommandParser


def _engine(auto_approve: bool = True) -> ShellEngine:
    root = Path(tempfile.mkdtemp())
    (root / "note.txt").write_text("data")
    policy = PermissionPolicy(auto_approve_below=RiskLevel.CRITICAL)
    eng = ShellEngine(config=ShellConfig(sandbox_root=root, log_file=None), policy=policy)
    if auto_approve:
        eng.approval_fn = lambda p: True
    return eng


# ----------------------------------------------------------------------
# Parser
# ----------------------------------------------------------------------


def test_parser_routes_traditional() -> None:
    p = CommandParser(known_commands={"ls"})
    parsed = p.parse("ls -l /tmp")
    assert hasattr(parsed, "name")
    assert parsed.name == "ls"  # type: ignore[union-attr]
    assert parsed.flags.get("l") is None  # type: ignore[union-attr]


def test_parser_routes_natural_language() -> None:
    p = CommandParser(known_commands={"ls"})
    parsed = p.parse("organize my project files")
    assert hasattr(parsed, "text")


def test_parser_force_nl_with_ai_prefix() -> None:
    p = CommandParser(known_commands={"ls"})
    parsed = p.parse("ai list files")
    assert hasattr(parsed, "text")
    assert parsed.text == "list files"  # type: ignore[union-attr]


def test_parser_flag_with_value() -> None:
    p = CommandParser(known_commands={"find"})
    parsed = p.parse("find . --name '*.py'")
    assert hasattr(parsed, "flags")
    assert parsed.flags.get("name") == "*.py"  # type: ignore[union-attr]


# ----------------------------------------------------------------------
# Traditional commands
# ----------------------------------------------------------------------


def test_ls_and_cat() -> None:
    eng = _engine()
    assert "note.txt" in eng.execute("ls").stdout
    assert eng.execute("cat note.txt").stdout == "data"


def test_mkdir_and_tree() -> None:
    eng = _engine()
    assert eng.execute("mkdir -p a/b").success
    assert "a" in eng.execute("tree").stdout


def test_rm_requires_recursive_for_dir() -> None:
    eng = _engine()
    eng.execute("mkdir sub")
    res = eng.execute("rm sub")
    assert not res.success
    assert eng.execute("rm -r sub").success


def test_glob_mv_noop_is_success() -> None:
    eng = _engine()
    eng.execute("mkdir dest")
    res = eng.execute("mv *.py dest")
    assert res.success


def test_sandbox_blocks_escape() -> None:
    eng = _engine()
    res = eng.execute("cat ../secret")
    assert not res.success


def test_unknown_command() -> None:
    eng = _engine()
    assert not eng.execute("frobnicate").success


# ----------------------------------------------------------------------
# AI interface
# ----------------------------------------------------------------------


def test_nl_plan_executes() -> None:
    eng = _engine()
    res = eng.execute("ai organize my project files")
    assert res.success
    assert "project" in res.stdout


def test_explain_command() -> None:
    eng = _engine()
    text = eng.explain("rm -r old")
    assert "Irreversible" in text


def test_generate_automation() -> None:
    eng = _engine()
    script = eng.generate_automation("organize my project files")
    assert script.startswith("#")
    assert "mkdir" in script


def test_suggestions_present() -> None:
    eng = _engine()
    assert any("ls" in s for s in eng.suggest())


# ----------------------------------------------------------------------
# Security
# ----------------------------------------------------------------------


def test_permission_denylist_blocks() -> None:
    eng = _engine()
    eng.policy.deny_list.add("rm")
    res = eng.execute("rm -r x")
    assert not res.success


def test_sandbox_violation_logged() -> None:
    eng = _engine()
    eng.execute("cat ../x")
    assert any(e.outcome == "sandbox_violation" for e in eng.log)


def test_activity_log_records() -> None:
    eng = _engine()
    eng.execute("ls")
    assert len(eng.log) >= 1


def test_reject_plan_records_rejection() -> None:
    eng = _engine()
    eng.approval_fn = lambda p: False
    with pytest.raises(Exception):
        eng.execute("ai organize my project files")
    assert any(e.outcome == "rejected" for e in eng.log)


# ----------------------------------------------------------------------
# Script execution
# ----------------------------------------------------------------------


def test_run_arc_script() -> None:
    eng = _engine()
    script = eng.config.sandbox_root / "deploy.arc"
    script.write_text("mkdir build\n# comment\necho done\n")
    res = eng.execute(f"run {script.name}")
    assert res.success
    assert "done" in res.stdout
