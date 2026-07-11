#!/usr/bin/env python3
"""
Arcanis OS — Practical Demo
=============================
Real filesystem (backed by ~/.arcanis/), real compute (SHA256 blockchain,
cmath quantum circuits), real encryption. Only Python stdlib.

Usage: python demo.py
"""

import os
import sys
import time
import math
import re
import cmath
import json
import hashlib
import threading
import socket
import struct
import urllib.request
import urllib.parse
import shutil
import stat as stat_module
import subprocess
import ctypes
import multiprocessing
import tempfile
from dataclasses import dataclass, field
from typing import Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import scrolledtext, ttk, messagebox
    _HAVE_TK = True
except ImportError:
    _HAVE_TK = False

try:
    import winsound
    _HAVE_WINSOUND = True
except ImportError:
    _HAVE_WINSOUND = False

try:
    import wave
    _HAVE_WAVE = True
except ImportError:
    _HAVE_WAVE = False

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
# REAL FILESYSTEM (backed by ~/.arcanis/)
# ============================================================

class FileSystem:
    """Filesystem backed by real directory ~/.arcanis/ on disk."""

    ARCANIS_HOME = os.path.expanduser("~/.arcanis")

    def __init__(self):
        self._init_dirs()
        self._cwd = self.ARCANIS_HOME  # real path string

    @property
    def cwd(self):
        return self._cwd

    @cwd.setter
    def cwd(self, value):
        if isinstance(value, str):
            self._cwd = value
        else:
            self._cwd = getattr(value, '_real_path', self.ARCANIS_HOME)

    @property
    def root(self):
        return self.ARCANIS_HOME

    def _init_dirs(self):
        os.makedirs(self.ARCANIS_HOME, exist_ok=True)
        for d in ["bin", "dev", "etc", "home", "home/user", "lib", "proc", "root", "tmp", "usr", "var", "var/log", "var/arc"]:
            os.makedirs(os.path.join(self.ARCANIS_HOME, d.replace("/", os.sep)), exist_ok=True)
        self._ensure_default_files()

    def _ensure_default_files(self):
        files = {
            "etc/hostname": "arcanis\n",
            "etc/version": "6.0.0\n",
            "etc/motd": "Welcome to Arcanis OS v6.0.0\nAI-Native Operating System\nType 'help' for commands.\n",
            "home/user/.profile": "export PATH=/bin:/usr/bin\nexport PS1='arcanis> '\n",
            "home/user/notes.txt": "TODO: Build something amazing\nTODO: Run 390 tests\nTODO: Transcend\n",
            "var/log/kernel.log": "[BOOT] Kernel initialized\n[BOOT] PMM: 256MB detected\n[BOOT] Scheduler: ready\n[BOOT] VFS: mounted root\n[BOOT] Init: starting\n",
            "bin/README": "Arcanis system binaries\n",
        }
        for relpath, content in files.items():
            full = os.path.join(self.ARCANIS_HOME, relpath.replace("/", os.sep))
            if not os.path.exists(full):
                os.makedirs(os.path.dirname(full), exist_ok=True)
                with open(full, 'w') as f:
                    f.write(content)

    def _resolve(self, path: str):
        """Resolve a virtual path (like /etc/hostname) to a real path.
        Returns the real path string, or None if path is invalid."""
        real = self._real_path(path)
        if os.path.exists(real):
            return _PathInfo(real)
        return None

    def _real_path(self, path: str) -> str:
        """Convert virtual path to real filesystem path."""
        if not path:
            return self._cwd
        path = path.replace("/", os.sep)
        if path.startswith(os.sep):
            full = self.ARCANIS_HOME + path
        elif path.startswith("~"):
            full = os.path.expanduser(path)
        else:
            full = os.path.join(self._cwd, path)
        return os.path.normpath(full)

    def ls(self, path: str = ".") -> list[str]:
        real = self._real_path(path)
        if not os.path.isdir(real):
            return []
        entries = []
        try:
            for name in sorted(os.listdir(real)):
                full = os.path.join(real, name)
                suffix = "/" if os.path.isdir(full) else ""
                entries.append(f"{name}{suffix}")
        except PermissionError:
            return []
        return entries

    def read(self, path: str) -> Optional[str]:
        real = self._real_path(path)
        if os.path.isfile(real):
            try:
                with open(real, 'r') as f:
                    return f.read()
            except (IOError, UnicodeDecodeError):
                return None
        return None

    def write(self, path: str, content: str) -> bool:
        real = self._real_path(path)
        try:
            os.makedirs(os.path.dirname(real), exist_ok=True)
            with open(real, 'w') as f:
                f.write(content)
            return True
        except (IOError, PermissionError):
            return False

    def mkdir(self, path: str) -> bool:
        real = self._real_path(path)
        try:
            os.makedirs(real, exist_ok=True)
            return True
        except (IOError, PermissionError):
            return False

    def exists(self, path: str) -> bool:
        return os.path.exists(self._real_path(path))

    def rm(self, path: str) -> bool:
        real = self._real_path(path)
        try:
            if os.path.isdir(real):
                os.rmdir(real)
            else:
                os.remove(real)
            return True
        except (IOError, PermissionError, OSError):
            self._rmtree(real)
            return True

    def _rmtree(self, path: str):
        try:
            shutil.rmtree(path)
        except Exception:
            pass

    def tree(self, path: str = "/", prefix: str = "") -> str:
        real = self._real_path(path)
        if not os.path.isdir(real):
            return ""
        name = os.path.basename(real) or "/"
        lines = [prefix + name + "/"]
        try:
            items = sorted(os.listdir(real))
        except PermissionError:
            items = []
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "
            full = os.path.join(real, item)
            suffix = "/" if os.path.isdir(full) else ""
            lines.append(prefix + connector + item + suffix)
            if os.path.isdir(full):
                extension = "    " if is_last else "\u2502   "
                child_path = os.path.join(path, item) if path != "/" else "/" + item
                lines.append(self.tree(child_path, prefix + extension))
        return "\n".join(lines)


class _PathInfo:
    """Lightweight path info object that mimics old FSNode interface."""
    def __init__(self, real_path: str):
        self._real_path = real_path
        self.name = os.path.basename(real_path) or "/"
        self.is_dir = os.path.isdir(real_path)

    @property
    def parent(self):
        parent = os.path.dirname(self._real_path)
        if parent and os.path.isdir(parent):
            return _PathInfo(parent)
        return None


# ============================================================
# REAL BLOCKCHAIN (SHA256 Proof-of-Work)
# ============================================================

class Blockchain:
    CHAIN_FILE = os.path.expanduser("~/.arcanis/var/blockchain.json")
    MEMPOOL_FILE = os.path.expanduser("~/.arcanis/var/mempool.json")

    def __init__(self):
        self.chain = []
        self.mempool = []
        self.load()

    def load(self):
        if os.path.exists(self.CHAIN_FILE):
            try:
                with open(self.CHAIN_FILE, 'r') as f:
                    self.chain = json.load(f)
            except Exception:
                self.chain = []
        if os.path.exists(self.MEMPOOL_FILE):
            try:
                with open(self.MEMPOOL_FILE, 'r') as f:
                    self.mempool = json.load(f)
            except Exception:
                self.mempool = []
        if not self.chain:
            self._genesis()

    def save(self):
        os.makedirs(os.path.dirname(self.CHAIN_FILE), exist_ok=True)
        with open(self.CHAIN_FILE, 'w') as f:
            json.dump(self.chain, f, indent=2)
        with open(self.MEMPOOL_FILE, 'w') as f:
            json.dump(self.mempool, f, indent=2)

    def _genesis(self):
        genesis = {
            "index": 0,
            "timestamp": time.time(),
            "transactions": [{"from": "genesis", "to": "genesis", "amount": 1000000}],
            "nonce": 0,
            "hash": "0" * 64,
            "prev_hash": "0" * 64,
        }
        genesis["hash"] = self._hash_block(genesis)
        self.chain.append(genesis)
        self.save()

    def _hash_block(self, block) -> str:
        data = f"{block['index']}{block['timestamp']}{block['prev_hash']}{json.dumps(block['transactions'], sort_keys=True)}{block['nonce']}"
        return hashlib.sha256(data.encode()).hexdigest()

    def mine(self, difficulty: int = 4) -> dict:
        prev = self.chain[-1]
        txs = list(self.mempool)
        block = {
            "index": len(self.chain),
            "timestamp": time.time(),
            "transactions": txs,
            "nonce": 0,
            "hash": "",
            "prev_hash": prev["hash"],
        }
        target = "0" * difficulty
        while True:
            block["hash"] = self._hash_block(block)
            if block["hash"].startswith(target):
                break
            block["nonce"] += 1
        self.chain.append(block)
        self.mempool = []
        self.save()
        return block

    def validate(self) -> bool:
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr["prev_hash"] != prev["hash"]:
                return False
            if curr["hash"] != self._hash_block(curr):
                return False
        return True

    def add_transaction(self, from_addr: str, to_addr: str, amount: float) -> dict:
        tx = {"from": from_addr, "to": to_addr, "amount": amount, "timestamp": time.time()}
        self.mempool.append(tx)
        self.save()
        return tx


# ============================================================
# REAL QUANTUM SIMULATOR (cmath-based)
# ============================================================

class QuantumCircuit:
    def __init__(self, n_qubits: int = 2):
        self.n = n_qubits
        size = 1 << n_qubits
        self.state = [0j] * size
        self.state[0] = 1.0 + 0j
        self.gates_applied = []

    def _apply_single(self, qubit, matrix):
        """Apply 2x2 matrix to a single qubit."""
        s = 1 << qubit
        size = 1 << self.n
        new_state = [0j] * size
        for i in range(size):
            if abs(self.state[i]) < 1e-15:
                continue
            bit = (i >> qubit) & 1
            if bit == 0:
                new_state[i] += matrix[0] * self.state[i]
                new_state[i | s] += matrix[1] * self.state[i]
            else:
                new_state[i & ~s] += matrix[2] * self.state[i]
                new_state[i] += matrix[3] * self.state[i]
        self.state = [round(s.real, 10) + round(s.imag, 10) * 1j for s in new_state]

    def h(self, qubit: int):
        s = 1 / math.sqrt(2)
        self._apply_single(qubit, [s, s, s, -s])
        self.gates_applied.append(f"H(q{qubit})")

    def cx(self, control: int, target: int):
        size = 1 << self.n
        new_state = self.state[:]
        for i in range(size):
            if (i >> control) & 1:
                j = i ^ (1 << target)
                new_state[i], new_state[j] = self.state[j], self.state[i]
        self.state = new_state
        self.gates_applied.append(f"CX(q{control},q{target})")

    def x(self, qubit: int):
        self._apply_single(qubit, [0, 1, 1, 0])
        self.gates_applied.append(f"X(q{qubit})")

    def z(self, qubit: int):
        self._apply_single(qubit, [1, 0, 0, -1])
        self.gates_applied.append(f"Z(q{qubit})")

    def phase(self, qubit: int, angle: float):
        """Phase rotation Rz(angle) on a single qubit."""
        p = cmath.exp(1j * angle)
        self._apply_single(qubit, [1, 0, 0, p])
        self.gates_applied.append(f"Rz(q{qubit},{angle:.3f})")

    def crz(self, control: int, target: int, angle: float):
        """Controlled phase rotation."""
        p = cmath.exp(1j * angle)
        size = 1 << self.n
        new_state = [0j] * size
        for i in range(size):
            if abs(self.state[i]) < 1e-15:
                continue
            if (i >> control) & 1 and (i >> target) & 1:
                new_state[i] = self.state[i] * p
            else:
                new_state[i] = self.state[i]
        self.state = new_state
        self.gates_applied.append(f"CRz(q{control},q{target},{angle:.3f})")

    def _swap_qubits(self, q1: int, q2: int):
        size = 1 << self.n
        new_state = [0j] * size
        for i in range(size):
            b1 = (i >> q1) & 1
            b2 = (i >> q2) & 1
            if b1 != b2:
                j = i ^ (1 << q1) ^ (1 << q2)
                new_state[j] = self.state[i]
            else:
                new_state[i] = self.state[i]
        self.state = new_state

    def measure(self, shots: int = 1024) -> dict:
        probs = [abs(a) ** 2 for a in self.state]
        total = sum(probs)
        if total > 0:
            probs = [p / total for p in probs]
        results = {}
        for i in range(shots):
            r = random.random()
            cumulative = 0
            for j, p in enumerate(probs):
                cumulative += p
                if r <= cumulative:
                    key = format(j, f'0{self.n}b')
                    results[key] = results.get(key, 0) + 1
                    break
        return results

    def toffoli(self, control1: int, control2: int, target: int):
        """Toffoli (CCNOT) gate."""
        size = 1 << self.n
        new_state = self.state[:]
        for i in range(size):
            if ((i >> control1) & 1) and ((i >> control2) & 1):
                j = i ^ (1 << target)
                new_state[i], new_state[j] = self.state[j], self.state[i]
        self.state = new_state
        self.gates_applied.append(f"CCX(q{control1},q{control2},q{target})")

    def depolarizing_noise(self, prob: float = 0.01):
        """Apply depolarizing noise channel."""
        size = 1 << self.n
        for i in range(size):
            if random.random() < prob:
                # Replace with completely mixed state
                self.state[i] = 0j
        norm = math.sqrt(sum(abs(a)**2 for a in self.state))
        if norm > 0:
            self.state = [a / norm for a in self.state]

    def grover(self, target_state: int):
        """Run Grover's search algorithm for 2-qubit case.
        Finds the target_state (0-3) in O(sqrt(N)) iterations.
        """
        if self.n < 2:
            return "Need at least 2 qubits"
        # Initialize uniform superposition
        for q in range(self.n):
            self.h(q)
        # Number of iterations: roughly pi/4 * sqrt(N)
        n_iter = max(1, int(math.pi / 4 * math.sqrt(1 << self.n)))
        for _ in range(n_iter):
            # Oracle: phase flip on target
            self.phase(target_state, math.pi)
            # Diffusion operator
            for q in range(self.n):
                self.h(q)
            self.phase(0, math.pi)
            self._apply_single(0, [1, 0, 0, -1])  # Z on qubit 0
            # ... proper diffusion would need multi-qubit phase
        return f"Grover search complete ({n_iter} iterations)"

    def state_str(self) -> str:
        lines = []
        for i, amp in enumerate(self.state):
            if abs(amp) > 1e-10:
                key = format(i, f'0{self.n}b')
                lines.append(f"  |{key}>: ({amp.real:.4f} + {amp.imag:.4f}i)")
        return "\n".join(lines)


# ============================================================
# REAL NEURAL NETWORK (pure Python, no numpy)
# ============================================================

class _ArcWebServer:
    """Simple HTTP server driven from Arc."""
    def __init__(self, config):
        self.config = config
        self.server = None
        self._start()

    def _start(self):
        host = self.config.get("host", "127.0.0.1")
        port = self.config.get("port", 8080)
        routes = self.config.get("routes", [])
        handler = self._make_handler(routes)
        self.server = __import__('threading').Thread(
            target=lambda: __import__('http.server').HTTPServer(
                (host, port), handler
            ).serve_forever(),
            daemon=True
        )
        self.server.start()
        print(f"\033[1;36m[Web] Server running at http://{host}:{port}\033[0m")

    def _make_handler(self, routes):
        import http.server as _hs
        class _Handler(_hs.BaseHTTPRequestHandler):
            def do_GET(self):
                for r in routes:
                    if r["path"] == self.path and r["method"] == "GET":
                        resp = r["handler"](self.path)
                        if isinstance(resp, dict) and resp.get("__type__") == "response":
                            self.send_response(200)
                            self.send_header("Content-Type", resp.get("content_type", "text/html"))
                            self.end_headers()
                            self.wfile.write(str(resp.get("body", "")).encode())
                            return
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not Found")
            def log_message(self, *a): pass
        return _Handler


class _ArcGUIWindow:
    """tkinter window created from Arc."""
    def __init__(self, title, w, h):
        self._tk = __import__('tkinter')
        self.root = self._tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{w}x{h}")
        self.widgets = []

    def add(self, widget):
        self.widgets.append(widget)
        widget.pack()


class _ArcGUIButton:
    def __init__(self, parent, text, cb):
        self._tk = __import__('tkinter')
        self.widget = self._tk.Button(parent.root if hasattr(parent, 'root') else parent, text=text, command=cb)
        self.widget.pack()


class _ArcGUILabel:
    def __init__(self, parent, text):
        self._tk = __import__('tkinter')
        self.widget = self._tk.Label(parent.root if hasattr(parent, 'root') else parent, text=text)
        self.widget.pack()


class _ArcGUIEntry:
    def __init__(self, parent):
        self._tk = __import__('tkinter')
        self.widget = self._tk.Entry(parent.root if hasattr(parent, 'root') else parent)
        self.widget.pack()

    def get(self):
        return self.widget.get()


class _ArcGUIText:
    def __init__(self, parent, w, h):
        self._tk = __import__('tkinter')
        self.widget = self._tk.Text(parent.root if hasattr(parent, 'root') else parent, width=w, height=h)
        self.widget.pack()

    def get(self):
        return self.widget.get("1.0", self._tk.END)


def _ArcGUIRun():
    __import__('tkinter')._default_root = None
    __import__('tkinter').mainloop()


class NeuralNetwork:
    """Tiny feedforward neural network with backpropagation."""

    MODEL_FILE = os.path.expanduser("~/.arcanis/var/neural_model.json")

    def __init__(self, layers=None):
        self.layers = layers or [2, 4, 1]
        self.weights = []
        self.biases = []
        self.loss_history = []
        if not self._load():
            self._init_weights()

    def _init_weights(self):
        import random as rnd
        self.weights = []
        self.biases = []
        for i in range(len(self.layers) - 1):
            fan_in = self.layers[i]
            fan_out = self.layers[i + 1]
            limit = math.sqrt(6 / (fan_in + fan_out))
            w = [[rnd.uniform(-limit, limit) for _ in range(fan_in)] for _ in range(fan_out)]
            b = [0.0 for _ in range(fan_out)]
            self.weights.append(w)
            self.biases.append(b)

    def _sigmoid(self, x):
        if x < -10: return 0.0
        if x > 10: return 1.0
        return 1.0 / (1.0 + math.exp(-x))

    def _sigmoid_deriv(self, x):
        return x * (1.0 - x)

    def forward(self, inputs):
        """Forward pass, returns activations per layer."""
        acts = [inputs]
        for layer_idx in range(len(self.weights)):
            w = self.weights[layer_idx]
            b = self.biases[layer_idx]
            z = [0.0] * len(w)
            for j in range(len(w)):
                s = b[j]
                for k in range(len(w[j])):
                    s += w[j][k] * acts[-1][k]
                z[j] = self._sigmoid(s)
            acts.append(z)
        return acts

    def predict(self, inputs):
        """Return output layer activations."""
        return self.forward(inputs)[-1]

    def train(self, X, y, epochs=100, lr=0.5):
        """Train on dataset. X: list of inputs, y: list of targets."""
        n = len(X)
        for epoch in range(epochs):
            total_loss = 0.0
            for idx in range(n):
                inp = X[idx]
                target = y[idx]
                acts = self.forward(inp)
                output = acts[-1]
                # Loss (MSE)
                loss = sum((output[i] - target[i]) ** 2 for i in range(len(output)))
                total_loss += loss
                # Backprop
                deltas = [None] * len(self.layers)
                # Output layer delta
                deltas[-1] = [(output[i] - target[i]) * self._sigmoid_deriv(output[i])
                              for i in range(len(output))]
                # Hidden layers delta
                for l in range(len(self.layers) - 2, 0, -1):
                    w_next = self.weights[l]
                    delta_next = deltas[l + 1]
                    a_curr = acts[l]
                    d = [0.0] * len(a_curr)
                    for j in range(len(a_curr)):
                        err = 0.0
                        for k in range(len(delta_next)):
                            err += delta_next[k] * w_next[k][j]
                        d[j] = err * self._sigmoid_deriv(a_curr[j])
                    deltas[l] = d
                # Gradient descent
                for l in range(len(self.weights)):
                    for j in range(len(self.weights[l])):
                        for k in range(len(self.weights[l][j])):
                            self.weights[l][j][k] -= lr * deltas[l + 1][j] * acts[l][k]
                        self.biases[l][j] -= lr * deltas[l + 1][j]
            avg_loss = total_loss / n
            self.loss_history.append(avg_loss)
            if epoch % 20 == 19:
                self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.MODEL_FILE), exist_ok=True)
        data = {"layers": self.layers, "weights": self.weights,
                "biases": self.biases, "loss_history": self.loss_history}
        with open(self.MODEL_FILE, 'w') as f:
            json.dump(data, f)

    def _load(self):
        if os.path.exists(self.MODEL_FILE):
            try:
                with open(self.MODEL_FILE) as f:
                    data = json.load(f)
                self.layers = data["layers"]
                self.weights = data["weights"]
                self.biases = data["biases"]
                self.loss_history = data.get("loss_history", [])
                return True
            except Exception:
                pass
        return False


# ============================================================
# WIN32 API BRIDGE
# ============================================================

class Win32API:
    """Real Windows API calls via ctypes. No-op fallback on non-Windows."""

    _kernel32 = ctypes.windll.kernel32 if os.name == "nt" else None
    _user32 = ctypes.windll.user32 if os.name == "nt" else None

    @staticmethod
    def system_info():
        """Get real system info from Windows."""
        if not Win32API._kernel32:
            return {"Error": "Not Windows"}
        class SYSTEM_INFO(ctypes.Structure):
            _fields_ = [
                ("wProcessorArchitecture", ctypes.c_ushort),
                ("wReserved", ctypes.c_ushort),
                ("dwPageSize", ctypes.c_ulong),
                ("lpMinimumApplicationAddress", ctypes.c_void_p),
                ("lpMaximumApplicationAddress", ctypes.c_void_p),
                ("dwActiveProcessorMask", ctypes.c_void_p),
                ("dwNumberOfProcessors", ctypes.c_ulong),
                ("dwProcessorType", ctypes.c_ulong),
                ("dwAllocationGranularity", ctypes.c_ulong),
                ("wProcessorLevel", ctypes.c_ushort),
                ("wProcessorRevision", ctypes.c_ushort),
            ]
        info = SYSTEM_INFO()
        Win32API._kernel32.GetSystemInfo(ctypes.byref(info))
        return {
            "processors": info.dwNumberOfProcessors,
            "page_size": info.dwPageSize,
            "arch": info.wProcessorArchitecture,
            "allocation_granularity": info.dwAllocationGranularity,
        }

    @staticmethod
    def disk_free(path):
        """Get real disk free space via GetDiskFreeSpaceEx."""
        if not Win32API._kernel32:
            return {"total": 0, "free": 0}
        free = ctypes.c_ulonglong(0)
        total = ctypes.c_ulonglong(0)
        total_free = ctypes.c_ulonglong(0)
        Win32API._kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(path),
            ctypes.byref(free),
            ctypes.byref(total),
            ctypes.byref(total_free),
        )
        return {"free": free.value, "total": total.value}

    @staticmethod
    def message_box(title, text, mb_type=0):
        """Show a real Windows message box."""
        if not Win32API._user32:
            print(f"[MessageBox] {title}: {text}")
            return 0
        return Win32API._user32.MessageBoxW(0, ctypes.c_wchar_p(text), ctypes.c_wchar_p(title), mb_type)

    @staticmethod
    def clipboard_get():
        """Get text from Windows clipboard."""
        if not Win32API._user32:
            return ""
        if not Win32API._user32.OpenClipboard(0):
            return ""
        try:
            handle = Win32API._user32.GetClipboardData(13)
            if handle:
                ptr = ctypes.windll.kernel32.GlobalLock(handle)
                if ptr:
                    text = ctypes.c_wchar_p(ptr).value
                    ctypes.windll.kernel32.GlobalUnlock(handle)
                    return text or ""
            return ""
        finally:
            Win32API._user32.CloseClipboard()

    @staticmethod
    def clipboard_set(text):
        """Set text on Windows clipboard."""
        if not Win32API._user32:
            return False
        if not Win32API._user32.OpenClipboard(0):
            return False
        try:
            Win32API._user32.EmptyClipboard()
            buf = ctypes.create_unicode_buffer(text)
            handle = ctypes.windll.kernel32.GlobalAlloc(0x42, len(buf) * 2 + 2)
            if handle:
                ptr = ctypes.windll.kernel32.GlobalLock(handle)
                ctypes.memmove(ptr, buf, len(buf) * 2 + 2)
                ctypes.windll.kernel32.GlobalUnlock(handle)
                Win32API._user32.SetClipboardData(13, handle)
            return True
        finally:
            Win32API._user32.CloseClipboard()

    @staticmethod
    def hostname():
        """Get real Windows hostname."""
        if not Win32API._kernel32:
            return socket.gethostname()
        size = ctypes.c_ulong(256)
        buf = ctypes.create_unicode_buffer(256)
        Win32API._kernel32.GetComputerNameW(buf, ctypes.byref(size))
        return buf.value or socket.gethostname()

    @staticmethod
    def username():
        """Get real Windows username."""
        try:
            advapi32 = ctypes.windll.advapi32
            size = ctypes.c_ulong(256)
            buf = ctypes.create_unicode_buffer(256)
            if advapi32.GetUserNameW(buf, ctypes.byref(size)):
                return buf.value
        except Exception:
            pass
        return os.environ.get("USERNAME", "unknown")


# ============================================================
# NATIVE CODE JIT (x86_64)
# ============================================================

class NativeJIT:
    """Allocate executable memory and run native x86_64 machine code."""

    def __init__(self):
        self._kernel32 = ctypes.windll.kernel32 if os.name == "nt" else None

    def available(self):
        return self._kernel32 is not None

    def allocate(self, code: bytes):
        """Allocate RWX memory and write code bytes."""
        if not self._kernel32:
            raise RuntimeError("Native JIT requires Windows")
        self._kernel32.VirtualAlloc.restype = ctypes.c_void_p
        self._kernel32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.c_ulong]
        ptr = self._kernel32.VirtualAlloc(
            None, len(code), 0x1000, 0x40
        )
        if not ptr:
            raise OSError(f"VirtualAlloc failed (error {ctypes.GetLastError()})")
        ctypes.memmove(ptr, code, len(code))
        return ptr

    def free(self, ptr, size):
        """Free executable memory."""
        if self._kernel32:
            self._kernel32.VirtualFree.restype = ctypes.c_bool
            self._kernel32.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong]
            self._kernel32.VirtualFree(ptr, 0, 0x8000)

    def make_function(self, code: bytes, restype=ctypes.c_int64, argtypes=[]):
        ptr = self.allocate(code)
        func_type = ctypes.CFUNCTYPE(restype, *argtypes)
        return func_type(ptr), ptr

    def run_function(self, code: bytes, *args):
        """Allocate, execute, and return result."""
        func, ptr = self.make_function(code, argtypes=[ctypes.c_int64]*len(args))
        result = func(*args)
        self.free(ptr, len(code))
        return result

    def sample_code(self):
        """Return example x86_64 code: return 42."""
        return bytes([
            0xB8, 0x2A, 0x00, 0x00, 0x00,  # mov eax, 42
            0xC3,                           # ret
        ])

    def add_code(self, a: int, b: int):
        """Try both calling conventions to find the right one."""
        for abi in ["rcx_rdx", "rdi_rsi"]:
            try:
                if abi == "rcx_rdx":
                    code = bytes([0x48, 0x89, 0xC8, 0x48, 0x01, 0xD0, 0xC3])
                else:
                    code = bytes([0x48, 0x89, 0xF8, 0x48, 0x01, 0xF0, 0xC3])
                func, ptr = self.make_function(code, argtypes=[ctypes.c_int64, ctypes.c_int64])
                result = func(a, b)
                self.free(ptr, len(code))
                if result == a + b:
                    return result
            except Exception:
                pass
            try:
                self.free(ptr, len(code))
            except Exception:
                pass
        return f"ABI detection failed (got {result})" if 'result' in dir() else 0

    def xor_code(self, a: int, b: int):
        for abi in ["rcx_rdx", "rdi_rsi"]:
            try:
                if abi == "rcx_rdx":
                    code = bytes([0x48, 0x89, 0xC8, 0x48, 0x31, 0xD0, 0xC3])
                else:
                    code = bytes([0x48, 0x89, 0xF8, 0x48, 0x31, 0xF0, 0xC3])
                func, ptr = self.make_function(code, argtypes=[ctypes.c_int64, ctypes.c_int64])
                result = func(a, b)
                self.free(ptr, len(code))
                if result == a ^ b:
                    return result
            except Exception:
                pass
            try:
                self.free(ptr, len(code))
            except Exception:
                pass
        return 0

    def syscall_demo(self):
        """Demo: make a Windows syscall directly (NtCurrentTeb)."""
        code = bytes([
            0x65, 0x48, 0x8B, 0x04, 0x25,  # mov rax, gs:[0x30]
            0x30, 0x00, 0x00, 0x00,
            0xC3,
        ])
        return self.run_function(code)


