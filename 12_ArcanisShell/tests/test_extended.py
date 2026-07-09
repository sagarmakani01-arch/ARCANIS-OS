from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest

from arcanis_shell import (
    ActivityLog,
    CommandResult,
    CommandParser,
    ExecutionPlan,
    PermissionPolicy,
    RiskLevel,
    Sandbox,
    ShellConfig,
    ShellEngine,
)
from arcanis_shell.ai_interface import AIInterface, Explanation
from arcanis_shell.commands import (
    Command,
    CommandContext,
    Registry,
    build_registry,
    cmd_cat,
    cmd_cd,
    cmd_cp,
    cmd_echo,
    cmd_env,
    cmd_find,
    cmd_kill,
    cmd_ls,
    cmd_mkdir,
    cmd_mv,
    cmd_ps,
    cmd_rm,
    cmd_run,
    cmd_sysinfo,
    cmd_tree,
    cmd_which,
)
from arcanis_shell.errors import (
    AIUnavailableError,
    ArcanisShellError,
    CommandNotFoundError,
    ParseError,
    PermissionDeniedError,
    PlanRejectedError,
    SandboxViolationError,
    ShellRuntimeError,
)
from arcanis_shell.integration import (
    AgentsAdapter,
    BrainAdapter,
    BrainResponse,
    LocalAgentsAdapter,
    LocalBrainAdapter,
    LocalOSAdapter,
    OSAdapter,
    load_agents,
    load_brain,
    load_os,
)
from arcanis_shell.parser import NaturalLanguageRequest, TraditionalCommand
from arcanis_shell.script import run_script
from arcanis_shell.types import (
    ActivityEntry,
    CommandSource,
    CommandSpec,
    PlanStep,
    RiskLevel,
)


def _root() -> Path:
    return Path(tempfile.mkdtemp())


def _ctx(root: Path) -> CommandContext:
    sb = Sandbox(root=root)
    return CommandContext(cwd=root, sandbox=sb, registry=build_registry())


def _engine(auto_approve: bool = True) -> ShellEngine:
    root = _root()
    (root / "note.txt").write_text("data")
    policy = PermissionPolicy(auto_approve_below=RiskLevel.CRITICAL)
    eng = ShellEngine(
        config=ShellConfig(sandbox_root=root, log_file=None), policy=policy
    )
    if auto_approve:
        eng.approval_fn = lambda p: True
    return eng


# ----------------------------------------------------------------------
# Parser edge cases
# ----------------------------------------------------------------------


def test_parser_empty_input_raises():
    p = CommandParser(known_commands={"ls"})
    with pytest.raises(ParseError):
        p.parse("")


def test_parser_whitespace_only_raises():
    p = CommandParser(known_commands={"ls"})
    with pytest.raises(ParseError):
        p.parse("   ")


def test_parser_bom_stripped():
    p = CommandParser(known_commands={"ls"})
    parsed = p.parse("\ufeffls")
    assert isinstance(parsed, TraditionalCommand)
    assert parsed.name == "ls"


def test_parser_alias_redirects():
    p = CommandParser(known_commands={"list"}, aliases={"ll": "list"})
    parsed = p.parse("ll /tmp")
    assert isinstance(parsed, TraditionalCommand)
    assert parsed.name == "list"
    assert parsed.args == ["/tmp"]


def test_parser_unrecognized_single_word_raises():
    p = CommandParser(known_commands={"ls"})
    with pytest.raises(ParseError):
        p.parse("frobnicate")


def test_parser_natural_language_multi_word():
    p = CommandParser(known_commands={"ls"})
    parsed = p.parse("show me all files")
    assert isinstance(parsed, NaturalLanguageRequest)
    assert parsed.text == "show me all files"


def test_parser_colon_prefix_forces_nl():
    p = CommandParser(known_commands={"ls"})
    parsed = p.parse(":list files in /tmp")
    assert isinstance(parsed, NaturalLanguageRequest)
    assert parsed.text == "list files in /tmp"


def test_parser_flag_short_boolean():
    p = CommandParser(known_commands={"rm"})
    parsed = p.parse("rm -r src")
    assert isinstance(parsed, TraditionalCommand)
    assert parsed.flags.get("r") is None
    assert parsed.args == ["src"]


def test_parser_long_flag_with_equals():
    p = CommandParser(known_commands={"find"})
    parsed = p.parse("find . --name=*.py")
    assert isinstance(parsed, TraditionalCommand)
    assert parsed.flags.get("name") == "*.py"


def test_parser_long_flag_with_next_token():
    p = CommandParser(known_commands={"find"})
    parsed = p.parse("find . --name *.py")
    assert isinstance(parsed, TraditionalCommand)
    assert parsed.flags.get("name") == "*.py"


def test_parser_long_flag_standalone():
    p = CommandParser(known_commands={"find"})
    parsed = p.parse("find . --hidden")
    assert isinstance(parsed, TraditionalCommand)
    assert parsed.flags.get("hidden") is None


def test_parser_traditional_command_as_shell_string():
    cmd = TraditionalCommand(name="ls", args=["-l"], flags={"l": None}, raw="ls -l")
    assert cmd.as_shell_string() == "ls -l"


def test_parser_nl_command_as_shell_string():
    req = NaturalLanguageRequest(text="list files", raw="list files")
    assert req.as_shell_string() == "list files"


def test_parser_register():
    p = CommandParser(known_commands=set())
    p.register("mycmd")
    assert "mycmd" in p.known_commands


# ----------------------------------------------------------------------
# Commands: find
# ----------------------------------------------------------------------


def test_find_default_all():
    root = _root()
    ctx = _ctx(root)
    (root / "a.py").write_text("x")
    (root / "b.py").write_text("y")
    res = cmd_find(["."], {}, ctx)
    assert res.success
    assert "a.py" in res.stdout
    assert "b.py" in res.stdout


def test_find_with_name_flag():
    root = _root()
    ctx = _ctx(root)
    (root / "a.py").write_text("x")
    (root / "b.txt").write_text("y")
    res = cmd_find(["."], {"name": "*.py"}, ctx)
    assert res.success
    assert "a.py" in res.stdout
    assert "b.txt" not in res.stdout


def test_find_no_match():
    root = _root()
    ctx = _ctx(root)
    res = cmd_find(["."], {"name": "*.xyz"}, ctx)
    assert res.success
    assert res.stdout == ""


