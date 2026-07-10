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
        print("\033[90m  AI-Native Operating System v1.7.0\033[0m")
        print("\033[90m  49 modules | 46 syscalls | 80 shell commands\033[0m")
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
            "svc": self.cmd_svc,
            "user": self.cmd_user,
            "login": self.cmd_login,
            "pkg": self.cmd_pkg,
            "net": self.cmd_net,
            "ping": self.cmd_ping,
            "vi": self.cmd_vi,
            "vim": self.cmd_vi,
            "nano": self.cmd_nano,
            "ed": self.cmd_ed,
            "asm": self.cmd_asm,
            "ld": self.cmd_ld,
            "mount": self.cmd_mount,
            "df": self.cmd_df,
            "mmap": self.cmd_mmap,
            "free": self.cmd_free,
            "lscpu": self.cmd_lscpu,
            "top": self.cmd_top,
            "dmesg": self.cmd_dmesg,
            "gui": self.cmd_gui,
            "filemanager": self.cmd_filemanager,
            "term": self.cmd_term,
            "ipcs": self.cmd_ipcs,
            "nice": self.cmd_nice,
            "renice": self.cmd_nice,
            "jobs": self.cmd_jobs,
            "bg": self.cmd_bg,
            "fg": self.cmd_fg,
            "nslookup": self.cmd_nslookup,
            "dig": self.cmd_dig,
            "curl": self.cmd_curl,
            "wget": self.cmd_wget,
            "dhcp": self.cmd_dhcp,
            "gdb": self.cmd_gdb,
            "lspci": self.cmd_lspci,
            "lsusb": self.cmd_lsusb,
            "strace": self.cmd_strace,
            "ltrace": self.cmd_ltrace,
            "calc": self.cmd_calc,
            "script": self.cmd_script,
            "tar": self.cmd_tar,
            "htop": self.cmd_htop,
            "ifconfig": self.cmd_ifconfig,
            "netstat": self.cmd_netstat,
            "route": self.cmd_route,
            "arp": self.cmd_arp,
            "chmod": self.cmd_chmod,
            "encrypt": self.cmd_encrypt,
            "decrypt": self.cmd_decrypt,
            "passwd": self.cmd_passwd,
            "make": self.cmd_make,
            "awk": self.cmd_awk,
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
        print(f"║  Network  : TCP/IP stack loaded           ║")
        print(f"║  Users    : 2 registered                 ║")
        print(f"║  Services : 5 managed                    ║")
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

    # ---- Services ----
    def cmd_svc(self, args):
        if not args:
            print("\033[31msvc: usage: svc [start|stop|restart|list] [service]\033[0m")
            return
        action = args[0]
        if action == "list":
            services = [
                ("kernel-scheduler", "Process scheduler", "running"),
                ("vfs", "Virtual filesystem", "running"),
                ("shell", "Interactive shell", "running"),
                ("network", "TCP/IP stack", "running"),
                ("inference", "AI inference engine", "stopped"),
            ]
            print(f"{'SERVICE':<20}  {'STATE':<10}  {'DESCRIPTION'}")
            print("-" * 60)
            for name, desc, state in services:
                color = "\033[32m" if state == "running" else "\033[31m"
                print(f"{name:<20}  {color}{state:<10}\033[0m  {desc}")
        elif action == "start" and len(args) > 1:
            print(f"\033[32mService '{args[1]}' started\033[0m")
        elif action == "stop" and len(args) > 1:
            print(f"\033[31mService '{args[1]}' stopped\033[0m")
        elif action == "restart" and len(args) > 1:
            print(f"\033[33mService '{args[1]}' restarted\033[0m")
        else:
            print("\033[31msvc: invalid usage\033[0m")

    # ---- Users ----
    def cmd_user(self, args):
        if not args:
            print("\033[31muser: usage: user [list|add|delete|passwd] [name]\033[0m")
            return
        action = args[0]
        users = [
            ("root", 0, "admin,system"),
            ("user", 1000, "admin"),
            ("guest", 1001, ""),
        ]
        if action == "list":
            print(f"{'USER':<12}  {'UID':<8}  {'FLAGS'}")
            print("-" * 40)
            for name, uid, flags in users:
                print(f"{name:<12}  {uid:<8}  {flags}")
        elif action == "add" and len(args) > 1:
            print(f"\033[32mUser '{args[1]}' created (uid=1002)\033[0m")
        elif action == "delete" and len(args) > 1:
            print(f"\033[31mUser '{args[1]}' deleted\033[0m")
        elif action == "passwd" and len(args) > 1:
            print(f"\033[32mPassword changed for '{args[1]}'\033[0m")
        else:
            print("\033[31muser: invalid usage\033[0m")

    def cmd_login(self, args):
        if len(args) < 2:
            print("\033[31mlogin: usage: login <username> <password>\033[0m")
            return
        username, password = args[0], args[1]
        # Simulated auth
        if username in ["root", "user"] and password in ["toor", "user"]:
            print(f"\033[32mWelcome, {username}!\033[0m")
            self.env["USER"] = username
        else:
            print(f"\033[31mLogin failed for {username}\033[0m")

    # ---- Packages ----
    def cmd_pkg(self, args):
        if not args:
            print("\033[31mpkg: usage: pkg [install|remove|search|list|update] [package]\033[0m")
            return
        action = args[0]
        packages = [
            ("arcanis-core", "1.1.0", "Core system", "installed"),
            ("arcanis-shell", "1.0.0", "Interactive shell", "installed"),
            ("arcanis-kernel", "1.1.0", "Kernel modules", "installed"),
            ("arcanis-net", "0.1.0", "Network utilities", "available"),
            ("arcanis-dev", "0.1.0", "Development tools", "available"),
            ("arcanis-gui", "0.0.1", "Graphical interface", "available"),
            ("vim-arcanis", "0.1.0", "Text editor", "available"),
            ("gcc-arcanis", "0.1.0", "C compiler", "available"),
        ]
        if action == "list":
            print(f"{'PACKAGE':<20}  {'VERSION':<10}  {'STATUS':<12}  {'DESCRIPTION'}")
            print("-" * 70)
            for name, ver, desc, status in packages:
                color = "\033[32m" if status == "installed" else "\033[90m"
                print(f"{name:<20}  {ver:<10}  {color}{status:<12}\033[0m  {desc}")
        elif action == "search" and len(args) > 1:
            query = args[1]
            found = [(n,v,d,s) for n,v,d,s in packages if query in n or query in d]
            for name, ver, desc, _ in found:
                print(f"  {name} ({ver}) - {desc}")
            if not found:
                print(f"  No packages matching '{query}'")
        elif action == "install" and len(args) > 1:
            print(f"\033[32mPackage '{args[1]}' installed successfully\033[0m")
        elif action == "remove" and len(args) > 1:
            print(f"\033[31mPackage '{args[1]}' removed\033[0m")
        elif action == "update":
            print("\033[33mUpdating package database...\033[0m")
            print("\033[32mDatabase updated\033[0m")
        else:
            print("\033[31mpkg: invalid usage\033[0m")

    # ---- Network ----
    def cmd_net(self, args):
        if not args:
            print("\033[31mnet: usage: net [ifconfig|route|arp|stat]\033[0m")
            return
        action = args[0]
        if action == "ifconfig":
            print("\033[1;36mNetwork Interfaces:\033[0m")
            print(f"  eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>")
            print(f"        inet 192.168.1.100  netmask 255.255.255.0")
            print(f"        ether 02:42:ac:11:00:02")
            print(f"        RX packets 1234  TX packets 5678")
        elif action == "route":
            print("\033[1;36mRouting Table:\033[0m")
            print(f"  {'DESTINATION':<20}  {'GATEWAY':<16}  {'METRIC'}")
            print(f"  {'0.0.0.0/0':<20}  {'192.168.1.1':<16}  {'100'}")
            print(f"  {'192.168.1.0/24':<20}  {'0.0.0.0':<16}  {'0'}")
        elif action == "arp":
            print("\033[1;36mARP Table:\033[0m")
            print(f"  {'IP ADDRESS':<16}  {'MAC ADDRESS':<20}  {'AGE'}")
            print(f"  {'192.168.1.1':<16}  {'aa:bb:cc:dd:ee:ff':<20}  {'0s'}")
        elif action == "stat":
            print("\033[1;36mNetwork Statistics:\033[0m")
            print(f"  RX packets: 1234  TX packets: 5678")
            print(f"  RX bytes: 1.2MB   TX bytes: 567KB")
            print(f"  Errors: 0  Dropped: 0")
        else:
            print("\033[31mnet: invalid usage\033[0m")

    def cmd_ping(self, args):
        if not args:
            print("\033[31mping: usage: ping <host>\033[0m")
            return
        host = args[0]
        print(f"PING {host} ({host}) 56(84) bytes of data.")
        for i in range(4):
            time_ms = 0.5 + (i * 0.1)
            print(f"64 bytes from {host}: icmp_seq={i+1} ttl=64 time={time_ms:.1f} ms")
        print(f"\n--- {host} ping statistics ---")
        print(f"4 packets transmitted, 4 received, 0% packet loss")

    # ---- Text Editors ----
    def cmd_vi(self, args):
        """Vi-like text editor simulation."""
        if not args:
            print("\033[33mvi: usage: vi <filename>\033[0m")
            return
        filename = args[0]
        content = self.fs.read(filename) or ""
        print(f"\033[1;33m[VI EDITOR]\033[0m Editing: {filename}")
        print("\033[90m  Commands: i=insert, :=command, w=write, q=quit, h=help\033[0m")
        print("\033[90m  This is a simulation — in the real OS, vi runs as a process.\033[0m")
        if content:
            for i, line in enumerate(content.splitlines()[:10], 1):
                print(f"  {i:>3}  {line}")
        else:
            print("  (empty file)")

    def cmd_nano(self, args):
        """Nano-like editor simulation."""
        if not args:
            print("\033[33mnano: usage: nano <filename>\033[0m")
            return
        filename = args[0]
        content = self.fs.read(filename) or ""
        print(f"\033[1;33m[NANO EDITOR]\033[0m Editing: {filename}")
        print("\033[90m  This is a simulation — in the real OS, nano runs as a process.\033[0m")
        if content:
            print(content[:500])

    def cmd_ed(self, args):
        """Line editor simulation."""
        if not args:
            print("\033[33med: usage: ed <filename>\033[0m")
            return
        filename = args[0]
        content = self.fs.read(filename) or ""
        print(f"\033[1;33m[ED LINE EDITOR]\033[0m Editing: {filename}")
        print("\033[90m  This is a simulation — in the real OS, ed runs as a process.\033[0m")

    # ---- Development Tools ----
    def cmd_asm(self, args):
        """Assembler simulation."""
        if not args:
            print("\033[33masm: usage: asm <input.s> -o <output.o>\033[0m")
            return
        filename = args[0]
        content = self.fs.read(filename)
        if content is None:
            print(f"\033[31masm: {filename}: no such file\033[0m")
            return
        lines = content.count("\n") + 1
        print(f"\033[1;33m[ASSEMBLER]\033[0m Assembling: {filename}")
        print(f"  Lines: {lines}")
        print(f"  Output: {filename}.o (simulated)")
        print(f"  Status: \033[32msuccess\033[0m")

    def cmd_ld(self, args):
        """Linker simulation."""
        if not args:
            print("\033[33mld: usage: ld <input.o> -o <output.bin>\033[0m")
            return
        filename = args[0]
        print(f"\033[1;33m[LINKER]\033[0m Linking: {filename}")
        print(f"  Symbols resolved: 12")
        print(f"  Sections: .text .data .bss")
        print(f"  Entry point: 0x08048000")
        print(f"  Output: {filename}.bin (simulated)")
        print(f"  Status: \033[32msuccess\033[0m")

    # ---- Filesystem ----
    def cmd_mount(self, args):
        """Mount filesystem simulation."""
        print("\033[1;36mFilesystem mounts:\033[0m")
        print(f"  /dev       tmpfs     256MB")
        print(f"  /proc      procfs    0MB")
        print(f"  /tmp       tmpfs     128MB")
        print(f"  /home      ext2      2GB")
        print(f"  /          ext2      4GB")

    def cmd_df(self, args):
        """Disk free simulation."""
        print(f"\033[1;36m{'FILESYSTEM':<20}  {'SIZE':<8}  {'USED':<8}  {'AVAIL':<8}  {'MOUNT'}\033[0m")
        print(f"  {'/dev/sda1':<20}  {'8GB':<8}  {'2.1GB':<8}  {'5.9GB':<8}  /")
        print(f"  {'tmpfs':<20}  {'256MB':<8}  {'12MB':<8}  {'244MB':<8}  /dev")
        print(f"  {'tmpfs':<20}  {'128MB':<8}  {'4MB':<8}  {'124MB':<8}  /tmp")

    def cmd_mmap(self, args):
        """Memory map simulation."""
        if not args:
            print(f"\033[1;36m{'ADDRESS':<16}  {'SIZE':<10}  {'PROT':<10}  {'FILE'}\033[0m")
            print(f"  {'0x08048000':<16}  {'64KB':<10}  {'r-x':<10}  /bin/arcanis-sh")
            print(f"  {'0x08058000':<16}  {'32KB':<10}  {'rw-':<10}  [heap]")
            print(f"  {'0xb7e00000':<16}  {'1.2MB':<10}  {'r--':<10}  /lib/libc.so")
            print(f"  {'0xbff00000':<16}  {'8KB':<10}  {'rw-':<10}  [stack]")
        else:
            print(f"\033[33mmmap: mapping {args[0]} at 0xb7f00000 (simulated)\033[0m")

    # ---- System Info ----
    def cmd_free(self, _):
        """Memory usage simulation."""
        print(f"\033[1;36m{'':<12}  {'TOTAL':<10}  {'USED':<10}  {'FREE':<10}  {'SHARED':<10}  {'BUFF/CACHE'}\033[0m")
        print(f"  {'Mem:':<12}  {'256MB':<10}  {'84MB':<10}  {'142MB':<10}  {'12MB':<10}  {'30MB'}")
        print(f"  {'Swap:':<12}  {'0MB':<10}  {'0MB':<10}  {'0MB':<10}  {'':<10}  {''}")

    def cmd_lscpu(self, _):
        """CPU info simulation."""
        print(f"\033[1;36mCPU Information:\033[0m")
        print(f"  Architecture:        x86 (i686)")
        print(f"  CPU(s):              1")
        print(f"  Model:               Arcanis Virtual CPU")
        print(f"  Clock speed:         100 MHz (simulated)")
        print(f"  Cache:               64KB L1")
        print(f"  Flags:               sse sse2 mmx fpu")

    def cmd_top(self, _):
        """Process monitor simulation."""
        print(f"\033[1;36m{'PID':<8}  {'NAME':<20}  {'CPU%':<8}  {'MEM':<8}  {'STATE'}\033[0m")
        procs = self.kernel.list_processes()
        for p in procs[:10]:
            print(f"  {p.pid:<8}  {p.name:<20}  {'0.1':<8}  {'4MB':<8}  {p.state}")
        print(f"\n  Tasks: {len(procs)} total, 1 running, {len(procs)-1} sleeping")

    def cmd_dmesg(self, _):
        """Kernel message log."""
        content = self.fs.read("/var/log/kernel.log")
        if content:
            for line in content.splitlines():
                print(f"\033[90m{line}\033[0m")
        else:
            print("\033[90m[BOOT] Kernel initialized\033[0m")

    # ---- GUI / Desktop ----
    def cmd_gui(self, _):
        """GUI window manager simulation."""
        print("\033[1;36m╔══════════════════════════════════════════════════╗")
        print("║           ARCANIS DESKTOP ENVIRONMENT            ║")
        print("╠══════════════════════════════════════════════════╣")
        print("║  Resolution:  1024x768                          ║")
        print("║  Color depth: 32-bit                            ║")
        print("║  Renderer:    Software (VESA)                   ║")
        print("║  Layout:      Tiling window manager             ║")
        print("║  Widgets:     Button, Label, TextBox, CheckBox  ║")
        print("║               ComboBox, Progress, Slider, Menu  ║")
        print("║  Taskbar:     Auto-hiding bottom bar            ║")
        print("║                                                  ║")
        print("║  Running windows:                               ║")
        print("║    - Terminal (PID 3)                           ║")
        print("║    - File Manager (PID 4)                       ║")
        print("║    - System Monitor (PID 5)                     ║")
        print("╚══════════════════════════════════════════════════╝\033[0m")

    def cmd_filemanager(self, _):
        """File manager simulation."""
        print("\033[1;36m╔══════════════════════════════════════════════════╗")
        print("║              FILE MANAGER                        ║")
        print("╠══════════════════════════════════════════════════╣")
        print("║  Current: /home/user                             ║")
        print("║                                                  ║")
        print("║  /     (4GB)                                    ║")
        print("║  dev/  (256MB)                                  ║")
        print("║  etc/                                            ║")
        print("║  home/                                           ║")
        print("║  tmp/                                            ║")
        print("║  user/                                           ║")
        print("║    notes.txt     128 bytes                       ║")
        print("║    .profile      64 bytes                        ║")
        print("║    project/                                       ║")
        print("║  var/                                            ║")
        print("║  bin/                                            ║")
        print("╚══════════════════════════════════════════════════╝\033[0m")

    def cmd_term(self, _):
        """Terminal emulator simulation."""
        print("\033[1;36m╔══════════════════════════════════════════════════╗")
        print("║           TERMINAL EMULATOR                      ║")
        print("╠══════════════════════════════════════════════════╣")
        print("║  Size:      80x24                               ║")
        print("║  Encoding:  UTF-8                               ║")
        print("║  ANSI:      Full support (256 colors)           ║")
        print("║  Font:      Fixed 8x16                          ║")
        print("║  Scroll:    1024 lines                          ║")
        print("║  Tabs:      Supported                           ║")
        print("║                                                  ║")
        print("║  Colors: Catppuccin Mocha palette               ║")
        print("║  FG: #CDD6F4  BG: #1E1E2E  BORDER: #45475A     ║")
        print("╚══════════════════════════════════════════════════╝\033[0m")

    # ---- IPC ----
    def cmd_ipcs(self, _):
        """IPC status."""
        print(f"\033[1;36m{'TYPE':<12}  {'KEY':<10}  {'ID':<8}  {'STATUS'}\033[0m")
        print(f"  {'msgqueue':<12}  {'0x1234':<10}  {'1':<8}  active")
        print(f"  {'msgqueue':<12}  {'0x5678':<10}  {'2':<8}  active")
        print(f"  {'shm':<12}  {'0xABCD':<10}  {'1':<8}  4096 bytes")
        print(f"  {'semaphore':<12}  {'0x0001':<10}  {'1':<8}  value=1")
        print(f"  {'semaphore':<12}  {'0x0002':<10}  {'2':<8}  value=0")
        print(f"\n  Messages queued: 3")
        print(f"  Shared memory attached: 2 processes")
        print(f"  Semaphores: 2 (1 locked)")

    # ---- Process control ----
    def cmd_nice(self, args):
        """Set process priority."""
        if len(args) < 2:
            print("\033[33mnice: usage: nice <priority> <pid>\033[0m")
            return
        try:
            pri = int(args[0])
            pid = int(args[1])
            print(f"\033[32mProcess {pid} priority set to {pri}\033[0m")
        except ValueError:
            print("\033[31mnice: invalid arguments\033[0m")

    def cmd_jobs(self, _):
        """List background jobs."""
        print(f"{'JOB':<8}  {'PID':<8}  {'STATE':<12}  {'COMMAND'}")
        print("-" * 50)
        print(f"  {'1':<8}  {'12':<8}  {'running':<12}  sleep 100")
        print(f"  {'2':<8}  {'15':<8}  {'suspended':<12}  vim /tmp/test")

    def cmd_bg(self, args):
        """Resume background."""
        if not args:
            print("\033[33mbg: usage: bg <job>\033[0m")
            return
        print(f"\033[32mJob {args[0]} resumed in background\033[0m")

    def cmd_fg(self, args):
        """Bring to foreground."""
        if not args:
            print("\033[33mfg: usage: fg <job>\033[0m")
            return
        print(f"\033[32mJob {args[0]} brought to foreground\033[0m")

    # ---- Network Applications ----
    def cmd_nslookup(self, args):
        """DNS lookup."""
        if not args:
            print("\033[33mnslookup: usage: nslookup <hostname>\033[0m")
            return
        host = args[0]
        print(f"Server:   8.8.8.8")
        print(f"Address:  8.8.8.8#53")
        print()
        print(f"Non-authoritative answer:")
        print(f"Name:     {host}")
        print(f"Address:  142.250.80.4")

    def cmd_dig(self, args):
        """DNS query (verbose)."""
        if not args:
            print("\033[33mdig: usage: dig <hostname> [type]\033[0m")
            return
        host = args[0]
        rtype = args[1] if len(args) > 1 else "A"
        print(f";; QUESTION SECTION:")
        print(f";; {host:<30} IN  {rtype}")
        print()
        print(f";; ANSWER SECTION:")
        print(f"{host}        300    IN  A       142.250.80.4")
        print()
        print(f";; Query time: 23 msec")
        print(f";; SERVER: 8.8.8.8#53")
        print(f";; WHEN: Fri Jul 10 2026")

    def cmd_curl(self, args):
        """HTTP client."""
        if not args:
            print("\033[33mcurl: usage: curl <url>\033[0m")
            return
        url = args[0]
        print(f"  % Total    % Received  Xferd  Speed")
        print(f"  100  1256  100  1256    0     0  12560      0 --:--:-- --:--:-- --:--:-- 12560")
        print(f"<!DOCTYPE html><html><head><title>Arcanis OS</title></head>")
        print(f"<body><h1>Welcome to Arcanis OS</h1></body></html>")

    def cmd_wget(self, args):
        """Download file."""
        if not args:
            print("\033[33mwget: usage: wget <url>\033[0m")
            return
        url = args[0]
        print(f"Connecting to {url}... connected.")
        print(f"HTTP request sent, awaiting response... 200 OK")
        print(f"Length: 4096 (4.0K) [text/html]")
        print(f"Saving to: 'index.html'")
        print(f"index.html 100%[===================>]   4.00K  --.-KB/s    in 0s")
        print(f"2026-07-10 12:00:00 (40.0 MB/s) - 'index.html' saved [4096/4096]")

    def cmd_dhcp(self, args):
        """DHCP client status."""
        print(f"\033[1;36mDHCP Client Status:\033[0m")
        print(f"  State:      BOUND")
        print(f"  Interface:  eth0")
        print(f"  MAC:        02:42:ac:11:00:02")
        print(f"  IP:         192.168.1.100")
        print(f"  Subnet:     255.255.255.0")
        print(f"  Gateway:    192.168.1.1")
        print(f"  DNS:        8.8.8.8, 8.8.4.4")
        print(f"  Lease:      86400s (expires in 43200s)")
        print(f"  Server:     192.168.1.1")

    # ---- Debugging ----
    def cmd_gdb(self, args):
        """GDB-like debugger."""
        print("\033[1;36m╔══════════════════════════════════════════════════╗")
        print("║          ARCANIS DEBUGGER (GDB stub)             ║")
        print("╠══════════════════════════════════════════════════╣")
        print("║  Commands:                                      ║")
        print("║    r        Run program                         ║")
        print("║    c        Continue execution                   ║")
        print("║    s        Single step                          ║")
        print("║    n        Step over                            ║")
        print("║    b <addr> Set breakpoint                      ║")
        print("║    d <addr> Delete breakpoint                   ║")
        print("║    i        Info registers                      ║")
        print("║    x <addr> Examine memory                      ║")
        print("║    bt       Backtrace                           ║")
        print("║    q        Quit debugger                       ║")
        print("╚══════════════════════════════════════════════════╝\033[0m")

    def cmd_lspci(self, _):
        """List PCI devices."""
        print(f"{'BDF':<12}  {'CLASS':<28}  {'DEVICE'}")
        print("-" * 70)
        devices = [
            ("00:00.0", "Host bridge", "440FX - 82441FX PMC [Intel]"),
            ("00:01.0", "ISA bridge", "82371SB PIIX3 ISA [Intel]"),
            ("00:01.1", "IDE interface", "82371AB PIIX4 IDE [Intel]"),
            ("00:01.3", "Bridge", "82371AB PIIX4 ACPI [Intel]"),
            ("00:02.0", "VGA compatible", "Device 1111 [Red Hat]"),
            ("00:03.0", "Ethernet controller", "RTL8111/8168 [Realtek]"),
            ("00:04.0", "Network controller", "VirtIO Network [Red Hat]"),
        ]
        for bdf, cls, dev in devices:
            print(f"  {bdf:<12}  {cls:<28}  {dev}")
        print(f"\n  {len(devices)} devices found")

    def cmd_lsusb(self, _):
        """List USB devices."""
        print(f"{'BUS':<6}  {'ID':<12}  {'DESCRIPTION'}")
        print("-" * 50)
        print(f"  001    1d6b:0002   Linux Foundation 2.0 root hub")
        print(f"  001    8087:0024   Intel Integrated Hub")
        print(f"  002    0627:0001   Adomax Virtual Device")
        print(f"\n  3 devices found")

    def cmd_strace(self, args):
        """System call tracer."""
        if not args:
            print("\033[33mstrace: usage: strace <command>\033[0m")
            return
        cmd = " ".join(args)
        print(f"execve(\"{cmd}\", [{cmd}], 0x7ffd1234) = 3")
        print(f"brk(NULL)                               = 0x55a1234000")
        print(f"open(\"/etc/ld.so.cache\", O_RDONLY|O_CLOEXEC) = 4")
        print(f"mmap(NULL, 8192, PROT_READ, MAP_PRIVATE, 4, 0) = 0x7f12340000")
        print(f"read(0, \"hello\\n\", 1024)              = 6")
        print(f"write(1, \"hello\\n\", 6)               = 6")
        print(f"exit_group(0)                           = ?")
        print(f"+++ exited with 0 +++")

    def cmd_ltrace(self, args):
        """Library call tracer."""
        if not args:
            print("\033[33mltrace: usage: ltrace <command>\033[0m")
            return
        cmd = " ".join(args)
        print(f"__libc_start_main(0x55a1234, 1, 0x7ffd, ...)")
        print(f"printf(\"Hello, %s!\\n\", \"world\") = 13")
        print(f"malloc(1024)                           = 0x55a6789")
        print(f"free(0x55a6789)                        = <void>")
        print(f"+++ exited (status 0) +++")

    # ---- Shell Scripting / Apps ----
    def cmd_calc(self, args):
        """Scientific calculator."""
        if not args:
            print("\033[33mcalc: usage: calc <expression>\033[0m")
            print("  Supports: +, -, *, /, %, ^, sin, cos, tan, sqrt, log, ln, abs")
            print("  Example: calc 2+3*4  |  calc sin(3.14/2)  |  calc sqrt(144)")
            return
        expr = " ".join(args)
        try:
            # Simple evaluation for demo
            result = eval(expr, {"__builtins__": {}}, {"pi": 3.14159, "e": 2.71828})
            print(f"\033[1;32m= {result}\033[0m")
        except:
            print(f"\033[31mcalc: error evaluating '{expr}'\033[0m")

    def cmd_script(self, args):
        """Shell script execution."""
        if not args:
            print("\033[33mscript: usage: script <file.sh>\033[0m")
            print("  Supports: variables, if/else, for/while loops, functions")
            print("  Example:")
            print("    #!/bin/arcanis-sh")
            print("    name='world'")
            print("    echo \"Hello, $name!\"")
            print("    for i in 1 2 3; do echo $i; done")
            return
        filename = args[0]
        content = self.fs.read(filename)
        if content:
            print(f"\033[1;33m[SCRIPT]\033[0m Executing: {filename}")
            print(content[:500])
        else:
            print(f"\033[31mscript: {filename}: file not found\033[0m")

    def cmd_tar(self, args):
        """TAR archiver."""
        if not args:
            print("\033[33mtar: usage: tar [c|x|t] <archive.tar> [files...]\033[0m")
            print("  c  Create archive")
            print("  x  Extract archive")
            print("  t  List contents")
            return
        action = args[0]
        if action == 'c' and len(args) > 1:
            archive = args[1]
            files = args[2:]
            print(f"\033[1;33m[TAR]\033[0m Creating archive: {archive}")
            print(f"  Files: {', '.join(files) if files else '(none)'}")
            print(f"  Size: {len(files) * 512} bytes")
            print(f"  Status: \033[32msuccess\033[0m")
        elif action == 'x' and len(args) > 1:
            print(f"\033[1;33m[TAR]\033[0m Extracting: {args[1]}")
            print(f"  Files extracted: 3")
            print(f"  Status: \033[32msuccess\033[0m")
        elif action == 't' and len(args) > 1:
            print(f"\033[1;33m[TAR]\033[0m Contents of: {args[1]}")
            print(f"  -rw-r--r-- root/root  1024 2026-07-10 file.txt")
            print(f"  drwxr-xr-x root/root     0 2026-07-10 dir/")
            print(f"  -rw-r--r-- root/root  2048 2026-07-10 dir/data.bin")
        else:
            print("\033[33mtar: invalid usage\033[0m")

    def cmd_htop(self, _):
        """Interactive process monitor."""
        print("\033[1;36m╔══════════════════════════════════════════════════════════════╗")
        print("║  PID USER    PRI  NI  VIRT  RES  SHR S CPU% MEM%  TIME+ COMMAND ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print("║    1 root     20   0  2400 1200  800 S  0.0  0.5  0:01.23 init   ║")
        print("║    2 root     20   0  4096 2048 1024 S  0.0  0.8  0:00.45 shell  ║")
        print("║    3 user     20   0  8192 4096 2048 S  0.1  1.6  0:02.10 bash   ║")
        print("║    4 user     20   0 16384 8192 4096 S  0.2  3.2  0:05.67 vim    ║")
        print("║    5 user     20   0 32768 16384 8192 S  0.5  6.4  0:12.34 gcc    ║")
        print("║    6 user     20   0  4096 2048 1024 S  0.0  0.8  0:00.89 grep   ║")
        print("║    7 root     20   0  8192 4096 2048 S  0.1  1.6  0:03.45 sshd   ║")
        print("║    8 root     20   0  2048 1024  512 S  0.0  0.4  0:00.12 cron   ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print("║  Tasks:  8 total,  2 running                             ║")
        print("║  Load:   0.12 0.08 0.05                                  ║")
        print("║  Mem:    256MB total, 84MB used, 142MB free              ║")
        print("║  Swap:   0MB total, 0MB used                             ║")
        print("╚══════════════════════════════════════════════════════════════╝\033[0m")

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
        print("║  TEXT EDITORS:                                              ║")
        print("║    vi <file>        Vi-like modal editor                    ║")
        print("║    nano <file>      Nano-like simple editor                 ║")
        print("║    ed <file>        Line editor                             ║")
        print("║                                                              ║")
        print("║  DEVELOPMENT:                                               ║")
        print("║    asm <file.s>     x86 assembler                           ║")
        print("║    ld <file.o>      ELF linker                              ║")
        print("║                                                              ║")
        print("║  FILESYSTEM:                                                ║")
        print("║    mount            Show mount points                       ║")
        print("║    df               Show disk usage                         ║")
        print("║    mmap [file]      Show memory mappings                    ║")
        print("║                                                              ║")
        print("║  SYSTEM INFO:                                               ║")
        print("║    free             Show memory usage                       ║")
        print("║    lscpu            Show CPU information                    ║")
        print("║    top              Process monitor                         ║")
        print("║    dmesg            Kernel message log                      ║")
        print("║                                                              ║")
        print("║  DESKTOP/GUI:                                               ║")
        print("║    gui              Window manager / desktop                ║")
        print("║    filemanager      Graphical file manager                  ║")
        print("║    term             Terminal emulator info                  ║")
        print("║                                                              ║")
        print("║  IPC/PROCESS:                                               ║")
        print("║    ipcs             IPC status (queues/shm/sem)             ║")
        print("║    nice <pri> <pid> Set process priority                    ║")
        print("║    jobs             List background jobs                    ║")
        print("║    bg <job>         Resume job in background                ║")
        print("║    fg <job>         Bring job to foreground                 ║")
        print("║                                                              ║")
        print("║  NETWORK:                                                   ║")
        print("║    nslookup <host>  DNS lookup                              ║")
        print("║    dig <host>       DNS query (verbose)                     ║")
        print("║    curl <url>       HTTP client                             ║")
        print("║    wget <url>       Download file                           ║")
        print("║    dhcp             DHCP client status                      ║")
        print("║                                                              ║")
        print("║  DEBUGGING:                                                 ║")
        print("║    gdb              GDB-like debugger                       ║")
        print("║    strace <cmd>     System call tracer                      ║")
        print("║    ltrace <cmd>     Library call tracer                     ║")
        print("║                                                              ║")
        print("║  HARDWARE:                                                  ║")
        print("║    lspci            List PCI devices                        ║")
        print("║    lsusb            List USB devices                        ║")
        print("║                                                              ║")
        print("║  SCRIPTING/TOOLS:                                           ║")
        print("║    calc <expr>      Scientific calculator                   ║")
        print("║    script <file>    Execute shell script                    ║")
        print("║    tar [c|x|t]      TAR archiver                            ║")
        print("║    htop             Interactive process monitor             ║")
        print("║                                                              ║")
        print("║  NETWORK TOOLS:                                              ║")
        print("║    ifconfig         Network interface configuration         ║")
        print("║    netstat          Network connections                     ║")
        print("║    route            Routing table                           ║")
        print("║    arp              ARP table                               ║")
        print("║                                                              ║")
        print("║  SECURITY:                                                   ║")
        print("║    chmod <mode>     Change file permissions                 ║")
        print("║    encrypt <f> <p>  Encrypt file (AES-256)                  ║")
        print("║    decrypt <f> <p>  Decrypt file (AES-256)                  ║")
        print("║    passwd [user]    Change password                         ║")
        print("║                                                              ║")
        print("║  DEVELOPMENT:                                               ║")
        print("║    asm <file.s>     x86 assembler                           ║")
        print("║    ld <file.o>      ELF linker                              ║")
        print("║    make [target]    Build automation                        ║")
        print("║    awk '<pat> {a}'  Text processing                         ║")
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
        print("    ║    ARC A N I S   O S   v1.7.0     ║")
        print("    ║    AI-Native Operating System      ║")
        print("    ╚═══════════════════════════════════╝")
        print("\033[0m")

    # ---- Network Tools ----
    def cmd_ifconfig(self, args):
        """Network interface configuration."""
        if not args:
            print("\033[1;36meth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>\033[0m")
            print("        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255")
            print("        ether 02:42:ac:11:00:02  txqueuelen 1000")
            print("        RX packets 12345  bytes 1234567 (1.2 MB)")
            print("        TX packets 6789  bytes 789012 (789.0 KB)")
            print("        interrupts 10  base address 0x1000")
            print()
            print("\033[1;36mlo: flags=73<UP,LOOPBACK,RUNNING>\033[0m")
            print("        inet 127.0.0.1  netmask 255.0.0.0")
            print("        loop  txqueuelen 1000")
        elif args[0] == "eth0":
            print("\033[1;36meth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>\033[0m")
            print("        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255")
            print("        ether 02:42:ac:11:00:02  txqueuelen 1000")
        else:
            print(f"\033[31mifconfig: {args[0]}: no such interface\033[0m")

    def cmd_netstat(self, args):
        """Network connections."""
        print("\033[1;36mActive Internet connections:\033[0m")
        print(f"  {'PROTO':<8}  {'RECV-Q':<8}  {'SEND-Q':<8}  {'LOCAL':<22}  {'FOREIGN':<22}  {'STATE'}")
        conns = [
            ("tcp", 0, 0, "0.0.0.0:22", "0.0.0.0:*", "LISTEN"),
            ("tcp", 0, 0, "0.0.0.0:80", "0.0.0.0:*", "LISTEN"),
            ("tcp", 0, 0, "192.168.1.100:45678", "142.250.80.4:443", "ESTABLISHED"),
            ("tcp", 0, 0, "192.168.1.100:45679", "142.250.80.5:443", "ESTABLISHED"),
            ("udp", 0, 0, "0.0.0.0:53", "0.0.0.0:*", ""),
        ]
        for proto, rq, sq, local, foreign, state in conns:
            print(f"  {proto:<8}  {rq:<8}  {sq:<8}  {local:<22}  {foreign:<22}  {state}")

    def cmd_route(self, args):
        """Routing table."""
        print("\033[1;36mKernel IP routing table:\033[0m")
        print(f"  {'DESTINATION':<18}  {'GATEWAY':<18}  {'GENMASK':<18}  {'METRIC':<8}  {'IFACE'}")
        routes = [
            ("0.0.0.0", "192.168.1.1", "0.0.0.0", "100", "eth0"),
            ("192.168.1.0", "0.0.0.0", "255.255.255.0", "0", "eth0"),
            ("127.0.0.0", "0.0.0.0", "255.0.0.0", "0", "lo"),
        ]
        for dest, gw, mask, metric, iface in routes:
            print(f"  {dest:<18}  {gw:<18}  {mask:<18}  {metric:<8}  {iface}")

    def cmd_arp(self, args):
        """ARP table."""
        print("\033[1;36mARP table:\033[0m")
        print(f"  {'IP ADDRESS':<18}  {'HW ADDRESS':<20}  {'HW TYPE':<10}  {'IFACE'}")
        entries = [
            ("192.168.1.1", "aa:bb:cc:dd:ee:ff", "ether", "eth0"),
            ("192.168.1.100", "02:42:ac:11:00:02", "ether", "eth0"),
            ("192.168.1.200", "00:11:22:33:44:55", "ether", "eth0"),
        ]
        for ip, mac, hwtype, iface in entries:
            print(f"  {ip:<18}  {mac:<20}  {hwtype:<10}  {iface}")

    # ---- Security ----
    def cmd_chmod(self, args):
        """Change file permissions."""
        if len(args) < 2:
            print("\033[33mchmod: usage: chmod <mode> <file>\033[0m")
            print("  Modes: 755 (rwxr-xr-x), 644 (rw-r--r--), 600 (rw-------)")
            return
        mode, filename = args[0], args[1]
        print(f"\033[32mchmod {mode} {filename}\033[0m")
        print(f"  Permissions updated to {mode}")

    def cmd_encrypt(self, args):
        """Encrypt file."""
        if len(args) < 2:
            print("\033[33mencrypt: usage: encrypt <file> <password>\033[0m")
            return
        filename, password = args[0], args[1]
        print(f"\033[1;33m[ENCRYPT]\033[0m Encrypting: {filename}")
        print(f"  Algorithm: AES-256-CBC")
        print(f"  Key size: 256 bits")
        print(f"  Status: \033[32msuccess\033[0m")

    def cmd_decrypt(self, args):
        """Decrypt file."""
        if len(args) < 2:
            print("\033[33mdecrypt: usage: decrypt <file> <password>\033[0m")
            return
        filename, password = args[0], args[1]
        print(f"\033[1;33m[DECRYPT]\033[0m Decrypting: {filename}")
        print(f"  Algorithm: AES-256-CBC")
        print(f"  Status: \033[32msuccess\033[0m")

    def cmd_passwd(self, args):
        """Change password."""
        if not args:
            print("\033[33mpasswd: usage: passwd [username]\033[0m")
            return
        username = args[0]
        print(f"Changing password for {username}")
        print(f"  Password updated successfully")

    # ---- Development Tools ----
    def cmd_make(self, args):
        """Build automation."""
        if not args:
            print("\033[33mmake: usage: make [target] [options]\033[0m")
            print("  Targets: all, clean, install, test")
            print("  Options: -n (dry run), -v (verbose)")
            return
        target = args[0]
        print(f"\033[1;33m[MAKE]\033[0m Building target: {target}")
        print(f"  gcc -Wall -O2 -c main.c -o main.o")
        print(f"  gcc -Wall -O2 -c utils.c -o utils.o")
        print(f"  gcc main.o utils.o -o arcanis")
        print(f"  Build \033[32msuccessful\033[0m")

    def cmd_awk(self, args):
        """Text processing."""
        if not args:
            print("\033[33mawk: usage: awk '<pattern> {action}' [file]\033[0m")
            print("  Example: awk '{print $1}' file.txt")
            print("  Example: awk '/error/ {print NR, $0}' log.txt")
            return
        pattern = " ".join(args)
        print(f"\033[1;33m[AWK]\033[0m Processing: {pattern}")
        print(f"  1 line 1")
        print(f"  2 line 2")
        print(f"  3 line 3")


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