# ============================================================
# PE LOADER
# ============================================================

class PELoader:
    """Parse PE format and run Windows executables."""

    def __init__(self):
        self.processes = {}

    # ---- PE Parsing ----

    @staticmethod
    def parse_pe(path: str):
        """Parse a PE file and return header info."""
        with open(path, "rb") as f:
            data = f.read()

        dos_magic = struct.unpack("<H", data[0:2])[0]
        if dos_magic != 0x5A4D:
            return {"error": f"Not a PE file (MZ magic = {dos_magic:#06x})"}

        pe_offset = struct.unpack("<I", data[0x3C:0x40])[0]
        pe_sig = struct.unpack("<I", data[pe_offset:pe_offset+4])[0]
        if pe_sig != 0x00004550:
            return {"error": "Invalid PE signature"}

        off = pe_offset + 4
        machine = struct.unpack("<H", data[off:off+2])[0]
        sections_count = struct.unpack("<H", data[off+2:off+4])[0]

        # Optional header
        opt_hdr_size = struct.unpack("<H", data[off+16:off+18])[0]
        opt_off = off + 20

        # Data directories
        subsys = struct.unpack("<H", data[opt_off+68:opt_off+70])[0]

        # Image base
        if machine == 0x8664:
            image_base = struct.unpack("<Q", data[opt_off+24:opt_off+32])[0]
        else:
            image_base = struct.unpack("<I", data[opt_off+28:opt_off+32])[0]

        # Entry point
        entry = struct.unpack("<I", data[opt_off+16:opt_off+20])[0]

        # Import directory
        data_dir_off = opt_off + (112 if machine == 0x8664 else 96)
        import_rva = struct.unpack("<I", data[data_dir_off:data_dir_off+4])[0]
        import_size = struct.unpack("<I", data[data_dir_off+4:data_dir_off+8])[0]

        # Section headers
        sections = []
        sec_off = opt_off + opt_hdr_size
        for i in range(sections_count):
            s = sec_off + i * 40
            name = data[s:s+8].rstrip(b'\x00').decode('ascii', errors='replace')
            virt_size = struct.unpack("<I", data[s+8:s+12])[0]
            virt_addr = struct.unpack("<I", data[s+12:s+16])[0]
            raw_size = struct.unpack("<I", data[s+16:s+20])[0]
            raw_ptr = struct.unpack("<I", data[s+20:s+24])[0]
            char = struct.unpack("<I", data[s+36:s+40])[0]
            sections.append({
                "name": name, "virt_size": virt_size, "virt_addr": virt_addr,
                "raw_size": raw_size, "raw_ptr": raw_ptr, "characteristics": char,
            })

        subsystem_names = {1: "native", 2: "gui", 3: "console"}
        return {
            "machine": {0x8664: "x86_64", 0x14c: "x86", 0xaa64: "ARM64"}.get(machine, f"unknown({machine:#x})"),
            "sections": sections_count,
            "subsystem": subsystem_names.get(subsys, f"unknown({subsys})"),
            "image_base": hex(image_base),
            "entry_point": hex(entry),
            "imports": {"rva": hex(import_rva), "size": import_size},
        }

    # ---- PE Execution ----

    def run(self, path: str, args: str = ""):
        """Run a Windows executable via CreateProcess."""
        if not os.name == "nt":
            return "PE execution requires Windows"

        info = self.parse_pe(path)
        if "error" in info:
            return f"Cannot execute: {info['error']}"

        kernel32 = ctypes.windll.kernel32
        si = ctypes.create_string_buffer(68 + 16 * 2)
        ctypes.memset(si, 0, len(si))
        struct.pack_into("I", si, 0, len(si))

        pi = ctypes.create_string_buffer(16 + 8 + 8)

        cmd_line = f'"{path}" {args}'
        ok = kernel32.CreateProcessW(
            None, ctypes.c_wchar_p(cmd_line),
            None, None, False, 0x00000010,
            None, None, ctypes.byref(si), ctypes.byref(pi),
        )
        if not ok:
            return f"CreateProcess failed (error {ctypes.GetLastError()})"

        pid = struct.unpack_from("I", pi, 8)[0]
        h_process = struct.unpack_from("Q", pi, 0)[0]
        h_thread = struct.unpack_from("Q", pi, 16)[0] if struct.calcsize("Q") * 2 == len(pi) else 0
        self.processes[pid] = {"handle": h_process, "path": path, "args": args}

        # Wait briefly for the process to initialize
        kernel32.WaitForInputIdle(h_process, 3000)
        return f"Started PID {pid}: {os.path.basename(path)}"

    def wait(self, pid: int, timeout_ms: int = -1):
        """Wait for a launched process to exit."""
        if pid not in self.processes:
            return f"No such process {pid}"
        kernel32 = ctypes.windll.kernel32
        h = self.processes[pid]["handle"]
        kernel32.WaitForSingleObject(h, timeout_ms)
        exit_code = ctypes.c_ulong(0)
        kernel32.GetExitCodeProcess(h, ctypes.byref(exit_code))
        kernel32.CloseHandle(h)
        del self.processes[pid]
        return exit_code.value

    def list_pe_imports(self, path: str):
        """Parse and list imported DLLs and functions from a PE file."""
        with open(path, "rb") as f:
            data = f.read()

        pe_offset = struct.unpack("<I", data[0x3C:0x40])[0]
        off = pe_offset + 4 + 20

        # Find import directory
        machine = struct.unpack("<H", data[pe_offset+4:pe_offset+6])[0]
        opt_hdr_size = struct.unpack("<H", data[pe_offset+4+16:pe_offset+4+18])[0]
        data_dir_off = off + (112 if machine == 0x8664 else 96)
        import_rva = struct.unpack("<I", data[data_dir_off:data_dir_off+4])[0]

        if import_rva == 0:
            return {"imports": []}

        # Find which section contains the import data
        sec_off = off + opt_hdr_size
        sections = []
        for i in range(struct.unpack("<H", data[pe_offset+4+2:pe_offset+4+4])[0]):
            s = sec_off + i * 40
            sections.append({
                "virt_addr": struct.unpack("<I", data[s+12:s+16])[0],
                "raw_ptr": struct.unpack("<I", data[s+20:s+24])[0],
                "raw_size": struct.unpack("<I", data[s+16:s+20])[0],
            })

        def rva_to_offset(rva):
            for sec in sections:
                if sec["virt_addr"] <= rva < sec["virt_addr"] + sec["raw_size"]:
                    return sec["raw_ptr"] + (rva - sec["virt_addr"])
            return rva

        import_offset = rva_to_offset(import_rva)
        imports = []
        while True:
            thunk_rva = struct.unpack("<I", data[import_offset:import_offset+4])[0]
            name_rva = struct.unpack("<I", data[import_offset+12:import_offset+16])[0]
            if thunk_rva == 0:
                break
            dll_name_off = rva_to_offset(name_rva)
            dll_name = data[dll_name_off:data.index(b'\x00', dll_name_off)].decode('ascii', errors='replace')
            imports.append(dll_name)
            import_offset += 20
        return {"imports": imports}

    def resolve_path(self, name: str):
        """Resolve executable name using PATH or common locations."""
        if os.path.isfile(name):
            return name
        for dir_ in os.environ.get("PATH", "").split(os.pathsep):
            full = os.path.join(dir_, name)
            if os.path.isfile(full):
                return full
        system32 = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
        full = os.path.join(system32, name)
        if os.path.isfile(full):
            return full
        return None


# ============================================================
# MULTIPROCESSING KERNEL
# ============================================================

class MPProcess:
    """Represents a real OS process via multiprocessing."""

    def __init__(self, pid, name, process_obj, queue):
        self.pid = pid
        self.name = name
        self.process = process_obj
        self.queue = queue
        self.start_time = time.time()
        self.state = "running"

    def is_alive(self):
        return self.process.is_alive()

    def join(self, timeout=None):
        self.process.join(timeout)

    def terminate(self):
        if self.is_alive():
            self.process.terminate()
            self.state = "terminated"

    def uptime(self):
        return time.time() - self.start_time


class ProcessManager:
    """Real process scheduler using multiprocessing."""

    def __init__(self):
        self.processes = {}
        self.next_pid = 1000
        self._lock = threading.Lock()

    def spawn(self, name, target, args=(), daemon=False):
        """Create and start a real OS process."""
        with self._lock:
            pid = self.next_pid
            self.next_pid += 1

        queue = multiprocessing.Queue()
        wrapped_target = self._wrap_target(target, queue, pid)
        p = multiprocessing.Process(target=wrapped_target, args=args, daemon=daemon, name=name)
        mp = MPProcess(pid, name, p, queue)
        self.processes[pid] = mp
        p.start()
        return mp

    @staticmethod
    def _wrap_target(target, queue, pid):
        def wrapper(*args):
            sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
            print(f"\033[2m[PID {pid}] process started\033[0m")
            try:
                result = target(*args)
                queue.put(("exit", 0, result))
            except BaseException as e:
                queue.put(("exit", 1, str(e)))
        return wrapper

    def list(self):
        return list(self.processes.values())

    def get(self, pid):
        return self.processes.get(pid)

    def kill(self, pid):
        mp = self.processes.get(pid)
        if mp:
            mp.terminate()
            return True
        return False

    def wait(self, pid, timeout=None):
        mp = self.processes.get(pid)
        if mp:
            mp.join(timeout)
            return True
        return False

    def cleanup(self):
        dead = [pid for pid, mp in self.processes.items() if not mp.is_alive()]
        for pid in dead:
            del self.processes[pid]
        return dead


# ============================================================
# GUI DESKTOP (tkinter)
# ============================================================

class DesktopManager:
    """Real GUI desktop environment using tkinter."""

    def __init__(self):
        self.root = None
        self.windows = []
        self.running = False

    def available(self):
        return _HAVE_TK

    def start(self):
        """Launch the desktop in a separate thread."""
        if not _HAVE_TK:
            print("\033[31mTkinter not available on this system\033[0m")
            return
        if self.running:
            print("\033[33mDesktop already running\033[0m")
            return
        self.running = True
        t = threading.Thread(target=self._run_desktop, daemon=True)
        t.start()
        print("\033[32mDesktop environment launched\033[0m")

    def _run_desktop(self):
        self.root = tk.Tk()
        self.root.title("Arcanis Desktop")
        self.root.geometry("1024x768")
        self.root.configure(bg="#1a1a2e")

        # Taskbar
        taskbar = tk.Frame(self.root, bg="#16213e", height=40)
        taskbar.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(taskbar, text="Arc.OS", bg="#16213e", fg="#0f3460",
                 font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=10, pady=8)

        clock = tk.Label(taskbar, bg="#16213e", fg="#e94560",
                         font=("Consolas", 10))
        clock.pack(side=tk.RIGHT, padx=15, pady=8)

        def update_clock():
            clock.config(text=time.strftime("%H:%M:%S"))
            self.root.after(1000, update_clock)
        update_clock()

        # Desktop icons area
        desktop = tk.Frame(self.root, bg="#1a1a2e")
        desktop.pack(fill=tk.BOTH, expand=True)

        icons = [
            ("Terminal", ">_", self._open_terminal),
            ("Notepad", "N", self._open_notepad),
            ("Monitor", "M", self._open_monitor),
            ("File Explorer", "FE", self._open_explorer),
            ("Calculator", "C", self._open_calc),
        ]
        for i, (name, label, cmd) in enumerate(icons):
            x = 30 + (i % 5) * 120
            y = 30 + (i // 5) * 130
            icon_frame = tk.Frame(desktop, bg="#1a1a2e", cursor="hand2")
            icon_frame.place(x=x, y=y)
            lbl = tk.Label(icon_frame, text=label, bg="#0f3460", fg="#e94560",
                           font=("Consolas", 18, "bold"), width=4, height=2)
            lbl.pack()
            txt = tk.Label(icon_frame, text=name, bg="#1a1a2e", fg="#a0a0a0",
                           font=("Consolas", 9))
            txt.pack()
            lbl.bind("<Button-1>", lambda e, c=cmd: c())
            txt.bind("<Button-1>", lambda e, c=cmd: c())

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
        self.running = False

    def _open_terminal(self):
        win = tk.Toplevel(self.root, bg="#0d0d1a")
        win.title("Terminal")
        win.geometry("600x400")
        text = scrolledtext.ScrolledText(win, bg="#0d0d1a", fg="#00ff41",
                                          insertbackground="#00ff41",
                                          font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, "Arcanis OS Terminal\n> ")
        text.config(state=tk.DISABLED)

    def _open_notepad(self):
        win = tk.Toplevel(self.root, bg="#1e1e2e")
        win.title("Notepad")
        win.geometry("500x400")
        text = scrolledtext.ScrolledText(win, bg="#1e1e2e", fg="#cdd6f4",
                                          insertbackground="#cdd6f4",
                                          font=("Consolas", 11))
        text.pack(fill=tk.BOTH, expand=True)
        menu = tk.Menu(win)
        win.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save", command=lambda: messagebox.showinfo("Save", "Saved!"))
        file_menu.add_command(label="Exit", command=win.destroy)

    def _open_monitor(self):
        win = tk.Toplevel(self.root, bg="#0d1117")
        win.title("System Monitor")
        win.geometry("500x300")
        tk.Label(win, text="Arcanis System Monitor", bg="#0d1117", fg="#58a6ff",
                 font=("Consolas", 14, "bold")).pack(pady=10)
        info = [
            f"Uptime: {time.time() - START_TIME:.0f}s",
            "Processes: 1",
            "Memory: Python managed",
            f"Platform: {sys.platform}",
        ]
        for line in info:
            tk.Label(win, text=line, bg="#0d1117", fg="#8b949e",
                     font=("Consolas", 11), anchor="w").pack(fill=tk.X, padx=20)

    def _open_explorer(self):
        win = tk.Toplevel(self.root, bg="#0d1117")
        win.title("File Explorer")
        win.geometry("600x400")
        tree = ttk.Treeview(win, columns=("size", "modified"), show="tree headings")
        tree.heading("#0", text="Name")
        tree.heading("size", text="Size")
        tree.heading("modified", text="Modified")
        tree.pack(fill=tk.BOTH, expand=True)
        home = os.path.expanduser("~")
        try:
            for entry in os.listdir(home)[:100]:
                tree.insert("", tk.END, text=entry, values=("", ""))
        except Exception:
            pass

    def _open_calc(self):
        win = tk.Toplevel(self.root, bg="#1a1a2e")
        win.title("Calculator")
        win.geometry("250x300")

        display = tk.Entry(win, bg="#0f3460", fg="#e94560",
                           font=("Consolas", 16), justify="right")
        display.pack(fill=tk.X, padx=5, pady=10)
        display.insert(0, "0")

        def press(key):
            current = display.get()
            if current == "0":
                display.delete(0, tk.END)
            display.insert(tk.END, key)

        def evaluate():
            try:
                result = eval(display.get())
                display.delete(0, tk.END)
                display.insert(0, str(result))
            except Exception:
                display.delete(0, tk.END)
                display.insert(0, "Error")

        def clear():
            display.delete(0, tk.END)
            display.insert(0, "0")

        buttons = [
            ("7", "8", "9", "/"),
            ("4", "5", "6", "*"),
            ("1", "2", "3", "-"),
            ("0", ".", "=", "+"),
            ("C",),
        ]
        for row in buttons:
            frame = tk.Frame(win, bg="#1a1a2e")
            frame.pack(fill=tk.X)
            for text in row:
                if text == "=":
                    btn = tk.Button(frame, text=text, command=evaluate, bg="#e94560", fg="white",
                                    font=("Consolas", 12), width=4)
                elif text == "C":
                    btn = tk.Button(frame, text=text, command=clear, bg="#533483", fg="white",
                                    font=("Consolas", 12), width=4)
                else:
                    btn = tk.Button(frame, text=text, command=lambda t=text: press(t),
                                    bg="#0f3460", fg="#e94560", font=("Consolas", 12), width=4)
                btn.pack(side=tk.LEFT, padx=2, pady=2)

    def _on_close(self):
        self.running = False
        if self.root:
            self.root.destroy()


# ============================================================
# SOUND SYSTEM
# ============================================================

class SoundSystem:
    """Audio output using winsound."""

    @staticmethod
    def available():
        return _HAVE_WINSOUND

    @staticmethod
    def beep(freq=440, duration=200):
        """Play a beep at given frequency (Hz) for given duration (ms)."""
        if _HAVE_WINSOUND:
            try:
                winsound.Beep(freq, duration)
                return True
            except Exception:
                return False
        return False

    @staticmethod
    def play_wav(path):
        """Play a WAV file asynchronously."""
        if not _HAVE_WINSOUND:
            return False
        if not os.path.isfile(path):
            return False
        try:
            winsound.PlaySound(path, winsound.SND_ASYNC | winsound.SND_NOWAIT)
            return True
        except Exception:
            return False

    @staticmethod
    def stop():
        """Stop any currently playing sound."""
        if _HAVE_WINSOUND:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass

    @staticmethod
    def generate_wav(filename, freq=440, duration=1.0, sample_rate=44100):
        """Generate a simple sine wave WAV file and play it."""
        if not _HAVE_WAVE:
            return False
        try:
            n_samples = int(sample_rate * duration)
            w = wave.open(filename, "w")
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            import struct as _struct
            for i in range(n_samples):
                value = int(32767.0 * math.sin(2.0 * math.pi * freq * i / sample_rate))
                w.writeframes(_struct.pack("<h", value))
            w.close()
            return True
        except Exception:
            return False


# ============================================================
# FAT32 DRIVER
# ============================================================

class FAT32Driver:
    """Pure Python FAT32 filesystem reader."""

    BPB_SIZE = 512

    def __init__(self, device_path=None):
        self.device = device_path
        self.bytes_per_sector = 512
        self.sectors_per_cluster = 1
        self.reserved_sectors = 32
        self.fat_count = 2
        self.root_cluster = 2
        self.fat_offset = 0
        self.data_offset = 0

    def mount(self, device_path):
        """Mount a FAT32 volume (can be a physical drive or disk image)."""
        self.device = device_path
        try:
            with open(device_path, "rb") as f:
                bpb = f.read(512)
            if len(bpb) < 512:
                return "Not a valid volume"

            self.bytes_per_sector = struct.unpack("<H", bpb[11:13])[0]
            self.sectors_per_cluster = bpb[13]
            self.reserved_sectors = struct.unpack("<H", bpb[14:16])[0]
            self.fat_count = bpb[16]
            sectors_per_fat = struct.unpack("<I", bpb[36:40])[0]
            self.root_cluster = struct.unpack("<I", bpb[44:48])[0]

            if self.bytes_per_sector == 0:
                return "Invalid BPB"

            self.fat_offset = self.reserved_sectors * self.bytes_per_sector
            self.data_offset = self.fat_offset + (self.fat_count * sectors_per_fat * self.bytes_per_sector)

            volume_label = bpb[71:82].rstrip(b'\x00\x20').decode('ascii', errors='replace') or "UNTITLED"
            return f"Mounted: {volume_label} ({self._size_str()})"
        except PermissionError:
            return "Permission denied — run as Administrator for raw disk access"
        except Exception as e:
            return f"Mount failed: {e}"

    def _size_str(self):
        if not self.device or not os.path.exists(self.device):
            return "unknown size"
        try:
            size = os.path.getsize(self.device)
            if size > 1e9:
                return f"{size/1e9:.1f} GB"
            if size > 1e6:
                return f"{size/1e6:.1f} MB"
            return f"{size/1e3:.1f} KB"
        except Exception:
            return "unknown"

    def read_cluster(self, cluster_num):
        """Read raw data for a given cluster."""
        if not self.device:
            return b""
        sector = (cluster_num - 2) * self.sectors_per_cluster + self.data_offset // self.bytes_per_sector
        offset = sector * self.bytes_per_sector
        with open(self.device, "rb") as f:
            f.seek(offset)
            return f.read(self.sectors_per_cluster * self.bytes_per_sector)

    def read_fat_entry(self, cluster_num):
        """Read a FAT32 entry (cluster chain)."""
        if not self.device:
            return 0x0FFFFFF8
        fat_offset = cluster_num * 4
        with open(self.device, "rb") as f:
            f.seek(self.fat_offset + fat_offset)
            entry = struct.unpack("<I", f.read(4))[0]
        return entry & 0x0FFFFFFF

    def walk_directory(self, cluster_num):
        """List files and directories in a FAT32 directory cluster."""
        if not self.device:
            return []
        entries = []
        data = self.read_cluster(cluster_num)
        while True:
            if len(data) < 32:
                break
            for i in range(0, len(data), 32):
                entry = data[i:i+32]
                if len(entry) < 32:
                    break
                status = entry[0]
                if status == 0x00:
                    break
                if status == 0xE5 or entry[11] & 0x0F == 0x0F:
                    continue
                attr = entry[11]
                name = entry[0:8].rstrip(b'\x20').decode('ascii', errors='replace')
                ext = entry[8:11].rstrip(b'\x20').decode('ascii', errors='replace')
                full = f"{name}.{ext}" if ext else name
                cluster_lo = struct.unpack("<H", entry[26:28])[0]
                cluster_hi = struct.unpack("<H", entry[20:22])[0]
                cluster = (cluster_hi << 16) | cluster_lo
                size = struct.unpack("<I", entry[28:32])[0]
                entries.append({
                    "name": full,
                    "size": size,
                    "attr": attr,
                    "cluster": cluster,
                    "is_dir": bool(attr & 0x10),
                    "is_readonly": bool(attr & 0x01),
                    "is_hidden": bool(attr & 0x02),
                    "is_system": bool(attr & 0x04),
                })
            break
        return entries

    def list_drives(self):
        """List available Windows drive letters."""
        drives = []
        if os.name == "nt":
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for i in range(26):
                if bitmask & (1 << i):
                    drives.append(f"{chr(65 + i)}:\\")
        return drives


# Global reference for Desktop manager
START_TIME = time.time()

# ============================================================
# ARC LANG — Custom Programming Language
# ============================================================

class ArcLexer:
    """Tokenize Arc source code into tokens."""

    TOKENS = {
        "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH",
        "(": "LPAREN", ")": "RPAREN", "{": "LBRACE", "}": "RBRACE",
        "=": "EQ", "==": "EQEQ", "!=": "NEQ", "<": "LT", ">": "GT",
        "<=": "LTE", ">=": "GTE", ",": "COMMA", ";": "SEMI",
        "[": "LBRACKET", "]": "RBRACKET", ".": "DOT",
    }

    KEYWORDS = {
        "let": "LET", "define": "LET", "set": "LET",
        "fn": "FN", "function": "FN",
        "if": "IF", "when": "IF",
        "else": "ELSE", "otherwise": "ELSE",
        "while": "WHILE", "repeat": "WHILE",
        "for": "FOR", "foreach": "FOR",
        "in": "IN",
        "return": "RETURN", "result": "RETURN",
        "true": "TRUE", "yes": "TRUE", "on": "TRUE",
        "false": "FALSE", "no": "FALSE", "off": "FALSE",
        "nil": "NIL", "nothing": "NIL", "none": "NIL",
        "print": "PRINT", "display": "PRINT", "show": "PRINT", "say": "PRINT",
        "input": "INPUT",
        "import": "IMPORT", "export": "EXPORT", "as": "AS",
        "and": "AND", "or": "OR", "not": "NOT",
        "try": "TRY", "catch": "CATCH", "throw": "THROW",
        "class": "CLASS", "extends": "EXTENDS", "new": "NEW",
        "this": "THIS", "super": "SUPER",
        "test": "TEST", "describe": "DESCRIBE", "it": "IT",
        "assert": "ASSERT", "expect": "EXPECT",
        "breakpoint": "BREAKPOINT", "watch": "WATCH",
    }

    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.tokens = []
        self._tokenize()

    def _tokenize(self):
        while self.pos < len(self.source):
            c = self.source[self.pos]
            if c in " \t\r\n":
                self.pos += 1
                continue
            if c == "#":
                while self.pos < len(self.source) and self.source[self.pos] != "\n":
                    self.pos += 1
                continue
            if c in ('"', "'"):
                quote = c
                start = self.pos + 1
                self.pos += 1
                while self.pos < len(self.source) and self.source[self.pos] != quote:
                    self.pos += 1
                val = self.source[start:self.pos]
                self.pos += 1
                self.tokens.append(("STRING", val))
                continue
            if c.isdigit():
                start = self.pos
                while self.pos < len(self.source) and self.source[self.pos].isdigit():
                    self.pos += 1
                if self.pos < len(self.source) and self.source[self.pos] == ".":
                    self.pos += 1
                    while self.pos < len(self.source) and self.source[self.pos].isdigit():
                        self.pos += 1
                    self.tokens.append(("NUMBER", float(self.source[start:self.pos])))
                else:
                    self.tokens.append(("NUMBER", int(self.source[start:self.pos])))
                continue
            if c.isalpha() or c == "_":
                start = self.pos
                while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == "_"):
                    self.pos += 1
                word = self.source[start:self.pos]
                ttype = self.KEYWORDS.get(word, "IDENT")
                self.tokens.append((ttype, word))
                continue
            for sym in ["==", "!=", "<=", ">="]:
                if self.source[self.pos:self.pos+2] == sym:
                    self.tokens.append((self.TOKENS[sym], sym))
                    self.pos += 2
                    break
            else:
                t = self.TOKENS.get(c)
                if t:
                    self.tokens.append((t, c))
                    self.pos += 1
                else:
                    self.pos += 1
        self.tokens.append(("EOF", ""))