def test_find_nonexistent_root():
    root = _root()
    ctx = _ctx(root)
    (root / "nonexistent_sub").mkdir()
    res = cmd_find(["nonexistent_sub/deep_xyz"], {}, ctx)
    assert not res.success
    assert "no such path" in res.stderr


def test_find_nested_dirs():
    root = _root()
    ctx = _ctx(root)
    (root / "sub").mkdir()
    (root / "sub" / "deep.py").write_text("z")
    res = cmd_find(["."], {"name": "*.py"}, ctx)
    assert res.success
    assert "deep.py" in res.stdout


def test_find_default_pattern():
    root = _root()
    ctx = _ctx(root)
    (root / "file1.txt").write_text("a")
    (root / "file2.log").write_text("b")
    res = cmd_find(["."], {}, ctx)
    assert res.success
    assert "file1.txt" in res.stdout
    assert "file2.log" in res.stdout


# ----------------------------------------------------------------------
# Commands: ps / kill
# ----------------------------------------------------------------------


def test_ps_returns_header():
    root = _root()
    ctx = _ctx(root)
    res = cmd_ps([], {}, ctx)
    assert res.success
    assert "PID" in res.stdout
    assert "NAME" in res.stdout


def test_kill_missing_pid():
    root = _root()
    ctx = _ctx(root)
    res = cmd_kill([], {}, ctx)
    assert not res.success
    assert "missing pid" in res.stderr


def test_kill_invalid_pid():
    root = _root()
    ctx = _ctx(root)
    res = cmd_kill(["abc"], {}, ctx)
    assert not res.success
    assert "invalid pid" in res.stderr


def test_kill_nonexistent_pid():
    from unittest.mock import patch

    root = _root()
    ctx = _ctx(root)
    with patch("arcanis_shell.commands.kill_process", side_effect=ProcessLookupError("no such process")):
        res = cmd_kill(["99999999"], {}, ctx)
    assert not res.success
    assert "no such pid" in res.stderr


# ----------------------------------------------------------------------
# Commands: sysinfo
# ----------------------------------------------------------------------


def test_sysinfo_returns_platform_info():
    root = _root()
    ctx = _ctx(root)
    res = cmd_sysinfo([], {}, ctx)
    assert res.success
    assert "system" in res.stdout
    assert "python" in res.stdout
    assert "cores" in res.stdout


# ----------------------------------------------------------------------
# Commands: echo
# ----------------------------------------------------------------------


def test_echo_single_arg():
    root = _root()
    ctx = _ctx(root)
    res = cmd_echo(["hello"], {}, ctx)
    assert res.success
    assert res.stdout == "hello"


def test_echo_multiple_args():
    root = _root()
    ctx = _ctx(root)
    res = cmd_echo(["hello", "world"], {}, ctx)
    assert res.success
    assert res.stdout == "hello world"


def test_echo_no_args():
    root = _root()
    ctx = _ctx(root)
    res = cmd_echo([], {}, ctx)
    assert res.success
    assert res.stdout == ""


# ----------------------------------------------------------------------
# Commands: which
# ----------------------------------------------------------------------


def test_which_found():
    root = _root()
    ctx = _ctx(root)
    res = cmd_which(["python"], {}, ctx)
    assert res.success
    assert len(res.stdout) > 0


def test_which_not_found():
    root = _root()
    ctx = _ctx(root)
    res = cmd_which(["nonexistent_cmd_xyz_123"], {}, ctx)
    assert not res.success
    assert "not found" in res.stderr


def test_which_missing_arg():
    root = _root()
    ctx = _ctx(root)
    res = cmd_which([], {}, ctx)
    assert not res.success
    assert "missing command" in res.stderr


# ----------------------------------------------------------------------
# Commands: env
# ----------------------------------------------------------------------


def test_env_returns_vars():
    root = _root()
    ctx = _ctx(root)
    res = cmd_env([], {}, ctx)
    assert res.success
    assert "PATH=" in res.stdout


def test_env_sorted():
    root = _root()
    ctx = _ctx(root)
    res = cmd_env([], {}, ctx)
    lines = res.stdout.split("\n")
    keys = [line.split("=", 1)[0] for line in lines]
    assert keys == sorted(keys, key=str.casefold)


# ----------------------------------------------------------------------
# Commands: cp
# ----------------------------------------------------------------------


def test_cp_file_to_file():
    root = _root()
    ctx = _ctx(root)
    (root / "src.txt").write_text("content")
    res = cmd_cp(["src.txt", "dst.txt"], {}, ctx)
    assert res.success
    assert (root / "dst.txt").read_text() == "content"


def test_cp_file_to_dir():
    root = _root()
    ctx = _ctx(root)
    (root / "src.txt").write_text("content")
    (root / "dest").mkdir()
    res = cmd_cp(["src.txt", "dest"], {}, ctx)
    assert res.success
    assert (root / "dest" / "src.txt").read_text() == "content"


def test_cp_missing_operands():
    root = _root()
    ctx = _ctx(root)
    res = cmd_cp([], {}, ctx)
    assert not res.success
    assert "missing operands" in res.stderr


def test_cp_single_operand():
    root = _root()
    ctx = _ctx(root)
    res = cmd_cp(["src.txt"], {}, ctx)
    assert not res.success
    assert "missing operands" in res.stderr


def test_cp_nonexistent_source():
    root = _root()
    ctx = _ctx(root)
    res = cmd_cp(["nope.txt", "dst.txt"], {}, ctx)
    assert not res.success
    assert "no such file" in res.stderr


def test_cp_dir_to_dir():
    root = _root()
    ctx = _ctx(root)
    (root / "srcdir").mkdir()
    (root / "srcdir" / "file.txt").write_text("data")
    (root / "destdir").mkdir()
    res = cmd_cp(["srcdir", "destdir"], {}, ctx)
    assert res.success
    assert (root / "destdir" / "srcdir" / "file.txt").exists()


def test_cp_glob_no_match():
    root = _root()
    ctx = _ctx(root)
    (root / "dest").mkdir()
    res = cmd_cp(["*.xyz", "dest"], {}, ctx)
    assert res.success
    assert "no-op" in res.stdout.lower() or "no source" in res.stdout.lower()


# ----------------------------------------------------------------------
# Commands: mv
# ----------------------------------------------------------------------


