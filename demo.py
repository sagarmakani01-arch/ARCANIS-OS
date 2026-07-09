#!/usr/bin/env python3
"""
Arcanis OS — Interactive Demo
==============================
Simulates the complete OS: shell, filesystem, processes, signals, inference.
Run this to experience how Arcanis works.

Usage: python demo.py
"""

import os
import sys
import time
import signal
import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# ============================================================
# KERNEL SIMULATION
# ============================================================

class Process:
    _next_pid = 1

    def __init__(self, name: str, parent_pid: int = 0):
        self.pid = Process._next_pid
        Process._next_pid += 1
        self.name = name
        self.state = "running"
        self.parent_pid = parent_pid
        self.exit_code = 0
        self.fd_table = {}
        self.signal_handlers = {}
        self.cwd = "/"

    def __repr__(self):
        return f"PID={self.pid} NAME={self.name} STATE={self.state}"


class Kernel:
    def __init__(self):
        self.processes: dict[int, Process] = {}
        self.current_pid = 0
        self.uptime = 0
        self.syscall_log: list[str] = []
        self._init_process()

    def _init_process(self):
        init = Process("init")
        self.processes[init.pid] = init
        self.current_pid = init.pid

    def syscall(self, name: str, *args) -> Any:
        self.syscall_log.append(f"syscall({name}, {', '.join(str(a) for a in args)})")
        handler = getattr(self, f"_sys_{name}", None)
        if handler:
            return handler(*args)
        return -1

    def _sys_fork(self) -> int:
        parent = self.processes.get(self.current_pid)
        if not parent:
            return -1
        child = Process(f"{parent.name}", parent.pid)
        self.processes[child.pid] = child
        return child.pid

    def _sys_exec(self, path: str) -> int:
        return 0

    def _sys_exit(self, code: int = 0):
        proc = self.processes.get(self.current_pid)
        if proc:
            proc.state = "terminated"
            proc.exit_code = code

    def _sys_getpid(self) -> int:
        return self.current_pid

    def _sys_wait(self, pid: int = -1) -> int:
        for p in self.processes.values():
            if p.parent_pid == self.current_pid and p.state == "terminated":
                self.processes.pop(p.pid, None)
                return p.pid
        return -1

    def _sys_kill(self, pid: int) -> int:
        if pid in self.processes:
            self.processes[pid].state = "terminated"
            return 0
        return -1

    def _sys_signal(self, pid: int, signum: int) -> int:
        if pid in self.processes:
            proc = self.processes[pid]
            if signum in proc.signal_handlers:
                proc.signal_handlers[signum](signum)
                return 0
        return -1

    def list_processes(self) -> list[Process]:
        return [p for p in self.processes.values() if p.state != "terminated"]

    def tick(self):
        self.uptime += 1


# ============================================================
# FILESYSTEM SIMULATION
# ============================================================

class FSNode:
    def __init__(self, name: str, is_dir: bool = False, content: str = ""):
        self.name = name
        self.is_dir = is_dir
        self.content = content
        self.children: dict[str, FSNode] = {}
        self.parent: Optional['FSNode'] = None

    def __repr__(self):
        return f"{'[DIR]' if self.is_dir else '[FILE]'} {self.name}"