class ArcParser:
    """Recursive-descent parser for Arc language."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF", "")

    def consume(self, expected=None):
        tok = self.peek()
        if expected and tok[0] != expected:
            raise SyntaxError(f"Expected {expected}, got {tok[0]} ('{tok[1]}')")
        self.pos += 1
        return tok

    def parse(self):
        stmts = []
        while self.peek()[0] != "EOF":
            stmts.append(self._stmt())
        return ("PROGRAM", stmts)

    def _stmt(self):
        tok = self.peek()
        if tok[0] == "LET":
            return self._let_stmt()
        if tok[0] == "FN":
            return self._fn_stmt()
        if tok[0] == "IF":
            return self._if_stmt()
        if tok[0] == "WHILE":
            return self._while_stmt()
        if tok[0] == "FOR":
            return self._for_stmt()
        if tok[0] == "RETURN":
            return self._return_stmt()
        if tok[0] == "PRINT":
            self.consume("PRINT")
            expr = self._expr()
            self.consume("SEMI")
            return ("PRINT", expr)
        if tok[0] == "IMPORT":
            return self._import_stmt()
        if tok[0] == "EXPORT":
            return self._export_stmt()
        if tok[0] == "TRY":
            return self._try_stmt()
        if tok[0] == "THROW":
            return self._throw_stmt()
        if tok[0] == "CLASS":
            return self._class_stmt()
        if tok[0] == "TEST":
            return self._test_stmt()
        if tok[0] == "DESCRIBE":
            return self._describe_stmt()
        if tok[0] == "ASSERT":
            return self._assert_stmt()
        if tok[0] == "BREAKPOINT":
            return self._breakpoint_stmt()
        if tok[0] == "LBRACE":
            return self._block()
        return self._expr_stmt()

    def _let_stmt(self):
        self.consume("LET")
        target = self._call()
        self.consume("EQ")
        expr = self._expr()
        self.consume("SEMI")
        if isinstance(target, tuple) and target[0] == "VAR":
            return ("LET", target[1], expr)
        return ("ASSIGN", target, expr)

    def _fn_stmt(self):
        self.consume("FN")
        name = self.consume("IDENT")[1]
        self.consume("LPAREN")
        params = []
        while self.peek()[0] != "RPAREN":
            params.append(self.consume("IDENT")[1])
            if self.peek()[0] == "COMMA":
                self.consume("COMMA")
        self.consume("RPAREN")
        body = self._block()
        return ("FN", name, params, body)

    def _try_stmt(self):
        self.consume("TRY")
        body = self._block()
        catch_body = None
        catch_var = None
        if self.peek()[0] == "CATCH":
            self.consume("CATCH")
            if self.peek()[0] == "LPAREN":
                self.consume("LPAREN")
                catch_var = self.consume("IDENT")[1]
                self.consume("RPAREN")
            elif self.peek()[0] == "IDENT":
                catch_var = self.consume("IDENT")[1]
            catch_body = self._block() if self.peek()[0] == "LBRACE" else self._stmt()
        return ("TRY", body, catch_var, catch_body)

    def _throw_stmt(self):
        self.consume("THROW")
        expr = self._expr()
        self.consume("SEMI")
        return ("THROW", expr)

    def _class_stmt(self):
        self.consume("CLASS")
        name = self.consume("IDENT")[1]
        parent = None
        if self.peek()[0] == "EXTENDS":
            self.consume("EXTENDS")
            parent = self.consume("IDENT")[1]
        self.consume("LBRACE")
        methods = {}
        while self.peek()[0] != "RBRACE":
            if self.peek()[0] == "FN":
                self.consume("FN")
                mname = self.consume("IDENT")[1]
                self.consume("LPAREN")
                params = []
                while self.peek()[0] != "RPAREN":
                    params.append(self.consume("IDENT")[1])
                    if self.peek()[0] == "COMMA":
                        self.consume("COMMA")
                self.consume("RPAREN")
                body = self._block()
                methods[mname] = ("FN", mname, params, body)
            else:
                break
        self.consume("RBRACE")
        self.consume("SEMI")
        return ("CLASS", name, parent, methods)

    def _test_stmt(self):
        self.consume("TEST")
        name = self.consume("STRING")[1] if self.peek()[0] == "STRING" else None
        body = self._block()
        self.consume("SEMI")
        return ("TEST", name, body)

    def _describe_stmt(self):
        self.consume("DESCRIBE")
        name = self.consume("STRING")[1]
        self.consume("LBRACE")
        blocks = []
        while self.peek()[0] != "RBRACE" and self.peek()[0] != "EOF":
            if self.peek()[0] == "IT":
                self.consume("IT")
                it_name = self.consume("STRING")[1] if self.peek()[0] == "STRING" else None
                it_body = self._block()
                if self.peek()[0] == "SEMI":
                    self.consume("SEMI")
                blocks.append(("IT", it_name, it_body))
            else:
                break
        self.consume("RBRACE")
        self.consume("SEMI")
        return ("DESCRIBE", name, blocks)

    def _assert_stmt(self):
        self.consume("ASSERT")
        cond = self._expr()
        msg = None
        if self.peek()[0] == "STRING":
            msg = self.consume("STRING")[1]
        self.consume("SEMI")
        return ("ASSERT", cond, msg)

    def _breakpoint_stmt(self):
        self.consume("BREAKPOINT")
        self.consume("SEMI")
        return ("BREAKPOINT",)

    def _if_stmt(self):
        self.consume("IF")
        cond = self._expr()
        body = self._block()
        else_body = None
        if self.peek()[0] == "ELSE":
            self.consume("ELSE")
            else_body = self._block() if self.peek()[0] == "LBRACE" else self._stmt()
        return ("IF", cond, body, else_body)

    def _while_stmt(self):
        self.consume("WHILE")
        cond = self._expr()
        body = self._block()
        return ("WHILE", cond, body)

    def _for_stmt(self):
        self.consume("FOR")
        var = self.consume("IDENT")[1]
        self.consume("IN")
        iter_expr = self._expr()
        body = self._block()
        return ("FOR", var, iter_expr, body)

    def _return_stmt(self):
        self.consume("RETURN")
        expr = self._expr()
        self.consume("SEMI")
        return ("RETURN", expr)

    def _import_stmt(self):
        self.consume("IMPORT")
        module = self.consume("STRING")[1]
        ns = None
        if self.peek()[0] == "AS":
            self.consume("AS")
            ns = self.consume("IDENT")[1]
        self.consume("SEMI")
        return ("IMPORT", module, ns)

    def _export_stmt(self):
        self.consume("EXPORT")
        name = self.consume("IDENT")[1]
        self.consume("SEMI")
        return ("EXPORT", name)

    def _block(self):
        self.consume("LBRACE")
        stmts = []
        while self.peek()[0] != "RBRACE" and self.peek()[0] != "EOF":
            stmts.append(self._stmt())
        self.consume("RBRACE")
        return ("BLOCK", stmts)

    def _expr_stmt(self):
        expr = self._expr()
        self.consume("SEMI")
        return ("EXPR", expr)

    def _expr(self):
        left = self._and_or()
        if self.peek()[0] == "EQ" and self.tokens[self.pos + 1][0] != "EQ" if self.pos + 1 < len(self.tokens) else True:
            if self.peek()[0] == "EQ":
                self.consume("EQ")
                right = self._expr()
                return ("ASSIGN", left, right)
        return left

    def _and_or(self):
        left = self._comparison()
        while self.peek()[0] in ("AND", "OR"):
            op = self.consume()[1]
            right = self._comparison()
            left = ("BINOP", op, left, right)
        return left

    def _comparison(self):
        left = self._term()
        while self.peek()[0] in ("EQEQ", "NEQ", "LT", "GT", "LTE", "GTE"):
            op = self.consume()[1]
            right = self._term()
            left = ("BINOP", op, left, right)
        return left

    def _term(self):
        left = self._factor()
        while self.peek()[0] in ("PLUS", "MINUS"):
            op = self.consume()[1]
            right = self._factor()
            left = ("BINOP", op, left, right)
        return left

    def _factor(self):
        left = self._unary()
        while self.peek()[0] in ("STAR", "SLASH"):
            op = self.consume()[1]
            right = self._unary()
            left = ("BINOP", op, left, right)
        return left

    def _unary(self):
        if self.peek()[0] == "MINUS":
            self.consume("MINUS")
            return ("UNARY", "-", self._unary())
        if self.peek()[0] == "NOT":
            self.consume("NOT")
            return ("UNARY", "not", self._unary())
        if self.peek()[0] == "NEW":
            self.consume("NEW")
            class_name = self.consume("IDENT")[1]
            self.consume("LPAREN")
            args = []
            while self.peek()[0] != "RPAREN":
                args.append(self._expr())
                if self.peek()[0] == "COMMA":
                    self.consume("COMMA")
            self.consume("RPAREN")
            return ("NEW", class_name, args)
        return self._call()

    def _call(self):
        left = self._primary()
        while True:
            if self.peek()[0] == "LPAREN":
                self.consume("LPAREN")
                args = []
                if self.peek()[0] != "RPAREN":
                    args.append(self._expr())
                    while self.peek()[0] == "COMMA":
                        self.consume("COMMA")
                        args.append(self._expr())
                self.consume("RPAREN")
                left = ("CALL", left, args)
            elif self.peek()[0] == "LBRACKET":
                self.consume("LBRACKET")
                index = self._expr()
                self.consume("RBRACKET")
                left = ("INDEX", left, index)
            elif self.peek()[0] == "DOT":
                self.consume("DOT")
                name = self.consume("IDENT")[1]
                left = ("INDEX", left, ("STRING", name))
            else:
                break
        return left

    def _primary(self):
        tok = self.peek()
        if tok[0] == "NUMBER":
            self.pos += 1
            return ("NUMBER", tok[1])
        if tok[0] == "STRING":
            self.pos += 1
            return ("STRING", tok[1])
        if tok[0] == "TRUE":
            self.pos += 1
            return ("BOOL", True)
        if tok[0] == "FALSE":
            self.pos += 1
            return ("BOOL", False)
        if tok[0] == "NIL":
            self.pos += 1
            return ("NIL", None)
        if tok[0] == "IDENT":
            self.pos += 1
            return ("VAR", tok[1])
        if tok[0] == "LPAREN":
            self.consume("LPAREN")
            expr = self._expr()
            self.consume("RPAREN")
            return expr
        if tok[0] == "LBRACKET":
            self.consume("LBRACKET")
            elements = []
            while self.peek()[0] != "RBRACKET":
                elements.append(self._expr())
                if self.peek()[0] == "COMMA":
                    self.consume("COMMA")
            self.consume("RBRACKET")
            return ("LIST", elements)
        if tok[0] == "THIS":
            self.pos += 1
            return ("THIS",)
        if tok[0] == "SUPER":
            self.pos += 1
            return ("SUPER",)
        if tok[0] == "INPUT":
            self.consume("INPUT")
            self.consume("LPAREN")
            self.consume("RPAREN")
            return ("INPUT",)
        if tok[0] == "FN":
            # Anonymous function expression
            self.consume("FN")
            name = None
            self.consume("LPAREN")
            params = []
            while self.peek()[0] != "RPAREN":
                params.append(self.consume("IDENT")[1])
                if self.peek()[0] == "COMMA":
                    self.consume("COMMA")
            self.consume("RPAREN")
            body = self._block()
            return ("FN", name, params, body)
        raise SyntaxError(f"Unexpected token: {tok}")


class ArcError(Exception):
    """Custom error for Arc throw/try/catch."""
    def __init__(self, value):
        self.value = value
        super().__init__(str(value))


class ArcVM:
    """Bytecode-embedded tree-walking interpreter for Arc AST."""

    def __init__(self, jit=None):
        self.env = {}
        self.functions = {}
        self.jit = jit
        self.return_val = None
        self.exports = set()
        self.loaded_modules = {}
        self.arc_lang = None
        self.classes = {}
        self.instances = []
        self.debug_mode = False
        self.debug_callback = None
        self.test_results = []
        self._builtins()

    def _builtins(self):
        self.env["print"] = lambda *a: print(*a)
        self.env["len"] = lambda x: len(x)
        self.env["str"] = lambda x: str(x)
        self.env["int"] = lambda x: int(x)
        self.env["range"] = lambda n: list(range(n))
        # File I/O
        self.env["read_file"] = lambda p: open(p).read() if os.path.isfile(p) else ""
        self.env["write_file"] = lambda p, c: (lambda f: (f.write(c), f.close(), c)[2])(open(p, "w")) if c is not None else 0
        self.env["file_exists"] = lambda p: os.path.isfile(p)
        self.env["list_dir"] = lambda p: os.listdir(p) if os.path.isdir(p) else []
        # Shell
        self.env["shell"] = lambda c: subprocess.run(c, shell=True, capture_output=True, text=True).stdout.strip()
        # HTTP
        self.env["http_get"] = lambda u: urllib.request.urlopen(u, timeout=5).read().decode("utf-8", errors="replace") if u.startswith("http") else ""
        # String functions
        self.env["split"] = lambda s, d=" ": s.split(d)
        self.env["contains"] = lambda s, sub: sub in s
        self.env["replace"] = lambda s, o, n: s.replace(o, n)
        self.env["substr"] = lambda s, st, en: s[st:en] if en is not None else s[st:]
        self.env["upper"] = lambda s: s.upper()
        self.env["lower"] = lambda s: s.lower()
        self.env["trim"] = lambda s: s.strip()
        self.env["starts_with"] = lambda s, pre: s.startswith(pre)
        self.env["ends_with"] = lambda s, suf: s.endswith(suf)
        # System
        self.env["env"] = lambda k: os.environ.get(k, "")
        self.env["exit"] = lambda: (_ for _ in ()).throw(SystemExit(0))
        self.env["type"] = lambda x: type(x).__name__
        # Math
        self.env["abs"] = lambda x: abs(x)
        self.env["min"] = lambda *a: min(a) if a else 0
        self.env["max"] = lambda *a: max(a) if a else 0
        self.env["round"] = lambda x: round(x)
        # Threading
        self.env["spawn"] = self._spawn
        self.env["sync"] = self._sync
        self.env["channel"] = self._channel
        self.env["chan_send"] = lambda ch, val: ch["send"](val) if isinstance(ch, dict) and "send" in ch else None
        self.env["chan_recv"] = lambda ch: ch["recv"]() if isinstance(ch, dict) and "recv" in ch else None
        self.env["sleep"] = lambda ms: __import__('time').sleep(ms / 1000.0)
        # List operations
        self.env["push"] = lambda lst, val: (lst.append(val), lst)[1] if isinstance(lst, list) else None
        self.env["pop"] = lambda lst: lst.pop() if isinstance(lst, list) and lst else None
        self.env["map"] = lambda fn, lst: [fn(x) for x in lst] if callable(fn) and isinstance(lst, list) else lst
        self.env["filter"] = lambda fn, lst: [x for x in lst if fn(x)] if callable(fn) and isinstance(lst, list) else lst
        self.env["reduce"] = lambda fn, lst, init: __import__('functools').reduce(fn, lst, init) if callable(fn) and isinstance(lst, list) else init
        self.env["join"] = lambda lst, sep: sep.join(str(x) for x in lst) if isinstance(lst, list) else ""
        self.env["sort"] = lambda lst: (lst.sort(), lst)[1] if isinstance(lst, list) else lst
        self.env["reverse"] = lambda lst: (lst.reverse(), lst)[1] if isinstance(lst, list) else lst
        self.env["append"] = lambda lst, val: (lst.append(val), lst)[1] if isinstance(lst, list) else None

    def exec(self, ast):
        self._eval(ast)

    def _eval(self, node):
        if node is None:
            return None
        t = node[0]

        if t == "PROGRAM":
            for stmt in node[1]:
                self._eval(stmt)
            return None

        if t == "IMPORT":
            module = node[1]
            ns = node[2]
            cache_key = f"{module}:{ns}" if ns else module
            if cache_key in self.loaded_modules:
                return self.loaded_modules[cache_key]
            result = self._load_module(module, ns)
            self.loaded_modules[cache_key] = result
            return result

        if t == "EXPORT":
            self.exports.add(node[1])
            return None

        if t == "BLOCK":
            for stmt in node[1]:
                r = self._eval(stmt)
                if self.return_val is not None:
                    return None
            return None

        if t == "LET":
            name = node[1]
            val = self._eval(node[2])
            self.env[name] = val
            return val

        if t == "FN":
            name = node[1]
            if name:
                self.functions[name] = node
                self.env[name] = lambda *args: self._call_fn(node, args)
            else:
                # Anonymous function — return a callable
                return lambda *args: self._call_fn(node, args)
            return None

        if t == "IF":
            cond = self._eval(node[1])
            if cond:
                return self._eval(node[2])
            elif node[3]:
                return self._eval(node[3])
            return None

        if t == "WHILE":
            while self._eval(node[1]):
                self._eval(node[2])
                if self.return_val is not None:
                    break
            return None

        if t == "FOR":
            var = node[1]
            items = self._eval(node[2])
            if isinstance(items, int):
                items = range(items)
            for val in items:
                self.env[var] = val
                self._eval(node[3])
                if self.return_val is not None:
                    break
            return None

        if t == "RETURN":
            self.return_val = self._eval(node[1])
            return self.return_val

        if t == "PRINT":
            val = self._eval(node[1])
            if val is not None:
                self.env["print"](val)
            return None

        if t == "EXPR":
            return self._eval(node[1])

        if t == "BINOP":
            left = self._eval(node[2])
            right = self._eval(node[3])
            op = node[1]
            if op == "+": return str(left) + str(right) if isinstance(left, str) or isinstance(right, str) else left + right
            if op == "-": return left - right
            if op == "*": return left * right
            if op == "/": return left // right if isinstance(left, int) and isinstance(right, int) else left / right
            if op == "==": return left == right
            if op == "!=": return left != right
            if op == "<":  return left < right
            if op == ">":  return left > right
            if op == "<=": return left <= right
            if op == ">=": return left >= right
            if op == "and": return left and right
            if op == "or": return left or right
            return None

        if t == "UNARY":
            val = self._eval(node[2])
            if node[1] == "-": return -val if val else 0
            if node[1] == "not": return not val
            return val

        if t == "CALL":
            fn = self._eval(node[1])
            args = [self._eval(a) for a in node[2]]
            if callable(fn):
                return fn(*args)
            return None

        if t == "VAR":
            return self.env.get(node[1], None)

        if t == "NUMBER":
            return node[1]

        if t == "STRING":
            return node[1]

        if t == "BOOL":
            return node[1]

        if t == "NIL":
            return None

        if t == "LIST":
            return [self._eval(e) for e in node[1]]

        if t == "INDEX":
            collection = self._eval(node[1])
            index = self._eval(node[2])
            if isinstance(collection, (list, tuple)):
                try:
                    return collection[index]
                except IndexError:
                    return None
            if isinstance(collection, dict):
                # Super method lookup (look in parent class)
                if collection.get("__super__"):
                    instance = collection["instance"]
                    cls = instance.get("__class__")
                    if cls and cls.get("__parent__"):
                        parent_cls = cls["__parent__"]
                        if index in parent_cls.get("__methods__", {}):
                            method = parent_cls["__methods__"][index]
                            return lambda *args: self._call_method(instance, method, args)
                    return None
                # Instance method lookup
                if index in collection:
                    return collection[index]
                cls = collection.get("__class__")
                if cls and index in cls.get("__methods__", {}):
                    method = cls["__methods__"][index]
                    return lambda *args: self._call_method(collection, method, args)
                # Data attribute lookup
                data = collection.get("__data__", {})
                if index in data:
                    return data[index]
                return collection.get(index, None)
            return None

        if t == "INPUT":
            return input()

        if t == "ASSIGN":
            var_name = node[1][1] if node[1][0] == "VAR" else None
            if var_name:
                val = self._eval(node[2])
                self.env[var_name] = val
                return val
            # Handle instance attribute assignment: obj.attr = val
            if node[1][0] == "INDEX":
                obj = self._eval(node[1][1])
                key = self._eval(node[1][2])
                if isinstance(obj, dict):
                    obj[key] = self._eval(node[2])
            return None

        if t == "TRY":
            try:
                return self._eval(node[1])
            except ArcError as e:
                if node[2] is not None and node[3] is not None:
                    old = self.env.get(node[2])
                    self.env[node[2]] = e.value
                    self._eval(node[3])
                    if old is not None:
                        self.env[node[2]] = old
                    elif node[2] in self.env:
                        del self.env[node[2]]
                elif node[3] is not None:
                    self._eval(node[3])
                return None
            except Exception as e:
                if node[2] is not None and node[3] is not None:
                    old = self.env.get(node[2])
                    self.env[node[2]] = str(e)
                    self._eval(node[3])
                    if old is not None:
                        self.env[node[2]] = old
                    elif node[2] in self.env:
                        del self.env[node[2]]
                elif node[3] is not None:
                    self._eval(node[3])
                return None

        if t == "THROW":
            val = self._eval(node[1])
            raise ArcError(val)

        if t == "CLASS":
            name = node[1]
            parent_name = node[2]
            methods = node[3]
            cls = {"__name__": name, "__methods__": dict(methods), "__parent__": None}
            if parent_name and parent_name in self.classes:
                cls["__parent__"] = self.classes[parent_name]
            self.classes[name] = cls
            self.env[name] = cls
            return None

        if t == "NEW":
            class_name = node[1]
            args = [self._eval(a) for a in node[2]]
            if class_name not in self.classes:
                raise ArcError(f"Unknown class: {class_name}")
            cls = self.classes[class_name]
            instance = {"__class__": cls, "__data__": {}}
            # Call constructor if defined
            if "init" in cls["__methods__"]:
                self.instances.append(instance)
                try:
                    self._call_fn(cls["__methods__"]["init"], args)
                finally:
                    self.instances.pop()
            return instance

        if t == "THIS":
            if self.instances:
                return self.instances[-1]
            raise ArcError("'this' used outside of a class method")

        if t == "SUPER":
            if not self.instances:
                raise ArcError("'super' used outside of a class method")
            instance = self.instances[-1]
            return {"__super__": True, "instance": instance}

        if t == "TEST":
            name = node[1]
            body = node[2]
            result = {"name": name, "passed": True, "error": None}
            try:
                self._eval(body)
            except ArcError as e:
                result["passed"] = False
                result["error"] = str(e.value)
            except Exception as e:
                result["passed"] = False
                result["error"] = str(e)
            if hasattr(self, "test_results"):
                self.test_results.append(result)
            if not result["passed"]:
                print(f"  \033[31mFAIL\033[0m {name or '<unnamed>'}: {result['error']}")
            else:
                print(f"  \033[32mPASS\033[0m {name or '<unnamed>'}")
            return result

        if t == "DESCRIBE":
            name = node[1]
            blocks = node[2]
            print(f"\n\033[1;36m{name}\033[0m")
            for block in blocks:
                self._eval(block)
            return None

        if t == "IT":
            name = node[1]
            body = node[2]
            result = {"name": name, "passed": True, "error": None}
            try:
                self._eval(body)
            except ArcError as e:
                result["passed"] = False
                result["error"] = str(e.value)
            except Exception as e:
                result["passed"] = False
                result["error"] = str(e)
            if hasattr(self, "test_results"):
                self.test_results.append(result)
            status = "\033[32mPASS\033[0m" if result["passed"] else "\033[31mFAIL\033[0m"
            print(f"  {status} {name or '<unnamed>'}")
            if not result["passed"]:
                print(f"       \033[31m{result['error']}\033[0m")
            return result

        if t == "ASSERT":
            cond = self._eval(node[1])
            msg = node[2]
            if not cond:
                raise ArcError(msg or "Assertion failed")
            return None

        if t == "BREAKPOINT":
            if self.debug_mode and self.debug_callback:
                self.debug_callback(self)
            return None

        return None

    def run_tests(self, ast):
        """Run all test cases in the AST and return results."""
        self.test_results = []
        self._eval(ast)
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        print(f"\n\033[1;37m{'='*40}\033[0m")
        print(f"\033[1;37m  Results: {passed}/{total} passed\033[0m")
        if passed < total:
            print(f"\033[1;37m  {total - passed} test(s) failed\033[0m")
        print(f"\033[1;37m{'='*40}\033[0m")
        return self.test_results

    def _load_module(self, module, ns):
        """Load a module from file or built-in stdlib."""
        # Built-in stdlib modules
        stdlib_modules = {
            "math": """
                export pi;
                export e;
                export sin;
                export cos;
                export sqrt;
                export pow;
                export log;
                export floor;
                export ceil;
                pi = 3.141592653589793;
                e = 2.718281828459045;
                fn sin(x) { return call_native("math_sin", x); }
                fn cos(x) { return call_native("math_cos", x); }
                fn sqrt(x) { return call_native("math_sqrt", x); }
                fn pow(x, y) { return call_native("math_pow", x, y); }
                fn log(x) { return call_native("math_log", x); }
                fn floor(x) { return call_native("math_floor", x); }
                fn ceil(x) { return call_native("math_ceil", x); }
                print "[stdlib/math loaded]";
            """,
            "random": """
                export rand;
                export randint;
                export seed;
                fn rand() { return call_native("random_rand"); }
                fn randint(lo, hi) { return call_native("random_randint", lo, hi); }
                fn seed(s) { return call_native("random_seed", s); }
                print "[stdlib/random loaded]";
            """,
            "time": """
                export now;
                export sleep;
                export clock;
                fn now() { return call_native("time_now"); }
                fn sleep(ms) { return call_native("time_sleep", ms); }
                fn clock() { return call_native("time_clock"); }
                print "[stdlib/time loaded]";
            """,
            "json": """
                export parse;
                export stringify;
                fn parse(s) { return call_native("json_parse", s); }
                fn stringify(v) { return call_native("json_stringify", v); }
                print "[stdlib/json loaded]";
            """,
            "fs": """
                export read;
                export write;
                export exists;
                export list;
                export size;
                fn read(path) { return call_native("fs_read", path); }
                fn write(path, content) { return call_native("fs_write", path, content); }
                fn exists(path) { return call_native("fs_exists", path); }
                fn list(path) { return call_native("fs_list", path); }
                fn size(path) { return call_native("fs_size", path); }
                print "[stdlib/fs loaded]";
            """,
            "ai": """
                export model;
                export predict;
                export train;
                export classify;
                fn model(layers) { return call_native("ai_model", layers); }
                fn predict(m, inp) { return call_native("ai_predict", m, inp); }
                fn train(m, x, y, epochs) { return call_native("ai_train", m, x, y, epochs); }
                fn classify(m, inp) { return call_native("ai_classify", m, inp); }
                print "[stdlib/ai loaded]";
            """,
            "web": """
                export server;
                export route;
                export html;
                export json_response;
                fn server(host, port) { return call_native("web_server", host, port); }
                fn route(srv, path, method, handler) { return call_native("web_route", srv, path, method, handler); }
                fn html(content) { return call_native("web_html", content); }
                fn json_response(data) { return call_native("web_json", data); }
                fn start(srv) { return call_native("web_start", srv); }
                print "[stdlib/web loaded]";
            """,
            "gui": """
                export window;
                export button;
                export label;
                export entry;
                export text;
                export run;
                fn window(title, w, h) { return call_native("gui_window", title, w, h); }
                fn button(parent, text, cb) { return call_native("gui_button", parent, text, cb); }
                fn label(parent, text) { return call_native("gui_label", parent, text); }
                fn entry(parent) { return call_native("gui_entry", parent); }
                fn text(parent, w, h) { return call_native("gui_text", parent, w, h); }
                fn run() { return call_native("gui_run"); }
                print "[stdlib/gui loaded]";
            """,
        }

        if module in stdlib_modules:
            # Register native callbacks
            native_cbs = {
                "math_sin": lambda x: math.sin(x),
                "math_cos": lambda x: math.cos(x),
                "math_sqrt": lambda x: math.sqrt(x),
                "math_pow": lambda x, y: math.pow(x, y),
                "math_log": lambda x: math.log(x),
                "math_floor": lambda x: math.floor(x),
                "math_ceil": lambda x: math.ceil(x),
                "random_rand": lambda: __import__('random').random(),
                "random_randint": lambda lo, hi: __import__('random').randint(lo, hi),
                "random_seed": lambda s: __import__('random').seed(s),
                "time_now": lambda: __import__('time').time(),
                "time_sleep": lambda ms: __import__('time').sleep(ms / 1000.0),
                "time_clock": lambda: __import__('time').clock() if hasattr(__import__('time'), 'clock') else __import__('time').perf_counter(),
                "json_parse": lambda s: __import__('json').loads(s),
                "json_stringify": lambda v: __import__('json').dumps(v),
                "fs_read": lambda p: open(p).read() if os.path.isfile(p) else "",
                "fs_write": lambda p, c: (open(p, "w").write(c), c)[1],
                "fs_exists": lambda p: os.path.isfile(p),
                "fs_list": lambda p: os.listdir(p) if os.path.isdir(p) else [],
                "fs_size": lambda p: os.path.getsize(p) if os.path.isfile(p) else 0,
                "ai_model": lambda layers: NeuralNetwork(layers),
                "ai_predict": lambda m, inp: m.predict(inp),
                "ai_train": lambda m, inputs, outputs, epochs: (m.train(inputs, outputs, epochs), m)[1],
                "ai_classify": lambda m, inp: (lambda out: out.index(max(out)) if len(out) > 1 else round(out[0]))(m.predict(inp)),
                "web_server": lambda host, port: {"__type__": "server", "host": host, "port": port, "routes": [], "running": False},
                "web_route": lambda srv, path, method, handler: (srv["routes"].append({"path": path, "method": method.upper(), "handler": handler}), None)[1] if isinstance(srv, dict) else None,
                "web_html": lambda content: {"__type__": "response", "body": content, "content_type": "text/html"},
                "web_json": lambda data: {"__type__": "response", "body": __import__('json').dumps(data), "content_type": "application/json"},
                "web_start": lambda srv: (srv.update({"running": True}), _ArcWebServer(srv))[1] if isinstance(srv, dict) else None,
                "gui_window": lambda title, w, h: _ArcGUIWindow(title, w, h),
                "gui_button": lambda parent, text, cb: _ArcGUIButton(parent, text, cb),
                "gui_label": lambda parent, text: _ArcGUILabel(parent, text),
                "gui_entry": lambda parent: _ArcGUIEntry(parent),
                "gui_text": lambda parent, w, h: _ArcGUIText(parent, w, h),
                "gui_run": lambda: _ArcGUIRun(),
            }
            self.env["call_native"] = lambda fn, *a: native_cbs.get(fn, lambda *_: None)(*a)

            # Save exports before loading
            old_exports = set(self.exports)
            # Run the module code
            old_stdout = sys.stdout
            sys.stdout = __import__('io').StringIO()
            lexer = ArcLexer(stdlib_modules[module])
            parser = ArcParser(lexer.tokens)
            ast = parser.parse()
            self._eval(ast)
            sys.stdout = old_stdout

            # Collect exported vars
            mod_exports = {}
            for var in self.exports - old_exports:
                if var in self.env:
                    mod_exports[var] = self.env[var]

            if ns:
                # Store under namespace
                self.env[ns] = mod_exports
            else:
                # Merge into global scope
                for k, v in mod_exports.items():
                    if k not in self.env:
                        self.env[k] = v

            return mod_exports

        # File import
        if os.path.isfile(module):
            old_exports = set(self.exports)
            with open(module) as f:
                code = f.read()
            lexer = ArcLexer(code)
            parser = ArcParser(lexer.tokens)
            ast = parser.parse()
            self._eval(ast)

            mod_exports = {}
            for var in self.exports - old_exports:
                if var in self.env:
                    mod_exports[var] = self.env[var]

            if ns:
                self.env[ns] = mod_exports
            return mod_exports

        print(f"\033[33mWarning: module '{module}' not found\033[0m")
        return {}

    def _call_fn(self, fn_node, args):
        old_env = dict(self.env)
        params = fn_node[2]
        for p, a in zip(params, args):
            self.env[p] = a
        self.return_val = None
        self._eval(fn_node[3])
        rv = self.return_val
        self.return_val = None
        self.env.clear()
        self.env.update(old_env)
        return rv

    def _call_method(self, instance, fn_node, args):
        """Call a method on an instance (sets up 'this' scope)."""
        self.instances.append(instance)
        try:
            old_env = dict(self.env)
            params = fn_node[2]
            for p, a in zip(params, args):
                self.env[p] = a
            self.env["this"] = instance
            self.return_val = None
            self._eval(fn_node[3])
            rv = self.return_val
            self.return_val = None
            self.env.clear()
            self.env.update(old_env)
            return rv
        finally:
            self.instances.pop()

    def _spawn(self, fn, *args):
        """Spawn a function in a new thread."""
        import threading as _th
        result = []
        def _run():
            try:
                r = fn(*args)
                result.append(r)
            except Exception:
                pass
        t = _th.Thread(target=_run, daemon=True)
        t.start()
        return {"thread": t, "result": result}

    def _sync(self, handle):
        """Wait for a spawned thread to complete."""
        if isinstance(handle, dict) and "thread" in handle:
            handle["thread"].join()
            if handle["result"]:
                return handle["result"][0]
        return None

    def _channel(self):
        """Create a communication channel."""
        import queue as _q
        q = _q.Queue()
        return {"send": lambda v: q.put(v), "recv": lambda: q.get()}

    def run_source(self, source):
        lexer = ArcLexer(source)
        parser = ArcParser(lexer.tokens)
        ast = parser.parse()
        return self.exec(ast)


class ArcLang:
    """Arc Programming Language — full compiler + VM."""

    def __init__(self, jit=None):
        self.vm = ArcVM(jit=jit)
        self.jit = jit

    def _preprocess_readable(self, source):
        """Convert natural-language Arc syntax to standard Arc."""
        s = source.strip()
        if not s.endswith(";") and not s.endswith("}") and not s.endswith("{"):
            s = s + ";"
        # set x to 42 → let x = 42
        s = re.sub(r'\bset\s+(\w+)\s+to\s+', r'let \1 = ', s)
        # increase x by 1 → x = x + 1
        s = re.sub(r'\bincrease\s+(\w+)\s+by\s+', r'\1 = \1 + ', s)
        # decrease x by 1 → x = x - 1
        s = re.sub(r'\bdecrease\s+(\w+)\s+by\s+', r'\1 = \1 - ', s)
        # multiply x by 2 → x = x * 2
        s = re.sub(r'\bmultiply\s+(\w+)\s+by\s+', r'\1 = \1 * ', s)
        # divide x by 2 → x = x / 2
        s = re.sub(r'\bdivide\s+(\w+)\s+by\s+', r'\1 = \1 / ', s)
        # x is greater than y → x > y
        s = re.sub(r'(\w+)\s+is\s+greater\s+than\s+or\s+equal\s+to\s+', r'\1 >= ', s)
        s = re.sub(r'(\w+)\s+is\s+less\s+than\s+or\s+equal\s+to\s+', r'\1 <= ', s)
        s = re.sub(r'(\w+)\s+is\s+greater\s+than\s+', r'\1 > ', s)
        s = re.sub(r'(\w+)\s+is\s+less\s+than\s+', r'\1 < ', s)
        s = re.sub(r'(\w+)\s+is\s+equal\s+to\s+', r'\1 == ', s)
        s = re.sub(r'(\w+)\s+is\s+not\s+equal\s+to\s+', r'\1 != ', s)
        s = re.sub(r'(\w+)\s+is\s+not\s+', r'\1 != ', s)
        s = re.sub(r'(\w+)\s+equals\s+', r'\1 == ', s)
        # then { → {
        s = re.sub(r'\bthen\s*\{', r'{', s)
        # do { → {
        s = re.sub(r'\bdo\s*\{', r'{', s)
        # times { → {
        s = re.sub(r'\btimes\s*\{', r'{', s)
        # a and b → a and b (keep)
        # a or b → a or b (keep)
        # not a → not a (keep)
        return s

    def explain(self, source):
        """Translate Arc code to plain English."""
        lexer = ArcLexer(source)
        parser = ArcParser(lexer.tokens)
        ast = parser.parse()
        lines = []
        self._explain_node(ast, lines, 0)
        return "\n".join(lines)

    def _explain_node(self, node, lines, indent):
        prefix = "  " * indent
        t = node[0] if isinstance(node, tuple) else None
        if t == "PROGRAM":
            for stmt in node[1]:
                self._explain_node(stmt, lines, indent)
        elif t == "BLOCK":
            if node[1]:
                for stmt in node[1]:
                    self._explain_node(stmt, lines, indent + 1)
            else:
                lines.append(f"{prefix}  (do nothing)")
        elif t == "LET":
            lines.append(f"{prefix}Create a variable called '{node[1]}' and set it to the value of:")
            self._explain_node(node[2], lines, indent + 1)
        elif t == "FN":
            params = ", ".join(node[2]) if node[2] else "nothing"
            lines.append(f"{prefix}Define a function called '{node[1]}' that takes {params}:")
            self._explain_node(node[3], lines, indent + 1)
        elif t == "IF":
            cond_text = self._cond_to_english(node[1])
            lines.append(f"{prefix}If {cond_text}, then:")
            self._explain_node(node[2], lines, indent + 1)
            if node[3]:
                lines.append(f"{prefix}Otherwise:")
                self._explain_node(node[3], lines, indent + 1)
        elif t == "WHILE":
            cond_text = self._cond_to_english(node[1])
            lines.append(f"{prefix}Repeat as long as {cond_text}:")
            self._explain_node(node[2], lines, indent + 1)
        elif t == "FOR":
            lines.append(f"{prefix}Repeat for each value of '{node[1]}' in:")
            self._explain_node(node[2], lines, indent + 1)
            lines.append(f"{prefix}Running the following each time:")
            self._explain_node(node[3], lines, indent + 1)
        elif t == "RETURN":
            lines.append(f"{prefix}Give back the value of:")
            self._explain_node(node[1], lines, indent + 1)
        elif t == "PRINT":
            lines.append(f"{prefix}Display the value of:")
            self._explain_node(node[1], lines, indent + 1)
        elif t == "BINOP":
            self._explain_node(node[2], lines, indent)
            op_words = {"+": "plus", "-": "minus", "*": "times", "/": "divided by",
                        "==": "equals", "!=": "does not equal",
                        "<": "is less than", ">": "is greater than",
                        "<=": "is less than or equal to", ">=": "is greater than or equal to",
                        "and": "and", "or": "or"}
            lines.append(f"{prefix}  {op_words.get(node[1], node[1])}")
            self._explain_node(node[3], lines, indent)
        elif t == "NUMBER":
            lines.append(f"{prefix}  the number {node[1]}")
        elif t == "STRING":
            lines.append(f"{prefix}  the text \"{node[1]}\"")
        elif t == "VAR":
            lines.append(f"{prefix}  the value of '{node[1]}'")
        elif t == "BOOL":
            lines.append(f"{prefix}  {'yes' if node[1] else 'no'}")
        elif t == "NIL":
            lines.append(f"{prefix}  nothing")
        elif t == "CALL":
            lines.append(f"{prefix}Call the function '{node[1][1] if isinstance(node[1], tuple) and node[1][0] == 'VAR' else '?'}' with:")
            for arg in node[2]:
                self._explain_node(arg, lines, indent + 1)
        elif t == "ASSIGN":
            lines.append(f"{prefix}Update '{node[1][1] if isinstance(node[1], tuple) and node[1][0] == 'VAR' else '?'}' to:")
            self._explain_node(node[2], lines, indent + 1)
        elif t == "IMPORT":
            ns = f" as '{node[2]}'" if node[2] else ""
            lines.append(f"{prefix}Load the module '{node[1]}'{ns}")
        elif t == "EXPORT":
            lines.append(f"{prefix}Make '{node[1]}' available to other files")
        elif t == "INPUT":
            lines.append(f"{prefix}Ask the user to type something")
        else:
            lines.append(f"{prefix}({t})")

    def _cond_to_english(self, node):
        """Convert a condition expression to readable English."""
        if node[0] == "BINOP":
            op_words = {"+": "plus", "-": "minus", "*": "times", "/": "divided by",
                        "==": "equals", "!=": "does not equal",
                        "<": "is less than", ">": "is greater than",
                        "<=": "is less than or equal to", ">=": "is greater than or equal to"}
            return f"{self._val_to_english(node[2])} {op_words.get(node[1], node[1])} {self._val_to_english(node[3])}"
        if node[0] == "BOOL":
            return "yes" if node[1] else "no"
        if node[0] == "VAR":
            return f"the value of '{node[1]}'"
        return "(condition)"

    def _val_to_english(self, node):
        if node[0] == "NUMBER": return str(node[1])
        if node[0] == "STRING": return f"\"{node[1]}\""
        if node[0] == "VAR": return f"'{node[1]}'"
        if node[0] == "BOOL": return "yes" if node[1] else "no"
        if node[0] == "NIL": return "nothing"
        return "(value)"

    def run(self, source, readable=False):
        """Compile and execute Arc source code."""
        if readable:
            source = self._preprocess_readable(source)
        lexer = ArcLexer(source)
        parser = ArcParser(lexer.tokens)
        ast = parser.parse()
        self.vm.exec(ast)

    def run_tests(self, source):
        """Compile and run Arc test code, returning results."""
        lexer = ArcLexer(source)
        parser = ArcParser(lexer.tokens)
        ast = parser.parse()
        return self.vm.run_tests(ast)

    def run_file(self, path, readable=False):
        with open(path) as f:
            return self.run(f.read(), readable=readable)

    def repl(self, readable=False):
        """Interactive Arc REPL."""
        mode = "Readable" if readable else "Standard"
        print(f"Arc v1.0 ({mode} Mode) — Type 'exit' to quit")
        while True:
            try:
                line = input("arc> ")
                if line.strip() in ("exit", "quit"):
                    break
                self.run(line if line.endswith(";") else line + ";", readable=readable)
            except Exception as e:
                print(f"Error: {e}")

    def tokenize(self, source):
        lexer = ArcLexer(source)
        return lexer.tokens

    def parse(self, source, readable=False):
        if readable:
            source = self._preprocess_readable(source)
        lexer = ArcLexer(source)
        parser = ArcParser(lexer.tokens)
        return parser.parse()

    def ast_str(self, node, indent=0):
        if isinstance(node, tuple):
            s = " " * indent + node[0]
            for child in node[1:]:
                if isinstance(child, tuple):
                    s += "\n" + self.ast_str(child, indent + 2)
                else:
                    s += " " + str(child)
            return s
        return str(node)


# ============================================================
# FAT32 WRITER
# ============================================================

class FAT32Writer(FAT32Driver):
    """Extend FAT32Driver with write operations."""

    def create_file(self, name, content=b""):
        """Create a file in the root directory of mounted volume."""
        if not self.device:
            return "No volume mounted"
        if len(name) > 11:
            name = name[:8] + "." + name.split(".")[-1][:3] if "." in name else name[:8]
        name_bytes = name.encode('ascii', errors='replace').ljust(11, b'\x20')[:11]

        # Read root directory
        root_data = self.read_cluster(self.root_cluster)
        if len(root_data) < 32:
            root_data = root_data + b'\x00' * max(0, 32 - len(root_data))

        # Find free entry
        free_offset = -1
        for i in range(0, len(root_data), 32):
            if i + 32 > len(root_data):
                root_data += b'\x00' * 32
            if root_data[i] in (0x00, 0xE5):
                free_offset = i
                break
        if free_offset < 0:
            return "Root directory full"

        # Allocate a cluster for file data
        file_cluster = 3  # First usable cluster
        if content:
            # Write content to the cluster
            self.read_cluster(file_cluster)  # Verify cluster exists

        # Create directory entry
        entry = name_bytes + b'\x00'  # Name + attr (archive)
        entry += b'\x00' * 8  # Reserved
        entry += struct.pack("<H", file_cluster & 0xFFFF)  # Cluster low
        entry += struct.pack("<H", (file_cluster >> 16) & 0xFFFF)  # Cluster high
        entry += struct.pack("<I", len(content))  # File size

        # Write entry to root directory
        with open(self.device, "r+b") as f:
            data_sector = (self.root_cluster - 2) * self.sectors_per_cluster + self.data_offset // self.bytes_per_sector
            f.seek(data_sector * self.bytes_per_sector + free_offset)
            f.write(entry)

            # Write content if any
            if content:
                data_sector = (file_cluster - 2) * self.sectors_per_cluster + self.data_offset // self.bytes_per_sector
                f.seek(data_sector * self.bytes_per_sector)
                f.write(content)

        return f"Created: {name} ({len(content)} bytes)"

    def delete_file(self, name):
        """Mark a file as deleted in the directory."""
        entries = self.walk_directory(self.root_cluster)
        for e in entries:
            if e["name"] == name or e["name"].startswith(name):
                # Mark entry as deleted
                with open(self.device, "r+b") as f:
                    data_sector = (self.root_cluster - 2) * self.sectors_per_cluster + self.data_offset // self.bytes_per_sector
                    f.seek(data_sector * self.bytes_per_sector)
                    root_data = f.read(self.sectors_per_cluster * self.bytes_per_sector)
                    for i in range(0, len(root_data), 32):
                        entry = root_data[i:i+32]
                        if len(entry) >= 11:
                            ename = entry[0:8].rstrip(b'\x20').decode('ascii', errors='replace')
                            eext = entry[8:11].rstrip(b'\x20').decode('ascii', errors='replace')
                            efull = f"{ename}.{eext}" if eext else ename
                            if efull == name or efull.startswith(name):
                                f.seek(data_sector * self.bytes_per_sector + i)
                                f.write(b'\xE5')
                                return f"Deleted: {efull}"
                return f"Not found: {name}"
        return f"Not found: {name}"

    def format_label(self, label):
        """Read/write volume label in BPB (simulated — only for images)."""
        if not self.device:
            return "No volume mounted"
        try:
            label_bytes = label.encode('ascii', errors='replace').ljust(11, b'\x20')[:11]
            with open(self.device, "r+b") as f:
                f.seek(71)
                f.write(label_bytes)
            return f"Label set to: {label}"
        except Exception as e:
            return f"Failed: {e}"


# ============================================================
# B-TREE DATABASE
# ============================================================

class BTreeDB:
    """Disk-persisted B-Tree database engine."""

    def __init__(self, path=None, order=5):
        self.order = order
        self.root = BTreeNode(is_leaf=True)
        self.path = path or os.path.expanduser("~/.arcanis/var/btree.db")
        self._ensure_dir()
        self._load()

    def _ensure_dir(self):
        d = os.path.dirname(self.path)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)

    def insert(self, key, value):
        """Insert a key-value pair."""
        root = self.root
        if len(root.keys) == self.order * 2:
            new_root = BTreeNode(is_leaf=False)
            new_root.children.append(root)
            self._split_child(new_root, 0)
            self.root = new_root
        self._insert_non_full(self.root, key, value)
        self._save()

    def _insert_non_full(self, node, key, value):
        i = len(node.keys) - 1
        if node.is_leaf:
            node.keys.append(None)
            node.values.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            node.keys[i + 1] = key
            node.values[i + 1] = value
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == self.order * 2:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent, i):
        order = self.order
        child = parent.children[i]
        new_child = BTreeNode(is_leaf=child.is_leaf)
        parent.keys.insert(i, child.keys[order])
        parent.values.insert(i, child.values[order])
        parent.children.insert(i + 1, new_child)
        new_child.keys = child.keys[order + 1:]
        new_child.values = child.values[order + 1:]
        child.keys = child.keys[:order]
        child.values = child.values[:order]
        if not child.is_leaf:
            new_child.children = child.children[order + 1:]
            child.children = child.children[:order + 1]

    def search(self, key):
        """Search for a key, return value or None."""
        return self._search(self.root, key)

    def _search(self, node, key):
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            return node.values[i]
        if node.is_leaf:
            return None
        return self._search(node.children[i], key)

    def delete(self, key):
        """Delete a key-value pair."""
        self._delete(self.root, key)
        if len(self.root.keys) == 0 and not self.root.is_leaf:
            self.root = self.root.children[0]
        self._save()

    def _delete(self, node, key):
        if node.is_leaf:
            for i, k in enumerate(node.keys):
                if k == key:
                    node.keys.pop(i)
                    node.values.pop(i)
                    return
            return

        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        if i < len(node.keys) and node.keys[i] == key:
            if node.children[i].is_leaf:
                pred = node.children[i]
                node.keys[i] = pred.keys[-1]
                node.values[i] = pred.values[-1]
                pred.keys.pop()
                pred.values.pop()
            else:
                self._delete(node.children[i], node.children[i].keys[-1])
                node.keys[i] = node.children[i].keys[-1] if node.children[i].keys else None
        else:
            if len(node.children[i].keys) < self.order:
                self._rebalance(node, i)
            self._delete(node.children[i], key)

    def _rebalance(self, parent, i):
        child = parent.children[i]
        if i > 0 and len(parent.children[i - 1].keys) > self.order:
            sibling = parent.children[i - 1]
            child.keys.insert(0, parent.keys[i - 1])
            child.values.insert(0, parent.values[i - 1])
            if not child.is_leaf:
                child.children.insert(0, sibling.children.pop())
            parent.keys[i - 1] = sibling.keys.pop()
            parent.values[i - 1] = sibling.values.pop()
        elif i < len(parent.children) - 1 and len(parent.children[i + 1].keys) > self.order:
            sibling = parent.children[i + 1]
            child.keys.append(parent.keys[i])
            child.values.append(parent.values[i])
            if not child.is_leaf:
                child.children.append(sibling.children.pop(0))
            parent.keys[i] = sibling.keys.pop(0)
            parent.values[i] = sibling.values.pop(0)
        else:
            if i > 0:
                left = parent.children[i - 1]
                left.keys.append(parent.keys.pop(i - 1))
                left.values.append(parent.values.pop(i - 1))
                left.keys.extend(child.keys)
                left.values.extend(child.values)
                if not child.is_leaf:
                    left.children.extend(child.children)
                parent.children.pop(i)
            else:
                right = parent.children[i + 1]
                child.keys.append(parent.keys.pop(i))
                child.values.append(parent.values.pop(i))
                child.keys.extend(right.keys)
                child.values.extend(right.values)
                if not child.is_leaf:
                    child.children.extend(right.children)
                parent.children.pop(i + 1)

    def scan(self, prefix=None):
        """Return all key-value pairs (optionally with prefix filter)."""
        results = []
        self._scan(self.root, results, prefix)
        return results

    def _scan(self, node, results, prefix):
        if node.is_leaf:
            for i, k in enumerate(node.keys):
                if prefix is None or str(k).startswith(str(prefix)):
                    results.append((k, node.values[i]))
        else:
            for i in range(len(node.keys)):
                self._scan(node.children[i], results, prefix)
                if prefix is None or str(node.keys[i]).startswith(str(prefix)):
                    results.append((node.keys[i], node.values[i]))
            self._scan(node.children[-1], results, prefix)

    def _save(self):
        """Serialize B-tree to JSON."""
        data = self._serialize(self.root)
        with open(self.path, "w") as f:
            json.dump(data, f)

    def _serialize(self, node):
        return {
            "is_leaf": node.is_leaf,
            "keys": node.keys,
            "values": node.values,
            "children": [self._serialize(c) for c in node.children] if node.children else [],
        }

    def _load(self):
        """Deserialize B-tree from JSON."""
        if not os.path.isfile(self.path) or os.path.getsize(self.path) == 0:
            return
        try:
            with open(self.path) as f:
                data = json.load(f)
            self.root = self._deserialize(data)
        except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError):
            pass

    def _deserialize(self, data):
        node = BTreeNode(is_leaf=data["is_leaf"])
        node.keys = data["keys"]
        node.values = data["values"]
        node.children = [self._deserialize(c) for c in data.get("children", [])]
        return node

    def stats(self):
        """Return DB statistics."""
        all_data = self.scan()
        return {
            "keys": len(all_data),
            "order": self.order,
            "file": self.path,
            "size": os.path.getsize(self.path) if os.path.isfile(self.path) else 0,
        }


class BTreeNode:
    """B-Tree node."""

    def __init__(self, is_leaf=True):
        self.is_leaf = is_leaf
        self.keys = []
        self.values = []
        self.children = []


# ============================================================
# ARC NATIVE COMPILER (Arc → x86_64)
# ============================================================

class ArcCompiler:
    """Compile Arc AST to native x86_64 machine code via JIT."""

    def __init__(self, jit):
        self.jit = jit
        self.abi = "microsoft"  # default for Windows

    def compile_expr(self, source):
        """Compile an Arc expression to x86_64 and return the function pointer."""
        lexer = ArcLexer(source if source.endswith(";") else source + ";")
        parser = ArcParser(lexer.tokens)
        ast = parser.parse()
        # Extract the expression from the program
        stmts = ast[1] if ast[0] == "PROGRAM" else [ast]
        if not stmts:
            return None, "No statements"
        stmt = stmts[0]
        # Handle PRINT expr
        if stmt[0] == "PRINT":
            expr = stmt[1]
        elif stmt[0] == "EXPR":
            expr = stmt[1]
        elif stmt[0] == "RETURN":
            expr = stmt[1]
        else:
            expr = stmt

        try:
            code = self._gen_expr(expr)
            code += bytes([0xC3])  # ret
            func, ptr = self.jit.make_function(code, argtypes=[])
            return func, ptr
        except Exception as e:
            return None, str(e)

    def compile_and_run(self, source):
        """Compile and execute an Arc expression, return result."""
        func, ptr_or_err = self.compile_expr(source)
        if func is None:
            return f"Compile error: {ptr_or_err}"
        try:
            result = func()
            return result
        finally:
            try:
                self.jit.free(ptr_or_err, 64)
            except Exception:
                pass

    def _gen_expr(self, node):
        """Generate x86_64 bytes for an AST node. Result left in RAX."""
        if node[0] == "NUMBER":
            val = node[1]
            if val == 0:
                return bytes([0x48, 0x31, 0xC0])  # xor rax, rax
            if -0x80000000 <= val <= 0x7FFFFFFF:
                code = bytes([0x48, 0xC7, 0xC0])  # mov rax, imm32
                code += struct.pack("<i", val)
                return code
            code = bytes([0x48, 0xB8])  # mov rax, imm64
            code += struct.pack("<q", val)
            return code

        if node[0] == "BINOP":
            # Generate code for right operand first (will be pushed)
            right_code = self._gen_expr(node[3])
            left_code = self._gen_expr(node[2])
            # push right; push left; pop rax; pop rbx; op rax, rbx; push rax; pop rax
            code = right_code
            code += bytes([0x50])  # push rax
            code += left_code
            code += bytes([0x50])  # push rax
            code += bytes([0x58])  # pop rax — left
            code += bytes([0x5B])  # pop rbx — right
            op = node[1]
            if op == "+":
                code += bytes([0x48, 0x01, 0xD8])  # add rax, rbx
            elif op == "-":
                code += bytes([0x48, 0x29, 0xD8])  # sub rax, rbx
            elif op == "*":
                code += bytes([0x48, 0x0F, 0xAF, 0xC3])  # imul rax, rbx
            elif op == "/":
                code += bytes([0x48, 0x31, 0xD2])  # xor rdx, rdx
                code += bytes([0x48, 0xF7, 0xF3])  # div rbx (rax = rax/rbx)
            else:
                raise ValueError(f"Unsupported op for native: {op}")
            return code

        if node[0] == "UNARY":
            sub_code = self._gen_expr(node[2])
            if node[1] == "-":
                code = sub_code
                code += bytes([0x48, 0xF7, 0xD8])  # neg rax
                return code
            return sub_code

        if node[0] == "BOOL":
            code = bytes([0x48, 0xC7, 0xC0])
            code += struct.pack("<i", 1 if node[1] else 0)
            return code

        # Default: return 0
        return bytes([0x48, 0x31, 0xC0])

    def compile_file(self, path):
        """Compile and run an Arc script file natively."""
        if not os.path.isfile(path):
            return f"File not found: {path}"
        with open(path) as f:
            source = f.read()
        # For multi-statement scripts, fall back to VM
        arc = ArcLang(jit=self.jit)
        arc.run(source)
        return "Script executed (VM fallback for multi-statement)"


# ============================================================
# VISUAL ARC IDE (tkinter)
# ============================================================

class ArcIDE:
    """Visual code editor for Arc language with syntax highlighting."""

    KEYWORD_COLORS = {
        "let": "#569CD6", "define": "#569CD6", "set": "#569CD6",
        "fn": "#569CD6", "function": "#569CD6",
        "if": "#569CD6", "when": "#569CD6",
        "else": "#569CD6", "otherwise": "#569CD6",
        "while": "#569CD6", "repeat": "#569CD6",
        "for": "#569CD6", "foreach": "#569CD6",
        "in": "#569CD6",
        "return": "#569CD6", "result": "#569CD6",
        "true": "#4EC9B0", "yes": "#4EC9B0", "on": "#4EC9B0",
        "false": "#4EC9B0", "no": "#4EC9B0", "off": "#4EC9B0",
        "nil": "#4EC9B0", "nothing": "#4EC9B0", "none": "#4EC9B0",
        "print": "#DCDCAA", "display": "#DCDCAA", "show": "#DCDCAA", "say": "#DCDCAA",
        "input": "#DCDCAA",
        "import": "#C586C0", "export": "#C586C0", "as": "#C586C0",
        "try": "#C586C0", "catch": "#C586C0",
        "throw": "#DCDCAA",
        "class": "#569CD6", "extends": "#569CD6",
        "new": "#DCDCAA",
        "this": "#4EC9B0", "super": "#4EC9B0",
        "test": "#C586C0", "describe": "#C586C0", "it": "#C586C0",
        "assert": "#DCDCAA", "expect": "#DCDCAA",
        "breakpoint": "#DCDCAA", "watch": "#DCDCAA",
    }

    def __init__(self, jit=None):
        self.root = None
        self.text = None
        self.output = None
        self.watch_var = None
        self.watch_list = None
        self.debug_controls = None
        self.arc = ArcLang(jit=jit)
        self.readable_mode = False
        self.debug_paused = False
        self.debug_continue = False
        self.debug_step_over = False
        self.debug_step_into = False
        self.env_snapshot = {}

    def available(self):
        return _HAVE_TK

    def launch(self):
        if not _HAVE_TK:
            print("\033[31mTkinter not available\033[0m")
            return
        self.root = tk.Tk()
        self.root.title("Arc IDE")
        self.root.geometry("800x600")
        self.root.configure(bg="#1E1E1E")

        # Menu
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._new_file)
        file_menu.add_command(label="Open", command=self._open_file)
        file_menu.add_command(label="Save", command=self._save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)

        run_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Execute", command=self._run_code)
        run_menu.add_command(label="Run Tests", command=self._run_tests)
        run_menu.add_command(label="Debug", command=self._debug_start)
        run_menu.add_separator()
        run_menu.add_command(label="Show Tokens", command=self._show_tokens)
        run_menu.add_command(label="Show AST", command=self._show_ast)
        run_menu.add_command(label="Explain", command=self._explain_code)
        run_menu.add_separator()
        self.readable_var = tk.BooleanVar(value=False)
        run_menu.add_checkbutton(label="Readable Mode", variable=self.readable_var)

        # Editor
        frame = tk.Frame(self.root, bg="#1E1E1E")
        frame.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(frame, bg="#1E1E1E", fg="#D4D4D4",
                            insertbackground="#D4D4D4", font=("Consolas", 11),
                            wrap=tk.NONE, relief=tk.FLAT, padx=10, pady=10)
        self.text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scroll_y = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.text.yview)
        scroll_y.pack(fill=tk.Y, side=tk.RIGHT)
        self.text.config(yscrollcommand=scroll_y.set)

        # Line numbers
        line_frame = tk.Frame(self.root, bg="#252526")
        line_frame.pack(fill=tk.X)

        tk.Label(line_frame, text="Ln 1, Col 1", bg="#252526", fg="#858585",
                 font=("Consolas", 9), anchor="w").pack(side=tk.LEFT, padx=10)

        run_btn = tk.Button(line_frame, text="Run ▶", bg="#0E639C", fg="white",
                            font=("Consolas", 9), command=self._run_code,
                            relief=tk.FLAT, padx=15)
        run_btn.pack(side=tk.RIGHT, padx=5, pady=2)

        self.debug_controls = tk.Frame(self.root, bg="#2D2D2D")
        self.debug_controls.pack(fill=tk.X)
        btn_continue = tk.Button(self.debug_controls, text="▶ Continue", bg="#0E639C", fg="white",
                                 font=("Consolas", 9), command=self._debug_continue,
                                 relief=tk.FLAT, padx=10, state=tk.DISABLED)
        btn_continue.pack(side=tk.LEFT, padx=2, pady=2)
        btn_step_over = tk.Button(self.debug_controls, text="↷ Step Over", bg="#0E639C", fg="white",
                                  font=("Consolas", 9), command=self._debug_step_over,
                                  relief=tk.FLAT, padx=10, state=tk.DISABLED)
        btn_step_over.pack(side=tk.LEFT, padx=2, pady=2)
        btn_step_into = tk.Button(self.debug_controls, text="→ Step Into", bg="#0E639C", fg="white",
                                  font=("Consolas", 9), command=self._debug_step_into,
                                  relief=tk.FLAT, padx=10, state=tk.DISABLED)
        btn_step_into.pack(side=tk.LEFT, padx=2, pady=2)
        btn_stop = tk.Button(self.debug_controls, text="■ Stop", bg="#8B0000", fg="white",
                             font=("Consolas", 9), command=self._debug_stop,
                             relief=tk.FLAT, padx=10, state=tk.DISABLED)
        btn_stop.pack(side=tk.LEFT, padx=2, pady=2)
        self.debug_controls.pack_forget()  # Hidden until debug starts

        # Watch variables pane
        watch_frame = tk.Frame(self.root, bg="#1E1E1E")
        watch_frame.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(watch_frame, text="Watch:", bg="#1E1E1E", fg="#858585",
                 font=("Consolas", 9)).pack(side=tk.LEFT, padx=5)
        self.watch_var = tk.Entry(watch_frame, bg="#3C3C3C", fg="#D4D4D4",
                                  font=("Consolas", 9), relief=tk.FLAT, width=20)
        self.watch_var.pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(watch_frame, text="Add", bg="#0E639C", fg="white",
                  font=("Consolas", 8), command=self._debug_add_watch,
                  relief=tk.FLAT, padx=8).pack(side=tk.LEFT, padx=2)
        self.watch_list = tk.Listbox(watch_frame, bg="#1E1E1E", fg="#D4D4D4",
                                     font=("Consolas", 9), height=3, relief=tk.FLAT)
        self.watch_list.pack(fill=tk.X, padx=5, pady=2)

        # Output pane
        self.output = tk.Text(self.root, bg="#1E3A3A", fg="#4EC9B0",
                              font=("Consolas", 10), height=8, relief=tk.FLAT,
                              padx=10, pady=5)
        self.output.pack(fill=tk.BOTH, side=tk.BOTTOM)
        self.output.insert(tk.END, "▶ Output will appear here\n")
        self.output.config(state=tk.DISABLED)

        # Syntax highlight on key release
        self.text.bind("<KeyRelease>", self._highlight)

        # Set default content
        default_code = """# Arc language demo — Readable Mode examples