def test_mv_file_to_file():
    root = _root()
    ctx = _ctx(root)
    (root / "a.txt").write_text("hello")
    res = cmd_mv(["a.txt", "b.txt"], {}, ctx)
    assert res.success
    assert not (root / "a.txt").exists()
    assert (root / "b.txt").read_text() == "hello"


def test_mv_file_to_dir():
    root = _root()
    ctx = _ctx(root)
    (root / "a.txt").write_text("hello")
    (root / "dest").mkdir()
    res = cmd_mv(["a.txt", "dest"], {}, ctx)
    assert res.success
    assert (root / "dest" / "a.txt").read_text() == "hello"


def test_mv_missing_operands():
    root = _root()
    ctx = _ctx(root)
    res = cmd_mv([], {}, ctx)
    assert not res.success
    assert "missing operands" in res.stderr


def test_mv_nonexistent_source():
    root = _root()
    ctx = _ctx(root)
    res = cmd_mv(["nope.txt", "dst.txt"], {}, ctx)
    assert not res.success
    assert "no such file" in res.stderr


def test_mv_glob_no_match():
    root = _root()
    ctx = _ctx(root)
    (root / "dest").mkdir()
    res = cmd_mv(["*.xyz", "dest"], {}, ctx)
    assert res.success
    assert "no-op" in res.stdout.lower() or "no source" in res.stdout.lower()


# ----------------------------------------------------------------------
# Commands: cat error paths
# ----------------------------------------------------------------------


def test_cat_no_args():
    root = _root()
    ctx = _ctx(root)
    res = cmd_cat([], {}, ctx)
    assert not res.success
    assert "missing file argument" in res.stderr


def test_cat_not_a_file():
    root = _root()
    ctx = _ctx(root)
    (root / "subdir").mkdir()
    res = cmd_cat(["subdir"], {}, ctx)
    assert not res.success
    assert "not a file" in res.stderr


# ----------------------------------------------------------------------
# Commands: mkdir error paths
# ----------------------------------------------------------------------


def test_mkdir_no_args():
    root = _root()
    ctx = _ctx(root)
    res = cmd_mkdir([], {}, ctx)
    assert not res.success
    assert "missing operand" in res.stderr


def test_mkdir_exists_without_p():
    root = _root()
    ctx = _ctx(root)
    (root / "existing").mkdir()
    res = cmd_mkdir(["existing"], {}, ctx)
    assert not res.success
    assert "exists" in res.stderr


def test_mkdir_with_p_exists():
    root = _root()
    ctx = _ctx(root)
    (root / "a").mkdir()
    res = cmd_mkdir(["a/b"], {"p": None}, ctx)
    assert res.success


# ----------------------------------------------------------------------
# Commands: rm error paths
# ----------------------------------------------------------------------


def test_rm_no_args():
    root = _root()
    ctx = _ctx(root)
    res = cmd_rm([], {}, ctx)
    assert not res.success
    assert "missing operand" in res.stderr


def test_rm_nonexistent_file():
    root = _root()
    ctx = _ctx(root)
    res = cmd_rm(["nope.txt"], {}, ctx)
    assert not res.success
    assert "no such file" in res.stderr


def test_rm_empty_glob():
    root = _root()
    ctx = _ctx(root)
    res = cmd_rm(["*.xyz"], {}, ctx)
    assert not res.success
    assert "no such file" in res.stderr


def test_rm_file_without_r_flag():
    root = _root()
    ctx = _ctx(root)
    (root / "file.txt").write_text("x")
    res = cmd_rm(["file.txt"], {}, ctx)
    assert res.success


def test_rm_dir_without_r_flag():
    root = _root()
    ctx = _ctx(root)
    (root / "subdir").mkdir()
    res = cmd_rm(["subdir"], {}, ctx)
    assert not res.success
    assert "is a directory" in res.stderr


# ----------------------------------------------------------------------
# Commands: ls error paths
# ----------------------------------------------------------------------


def test_ls_nonexistent():
    root = _root()
    ctx = _ctx(root)
    res = cmd_ls(["nonexistent_xyz_file.txt"], {}, ctx)
    assert not res.success
    assert "no such path" in res.stderr


def test_ls_single_file():
    root = _root()
    ctx = _ctx(root)
    (root / "file.txt").write_text("x")
    res = cmd_ls(["file.txt"], {}, ctx)
    assert res.success
    assert "file.txt" in res.stdout


# ----------------------------------------------------------------------
# Commands: tree
# ----------------------------------------------------------------------


def test_tree_non_directory():
    root = _root()
    ctx = _ctx(root)
    (root / "file.txt").write_text("x")
    res = cmd_tree(["file.txt"], {}, ctx)
    assert not res.success
    assert "not a directory" in res.stderr


def test_tree_nested():
    root = _root()
    ctx = _ctx(root)
    (root / "a").mkdir()
    (root / "a" / "b").mkdir()
    (root / "a" / "b" / "c.txt").write_text("z")
    res = cmd_tree([], {}, ctx)
    assert res.success
    assert "a" in res.stdout
    assert "b" in res.stdout
    assert "c.txt" in res.stdout


# ----------------------------------------------------------------------
# Commands: cd
# ----------------------------------------------------------------------


def test_cd_existing_dir():
    root = _root()
    ctx = _ctx(root)
    (root / "sub").mkdir()
    res = cmd_cd(["sub"], {}, ctx)
    assert res.success
    assert ctx.cwd == (root / "sub").resolve()


def test_cd_nonexistent():
    root = _root()
    ctx = _ctx(root)
    res = cmd_cd(["nonexistent_xyz"], {}, ctx)
    assert not res.success
    assert "not a directory" in res.stderr


def test_cd_no_args_goes_to_root():
    root = _root()
    ctx = _ctx(root)
    (root / "sub").mkdir()
    ctx.cwd = root / "sub"
    res = cmd_cd([], {}, ctx)
    assert res.success
    assert ctx.cwd == root.resolve()


# ----------------------------------------------------------------------
# Commands: run (script execution)
# ----------------------------------------------------------------------


def test_run_no_args():
    root = _root()
    ctx = _ctx(root)
    res = cmd_run([], {}, ctx)
    assert not res.success
    assert "missing script path" in res.stderr


def test_run_nonexistent_script():
    root = _root()
    ctx = _ctx(root)
    res = cmd_run(["nope.arc"], {}, ctx)
    assert not res.success
    assert "no such script" in res.stderr


