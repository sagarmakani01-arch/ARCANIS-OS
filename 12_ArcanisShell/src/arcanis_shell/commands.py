"""ArcanisShell — command registry and traditional command implementations.

Implements the traditional shell feature set:
  * File commands      (ls, cat, mkdir, rm, cp, mv, find, tree)
  * Process management (ps, kill)
  * System information (sysinfo, pwd, echo, cd)
  * Script execution   (run  — execute a .arc script file)

Each command is a callable returning a CommandResult. Commands are pure
with respect to the sandbox: file operations are constrained by the
provided Sandbox instance.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .errors import ShellRuntimeError
from .security.sandbox import Sandbox
from .types import CommandResult, CommandSource, RiskLevel

CommandFn = Callable[[list[str], dict[str, Optional[str]], "CommandContext"], CommandResult]


@dataclass
class CommandContext:
    """Execution context handed to every traditional command."""

    cwd: Path
    sandbox: Sandbox
    source: CommandSource = CommandSource.TRADITIONAL
    registry: Optional["Registry"] = None

    def resolve(self, target: str) -> Path:
        path = (
            (self.cwd / target).resolve()
            if not Path(target).is_absolute()
            else Path(target).resolve()
        )
        return self.sandbox.require_inside(path)


@dataclass
class Command:
    """A registered traditional command."""

    name: str
    fn: CommandFn
    description: str
    category: str
    risk: RiskLevel = RiskLevel.LOW
    examples: list[str] = field(default_factory=list)


class Registry:
    """Holds the set of available traditional commands."""

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, cmd: Command) -> None:
        self._commands[cmd.name] = cmd

    def get(self, name: str) -> Optional[Command]:
        return self._commands.get(name)

    def all(self) -> list[Command]:
        return list(self._commands.values())

    def names(self) -> set[str]:
        return set(self._commands)


# --------------------------------------------------------------------------
# File commands
# --------------------------------------------------------------------------


def cmd_ls(args: list[str], flags: dict[str, Optional[str]], ctx: CommandContext) -> CommandResult:
    target = ctx.resolve(args[0]) if args else ctx.cwd
    if not target.exists():
        return CommandResult(success=False, stderr=f"no such path: {target}", exit_code=1)
    if target.is_file():
        return CommandResult(success=True, stdout=str(target))
    entries = sorted(target.iterdir()) if target.is_dir() else []
    lines = [e.name + ("/" if e.is_dir() else "") for e in entries]
    return CommandResult(success=True, stdout="\n".join(lines))


def cmd_cat(
    args: list[str], _flags: dict[str, Optional[str]], ctx: CommandContext
) -> CommandResult:
    if not args:
        return CommandResult(success=False, stderr="cat: missing file argument", exit_code=1)
    out: list[str] = []
    for arg in args:
        path = ctx.resolve(arg)
        if not path.is_file():
            return CommandResult(success=False, stderr=f"cat: not a file: {path}", exit_code=1)
        out.append(path.read_text(encoding="utf-8", errors="replace"))
    return CommandResult(success=True, stdout="\n".join(out))


def cmd_mkdir(
    args: list[str], flags: dict[str, Optional[str]], ctx: CommandContext
) -> CommandResult:
    if not args:
        return CommandResult(success=False, stderr="mkdir: missing operand", exit_code=1)
    parents = "p" in flags or "parents" in flags
    created: list[str] = []
    for arg in args:
        path = ctx.resolve(arg)
        try:
            if parents:
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.mkdir()
            created.append(str(path))
        except FileExistsError:
            if not parents:
                return CommandResult(success=False, stderr=f"mkdir: exists: {path}", exit_code=1)
    return CommandResult(success=True, stdout="\n".join(created) or "ok")


def _expand(path_str: str, ctx: CommandContext) -> list[Path]:
    """Resolve a single argument, expanding glob patterns when present."""
    if any(ch in path_str for ch in "*?["):
        base = ctx.cwd if not Path(path_str).is_absolute() else ctx.sandbox.root
        matches = sorted(base.glob(path_str))
        return [ctx.sandbox.require_inside(m) for m in matches]
    return [ctx.resolve(path_str)]


def cmd_rm(args: list[str], flags: dict[str, Optional[str]], ctx: CommandContext) -> CommandResult:
    if not args:
        return CommandResult(success=False, stderr="rm: missing operand", exit_code=1)
    recursive = "r" in flags or "recursive" in flags
    removed: list[str] = []
    for arg in args:
        targets = _expand(arg, ctx)
        if not targets:
            return CommandResult(success=False, stderr=f"rm: no such file: {arg}", exit_code=1)
        for path in targets:
            if not path.exists():
                return CommandResult(success=False, stderr=f"rm: no such file: {path}", exit_code=1)
            if path.is_dir() and not recursive:
                return CommandResult(
                    success=False, stderr=f"rm: is a directory: {path} (use -r)", exit_code=1
                )
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed.append(str(path))
    return CommandResult(success=True, stdout="\n".join(removed) or "ok")


def cmd_cp(args: list[str], _flags: dict[str, Optional[str]], ctx: CommandContext) -> CommandResult:
    if len(args) < 2:
        return CommandResult(success=False, stderr="cp: missing operands", exit_code=1)
    dst = ctx.resolve(args[-1])
    sources = [s for a in args[:-1] for s in _expand(a, ctx)]
    if not sources:
        return CommandResult(
            success=True, stdout="cp: no source files matched (no-op)", exit_code=0
        )
    copied: list[str] = []
    for src in sources:
        if not src.exists():
            return CommandResult(success=False, stderr=f"cp: no such file: {src}", exit_code=1)
        target = dst / src.name if dst.is_dir() else dst
        if src.is_dir():
            shutil.copytree(src, target, dirs_exist_ok=True)
        else:
            shutil.copy2(src, target)
        copied.append(str(target))
    return CommandResult(success=True, stdout="\n".join(copied))


def cmd_mv(args: list[str], _flags: dict[str, Optional[str]], ctx: CommandContext) -> CommandResult:
    if len(args) < 2:
        return CommandResult(success=False, stderr="mv: missing operands", exit_code=1)
    dst = ctx.resolve(args[-1])
    sources = [s for a in args[:-1] for s in _expand(a, ctx)]
    if not sources:
        return CommandResult(
            success=True, stdout="mv: no source files matched (no-op)", exit_code=0
        )
    moved: list[str] = []
    for src in sources:
        if not src.exists():
            return CommandResult(success=False, stderr=f"mv: no such file: {src}", exit_code=1)
        target = dst / src.name if dst.is_dir() else dst
        shutil.move(str(src), str(target))
        moved.append(str(target))
    return CommandResult(success=True, stdout="\n".join(moved))


def cmd_find(
    args: list[str], flags: dict[str, Optional[str]], ctx: CommandContext
) -> CommandResult:
    root = ctx.resolve(args[0]) if args else ctx.cwd
    pattern = flags.get("name") or (args[1] if len(args) > 1 else "*")
    matches: list[str] = []
    if not root.exists():
        return CommandResult(success=False, stderr=f"find: no such path: {root}", exit_code=1)
    for path in root.rglob(pattern):
        matches.append(str(path))
    return CommandResult(success=True, stdout="\n".join(sorted(matches)))


def cmd_tree(
    args: list[str], _flags: dict[str, Optional[str]], ctx: CommandContext
) -> CommandResult:
    root = ctx.resolve(args[0]) if args else ctx.cwd
    if not root.is_dir():
        return CommandResult(success=False, stderr=f"tree: not a directory: {root}", exit_code=1)
    lines = [root.name]

    def walk(d: Path, prefix: str) -> None:
        items = sorted(d.iterdir())
        for i, item in enumerate(items):
            last = i == len(items) - 1
            branch = "└── " if last else "├── "
            lines.append(prefix + branch + item.name)
            if item.is_dir():
                walk(item, prefix + ("    " if last else "│   "))

    walk(root, "")
    return CommandResult(success=True, stdout="\n".join(lines))


# --------------------------------------------------------------------------
# Process management
# --------------------------------------------------------------------------


def cmd_ps(
    _args: list[str], _flags: dict[str, Optional[str]], _ctx: CommandContext
) -> CommandResult:
    lines = ["PID\tNAME"]
    for proc in sorted(psutil_processes(), key=lambda p: p["pid"]):
        lines.append(f"{proc['pid']}\t{proc['name']}")
    return CommandResult(success=True, stdout="\n".join(lines))


def cmd_kill(
    args: list[str], _flags: dict[str, Optional[str]], _ctx: CommandContext
) -> CommandResult:
    if not args:
        return CommandResult(success=False, stderr="kill: missing pid", exit_code=1)
    killed: list[str] = []
    for arg in args:
        try:
            pid = int(arg)
        except ValueError:
            return CommandResult(success=False, stderr=f"kill: invalid pid: {arg}", exit_code=1)
        try:
            kill_process(pid)
            killed.append(str(pid))
        except ProcessLookupError:
            return CommandResult(success=False, stderr=f"kill: no such pid: {pid}", exit_code=1)
    return CommandResult(success=True, stdout=f"killed: {', '.join(killed)}")


# --------------------------------------------------------------------------
# System information
# --------------------------------------------------------------------------


def cmd_sysinfo(
    _args: list[str], _flags: dict[str, Optional[str]], _ctx: CommandContext
) -> CommandResult:
    uname = platform.uname()
    info = [
        f"system : {uname.system} {uname.release}",
        f"node   : {uname.node}",
        f"machine: {uname.machine}",
        f"cpu    : {platform.processor() or 'unknown'}",
        f"python : {platform.python_version()}",
        f"cores  : {os.cpu_count()}",
    ]
    return CommandResult(success=True, stdout="\n".join(info))


def cmd_pwd(
    _args: list[str], _flags: dict[str, Optional[str]], ctx: CommandContext
) -> CommandResult:
    return CommandResult(success=True, stdout=str(ctx.cwd))


def cmd_echo(
    args: list[str], _flags: dict[str, Optional[str]], _ctx: CommandContext
) -> CommandResult:
    return CommandResult(success=True, stdout=" ".join(args))


def cmd_cd(args: list[str], _flags: dict[str, Optional[str]], ctx: CommandContext) -> CommandResult:
    target = ctx.resolve(args[0]) if args else ctx.sandbox.root
    if not target.is_dir():
        return CommandResult(success=False, stderr=f"cd: not a directory: {target}", exit_code=1)
    ctx.cwd = target
    return CommandResult(success=True, stdout=str(target))


def cmd_which(
    args: list[str], _flags: dict[str, Optional[str]], _ctx: CommandContext
) -> CommandResult:
    if not args:
        return CommandResult(success=False, stderr="which: missing command", exit_code=1)
    found = shutil.which(args[0])
    return CommandResult(
        success=found is not None,
        stdout=found or "",
        stderr="" if found else f"not found: {args[0]}",
    )


def cmd_env(
    _args: list[str], _flags: dict[str, Optional[str]], _ctx: CommandContext
) -> CommandResult:
    lines = [f"{k}={v}" for k, v in sorted(os.environ.items())]
    return CommandResult(success=True, stdout="\n".join(lines))


# --------------------------------------------------------------------------
# Script execution (.arc scripts)
# --------------------------------------------------------------------------


def cmd_run(
    args: list[str], _flags: dict[str, Optional[str]], ctx: CommandContext
) -> CommandResult:
    if not args:
        return CommandResult(success=False, stderr="run: missing script path", exit_code=1)
    script = ctx.resolve(args[0])
    if not script.is_file():
        return CommandResult(success=False, stderr=f"run: no such script: {script}", exit_code=1)
    source = script.read_text(encoding="utf-8")
    from .script import run_script

    try:
        output = run_script(source, ctx)
    except ShellRuntimeError as exc:
        return CommandResult(success=False, stderr=str(exc), exit_code=1)
    return CommandResult(success=True, stdout=output)


def build_registry() -> Registry:
    """Construct the default command registry."""
    reg = Registry()
    reg.register(
        Command("ls", cmd_ls, "List directory contents", "file", RiskLevel.SAFE, ["ls", "ls -l"])
    )
    reg.register(
        Command("cat", cmd_cat, "Print file contents", "file", RiskLevel.SAFE, ["cat notes.txt"])
    )
    reg.register(
        Command(
            "mkdir", cmd_mkdir, "Create directories", "file", RiskLevel.LOW, ["mkdir -p build/logs"]
        )
    )
    reg.register(
        Command(
            "rm", cmd_rm, "Remove files or directories", "file", RiskLevel.MEDIUM, ["rm -r old"]
        )
    )
    reg.register(
        Command(
            "cp", cmd_cp, "Copy files or directories", "file", RiskLevel.LOW, ["cp a.txt b.txt"]
        )
    )
    reg.register(
        Command("mv", cmd_mv, "Move/rename files", "file", RiskLevel.LOW, ["mv a.txt b.txt"])
    )
    reg.register(
        Command(
            "find",
            cmd_find,
            "Search for files by name",
            "file",
            RiskLevel.SAFE,
            ["find . --name '*.py'"],
        )
    )
    reg.register(
        Command("tree", cmd_tree, "Show directory tree", "file", RiskLevel.SAFE, ["tree src"])
    )
    reg.register(Command("ps", cmd_ps, "List running processes", "process", RiskLevel.SAFE, ["ps"]))
    reg.register(
        Command(
            "kill", cmd_kill, "Terminate a process by PID", "process", RiskLevel.HIGH, ["kill 1234"]
        )
    )
    reg.register(
        Command(
            "sysinfo", cmd_sysinfo, "Show system information", "system", RiskLevel.SAFE, ["sysinfo"]
        )
    )
    reg.register(
        Command("pwd", cmd_pwd, "Print working directory", "system", RiskLevel.SAFE, ["pwd"])
    )
    reg.register(
        Command("echo", cmd_echo, "Print arguments", "system", RiskLevel.SAFE, ["echo hello"])
    )
    reg.register(Command("cd", cmd_cd, "Change directory", "system", RiskLevel.SAFE, ["cd src"]))
    reg.register(
        Command("which", cmd_which, "Locate a command", "system", RiskLevel.SAFE, ["which python"])
    )
    reg.register(
        Command("env", cmd_env, "Show environment variables", "system", RiskLevel.SAFE, ["env"])
    )
    reg.register(
        Command(
            "run", cmd_run, "Execute an .arc script", "script", RiskLevel.MEDIUM, ["run deploy.arc"]
        )
    )

    # ---- Core Utilities (from 25_DeveloperTools) ----
    def cmd_grep(args, flags, ctx):
        from arcanis_utils.coreutils import grep
        pattern = args[0] if args else ""
        paths = args[1:] if len(args) > 1 else None
        result = grep(pattern, paths, ignore_case="i" in flags, invert="v" in flags,
                      count="c" in flags, line_number="n" in flags)
        return CommandResult(success=True, stdout=result)
    reg.register(Command("grep", cmd_grep, "Search for pattern in files", "text", RiskLevel.SAFE,
                         ["grep 'TODO' src/*.py", "grep -i error log.txt"]))

    def cmd_sed(args, flags, ctx):
        from arcanis_utils.coreutils import sed
        expr = args[0] if args else ""
        text = args[1] if len(args) > 1 else ""
        return CommandResult(success=True, stdout=sed(expr, text))
    reg.register(Command("sed", cmd_sed, "Stream editor (substitute)", "text", RiskLevel.SAFE,
                         ["sed 's/foo/bar/g' input.txt"]))

    def cmd_sort(args, flags, ctx):
        from arcanis_utils.coreutils import sort_lines
        text = args[0] if args else ""
        result = sort_lines(text, numeric="n" in flags, reverse="r" in flags, unique="u" in flags)
        return CommandResult(success=True, stdout=result)
    reg.register(Command("sort", cmd_sort, "Sort lines of text", "text", RiskLevel.SAFE,
                         ["sort names.txt", "sort -n -r scores.txt"]))

    def cmd_wc(args, flags, ctx):
        from arcanis_utils.coreutils import wc
        text = args[0] if args else ""
        return CommandResult(success=True, stdout=wc(text))
    reg.register(Command("wc", cmd_wc, "Count lines, words, characters", "text", RiskLevel.SAFE,
                         ["wc file.txt", "wc -l *.py"]))

    def cmd_head(args, flags, ctx):
        from arcanis_utils.coreutils import head
        n = int(flags.get("n", "10"))
        text = args[0] if args else ""
        return CommandResult(success=True, stdout=head(text, n))
    reg.register(Command("head", cmd_head, "Output first N lines", "text", RiskLevel.SAFE,
                         ["head -n 5 file.txt"]))

    def cmd_tail(args, flags, ctx):
        from arcanis_utils.coreutils import tail
        n = int(flags.get("n", "10"))
        text = args[0] if args else ""
        return CommandResult(success=True, stdout=tail(text, n))
    reg.register(Command("tail", cmd_tail, "Output last N lines", "text", RiskLevel.SAFE,
                         ["tail -n 20 log.txt"]))

    def cmd_diff(args, flags, ctx):
        from arcanis_utils.coreutils import diff
        if len(args) < 2:
            return CommandResult(success=False, stderr="diff: need two files", exit_code=1)
        return CommandResult(success=True, stdout=diff(args[0], args[1]))
    reg.register(Command("diff", cmd_diff, "Compare two files", "text", RiskLevel.SAFE,
                         ["diff old.txt new.txt"]))

    def cmd_touch_cmd(args, flags, ctx):
        from arcanis_utils.coreutils import touch
        for arg in args:
            touch(arg)
        return CommandResult(success=True, stdout="ok")
    reg.register(Command("touch", cmd_touch_cmd, "Create file or update timestamp", "file", RiskLevel.LOW,
                         ["touch newfile.txt"]))

    def cmd_chmod_cmd(args, flags, ctx):
        from arcanis_utils.coreutils import chmod
        if len(args) < 2:
            return CommandResult(success=False, stderr="chmod: need mode and file", exit_code=1)
        return CommandResult(success=True, stdout=chmod(args[0], args[1]))
    reg.register(Command("chmod", cmd_chmod_cmd, "Change file permissions", "file", RiskLevel.MEDIUM,
                         ["chmod 755 script.sh"]))

    def cmd_ln(args, flags, ctx):
        from arcanis_utils.coreutils import ln
        if len(args) < 2:
            return CommandResult(success=False, stderr="ln: need target and link", exit_code=1)
        ln(args[-2], args[-1], symbolic="s" in flags)
        return CommandResult(success=True, stdout="ok")
    reg.register(Command("ln", cmd_ln, "Create file link", "file", RiskLevel.LOW,
                         ["ln -s /bin/sh /usr/bin/sh"]))

    def cmd_uptime_cmd(args, flags, ctx):
        from arcanis_utils.coreutils import uptime_str
        return CommandResult(success=True, stdout=uptime_str())
    reg.register(Command("uptime", cmd_uptime_cmd, "Show system uptime", "system", RiskLevel.SAFE,
                         ["uptime"]))

    def cmd_date_cmd(args, flags, ctx):
        from arcanis_utils.coreutils import date_str
        fmt = args[0] if args else ""
        return CommandResult(success=True, stdout=date_str(fmt))
    reg.register(Command("date", cmd_date_cmd, "Show current date/time", "system", RiskLevel.SAFE,
                         ["date", "date '+%Y-%m-%d'"]))

    def cmd_cut(args, flags, ctx):
        from arcanis_utils.coreutils import cut
        d = flags.get("d", "\t")
        f = [int(x) for x in flags.get("f", "1").split(",")]
        text = args[0] if args else ""
        return CommandResult(success=True, stdout=cut(d, f, text))
    reg.register(Command("cut", cmd_cut, "Cut fields from lines", "text", RiskLevel.SAFE,
                         ["cut -d',' -f1,3 data.csv"]))

    def cmd_tr_cmd(args, flags, ctx):
        from arcanis_utils.coreutils import tr
        if len(args) < 3:
            return CommandResult(success=False, stderr="tr: need SET1 SET2 TEXT", exit_code=1)
        return CommandResult(success=True, stdout=tr(args[0], args[1], " ".join(args[2:])))
    reg.register(Command("tr", cmd_tr_cmd, "Translate characters", "text", RiskLevel.SAFE,
                         ["tr 'a-z' 'A-Z' hello"]))

    def cmd_rev(args, flags, ctx):
        from arcanis_utils.coreutils import rev
        text = args[0] if args else ""
        return CommandResult(success=True, stdout=rev(text))
    reg.register(Command("rev", cmd_rev, "Reverse text lines", "text", RiskLevel.SAFE,
                         ["rev file.txt"]))

    def cmd_seq(args, flags, ctx):
        from arcanis_utils.coreutils import seq
        nums = [int(x) for x in args]
        if len(nums) == 1:
            return CommandResult(success=True, stdout=seq(nums[0]))
        elif len(nums) >= 2:
            return CommandResult(success=True, stdout=seq(nums[0], nums[1], nums[2] if len(nums) > 2 else 1))
        return CommandResult(success=False, stderr="seq: need at least one number", exit_code=1)
    reg.register(Command("seq", cmd_seq, "Print number sequence", "text", RiskLevel.SAFE,
                         ["seq 10", "seq 1 2 20"]))

    def cmd_paste(args, flags, ctx):
        from arcanis_utils.coreutils import paste
        if len(args) < 2:
            return CommandResult(success=False, stderr="paste: need two files", exit_code=1)
        d = flags.get("d", "\t")
        return CommandResult(success=True, stdout=paste(args[0], args[1], d))
    reg.register(Command("paste", cmd_paste, "Merge files side by side", "text", RiskLevel.SAFE,
                         ["paste file1.txt file2.txt"]))

    return reg


# --------------------------------------------------------------------------
# Process helpers (kept isolated so psutil is optional)
# --------------------------------------------------------------------------


def psutil_processes() -> list[dict[str, Any]]:
    try:
        import psutil  # type: ignore[import-untyped,unused-ignore]

        return [{"pid": p.pid, "name": p.name()} for p in psutil.process_iter(["pid", "name"])]
    except ImportError:
        out = subprocess.run(  # noqa: S602
            ["tasklist", "/FO", "CSV"] if os.name == "nt" else ["ps", "-e", "-o", "pid=,comm="],
            capture_output=True,
            text=True,
            check=False,
        )
        procs: list[dict[str, Any]] = []
        if os.name == "nt":
            for line in out.stdout.splitlines()[1:]:
                parts = line.strip().strip('"').split('","')
                if len(parts) >= 2:
                    procs.append({"pid": len(procs) + 1, "name": parts[0]})
        else:
            for line in out.stdout.splitlines():
                parts = line.split(None, 1)
                if len(parts) == 2:
                    procs.append({"pid": int(parts[0]), "name": parts[1]})
        return procs


def kill_process(pid: int) -> None:
    try:
        import psutil  # type: ignore[import-untyped,unused-ignore]

        psutil.Process(pid).terminate()
        return
    except ImportError:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid)], check=False)  # noqa: S602
        else:
            os.kill(pid, 15)