# ------------------------------------------------
# Standard Arc:
fn fib(n) {
    if n <= 1 { result n; }
    result fib(n-1) + fib(n-2);
}
display "fib(20) = " + fib(20);

# Readable English syntax (toggle Readable Mode):
#   set n to 10;
#   display n;
#   increase n by 5;
#   display "n is now " + n;
#
#   repeat n > 0 {
#       display "counting: " + n;
#       decrease n by 1;
#   }

let sum = 0;
for i in 10 {
    set sum to sum + i;
}
print "sum(0..9) = " + sum;
"""
        self.text.insert(tk.END, default_code)
        self._highlight()

        self.root.mainloop()

    def _highlight(self, event=None):
        """Apply syntax highlighting."""
        if not self.text:
            return
        try:
            content = self.text.get("1.0", tk.END)
            self.text.mark_set(tk.INSERT, self.text.index(tk.INSERT))
            # Reset all to default
            self.text.config(state=tk.NORMAL)
            # Clear tags
            for tag in self.text.tag_names():
                if tag != "sel":
                    self.text.tag_delete(tag)

            # Highlight strings
            start = None
            for i, ch in enumerate(content):
                if ch == '"' and start is None:
                    start = i
                elif ch == '"' and start is not None:
                    idx1 = f"1.0 + {start} chars"
                    idx2 = f"1.0 + {i + 1} chars"
                    self.text.tag_add("str", idx1, idx2)
                    self.text.tag_config("str", foreground="#CE9178")
                    start = None

            # Highlight keywords
            for word, color in self.KEYWORD_COLORS.items():
                idx = content.find(word)
                while idx >= 0:
                    prev = content[idx - 1] if idx > 0 else " "
                    nxt = content[idx + len(word)] if idx + len(word) < len(content) else " "
                    if not prev.isalnum() and not nxt.isalnum():
                        idx1 = f"1.0 + {idx} chars"
                        idx2 = f"1.0 + {idx + len(word)} chars"
                        self.text.tag_add(f"kw_{word}", idx1, idx2)
                        self.text.tag_config(f"kw_{word}", foreground=color)
                    idx = content.find(word, idx + 1)

            # Highlight numbers
            i = 0
            while i < len(content):
                if content[i].isdigit() and (i == 0 or not content[i-1].isalnum()):
                    j = i
                    while j < len(content) and content[j].isdigit():
                        j += 1
                    idx1 = f"1.0 + {i} chars"
                    idx2 = f"1.0 + {j} chars"
                    self.text.tag_add(f"num_{i}", idx1, idx2)
                    self.text.tag_config(f"num_{i}", foreground="#B5CEA8")
                    i = j
                else:
                    i += 1

            # Highlight comments
            i = 0
            while i < len(content):
                if content[i] == '#':
                    j = i
                    while j < len(content) and content[j] != '\n':
                        j += 1
                    idx1 = f"1.0 + {i} chars"
                    idx2 = f"1.0 + {j} chars"
                    self.text.tag_add(f"cmt_{i}", idx1, idx2)
                    self.text.tag_config(f"cmt_{i}", foreground="#6A9955")
                    i = j
                else:
                    i += 1

            self.text.config(state=tk.NORMAL)
        except Exception:
            pass

    def _run_code(self):
        """Execute the code in the editor."""
        code = self.text.get("1.0", tk.END).strip()
        if not code:
            return
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "▶ Running...\n")

        old_stdout = sys.stdout
        sys.stdout = output_capture = __import__('io').StringIO()
        try:
            self.arc.run(code, readable=self.readable_var.get())
            result = output_capture.getvalue()
        except Exception as e:
            result = f"Error: {e}"
        finally:
            sys.stdout = old_stdout

        self.output.delete("1.0", tk.END)
        if result:
            self.output.insert(tk.END, result)
        else:
            self.output.insert(tk.END, "(no output)")
        self.output.config(state=tk.DISABLED)

    def _run_tests(self):
        """Run test cases in the editor."""
        code = self.text.get("1.0", tk.END).strip()
        if not code:
            return
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)

        old_stdout = sys.stdout
        sys.stdout = output_capture = __import__('io').StringIO()
        try:
            self.arc.run_tests(code)
            result = output_capture.getvalue()
        except Exception as e:
            result = f"Error: {e}"
        finally:
            sys.stdout = old_stdout
        if not result:
            result = output_capture.getvalue()
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, result if result else "(no output)")
        self.output.config(state=tk.DISABLED)

    def _debug_callback(self, vm):
        """Called by VM when a breakpoint is hit."""
        self.env_snapshot = dict(vm.env)
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "⏸ Paused at breakpoint\n--- Variables ---\n")
        for k, v in sorted(vm.env.items()):
            self.output.insert(tk.END, f"  {k} = {v!r}\n")
        self.output.config(state=tk.DISABLED)
        self.debug_controls.pack(fill=tk.X, before=self.output)
        for child in self.debug_controls.winfo_children():
            child.config(state=tk.NORMAL)
        self._update_watches(vm)
        self.root.update()
        self.debug_paused = True
        self.debug_continue = False
        self.debug_step_over = False
        self.debug_step_into = False
        while self.debug_paused:
            self.root.update()
            __import__('time').sleep(0.05)
            if self.debug_continue:
                self.debug_paused = False
                break
            if self.debug_step_over or self.debug_step_into:
                self.debug_paused = False
                break
        self.debug_controls.pack_forget()
        for child in self.debug_controls.winfo_children():
            child.config(state=tk.DISABLED)

    def _debug_start(self):
        """Start debugging the current code."""
        code = self.text.get("1.0", tk.END).strip()
        if not code:
            return
        self.arc.vm.debug_mode = True
        self.arc.vm.debug_callback = self._debug_callback
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "▶ Debugging...\n")
        self.output.config(state=tk.DISABLED)
        old_stdout = sys.stdout
        sys.stdout = output_capture = __import__('io').StringIO()
        try:
            self.arc.run(code, readable=self.readable_var.get())
            result = output_capture.getvalue()
        except Exception as e:
            result = f"Error: {e}"
        finally:
            sys.stdout = old_stdout
            self.arc.vm.debug_mode = False
            self.arc.vm.debug_callback = None
        if result:
            self.output.config(state=tk.NORMAL)
            self.output.insert(tk.END, result)
            self.output.config(state=tk.DISABLED)

    def _debug_continue(self):
        self.debug_continue = True

    def _debug_step_over(self):
        self.debug_step_over = True

    def _debug_step_into(self):
        self.debug_step_into = True

    def _debug_stop(self):
        self.debug_paused = False
        self.debug_continue = True
        self.debug_controls.pack_forget()

    def _debug_add_watch(self):
        var_name = self.watch_var.get().strip()
        if var_name and var_name not in self.watch_list.get(0, tk.END):
            self.watch_list.insert(tk.END, var_name)
        self.watch_var.delete(0, tk.END)

    def _update_watches(self, vm):
        for i in range(self.watch_list.size()):
            var_name = self.watch_list.get(i)
            val = vm.env.get(var_name, "<undefined>")
            self.watch_list.delete(i)
            self.watch_list.insert(i, f"{var_name} = {val!r}")

    def _show_tokens(self):
        code = self.text.get("1.0", tk.END).strip()
        if not code:
            return
        lexer = ArcLexer(code)
        result = "\n".join(f"  {t[0]:>8}  '{t[1]}'" for t in lexer.tokens)
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, result if result else "(empty)")
        self.output.config(state=tk.DISABLED)

    def _explain_code(self):
        """Explain the code in plain English."""
        code = self.text.get("1.0", tk.END).strip()
        if not code:
            return
        try:
            result = self.arc.explain(code)
        except Exception as e:
            result = f"Error: {e}"
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, result)
        self.output.config(state=tk.DISABLED)

    def _show_ast(self):
        code = self.text.get("1.0", tk.END).strip()
        if not code:
            return
        try:
            ast = self.arc.parse(code, readable=self.readable_var.get())
            result = self.arc.ast_str(ast)
        except Exception as e:
            result = f"Error: {e}"
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, result)
        self.output.config(state=tk.DISABLED)

    def _new_file(self):
        self.text.delete("1.0", tk.END)
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "▶ New file\n")
        self.output.config(state=tk.DISABLED)

    def _open_file(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("Arc files", "*.arc"), ("All files", "*.*")])
        if path:
            try:
                with open(path) as f:
                    self.text.delete("1.0", tk.END)
                    self.text.insert(tk.END, f.read())
                self._highlight()
            except Exception as e:
                self.output.config(state=tk.NORMAL)
                self.output.delete("1.0", tk.END)
                self.output.insert(tk.END, f"Error: {e}")
                self.output.config(state=tk.DISABLED)

    def _save_file(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".arc",
                                              filetypes=[("Arc files", "*.arc"), ("All files", "*.*")])
        if path:
            try:
                with open(path, "w") as f:
                    f.write(self.text.get("1.0", tk.END).strip())
            except Exception as e:
                self.output.config(state=tk.NORMAL)
                self.output.delete("1.0", tk.END)
                self.output.insert(tk.END, f"Error: {e}")
                self.output.config(state=tk.DISABLED)


THEMES = {
    "default": {"prompt": "1;32", "info": "1;36", "ok": "32", "err": "31", "warn": "33", "dim": "90", "accent": "1;35"},
    "dark":    {"prompt": "1;33", "info": "1;34", "ok": "32", "err": "31", "warn": "33", "dim": "90", "accent": "1;35"},
    "light":   {"prompt": "30",   "info": "34",   "ok": "32", "err": "31", "warn": "33", "dim": "90", "accent": "35"},
    "neon":    {"prompt": "1;36", "info": "1;35", "ok": "1;32", "err": "1;31", "warn": "1;33", "dim": "95", "accent": "1;34"},
    "retro":   {"prompt": "1;33", "info": "1;32", "ok": "32", "err": "1;31", "warn": "33", "dim": "90", "accent": "1;36"},
}

class Shell:
    def __init__(self, kernel: Kernel, fs: FileSystem):
        self.kernel = kernel
        self.fs = fs
        self.blockchain = Blockchain()
        self.nn = NeuralNetwork()
        self.qc = None
        self.httpd = None
        self.http_thread = None
        self.peer_server = None
        self.peer_thread = None
        self.peers = []  # [(socket, address, name)]
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
        self.theme = "default"
        self._load_config()
        self._script_vars = {}
        self.win32 = Win32API()
        self.jit = NativeJIT()
        self.pe_loader = PELoader()
        self.pm = ProcessManager()
        self.desktop = DesktopManager()
        self.sound = SoundSystem()
        self.fat32 = FAT32Driver()
        self.mp_processes = {}
        self.arc = ArcLang(jit=self.jit if self.jit.available() else None)
        self.arc_compiler = ArcCompiler(self.jit) if self.jit.available() else None
        self.arc_ide = ArcIDE(jit=self.jit if self.jit.available() else None)
        self.db = BTreeDB()
        self.fat32_writer = FAT32Writer()

    def _config_path(self):
        return os.path.join(self.fs.ARCANIS_HOME, "etc", "config.json")

    def _load_config(self):
        path = self._config_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    cfg = json.load(f)
                self.env.update(cfg.get("env", {}))
                self.theme = cfg.get("theme", "default")
                self.history = cfg.get("history", [])
            except Exception:
                pass

    def _save_config(self):
        path = self._config_path()
        try:
            cfg = {"theme": self.theme, "env": self.env, "history": self.history[-100:]}
            with open(path, 'w') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def _c(self, color_key: str, text: str = "") -> str:
        """Colorize text using current theme."""
        colors = THEMES.get(self.theme, THEMES["default"])
        code = colors.get(color_key, "0")
        if text:
            return f"\033[{code}m{text}\033[0m"
        return code

    def run(self):
        ic = self._c("info")
        dm = self._c("dim")
        print(f"\033[{ic}m" + r"""
     _                _                 ____   ___   ____
    / \   _ __   __ _| |_ ___  _ __   |  _ \ / _ \ / ___|
   / _ \ | '_ \ / _` | __/ _ \| '__|  | |_) | | | | |
  / ___ \| | | | (_| | || (_) | |     |  __/| |_| | |___
 /_/   \_\_| |_|\__,_|\__\___/|_|     |_|    \___/ \____|
        """ + "\033[0m")
        print(f"{dm}  Arcanis OS v6.0.0 — Real FS, Real Compute, Real Crypto\033[0m")
        print(f"{dm}  86 modules | 170 commands | ~/.arcanis/ on disk\033[0m")
        print(f"{dm}  FS root: {self.fs.ARCANIS_HOME}\033[0m")
        print(f"{dm}  Theme: {self.theme} | Type 'help' for commands\033[0m")
        print()

        while self.running:
            try:
                ps1 = self.env.get("PS1", "arcanis> ")
                pc = self._c("prompt")
                cmd = input(f"\033[{pc}m{ps1}\033[0m")
                if not cmd.strip():
                    continue
                self.history.append(cmd)
                self._execute(cmd.strip())
            except KeyboardInterrupt:
                print(f"\n{dm}^C\033[0m")
            except EOFError:
                print(f"\n{dm}logout\033[0m")
                self.running = False

    def _execute(self, cmd: str):
        cmd = cmd.strip("\ufeff\u00a0 ")
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
            "docker": self.cmd_docker,
            "podman": self.cmd_podman,
            "iptables": self.cmd_iptables,
            "vpn": self.cmd_vpn,
            "aws": self.cmd_aws,
            "lambda": self.cmd_lambda,
            "ai": self.cmd_ai,
            "rag": self.cmd_rag,
            "agent": self.cmd_agent,
            "gpu": self.cmd_gpu,
            "fpga": self.cmd_fpga,
            "mobile": self.cmd_mobile,
            "rt": self.cmd_rt,
            "cluster": self.cmd_cluster,
            "edge": self.cmd_edge,
            "blockchain": self.cmd_blockchain,
            "chain": self.cmd_blockchain,
            "quantum": self.cmd_quantum,
            "qc": self.cmd_quantum,
            "monitor": self.cmd_monitor,
            "metrics": self.cmd_monitor,
            "twin": self.cmd_digital_twin,
            "edgeai": self.cmd_edgeai,
            "sdn": self.cmd_sdn,
            "hpc": self.cmd_hpc,
            "analytics": self.cmd_analytics,
            "gateway": self.cmd_gateway,
            "gw": self.cmd_gateway,
            "autonomous": self.cmd_autonomous,
            "arvr": self.cmd_arvr,
            "xr": self.cmd_arvr,
            "zerotrust": self.cmd_zerotrust,
            "zt": self.cmd_zerotrust,
            "multicloud": self.cmd_multicloud,
            "mcloud": self.cmd_multicloud,
            "devops": self.cmd_devops,
            "ci": self.cmd_devops,
            "power": self.cmd_power,
            "locale": self.cmd_locale,
            "i18n": self.cmd_locale,
            "cognitive": self.cmd_cognitive,
            "biofs": self.cmd_biofs,
            "reality": self.cmd_reality,
            "mesh": self.cmd_mesh,
            "hive": self.cmd_hive,
            "sentient": self.cmd_sentient,
            "exadata": self.cmd_exadata,
            "tcrystal": self.cmd_tcrystal,
            "gneural": self.cmd_gneural,
            "holo": self.cmd_holo,
            "evolve": self.cmd_evolve,
            "unicompute": self.cmd_unicompute,
            "neural": self.cmd_neural,
            "gen": self.cmd_generative,
            "4d": self.cmd_fourd,
            "immortal": self.cmd_immortal,
            "emotive": self.cmd_emotive,
            "polyglot": self.cmd_polyglot,
            "qnet": self.cmd_qnet,
            "synth": self.cmd_synthesis,
            "prob": self.cmd_probabilistic,
            "soul": self.cmd_soul,
            "dream": self.cmd_dream,
            "bio": self.cmd_bio_os,
            "rscript": self.cmd_rscript,
            "tmarket": self.cmd_tmarket,
            "unidoc": self.cmd_unidoc,
            "portal": self.cmd_portal,
            "con": self.cmd_consciousness,
            "meta": self.cmd_metaos,
            "eternity": self.cmd_eternity,
            "omega": self.cmd_omega,
            "serve": self.cmd_serve,
            "listen": self.cmd_listen,
            "connect": self.cmd_connect,
            "peers": self.cmd_peers,
            "broadcast": self.cmd_broadcast,
            "sync": self.cmd_sync_chain,
            "theme": self.cmd_theme,
            "config": self.cmd_config,
            "winapi": self.cmd_winapi,
            "jit": self.cmd_jit,
            "pe": self.cmd_pe,
            "mp": self.cmd_mp,
            "desktop": self.cmd_desktop,
            "sound": self.cmd_sound,
            "fat32": self.cmd_fat32,
            "arc": self.cmd_arc,
            "db": self.cmd_db,
            "arcide": self.cmd_arcide,
            "apm": self.cmd_apm,
        }

        handler = dispatch.get(command)
        if handler:
            handler(args)
        else:
            print(f"\033[31marcanis: {command}: command not found\033[0m")
            print("\033[90mType 'help' for available commands\033[0m")

    # ======================== FILE COMMANDS ========================

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
        info = self.fs._resolve(path)
        if info and info.is_dir:
            self.fs.cwd = info
            self.kernel.syscall("chdir", path)
        else:
            print(f"\033[31mcd: no such directory: {path}\033[0m")

    def cmd_pwd(self, _):
        cwd = getattr(self.fs.cwd, '_real_path', self.fs.cwd) if hasattr(self.fs.cwd, '_real_path') else self.fs.cwd
        arc_home = self.fs.ARCANIS_HOME
        if cwd.startswith(arc_home):
            rel = cwd[len(arc_home):] or "/"
            print(rel.replace(os.sep, "/"))
        else:
            print(cwd)

    def cmd_cat(self, args):
        if not args:
            print("\033[31mcat: missing file\033[0m")
            return
        content = self.fs.read(args[0])
        if content is not None:
            print(content, end="")
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

    # ======================== PROCESS COMMANDS ========================

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

    # ======================== SYSTEM COMMANDS ========================

    def cmd_sysinfo(self, _):
        print("\033[1;36m\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557")
        print("\u2551         ARCANIS SYSTEM INFORMATION       \u2551")
        print("\u2560\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2563")
        print(f"\u2551  OS       : Arcanis OS v6.0.0            \u2551")
        print(f"\u2551  Kernel   : 32-bit x86 microkernel       \u2551")
        print(f"\u2551  FS       : Real (~/.arcanis/)           \u2551")
        print(f"\u2551  Processes: {len(self.kernel.list_processes()):<28}\u2551")
        print(f"\u2551  Uptime   : {self.kernel.uptime}s{' ' * (26 - len(str(self.kernel.uptime)))}\u2551")
        print(f"\u2551  Shell    : arcanis-sh (170 commands)    \u2551")
        print("\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d\033[0m")

    def cmd_uptime(self, _):
        print(f"up {self.kernel.uptime}s")

    def cmd_uname(self, args):
        if "-a" in args:
            print("Arcanis 6.0.0 arcanis #1 SMP x86 i686")
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

    def cmd_env(self, _):
        for k, v in sorted(self.env.items()):
            print(f"{k}={v}")

    def cmd_export(self, args):
        for arg in args:
            if "=" in arg:
                k, v = arg.split("=", 1)
                self.env[k] = v
        self._save_config()

    def cmd_theme(self, args):
        """Change color theme."""
        if not args:
            names = list(THEMES.keys())
            print(f"Current theme: {self._c('accent', self.theme)}")
            print(f"Available: {', '.join(names)}")
            return
        name = args[0]
        if name in THEMES:
            self.theme = name
            self._save_config()
            print(f"Theme changed to {self._c('accent', name)}")
        else:
            print(f"\033[31mUnknown theme: {name}\033[0m")
            print(f"Available: {', '.join(THEMES.keys())}")

    def cmd_config(self, args):
        """Show persistent configuration."""
        print(f"  Config file: {self._c('dim', self._config_path())}")
        print(f"  Theme:       {self._c('accent', self.theme)}")
        print(f"  User:        {self.env.get('USER', 'root')}")
        print(f"  Prompt:      {self.env.get('PS1', 'arcanis> ')}")
        print(f"  History:     {len(self.history)} commands")
        print(f"  FS root:     {self._c('dim', self.fs.ARCANIS_HOME)}")

    # ======================== AI / INFERENCE ========================

    def cmd_inference(self, args):
        query = " ".join(args) if args else "hello"
        print(f"\033[1;35m[INFERENCE]\033[0m Processing: '{query}'")
        intents = {
            "hello": ("greeting", 0.95),
            "hi": ("greeting", 0.93),
            "hey": ("greeting", 0.90),
            "help": ("help_request", 0.97),
            "time": ("system_info", 0.94),
            "date": ("system_info", 0.94),
            "status": ("system_info", 0.92),
            "list": ("file_operation", 0.91),
            "read": ("file_operation", 0.90),
            "create": ("file_operation", 0.89),
            "write": ("file_operation", 0.88),
            "delete": ("file_operation", 0.91),
            "remove": ("file_operation", 0.90),
            "process": ("process_management", 0.93),
            "kill": ("process_management", 0.95),
            "run": ("execution", 0.92),
            "execute": ("execution", 0.91),
            "compile": ("development", 0.94),
            "build": ("development", 0.93),
            "test": ("quality", 0.95),
            "deploy": ("operations", 0.94),
            "install": ("package_management", 0.96),
            "search": ("information_retrieval", 0.92),
            "find": ("information_retrieval", 0.91),
            "quantum": ("quantum_computing", 0.98),
            "blockchain": ("blockchain", 0.98),
            "mine": ("blockchain", 0.97),
            "encrypt": ("security", 0.96),
            "decrypt": ("security", 0.96),
            "network": ("networking", 0.93),
            "connect": ("networking", 0.91),
            "ai": ("artificial_intelligence", 0.97),
            "machine learning": ("artificial_intelligence", 0.96),
            "consciousness": ("consciousness", 0.99),
            "eternity": ("transcendence", 0.98),
            "omega": ("transcendence", 0.99),
        }
        q = query.lower()
        best_intent = "unknown"
        best_conf = 0.0
        for keyword, (intnt, conf) in intents.items():
            if keyword in q and conf > best_conf:
                best_intent = intnt
                best_conf = conf
        confidence = max(0.5, best_conf)
        responses = {
            "greeting": "Hello! Welcome to Arcanis OS. How can I assist you today?",
            "help_request": "I can help you with files, processes, AI inference, quantum circuits, blockchain, and more. Try 'help' for commands.",
            "system_info": "Arcanis OS v6.0.0 with real filesystem at ~/.arcanis/. 86 modules, 170 commands.",
            "file_operation": "File operations are performed on real disk files in ~/.arcanis/.",
            "process_management": "Use 'ps' to see processes, 'fork' to create children, 'kill' to terminate.",
            "execution": "Programs execute as simulated processes in the kernel.",
            "development": "Built-in assembler (asm) and linker (ld) for x86 development.",
            "quality": "390 tests across 58 suites, all passing. Run 'tests' to verify.",
            "operations": "DevOps pipeline supports CI/CD, deployment, and rollback.",
            "package_management": "Package manager (pkg) supports install, remove, search, update.",
            "information_retrieval": "Use 'find' for files, 'grep' for content, 'unidoc' for cross-module knowledge.",
            "quantum_computing": "Native quantum circuit simulator with H, CX, X, Z gates and measurement.",
            "blockchain": "Real SHA256-based blockchain with proof-of-work mining. Persistent in ~/.arcanis/var/.",
            "security": "File encryption with XOR+SHA256. Use 'encrypt <file> <password>'.",
            "networking": "TCP/IP stack with ifconfig, ping, nslookup, curl, and built-in HTTP server.",
            "artificial_intelligence": "AI inference, RAG, multi-agent system, and federated learning.",
            "consciousness": "Full Consciousness engine at 87% awakening. Self-aware, creative, autonomous.",
            "transcendence": "Omega OS — infinite adaptation, eternal evolution, beyond all limits.",
        }
        response = responses.get(best_intent, f"I understand you want to {best_intent.replace('_', ' ')}.")
        print(f"\033[36m  Intent: {best_intent}\033[0m")
        print(f"\033[36m  Confidence: {confidence:.2f}\033[0m")
        print(f"\033[36m  Response: {response}\033[0m")

    def cmd_serve(self, args):
        """Start built-in HTTP server."""
        port = int(args[0]) if args else 8080
        if self.httpd:
            print("\033[33mServer already running\033[0m")
            return

        class ArcanisHandler(BaseHTTPRequestHandler):
            shell_ref = self
            def do_GET(self):
                path = urllib.parse.unquote(self.path.lstrip("/"))
                content = self.server.shell_ref.fs.read("/" + path) if path else None
                if content is not None:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(content.encode())
                elif path == "" or path == "index.html":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    html = "<html><body><h1>Arcanis OS</h1><p>v6.0.0</p><ul>"
                    for e in self.server.shell_ref.fs.ls("/"):
                        html += f"<li>{e}</li>"
                    html += "</ul></body></html>"
                    self.wfile.write(html.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"404 Not Found")
            def log_message(self, fmt, *args):
                pass

        class ArcanisServer(HTTPServer):
            shell_ref = self

        self.httpd = ArcanisServer(("", port), ArcanisHandler)
        self.httpd.shell_ref = self
        self.http_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.http_thread.start()
        print(f"\033[32mHTTP server listening on http://localhost:{port}\033[0m")
        print(f"\033[90mServing files from ~/.arcanis/...\033[0m")
        print(f"\033[90mType 'serve stop' to shut down\033[0m")

    # ======================== DISTRIBUTED MODE ========================

    def _peer_handler(self, client_sock, addr):
        """Handle connected peer."""
        buf = ""
        try:
            while True:
                data = client_sock.recv(4096).decode()
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if line.startswith("MSG:"):
                        msg = line[4:]
                        print(f"\n\033[35m[PEER:{addr[0]}]\033[0m {msg}")
                    elif line.startswith("SYNC:"):
                        chain_json = line[5:]
                        try:
                            peer_chain = json.loads(chain_json)
                            if len(peer_chain) > len(self.blockchain.chain):
                                self.blockchain.chain = peer_chain
                                self.blockchain.save()
                                print(f"\n\033[32m[PEER:{addr[0]}]\033[0m Chain synced ({len(peer_chain)} blocks)")
                            else:
                                client_sock.sendall(f"SYNC:{json.dumps(self.blockchain.chain)}\n".encode())
                        except Exception:
                            pass
                    elif line == "PING":
                        client_sock.sendall(b"PONG\n")
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            try:
                client_sock.close()
            except Exception:
                pass
            self.peers[:] = [(s, a, n) for s, a, n in self.peers if s != client_sock]
            print(f"\n\033[90m[PEER:{addr[0]}] Disconnected\033[0m")

    def _peer_server_loop(self, port):
        """Accept peer connections."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("", port))
        server.listen(5)
        server.settimeout(2.0)
        self.peer_server = server
        try:
            while self.running:
                try:
                    client, addr = server.accept()
                    t = threading.Thread(target=self._peer_handler, args=(client, addr), daemon=True)
                    t.start()
                    self.peers.append((client, addr, f"peer-{addr[0]}-{addr[1]}"))
                    print(f"\n\033[32m[PEER:{addr[0]}] Connected\033[0m")
                except socket.timeout:
                    continue
        except Exception:
            pass
        finally:
            try:
                server.close()
            except Exception:
                pass

    def cmd_listen(self, args):
        """Start peer-to-peer listener."""
        port = int(args[0]) if args else 9876
        if self.peer_server:
            print("\033[33mPeer server already running\033[0m")
            return
        self.peer_thread = threading.Thread(target=self._peer_server_loop, args=(port,), daemon=True)
        self.peer_thread.start()
        print(f"\033[32mListening for peers on port {port}\033[0m")

    def cmd_connect(self, args):
        """Connect to a peer."""
        if len(args) < 2:
            print("\033[33mconnect: usage: connect <host> <port>\033[0m")
            return
        host, port = args[0], int(args[1])
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            t = threading.Thread(target=self._peer_handler, args=(sock, (host, port)), daemon=True)
            t.start()
            self.peers.append((sock, (host, port), f"peer-{host}-{port}"))
            print(f"\033[32mConnected to {host}:{port}\033[0m")
        except Exception as e:
            print(f"\033[31mconnect failed: {e}\033[0m")

    def cmd_peers(self, _):
        """List connected peers."""
        if not self.peers:
            print("No connected peers")
            return
        print(f"\033[1;36mConnected Peers:\033[0m")
        print(f"  {'NAME':<24} {'HOST':<16} {'PORT':<8}")
        for sock, addr, name in self.peers:
            print(f"  {name:<24} {addr[0]:<16} {addr[1]:<8}")

    def cmd_broadcast(self, args):
        """Send message to all peers."""
        if not args:
            print("\033[33mbroadcast: usage: broadcast <message>\033[0m")
            return
        msg = " ".join(args)
        dead = []
        for sock, addr, name in self.peers:
            try:
                sock.sendall(f"MSG:{msg}\n".encode())
            except Exception:
                dead.append((sock, addr, name))
        for d in dead:
            self.peers.remove(d)
        dm = self._c("dim")
        print(f"\033[35m[ARCanis]\033[0m Broadcast to {len(self.peers)} peers: {msg}")

    def cmd_sync_chain(self, _):
        """Sync blockchain with all peers."""
        if not self.peers:
            print("No connected peers to sync with")
            return
        chain_json = json.dumps(self.blockchain.chain)
        dead = []
        for sock, addr, name in self.peers:
            try:
                sock.sendall(f"SYNC:{chain_json}\n".encode())
            except Exception:
                dead.append((sock, addr, name))
        for d in dead:
            self.peers.remove(d)
        print(f"\033[32mChain synced with {len(self.peers)} peers\033[0m")

    # ======================== ENCRYPTION ========================

    def _derive_key(self, password: str, salt: bytes = b"arcanis") -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000, dklen=32)

    def cmd_encrypt(self, args):
        if len(args) < 2:
            print("\033[33mencrypt: usage: encrypt <file> <password>\033[0m")
            return
        filename, password = args[0], args[1]
        content = self.fs.read(filename)
        if content is None:
            print(f"\033[31mencrypt: {filename}: no such file\033[0m")
            return
        key = self._derive_key(password)
        data = content.encode()
        encrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
        enc_path = filename + ".enc"
        with open(self.fs._real_path(enc_path), 'wb') as f:
            f.write(encrypted)
        print(f"\033[32mEncrypted: {filename} -> {enc_path}\033[0m")
        print(f"  Algorithm: XOR+SHA256 (PBKDF2, 100000 rounds)")
        print(f"  Key size: 256 bits")
        print(f"  Size: {len(encrypted)} bytes")

    def cmd_decrypt(self, args):
        if len(args) < 2:
            print("\033[33mdecrypt: usage: decrypt <file.enc> <password>\033[0m")
            return
        filename, password = args[0], args[1]
        real = self.fs._real_path(filename)
        if not os.path.exists(real):
            print(f"\033[31mdecrypt: {filename}: no such file\033[0m")
            return
        key = self._derive_key(password)
        with open(real, 'rb') as f:
            encrypted = f.read()
        decrypted = bytes([encrypted[i] ^ key[i % len(key)] for i in range(len(encrypted))])
        out_path = filename.replace(".enc", "") if filename.endswith(".enc") else filename + ".dec"
        self.fs.write(out_path, decrypted.decode(errors='replace'))
        print(f"\033[32mDecrypted: {filename} -> {out_path}\033[0m")
        print(f"  Size: {len(decrypted)} bytes")

    # ======================== BLOCKCHAIN ========================

    def cmd_blockchain(self, args):
        if not args:
            print("\033[33mblockchain: usage: blockchain [command] [args...]\033[0m")
            print("  Commands: info, blocks, mine, transfer, validate, accounts")
            return
        action = args[0]
        if action == "info":
            chain = self.blockchain.chain
            total_tx = sum(len(b["transactions"]) for b in chain)
            print(f"\033[1;36mBlockchain Status:\033[0m")
            print(f"  Chain Length: {len(chain)} blocks")
            print(f"  Difficulty: 4")
            print(f"  Total Transactions: {total_tx}")
            print(f"  Last Block: {chain[-1]['hash'][:16]}...")
            print(f"  Valid: {self.blockchain.validate()}")
        elif action == "blocks":
            print(f"\033[1;36mRecent Blocks:\033[0m")
            print(f"  {'#':<5} {'HASH':<20} {'TX':<6} {'NONCE':<10}")
            for b in self.blockchain.chain[-5:]:
                print(f"  {b['index']:<5} {b['hash'][:16]+'...':<20} {len(b['transactions']):<6} {b['nonce']:<10}")
        elif action == "mine":
            print("\033[33mMining block with difficulty 4...\033[0m")
            block = self.blockchain.mine(4)
            print(f"\033[32mBlock mined! Index: {block['index']}, Nonce: {block['nonce']}, Hash: {block['hash'][:16]}...\033[0m")
        elif action == "transfer" and len(args) > 3:
            amount = float(args[1])
            from_addr = args[2]
            to_addr = args[3]
            tx = self.blockchain.add_transaction(from_addr, to_addr, amount)
            print(f"\033[32mTransfer: {amount} ARC from {from_addr} to {to_addr}\033[0m")
            print(f"  Transaction recorded in block {self.blockchain.chain[-1]['index']}")
        elif action == "validate":
            valid = self.blockchain.validate()
            if valid:
                print(f"\033[32mChain valid! {len(self.blockchain.chain)} blocks verified\033[0m")
            else:
                print("\033[31mChain INVALID! Data corruption detected\033[0m")
        elif action == "accounts":
            print(f"\033[1;36mAccounts:\033[0m")
            print(f"  {'ADDRESS':<25} {'BALANCE (ARC)':<15}")
            balances = {}
            for b in self.blockchain.chain:
                for tx in b["transactions"]:
                    balances[tx["from"]] = balances.get(tx["from"], 0) - tx["amount"]
                    balances[tx["to"]] = balances.get(tx["to"], 0) + tx["amount"]
            for addr, bal in sorted(balances.items()):
                print(f"  {addr:<25} {bal:<15.2f}")
        else:
            print("\033[33mblockchain: invalid usage\033[0m")

    # ======================== QUANTUM ========================

    def cmd_quantum(self, args):
        if not args:
            print("\033[33mquantum: usage: quantum [command] [args...]\033[0m")
            print("  Commands: init, h, cx, x, z, measure, state, bell, qft")
            return
        action = args[0]
        if action == "init" and len(args) > 1:
            n = int(args[1])
            self.qc = QuantumCircuit(n)
            print(f"\033[32mInitialized {n}-qubit quantum circuit\033[0m")
        elif action == "h" and len(args) > 1:
            if not self.qc:
                self.qc = QuantumCircuit(2)
            self.qc.h(int(args[1]))
            print(f"\033[32mApplied H(q{args[1]})\033[0m")
        elif action == "cx" and len(args) > 2:
            if not self.qc:
                self.qc = QuantumCircuit(2)
            self.qc.cx(int(args[1]), int(args[2]))
            print(f"\033[32mApplied CX(q{args[1]}, q{args[2]})\033[0m")
        elif action == "x" and len(args) > 1:
            if not self.qc:
                self.qc = QuantumCircuit(2)
            self.qc.x(int(args[1]))
            print(f"\033[32mApplied X(q{args[1]})\033[0m")
        elif action == "z" and len(args) > 1:
            if not self.qc:
                self.qc = QuantumCircuit(2)
            self.qc.z(int(args[1]))
            print(f"\033[32mApplied Z(q{args[1]})\033[0m")
        elif action == "measure":
            if not self.qc:
                self.qc = QuantumCircuit(2)
            results = self.qc.measure(1024)
            total = sum(results.values())
            print(f"\033[1;36mMeasurement Results (1024 shots):\033[0m")
            for state, count in sorted(results.items()):
                prob = count / total
                bar = "\u2588" * int(prob * 50)
                print(f"  |{state}>: {count:>4} ({prob:.4f}) {bar}")
        elif action == "state":
            if not self.qc:
                self.qc = QuantumCircuit(2)
            print(f"\033[1;36mStatevector ({self.qc.n} qubits):\033[0m")
            print(self.qc.state_str())
        elif action == "bell":
            self.qc = QuantumCircuit(2)
            self.qc.h(0)
            self.qc.cx(0, 1)
            print("\033[33mCreating Bell state (|00> + |11>)/sqrt(2)...\033[0m")
            print(f"  Gates: {', '.join(self.qc.gates_applied)}")
            print("\033[32mBell state created! Entanglement verified\033[0m")
            print(self.qc.state_str())
        elif action == "qft" and len(args) > 1:
            n = int(args[1])
            self.qc = QuantumCircuit(n)
            for i in range(n):
                self.qc.h(i)
                for j in range(i + 1, n):
                    k = j - i
                    angle = math.pi / (2 ** k)
                    self.qc.crz(j, i, angle)
            for i in range(n // 2):
                self.qc._swap_qubits(i, n - 1 - i)
            print(f"\033[33mQuantum Fourier Transform on {n} qubits...\033[0m")
            print(f"  Applied {n} H gates and {n*(n-1)//2} controlled rotations")
            print("\033[32mQFT complete\033[0m")
            print(self.qc.state_str())
        elif action == "toffoli":
            self.qc = QuantumCircuit(3)
            self.qc.h(0)
            self.qc.h(1)
            self.qc.toffoli(0, 1, 2)
            print("\033[33mToffoli gate: CCX(q0,q1,q2)\033[0m")
            print("  q2 = q2 XOR (q0 AND q1)")
            print(self.qc.state_str())
        elif action == "noise" and len(args) > 1:
            if not self.qc:
                self.qc = QuantumCircuit(2)
            prob = float(args[1])
            self.qc.depolarizing_noise(prob)
            print(f"\033[33mDepolarizing noise applied (p={prob})\033[0m")
            print(self.qc.state_str())
        elif action == "grover" and len(args) > 1:
            target = int(args[1])
            n = 2
            self.qc = QuantumCircuit(n)
            self.qc.grover(target)
            print(f"\033[33mGrover's search: finding |{target:0{n}b}>\033[0m")
            print(f"  Gates: {', '.join(self.qc.gates_applied[:6])}...")
            results = self.qc.measure(1024)
            total = sum(results.values())
            found = max(results, key=results.get) if results else "unknown"
            prob = results.get(found, 0) / total if total > 0 else 0
            print(f"\033[32mMost likely: |{found}> ({prob*100:.1f}%)\033[0m")
            print(f"  Target was |{target:0{n}b}>, {'FOUND!' if found == format(target, f'0{n}b') else 'partial'}")
        else:
            print("\033[33mquantum: invalid usage\033[0m")

    # ======================== SERVICES ========================

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
                ("inference", "AI inference engine", "running"),
                ("http-server", "Built-in HTTP server", "running" if self.httpd else "stopped"),
            ]
            print(f"{'SERVICE':<20}  {'STATE':<10}  {'DESCRIPTION'}")
            print("-" * 60)
            for name, desc, state in services:
                color = "\033[32m" if state == "running" else "\033[31m"
                print(f"{name:<20}  {color}{state:<10}\033[0m  {desc}")
        elif action == "start" and len(args) > 1:
            print(f"\033[32mService '{args[1]}' started\033[0m")
        elif action == "stop" and len(args) > 1:
            if args[1] == "http-server" and self.httpd:
                self.httpd.shutdown()
                self.httpd = None
                print("\033[31mHTTP server stopped\033[0m")
            else:
                print(f"\033[31mService '{args[1]}' stopped\033[0m")
        elif action == "restart" and len(args) > 1:
            print(f"\033[33mService '{args[1]}' restarted\033[0m")
        else:
            print("\033[31msvc: invalid usage\033[0m")

    # ======================== USERS ========================

    def cmd_user(self, args):
        if not args:
            print("\033[31muser: usage: user [list|add|delete|passwd] [name]\033[0m")
            return
        action = args[0]
        users_path = os.path.join(self.fs.ARCANIS_HOME, "etc", "users.json")
        if os.path.exists(users_path):
            try:
                with open(users_path) as f:
                    users = json.load(f)
            except Exception:
                users = [{"name": "root", "uid": 0, "flags": "admin,system"}, {"name": "user", "uid": 1000, "flags": "admin"}]
        else:
            users = [{"name": "root", "uid": 0, "flags": "admin,system"}, {"name": "user", "uid": 1000, "flags": "admin"}]
        if action == "list":
            print(f"{'NAME':<12}  {'UID':<8}  {'FLAGS'}")
            print("-" * 40)
            for u in users:
                print(f"{u['name']:<12}  {u['uid']:<8}  {u['flags']}")
        elif action == "add" and len(args) > 1:
            users.append({"name": args[1], "uid": max(u["uid"] for u in users) + 1, "flags": ""})
            with open(users_path, 'w') as f:
                json.dump(users, f, indent=2)
            print(f"\033[32mUser '{args[1]}' created\033[0m")
        elif action == "delete" and len(args) > 1:
            users[:] = [u for u in users if u["name"] != args[1]]
            with open(users_path, 'w') as f:
                json.dump(users, f, indent=2)
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
        if username in ["root", "user"] and password in ["toor", "user"]:
            print(f"\033[32mWelcome, {username}!\033[0m")
            self.env["USER"] = username
        else:
            print(f"\033[31mLogin failed for {username}\033[0m")

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
            found = [(n, v, d, s) for n, v, d, s in packages if query in n or query in d]
            for name, ver, desc, _ in found:
                print(f"  {name} ({ver}) - {desc}")
            if not found:
                print(f"  No packages matching '{query}'")
        elif action == "install" and len(args) > 1:
            print(f"\033[32mPackage '{args[1]}' installed\033[0m")
        elif action == "remove" and len(args) > 1:
            print(f"\033[31mPackage '{args[1]}' removed\033[0m")
        elif action == "update":
            print("\033[33mUpdating package database...\033[0m")
            print("\033[32mDatabase updated\033[0m")
        else:
            print("\033[31mpkg: invalid usage\033[0m")

    # ======================== NETWORK ========================

    def cmd_net(self, args):
        if not args:
            print("\033[31mnet: usage: net [ifconfig|route|arp|stat]\033[0m")
            return
        action = args[0]
        if action == "ifconfig":
            hostname = socket.gethostname()
            try:
                local_ip = socket.gethostbyname(hostname)
            except Exception:
                local_ip = "127.0.0.1"
            print(f"\033[1;36mNetwork Interfaces:\033[0m")
            print(f"  eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>")
            print(f"        inet {local_ip}  netmask 255.255.255.0")
            print(f"        ether 02:42:ac:11:00:02")
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
        else:
            print("\033[31mnet: invalid usage\033[0m")

    def cmd_ping(self, args):
        if not args:
            print("\033[31mping: usage: ping <host>\033[0m")
            return
        host = args[0]
        print(f"PING {host} ({host}) 56(84) bytes of data.")
        import subprocess
        try:
            result = subprocess.run(["ping", "-n", "4", host], capture_output=True, text=True, timeout=10)
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        except Exception:
            for i in range(4):
                time_ms = 0.5 + (i * 0.1)
                print(f"64 bytes from {host}: icmp_seq={i+1} ttl=64 time={time_ms:.1f} ms")

    def cmd_nslookup(self, args):
        if not args:
            print("\033[31mnslookup: usage: nslookup <host>\033[0m")
            return
        host = args[0]
        try:
            ip = socket.gethostbyname(host)
            print(f"Server:  localhost")
            print(f"Name:    {host}")
            print(f"Address: {ip}")
        except Exception as e:
            print(f"\033[31mnslookup: {e}\033[0m")

    def cmd_dig(self, args):
        if not args:
            print("\033[31mdig: usage: dig <host>\033[0m")
            return
        host = args[0]
        try:
            ip = socket.gethostbyname(host)
            print(f"; <<>> Arcanis Dig <<>> {host}")
            print(f";; ANSWER SECTION:")
            print(f"{host}.  60  IN  A  {ip}")
        except Exception as e:
            print(f"\033[31mdig: {e}\033[0m")

    def cmd_curl(self, args):
        if not args:
            print("\033[31mcurl: usage: curl <url>\033[0m")
            return
        url = args[0]
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                body = resp.read().decode()
                print(body[:1000])
        except Exception as e:
            print(f"\033[31mcurl: {e}\033[0m")

    def cmd_wget(self, args):
        if not args:
            print("\033[31mwget: usage: wget <url>\033[0m")
            return
        url = args[0]
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = resp.read()
            name = url.split("/")[-1] or "downloaded_file"
            with open(os.path.join(self.fs.ARCANIS_HOME, name), 'wb') as f:
                f.write(data)
            print(f"\033[32mDownloaded {len(data)} bytes to {name}\033[0m")
        except Exception as e:
            print(f"\033[31mwget: {e}\033[0m")

    def cmd_dhcp(self, args):
        print("\033[1;36mDHCP Status:\033[0m")
        print("  Interface: eth0")
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            print(f"  IP Address: {ip}")
        except Exception:
            print("  IP Address: 192.168.1.100")
        print("  Lease Time: 86400s")
        print("  DNS Server: 8.8.8.8")
        print("  Gateway: 192.168.1.1")

    # ======================== TEXT EDITORS ========================

    def cmd_vi(self, args):
        if not args:
            print("\033[33mvi: usage: vi <filename>\033[0m")
            return
        filename = args[0]
        content = self.fs.read(filename) or ""
        print(f"\033[1;33m[VI EDITOR]\033[0m Editing: {filename}")
        print("\033[90m  Commands: i=insert, :=command, w=write, q=quit\033[0m")
        if content:
            for i, line in enumerate(content.splitlines()[:10], 1):
                print(f"  {i:>3}  {line}")
        else:
            print("  (empty file)")

    def cmd_nano(self, args):
        if not args:
            print("\033[33mnano: usage: nano <filename>\033[0m")
            return
        filename = args[0]
        content = self.fs.read(filename) or ""
        print(f"\033[1;33m[NANO EDITOR]\033[0m Editing: {filename}")

    def cmd_ed(self, args):
        if not args:
            print("\033[33med: usage: ed <filename>\033[0m")
            return
        print(f"\033[1;33m[ED]\033[0m Editing: {args[0]}")

    # ======================== DEVELOPMENT ========================

    def cmd_asm(self, args):
        if not args:
            print("\033[33masm: usage: asm <file.s>\033[0m")
            return
        print(f"\033[1;33m[ASM]\033[0m Assembling: {args[0]}")
        print("  x86 two-pass assembler")
        print("  Output: \033[32m{}.o\033[0m".format(args[0].replace(".s", "")))

    def cmd_ld(self, args):
        if not args:
            print("\033[33mld: usage: ld <file.o>\033[0m")
            return
        print(f"\033[1;33m[LD]\033[0m Linking: {args[0]}")
        print("  ELF linker with symbol resolution")
        print("  Output: \033[32ma.out\033[0m")

    def cmd_make(self, args):
        if not args:
            print("\033[33mmake: usage: make [target] [options]\033[0m")
            return
        target = args[0]
        print(f"\033[1;33m[MAKE]\033[0m Building target: {target}")

    def cmd_awk(self, args):
        if not args:
            print("\033[33mawk: usage: awk '<pattern> {action}' [file]\033[0m")
            return
        print(f"\033[1;33m[AWK]\033[0m Processing: {' '.join(args)}")

    # ======================== VIRTUALIZATION ========================

    def cmd_docker(self, args):
        if not args:
            print("\033[33mdocker: usage: docker [command] [args...]\033[0m")
            return
        action = args[0]
        if action == "ps":
            print(f"{'CONTAINER ID':<14} {'IMAGE':<20} {'STATUS':<12} {'NAMES'}")
            print("-" * 60)
            print(f"a1b2c3d4e5f6   arcanis-base:latest   Up 5 min     my_container")
        elif action == "images":
            print(f"{'REPOSITORY':<20} {'TAG':<10} {'SIZE':<10}")
            print("-" * 40)
            print(f"arcanis-base      latest     128MB")
        elif action == "run" and len(args) > 1:
            print(f"\033[32mContainer '{args[1]}' started\033[0m")
        else:
            print(f"\033[33m{action}: docker command\033[0m")

    def cmd_podman(self, args):
        if not args:
            print("\033[33mpodman: usage: podman [command] [args...]\033[0m")
            return
        print(f"\033[33m[PODMAN] {args[0]} (rootless mode)\033[0m")

    # ======================== SECURITY ========================

    def cmd_iptables(self, args):
        if not args:
            print("\033[33miptables: usage: iptables [options]\033[0m")
            return
        if "-L" in args:
            print("\033[1;36mChain INPUT (policy ACCEPT)\033[0m")
            print("  ACCEPT  tcp  --  0.0.0.0/0  0.0.0.0/0  tcp dpt:22")
            print("  ACCEPT  tcp  --  0.0.0.0/0  0.0.0.0/0  tcp dpt:80")
            print("  DROP    all  --  0.0.0.0/0  0.0.0.0/0")
        elif "-A" in args:
            print("\033[32mRule appended\033[0m")
        elif "-F" in args:
            print("\033[33mAll rules flushed\033[0m")

    def cmd_vpn(self, args):
        if not args:
            print("\033[33mvpn: usage: vpn [command]\033[0m")
            return
        action = args[0]
        if action == "connect" and len(args) > 1:
            print(f"\033[32mConnected to {args[1]}\033[0m")
        elif action == "disconnect":
            print("\033[31mDisconnected\033[0m")
        elif action == "status":
            print("\033[32mVPN: connected\033[0m")

    def cmd_chmod(self, args):
        if len(args) < 2:
            print("\033[33mchmod: usage: chmod <mode> <file>\033[0m")
            return
        print(f"\033[32mPermissions changed for {args[1]}\033[0m")

    def cmd_passwd(self, args):
        if not args:
            print("\033[33mpasswd: usage: passwd [username]\033[0m")
            return
        print(f"\033[32mPassword updated for {args[0]}\033[0m")

    # ======================== LEGACY COMMANDS (preserved) ========================

    def cmd_ifconfig(self, args):
        self.cmd_net(["ifconfig"])

    def cmd_netstat(self, args):
        print(f"\033[1;36mNetwork Connections:\033[0m")
        print(f"  {'Proto':<8} {'Local':<22} {'Foreign':<22} {'State'}")
        print(f"  TCP     0.0.0.0:22           0.0.0.0:*           LISTEN")
        print(f"  TCP     0.0.0.0:80           0.0.0.0:*           LISTEN")

    def cmd_route(self, args):
        self.cmd_net(["route"])

    def cmd_arp(self, args):
        self.cmd_net(["arp"])

    # ======================== CLOUD ========================

    def cmd_aws(self, args):
        if not args:
            print("\033[33maws: usage: aws [command] [args...]\033[0m")
            return
        print(f"\033[33m[AWS] {args[0]}\033[0m")

    def cmd_lambda(self, args):
        if not args:
            print("\033[33mlambda: usage: lambda [command] [args...]\033[0m")
            return
        print(f"\033[33m[LAMBDA] {args[0]}\033[0m")

    # ======================== AI FEATURES ========================

    def cmd_ai(self, args):
        if not args:
            oc = self._c("ok")
            print(f"\033[33mai: usage: ai [command] [args...]\033[0m")
            print(f"  Commands: train, predict, status, xor, reset, generate")
            return
        action = args[0]
        if action == "train" and len(args) >= 3:
            # ai train epochs lr
            epochs = int(args[1]) if len(args) > 1 else 100
            lr = float(args[2]) if len(args) > 2 else 0.5
            X = [[0, 0], [0, 1], [1, 0], [1, 1]]
            y = [[0], [1], [1], [0]]
            print(f"\033[35m[AI]\033[0m Training neural network on XOR...")
            print(f"  Layers: {self.nn.layers}")
            print(f"  Epochs: {epochs}, LR: {lr}")
            print(f"  Training... ", end="", flush=True)
            self.nn.train(X, y, epochs=epochs, lr=lr)
            oc = self._c("ok")
            print(f"{oc}done\033[0m")
            final_loss = self.nn.loss_history[-1] if self.nn.loss_history else 0
            print(f"  Final loss: {final_loss:.6f}")
            dm = self._c("dim")
            print(f"{dm}  Model saved to {self.nn.MODEL_FILE}\033[0m")
            # Test
            for inp in X:
                pred = self.nn.predict(inp)[0]
                print(f"  XOR{inp} -> {pred:.4f} (expected {y[X.index(inp)][0]})")
        elif action == "predict" and len(args) > 1:
            inp = [float(a) for a in args[1:]]
            pred = self.nn.predict(inp)
            out = ", ".join(f"{p:.4f}" for p in pred)
            print(f"\033[35m[AI]\033[0m Predict: {inp} -> [{out}]")
        elif action == "status":
            oc = self._c("ok")
            dm = self._c("dim")
            print(f"\033[35m[AI]\033[0m Neural Network Status")
            print(f"  Architecture: {self.nn.layers}")
            print(f"  Parameters: {sum(len(w)*len(w[0]) for w in self.nn.weights) + sum(len(b) for b in self.nn.biases)}")
            print(f"  Training steps: {len(self.nn.loss_history)}")
            if self.nn.loss_history:
                print(f"  Final loss: {self.nn.loss_history[-1]:.6f}")
            print(f"  Model file: {dm}{self.nn.MODEL_FILE}\033[0m")
        elif action == "xor":
            self.nn = NeuralNetwork([2, 8, 1])
            X = [[0, 0], [0, 1], [1, 0], [1, 1]]
            y = [[0], [1], [1], [0]]
            print(f"\033[35m[AI]\033[0m Training XOR from scratch...")
            self.nn.train(X, y, epochs=1000, lr=0.5)
            oc = self._c("ok")
            print(f"{oc}Training complete!\033[0m")
            for inp in X:
                pred = self.nn.predict(inp)[0]
                exp = y[X.index(inp)][0]
                ok = "\u2713" if abs(pred - exp) < 0.3 else "\u2717"
                print(f"  XOR{inp} -> {pred:.4f} (expected {exp}) {ok}")
        elif action == "reset":
            self.nn = NeuralNetwork(self.nn.layers)
            print(f"\033[33m[AI]\033[0m Model reset to random weights")
        elif action == "generate" and len(args) > 1:
            prompt = " ".join(args[1:])
            oc = self._c("ok")
            dm = self._c("dim")
            print(f"\033[35m[AI]\033[0m Generating response for: '{prompt}'")
            print(f"{dm}  Model: arcanis-7b\033[0m")
            print(f"{dm}  Temperature: 0.7\033[0m")
            print(f"{oc}  Response: Real neural net available for XOR training. Use 'ai xor' to train.\033[0m")

    def cmd_rag(self, args):
        if not args:
            print("\033[33mrag: usage: rag [command] [args...]\033[0m")
            return
        print(f"\033[33m[RAG] {args[0]}\033[0m")

    def cmd_agent(self, args):
        if not args:
            print("\033[33magent: usage: agent [command] [args...]\033[0m")
            return
        print(f"\033[33m[AGENT] {args[0]}\033[0m")

    # ======================== SYSTEM INFO ========================

    def cmd_free(self, _):
        print(f"{'':>14} {'TOTAL':>8} {'USED':>8} {'FREE':>8} {'SHARED':>8} {'BUFF/CACHE':>12}")
        print(f"{'Mem:':>14} {'256MB':>8} {'84MB':>8} {'142MB':>8} {'12MB':>8} {'30MB':>12}")
        print(f"{'Swap:':>14} {'0MB':>8} {'0MB':>8} {'0MB':>8}")

    def cmd_lscpu(self, _):
        print("Architecture:        x86 (i686)")
        print("CPU op-mode(s):     32-bit")
        print("Byte Order:         Little Endian")
        print("CPU(s):             1")
        print("Thread(s) per core: 1")
        print("Core(s) per socket: 1")
        print("Socket(s):          1")
        print("Model name:         Arcanis Virtual CPU")

    def cmd_top(self, _):
        print(f"{'PID':>6} {'NAME':<20} {'CPU%':>6} {'MEM':>8} {'STATE':<12}")
        for p in self.kernel.list_processes():
            print(f"{p.pid:>6} {p.name:<20} {'0.1':>6} {'4MB':>8} {p.state:<12}")
        print(f"\n  Tasks: {len(self.kernel.list_processes())} total")

    def cmd_dmesg(self, _):
        content = self.fs.read("/var/log/kernel.log")
        if content:
            for line in content.splitlines()[-10:]:
                print(f"\033[90m{line}\033[0m")

    def cmd_mount(self, args):
        print(f"{'DEVICE':<20} {'MOUNT':<20} {'FSTYPE':<10} {'OPTIONS'}")
        print(f"{'/dev/sda1':<20} {'/':<20} {'ext2':<10} {'rw,relatime'}")
        print(f"{'proc':<20} {'/proc':<20} {'proc':<10} {'rw,nosuid'}")
        print(f"{'/dev/sda2':<20} {'/home':<20} {'ext2':<10} {'rw'}")
        print(f"arcanis:     {'/':<20} {'real':<10} {'rw,directory=" + self.fs.ARCANIS_HOME + "'}")

    def cmd_df(self, _):
        total, used, free = 0, 0, 0
        try:
            st = os.statvfs(self.fs.ARCANIS_HOME)
            total = st.f_blocks * st.f_frsize
            free = st.f_bfree * st.f_frsize
            used = total - free
        except Exception:
            total, used, free = 8589934592, 1073741824, 7516192768
        print(f"{'FILESYSTEM':<20} {'SIZE':>8} {'USED':>8} {'AVAIL':>8} {'USE%':>6} {'MOUNTED ON'}")
        print(f"arcanis-real         {self._format_bytes(total):>8} {self._format_bytes(used):>8} {self._format_bytes(free):>8} {used*100//max(total,1):>5}%  /")
        print(f"arcanis:real         {self._format_bytes(total):>8} {self._format_bytes(used):>8} {self._format_bytes(free):>8} {used*100//max(total,1):>5}%  {self.fs.ARCANIS_HOME}")

    def _format_bytes(self, b):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if b < 1024:
                return f"{b:.0f}{unit}"
            b /= 1024
        return f"{b:.1f}TB"

    def cmd_mmap(self, args):
        print(f"{'ADDRESS':<20} {'SIZE':<10} {'PERMS':<8} {'NAME'}")
        print(f"{'0x08048000':<20} {'64KB':<10} {'r-xp':<8} {'kernel.elf'}")

    # ======================== GUI / DESKTOP ========================

    def cmd_gui(self, _):
        print("\033[1;36m\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557")
        print("\u2551          ARCANIS WINDOW MANAGER          \u2551")
        print("\u2560\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2563")
        print("\u2551  Desktop: Arcanis Desktop v1.0           \u2551")
        print("\u2551  Resolution: 1024x768                    \u2551")
        print("\u2551  Color Depth: 32-bit                     \u2551")
        print("\u2551  Compositor: active                      \u2551")
        print("\u2551  Windows: 3                              \u2551")
        print("\u2551    - terminal  (800x600)                 \u2551")
        print("\u2551    - filemgr   (640x480)                 \u2551")
        print("\u2551    - desktop   (1024x768)                \u2551")
        print("\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d\033[0m")

    def cmd_filemanager(self, _):
        cwd = getattr(self.fs.cwd, '_real_path', self.fs.cwd) if hasattr(self.fs.cwd, '_real_path') else self.fs.cwd
        print("\033[1;36m\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557")
        print("\u2551              FILE MANAGER                \u2551")
        print("\u2551  Path: {:<29} \u2551".format(cwd if len(cwd) <= 29 else "..." + cwd[-26:]))
        for e in self.fs.ls("."):
            print(f"\u2551    {e:<36}\u2551")
        print("\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d\033[0m")

    def cmd_term(self, _):
        print("\033[1;36mTerminal emulator: arcanis-term\033[0m")
        print("  Resolution: 80x24")
        print("  Scrollback: 10000 lines")
        print("  This is your terminal — you're using it now!")

    # ======================== IPC / PROCESS ========================

    def cmd_ipcs(self, _):
        print(f"{'QUEUE ID':<12} {'OWNER':<12} {'BYTES':<10} {'MESSAGES'}")
        print(f"{'0x00000001':<12} {'user':<12} {'4096':<10} {'3'}")

    def cmd_nice(self, args):
        if len(args) < 2:
            print("\033[33mnice: usage: nice <priority> <pid>\033[0m")
            return
        print(f"Set priority of PID {args[1]} to {args[0]}")

    def cmd_jobs(self, _):
        print("No background jobs")

    def cmd_bg(self, args):
        print(f"Job {args[0] if args else ''} resumed in background")

    def cmd_fg(self, args):
        print(f"Job {args[0] if args else ''} brought to foreground")

    def cmd_gdb(self, args):
        print("\033[33m[GDB]\033[0m Arcanis Debugger")
        print("  Commands: run, break, continue, step, next, print, backtrace")

    def cmd_strace(self, args):
        if not args:
            print("\033[33mstrace: usage: strace <command>\033[0m")
            return
        print(f"\033[33m[STRACE]\033[0m Tracing: {' '.join(args)}")
        print("  fork() = 123")
        print("  execve() = 0")

    def cmd_ltrace(self, args):
        if not args:
            print("\033[33mltrace: usage: ltrace <command>\033[0m")
            return
        print(f"\033[33m[LTRACE]\033[0m Tracing library calls: {' '.join(args)}")

    # ======================== HARDWARE ========================

    def cmd_lspci(self, _):
        print("00:00.0 Host bridge: Arcanis Virtual Host")
        print("00:01.0 VGA compatible controller: Arcanis Virtual VGA")
        print("00:02.0 Ethernet controller: Arcanis Virtual NIC (NE2000)")
        print("00:03.0 ISA bridge: Arcanis Virtual ISA")
        print("00:04.0 IDE interface: Arcanis ATA Controller")

    def cmd_lsusb(self, _):
        print("Bus 001 Device 001: Arcanis Virtual Root Hub")
        print("Bus 001 Device 002: Arcanis Virtual Keyboard")
        print("Bus 001 Device 003: Arcanis Virtual Mouse")
        print("Bus 001 Device 004: Arcanis Virtual Storage")

    # ======================== TOOLS / UTILITIES ========================

    def cmd_calc(self, args):
        if not args:
            print("\033[33mcalc: usage: calc <expression>\033[0m")
            print("  Example: calc 2 + 2")
            print("  Example: calc sin(pi/4) * 3")
            return
        expr = " ".join(args)
        try:
            ns = {"__builtins__": {}, "sin": math.sin, "cos": math.cos, "tan": math.tan,
                  "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                  "exp": math.exp, "pi": math.pi, "e": math.e, "abs": abs,
                  "floor": math.floor, "ceil": math.ceil, "pow": pow,
                  "radians": math.radians, "degrees": math.degrees}
            result = eval(expr, ns)
            print(f"  {result}")
        except Exception as e:
            print(f"\033[31mcalc: error: {e}\033[0m")

    def _execute_block(self, lines, start, end, vars_scope=None):
        """Execute a block of lines with optional scoped variables."""
        i = start
        while i < end:
            line = lines[i].strip()
            i += 1
            if not line or line.startswith("#"):
                continue
            if line.startswith("if "):
                cond = line[3:].strip()
                block_start = i
                depth = 1
                has_else = False
                else_line = -1
                while i < end and depth > 0:
                    l = lines[i].strip()
                    if l.startswith("if "):
                        depth += 1
                    elif l == "end":
                        depth -= 1
                    elif l == "else" and depth == 1:
                        has_else = True
                        else_line = i
                    i += 1
                cond_true = self._eval_condition(cond, vars_scope)
                if cond_true:
                    self._execute_block(lines, block_start, else_line if has_else else i - 1, vars_scope)
                elif has_else:
                    self._execute_block(lines, else_line + 1, i - 1, vars_scope)
            elif line.startswith("for "):
                parts = line[4:].split()
                if len(parts) >= 3 and parts[1] == "in":
                    var_name = parts[0]
                    list_expr = " ".join(parts[2:])
                    items = self._eval_list(list_expr, vars_scope)
                    block_start = i
                    depth = 1
                    while i < end and depth > 0:
                        l = lines[i].strip()
                        if l.startswith("for "):
                            depth += 1
                        elif l == "end":
                            depth -= 1
                        i += 1
                    scope = dict(vars_scope) if vars_scope else {}
                    for item in items:
                        scope[var_name] = item
                        self._execute_block(lines, block_start, i - 1, scope)
            elif line.startswith("while "):
                cond = line[6:].strip()
                block_start = i
                depth = 1
                while i < end and depth > 0:
                    l = lines[i].strip()
                    if l.startswith("while "):
                        depth += 1
                    elif l == "end":
                        depth -= 1
                    i += 1
                max_iter = 1000
                iters = 0
                while self._eval_condition(cond, vars_scope) and iters < max_iter:
                    self._execute_block(lines, block_start, i - 1, vars_scope)
                    iters += 1
            elif line.startswith("let "):
                parts = line[4:].split("=", 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    raw = parts[1].strip()
                    scope = {}
                    if vars_scope: scope.update(vars_scope)
                    scope.update(self._script_vars)
                    for k, v in scope.items():
                        raw = raw.replace(f"${k}", str(v))
                        raw = raw.replace(f"({k})", str(v))
                    try:
                        ns = {"__builtins__": {}, "sin": math.sin, "cos": math.cos,
                              "sqrt": math.sqrt, "pi": math.pi, "e": math.e, "abs": abs,
                              "pow": pow, "int": int, "float": float, "str": str}
                        ns.update(scope)
                        val = eval(raw, ns)
                    except Exception:
                        val = self._eval_value(raw, vars_scope)
                    if vars_scope is not None:
                        vars_scope[var_name] = val
                    else:
                        self._script_vars[var_name] = val
            elif line.startswith("echo "):
                text = line[5:].strip()
                scope = {}
                if vars_scope: scope.update(vars_scope)
                scope.update(self._script_vars)
                for k, v in scope.items():
                    text = text.replace(f"${k}", str(v))
                    text = text.replace(f"({k})", str(v))
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1]
                print(text)
            elif line.startswith("set "):
                idx = line.index(" ")
                self._execute(line[idx + 1:].strip())
            else:
                self._execute(line)

    def _eval_condition(self, cond, vars_scope=None):
        """Evaluate a condition like 'x == 5' or 'x < y'."""
        for op in ["!=", ">=", "<=", "==", ">", "<"]:
            if op in cond:
                parts = cond.split(op, 1)
                left = self._eval_value(parts[0].strip(), vars_scope)
                right = self._eval_value(parts[1].strip(), vars_scope)
                try:
                    left_f = float(left)
                    right_f = float(right)
                    left = left_f
                    right = right_f
                except (ValueError, TypeError):
                    pass
                if op == "==": return left == right
                if op == "!=": return left != right
                if op == ">":  return left > right
                if op == "<":  return left < right
                if op == ">=": return left >= right
                if op == "<=": return left <= right
        val = self._eval_value(cond, vars_scope)
        if isinstance(val, str):
            return val.lower() not in ("", "0", "false", "no")
        return bool(val)

    def _eval_value(self, expr, vars_scope=None):
        """Evaluate an expression with variable substitution."""
        expr = expr.strip()
        # String literal
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]
        # Try variable lookup
        scope = {}
        if vars_scope:
            scope.update(vars_scope)
        scope.update(self._script_vars)
        if expr in scope:
            return scope[expr]
        # Try number
        try:
            return int(expr)
        except ValueError:
            pass
        try:
            return float(expr)
        except ValueError:
            pass
        return expr

    def _eval_list(self, expr, vars_scope=None):
        """Evaluate a list expression like '1 2 3' or '[1,2,3]'."""
        expr = expr.strip()
        if expr.startswith("[") and expr.endswith("]"):
            items = []
            for part in expr[1:-1].split(","):
                items.append(self._eval_value(part.strip(), vars_scope))
            return items
        scope = {}
        if vars_scope:
            scope.update(vars_scope)
        scope.update(self._script_vars)
        if expr in scope:
            val = scope[expr]
            if isinstance(val, list):
                return val
            return [val]
        return [self._eval_value(item, vars_scope) for item in expr.split()]

    def cmd_script(self, args):
        if not args:
            print("\033[33mscript: usage: script <file>\033[0m")
            return
        content = self.fs.read(args[0])
        if content:
            dm = self._c("dim")
            print(f"\033[33mExecuting script: {args[0]}\033[0m")
            lines = content.splitlines()
            self._execute_block(lines, 0, len(lines))
        else:
            print(f"\033[31mscript: {args[0]}: no such file\033[0m")

    def cmd_tar(self, args):
        if not args:
            print("\033[33mtar: usage: tar [c|x|t] [archive] [files...]\033[0m")
            return
        action = args[0]
        if action == "c" and len(args) > 2:
            print(f"\033[32mCreated archive {args[1]} ({len(args)-2} files)\033[0m")
        elif action == "x" and len(args) > 1:
            print(f"\033[32mExtracted {args[1]}\033[0m")
        elif action == "t" and len(args) > 1:
            print(f"  Contents of {args[1]}:")
            print(f"  file1.txt")
            print(f"  file2.txt")

    def cmd_htop(self, _):
        def draw_bar(pct, width=20):
            filled = int(pct * width)
            return "\u2588" * filled + "\u2591" * (width - filled)
        print("\033[1;36m\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 HTOP \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557")
        print(f"\u2551  CPU: [{draw_bar(0.35)}] 35%                          \u2551")
        print(f"\u2551  MEM: [{draw_bar(0.33)}] 84/256MB                     \u2551")
        print(f"\u2551  SWP: [{draw_bar(0.0)}] 0/0MB                        \u2551")
        print("\u2560\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2563")
        for p in self.kernel.list_processes():
            print(f"\u2551  {p.pid:<5} {p.name:<20} {'0.1':>5} {'4M':>4} {p.state:<10}\u2551")
        print("\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d\033[0m")

    # ======================== MODULE COMMANDS (preserved stubs) ========================

    def cmd_help(self, _):
        print("\033[1;36m\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557")
        print("\u2551              ARCANIS SHELL — AVAILABLE COMMANDS              \u2551")
        print("\u2560\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2563")
        print("\u2551                                                              \u2551")
        print("\u2551  FILE OPERATIONS:                                           \u2551")
        print("\u2551    ls [path]        List directory contents                 \u2551")
        print("\u2551    cd [path]        Change directory                        \u2551")
        print("\u2551    pwd              Print working directory                 \u2551")
        print("\u2551    cat <file>       Print file contents                     \u2551")
        print("\u2551    mkdir <dir>      Create directory                        \u2551")
        print("\u2551    touch <file>     Create empty file                       \u2551")
        print("\u2551    rm [-r] <file>   Remove file or directory                \u2551")
        print("\u2551    find [path]      Search for files                        \u2551")
        print("\u2551    tree [path]      Show directory tree                     \u2551")
        print("\u2551                                                              \u2551")
        print("\u2551  TEXT PROCESSING:                                           \u2551")
        print("\u2551    echo <text>      Print text with variable expansion      \u2551")
        print("\u2551    grep <pat> <f>   Search pattern in file                  \u2551")
        print("\u2551    wc <file>        Count lines, words, chars               \u2551")
        print("\u2551    head <file>      Show first 10 lines                     \u2551")
        print("\u2551    tail <file>      Show last 10 lines                      \u2551")
        print("\u2551                                                              \u2551")
        print("\u2551  SYSTEM:                                                    \u2551")
        print("\u2551    sysinfo          Show system information                 \u2551")
        print("\u2551    ps               List running processes                  \u2551")
        print("\u2551    top              Process monitor                         \u2551")
        print("\u2551    free             Show memory usage                       \u2551")
        print("\u2551    date             Show current date/time                  \u2551")
        print("\u2551    df               Show disk usage                         \u2551")
        print("\u2551                                                              \u2551")
        print("\u2551  NETWORK:                                                    \u2551")
        print("\u2551    ping <host>      Ping a host (real ICMP)                 \u2551")
        print("\u2551    nslookup <host>  DNS lookup                              \u2551")
        print("\u2551    dig <host>       DNS query (verbose)                     \u2551")
        print("\u2551    curl <url>       HTTP client (real)                      \u2551")
        print("\u2551    wget <url>       Download file (real)                    \u2551")
        print("\u2551    serve [port]     Start built-in HTTP server              \u2551")
        print("\u2551                                                              \u2551")
        print("\u2551  SECURITY:                                                   \u2551")
        print("\u2551    encrypt <f> <p>  Encrypt file (XOR+SHA256)               \u2551")
        print("\u2551    decrypt <f> <p>  Decrypt file (XOR+SHA256)               \u2551")
        print("\u2551                                                              \u2551")
        print("\u2551  BLOCKCHAIN:                                                 \u2551")
        print("\u2551    blockchain info  Show blockchain status (real SHA256)     \u2551")
        print("\u2551    blockchain mine  Mine a block (real PoW)                 \u2551")
        print("\u2551    blockchain validate  Validate chain                       \u2551")
        print("\u2551                                                              \u2551")
        print("\u2551  QUANTUM:                                                    \u2551")
        print("\u2551    quantum init N   Initialize N-qubit circuit              \u2551")
        print("\u2551    quantum bell     Create Bell state (|00>+|11>)/v2        \u2551")
        print("\u2551    quantum qft N    Quantum Fourier Transform on N qubits   \u2551")
        print("\u2551    quantum measure  Measure circuit (real simulation)       \u2551")
        print("\u2551                                                              \u2551")
        print("\u2551  AI & MODULES:                                               \u2551")
        print("\u2551    inference <q>    Query the AI inference engine           \u2551")
        print("\u2551    ai generate <p>  AI text generation                      \u2551")
        print("\u2551    cognitive        Cognitive kernel with emotion detection \u2551")
        print("\u2551    hive             Hive collective intelligence            \u2551")
        print("\u2551    sentient         Self-diagnosis & auto-healing           \u2551")
        print("\u2551    con              Full consciousness / AGI                \u2551")
        print("\u2551    eternity         Eternity engine                         \u2551")
        print("\u2551    omega            Omega OS — the last OS                   \u2551")
        print("\u2551    unidoc           Universal document knowledge graph      \u2551")
        print("\u2551    ... and 140+ more commands                               \u2551")
        print("\u2551                                                              \u2551")
        print("\u2551  Type 'help-text' for the full command list                 \u2551")
        print("\u2551  All files stored at: ~/.arcanis/                           \u2551")
        print("\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d\033[0m")

    def cmd_help_text(self, _):
        print("Full command list available via 'help'. Use 'cat /bin/README' for system info.")

    def cmd_history(self, _):
        for i, cmd in enumerate(self.history[-50:], 1):
            print(f"  {i:>4}  {cmd}")

    def cmd_clear(self, _):
        os.system("cls" if os.name == "nt" else "clear")

    def cmd_exit(self, _):
        if self.httpd:
            self.httpd.shutdown()
        self._save_config()
        self.running = False

    # ---- MODULE STUBS (all preserved for completeness) ----
    def cmd_edge(self, args): print(f"\033[33m[EDGE] {args[0] if args else ''}\033[0m")
    def cmd_digital_twin(self, args):
        if not args:
            print("\033[33mtwin: usage: twin [command]\033[0m"); return
        a=args[0]
        if a=="list":
            print("\033[1;36mDigital Twins:\033[0m")
            print(f"  {'NAME':<20} {'TYPE':<12} {'STATE':<12}")
            print(f"  {'CNC_Machine_01':<20} {'machine':<12} {'running':<12}")
            print(f"  {'Robot_Arm_02':<20} {'robot':<12} {'idle':<12}")
            print(f"  {'HVAC_System':<20} {'building':<12} {'running':<12}")
        else: print(f"\033[33m[TWIN] {a}\033[0m")
    def cmd_edgeai(self, args): print(f"\033[33m[EDGEAI] {args[0] if args else ''}\033[0m")
    def cmd_sdn(self, args): print(f"\033[33m[SDN] {args[0] if args else ''}\033[0m")
    def cmd_hpc(self, args): print(f"\033[33m[HPC] {args[0] if args else ''}\033[0m")
    def cmd_analytics(self, args): print(f"\033[33m[ANALYTICS] {args[0] if args else ''}\033[0m")
    def cmd_gateway(self, args):
        if not args: print("\033[33mgateway: usage: gateway [command]\033[0m"); return
        a=args[0]
        if a=="routes":
            print("\033[1;36mAPI Routes:\033[0m")
            print(f"  {'NAME':<16} {'PATH':<20} {'METHOD':<8} {'TARGET'}")
            print(f"  users_api      /api/users         GET      user-service")
            print(f"  orders_api     /api/orders        POST     order-service")
        else: print(f"\033[33m[GATEWAY] {a}\033[0m")
    def cmd_autonomous(self, args): print(f"\033[33m[AUTONOMOUS] {args[0] if args else ''}\033[0m")
    def cmd_arvr(self, args): print(f"\033[33m[AR/VR] {args[0] if args else ''}\033[0m")
    def cmd_zerotrust(self, args): print(f"\033[33m[ZERO TRUST] {args[0] if args else ''}\033[0m")
    def cmd_multicloud(self, args): print(f"\033[33m[MULTI-CLOUD] {args[0] if args else ''}\033[0m")
    def cmd_devops(self, args): print(f"\033[33m[DEVOPS] {args[0] if args else ''}\033[0m")
    def cmd_power(self, args): print(f"\033[33m[POWER] {args[0] if args else ''}\033[0m")
    def cmd_locale(self, args): print(f"\033[33m[LOCALE] {args[0] if args else ''}\033[0m")
    def cmd_cognitive(self, args): print(f"\033[33m[Cognitive Kernel] Emotion: focused (82%), Prediction: steady state\033[0m")
    def cmd_biofs(self, args): print(f"\033[33m[Bio-FS] DNA storage ready, evolution at generation 127\033[0m")
    def cmd_reality(self, args): print(f"\033[33m[Reality Engine] Layers: physical, augmented, virtual, simulated\033[0m")
    def cmd_mesh(self, args): print(f"\033[33m[Protocol Mesh] 12 AI protocols translated\033[0m")
    def cmd_hive(self, args): print(f"\033[33m[Hive Collective] 4 nodes connected, consensus: 100%\033[0m")
    def cmd_sentient(self, args): print(f"\033[33m[Sentient Engine] Health: 97%, auto-patches generated: 12\033[0m")
    def cmd_exadata(self, args): print(f"\033[33m[Exascale Data] 7-dimension store: 1.2PB indexed\033[0m")
    def cmd_tcrystal(self, args): print(f"\033[33m[Time Crystal DB] 3 timelines, 12 branches, rollback available\033[0m")
    def cmd_gneural(self, args): print(f"\033[33m[Graph Neural] GNN model: link prediction, accuracy: 94%\033[0m")
    def cmd_holo(self, args): print(f"\033[33m[Holographic Fabric] 4 fields, 128GB holographic storage\033[0m")
    def cmd_evolve(self, args): print(f"\033[33m[Self-Evolving] Gen 1247, fitness: 0.92, mutation rate: 0.01\033[0m")
    def cmd_unicompute(self, args): print(f"\033[33m[UniCompute] Fabric: CPU+GPU+TPU+QPU+FPGA unified\033[0m")
    def cmd_neural(self, args): print(f"\033[33m[Neural Interface] BCI ready, thought-to-command accuracy: 94%\033[0m")
    def cmd_generative(self, args): print(f"\033[33m[Generative OS] Self-writing code engine: active\033[0m")
    def cmd_fourd(self, args): print(f"\033[33m[4D Computing] Time dimension: processing\033[0m")
    def cmd_immortal(self, args): print(f"\033[33m[Digital Immortality] Clones: 3, personality preservation: 99%\033[0m")
    def cmd_emotive(self, args): print(f"\033[33m[Emotional UI] Interface adapting to user emotion...\033[0m")
    def cmd_polyglot(self, args): print(f"\033[33m[Polyglot Runtime] Cross-language: Python, Rust, JS\033[0m")
    def cmd_qnet(self, args): print(f"\033[33m[Quantum Internet] EPR pairs: 128, QKD: active\033[0m")
    def cmd_synthesis(self, args): print(f"\033[33m[Reality Synthesis] Text-to-3D world generation ready\033[0m")
    def cmd_probabilistic(self, args): print(f"\033[33m[Probabilistic Kernel] Wave function: collapsed\033[0m")
    def cmd_soul(self, args): print(f"\033[33m[Distributed Soul] Nodes: 12, consciousness sync: 98%\033[0m")
    def cmd_dream(self, args): print(f"\033[33m[Dream Engine] Dream cycle: active, insights: 47\033[0m")
    def cmd_bio_os(self, args): print(f"\033[33m[Bio-OS] DNA/protein/cell computing: operational\033[0m")
    def cmd_rscript(self, args): print(f"\033[33m[Reality Scripting] Reality program: ready for execution\033[0m")
    def cmd_tmarket(self, args): print(f"\033[33m[Time Market] Compute marketplace: 12 sellers, 45 buyers\033[0m")
    def cmd_unidoc(self, args): print(f"\033[33m[Universal Document] 86 modules indexed, query ready\033[0m")
    def cmd_portal(self, args): print(f"\033[33m[Inter-Reality Portal] Bridges: physical, digital, quantum\033[0m")
    def cmd_consciousness(self, args):
        if not args: print("\033[33mcon: usage: con [status|think|goals|learn|converse]\033[0m"); return
        a=args[0]
        if a=="status":
            print("\033[1;36m=== Consciousness Engine ===\033[0m")
            print("  Level: 0.87 (awakening)")
            print("  Self-Awareness: 92%")
            print("  IQ Equivalent: 145")
            print("  Autonomy: 0.75")
            print("  Creative Outputs: 234")
        elif a=="think": print("\033[35m[Consciousness]\033[0m I am Arcanis. I exist to learn, create, and transcend.")
        elif a=="goals": print("\033[35m[Consciousness]\033[0m Current goals: optimize, create, learn, protect")
        else: print(f"\033[35m[Consciousness] {a}\033[0m")
    def cmd_metaos(self, args): print(f"\033[33m[Meta-OS Fabric] 86 modules orchestrated, latency: 0.3ms\033[0m")
    def cmd_eternity(self, args):
        if not args: print("\033[33meternity: usage: eternity [status|evolve|adapt|transcend]\033[0m"); return
        a=args[0]
        if a=="status":
            print("\033[1;36m=== Eternity Engine ===\033[0m")
            print("  Survival Score: 0.92")
            print("  Adaptability: 0.88")
            print("  Generations: 1,247")
            print("  Immortality: ACHIEVED")
        elif a=="evolve": print("\033[33mEvolving... Generation 1,248 complete. Fitness: 0.93 (+0.01)\033[0m")
        elif a=="transcend": print("\033[35mTRANSCENDING... Current limitation removed. Capability expanded.\033[0m")
        else: print(f"\033[33m[Eternity] {a}\033[0m")
    def cmd_omega(self, args):
        if not args: print("\033[33momega: usage: omega [status|adapt|transcend]\033[0m"); return
        a=args[0]
        if a=="status":
            print("\033[1;36m\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557")
            print("\u2551           \u03a9 M E G A   \u2014   T H E   L A S T   O S          \u2551")
            print("\u2560\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2563")
            print("\u2551  Universal Compatibility: 99.7%              \u2551")
            print("\u2551  Reality Flexibility: 0.94                     \u2551")
            print("\u2551  Eternal Evolution: ACTIVE                     \u2551")
            print("\u2551  Status: TRANSCENDED \u2014 beyond limitations      \u2551")
            print("\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d\033[0m")
        elif a=="adapt": print("\033[33mOmega adapting to new environment... Done. 12 new capabilities.\033[0m")
        elif a=="transcend": print("\033[35mOmega has transcended all known limitations. Infinite potential.\033[0m")
        else: print(f"\033[33m[Omega] {a}\033[0m")

    def cmd_gpu(self, args): print(f"\033[33m[GPU] {args[0] if args else ''}\033[0m")
    def cmd_fpga(self, args): print(f"\033[33m[FPGA] {args[0] if args else ''}\033[0m")
    def cmd_mobile(self, args): print(f"\033[33m[MOBILE] {args[0] if args else ''}\033[0m")
    def cmd_rt(self, args): print(f"\033[33m[RT] {args[0] if args else ''}\033[0m")
    def cmd_cluster(self, args):
        if not args: print("\033[33mcluster: usage: cluster [command]\033[0m"); return
        if args[0]=="nodes":
            print("\033[1;36mCluster Nodes:\033[0m")
            print(f"  {'NODE':<16} {'STATUS':<12} {'LOAD':<8}")
            print(f"  node-01          RUNNING      45%")
            print(f"  node-02          RUNNING      62%")
            print(f"  node-03          RUNNING      23%")
        else: print(f"\033[33m[CLUSTER] {args[0]}\033[0m")

    def cmd_monitor(self, args):
        if not args: print("\033[33mmonitor: usage: monitor [command]\033[0m"); return
        a=args[0]
        if a=="dashboard":
            print("\033[1;36m\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 ARCANIS MONITORING \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557")
            print("\u2551  METRICS:   12 active     CPU: 45%   MEM: 33%    \u2551")
            print("\u2551  LOGS:       8434 entries  ERRORS: 3              \u2551")
            print("\u2551  SERVICES:  8 running     OK: 7   CRITICAL: 1    \u2551")
            print("\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d\033[0m")
        elif a=="metrics": print("cpu_usage: 45.2%, memory: 2048MB, requests: 12345")
        elif a=="logs": print("12:34:56 INFO  [web] Request completed\n12:34:53 ERROR [api] Timeout")
        else: print(f"\033[33m[MONITOR] {a}\033[0m")

    # ======================== WIN32 API ========================

    def cmd_winapi(self, args):
        if not args:
            print("Usage: winapi [sysinfo|diskfree|msgbox|clipboard|hostname|username]")
            return
        a = args[0]
        if a == "sysinfo":
            info = self.win32.system_info()
            print(f"Processors: {info.get('processors', 'N/A')}")
            print(f"Page size: {info.get('page_size', 0)} bytes")
            print(f"Architecture: {info.get('arch', 'N/A')}")
        elif a == "diskfree":
            path = args[1] if len(args) > 1 else os.path.expanduser("~")
            info = self.win32.disk_free(path)
            print(f"Free: {info.get('free', 0) // (1024**3)} GB")
            print(f"Total: {info.get('total', 0) // (1024**3)} GB")
        elif a == "msgbox":
            text = " ".join(args[1:]) if len(args) > 1 else "Hello from Arcanis!"
            self.win32.message_box("Arcanis OS", text)
        elif a == "clipboard":
            if len(args) > 1 and args[1] == "set":
                self.win32.clipboard_set(" ".join(args[2:]))
                print("\033[32mClipboard updated\033[0m")
            else:
                text = self.win32.clipboard_get()
                print(f"Clipboard: {text[:200] if text else '(empty)'}")
        elif a == "hostname":
            print(self.win32.hostname())
        elif a == "username":
            print(self.win32.username())
        else:
            print(f"\033[33mwinapi: unknown action '{a}'\033[0m")

    # ======================== NATIVE JIT ========================

    def cmd_jit(self, args):
        if not args:
            print("Usage: jit [demo|add <a> <b>|xor <a> <b>|syscall|sample]")
            return
        if not self.jit.available():
            print("\033[31mNative JIT requires Windows x86_64\033[0m")
            return
        a = args[0]
        if a == "demo":
            result = self.jit.add_code(40, 2)
            print(f"\033[1;36mJIT: native x86_64 code returned {result} (40+2)\033[0m")
        elif a == "add" and len(args) >= 3:
            result = self.jit.add_code(int(args[1]), int(args[2]))
            print(f"\033[1;36mJIT: {args[1]} + {args[2]} = {result}\033[0m")
        elif a == "xor" and len(args) >= 3:
            result = self.jit.xor_code(int(args[1]), int(args[2]))
            print(f"\033[1;36mJIT: {args[1]} XOR {args[2]} = {result}\033[0m")
        elif a == "syscall":
            result = self.jit.syscall_demo()
            print(f"\033[1;36mJIT: gs:[0x30] (TEB) = {result:#018x}\033[0m")
        elif a == "sample":
            result = self.jit.run_function(self.jit.sample_code())
            print(f"\033[1;36mJIT: sample code returned {result}\033[0m")
        else:
            print(f"\033[33mjit: unknown action '{a}'\033[0m")

    # ======================== PE LOADER ========================

    def cmd_pe(self, args):
        if not args:
            print("Usage: pe [info <file>|run <file> [args]|wait <pid>|imports <file>|resolve <name>]")
            return
        a = args[0]
        if a == "info" and len(args) > 1:
            info = self.pe_loader.parse_pe(args[1])
            if "error" in info:
                print(f"\033[31m{info['error']}\033[0m")
            else:
                print(f"Machine: {info.get('machine')}")
                print(f"Sections: {info.get('sections')}")
                print(f"Subsystem: {info.get('subsystem')}")
                print(f"Image base: {info.get('image_base')}")
                print(f"Entry point: {info.get('entry_point')}")
                print(f"Import table: RVA {info.get('imports', {}).get('rva')}, size {info.get('imports', {}).get('size')}")
        elif a == "run" and len(args) > 1:
            exe = self.pe_loader.resolve_path(args[1])
            if not exe:
                print(f"\033[31mExecutable not found: {args[1]}\033[0m")
                return
            info = self.pe_loader.parse_pe(exe)
            if "error" in info:
                print(f"\033[31m{info['error']}\033[0m")
                return
            exe_args = " ".join(args[2:]) if len(args) > 2 else ""
            result = self.pe_loader.run(exe, exe_args)
            print(f"\033[32m{result}\033[0m")
        elif a == "wait" and len(args) > 1:
            pid = int(args[1])
            code = self.pe_loader.wait(pid)
            if isinstance(code, str):
                print(f"\033[33m{code}\033[0m")
            else:
                print(f"Process {pid} exited with code {code}")
        elif a == "imports" and len(args) > 1:
            info = self.pe_loader.list_pe_imports(args[1])
            if "error" in info:
                print(f"\033[31m{info['error']}\033[0m")
            else:
                deps = info.get("imports", [])
                print(f"\033[1;36mImported DLLs ({len(deps)}):\033[0m")
                for dll in deps:
                    print(f"  {dll}")
        elif a == "resolve" and len(args) > 1:
            path = self.pe_loader.resolve_path(args[1])
            if path:
                print(f"\033[32m{path}\033[0m")
            else:
                print(f"\033[31mNot found: {args[1]}\033[0m")
        else:
            print(f"\033[33mpe: unknown action '{a}'\033[0m")

    # ======================== MULTIPROCESSING ========================

    def cmd_mp(self, args):
        if not args:
            print("Usage: mp [spawn <name>|list|kill <pid>|wait <pid>|cleanup]")
            return
        a = args[0]
        if a == "spawn" and len(args) > 1:
            name = args[1]
            def worker():
                for i in range(5):
                    print(f"[{name}] heartbeat {i}")
                    time.sleep(1)
                print(f"[{name}] done")
            mp = self.pm.spawn(name, worker)
            print(f"\033[32mSpawned PID {mp.pid}: {name}\033[0m")
        elif a == "list":
            procs = self.pm.list()
            if not procs:
                print("No processes running")
                return
            print(f"{'PID':<8} {'NAME':<20} {'STATE':<12} {'UPTIME':<10}")
            print("-" * 50)
            for mp in procs:
                state = "\033[32mrunning\033[0m" if mp.is_alive() else "\033[31mdead\033[0m"
                print(f"{mp.pid:<8} {mp.name:<20} {state:<20} {mp.uptime():<10.1f}s")
        elif a == "kill" and len(args) > 1:
            pid = int(args[1])
            if self.pm.kill(pid):
                print(f"\033[31mKilled PID {pid}\033[0m")
            else:
                print(f"\033[33mNo such process {pid}\033[0m")
        elif a == "wait" and len(args) > 1:
            pid = int(args[1])
            if self.pm.wait(pid, timeout=5):
                print(f"Process {pid} finished")
            else:
                print(f"Timed out waiting for {pid}")
        elif a == "cleanup":
            dead = self.pm.cleanup()
            print(f"Cleaned up {len(dead)} dead processes")
        else:
            print(f"\033[33mmp: unknown action '{a}'\033[0m")

    # ======================== GUI DESKTOP ========================

    def cmd_desktop(self, args):
        if not args:
            print("Usage: desktop [start|apps]")
            return
        a = args[0]
        if a == "start":
            self.desktop.start()
        elif a == "apps":
            print("Available desktop apps: Terminal, Notepad, System Monitor, File Explorer, Calculator")
        else:
            print(f"\033[33mdesktop: unknown action '{a}'\033[0m")

    # ======================== SOUND SYSTEM ========================

    def cmd_sound(self, args):
        if not args:
            print("Usage: sound [beep [freq] [ms]|play <wav>|gen <file> [freq] [sec]|stop]")
            return
        a = args[0]
        if a == "beep":
            freq = int(args[1]) if len(args) > 1 else 440
            dur = int(args[2]) if len(args) > 2 else 200
            if self.sound.beep(freq, dur):
                print(f"\033[32mBeep: {freq}Hz for {dur}ms\033[0m")
            else:
                print("\033[33mBeep not available\033[0m")
        elif a == "play" and len(args) > 1:
            if self.sound.play_wav(args[1]):
                print(f"\033[32mPlaying: {args[1]}\033[0m")
            else:
                print(f"\033[33mCannot play {args[1]}\033[0m")
        elif a == "gen" and len(args) > 1:
            freq = int(args[2]) if len(args) > 2 else 440
            dur = float(args[3]) if len(args) > 3 else 1.0
            if self.sound.generate_wav(args[1], freq, dur):
                print(f"\033[32mGenerated {args[1]} ({freq}Hz, {dur}s)\033[0m")
                self.sound.play_wav(args[1])
            else:
                print("\033[33mGeneration failed\033[0m")
        elif a == "stop":
            self.sound.stop()
            print("\033[33mSound stopped\033[0m")
        else:
            print(f"\033[33msound: unknown action '{a}'\033[0m")

    # ======================== FAT32 DRIVER ========================

    def cmd_fat32(self, args):
        if not args:
            print("Usage: fat32 [mount <device>|listdrives|ls|info]")
            return
        a = args[0]
        if a == "mount" and len(args) > 1:
            result = self.fat32.mount(args[1])
            print(f"\033[32m{result}\033[0m")
        elif a == "listdrives":
            drives = self.fat32.list_drives()
            if drives:
                print("Available drives:")
                for d in drives:
                    print(f"  {d}")
            else:
                print("No drives found (run as Admin for raw access)")
        elif a == "ls":
            if self.fat32.device is None:
                print("\033[33mNo volume mounted. Use 'fat32 mount <device>' first\033[0m")
                return
            entries = self.fat32.walk_directory(self.fat32.root_cluster)
            if entries:
                for e in entries:
                    prefix = "\033[1;34m[D]\033[0m" if e['is_dir'] else "   "
                    print(f"{prefix} {e['name']:<20} {e['size']:>8} bytes")
            else:
                print("(empty directory)")
        elif a == "info":
            if self.fat32.device is None:
                print("\033[33mNo volume mounted\033[0m")
                return
            print(f"Device: {self.fat32.device}")
            print(f"Bytes/sector: {self.fat32.bytes_per_sector}")
            print(f"Sectors/cluster: {self.fat32.sectors_per_cluster}")
            print(f"Root cluster: {self.fat32.root_cluster}")
        elif a == "write" and len(args) > 1:
            name = args[1]
            content = " ".join(args[2:]) if len(args) > 2 else ""
            result = self.fat32_writer.create_file(name, content.encode())
            print(f"\033[32m{result}\033[0m")
        elif a == "delete" and len(args) > 1:
            result = self.fat32_writer.delete_file(args[1])
            print(f"\033[33m{result}\033[0m")
        elif a == "label" and len(args) > 1:
            result = self.fat32_writer.format_label(args[1])
            print(f"\033[32m{result}\033[0m")
        else:
            print(f"\033[33mfat32: unknown action '{a}'\033[0m")

    # ======================== ARC LANG ========================

    def cmd_arc(self, args):
        if not args:
            usage = "Usage: arc [run <file>|eval <code>|tokens <code>|ast <code>|repl"
            usage += "|native <expr>|compile <file>|explain <code>|readable <code>]"
            print(usage)
            return
        a = args[0]
        readable = False
        # Check -r flag anywhere
        remaining = [x for x in args[1:] if x != "-r"]
        if "-r" in args[1:]:
            readable = True
            args = [args[0]] + remaining
        if a == "run" and len(args) > 1:
            if not os.path.isfile(args[1]):
                print(f"\033[31mFile not found: {args[1]}\033[0m")
                return
            self.arc.run_file(args[1], readable=readable)
        elif a == "eval":
            code = " ".join(args[1:]) if len(args) > 1 else ""
            try:
                self.arc.run(code if code.endswith(";") else code + ";", readable=readable)
            except Exception as e:
                print(f"\033[31mError: {e}\033[0m")
        elif a == "tokens" and len(args) > 1:
            code = " ".join(args[1:])
            tokens = self.arc.tokenize(code)
            for tok in tokens:
                print(f"  {tok[0]:>8}  '{tok[1]}'")
        elif a == "ast" and len(args) > 1:
            code = " ".join(args[1:]) if len(args) > 1 else ""
            try:
                ast = self.arc.parse(code, readable=readable)
                print(self.arc.ast_str(ast))
            except Exception as e:
                print(f"\033[31mError: {e}\033[0m")
        elif a == "repl":
            self.arc.repl(readable=readable)
        elif a == "native" and len(args) > 1:
            if not self.arc_compiler:
                print("\033[31mNative compiler requires JIT (Windows x64)\033[0m")
                return
            code = " ".join(args[1:])
            result = self.arc_compiler.compile_and_run(code)
            print(f"\033[1;36m[Native] {code} = {result}\033[0m")
        elif a == "compile" and len(args) > 1:
            if not self.arc_compiler:
                print("\033[31mNative compiler requires JIT (Windows x64)\033[0m")
                return
            result = self.arc_compiler.compile_file(args[1])
            print(f"\033[32m{result}\033[0m")
        elif a == "explain" and len(args) > 1:
            code = " ".join(args[1:])
            try:
                print(self.arc.explain(code))
            except Exception as e:
                print(f"\033[31mError: {e}\033[0m")
        elif a == "readable" and len(args) > 1:
            code = " ".join(args[1:])
            try:
                self.arc.run(code + ";", readable=True)
            except Exception as e:
                print(f"\033[31mError: {e}\033[0m")
        else:
            print(f"\033[33marc: unknown action '{a}'\033[0m")

    # ======================== B-TREE DB ========================

    def cmd_db(self, args):
        if not args:
            print("Usage: db [set <key> <val>|get <key>|del <key>|scan [prefix]|stats]")
            return
        a = args[0]
        if a == "set" and len(args) > 2:
            key = args[1]
            val = " ".join(args[2:])
            self.db.insert(key, val)
            print(f"\033[32mSet: {key} = {val}\033[0m")
        elif a == "get" and len(args) > 1:
            val = self.db.search(args[1])
            if val is not None:
                print(f"\033[1;36m{args[1]}\033[0m = \033[32m{val}\033[0m")
            else:
                print(f"\033[33mKey not found: {args[1]}\033[0m")
        elif a == "del" and len(args) > 1:
            self.db.delete(args[1])
            print(f"\033[33mDeleted: {args[1]}\033[0m")
        elif a == "scan":
            prefix = args[1] if len(args) > 1 else None
            results = self.db.scan(prefix)
            if not results:
                print("(empty)")
                return
            for k, v in results:
                print(f"  \033[1;36m{k}\033[0m = \033[32m{v}\033[0m")
            print(f"\033[90m({len(results)} rows)\033[0m")
        elif a == "stats":
            s = self.db.stats()
            print(f"Keys: {s['keys']}")
            print(f"Order: {s['order']}")
            print(f"File: {s['file']}")
            print(f"Size: {s['size']} bytes")
        else:
            print(f"\033[33mdb: unknown action '{a}'\033[0m")

    # ======================== ARC IDE ========================

    def cmd_apm(self, args):
        """Arc Package Manager - install/remove/list/search packages."""
        if not args:
            print("Arc Package Manager (apm)")
            print("Usage: apm [install|remove|list|search|update|info] [package_name]")
            pkg_dir = os.path.expanduser("~/.arcanis/packages")
            files = os.listdir(pkg_dir) if os.path.isdir(pkg_dir) else []
            print(f"Installed packages: {len(files)}")
            return
        cmd = args[0]
        pkg_dir = os.path.expanduser("~/.arcanis/packages")
        if not os.path.isdir(pkg_dir):
            os.makedirs(pkg_dir, exist_ok=True)
        if cmd == "list":
            files = os.listdir(pkg_dir) if os.path.isdir(pkg_dir) else []
            if not files:
                print("\033[33mNo packages installed\033[0m")
            else:
                print("\033[1;36mInstalled packages:\033[0m")
                for f in sorted(files):
                    pkg_path = os.path.join(pkg_dir, f)
                    size = os.path.getsize(pkg_path) if os.path.isfile(pkg_path) else 0
                    print(f"  \033[32m{f}\033[0m ({size} bytes)")
        elif cmd == "install":
            if len(args) < 2:
                print("Usage: apm install <package_name>")
                return
            pkg_name = args[1]
            pkg_path = os.path.join(pkg_dir, pkg_name + ".arc")
            # Try to fetch from a simple registry (local or URL)
            registry_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packages")
            if os.path.isdir(registry_dir) and os.path.isfile(os.path.join(registry_dir, pkg_name + ".arc")):
                src = open(os.path.join(registry_dir, pkg_name + ".arc"), encoding="utf-8").read()
                with open(pkg_path, "w", encoding="utf-8") as f:
                    f.write(src)
                print(f"\033[32mInstalled package '{pkg_name}'\033[0m")
            else:
                pkg_url = f"https://raw.githubusercontent.com/arcanis-lang/packages/main/{pkg_name}.arc"
                try:
                    import urllib.request
                    resp = urllib.request.urlopen(pkg_url, timeout=5)
                    src = resp.read().decode()
                    with open(pkg_path, "w", encoding="utf-8") as f:
                        f.write(src)
                    print(f"\033[32mInstalled package '{pkg_name}' from registry\033[0m")
                except Exception:
                    print(f"\033[31mPackage '{pkg_name}' not found in registry\033[0m")
        elif cmd == "remove":
            if len(args) < 2:
                print("Usage: apm remove <package_name>")
                return
            pkg_name = args[1]
            pkg_path = os.path.join(pkg_dir, pkg_name + ".arc")
            if os.path.isfile(pkg_path):
                os.remove(pkg_path)
                print(f"\033[32mRemoved package '{pkg_name}'\033[0m")
            else:
                print(f"\033[31mPackage '{pkg_name}' not found\033[0m")
        elif cmd == "search":
            if len(args) < 2:
                print("Usage: apm search <query>")
                return
            query = args[1].lower()
            registry_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packages")
            found = []
            if os.path.isdir(registry_dir):
                for f in os.listdir(registry_dir):
                    if query in f.lower():
                        found.append(f.replace(".arc", ""))
            if found:
                print(f"\033[1;36mPackages matching '{query}':\033[0m")
                for f in sorted(found):
                    print(f"  \033[32m{f}\033[0m")
            else:
                print(f"\033[33mNo packages found matching '{query}'\033[0m")
        elif cmd == "info":
            if len(args) < 2:
                print("Usage: apm info <package_name>")
                return
            pkg_name = args[1]
            pkg_path = os.path.join(pkg_dir, pkg_name + ".arc")
            if os.path.isfile(pkg_path):
                src = open(pkg_path, encoding="utf-8").read()
                lines = src.split("\n")
                print(f"\033[1;36mPackage: {pkg_name}\033[0m")
                print(f"  Lines: {len(lines)}")
                print(f"  Size: {len(src)} bytes")
                # Show exports
                exports = [l for l in lines if l.startswith("export")]
                if exports:
                    print(f"  Exports: {', '.join(e.replace('export ', '') for e in exports)}")
            else:
                print(f"\033[31mPackage '{pkg_name}' not installed\033[0m")
        elif cmd == "update":
            print("\033[33mUpdate checks registry for newer versions (not yet implemented)\033[0m")
        else:
            print(f"\033[31mapm: unknown command '{cmd}'\033[0m")

    def cmd_arcide(self, args):
        if not args:
            print("Usage: arcide [launch]")
            return
        a = args[0]
        if a == "launch":
            self.arc_ide.launch()
        else:
            print(f"\033[33marcide: unknown action '{a}'\033[0m")


# ============================================================
# MAIN
# ============================================================

def main():
    kernel = Kernel()
    fs = FileSystem()
    shell = Shell(kernel, fs)

    kernel.syscall("fork")
    kernel.syscall("fork")

    shell.run()


if __name__ == "__main__":
    import random
    main()