def test_run_script_with_failing_command():
    root = _root()
    ctx = _ctx(root)
    script = root / "fail.arc"
    script.write_text("rm sub\n")
    (root / "sub").mkdir()
    res = cmd_run(["fail.arc"], {}, ctx)
    assert not res.success
    assert res.exit_code == 1


def test_run_script_with_comment_only():
    root = _root()
    ctx = _ctx(root)
    script = root / "comments.arc"
    script.write_text("# just a comment\n# another comment\n")
    res = cmd_run(["comments.arc"], {}, ctx)
    assert res.success


def test_run_script_with_echo():
    root = _root()
    ctx = _ctx(root)
    script = root / "echo.arc"
    script.write_text("echo hello world\n")
    res = cmd_run(["echo.arc"], {}, ctx)
    assert res.success
    assert "hello world" in res.stdout


# ----------------------------------------------------------------------
# ShellEngine: different inputs
# ----------------------------------------------------------------------


def test_engine_execute_empty_string():
    eng = _engine()
    res = eng.execute("")
    assert not res.success
    assert "parse error" in res.stderr.lower()


def test_engine_execute_whitespace():
    eng = _engine()
    res = eng.execute("   ")
    assert not res.success


def test_engine_execute_unknown_command():
    eng = _engine()
    res = eng.execute("frobnicate")
    assert not res.success
    assert "unrecognized command" in res.stderr.lower()


def test_engine_execute_parse_error_logged():
    eng = _engine()
    eng.execute("")
    assert any(e.outcome == "parse_error" for e in eng.log)


def test_engine_cd_changes_cwd():
    eng = _engine()
    root = eng.config.sandbox_root
    (root / "subdir").mkdir()
    eng.execute("cd subdir")
    assert eng.cwd == (root / "subdir").resolve()


def test_engine_pwd_returns_cwd():
    eng = _engine()
    res = eng.execute("pwd")
    assert res.success
    assert str(eng.config.sandbox_root.resolve()) in res.stdout


def test_engine_execute_multiple_commands():
    eng = _engine()
    r1 = eng.execute("mkdir testdir")
    assert r1.success
    r2 = eng.execute("ls")
    assert r2.success
    assert "testdir" in r2.stdout


def test_engine_history_tracked():
    eng = _engine()
    eng.execute("ls")
    eng.execute("pwd")
    assert len(eng._history) == 2
    assert eng._history[0] == "ls"
    assert eng._history[1] == "pwd"


def test_engine_execute_cp_via_engine():
    eng = _engine()
    root = eng.config.sandbox_root
    (root / "original.txt").write_text("hello")
    res = eng.execute("cp original.txt copy.txt")
    assert res.success
    assert (root / "copy.txt").read_text() == "hello"


def test_engine_execute_mv_via_engine():
    eng = _engine()
    root = eng.config.sandbox_root
    (root / "move_me.txt").write_text("data")
    res = eng.execute("mv move_me.txt moved.txt")
    assert res.success
    assert not (root / "move_me.txt").exists()
    assert (root / "moved.txt").read_text() == "data"


def test_engine_execute_find_via_engine():
    eng = _engine()
    root = eng.config.sandbox_root
    (root / "target.py").write_text("code")
    res = eng.execute("find . --name *.py")
    assert res.success
    assert "target.py" in res.stdout


def test_engine_execute_ps_via_engine():
    eng = _engine()
    res = eng.execute("ps")
    assert res.success
    assert "PID" in res.stdout


def test_engine_execute_sysinfo_via_engine():
    eng = _engine()
    res = eng.execute("sysinfo")
    assert res.success
    assert "python" in res.stdout


def test_engine_execute_echo_via_engine():
    eng = _engine()
    res = eng.execute("echo hello")
    assert res.success
    assert res.stdout == "hello"


def test_engine_execute_env_via_engine():
    eng = _engine()
    res = eng.execute("env")
    assert res.success
    assert "PATH=" in res.stdout


def test_engine_execute_which_via_engine():
    eng = _engine()
    res = eng.execute("which python")
    assert res.success


def test_engine_log_records_on_success():
    eng = _engine()
    eng.execute("ls")
    assert len(eng.log) >= 1
    assert eng.log.recent(1)[0].outcome == "ok"


def test_engine_log_records_on_failure():
    eng = _engine()
    eng.execute("frobnicate")
    assert any(e.outcome in ("parse_error", "unknown_command") for e in eng.log)


# ----------------------------------------------------------------------
# Engine: permission / approval paths
# ----------------------------------------------------------------------


def test_engine_approval_rejected_for_nl():
    eng = _engine()
    eng.approval_fn = lambda p: False
    with pytest.raises(PlanRejectedError):
        eng.execute("ai organize my project files")
    assert any(e.outcome == "rejected" for e in eng.log)


def test_engine_permission_deny_blocks_execution():
    eng = _engine()
    eng.policy.deny_list.add("ls")
    res = eng.execute("ls")
    assert not res.success
    assert "denied" in res.stderr.lower() or "permission" in res.stderr.lower()


def test_engine_permission_deny_logged():
    eng = _engine()
    eng.policy.deny_list.add("ls")
    eng.execute("ls")
    assert any(e.outcome == "denied" for e in eng.log)


def test_engine_approval_for_medium_risk_command():
    eng = _engine()
    eng.policy.auto_approve_below = RiskLevel.LOW
    approved = []
    eng.approval_fn = lambda p: (approved.append(p.intent), True)[-1]
    eng.execute("rm -r something_that_does_not_exist")
    assert len(approved) >= 1


def test_engine_approval_rejection_for_medium_risk():
    eng = _engine()
    eng.policy.auto_approve_below = RiskLevel.LOW
    eng.approval_fn = lambda p: False
    res = eng.execute("rm -r something_that_does_not_exist")
    assert not res.success
    assert "rejected" in res.stderr


# ----------------------------------------------------------------------
# AI Interface
# ----------------------------------------------------------------------


def test_ai_interface_understand():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    plan = ai.understand("organize my project files", {"cwd": "/tmp"})
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) > 0


def test_ai_interface_explain_rm():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    exp = ai.explain("rm -r old")
    assert isinstance(exp, Explanation)
    assert "Irreversible" in exp.risks[0]


def test_ai_interface_explain_mv():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    exp = ai.explain("mv a.txt b.txt")
    assert "Move" in exp.summary or "move" in exp.summary


