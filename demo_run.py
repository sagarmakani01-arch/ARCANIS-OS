#!/usr/bin/env python3
"""Arcanis OS Demo — Automated run showing all features."""
import sys
sys.path.insert(0, ".")
from demo import Kernel, FileSystem, Shell

kernel = Kernel()
fs = FileSystem()
shell = Shell(kernel, fs)

# Start some processes
kernel.syscall("fork")
kernel.syscall("fork")

commands = [
    "sysinfo",
    "ls /",
    "tree /home",
    "cat /etc/motd",
    "cat /etc/version",
    "ps",
    "fork server",
    "fork worker",
    "ps",
    "echo Hello from Arcanis OS!",
    "grep TODO /home/user/notes.txt",
    "wc /var/log/kernel.log",
    "head /var/log/kernel.log",
    "tail /var/log/kernel.log",
    "date",
    "uname -a",
    "whoami",
    "hostname",
    "uptime",
    "env",
    "svc list",
    "user list",
    "pkg list",
    "net ifconfig",
    "net route",
    "net arp",
    "ping 192.168.1.1",
    "inference list files in the system",
    "inference what is the system status",
    "log",
    "history",
    "help",
]

for cmd in commands:
    print(f"\033[1;32marcanis> \033[0m{cmd}")
    shell._execute(cmd)
    print()

print("\033[90m" + "=" * 60)
print("Demo complete. Arcanis OS is ready.")
print("=" * 60 + "\033[0m")