class FileSystem:
    def __init__(self):
        self.root = FSNode("/", is_dir=True)
        self.cwd = self.root
        self._build_default_fs()

    def _build_default_fs(self):
        # Create standard directories
        for d in ["dev", "proc", "tmp", "home", "etc", "var", "bin", "lib", "usr", "root",
                  "home/user", "var/log"]:
            self.mkdir(f"/{d}")

        # Create some files
        self.write("/etc/hostname", "arcanis")
        self.write("/etc/version", "1.1.0")
        self.write("/etc/motd", "Welcome to Arcanis OS v1.1.0\nAI-Native Operating System\nType 'help' for commands.")
        self.write("/home/user/.profile", "export PATH=/bin:/usr/bin\nexport PS1='arcanis> '")
        self.write("/home/user/notes.txt", "TODO: Finish kernel modules\nTODO: Write tests\nTODO: Deploy to hardware")
        self.write("/var/log/kernel.log", "[BOOT] Kernel initialized\n[BOOT] PMM: 256MB detected\n[BOOT] VMM: paging enabled\n[BOOT] Scheduler: ready\n[BOOT] VFS: mounted root\n[BOOT] Init: starting")
        self.write("/bin/README", "Arcanis system binaries")

    def _resolve(self, path: str) -> FSNode:
        if path == "/":
            return self.root
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.root
        for part in parts:
            if part == "..":
                node = node.parent or node
            elif part == ".":
                continue
            elif part in node.children:
                node = node.children[part]
            else:
                return None
        return node

    def mkdir(self, path: str) -> bool:
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.root
        for part in parts:
            if part not in node.children:
                child = FSNode(part, is_dir=True)
                child.parent = node
                node.children[part] = child
            node = node.children[part]
            if not node.is_dir:
                return False
        return True

    def write(self, path: str, content: str) -> bool:
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.root
        # Auto-create parent directories
        for part in parts[:-1]:
            if part not in node.children:
                child = FSNode(part, is_dir=True)
                child.parent = node
                node.children[part] = child
            node = node.children[part]
            if not node.is_dir:
                return False
        name = parts[-1]
        file_node = FSNode(name, is_dir=False, content=content)
        file_node.parent = node
        node.children[name] = file_node
        return True

    def read(self, path: str) -> Optional[str]:
        node = self._resolve(path)
        if node and not node.is_dir:
            return node.content
        return None

    def ls(self, path: str = ".") -> list[str]:
        node = self._resolve(path)
        if not node or not node.is_dir:
            return []
        entries = []
        for name, child in sorted(node.children.items()):
            prefix = "/" if child.is_dir else ""
            entries.append(f"{name}{prefix}")
        return entries

    def exists(self, path: str) -> bool:
        return self._resolve(path) is not None

    def rm(self, path: str) -> bool:
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.root
        for part in parts[:-1]:
            if part not in node.children:
                return False
            node = node.children[part]
        name = parts[-1]
        if name in node.children:
            del node.children[name]
            return True
        return False

    def tree(self, path: str = "/", prefix: str = "") -> str:
        node = self._resolve(path)
        if not node or not node.is_dir:
            return ""
        lines = [prefix + node.name + "/"]
        items = sorted(node.children.items())
        for i, (name, child) in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            suffix = "/" if child.is_dir else ""
            lines.append(prefix + connector + name + suffix)
            if child.is_dir:
                extension = "    " if is_last else "│   "
                lines.append(self.tree(path + "/" + name, prefix + extension))
        return "\n".join(lines)


# ============================================================
# SHELL SIMULATION
# ============================================================