def test_ai_interface_explain_cp():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    exp = ai.explain("cp a.txt b.txt")
    assert "Copy" in exp.summary or "copy" in exp.summary


def test_ai_interface_explain_mkdir():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    exp = ai.explain("mkdir build")
    assert "Create" in exp.summary or "create" in exp.summary


def test_ai_interface_explain_kill():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    exp = ai.explain("kill 1234")
    assert "Terminate" in exp.summary or "terminate" in exp.summary


def test_ai_interface_explain_run():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    exp = ai.explain("run deploy.arc")
    assert "Execute" in exp.summary or "execute" in exp.summary


def test_ai_interface_explain_unknown():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    exp = ai.explain("frobnicate")
    assert "traditional" in exp.summary.lower() or "Execute" in exp.summary


def test_ai_interface_suggest():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    suggestions = ai.suggest({"cwd": "/tmp"})
    assert len(suggestions) > 0
    assert any("ls" in s for s in suggestions)


def test_ai_interface_generate_automation():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    script = ai.generate_automation("organize my project files", {"cwd": "/tmp"})
    assert script.startswith("#")
    assert "mkdir" in script


def test_ai_interface_delegate_no_agents():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain, agents=None)
    plan = ExecutionPlan(
        intent="test",
        summary="test",
        steps=[PlanStep(index=0, description="test", command="ls", risk=RiskLevel.SAFE)],
    )
    result = ai.delegate_to_agents(plan)
    assert result["status"] == "no_agents_backend"


def test_ai_interface_delegate_with_agents():
    brain = LocalBrainAdapter()
    agents = LocalAgentsAdapter()
    ai = AIInterface(brain, agents=agents)
    plan = ExecutionPlan(
        intent="test",
        summary="test",
        steps=[PlanStep(index=0, description="test", command="ls", risk=RiskLevel.SAFE)],
    )
    result = ai.delegate_to_agents(plan)
    assert "delegated" in result.get("status", "").lower() or "offline" in result.get("status", "").lower()


def test_ai_interface_plan_risk_levels():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    plan = ai.understand("organize my project files", {"cwd": "/tmp"})
    for step in plan.steps:
        assert isinstance(step.risk, RiskLevel)


def test_ai_interface_understand_fallback():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    plan = ai.understand("do something random", {"cwd": "/tmp"})
    assert isinstance(plan, ExecutionPlan)
    assert plan.intent == "do something random"


def test_ai_interface_list_files():
    brain = LocalBrainAdapter()
    ai = AIInterface(brain)
    plan = ai.understand("list files", {"cwd": "/tmp"})
    assert any("ls" in s.command for s in plan.steps)


# ----------------------------------------------------------------------
# AIInterface via engine explain methods
# ----------------------------------------------------------------------


def test_engine_explain_returns_string():
    eng = _engine()
    text = eng.explain("cp a.txt b.txt")
    assert isinstance(text, str)
    assert "Copy" in text or "copy" in text


def test_engine_suggest_returns_list():
    eng = _engine()
    suggestions = eng.suggest()
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0


def test_engine_generate_automation_returns_string():
    eng = _engine()
    script = eng.generate_automation("organize my project files")
    assert isinstance(script, str)
    assert script.startswith("#")


# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------


def test_config_default():
    cfg = ShellConfig.default()
    assert cfg.ai_backend == "arcanis_brain"
    assert cfg.prompt == "arcanis ❯"
    assert cfg.auto_approve_ai is False
    assert cfg.allow_sandbox_writes is True
    assert cfg.enable_network is False
    assert isinstance(cfg.sandbox_root, Path)
    assert isinstance(cfg.history_file, Path)


def test_config_from_file():
    root = _root()
    cfg_path = root / "test.toml"
    cfg_path.write_text(
        'sandbox_root = "/tmp/test_sandbox"\n'
        'ai_backend = "custom_brain"\n'
        'prompt = "custom ❯"\n'
        'auto_approve_ai = true\n'
        'allow_sandbox_writes = false\n'
        'enable_network = true\n'
    )
    cfg = ShellConfig.from_file(cfg_path)
    assert cfg.sandbox_root == Path("/tmp/test_sandbox")
    assert cfg.ai_backend == "custom_brain"
    assert cfg.prompt == "custom ❯"
    assert cfg.auto_approve_ai is True
    assert cfg.allow_sandbox_writes is False
    assert cfg.enable_network is True


def test_config_from_file_partial():
    root = _root()
    cfg_path = root / "partial.toml"
    cfg_path.write_text('sandbox_root = "/tmp/partial"\n')
    cfg = ShellConfig.from_file(cfg_path)
    assert cfg.sandbox_root == Path("/tmp/partial")
    assert cfg.ai_backend == "arcanis_brain"
    assert cfg.prompt == "arcanis ❯"


def test_config_from_file_with_log():
    root = _root()
    cfg_path = root / "log.toml"
    cfg_path.write_text('log_file = "/tmp/test.log"\n')
    cfg = ShellConfig.from_file(cfg_path)
    assert cfg.log_file == Path("/tmp/test.log")


def test_config_from_file_log_false_keeps_default():
    root = _root()
    cfg_path = root / "nulllog.toml"
    cfg_path.write_text("log_file = false\n")
    cfg = ShellConfig.from_file(cfg_path)
    assert cfg.log_file is not None


# ----------------------------------------------------------------------
# Types / models
# ----------------------------------------------------------------------


def test_risk_level_values():
    assert RiskLevel.SAFE.value == "safe"
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.MEDIUM.value == "medium"
    assert RiskLevel.HIGH.value == "high"
    assert RiskLevel.CRITICAL.value == "critical"


def test_risk_level_ordering():
    order = list(RiskLevel)
    assert order.index(RiskLevel.SAFE) < order.index(RiskLevel.LOW)
    assert order.index(RiskLevel.LOW) < order.index(RiskLevel.MEDIUM)
    assert order.index(RiskLevel.MEDIUM) < order.index(RiskLevel.HIGH)
    assert order.index(RiskLevel.HIGH) < order.index(RiskLevel.CRITICAL)


def test_command_source_values():
    assert CommandSource.TRADITIONAL.value == "traditional"
    assert CommandSource.AI_GENERATED.value == "ai_generated"
    assert CommandSource.AUTOMATION.value == "automation"


def test_command_result_success():
    r = CommandResult(success=True, stdout="ok")
    assert r.success
    assert r.output == "ok"
    assert str(r) == "ok"
    assert r.exit_code == 0


def test_command_result_failure():
    r = CommandResult(success=False, stderr="error", exit_code=1)
    assert not r.success
    assert str(r) == "error"
    assert r.exit_code == 1


def test_command_result_metadata():
    r = CommandResult(success=True, metadata={"key": "value"})
    assert r.metadata["key"] == "value"


def test_command_spec_model():
    spec = CommandSpec(
        name="ls",
        description="List files",
        category="file",
        risk=RiskLevel.SAFE,
        examples=["ls", "ls -l"],
    )
    assert spec.name == "ls"
    assert spec.accepts_args is True
    assert spec.accepts_flags is True


def test_plan_step_model():
    step = PlanStep(
        index=0,
        description="List files",
        command="ls",
        risk=RiskLevel.SAFE,
        rationale="test",
    )
    assert step.index == 0
    assert step.risk == RiskLevel.SAFE


def test_execution_plan_model():
    steps = [
        PlanStep(index=0, description="step1", command="ls", risk=RiskLevel.SAFE),
        PlanStep(index=1, description="step2", command="mkdir x", risk=RiskLevel.LOW),
    ]
    plan = ExecutionPlan(intent="test", summary="test plan", steps=steps)
    assert plan.max_risk == RiskLevel.LOW
    assert plan.requires_approval is True


def test_execution_plan_empty_steps():
    plan = ExecutionPlan(intent="test", summary="test plan", steps=[])
    assert plan.max_risk == RiskLevel.SAFE


def test_execution_plan_max_risk_critical():
    steps = [
        PlanStep(index=0, description="step1", command="ls", risk=RiskLevel.SAFE),
        PlanStep(index=1, description="step2", command="rm -r /", risk=RiskLevel.CRITICAL),
    ]
    plan = ExecutionPlan(intent="danger", summary="dangerous", steps=steps)
    assert plan.max_risk == RiskLevel.CRITICAL


def test_activity_entry_dataclass():
    entry = ActivityEntry(
        timestamp="2024-01-01T00:00:00",
        source=CommandSource.TRADITIONAL,
        action="ls",
        risk=RiskLevel.SAFE,
        approved=True,
        outcome="ok",
    )
    assert entry.source == CommandSource.TRADITIONAL
    assert entry.approved is True


def test_activity_entry_with_detail():
    entry = ActivityEntry(
        timestamp="2024-01-01T00:00:00",
        source=CommandSource.AI_GENERATED,
        action="mkdir x",
        risk=RiskLevel.LOW,
        approved=True,
        outcome="ok",
        detail="created directory",
    )
    assert entry.detail == "created directory"


# ----------------------------------------------------------------------
# Security: Sandbox
# ----------------------------------------------------------------------


def test_sandbox_is_inside():
    root = _root()
    sb = Sandbox(root=root)
    assert sb.is_inside(root / "file.txt")
    assert not sb.is_inside(Path("/some/other/path"))


def test_sandbox_require_inside():
    root = _root()
    sb = Sandbox(root=root)
    result = sb.require_inside(root / "file.txt")
    assert result == (root / "file.txt").resolve()


def test_sandbox_require_inside_violation():
    root = _root()
    sb = Sandbox(root=root)
    with pytest.raises(SandboxViolationError):
        sb.require_inside(Path("/etc/passwd"))


def test_sandbox_guard_write_blocked():
    root = _root()
    sb = Sandbox(root=root, allow_write=False)
    with pytest.raises(SandboxViolationError):
        sb.guard_write()


def test_sandbox_guard_write_allowed():
    root = _root()
    sb = Sandbox(root=root, allow_write=True)
    sb.guard_write()


def test_sandbox_guard_network_blocked():
    root = _root()
    sb = Sandbox(root=root, allow_network=False)
    with pytest.raises(SandboxViolationError):
        sb.guard_network()


def test_sandbox_guard_network_allowed():
    root = _root()
    sb = Sandbox(root=root, allow_network=True)
    sb.guard_network()


def test_sandbox_guard_subprocess_blocked():
    root = _root()
    sb = Sandbox(root=root, allow_subprocess=False)
    with pytest.raises(SandboxViolationError):
        sb.guard_subprocess(CommandSource.AI_GENERATED, RiskLevel.LOW)


def test_sandbox_guard_subprocess_traditional_allowed():
    root = _root()
    sb = Sandbox(root=root, allow_subprocess=False)
    sb.guard_subprocess(CommandSource.TRADITIONAL, RiskLevel.LOW)


def test_sandbox_guard_subprocess_allowed():
    root = _root()
    sb = Sandbox(root=root, allow_subprocess=True)
    sb.guard_subprocess(CommandSource.AI_GENERATED, RiskLevel.LOW)


def test_sandbox_allowed_paths():
    root = _root()
    sb = Sandbox(root=root)
    paths = list(sb.allowed_paths())
    assert len(paths) == 1
    assert paths[0] == root.resolve()


def test_sandbox_is_inside_root_itself():
    root = _root()
    sb = Sandbox(root=root)
    assert sb.is_inside(root)


# ----------------------------------------------------------------------
# Security: PermissionPolicy
# ----------------------------------------------------------------------


def test_policy_is_denied():
    p = PermissionPolicy()
    p.deny_list.add("rm")
    assert p.is_denied("rm")
    assert not p.is_denied("ls")


def test_policy_is_explicitly_allowed():
    p = PermissionPolicy()
    p.allow_list.add("ls")
    assert p.is_explicitly_allowed("ls")
    assert not p.is_explicitly_allowed("rm")


def test_policy_deny_overrides_allow():
    p = PermissionPolicy()
    p.deny_list.add("ls")
    p.allow_list.add("ls")
    assert p.is_denied("ls")
    with pytest.raises(PermissionDeniedError):
        p.check("ls", RiskLevel.SAFE, CommandSource.TRADITIONAL)


def test_policy_check_deny_raises():
    p = PermissionPolicy()
    p.deny_list.add("kill")
    with pytest.raises(PermissionDeniedError):
        p.check("kill", RiskLevel.HIGH, CommandSource.TRADITIONAL)


def test_policy_check_allowed_no_raise():
    p = PermissionPolicy()
    p.check("ls", RiskLevel.SAFE, CommandSource.TRADITIONAL)