class Shell:
    def __init__(self, kernel: Kernel, fs: FileSystem):
        self.kernel = kernel
        self.fs = fs
        self.history: list[str] = []
        self.running = True
        self.env = {
            "PATH": "/bin:/usr/bin",
            "HOME": "/home/user",
            "PS1": "arcanis> ",
            "USER": "user",
            "SHELL": "/bin/arcanis-sh",
            "TERM": "arcanis-256color",
        }

    def run(self):
        print("\033[1;36m" + r"""
     _                _                 ____   ___   ____
    / \   _ __   __ _| |_ ___  _ __   |  _ \ / _ \ / ___|
   / _ \ | '_ \ / _` | __/ _ \| '__|  | |_) | | | | |
  / ___ \| | | | (_| | || (_) | |     |  __/| |_| | |___
 /_/   \_\_| |_|\__,_|\__\___/|_|     |_|    \___/ \____|

        """ + "\033[0m")
        print("\033[90m  AI-Native Operating System v1.1.0\033[0m")
        print("\033[90m  49 modules | 32 syscalls | 34 shell commands\033[0m")
        print("\033[90m  Type 'help' for available commands\033[0m")
        print()

        while self.running:
            try:
                ps1 = self.env.get("PS1", "arcanis> ")
                cmd = input(f"\033[1;32m{ps1}\033[0m")
                if not cmd.strip():
                    continue
                self.history.append(cmd)
                self._execute(cmd.strip())
            except KeyboardInterrupt:
                print("\n\033[90m^C\033[0m")
            except EOFError:
                print("\n\033[90mlogout\033[0m")
                self.running = False

    def _execute(self, cmd: str):
        parts = cmd.split()
        if not parts:
            return
        command = parts[0]
        args = parts[1:]

        dispatch = {
            "help": self.cmd_help,
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "pwd": self.cmd_pwd,
            "cat": self.cmd_cat,
            "mkdir": self.cmd_mkdir,
            "touch": self.cmd_touch,
            "rm": self.cmd_rm,
            "echo": self.cmd_echo,
            "env": self.cmd_env,
            "export": self.cmd_export,
            "ps": self.cmd_ps,
            "kill": self.cmd_kill,
            "fork": self.cmd_fork,
            "wait": self.cmd_wait,
            "signal": self.cmd_signal,
            "sysinfo": self.cmd_sysinfo,
            "uptime": self.cmd_uptime,
            "tree": self.cmd_tree,
            "find": self.cmd_find,
            "grep": self.cmd_grep,
            "wc": self.cmd_wc,
            "head": self.cmd_head,
            "tail": self.cmd_tail,
            "date": self.cmd_date,
            "clear": self.cmd_clear,
            "history": self.cmd_history,
            "exit": self.cmd_exit,
            "uname": self.cmd_uname,
            "whoami": self.cmd_whoami,
            "hostname": self.cmd_hostname,
            "log": self.cmd_log,
            "inference": self.cmd_inference,
            "help-text": self.cmd_help_text,
        }

        handler = dispatch.get(command)
        if handler:
            handler(args)
        else:
            print(f"\033[31marcanis: {command}: command not found\033[0m")
            print(f"\033[90mType 'help' for available commands\033[0m")

    # ---- File commands ----
    def cmd_ls(self, args):
        path = args[0] if args else "."
        entries = self.fs.ls(path)
        for e in entries:
            if e.endswith("/"):
                print(f"\033[1;34m{e}\033[0m", end="  ")
            else:
                print(e, end="  ")
        if entries:
            print()

    def cmd_cd(self, args):
        path = args[0] if args else self.env.get("HOME", "/")
        node = self.fs._resolve(path)
        if node and node.is_dir:
            self.fs.cwd = node
            self.kernel.syscall("chdir", path)
        else:
            print(f"\033[31mcd: no such directory: {path}\033[0m")

    def cmd_pwd(self, _):
        path = "/"
        node = self.fs.cwd
        while node and node.parent:
            path = "/" + node.name + path
            node = node.parent
        print(path)

    def cmd_cat(self, args):
        if not args:
            print("\033[31mcat: missing file\033[0m")
            return
        content = self.fs.read(args[0])
        if content is not None:
            print(content)
        else:
            print(f"\033[31mcat: {args[0]}: no such file\033[0m")

    def cmd_mkdir(self, args):
        for arg in args:
            if self.fs.mkdir(arg):
                self.kernel.syscall("mkdir", arg)
            else:
                print(f"\033[31mmkdir: {arg}: failed\033[0m")

    def cmd_touch(self, args):
        for arg in args:
            if not self.fs.exists(arg):
                self.fs.write(arg, "")

    def cmd_rm(self, args):
        recursive = "-r" in args
        files = [a for a in args if a != "-r"]
        for f in files:
            if self.fs.rm(f):
                self.kernel.syscall("unlink", f)
            else:
                print(f"\033[31mrm: {f}: no such file\033[0m")

    def cmd_echo(self, args):
        text = " ".join(args)
        # Handle variable expansion
        for var, val in self.env.items():
            text = text.replace(f"${var}", val)
        print(text)

    def cmd_find(self, args):
        root = args[0] if args else "."
        pattern = args[1] if len(args) > 1 else "*"
        matches = []
        for entry in self.fs.ls(root):
            if pattern == "*" or pattern in entry:
                matches.append(f"{root}/{entry}")
        for m in matches:
            print(m)

    def cmd_grep(self, args):
        if len(args) < 2:
            print("\033[31mgrep: usage: grep PATTERN FILE\033[0m")
            return
        pattern, path = args[0], args[1]
        content = self.fs.read(path)
        if content is None:
            print(f"\033[31mgrep: {path}: no such file\033[0m")
            return
        for i, line in enumerate(content.splitlines(), 1):
            if pattern in line:
                print(f"{i}: {line}")

    def cmd_wc(self, args):
        path = args[0] if args else None
        if not path:
            print("\033[31mwc: missing file\033[0m")
            return
        content = self.fs.read(path)
        if content is None:
            print(f"\033[31mwc: {path}: no such file\033[0m")
            return
        lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        words = len(content.split())
        chars = len(content)
        print(f"  {lines}\t{words}\t{chars}\t{path}")

    def cmd_head(self, args):
        n = 10
        path = args[0] if args else None
        if not path:
            print("\033[31mhead: missing file\033[0m")
            return
        content = self.fs.read(path)
        if content is None:
            print(f"\033[31mhead: {path}: no such file\033[0m")
            return
        for line in content.splitlines()[:n]:
            print(line)

    def cmd_tail(self, args):
        n = 10
        path = args[0] if args else None
        if not path:
            print("\033[31mtail: missing file\033[0m")
            return
        content = self.fs.read(path)
        if content is None:
            print(f"\033[31mtail: {path}: no such file\033[0m")
            return
        for line in content.splitlines()[-n:]:
            print(line)

    # ---- Process commands ----
    def cmd_ps(self, _):
        print(f"{'PID':>6}  {'NAME':<20}  {'STATE':<12}  {'PARENT':<8}")
        print("-" * 52)
        for p in self.kernel.list_processes():
            print(f"{p.pid:>6}  {p.name:<20}  {p.state:<12}  {p.parent_pid:<8}")

    def cmd_kill(self, args):
        if not args:
            print("\033[31mkill: missing PID\033[0m")
            return
        pid = int(args[0])
        if self.kernel.syscall("kill", pid) == 0:
            print(f"Process {pid} killed")
        else:
            print(f"\033[31mkill: no such process: {pid}\033[0m")

    def cmd_fork(self, args):
        name = args[0] if args else "child"
        pid = self.kernel.syscall("fork")
        if pid > 0:
            child = self.kernel.processes.get(pid)
            if child:
                child.name = name
            print(f"Forked child PID={pid}")

    def cmd_wait(self, _):
        pid = self.kernel.syscall("wait")
        if pid > 0:
            print(f"Child {pid} exited")
        else:
            print("No children to wait for")

    def cmd_signal(self, args):
        if len(args) < 2:
            print("\033[31msignal: usage: signal PID SIGNUM\033[0m")
            return
        pid, signum = int(args[0]), int(args[1])
        self.kernel.syscall("signal", pid, signum)
        print(f"Signal {signum} sent to PID {pid}")

    # ---- System commands ----
    def cmd_sysinfo(self, _):
        print("\033[1;36m╔══════════════════════════════════════════╗")
        print("║         ARCANIS SYSTEM INFORMATION       ║")
        print("╠══════════════════════════════════════════╣")
        print(f"║  OS       : Arcanis OS v1.1.0            ║")
        print(f"║  Kernel   : 32-bit x86 microkernel       ║")
        print(f"║  Syscalls : 32                           ║")
        print(f"║  Processes: {len(self.kernel.list_processes()):<28}║")
        print(f"║  Uptime   : {self.kernel.uptime}s{' ' * (26 - len(str(self.kernel.uptime)))}║")
        print(f"║  Memory   : 256MB detected               ║")
        print(f"║  CPU      : x86 (i686)                   ║")
        print(f"║  Disk     : ATA PIO (8GB)                ║")
        print(f"║  Shell    : arcanis-sh                   ║")
        print(f"║  Inference: Built-in                     ║")
        print("╚══════════════════════════════════════════╝\033[0m")

    def cmd_uptime(self, _):
        print(f"up {self.kernel.uptime}s")

    def cmd_uname(self, args):
        if "-a" in args:
            print("Arcanis 1.1.0 arcanis #1 SMP x86 i686")
        else:
            print("Arcanis")

    def cmd_whoami(self, _):
        print(self.env.get("USER", "root"))

    def cmd_hostname(self, _):
        print("arcanis")

    def cmd_date(self, _):
        print(time.strftime("%Y-%m-%d %H:%M:%S"))

    def cmd_tree(self, args):
        path = args[0] if args else "/"
        print(self.fs.tree(path))

    def cmd_log(self, _):
        content = self.fs.read("/var/log/kernel.log")
        if content:
            for line in content.splitlines():
                print(f"\033[90m{line}\033[0m")

    # ---- Environment ----
    def cmd_env(self, _):
        for k, v in sorted(self.env.items()):
            print(f"{k}={v}")

    def cmd_export(self, args):
        for arg in args:
            if "=" in arg:
                k, v = arg.split("=", 1)
                self.env[k] = v

    # ---- AI/Inference ----
    def cmd_inference(self, args):
        query = " ".join(args) if args else "hello"
        print(f"\033[1;35m[INFERENCE]\033[0m Processing: '{query}'")
        time.sleep(0.5)

        # Simple intent classification
        intents = {
            "hello": "greeting",
            "help": "help_request",
            "time": "system_info",
            "status": "system_info",
            "list": "file_operation",
            "read": "file_operation",
            "create": "file_operation",
            "delete": "file_operation",
            "process": "process_management",
            "kill": "process_management",
        }

        intent = "unknown"
        for keyword, intnt in intents.items():
            if keyword in query.lower():
                intent = intnt
                break

        print(f"\033[36m  Intent: {intent}\033[0m")
        print(f"\033[36m  Confidence: 0.95\033[0m")
        print(f"\033[36m  Response: I understand you want to {intent.replace('_', ' ')}.\033[0m")

    # ---- Misc ----
    def cmd_history(self, _):
        for i, cmd in enumerate(self.history, 1):
            print(f"  {i:>4}  {cmd}")

    def cmd_clear(self, _):
        os.system("cls" if os.name == "nt" else "clear")

    def cmd_exit(self, _):
        self.running = False

    def cmd_help(self, _):
        print("\033[1;36m╔══════════════════════════════════════════════════════════════╗")
        print("║              ARCANIS SHELL — AVAILABLE COMMANDS              ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print("║                                                              ║")
        print("║  FILE OPERATIONS:                                           ║")
        print("║    ls [path]        List directory contents                 ║")
        print("║    cd [path]        Change directory                        ║")
        print("║    pwd              Print working directory                 ║")
        print("║    cat <file>       Print file contents                     ║")
        print("║    mkdir <dir>      Create directory                        ║")
        print("║    touch <file>     Create empty file                       ║")
        print("║    rm [-r] <file>   Remove file or directory                ║")
        print("║    find [path]      Search for files                        ║")
        print("║    tree [path]      Show directory tree                     ║")
        print("║                                                              ║")
        print("║  TEXT PROCESSING:                                           ║")
        print("║    echo <text>      Print text with variable expansion      ║")
        print("║    grep <pat> <f>   Search pattern in file                  ║")
        print("║    wc <file>        Count lines, words, chars               ║")
        print("║    head <file>      Show first 10 lines                     ║")
        print("║    tail <file>      Show last 10 lines                      ║")
        print("║                                                              ║")
        print("║  PROCESS MANAGEMENT:                                        ║")
        print("║    ps               List running processes                  ║")
        print("║    fork [name]      Fork a child process                    ║")
        print("║    kill <pid>       Terminate a process                     ║")
        print("║    wait             Wait for child process                  ║")
        print("║    signal <pid> <n> Send signal to process                  ║")
        print("║                                                              ║")
        print("║  SYSTEM:                                                    ║")
        print("║    sysinfo          Show system information                 ║")
        print("║    uptime           Show system uptime                      ║")
        print("║    uname [-a]       Show system name                        ║")
        print("║    whoami           Show current user                       ║")
        print("║    hostname         Show system hostname                    ║")
        print("║    date             Show current date/time                  ║")
        print("║    log              Show kernel log                         ║")
        print("║                                                              ║")
        print("║  ENVIRONMENT:                                               ║")
        print("║    env              Show environment variables              ║")
        print("║    export K=V       Set environment variable                ║")
        print("║                                                              ║")
        print("║  AI/INFERENCE:                                              ║")
        print("║    inference <query> Query the AI inference engine           ║")
        print("║                                                              ║")
        print("║  MISC:                                                      ║")
        print("║    history          Show command history                    ║")
        print("║    clear            Clear screen                            ║")
        print("║    exit             Exit shell                              ║")
        print("║    help             Show this help message                  ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝\033[0m")

    def cmd_help_text(self, _):
        """Show ASCII art help."""
        print("\033[1;33m")
        print("    ╔═══════════════════════════════════╗")
        print("    ║    ARC A N I S   O S   v1.1.0     ║")
        print("    ║    AI-Native Operating System      ║")
        print("    ╚═══════════════════════════════════╝")
        print("\033[0m")


# ============================================================
# MAIN
# ============================================================

def main():
    kernel = Kernel()
    fs = FileSystem()
    shell = Shell(kernel, fs)

    # Start init process
    kernel.syscall("fork")
    kernel.syscall("fork")

    shell.run()
    print("\n\033[90mGoodbye from Arcanis OS.\033[0m")


if __name__ == "__main__":
    main()