def test_policy_needs_approval_ai_source():
    p = PermissionPolicy()
    assert p.needs_approval("ls", RiskLevel.SAFE, CommandSource.AI_GENERATED)


def test_policy_needs_approval_allow_list_overrides_ai():
    p = PermissionPolicy()
    p.allow_list.add("ls")
    assert not p.needs_approval("ls", RiskLevel.SAFE, CommandSource.AI_GENERATED)


def test_policy_needs_approval_medium_risk():
    p = PermissionPolicy()
    assert p.needs_approval("rm", RiskLevel.MEDIUM, CommandSource.TRADITIONAL)


def test_policy_needs_approval_low_risk():
    p = PermissionPolicy()
    assert p.needs_approval("ls", RiskLevel.LOW, CommandSource.TRADITIONAL)


def test_policy_auto_approve_safe_only():
    p = PermissionPolicy()
    assert not p.needs_approval("ls", RiskLevel.SAFE, CommandSource.TRADITIONAL)


def test_policy_needs_approval_critical_risk():
    p = PermissionPolicy()
    assert p.needs_approval("rm", RiskLevel.CRITICAL, CommandSource.TRADITIONAL)


def test_policy_deny_list_blocks_needs_approval():
    p = PermissionPolicy()
    p.deny_list.add("ls")
    assert p.needs_approval("ls", RiskLevel.SAFE, CommandSource.TRADITIONAL)


def test_policy_custom_auto_approve_below():
    p = PermissionPolicy(auto_approve_below=RiskLevel.MEDIUM)
    assert not p.needs_approval("ls", RiskLevel.SAFE, CommandSource.TRADITIONAL)
    assert not p.needs_approval("ls", RiskLevel.LOW, CommandSource.TRADITIONAL)
    assert p.needs_approval("ls", RiskLevel.MEDIUM, CommandSource.TRADITIONAL)
    assert p.needs_approval("rm", RiskLevel.HIGH, CommandSource.TRADITIONAL)


# ----------------------------------------------------------------------
# Security: ActivityLog
# ----------------------------------------------------------------------


def test_activity_log_record():
    log = ActivityLog()
    entry = log.record(
        CommandSource.TRADITIONAL, "ls", RiskLevel.SAFE, True, "ok"
    )
    assert entry.outcome == "ok"
    assert len(log) == 1


def test_activity_log_recent():
    log = ActivityLog()
    for i in range(5):
        log.record(
            CommandSource.TRADITIONAL, f"cmd{i}", RiskLevel.SAFE, True, "ok"
        )
    recent = log.recent(3)
    assert len(recent) == 3


def test_activity_log_iter():
    log = ActivityLog()
    log.record(CommandSource.TRADITIONAL, "ls", RiskLevel.SAFE, True, "ok")
    log.record(CommandSource.TRADITIONAL, "pwd", RiskLevel.SAFE, True, "ok")
    entries = list(log)
    assert len(entries) == 2


def test_activity_log_len():
    log = ActivityLog()
    assert len(log) == 0
    log.record(CommandSource.TRADITIONAL, "ls", RiskLevel.SAFE, True, "ok")
    assert len(log) == 1
    log.record(CommandSource.TRADITIONAL, "pwd", RiskLevel.SAFE, True, "ok")
    assert len(log) == 2


def test_activity_log_persists_to_file():
    root = _root()
    log_path = root / "activity.jsonl"
    log = ActivityLog(path=log_path)
    log.record(CommandSource.TRADITIONAL, "ls", RiskLevel.SAFE, True, "ok")
    content = log_path.read_text()
    assert "ls" in content
    assert "ok" in content


def test_activity_log_recent_limit_exceeds():
    log = ActivityLog()
    log.record(CommandSource.TRADITIONAL, "ls", RiskLevel.SAFE, True, "ok")
    recent = log.recent(100)
    assert len(recent) == 1


# ----------------------------------------------------------------------
# Script execution
# ----------------------------------------------------------------------


def test_script_run_blank_lines_and_comments():
    root = _root()
    ctx = _ctx(root)
    source = "\n\n# comment\n\n"
    result = run_script(source, ctx)
    assert result == ""


def test_script_run_echo():
    root = _root()
    ctx = _ctx(root)
    source = "echo hello\n"
    result = run_script(source, ctx)
    assert "hello" in result


def test_script_run_multiple_commands():
    root = _root()
    ctx = _ctx(root)
    source = "echo first\nmkdir testdir\necho done\n"
    result = run_script(source, ctx)
    assert "first" in result
    assert "done" in result
    assert (root / "testdir").exists()


def test_script_run_unknown_command_raises():
    root = _root()
    ctx = _ctx(root)
    source = "frobnicate\n"
    with pytest.raises(ShellRuntimeError, match="line 1"):
        run_script(source, ctx)


def test_script_run_failing_command_raises():
    root = _root()
    ctx = _ctx(root)
    (root / "existing").mkdir()
    source = "mkdir existing\n"
    with pytest.raises(ShellRuntimeError, match="line 1"):
        run_script(source, ctx)


def test_script_run_nl_line_raises():
    root = _root()
    ctx = _ctx(root)
    source = "organize my project files\n"
    with pytest.raises(ShellRuntimeError, match="natural language not allowed"):
        run_script(source, ctx)


def test_script_run_no_registry_raises():
    root = _root()
    sb = Sandbox(root=root)
    ctx = CommandContext(cwd=root, sandbox=sb, registry=None)
    with pytest.raises(ShellRuntimeError, match="no command registry"):
        run_script("echo hi\n", ctx)


# ----------------------------------------------------------------------
# Error types
# ----------------------------------------------------------------------


def test_permission_denied_error_str():
    e = PermissionDeniedError("rm", "denied by policy")
    assert "rm" in str(e)
    assert "denied by policy" in str(e)


def test_sandbox_violation_error_str():
    e = SandboxViolationError("filesystem access outside sandbox", Path("/etc"))
    assert "sandbox" in str(e).lower()


def test_sandbox_violation_error_no_path():
    e = SandboxViolationError("write disabled")
    assert "unknown" in str(e).lower() or "sandbox" in str(e).lower()


def test_command_not_found_error_str():
    e = CommandNotFoundError("frobnicate")
    assert "frobnicate" in str(e)


def test_parse_error_str_with_detail():
    e = ParseError("bad input", "unbalanced quotes")
    assert "bad input" in str(e)
    assert "unbalanced quotes" in str(e)


def test_parse_error_str_without_detail():
    e = ParseError("bad input")
    assert "bad input" in str(e)


def test_plan_rejected_error_str():
    e = PlanRejectedError(step_count=3)
    assert "3" in str(e)


def test_ai_unavailable_error_str_with_detail():
    e = AIUnavailableError("my_backend", "timeout")
    assert "my_backend" in str(e)
    assert "timeout" in str(e)


def test_ai_unavailable_error_str_without_detail():
    e = AIUnavailableError("my_backend")
    assert "my_backend" in str(e)


def test_shell_runtime_error_str():
    e = ShellRuntimeError("something broke")
    assert "something broke" in str(e)


def test_shell_runtime_error_with_context():
    e = ShellRuntimeError("error", context={"line": 5})
    assert e.context["line"] == 5


def test_arcantis_shell_error_is_base():
    assert issubclass(PermissionDeniedError, ArcanisShellError)
    assert issubclass(SandboxViolationError, ArcanisShellError)
    assert issubclass(ParseError, ArcanisShellError)
    assert issubclass(PlanRejectedError, ArcanisShellError)
    assert issubclass(AIUnavailableError, ArcanisShellError)
    assert issubclass(ShellRuntimeError, ArcanisShellError)
    assert issubclass(CommandNotFoundError, ArcanisShellError)


# ----------------------------------------------------------------------
# Integration adapters
# ----------------------------------------------------------------------


def test_local_brain_organize():
    brain = LocalBrainAdapter()
    resp = brain.understand("organize my project files", {"cwd": "/tmp"})
    assert isinstance(resp, BrainResponse)
    assert len(resp.plan_steps) > 0
    assert resp.confidence > 0


def test_local_brain_list():
    brain = LocalBrainAdapter()
    resp = brain.understand("list files", {"cwd": "/tmp"})
    assert any("ls" in s.get("command", "") for s in resp.plan_steps)


def test_local_brain_fallback():
    brain = LocalBrainAdapter()
    resp = brain.understand("random unknown request", {"cwd": "/tmp"})
    assert len(resp.plan_steps) == 1
    assert "echo" in resp.plan_steps[0].get("command", "")


def test_local_agents_delegate():
    agents = LocalAgentsAdapter()
    result = agents.delegate({"intent": "test", "steps": []})
    assert result["status"] == "delegated_offline"


def test_local_os_filesystem_root():
    os_adapter = LocalOSAdapter()
    root = os_adapter.filesystem_root()
    assert isinstance(root, str)
    assert len(root) > 0


def test_local_os_security_token():
    os_adapter = LocalOSAdapter()
    token = os_adapter.security_token()
    assert token is None


def test_load_brain_default():
    brain = load_brain("arcanis_brain")
    assert isinstance(brain, BrainAdapter)


def test_load_brain_custom():
    brain = load_brain("custom_backend")
    assert isinstance(brain, BrainAdapter)


def test_load_agents():
    agents = load_agents()
    assert isinstance(agents, AgentsAdapter)


def test_load_os():
    os_adapter = load_os()
    assert isinstance(os_adapter, OSAdapter)


# ----------------------------------------------------------------------
# Command registry
# ----------------------------------------------------------------------


def test_build_registry_has_all_commands():
    reg = build_registry()
    expected = {
        "ls", "cat", "mkdir", "rm", "cp", "mv", "find", "tree",
        "ps", "kill", "sysinfo", "pwd", "echo", "cd", "which", "env", "run",
    }
    assert reg.names() == expected


def test_registry_get():
    reg = build_registry()
    cmd = reg.get("ls")
    assert cmd is not None
    assert cmd.name == "ls"


def test_registry_get_missing():
    reg = build_registry()
    cmd = reg.get("nonexistent")
    assert cmd is None


def test_registry_all():
    reg = build_registry()
    all_cmds = reg.all()
    assert len(all_cmds) == 17


def test_registry_register():
    reg = Registry()
    from arcanis_shell.commands import cmd_ls as fn
    cmd = Command(name="ls", fn=fn, description="list", category="file")
    reg.register(cmd)
    assert reg.get("ls") is not None
    assert "ls" in reg.names()


def test_command_risk_levels():
    reg = build_registry()
    assert reg.get("ls").risk == RiskLevel.SAFE
    assert reg.get("rm").risk == RiskLevel.MEDIUM
    assert reg.get("kill").risk == RiskLevel.HIGH
    assert reg.get("run").risk == RiskLevel.MEDIUM
    assert reg.get("ps").risk == RiskLevel.SAFE


def test_command_categories():
    reg = build_registry()
    assert reg.get("ls").category == "file"
    assert reg.get("ps").category == "process"
    assert reg.get("sysinfo").category == "system"
    assert reg.get("run").category == "script"


def test_command_examples():
    reg = build_registry()
    assert len(reg.get("ls").examples) > 0
    assert len(reg.get("find").examples) > 0


# ----------------------------------------------------------------------
# Engine: sandbox escape attempts
# ----------------------------------------------------------------------


def test_engine_sandbox_blocks_cat_escape():
    eng = _engine()
    res = eng.execute("cat ../secret")
    assert not res.success


def test_engine_sandbox_blocks_ls_escape():
    eng = _engine()
    res = eng.execute("ls /etc")
    assert not res.success


def test_engine_sandbox_violation_logged():
    eng = _engine()
    eng.execute("cat ../secret")
    assert any(e.outcome == "sandbox_violation" for e in eng.log)


# ----------------------------------------------------------------------
# Engine: NL via AI
# ----------------------------------------------------------------------


def test_engine_nl_plan_unknown_intent():
    eng = _engine()
    res = eng.execute("ai do something random")
    assert res.success
    assert res.stdout


def test_engine_nl_plan_list_files():
    eng = _engine()
    res = eng.execute("ai list files")
    assert res.success


def test_engine_nl_plan_with_approval():
    eng = _engine()
    eng.approval_fn = lambda p: True
    res = eng.execute("ai organize my project files")
    assert res.success
    assert "project" in res.stdout.lower() or "mkdir" in res.stdout.lower()


def test_engine_nl_step_failure():
    eng = _engine()
    eng.policy.deny_list.add("mkdir")
    res = eng.execute("ai organize my project files")
    assert not res.success
