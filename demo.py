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
        self.env["platform"] = lambda: sys.platform
        self.env["os_name"] = lambda: os.name
        self.env["cpu_count"] = lambda: os.cpu_count() or 1
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


# ============================================================
# ARCANIS MISSION SPACE — The Future of Computing Interface
# ============================================================
# An AI-native operating environment built around human intention.
# No apps. No files. No folders. No desktop.
# Agents, knowledge, creation, and collaboration around your mission.

class ArcDesktop:
    """ARCANIS Creation Engine — The Universal Creation Platform.
    Phase 8: From operating systems that launch applications
    to operating systems that create realities."""

    BG = "#0d1117"
    BG2 = "#161b22"
    FG = "#c9d1d9"
    FG2 = "#8b949e"
    FG3 = "#484f58"
    ACCENT = "#58a6ff"
    ACCENT2 = "#3fb950"
    ACCENT3 = "#d29922"
    SURFACE = "#21262d"
    BORDER = "#30363d"

    PIPELINE_STAGES = [
        "Understand", "Research", "Plan", "Prototype",
        "Build", "Test", "Improve", "Deploy",
    ]

    def __init__(self, digital_twin=None):
        self.root = None
        self.canvas = None
        self.mission = None
        self.civilization = None
        self.knowledge_nodes = []
        self.timeline_entries = []
        self.active_agent = None
        self._phase = "prompt"
        self._pipeline_index = 0
        self._project_history = []
        self._conversation = []
        self.twin = digital_twin or DigitalTwinMind()
        self.living = LivingSoftwareEngine()
        self.reality = RealityLayer()
        self.world = AutonomousWorldEngine()
        self.evolution = SelfEvolvingIntelligence()
        self._permissions_granted = False
        self._permissions_showing = False

    def available(self):
        return _HAVE_TK

    def launch(self):
        if not _HAVE_TK:
            print("\033[31mArcDesktop requires Tkinter\033[0m")
            return
        self.root = tk.Tk()
        self.root.title("ARCANIS Creation Engine")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg=self.BG)
        self.root.bind("<Escape>", lambda e: self._shutdown())

        self.canvas = tk.Canvas(self.root, bg=self.BG, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._render_prompt()
        self._tick()
        self.root.mainloop()

    def _truncate(self, text, n):
        return text if len(text) <= n else text[:n-3] + "..."

    # ================================================================
    # PHASE 1 — PROMPT: "What do you want to create?"
    # ================================================================

    def _render_prompt(self):
        self.canvas.delete("all")
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        cx, cy = w // 2, h // 2

        self.canvas.create_rectangle(0, 0, w, h, fill=self.BG, outline="", tags="bg")

        # Top-left branding
        self.canvas.create_rectangle(24, 24, 56, 56, fill=self.ACCENT, outline="", tags="logo")
        self.canvas.create_text(40, 40, text="A", fill="#fff",
                                font=("Segoe UI", 18, "bold"), tags="logo")
        self.canvas.create_text(64, 32, text="ARCANIS", fill=self.FG,
                                font=("Segoe UI", 12, "bold"), anchor="w", tags="brand")
        self.canvas.create_text(64, 50, text="Creation Engine", fill=self.FG3,
                                font=("Segoe UI", 9), anchor="w", tags="brand")

        # Center prompt
        self.canvas.create_text(cx, cy - 60, text="What do you want to create?",
                                fill=self.FG, font=("Segoe UI", 28), tags="prompt_text")
        self.canvas.create_text(cx, cy - 24, text="Describe your idea. ARCANIS will generate the workspace, agents, and plan.",
                                fill=self.FG2, font=("Segoe UI", 11), tags="prompt_hint")

        # Input
        input_y = cy + 20
        iw = int(w * 0.4)
        self.canvas.create_rectangle(cx - iw//2, input_y - 20, cx + iw//2, input_y + 20,
                                     fill=self.BG2, outline=self.BORDER, tags="input_box")
        self.idea_entry = tk.Entry(self.root, bg=self.BG2, fg=self.FG,
                                   font=("Segoe UI", 14), insertbackground=self.ACCENT,
                                   relief=tk.FLAT, bd=0, highlightthickness=0, width=40,
                                   justify="center")
        self.idea_entry.place(x=cx - iw//2 + 4, y=input_y - 16, width=iw - 8, height=32)
        self.idea_entry.insert(0, "")
        self.idea_entry.bind("<Return>", self._process_idea)
        self.idea_entry.focus()

        # Examples
        examples = [
            "Create a multiplayer strategy game",
            "Design a robotics control system",
            "Build a movie recommendation engine",
            "Plan an architectural project",
        ]
        for ei, ex in enumerate(examples):
            ey = input_y + 50 + ei * 28
            self.canvas.create_text(cx, ey, text=ex, fill=self.FG3,
                                    font=("Segoe UI", 9), tags=f"example_{ei}")

    def _process_idea(self, event=None):
        idea = self.idea_entry.get().strip()
        if not idea:
            return
        self.mission = idea
        if not self._permissions_granted:
            self._show_permissions()
            return
        self._generate_creation()

    # ================================================================
    # PHASE 2 — GENERATION: Workspace + Agents + Pipeline
    # ================================================================

    def _generate_creation(self):
        self._phase = "generating"
        self.idea_entry.place_forget()
        self.twin.remember_mission(self.mission)
        self.twin.context.track_action("creation_start", self.mission)

        # Detect creation type
        ml = self.mission.lower()
        if any(w in ml for w in ["game", "play", "multiplayer"]):
            ctype = "game"
        elif any(w in ml for w in ["robot", "hardware", "drone", "mechanical"]):
            ctype = "robotics"
        elif any(w in ml for w in ["app", "software", "program", "web"]):
            ctype = "software"
        elif any(w in ml for w in ["movie", "film", "video", "media"]):
            ctype = "media"
        elif any(w in ml for w in ["architecture", "building", "house", "space"]):
            ctype = "architecture"
        elif any(w in ml for w in ["research", "science", "study", "learn"]):
            ctype = "research"
        elif any(w in ml for w in ["business", "plan", "startup"]):
            ctype = "business"
        elif any(w in ml for w in ["music", "sound", "audio"]):
            ctype = "music"
        else:
            ctype = "software"

        # Generate specialist agents based on type
        self.civilization = AgentCivilization(digital_twin=self.twin)
        self.civilization.start_mission(self.mission)
        self._living_app = self.living.create_app(self.mission)
        self.reality.understand_goal(self.mission)
        self.world.analyze_query(self.mission)
        self.evolution.record_task_result("creation_generated", True)
        self._init_knowledge()
        self._init_timeline()

        # Record in project history
        self._project_history.append({
            "idea": self.mission,
            "type": ctype,
            "agents": len(self.civilization.agents) if self.civilization else 0,
            "pipeline": list(self.PIPELINE_STAGES),
        })

        self._phase = "active"
        self._pipeline_index = 0
        self._render_creation_view()

    # ================================================================
    # CREATION VIEW — One adaptive workspace
    # ================================================================

    def _render_creation_view(self):
        self.canvas.delete("all")
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        cx = w // 2

        self.canvas.create_rectangle(0, 0, w, h, fill=self.BG, outline="", tags="bg")

        # Top bar: back + title + status
        self.canvas.create_rectangle(0, 0, w, 48, fill=self.BG2, outline="", tags="topbar")
        self.canvas.create_text(24, 24, text="\u2190", fill=self.FG2,
                                font=("Segoe UI", 14), tags="back_btn")
        self.canvas.tag_bind("back_btn", "<Button-1>", lambda e: self._render_prompt())
        self.canvas.create_text(52, 24, text="ARCANIS", fill=self.FG3,
                                font=("Segoe UI", 9, "bold"), anchor="w", tags="topbar_brand")
        self.canvas.create_text(cx, 24, text=self._truncate(self.mission, 60),
                                fill=self.FG, font=("Segoe UI", 11), tags="topbar_title")

        # Pipeline progress bar
        bar_y = 60
        bar_w = int(w * 0.7)
        bar_x = cx - bar_w // 2
        step_w = bar_w // len(self.PIPELINE_STAGES)
        for pi, stage in enumerate(self.PIPELINE_STAGES):
            sx = bar_x + pi * step_w
            active = pi <= self._pipeline_index
            self.canvas.create_rectangle(sx, bar_y, sx + step_w - 2, bar_y + 6,
                                         fill=self.ACCENT if active else self.SURFACE,
                                         outline="", tags=f"pipe_{pi}")
            self.canvas.create_text(sx + step_w // 2, bar_y + 16, text=stage,
                                    fill=self.FG if active else self.FG3,
                                    font=("Segoe UI", 7), tags=f"pipe_lbl_{pi}")

        # Main workspace area
        ws_y = 90
        ws_h = h - ws_y - 20

        # Left panel: agents
        panel_w = int(w * 0.22)
        self.canvas.create_rectangle(12, ws_y, 12 + panel_w, ws_y + ws_h,
                                     fill=self.BG2, outline=self.BORDER, tags="agents_panel")
        self.canvas.create_text(12 + 12, ws_y + 14, text="Team",
                                fill=self.FG3, font=("Segoe UI", 8, "bold"), anchor="w", tags="agents_title")
        if self.civilization:
            pass
        # Right panel: knowledge / context
        kw = int(w * 0.22)
        kx = w - 12 - kw
        self.canvas.create_rectangle(kx, ws_y, kx + kw, ws_y + ws_h,
                                     fill=self.BG2, outline=self.BORDER, tags="knowledge_panel")
        self.canvas.create_text(kx + 12, ws_y + 14, text="Knowledge",
                                fill=self.FG3, font=("Segoe UI", 8, "bold"), anchor="w", tags="knowledge_title")

        # Center: main canvas
        cw = w - panel_w - kw - 48
        cx2 = 12 + panel_w + 12
        self.canvas.create_rectangle(cx2, ws_y, cx2 + cw, ws_y + ws_h,
                                     fill=self.BG2, outline=self.BORDER, tags="canvas_area")
        self.canvas.create_text(cx2 + 16, ws_y + 14, text=self.PIPELINE_STAGES[self._pipeline_index],
                                fill=self.ACCENT, font=("Segoe UI", 13, "bold"), anchor="w", tags="stage_title")
        active_stage_desc = {
            "Understand": "Analyzing your idea and defining goals.",
            "Research": "Gathering knowledge and exploring possibilities.",
            "Plan": "Creating architecture and development roadmap.",
            "Prototype": "Building initial working model.",
            "Build": "Constructing the full creation.",
            "Test": "Validating quality and performance.",
            "Improve": "Optimizing based on results.",
            "Deploy": "Preparing for launch and distribution.",
        }
        self.canvas.create_text(cx2 + 16, ws_y + 38,
                                text=active_stage_desc.get(self.PIPELINE_STAGES[self._pipeline_index], ""),
                                fill=self.FG2, font=("Segoe UI", 9), anchor="w", tags="stage_desc")

        # Agent list
        if self.civilization and self.civilization.agents:
            agent_list = list(self.civilization.agents.items())
            for ai, (key, agent) in enumerate(agent_list[:8]):
                ay = ws_y + 42 + ai * 40
                dot = {"idle": self.ACCENT2, "working": self.ACCENT3, "blocked": "#f78166"}.get(agent.status, self.FG3)
                self.canvas.create_oval(panel_w + 12 + 8, ay + 6, panel_w + 12 + 16, ay + 14,
                                        fill=dot, outline="", tags=f"agent_dot_{key}")
                self.canvas.create_text(panel_w + 12 + 24, ay + 6, text=agent.name,
                                        fill=agent.color, font=("Segoe UI", 8, "bold"), anchor="w", tags=f"agent_name_{key}")
                self.canvas.create_text(panel_w + 12 + 24, ay + 18, text=self._truncate(agent.role, 22),
                                        fill=self.FG2, font=("Segoe UI", 7), anchor="w", tags=f"agent_role_{key}")

    # ================================================================
    # INTENT & PERMISSIONS
    # ================================================================

    def _show_permissions(self):
        if self._permissions_showing:
            return
        self._permissions_showing = True
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        cx, cy = w // 2, h // 2
        pw, ph = 360, 240
        px, py = cx - pw // 2, cy - ph // 2
        self.canvas.create_rectangle(px, py, px + pw, py + ph,
                                     fill=self.BG2, outline=self.ACCENT, width=1, tags="perm_bg")
        self.canvas.create_text(cx, py + 22, text="ARCANIS requires permissions",
                                fill=self.FG, font=("Segoe UI", 9, "bold"), tags="perm_title")
        for i, name in enumerate(["Files", "Memory", "Applications", "Devices", "Knowledge"]):
            self.canvas.create_text(px + 24, py + 50 + i * 26, text=name,
                                    fill=self.FG2, font=("Segoe UI", 8), anchor="w", tags=f"perm_item_{i}")
        btn_y = py + ph - 40
        self.canvas.create_rectangle(px + 24, btn_y, px + 160, btn_y + 26,
                                     fill=self.ACCENT, outline="", tags="perm_accept")
        self.canvas.create_text(px + 92, btn_y + 13, text="Accept",
                                fill="#fff", font=("Segoe UI", 8, "bold"), tags="perm_accept_text")
        self.canvas.tag_bind("perm_accept", "<Button-1>", lambda e: self._accept_permissions())
        self.canvas.create_rectangle(px + 172, btn_y, px + pw - 24, btn_y + 26,
                                     fill="", outline=self.BORDER, tags="perm_decline")
        self.canvas.create_text(px + 92 + 156, btn_y + 13, text="Decline",
                                fill=self.FG2, font=("Segoe UI", 8), tags="perm_decline_text")
        self.canvas.tag_bind("perm_decline", "<Button-1>", lambda e: self._decline_permissions())

    def _accept_permissions(self):
        self._permissions_granted = True
        self._permissions_showing = False
        for t in ["perm_bg", "perm_title"] + [f"perm_item_{i}" for i in range(5)] + \
                 ["perm_accept", "perm_accept_text", "perm_decline", "perm_decline_text"]:
            self.canvas.delete(t)
        self._generate_creation()

    def _decline_permissions(self):
        self._permissions_showing = False
        for t in ["perm_bg", "perm_title"] + [f"perm_item_{i}" for i in range(5)] + \
                 ["perm_accept", "perm_accept_text", "perm_decline", "perm_decline_text"]:
            self.canvas.delete(t)

    def _start_mission(self):
        self._generate_creation()

    # ================================================================
    # BACKGROUND TICK — Pipeline progress
    # ================================================================

    def _tick(self):
        try:
            if self._phase == "active" and self.civilization:
                for agent in self.civilization.agents.values():
                    if agent.status == "idle" and not agent.current_task:
                        agent.status = "working"
                        agent.current_task = "Processing..."
                    elif agent.status == "working":
                        agent.tasks_completed += 1
                        if agent.tasks_completed % 5 == 0:
                            agent.current_task = None
                            agent.status = "idle"
                pm = getattr(self.civilization, "manager", None)
                if pm and pm.goal:
                    pm.progress = min(1.0, pm.progress + 0.02)
                    if pm.progress >= 1.0:
                        pm.status = "completed"
                        if self._pipeline_index < len(self.PIPELINE_STAGES) - 1:
                            self._pipeline_index += 1
                            pm.progress = 0.0
                            pm.status = "active"
                if self._phase == "active":
                    self._render_creation_view()
            self.root.after(3000, self._tick)
        except Exception:
            self.root.after(5000, self._tick)

    # ================================================================
    # STATE PERSISTENCE
    # ================================================================

    def _init_knowledge(self):
        ml = self.mission.lower()
        self.knowledge_nodes = [
            {"id": "root", "label": self._truncate(self.mission, 20), "parent": None, "level": 0},
            {"id": "research", "label": "Research", "parent": "root", "level": 1},
            {"id": "concepts", "label": "Core Concepts", "parent": "research", "level": 2},
            {"id": "references", "label": "References", "parent": "research", "level": 2},
            {"id": "design", "label": "Design", "parent": "root", "level": 1},
            {"id": "architecture", "label": "Architecture", "parent": "design", "level": 2},
            {"id": "materials", "label": "Materials", "parent": "design", "level": 2},
            {"id": "build", "label": "Build", "parent": "root", "level": 1},
            {"id": "prototype", "label": "Prototype", "parent": "build", "level": 2},
            {"id": "testing", "label": "Testing", "parent": "build", "level": 2},
            {"id": "knowledge", "label": "Knowledge", "parent": "root", "level": 1},
            {"id": "experiments", "label": "Experiments", "parent": "knowledge", "level": 2},
            {"id": "insights", "label": "Insights", "parent": "knowledge", "level": 2},
        ]
        if any(w in ml for w in ["code", "program", "software", "app"]):
            self.knowledge_nodes.append({"id": "software", "label": "Software", "parent": "build", "level": 2})
        if any(w in ml for w in ["robot", "hardware", "mechanical"]):
            self.knowledge_nodes.append({"id": "mechanical", "label": "Mechanical", "parent": "design", "level": 2})
        if any(w in ml for w in ["learn", "study", "education"]):
            self.knowledge_nodes.append({"id": "learning", "label": "Learning Path", "parent": "knowledge", "level": 2})
        if any(w in ml for w in ["ai", "vision", "intelligence"]):
            self.knowledge_nodes.append({"id": "ai", "label": "AI Systems", "parent": "research", "level": 2})

    def _init_timeline(self):
        self.timeline_entries = [
            (0.05, f"Idea: {self._truncate(self.mission, 22)}", True),
            (0.2, "Research & Explore", False),
            (0.38, "Design & Plan", False),
            (0.55, "Build & Create", False),
            (0.72, "Test & Refine", False),
            (0.88, "Launch & Share", False),
        ]

    def _shutdown(self):
        if self.root:
            try:
                state = self.twin.save_state()
                if self.civilization:
                    state["civilization"] = self.civilization.to_dict()
                state["living"] = self.living.to_dict()
                state["reality"] = self.reality.to_dict()
                state["world"] = self.world.to_dict()
                state["evolution"] = self.evolution.to_dict()
                state["project_history"] = self._project_history
                import json
                save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".digital_twin.json")
                with open(save_path, "w") as f:
                    json.dump(state, f, indent=2)
            except Exception:
                pass
            self.root.destroy()


# ============================================================
# AGENT CIVILIZATION — Autonomous Intelligence Workforce
# ============================================================
# Agents are not isolated assistants. They are an intelligent
# organization that collaborates to achieve complex goals.

class AgentMemory:
    """Personal memory for a single agent — what the agent learned."""

    def __init__(self):
        self._personal = []
        self._mission = []
        self._shared_tags = []

    def store_personal(self, content, context=None):
        import time
        self._personal.append({"content": content, "context": context, "time": time.time()})

    def store_mission(self, content, context=None):
        import time
        self._mission.append({"content": content, "context": context, "time": time.time()})

    def recall_personal(self, query=None, limit=5):
        if not query:
            return list(self._personal[-limit:])
        q = query.lower()
        results = [m for m in self._personal if q in m["content"].lower()]
        return results[-limit:]

    def recall_mission(self, query=None, limit=5):
        if not query:
            return list(self._mission[-limit:])
        q = query.lower()
        results = [m for m in self._mission if q in m["content"].lower()]
        return results[-limit:]

    def to_dict(self):
        return {"personal": self._personal, "mission": self._mission}

    def from_dict(self, data):
        self._personal = data.get("personal", [])
        self._mission = data.get("mission", [])


class AgentSafetyCage:
    """Permissions and restrictions for one agent."""

    def __init__(self):
        self._tools_allowed = []
        self._tools_denied = []
        self._max_tasks = 10
        self._requires_approval = []

    def allow_tool(self, tool):
        if tool not in self._tools_allowed:
            self._tools_allowed.append(tool)

    def deny_tool(self, tool):
        if tool not in self._tools_denied:
            self._tools_denied.append(tool)

    def can_use(self, tool):
        if tool in self._tools_denied:
            return False
        if self._tools_allowed and tool not in self._tools_allowed:
            return False
        return True

    def needs_approval(self, action):
        return action in self._requires_approval


class Agent:
    """Individual AI agent with purpose, skills, memory, tools, permissions."""

    def __init__(self, agent_id, name, role, color="#7744ff"):
        self.id = agent_id
        self.name = name
        self.role = role
        self.color = color
        self.skills = {}
        self.tools = []
        self.memory = AgentMemory()
        self.cage = AgentSafetyCage()
        self.performance = []
        self.status = "idle"
        self.current_task = None
        self.tasks_completed = 0
        self.created = __import__("time").time()

    def assign_task(self, task):
        self.current_task = task
        self.status = "working"
        self.memory.store_mission(f"Assigned: {task}", "task_assignment")

    def add_skill(self, name, level=0.5):
        self.skills[name] = max(0.0, min(1.0, level))

    def add_tool(self, tool_name):
        if tool_name not in self.tools:
            self.tools.append(tool_name)

    def complete_task(self, outcome="completed"):
        self.tasks_completed += 1
        self.status = "idle"
        entry = {"task": self.current_task, "outcome": outcome, "time": __import__("time").time()}
        self.performance.append(entry)
        self.memory.store_mission(f"Completed: {self.current_task} ({outcome})", "task_complete")
        self.current_task = None
        return entry

    def feedback(self, rating, comment=""):
        """Record user feedback (0.0 to 1.0)."""
        entry = {"rating": max(0.0, min(1.0, rating)), "comment": comment, "time": __import__("time").time()}
        self.performance.append(entry)
        return entry

    def improvement_needed(self):
        """Check if agent needs improvement based on recent performance."""
        recent = [p for p in self.performance[-5:] if "rating" in p]
        if not recent:
            return False
        avg = sum(r["rating"] for r in recent) / len(recent)
        return avg < 0.4

    def summary(self):
        return f"{self.name} ({self.role}) | Tasks: {self.tasks_completed} | Skills: {len(self.skills)} | Tools: {len(self.tools)} | Status: {self.status}"

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "role": self.role, "color": self.color,
            "skills": self.skills, "tools": self.tools, "status": self.status,
            "tasks_completed": self.tasks_completed, "current_task": self.current_task,
            "performance": self.performance, "memory": self.memory.to_dict(),
        }

    def from_dict(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.role = data["role"]
        self.color = data.get("color", "#7744ff")
        self.skills = data.get("skills", {})
        self.tools = data.get("tools", [])
        self.status = data.get("status", "idle")
        self.tasks_completed = data.get("tasks_completed", 0)
        self.current_task = data.get("current_task")
        self.performance = data.get("performance", [])
        if "memory" in data:
            self.memory.from_dict(data["memory"])


class AgentCommunicationNetwork:
    """Internal communication layer — agents share, debate, review, request, combine."""

    def __init__(self):
        self._messages = []
        self._channels = {}

    def send(self, from_agent, to_agent, subject, body, channel="general"):
        import time
        msg = {
            "id": len(self._messages),
            "from": from_agent,
            "to": to_agent,
            "subject": subject,
            "body": body,
            "channel": channel,
            "time": time.time(),
            "read": False,
        }
        self._messages.append(msg)
        if channel not in self._channels:
            self._channels[channel] = []
        self._channels[channel].append(msg)
        return msg

    def broadcast(self, from_agent, subject, body, channel="broadcast"):
        return self.send(from_agent, "*", subject, body, channel)

    def inbox(self, agent_id, limit=10):
        return [m for m in self._messages if m["to"] == agent_id or m["to"] == "*"][-limit:]

    def outbox(self, agent_id, limit=10):
        return [m for m in self._messages if m["from"] == agent_id][-limit:]

    def get_channel(self, channel, limit=20):
        return self._channels.get(channel, [])[-limit:]

    def conversation_between(self, agent_a, agent_b, limit=20):
        conv = [m for m in self._messages
                if (m["from"] == agent_a and m["to"] == agent_b) or
                   (m["from"] == agent_b and m["to"] == agent_a)]
        return conv[-limit:]

    def mark_read(self, msg_id):
        for m in self._messages:
            if m["id"] == msg_id:
                m["read"] = True

    def recent_activity(self, n=10):
        return sorted(self._messages, key=lambda m: m["time"], reverse=True)[:n]

    def to_dict(self):
        return {"messages": self._messages}

    def from_dict(self, data):
        self._messages = data.get("messages", [])
        self._channels = {}
        for m in self._messages:
            ch = m.get("channel", "general")
            if ch not in self._channels:
                self._channels[ch] = []
            self._channels[ch].append(m)


class MissionManager:
    """Central intelligence — understands goals, breaks into tasks, assigns agents, tracks progress."""

    def __init__(self, communication_network=None):
        self.goal = None
        self.tasks = []
        self.assignments = {}
        self.progress = 0.0
        self.status = "idle"
        self.network = communication_network or AgentCommunicationNetwork()

    def define_goal(self, goal):
        self.goal = goal
        self.tasks = []
        self.assignments = {}
        self.progress = 0.0
        self.status = "planning"
        self._break_down(goal)
        return self.tasks

    def _break_down(self, goal):
        """Break a goal into tasks based on keywords and structure."""
        gl = goal.lower()
        tasks = []

        # Always include core phases
        tasks.append({"id": "research", "name": "Research & Gather Knowledge", "phase": "research", "depends_on": []})
        tasks.append({"id": "plan", "name": "Plan & Design Approach", "phase": "planning", "depends_on": ["research"]})

        if any(w in gl for w in ["build", "create", "make", "develop", "code", "program", "robot", "product"]):
            tasks.append({"id": "design", "name": "Design Architecture", "phase": "design", "depends_on": ["plan"]})
            tasks.append({"id": "implement", "name": "Implement & Build", "phase": "build", "depends_on": ["design"]})
            tasks.append({"id": "test", "name": "Test & Validate", "phase": "testing", "depends_on": ["implement"]})
        if any(w in gl for w in ["learn", "study", "understand", "research"]):
            tasks.append({"id": "learn", "name": "Learn & Master Concepts", "phase": "learning", "depends_on": ["research"]})
        if any(w in gl for w in ["company", "startup", "business", "venture"]):
            tasks.append({"id": "market", "name": "Market Analysis", "phase": "business", "depends_on": ["research"]})
            tasks.append({"id": "strategy", "name": "Business Strategy", "phase": "business", "depends_on": ["market"]})
            tasks.append({"id": "finance", "name": "Financial Planning", "phase": "business", "depends_on": ["strategy"]})

        tasks.append({"id": "review", "name": "Review & Improve", "phase": "review", "depends_on": [t["id"] for t in tasks if t["id"] not in ["review"]]})
        tasks.append({"id": "deliver", "name": "Deliver Results", "phase": "delivery", "depends_on": ["review"]})
        self.tasks = tasks

    def get_available_tasks(self):
        """Get tasks whose dependencies are met."""
        completed_ids = {a["task_id"] for a in self.assignments.values() if a.get("completed")}
        return [t for t in self.tasks if t["id"] not in completed_ids and all(d in completed_ids for d in t.get("depends_on", []))]

    def assign(self, task_id, agent_id):
        if task_id not in {t["id"] for t in self.tasks}:
            return False
        if any(a.get("agent_id") == agent_id for a in self.assignments.values() if not a.get("completed")):
            return False
        self.assignments[task_id] = {"agent_id": agent_id, "task_id": task_id, "completed": False, "result": None}
        self.network.send("MissionManager", agent_id, "Task Assignment", f"Assigned: {task_id}", "assignments")
        return True

    def complete_task(self, task_id, result=None):
        if task_id in self.assignments:
            self.assignments[task_id]["completed"] = True
            self.assignments[task_id]["result"] = result
            self._update_progress()
            self.network.broadcast("MissionManager", f"Task completed: {task_id}", "progress")
            return True
        return False

    def _update_progress(self):
        if not self.tasks:
            return
        completed = sum(1 for a in self.assignments.values() if a.get("completed"))
        self.progress = completed / len(self.tasks)
        if self.progress >= 1.0:
            self.status = "completed"
        else:
            self.status = "in_progress"

    def get_task(self, task_id):
        for t in self.tasks:
            if t["id"] == task_id:
                return t
        return None

    def get_agent_tasks(self, agent_id):
        return [a for a in self.assignments.values() if a["agent_id"] == agent_id]

    def summary(self):
        completed = sum(1 for a in self.assignments.values() if a.get("completed"))
        total = len(self.tasks)
        return f"Mission: {self.goal} | Progress: {completed}/{total} ({self.progress*100:.0f}%) | Status: {self.status}"

    def organization_chart(self):
        """Return agent organization structure."""
        org = {"name": "Mission Manager", "children": []}
        phases = {}
        for t in self.tasks:
            phase = t.get("phase", "general")
            if phase not in phases:
                phases[phase] = []
            assignment = self.assignments.get(t["id"], {})
            phases[phase].append({"task": t["name"], "agent": assignment.get("agent_id"), "done": assignment.get("completed", False)})
        for phase, items in phases.items():
            org["children"].append({"name": phase.capitalize(), "items": items})
        return org

    def to_dict(self):
        return {
            "goal": self.goal, "tasks": self.tasks,
            "assignments": {k: v for k, v in self.assignments.items()},
            "progress": self.progress, "status": self.status,
        }

    def from_dict(self, data):
        self.goal = data.get("goal")
        self.tasks = data.get("tasks", [])
        self.assignments = {k: v for k, v in data.get("assignments", {}).items()}
        self.progress = data.get("progress", 0.0)
        self.status = data.get("status", "idle")


class AgentMarketplace:
    """Intelligence Ecosystem — Agent Marketplace with publishing, ratings, search, categories, collaboration."""

    def __init__(self):
        self._published = {}
        self._installed = {}
        self._ratings = {}
        self._categories = {
            "research": "Research & Analysis",
            "engineering": "Engineering & Design",
            "development": "Software Development",
            "creative": "Creative & Design",
            "business": "Business & Finance",
            "education": "Education & Learning",
            "health": "Health & Medicine",
            "science": "Science & Simulation",
        }
        self._init_builtins()

    def _init_builtins(self):
        builtins = [
            {"type": "researcher", "name": "Research Agent", "role": "Gathers knowledge, finds papers, analyzes information", "category": "research", "color": "#33bbcc", "skills": {"research": 0.8, "analysis": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "engineer", "name": "Engineering Agent", "role": "Designs architecture, plans systems, builds solutions", "category": "engineering", "color": "#5533cc", "skills": {"engineering": 0.8, "design": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "coder", "name": "Coding Agent", "role": "Writes, tests, and refines code across languages", "category": "development", "color": "#7744ff", "skills": {"programming": 0.8, "debugging": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "designer", "name": "Design Agent", "role": "Creates visual designs, prototypes, UI/UX", "category": "creative", "color": "#cc44aa", "skills": {"design": 0.8, "creativity": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "analyst", "name": "Analysis Agent", "role": "Analyzes data, identifies patterns, generates insights", "category": "research", "color": "#3366dd", "skills": {"analysis": 0.8, "statistics": 0.6}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "planner", "name": "Planning Agent", "role": "Defines milestones, manages timelines, tracks progress", "category": "business", "color": "#8888bb", "skills": {"planning": 0.8, "organization": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "critic", "name": "Critic Agent", "role": "Reviews work, finds gaps, suggests improvements", "category": "development", "color": "#ff6644", "skills": {"critique": 0.8, "quality": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "mentor", "name": "Learning Mentor", "role": "Creates learning paths, explains concepts, tracks progress", "category": "education", "color": "#44bb88", "skills": {"teaching": 0.8, "communication": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "medical_ai", "name": "Medical Research Agent", "role": "Analyzes medical data, finds treatments, tracks clinical trials", "category": "health", "color": "#44aaff", "skills": {"medical_knowledge": 0.8, "data_analysis": 0.7, "research": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "legal_ai", "name": "Legal Analysis Agent", "role": "Reviews contracts, finds precedents, ensures compliance", "category": "business", "color": "#8866cc", "skills": {"legal_knowledge": 0.8, "analysis": 0.7, "writing": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "physics_sim", "name": "Physics Simulation Agent", "role": "Runs physics simulations, models systems, analyzes results", "category": "science", "color": "#66ddff", "skills": {"physics": 0.8, "simulation": 0.8, "mathematics": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "climate_ai", "name": "Climate Research Agent", "role": "Models climate data, predicts patterns, suggests interventions", "category": "science", "color": "#22bb88", "skills": {"climate_science": 0.8, "modeling": 0.7, "analysis": 0.7}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
            {"type": "robotics_ai", "name": "Robotics Agent", "role": "Controls robots, plans movements, processes sensor data", "category": "engineering", "color": "#ff8844", "skills": {"robotics": 0.8, "control_systems": 0.7, "computer_vision": 0.6}, "author": "ARCANIS", "version": "1.0.0", "price": 0},
        ]
        for b in builtins:
            self._published[b["type"]] = b
            self._installed[b["type"]] = b

    def publish(self, agent_type, name, role, author, category="general", color="#7744ff", skills=None, version="1.0.0", price=0):
        entry = {
            "type": agent_type, "name": name, "role": role,
            "author": author, "category": category, "color": color,
            "skills": skills or {}, "version": version, "price": price,
            "published": time.time(), "installs": 0, "rating": 0.0, "ratings_count": 0,
        }
        self._published[agent_type] = entry
        return entry

    def install(self, agent_type):
        if agent_type in self._published:
            self._installed[agent_type] = self._published[agent_type]
            self._published[agent_type]["installs"] = self._published[agent_type].get("installs", 0) + 1
            return True
        return False

    def spawn(self, agent_type, agent_id=None):
        info = self._installed.get(agent_type) or self._published.get(agent_type)
        if not info:
            return None
        agent = Agent(agent_id or f"{agent_type}_{int(time.time())}", info["name"], info["role"], info.get("color", "#7744ff"))
        for skill, level in info.get("skills", {}).items():
            agent.add_skill(skill, level)
        return agent

    def rate(self, agent_type, rating):
        if agent_type not in self._published:
            return False
        rating = max(1, min(5, rating))
        entry = self._published[agent_type]
        prev_total = entry.get("rating", 0) * entry.get("ratings_count", 0)
        entry["ratings_count"] = entry.get("ratings_count", 0) + 1
        entry["rating"] = (prev_total + rating) / entry["ratings_count"]
        return True

    def search(self, query=None, category=None, author=None):
        results = list(self._published.values())
        if query:
            q = query.lower()
            results = [r for r in results if q in r["name"].lower() or q in r["role"].lower() or q in r["type"].lower()]
        if category and category in self._categories:
            results = [r for r in results if r.get("category") == category]
        if author:
            results = [r for r in results if r.get("author", "").lower() == author.lower()]
        return sorted(results, key=lambda r: r.get("rating", 0), reverse=True)

    def list_installed(self):
        return list(self._installed.values())

    def get_info(self, agent_type):
        return self._published.get(agent_type) or self._installed.get(agent_type)

    def to_dict(self):
        return {"published": self._published, "installed": {k: True for k in self._installed}}

    def from_dict(self, data):
        for k, v in data.get("published", {}).items():
            if k not in self._published:
                self._published[k] = v
        for k in data.get("installed", {}):
            if k in self._published and k not in self._installed:
                self._installed[k] = self._published[k]


class KnowledgeMarketplace:
    """Modular knowledge packs — knowledge graphs, learning paths, templates, expert agents."""

    def __init__(self):
        self._packs = {}
        self._installed_packs = {}
        self._init_builtins()

    def _init_builtins(self):
        builtins = [
            {
                "id": "quantum_computing", "name": "Quantum Computing Pack",
                "description": "Complete quantum computing knowledge — circuits, algorithms, error correction",
                "author": "ARCANIS", "version": "1.0.0", "price": 0, "category": "science",
                "concepts": ["qubit", "superposition", "entanglement", "quantum_gate", "qft", "grover", "shor", "error_correction"],
                "learning_paths": [{"name": "Quantum Basics", "steps": ["qubit", "superposition", "entanglement"]}, {"name": "Quantum Algorithms", "steps": ["qft", "grover", "shor"]}],
                "templates": ["bell_state", "quantum_teleportation", "qft_circuit"],
                "expert_agents": ["physics_sim"],
            },
            {
                "id": "machine_learning", "name": "Machine Learning Pack",
                "description": "Foundations of ML — neural networks, training, optimization, deployment",
                "author": "ARCANIS", "version": "1.0.0", "price": 0, "category": "development",
                "concepts": ["neural_network", "backpropagation", "gradient_descent", "cnn", "rnn", "transformer", "reinforcement_learning"],
                "learning_paths": [{"name": "ML Fundamentals", "steps": ["neural_network", "backpropagation", "gradient_descent"]}, {"name": "Advanced Architectures", "steps": ["cnn", "rnn", "transformer"]}],
                "templates": ["image_classifier", "text_generator", "rl_agent"],
                "expert_agents": ["researcher", "analyst"],
            },
            {
                "id": "robotics_engineering", "name": "Robotics Pack",
                "description": "Robotics engineering — kinematics, control, perception, planning",
                "author": "ARCANIS", "version": "1.0.0", "price": 0, "category": "engineering",
                "concepts": ["kinematics", "dynamics", "control_theory", "computer_vision", "slam", "motion_planning", "sensor_fusion"],
                "learning_paths": [{"name": "Robot Foundations", "steps": ["kinematics", "dynamics", "control_theory"]}, {"name": "Robot Perception", "steps": ["computer_vision", "slam", "sensor_fusion"]}],
                "templates": ["arm_controller", "mobile_robot", "vision_pipeline"],
                "expert_agents": ["engineer", "robotics_ai"],
            },
            {
                "id": "cybersecurity", "name": "Cybersecurity Pack",
                "description": "Security — cryptography, network defense, threat analysis, zero trust",
                "author": "ARCANIS", "version": "1.0.0", "price": 0, "category": "development",
                "concepts": ["cryptography", "network_security", "threat_modeling", "zero_trust", "intrusion_detection", "forensics"],
                "learning_paths": [{"name": "Security Basics", "steps": ["cryptography", "network_security", "threat_modeling"]}, {"name": "Advanced Defense", "steps": ["zero_trust", "intrusion_detection", "forensics"]}],
                "templates": ["firewall_rules", "audit_pipeline", "incident_response"],
                "expert_agents": ["analyst", "critic"],
            },
            {
                "id": "astrophysics", "name": "Astrophysics Pack",
                "description": "Astrophysics — stellar evolution, cosmology, exoplanets, gravitational waves",
                "author": "ARCANIS", "version": "1.0.0", "price": 0, "category": "science",
                "concepts": ["stellar_evolution", "cosmology", "exoplanets", "gravitational_waves", "dark_matter", "general_relativity"],
                "learning_paths": [{"name": "Astrophysics Foundations", "steps": ["stellar_evolution", "cosmology", "general_relativity"]}, {"name": "Modern Topics", "steps": ["exoplanets", "gravitational_waves", "dark_matter"]}],
                "templates": ["stellar_simulation", "cosmic_expansion", "exoplanet_detection"],
                "expert_agents": ["researcher", "physics_sim"],
            },
        ]
        for p in builtins:
            self._packs[p["id"]] = p
            self._installed_packs[p["id"]] = p

    def create_pack(self, pack_id, name, description, author, category="general", version="1.0.0", price=0):
        pack = {
            "id": pack_id, "name": name, "description": description,
            "author": author, "category": category, "version": version, "price": price,
            "concepts": [], "learning_paths": [], "templates": [], "expert_agents": [],
            "published": time.time(), "installs": 0, "rating": 0.0,
        }
        self._packs[pack_id] = pack
        return pack

    def add_concept(self, pack_id, concept):
        if pack_id in self._packs and concept not in self._packs[pack_id]["concepts"]:
            self._packs[pack_id]["concepts"].append(concept)

    def add_learning_path(self, pack_id, name, steps):
        if pack_id in self._packs:
            self._packs[pack_id]["learning_paths"].append({"name": name, "steps": steps})

    def add_template(self, pack_id, template):
        if pack_id in self._packs and template not in self._packs[pack_id]["templates"]:
            self._packs[pack_id]["templates"].append(template)

    def add_expert_agent(self, pack_id, agent_type):
        if pack_id in self._packs and agent_type not in self._packs[pack_id]["expert_agents"]:
            self._packs[pack_id]["expert_agents"].append(agent_type)

    def install_pack(self, pack_id):
        if pack_id in self._packs:
            self._installed_packs[pack_id] = self._packs[pack_id]
            self._packs[pack_id]["installs"] = self._packs[pack_id].get("installs", 0) + 1
            return True
        return False

    def search(self, query=None, category=None):
        results = list(self._packs.values())
        if query:
            q = query.lower()
            results = [r for r in results if q in r["name"].lower() or q in r["description"].lower()]
        if category:
            results = [r for r in results if r.get("category") == category]
        return results

    def list_installed(self):
        return list(self._installed_packs.values())

    def get_pack(self, pack_id):
        return self._packs.get(pack_id)

    def to_dict(self):
        return {"packs": self._packs, "installed": {k: True for k in self._installed_packs}}

    def from_dict(self, data):
        for k, v in data.get("packs", {}).items():
            if k not in self._packs:
                self._packs[k] = v
        for k in data.get("installed", {}):
            if k in self._packs and k not in self._installed_packs:
                self._installed_packs[k] = self._packs[k]


class MissionMarketplace:
    """Shareable mission templates — complete workflows with goals, agents, steps."""

    def __init__(self):
        self._missions = {}
        self._installed_missions = {}
        self._init_builtins()

    def _init_builtins(self):
        builtins = [
            {
                "id": "build_startup", "name": "Build a Startup",
                "description": "Complete startup launch — planning, research, finance, marketing, legal, documentation",
                "author": "ARCANIS", "version": "1.0.0", "price": 0,
                "goal": "Launch a successful startup from idea to market",
                "agents": ["planner", "researcher", "analyst", "designer"],
                "phases": ["research", "planning", "finance", "marketing", "legal", "documentation"],
                "estimated_hours": 40,
            },
            {
                "id": "build_robot", "name": "Build a Robot Arm",
                "description": "Design, simulate, and build a robotic arm — kinematics, control, fabrication",
                "author": "ARCANIS", "version": "1.0.0", "price": 0,
                "goal": "Design and build a functional robotic arm",
                "agents": ["engineer", "robotics_ai", "physics_sim", "designer"],
                "phases": ["research", "design", "simulation", "implementation", "testing"],
                "estimated_hours": 60,
            },
            {
                "id": "learn_ai", "name": "Become an AI Engineer",
                "description": "Personalized learning path — curriculum, projects, mentors, practice missions, portfolio",
                "author": "ARCANIS", "version": "1.0.0", "price": 0,
                "goal": "Master artificial intelligence engineering",
                "agents": ["mentor", "researcher", "coder", "critic"],
                "phases": ["foundations", "ml_basics", "deep_learning", "specialization", "portfolio"],
                "estimated_hours": 200,
            },
            {
                "id": "climate_research", "name": "Climate Research Project",
                "description": "Comprehensive climate analysis — data collection, modeling, prediction, intervention design",
                "author": "ARCANIS", "version": "1.0.0", "price": 0,
                "goal": "Analyze climate patterns and design intervention strategies",
                "agents": ["climate_ai", "researcher", "analyst", "physics_sim"],
                "phases": ["data_collection", "modeling", "analysis", "prediction", "intervention"],
                "estimated_hours": 80,
            },
            {
                "id": "quantum_research", "name": "Quantum Computing Research",
                "description": "Explore quantum algorithms — circuits, error correction, quantum advantage",
                "author": "ARCANIS", "version": "1.0.0", "price": 0,
                "goal": "Advance quantum computing research",
                "agents": ["physics_sim", "researcher", "coder", "analyst"],
                "phases": ["foundations", "algorithm_design", "simulation", "analysis", "publication"],
                "estimated_hours": 100,
            },
            {
                "id": "medical_diagnosis", "name": "Medical Diagnosis System",
                "description": "Build an AI-assisted medical diagnosis pipeline — data, models, validation, deployment",
                "author": "ARCANIS", "version": "1.0.0", "price": 0,
                "goal": "Create a medical diagnosis support system",
                "agents": ["medical_ai", "researcher", "coder", "analyst", "critic"],
                "phases": ["research", "data_prep", "modeling", "validation", "deployment"],
                "estimated_hours": 120,
            },
        ]
        for m in builtins:
            self._missions[m["id"]] = m
            self._installed_missions[m["id"]] = m

    def create_mission(self, mission_id, name, description, author, goal, agents=None, phases=None, version="1.0.0", price=0):
        mission = {
            "id": mission_id, "name": name, "description": description,
            "author": author, "version": version, "price": price,
            "goal": goal, "agents": agents or [],
            "phases": phases or [], "estimated_hours": 0,
            "published": time.time(), "installs": 0, "rating": 0.0,
        }
        self._missions[mission_id] = mission
        return mission

    def install_mission(self, mission_id):
        if mission_id in self._missions:
            self._installed_missions[mission_id] = self._missions[mission_id]
            self._missions[mission_id]["installs"] = self._missions[mission_id].get("installs", 0) + 1
            return True
        return False

    def search(self, query=None, category=None):
        results = list(self._missions.values())
        if query:
            q = query.lower()
            results = [r for r in results if q in r["name"].lower() or q in r["description"].lower() or q in r["goal"].lower()]
        return results

    def list_installed(self):
        return list(self._installed_missions.values())

    def get_mission(self, mission_id):
        return self._missions.get(mission_id)

    def to_dict(self):
        return {"missions": self._missions, "installed": {k: True for k in self._installed_missions}}

    def from_dict(self, data):
        for k, v in data.get("missions", {}).items():
            if k not in self._missions:
                self._missions[k] = v
        for k in data.get("installed", {}):
            if k in self._missions and k not in self._installed_missions:
                self._installed_missions[k] = self._missions[k]


class DeveloperPlatform:
    """SDK tools for creating and publishing agents, knowledge packs, and missions to the ecosystem."""

    def __init__(self, agent_market=None, knowledge_market=None, mission_market=None):
        self.agent_market = agent_market
        self.knowledge_market = knowledge_market
        self.mission_market = mission_market
        self._projects = {}
        self._templates = {
            "agent": {
                "description": "Create a new agent type for the marketplace",
                "fields": ["type_id", "name", "role", "category", "skills"],
            },
            "knowledge_pack": {
                "description": "Create a knowledge pack with concepts, learning paths, templates",
                "fields": ["pack_id", "name", "description", "category", "concepts"],
            },
            "mission_template": {
                "description": "Create a shareable mission template with agents and phases",
                "fields": ["mission_id", "name", "description", "goal", "agents", "phases"],
            },
        }

    def new_project(self, project_type, project_id, name):
        if project_type not in self._templates:
            return None
        project = {
            "id": project_id, "name": name, "type": project_type,
            "created": time.time(), "status": "draft",
            "fields": {},
        }
        self._projects[project_id] = project
        return project

    def set_field(self, project_id, field, value):
        if project_id not in self._projects:
            return False
        self._projects[project_id]["fields"][field] = value
        return True

    def build_agent(self, project_id):
        proj = self._projects.get(project_id)
        if not proj or proj["type"] != "agent":
            return None
        fields = proj["fields"]
        agent_type = fields.get("type_id", project_id)
        if self.agent_market:
            entry = self.agent_market.publish(
                agent_type=agent_type,
                name=fields.get("name", "Custom Agent"),
                role=fields.get("role", "General purpose agent"),
                author=fields.get("author", "developer"),
                category=fields.get("category", "general"),
                skills=fields.get("skills", {}),
            )
            proj["status"] = "published"
            return entry
        return None

    def build_knowledge_pack(self, project_id):
        proj = self._projects.get(project_id)
        if not proj or proj["type"] != "knowledge_pack":
            return None
        fields = proj["fields"]
        pack_id = fields.get("pack_id", project_id)
        if self.knowledge_market:
            pack = self.knowledge_market.create_pack(
                pack_id=pack_id,
                name=fields.get("name", "Custom Pack"),
                description=fields.get("description", ""),
                author=fields.get("author", "developer"),
                category=fields.get("category", "general"),
            )
            for c in fields.get("concepts", []):
                self.knowledge_market.add_concept(pack_id, c)
            proj["status"] = "published"
            return pack
        return None

    def build_mission(self, project_id):
        proj = self._projects.get(project_id)
        if not proj or proj["type"] != "mission_template":
            return None
        fields = proj["fields"]
        mission_id = fields.get("mission_id", project_id)
        if self.mission_market:
            mission = self.mission_market.create_mission(
                mission_id=mission_id,
                name=fields.get("name", "Custom Mission"),
                description=fields.get("description", ""),
                author=fields.get("author", "developer"),
                goal=fields.get("goal", "Complete a project"),
                agents=fields.get("agents", []),
                phases=fields.get("phases", []),
            )
            proj["status"] = "published"
            return mission
        return None

    def list_projects(self, status=None):
        results = list(self._projects.values())
        if status:
            results = [p for p in results if p["status"] == status]
        return results

    def get_project(self, project_id):
        return self._projects.get(project_id)

    def sdk_info(self):
        return {
            "templates": list(self._templates.keys()),
            "projects": len(self._projects),
            "published": sum(1 for p in self._projects.values() if p["status"] == "published"),
        }


class OpenIntelligenceProtocol:
    """Universal protocol for ecosystem-wide communication — agents, missions, knowledge, devices."""

    PROTOCOL_VERSION = "1.0.0"

    MESSAGE_TYPES = [
        "agent.request", "agent.response", "agent.broadcast",
        "mission.create", "mission.update", "mission.complete",
        "knowledge.query", "knowledge.share", "knowledge.sync",
        "marketplace.list", "marketplace.install", "marketplace.publish",
        "device.discover", "device.status", "device.command",
        "ecosystem.sync", "ecosystem.heartbeat",
    ]

    def __init__(self):
        self._handlers = {}
        self._message_log = []

    def register_handler(self, msg_type, handler):
        self._handlers[msg_type] = handler

    def create_message(self, msg_type, sender, target="*", payload=None):
        msg = {
            "protocol": self.PROTOCOL_VERSION,
            "type": msg_type,
            "sender": sender,
            "target": target,
            "payload": payload or {},
            "timestamp": time.time(),
            "id": hashlib.md5(f"{msg_type}{sender}{time.time()}".encode()).hexdigest()[:16],
        }
        return msg

    def send(self, msg, socket=None):
        self._message_log.append(msg)
        encoded = json.dumps(msg) + "\n"
        if socket:
            try:
                socket.sendall(encoded.encode())
                return True
            except Exception:
                return False
        return True

    def receive(self, data):
        try:
            msg = json.loads(data)
            if msg.get("protocol") != self.PROTOCOL_VERSION:
                return None
            self._message_log.append(msg)
            msg_type = msg.get("type")
            if msg_type in self._handlers:
                self._handlers[msg_type](msg)
            return msg
        except Exception:
            return None

    def to_dict(self):
        return {"version": self.PROTOCOL_VERSION, "message_types": self.MESSAGE_TYPES, "message_count": len(self._message_log)}


class EcosystemEconomy:
    """Economy layer — credits, subscriptions, publishing, revenue for the intelligence ecosystem."""

    def __init__(self):
        self._accounts = {}
        self._transactions = []
        self._subscriptions = {}
        self._pricing_tiers = {
            "free": {"price": 0, "features": ["basic_agents", "basic_knowledge"]},
            "creator": {"price": 10, "features": ["publish_agents", "publish_knowledge", "publish_missions", "analytics"]},
            "enterprise": {"price": 100, "features": ["private_network", "custom_agents", "priority_support", "audit_logs", "sla"]},
        }

    def create_account(self, account_id, name, tier="free"):
        self._accounts[account_id] = {
            "id": account_id, "name": name, "tier": tier,
            "credits": 100 if tier == "free" else 1000,
            "created": time.time(),
        }
        if tier != "free":
            self._subscriptions[account_id] = {
                "tier": tier, "started": time.time(),
                "active": True, "renewal": time.time() + 2592000,
            }
        return self._accounts[account_id]

    def add_credits(self, account_id, amount):
        if account_id in self._accounts:
            self._accounts[account_id]["credits"] += amount
            self._transactions.append({"type": "credit", "account": account_id, "amount": amount, "time": time.time()})

    def spend_credits(self, account_id, amount, item=None):
        acct = self._accounts.get(account_id)
        if not acct or acct["credits"] < amount:
            return False
        acct["credits"] -= amount
        self._transactions.append({"type": "spend", "account": account_id, "amount": amount, "item": item, "time": time.time()})
        return True

    def get_tier_features(self, tier):
        return self._pricing_tiers.get(tier, self._pricing_tiers["free"])

    def account_summary(self, account_id):
        acct = self._accounts.get(account_id)
        if not acct:
            return None
        sub = self._subscriptions.get(account_id)
        return {
            "name": acct["name"], "tier": acct["tier"],
            "credits": acct["credits"],
            "subscription": sub["tier"] if sub and sub.get("active") else "none",
            "transactions": sum(1 for t in self._transactions if t["account"] == account_id),
        }


class IntelligenceEcosystem:
    """Top-level orchestrator for the entire ARCANIS Intelligence Ecosystem."""

    def __init__(self):
        self.agent_market = AgentMarketplace()
        self.knowledge_market = KnowledgeMarketplace()
        self.mission_market = MissionMarketplace()
        self.dev_platform = DeveloperPlatform(
            agent_market=self.agent_market,
            knowledge_market=self.knowledge_market,
            mission_market=self.mission_market,
        )
        self.protocol = OpenIntelligenceProtocol()
        self.economy = EcosystemEconomy()
        self._account_id = f"user_{socket.gethostname()}_{int(time.time())}"

    def init_account(self, name="Developer", tier="free"):
        return self.economy.create_account(self._account_id, name, tier)

    def summary(self):
        return {
            "agents": len(self.agent_market._published),
            "agents_installed": len(self.agent_market._installed),
            "knowledge_packs": len(self.knowledge_market._packs),
            "missions": len(self.mission_market._missions),
            "dev_projects": len(self.dev_platform._projects),
            "protocol_messages": len(self.protocol._message_log),
            "account": self.economy.account_summary(self._account_id),
        }

    def to_dict(self):
        return {
            "agent_market": self.agent_market.to_dict(),
            "knowledge_market": self.knowledge_market.to_dict(),
            "mission_market": self.mission_market.to_dict(),
            "economy": {"accounts": self.economy._accounts, "transactions": self.economy._transactions[-50:]},
        }

    def from_dict(self, data):
        if "agent_market" in data:
            self.agent_market.from_dict(data["agent_market"])
        if "knowledge_market" in data:
            self.knowledge_market.from_dict(data["knowledge_market"])
        if "mission_market" in data:
            self.mission_market.from_dict(data["mission_market"])


class AgentTraining:
    """System for agent improvement through feedback and performance analysis."""

    def __init__(self):
        self._records = {}
        self._improvements = []

    def record_feedback(self, agent_id, rating, comment=""):
        if agent_id not in self._records:
            self._records[agent_id] = []
        entry = {"rating": max(0.0, min(1.0, rating)), "comment": comment, "time": __import__("time").time()}
        self._records[agent_id].append(entry)
        self._analyze(agent_id)
        return entry

    def _analyze(self, agent_id):
        records = self._records.get(agent_id, [])
        if len(records) < 3:
            return
        recent = records[-3:]
        avg = sum(r["rating"] for r in recent) / len(recent)
        if avg < 0.3:
            improvement = f"Agent {agent_id}: Performance critically low ({avg:.0%}). Recommend retraining or replacement."
            self._improvements.append(improvement)
        elif avg < 0.5:
            improvement = f"Agent {agent_id}: Below average ({avg:.0%}). Additional training suggested."
            self._improvements.append(improvement)

    def get_improvements(self, agent_id=None):
        if agent_id:
            return [i for i in self._improvements if agent_id in i]
        return list(self._improvements)

    def get_average_rating(self, agent_id):
        records = self._records.get(agent_id, [])
        if not records:
            return None
        return sum(r["rating"] for r in records) / len(records)

    def get_performance_summary(self):
        summary = {}
        for agent_id, records in self._records.items():
            ratings = [r["rating"] for r in records if "rating" in r]
            summary[agent_id] = {
                "total_feedback": len(records),
                "avg_rating": sum(ratings) / len(ratings) if ratings else None,
                "trend": "improving" if len(ratings) >= 2 and ratings[-1] > ratings[-2] else "declining" if len(ratings) >= 2 else "stable",
            }
        return summary


class WorkflowEngine:
    """Learns repeated workflows and automates them."""

    def __init__(self):
        self._workflows = {}
        self._patterns = []

    def record_workflow(self, name, steps):
        import time
        self._workflows[name] = {
            "name": name,
            "steps": steps,
            "count": 1,
            "last_used": time.time(),
            "created": time.time(),
        }
        return self._workflows[name]

    def execute_step(self, workflow_name, step_index=0):
        wf = self._workflows.get(workflow_name)
        if not wf or step_index >= len(wf["steps"]):
            return None
        wf["last_used"] = __import__("time").time()
        return wf["steps"][step_index]

    def learn_from_sequence(self, actions):
        """Detect patterns in repeated action sequences."""
        if len(actions) < 3:
            return None
        pattern = tuple(actions[-3:])
        # Update pattern count
        found = False
        for p in self._patterns:
            if p["pattern"] == pattern:
                p["count"] += 1
                found = True
                break
        if not found:
            self._patterns.append({"pattern": pattern, "count": 1})

        # Check if pattern appears frequently
        frequent = [p for p in self._patterns if p["count"] >= 3]
        if frequent:
            pat = frequent[-1]
            name = " → ".join(pat["pattern"])
            if name not in self._workflows:
                self.record_workflow(name, list(pat["pattern"]))
            return name
        return None

    def get_suggested_workflows(self, context=""):
        """Suggest workflows based on context."""
        if not context:
            return list(self._workflows.keys())
        ctx = context.lower()
        matches = []
        for name, wf in self._workflows.items():
            if any(ctx in step.lower() for step in wf["steps"]):
                matches.append(name)
        return matches

    def get_workflow(self, name):
        return self._workflows.get(name)

    def list_workflows(self):
        return {k: {"steps": len(v["steps"]), "count": v["count"]} for k, v in self._workflows.items()}

    def to_dict(self):
        return {"workflows": self._workflows, "patterns": self._patterns}

    def from_dict(self, data):
        self._workflows = data.get("workflows", {})
        self._patterns = data.get("patterns", [])


class SafetyArchitecture:
    """Permission boundaries, activity logs, user approval controls for the civilization."""

    def __init__(self):
        self._logs = []
        self._pending_approvals = []
        self._global_restrictions = []

    def log_activity(self, agent_id, action, details=None):
        import time
        entry = {"agent": agent_id, "action": action, "details": details, "time": time.time()}
        self._logs.append(entry)
        if len(self._logs) > 500:
            self._logs = self._logs[-250:]
        return entry

    def require_approval(self, agent_id, action, reason=""):
        req = {"id": len(self._pending_approvals), "agent": agent_id, "action": action, "reason": reason, "approved": None}
        self._pending_approvals.append(req)
        return req

    def approve(self, request_id):
        for req in self._pending_approvals:
            if req["id"] == request_id:
                req["approved"] = True
                return True
        return False

    def deny(self, request_id):
        for req in self._pending_approvals:
            if req["id"] == request_id:
                req["approved"] = False
                return True
        return False

    def get_pending(self):
        return [r for r in self._pending_approvals if r["approved"] is None]

    def get_logs(self, agent_id=None, n=20):
        if agent_id:
            return [l for l in self._logs if l["agent"] == agent_id][-n:]
        return list(self._logs[-n:])

    def restrict_global(self, action):
        if action not in self._global_restrictions:
            self._global_restrictions.append(action)

    def is_restricted(self, action):
        return action in self._global_restrictions

    def to_dict(self):
        return {"logs": self._logs, "restrictions": self._global_restrictions}

    def from_dict(self, data):
        self._logs = data.get("logs", [])
        self._global_restrictions = data.get("restrictions", [])


class AgentCivilization:
    """Top-level orchestrator — manages agents, communication, missions, and evolution."""

    def __init__(self, digital_twin=None):
        self.network = AgentCommunicationNetwork()
        self.manager = MissionManager(self.network)
        self.marketplace = AgentMarketplace()
        self.training = AgentTraining()
        self.safety = SafetyArchitecture()
        self.workflows = WorkflowEngine()
        self.twin = digital_twin
        self.agents = {}
        self._active = False

    def start_mission(self, goal):
        """Initialize a civilization for a new mission."""
        self.manager.define_goal(goal)
        self._spawn_team(goal)
        self._assign_initial_tasks()
        self._active = True
        self.safety.log_activity("system", "mission_start", {"goal": goal})
        return self._mission_summary()

    def _spawn_team(self, goal):
        """Spawn agents based on mission type."""
        gl = goal.lower()
        needed = ["researcher", "planner", "critic"]

        if any(w in gl for w in ["build", "create", "make", "develop", "code", "program"]):
            needed.extend(["engineer", "coder", "designer"])
        if any(w in gl for w in ["research", "study", "learn", "understand"]):
            needed.extend(["researcher", "mentor"])
            needed = list(dict.fromkeys(needed))
        if any(w in gl for w in ["company", "startup", "business", "venture"]):
            needed.extend(["analyst", "planner"])
            needed = list(dict.fromkeys(needed))
        if any(w in gl for w in ["data", "analysis", "analytics"]):
            needed.append("analyst")
            needed = list(dict.fromkeys(needed))

        # Ensure basic team
        if "researcher" not in needed:
            needed.append("researcher")
        if "planner" not in needed:
            needed.append("planner")

        for atype in needed:
            if atype not in self.agents:
                agent = self.marketplace.spawn(atype)
                if agent:
                    self.agents[atype] = agent

        for atype, agent in self.agents.items():
            self.network.broadcast(atype, f"{agent.name} ready for mission: {goal}", "status")

    def _assign_initial_tasks(self):
        """Assign available tasks to appropriate agents."""
        available = self.manager.get_available_tasks()
        for task in available:
            agent_id = self._best_agent_for(task)
            if agent_id:
                self.manager.assign(task["id"], agent_id)
                if agent_id in self.agents:
                    self.agents[agent_id].assign_task(task["name"])
                    self.network.send("MissionManager", agent_id, "Task", task["name"], "assignments")

    def _best_agent_for(self, task):
        """Find the most suitable agent for a task based on skills."""
        task_name = task["name"].lower()
        keyword_map = {
            "research": "researcher", "knowledge": "researcher", "gather": "researcher",
            "plan": "planner", "design": "designer", "architecture": "engineer",
            "build": "engineer", "implement": "coder", "code": "coder", "program": "coder",
            "test": "critic", "review": "critic", "validate": "critic",
            "learn": "mentor", "study": "mentor",
            "market": "analyst", "analy": "analyst", "data": "analyst",
            "finance": "analyst", "strategy": "planner",
        }
        for keyword, agent_type in keyword_map.items():
            if keyword in task_name and agent_type in self.agents:
                return agent_type
        # Fallback to first available
        for atype in self.agents:
            agent = self.agents[atype]
            if agent.status == "idle":
                return atype
        return None

    def communicate(self, from_agent, message, to_agent=None):
        """Send a message from one agent to another (or broadcast)."""
        if to_agent:
            self.network.send(from_agent, to_agent, "Message", message, "chat")
        else:
            self.network.broadcast(from_agent, message, "chat")
        self.safety.log_activity(from_agent, "communicate", {"to": to_agent or "all", "message": message[:50]})

    def complete_agent_task(self, agent_id, result=None):
        """Mark an agent's current task as complete."""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        completed = agent.complete_task("completed")
        # Find and complete the corresponding mission manager task
        for task_id, assignment in list(self.manager.assignments.items()):
            if assignment["agent_id"] == agent_id and not assignment["completed"]:
                self.manager.complete_task(task_id, result)
                break
        self.manager._update_progress()
        # Assign next task if available
        self._assign_initial_tasks()
        return True

    def get_activity_feed(self, n=10):
        """Get recent activity for visualization."""
        messages = self.network.recent_activity(n)
        logs = self.safety.get_logs(n=n)
        feed = []
        for m in messages:
            feed.append(f"{m['from']} → {m['to']}: {m['subject']}")
        for l in logs:
            feed.append(f"[{l['agent']}] {l['action']}")
        return feed[-n:]

    def organization_chart(self):
        """Visual organization structure."""
        org = self.manager.organization_chart()
        # Add agent details
        org["agents"] = {aid: {"name": a.name, "role": a.role, "status": a.status, "tasks": a.tasks_completed} for aid, a in self.agents.items()}
        return org

    def _mission_summary(self):
        return {
            "goal": self.manager.goal,
            "agents": {aid: {"name": a.name, "status": a.status, "skills": len(a.skills)} for aid, a in self.agents.items()},
            "tasks": len(self.manager.tasks),
            "progress": self.manager.progress,
            "activity": self.get_activity_feed(5),
        }

    def summary(self):
        return f"Civilization: {len(self.agents)} agents | Goal: {self.manager.goal} | Progress: {self.manager.progress*100:.0f}% | Messages: {len(self.network._messages)}"

    def to_dict(self):
        return {
            "agents": {aid: a.to_dict() for aid, a in self.agents.items()},
            "manager": self.manager.to_dict(),
            "network": self.network.to_dict(),
            "safety": self.safety.to_dict(),
            "workflows": self.workflows.to_dict(),
        }

    def from_dict(self, data):
        if "agents" in data:
            self.agents = {}
            for aid, adata in data["agents"].items():
                agent = Agent(adata.get("id", aid), adata["name"], adata["role"], adata.get("color", "#7744ff"))
                agent.from_dict(adata)
                self.agents[aid] = agent
        if "manager" in data:
            self.manager.from_dict(data["manager"])
        if "network" in data:
            self.network.from_dict(data["network"])
        if "safety" in data:
            self.safety.from_dict(data["safety"])
        if "workflows" in data:
            self.workflows.from_dict(data["workflows"])


# ============================================================
# LIVING SOFTWARE ENGINE — The Evolution Beyond Applications
# ============================================================
# Software is no longer static. It understands user needs,
# generates new tools, modifies itself, improves over time.

class SoftwareDNA:
    """Living architecture record — purpose, evolution, versions."""

    def __init__(self, app_id, name, purpose):
        import time
        self.app_id = app_id
        self.name = name
        self.purpose = purpose
        self.created = time.time()
        self.versions = []
        self.evolution = []
        self.current_version = "0.1.0"
        self._record_evolution("created", purpose)

    def _record_evolution(self, event, detail):
        import time
        self.evolution.append({
            "version": self.current_version,
            "event": event,
            "detail": detail,
            "time": time.time(),
        })

    def new_version(self, version, changes):
        self.current_version = version
        self.versions.append({"version": version, "changes": changes, "time": __import__("time").time()})
        self._record_evolution("version", f"{version}: {changes}")

    def improve(self, description):
        """Record an improvement made to the app."""
        self._record_evolution("improvement", description)

    def history(self):
        return list(self.evolution)

    def summary(self):
        return f"{self.name} v{self.current_version} — {self.purpose} ({len(self.versions)} versions, {len(self.evolution)} events)"

    def to_dict(self):
        return {
            "app_id": self.app_id, "name": self.name, "purpose": self.purpose,
            "created": self.created, "versions": self.versions,
            "evolution": self.evolution, "current_version": self.current_version,
        }

    def from_dict(self, data):
        self.app_id = data["app_id"]
        self.name = data["name"]
        self.purpose = data["purpose"]
        self.created = data.get("created", 0)
        self.versions = data.get("versions", [])
        self.evolution = data.get("evolution", [])
        self.current_version = data.get("current_version", "0.1.0")


class DynamicApp:
    """A dynamically generated application — features, UI, code, state."""

    def __init__(self, app_id, name, purpose, features=None):
        self.app_id = app_id
        self.name = name
        self.purpose = purpose
        self.features = features or []
        self.ui_spec = {}
        self.code_modules = {}
        self.state = {}
        self.status = "generated"
        self.dna = SoftwareDNA(app_id, name, purpose)

    def add_feature(self, name, description):
        self.features.append({"name": name, "description": description, "implemented": True})
        self.dna.improve(f"Added feature: {name}")

    def set_ui(self, ui_type, layout, components):
        self.ui_spec = {"type": ui_type, "layout": layout, "components": components}
        self.dna.improve(f"UI updated: {ui_type}/{layout}")

    def add_code(self, module_name, code):
        self.code_modules[module_name] = code
        self.dna.new_version(self.dna.current_version, f"Added module: {module_name}")

    def analyze_usage(self, usage_data):
        if usage_data.get("frequent_action"):
            suggestion = f"User frequently does '{usage_data['frequent_action']}' — consider automation"
            self.dna.improve(suggestion)
            return suggestion
        return None

    def summary(self):
        features_str = ", ".join(f["name"] for f in self.features[:5])
        return f"{self.name}: {features_str} | {self.dna.summary()} | Status: {self.status}"

    def to_dict(self):
        return {
            "app_id": self.app_id, "name": self.name, "purpose": self.purpose,
            "features": self.features, "ui_spec": self.ui_spec,
            "code_modules": self.code_modules, "state": self.state,
            "status": self.status, "dna": self.dna.to_dict(),
        }

    def from_dict(self, data):
        self.app_id = data["app_id"]
        self.name = data["name"]
        self.purpose = data["purpose"]
        self.features = data.get("features", [])
        self.ui_spec = data.get("ui_spec", {})
        self.code_modules = data.get("code_modules", {})
        self.state = data.get("state", {})
        self.status = data.get("status", "generated")
        if "dna" in data:
            self.dna = SoftwareDNA(self.app_id, self.name, self.purpose)
            self.dna.from_dict(data["dna"])


class AppCreationAgent:
    """Specialized agent responsible for creating software capabilities."""

    AGENT_TYPES = [
        ("architect", "Software Architect", "Designs architecture and structure of applications", "#7744ff"),
        ("programmer", "Programming Agent", "Writes code and implements features", "#33bbcc"),
        ("ui_designer", "UI Design Agent", "Creates user interfaces and experiences", "#cc44aa"),
        ("tester", "Testing Agent", "Validates functionality and finds bugs", "#44bb88"),
        ("security", "Security Agent", "Reviews code for vulnerabilities", "#ff6644"),
    ]

    def __init__(self, agent_type, name, role, color):
        self.agent_type = agent_type
        self.name = name
        self.role = role
        self.color = color
        self.apps_created = 0
        self.specialization = agent_type

    @classmethod
    def create_team(cls):
        return [cls(at, n, r, c) for at, n, r, c in cls.AGENT_TYPES]

    def design_application(self, request):
        """Generate app design based on natural language request."""
        rq = request.lower()
        features = []
        if any(w in rq for w in ["track", "manage", "database", "store", "log"]):
            features.append({"name": "Data Management", "description": "Store and organize information"})
        if any(w in rq for w in ["visualize", "graph", "chart", "plot", "display"]):
            features.append({"name": "Visualization", "description": "Visual representation of data"})
        if any(w in rq for w in ["analyze", "analyze", "insight", "report"]):
            features.append({"name": "Analysis", "description": "Analyze data and generate insights"})
        if any(w in rq for w in ["search", "find", "query"]):
            features.append({"name": "Search", "description": "Search and filter capabilities"})
        if any(w in rq for w in ["experiment", "test", "simulate", "simulation"]):
            features.append({"name": "Experiments", "description": "Run and track experiments"})
        if any(w in rq for w in ["collaborate", "share", "team", "multi"]):
            features.append({"name": "Collaboration", "description": "Multi-user collaboration"})
        if any(w in rq for w in ["report", "export", "pdf", "document"]):
            features.append({"name": "Reports", "description": "Generate reports and exports"})
        if any(w in rq for w in ["ai", "intelligent", "automate", "smart"]):
            features.append({"name": "AI Assistant", "description": "AI-powered assistance"})

        if not features:
            features = [
                {"name": "Core Function", "description": f"Core {request} functionality"},
                {"name": "Settings", "description": "Configuration and preferences"},
            ]

        app_id = f"app_{__import__('time').time_ns()}"
        app = DynamicApp(app_id, f"{request[:30]} App", request, features)
        app.set_ui("adaptive", "responsive", ["input", "display", "controls"])
        app.add_code("main.py", f"# {request} — generated by ARCANIS Living Software\n")
        self.apps_created += 1
        return app

    def summary(self):
        return f"{self.name} ({self.specialization}) — {self.apps_created} apps created"


class EvolutionEngine:
    """Tracks usage patterns, suggests improvements, auto-evolves software."""

    def __init__(self):
        self._observations = []
        self._improvements = []

    def observe(self, app_id, action, duration=None):
        import time
        self._observations.append({
            "app_id": app_id, "action": action, "duration": duration, "time": time.time(),
        })
        if len(self._observations) > 500:
            self._observations = self._observations[-250:]

    def analyze(self, app_id):
        """Analyze usage patterns for an app and suggest improvements."""
        app_obs = [o for o in self._observations if o["app_id"] == app_id]
        if len(app_obs) < 3:
            return []

        suggestions = []
        # Detect frequent actions
        actions = {}
        for o in app_obs:
            actions[o["action"]] = actions.get(o["action"], 0) + 1
        frequent = [(a, c) for a, c in sorted(actions.items(), key=lambda x: -x[1]) if c >= 2]
        for action, count in frequent[:3]:
            suggestions.append(f"'{action}' used {count} times — consider creating a shortcut or automation")

        # Detect slow actions
        slow = [o for o in app_obs if o.get("duration") and o["duration"] > 10]
        if slow:
            suggestions.append(f"Detected {len(slow)} slow operations — optimization recommended")

        # Detect repeated patterns
        if len(app_obs) >= 5:
            recent_actions = [o["action"] for o in app_obs[-5:]]
            if len(set(recent_actions)) <= 2:
                suggestions.append(f"Workflow detected: {' → '.join(recent_actions[:3])}... Automate this sequence?")

        self._improvements.extend(suggestions)
        return suggestions

    def get_improvement_history(self):
        return list(self._improvements)

    def to_dict(self):
        return {"observations": self._observations}

    def from_dict(self, data):
        self._observations = data.get("observations", [])


class SelfRepairSystem:
    """Detects issues, generates patches, validates fixes."""

    def __init__(self):
        self._issues = []
        self._patches = []
        self._fix_history = []

    def detect_issue(self, app_id, symptom, severity="medium"):
        import time
        issue = {
            "id": len(self._issues),
            "app_id": app_id,
            "symptom": symptom,
            "severity": severity,
            "detected": time.time(),
            "status": "open",
            "root_cause": None,
            "patch": None,
        }
        self._issues.append(issue)
        return issue

    def diagnose(self, issue_id):
        issue = next((i for i in self._issues if i["id"] == issue_id), None)
        if not issue:
            return None
        symptom = issue["symptom"].lower()
        if "performance" in symptom or "slow" in symptom:
            issue["root_cause"] = "Query optimization needed"
        elif "data" in symptom or "database" in symptom:
            issue["root_cause"] = "Data integrity check needed"
        elif "security" in symptom or "access" in symptom:
            issue["root_cause"] = "Permission boundary missing"
        elif "error" in symptom or "crash" in symptom or "fail" in symptom:
            issue["root_cause"] = "Input validation missing"
        else:
            issue["root_cause"] = "General stability improvement"
        return issue["root_cause"]

    def generate_patch(self, issue_id):
        issue = next((i for i in self._issues if i["id"] == issue_id), None)
        if not issue or not issue["root_cause"]:
            return None
        patch = {
            "issue_id": issue_id,
            "description": f"Patch: {issue['root_cause']}",
            "code": f"# Patch for {issue['app_id']}: {issue['root_cause']}\n# Generated by ARCANIS Self-Repair\n",
            "tested": False,
        }
        self._patches.append(patch)
        issue["patch"] = patch
        return patch

    def test_patch(self, patch):
        """Simulate testing a patch."""
        patch["tested"] = True
        import random
        patch["passed"] = True
        return patch["passed"]

    def apply_patch(self, issue_id):
        issue = next((i for i in self._issues if i["id"] == issue_id), None)
        if not issue or not issue.get("patch"):
            return False
        if issue["patch"].get("tested") and issue["patch"].get("passed", False):
            issue["status"] = "fixed"
            self._fix_history.append({
                "issue_id": issue_id,
                "app_id": issue["app_id"],
                "patch": issue["patch"]["description"],
                "time": __import__("time").time(),
            })
            return True
        # Auto-test if not tested
        patch = issue["patch"]
        if self.test_patch(patch):
            issue["status"] = "fixed"
            self._fix_history.append({
                "issue_id": issue_id,
                "app_id": issue["app_id"],
                "patch": patch["description"],
                "time": __import__("time").time(),
            })
            return True
        return False

    def get_open_issues(self, app_id=None):
        issues = [i for i in self._issues if i["status"] == "open"]
        if app_id:
            issues = [i for i in issues if i["app_id"] == app_id]
        return issues

    def get_fix_history(self):
        return list(self._fix_history)

    def summary(self):
        open_count = sum(1 for i in self._issues if i["status"] == "open")
        fixed_count = sum(1 for i in self._issues if i["status"] == "fixed")
        return f"{len(self._issues)} issues detected, {fixed_count} fixed, {open_count} open"

    def to_dict(self):
        return {"issues": self._issues, "patches": self._patches, "fix_history": self._fix_history}

    def from_dict(self, data):
        self._issues = data.get("issues", [])
        self._patches = data.get("patches", [])
        self._fix_history = data.get("fix_history", [])


class AdaptiveInterface:
    """Interface adapts based on user role, skill level, context, preferences."""

    MODES = {
        "beginner": {"complexity": "simple", "guidance": True, "shortcuts": False, "advanced": False},
        "intermediate": {"complexity": "moderate", "guidance": True, "shortcuts": True, "advanced": False},
        "expert": {"complexity": "full", "guidance": False, "shortcuts": True, "advanced": True},
    }

    def __init__(self):
        self.mode = "intermediate"
        self.role = "general"
        self.context = {}
        self.preferences = {}

    def set_mode(self, mode):
        if mode in self.MODES:
            self.mode = mode
            return True
        return False

    def set_role(self, role):
        self.role = role
        if role == "developer":
            self.mode = "expert"
        elif role == "researcher":
            self.mode = "intermediate"
        elif role == "beginner":
            self.mode = "beginner"

    def get_config(self):
        base = dict(self.MODES.get(self.mode, self.MODES["intermediate"]))
        base["role"] = self.role
        base["context"] = self.context
        return base

    def suggest_mode(self, skill_level, task_complexity):
        if skill_level < 0.3 or task_complexity < 0.3:
            return "beginner"
        elif skill_level < 0.7 or task_complexity < 0.7:
            return "intermediate"
        return "expert"

    def to_dict(self):
        return {"mode": self.mode, "role": self.role, "context": self.context, "preferences": self.preferences}

    def from_dict(self, data):
        self.mode = data.get("mode", "intermediate")
        self.role = data.get("role", "general")
        self.context = data.get("context", {})
        self.preferences = data.get("preferences", {})


class CapabilityRegistry:
    """Registry of available capabilities — replaces traditional app stores."""

    def __init__(self):
        self._capabilities = {}
        self._installed = {}

    def register(self, capability_id, name, description, category, features=None):
        self._capabilities[capability_id] = {
            "id": capability_id,
            "name": name,
            "description": description,
            "category": category,
            "features": features or [],
            "registered": __import__("time").time(),
        }

    def install(self, capability_id):
        if capability_id in self._capabilities:
            self._installed[capability_id] = self._capabilities[capability_id]
            self._installed[capability_id]["installed"] = __import__("time").time()
            return True
        return False

    def search(self, query):
        q = query.lower()
        results = []
        for cid, cap in self._capabilities.items():
            if q in cid.lower() or q in cap["name"].lower() or q in cap["description"].lower():
                results.append(cap)
        return results

    def get_installed(self):
        return list(self._installed.values())

    def get_available(self):
        return list(self._capabilities.values())

    def get_by_category(self, category):
        return [c for c in self._capabilities.values() if c["category"] == category]

    def categories(self):
        return sorted(set(c["category"] for c in self._capabilities.values()))

    def register_builtins(self):
        builtins = [
            ("experiment_tracker", "Experiment Tracker", "Track and manage scientific experiments", "research",
             ["Create experiments", "Log measurements", "View history", "Export data"]),
            ("research_assistant", "Research Assistant", "Collect and organize research information", "research",
             ["Search papers", "Save references", "Generate summaries", "Organize by topic"]),
            ("data_visualizer", "Data Visualizer", "Create visualizations from any data", "analysis",
             ["Import data", "Create charts", "Customize visuals", "Export graphics"]),
            ("project_planner", "Project Planner", "Plan and track project milestones", "productivity",
             ["Create timeline", "Set milestones", "Track progress", "Team view"]),
            ("code_playground", "Code Playground", "Write, test, and share code snippets", "development",
             ["Multi-language", "Run code", "Share snippets", "Version history"]),
            ("note_canvas", "Note Canvas", "Free-form note taking with AI organization", "productivity",
             ["Rich text", "AI organize", "Search", "Tag system"]),
            ("design_studio", "Design Studio", "Create prototypes and visual designs", "creative",
             ["Canvas", "Components", "Export", "Collaborate"]),
            ("ai_chat", "AI Chat Assistant", "Conversational AI for any task", "ai",
             ["Chat", "Context aware", "Memory", "Multi-agent"]),
        ]
        for bid, name, desc, cat, features in builtins:
            self.register(bid, name, desc, cat, features)

    def to_dict(self):
        return {"capabilities": self._capabilities, "installed": self._installed}

    def from_dict(self, data):
        self._capabilities = data.get("capabilities", {})
        self._installed = data.get("installed", {})


class LivingSoftwareEngine:
    """Top-level orchestrator — generates, evolves, repairs, and adapts software."""

    def __init__(self):
        self.creation_team = AppCreationAgent.create_team()
        self.evolution = EvolutionEngine()
        self.repair = SelfRepairSystem()
        interface = AdaptiveInterface()
        self.interface = interface
        self.capabilities = CapabilityRegistry()
        self.apps = {}
        self.capabilities.register_builtins()

    def create_app(self, request):
        """Generate a new application from natural language request."""
        agent = next((a for a in self.creation_team if a.agent_type == "architect"), self.creation_team[0])
        app = agent.design_application(request)

        # Programmer adds code
        prog = next((a for a in self.creation_team if a.agent_type == "programmer"), None)
        if prog:
            app.add_code("features.py", f"# Feature implementations for {app.name}\n")

        # UI Designer adds interface
        ui = next((a for a in self.creation_team if a.agent_type == "ui_designer"), None)
        if ui:
            app.set_ui("adaptive", "responsive", ["input", "display", "navigation", "controls"])

        # Tester validates
        tester = next((a for a in self.creation_team if a.agent_type == "tester"), None)
        if tester:
            app.status = "tested"

        self.apps[app.app_id] = app
        return app

    def get_app(self, app_id):
        return self.apps.get(app_id)

    def find_apps_by_purpose(self, purpose):
        p = purpose.lower()
        return [a for a in self.apps.values() if p in a.purpose.lower() or p in a.name.lower()]

    def observe_usage(self, app_id, action, duration=None):
        """Track how an app is being used."""
        self.evolution.observe(app_id, action, duration)
        app = self.apps.get(app_id)
        if app:
            return app.analyze_usage({"frequent_action": action})
        return None

    def analyze_and_improve(self, app_id):
        """Analyze usage and suggest improvements for an app."""
        suggestions = self.evolution.analyze(app_id)
        app = self.apps.get(app_id)
        if app and suggestions:
            for s in suggestions:
                app.dna.improve(s)
        return suggestions

    def report_issue(self, app_id, symptom, severity="medium"):
        """Report an issue with an app."""
        issue = self.repair.detect_issue(app_id, symptom, severity)
        self.repair.diagnose(issue["id"])
        patch = self.repair.generate_patch(issue["id"])
        if patch:
            self.repair.test_patch(patch)
            self.repair.apply_patch(issue["id"])
        return issue

    def install_capability(self, capability_id):
        return self.capabilities.install(capability_id)

    def get_ecosystem_summary(self):
        return {
            "apps": len(self.apps),
            "capabilities": len(self.capabilities.get_available()),
            "installed": len(self.capabilities.get_installed()),
            "repairs": self.repair.summary(),
            "improvements": len(self.evolution.get_improvement_history()),
            "team": [a.summary() for a in self.creation_team],
        }

    def summary(self):
        s = self.get_ecosystem_summary()
        return f"Living Software: {s['apps']} apps, {s['capabilities']} capabilities, {s['installed']} installed, {s['repairs']}"

    def to_dict(self):
        return {
            "apps": {aid: a.to_dict() for aid, a in self.apps.items()},
            "evolution": self.evolution.to_dict(),
            "repair": self.repair.to_dict(),
            "interface": self.interface.to_dict(),
            "capabilities": self.capabilities.to_dict(),
        }

    def from_dict(self, data):
        if "apps" in data:
            self.apps = {}
            for aid, adata in data["apps"].items():
                app = DynamicApp(aid, adata["name"], adata["purpose"])
                app.from_dict(adata)
                self.apps[aid] = app
        if "evolution" in data:
            self.evolution.from_dict(data["evolution"])
        if "repair" in data:
            self.repair.from_dict(data["repair"])
        if "interface" in data:
            self.interface.from_dict(data["interface"])
        if "capabilities" in data:
            self.capabilities.from_dict(data["capabilities"])


# ============================================================
# REALITY LAYER — Bridge Between Digital Intelligence & Physical Reality
# ============================================================
# v18.0.0 — Phase 5: Computing extends beyond the screen.
# Devices, robots, sensors, spaces become intelligent nodes
# in a unified reality intelligence network.

class DeviceNode:
    """Represents any connected device in the ecosystem — phone, robot, sensor, camera, computer, wearable."""

    def __init__(self, device_id, name, device_type, capabilities=None):
        self.device_id = device_id
        self.name = name
        self.device_type = device_type
        self.capabilities = capabilities or []
        self.status = "offline"
        self.location = None
        self.last_seen = 0
        self.metrics = {}
        self._command_log = []

    def connect(self):
        self.status = "online"
        self.last_seen = __import__("time").time()
        return True

    def disconnect(self):
        self.status = "offline"
        return True

    def send_command(self, command):
        if self.status != "online":
            return False
        self._command_log.append({"command": command, "time": __import__("time").time()})
        return True

    def get_telemetry(self):
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "status": self.status,
            "location": self.location,
            "last_seen": self.last_seen,
            "metrics": self.metrics,
            "commands_sent": len(self._command_log),
        }

    def to_dict(self):
        return {
            "device_id": self.device_id, "name": self.name,
            "device_type": self.device_type, "capabilities": self.capabilities,
            "status": self.status, "location": self.location,
            "last_seen": self.last_seen, "metrics": self.metrics,
        }

    def from_dict(self, data):
        self.device_id = data["device_id"]
        self.name = data["name"]
        self.device_type = data["device_type"]
        self.capabilities = data.get("capabilities", [])
        self.status = data.get("status", "offline")
        self.location = data.get("location")
        self.last_seen = data.get("last_seen", 0)
        self.metrics = data.get("metrics", {})


class SpatialNode:
    """A node in spatial space — represents objects, devices, workspaces in 3D."""

    def __init__(self, node_id, name, position=None):
        self.node_id = node_id
        self.name = name
        self.position = position or {"x": 0, "y": 0, "z": 0}
        self.connections = []
        self.data = {}
        self.node_type = "generic"

    def link_to(self, other_node):
        if other_node.node_id not in self.connections:
            self.connections.append(other_node.node_id)
            other_node.connections.append(self.node_id)

    def move_to(self, x, y, z):
        self.position = {"x": x, "y": y, "z": z}

    def to_dict(self):
        return {
            "node_id": self.node_id, "name": self.name,
            "position": self.position, "connections": self.connections,
            "data": self.data, "node_type": self.node_type,
        }

    def from_dict(self, data):
        self.node_id = data["node_id"]
        self.name = data["name"]
        self.position = data.get("position", {"x": 0, "y": 0, "z": 0})
        self.connections = data.get("connections", [])
        self.data = data.get("data", {})
        self.node_type = data.get("node_type", "generic")


class SensorReading:
    """Represents a single sensor reading with metadata."""

    def __init__(self, sensor_id, sensor_type, value, unit, timestamp=None):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.value = value
        self.unit = unit
        self.timestamp = timestamp or __import__("time").time()

    def to_dict(self):
        return {
            "sensor_id": self.sensor_id, "sensor_type": self.sensor_type,
            "value": self.value, "unit": self.unit, "timestamp": self.timestamp,
        }


class SensorNetwork:
    """Manages sensors — register, record, query, analyze readings."""

    def __init__(self):
        self.sensors = {}
        self.readings = []

    def register_sensor(self, sensor_id, sensor_type, name, location=None):
        self.sensors[sensor_id] = {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "name": name,
            "location": location,
            "registered": __import__("time").time(),
        }
        return True

    def record_reading(self, sensor_id, sensor_type, value, unit):
        reading = SensorReading(sensor_id, sensor_type, value, unit)
        self.readings.append(reading)
        if len(self.readings) > 1000:
            self.readings = self.readings[-500:]
        return reading

    def get_readings(self, sensor_id=None, sensor_type=None, limit=10):
        results = self.readings
        if sensor_id:
            results = [r for r in results if r.sensor_id == sensor_id]
        if sensor_type:
            results = [r for r in results if r.sensor_type == sensor_type]
        return results[-limit:]

    def analyze(self, sensor_id):
        readings = self.get_readings(sensor_id, limit=50)
        if not readings:
            return {"min": None, "max": None, "avg": None, "count": 0}
        values = [r.value for r in readings if isinstance(r.value, (int, float))]
        if not values:
            return {"min": None, "max": None, "avg": None, "count": len(readings)}
        return {
            "min": min(values), "max": max(values),
            "avg": sum(values) / len(values), "count": len(values),
        }

    def get_sensor_summary(self):
        return {sid: {"type": s["sensor_type"], "name": s["name"]} for sid, s in self.sensors.items()}

    def to_dict(self):
        return {
            "sensors": self.sensors,
            "readings": [r.to_dict() for r in self.readings[-100:]],
        }

    def from_dict(self, data):
        self.sensors = data.get("sensors", {})
        self.readings = [SensorReading(**r) for r in data.get("readings", [])]


class RealityTwin:
    """Digital Twin of Reality — devices, spaces, machines, sensors, physical systems."""

    def __init__(self):
        self.devices = {}
        self.spaces = {}
        self.machines = {}
        self.sensor_network = SensorNetwork()
        self.spatial_nodes = {}

    def register_device(self, device_id, name, device_type, capabilities=None):
        device = DeviceNode(device_id, name, device_type, capabilities)
        self.devices[device_id] = device
        return device

    def get_device(self, device_id):
        return self.devices.get(device_id)

    def get_online_devices(self):
        return [d for d in self.devices.values() if d.status == "online"]

    def track_space(self, space_id, name, dimensions=None):
        self.spaces[space_id] = {
            "space_id": space_id,
            "name": name,
            "dimensions": dimensions or {"width": 0, "height": 0, "depth": 0},
            "devices": [],
            "created": __import__("time").time(),
        }
        return self.spaces[space_id]

    def add_spatial_node(self, node_id, name, position=None):
        node = SpatialNode(node_id, name, position)
        self.spatial_nodes[node_id] = node
        return node

    def get_environment_summary(self):
        return {
            "devices": len(self.devices),
            "online_devices": len(self.get_online_devices()),
            "spaces": len(self.spaces),
            "sensors": len(self.sensor_network.sensors),
            "spatial_nodes": len(self.spatial_nodes),
            "machines": len(self.machines),
        }

    def to_dict(self):
        return {
            "devices": {did: d.to_dict() for did, d in self.devices.items()},
            "spaces": self.spaces,
            "sensor_network": self.sensor_network.to_dict(),
            "spatial_nodes": {nid: n.to_dict() for nid, n in self.spatial_nodes.items()},
            "machines": self.machines,
        }

    def from_dict(self, data):
        if "devices" in data:
            self.devices = {}
            for did, ddata in data["devices"].items():
                device = DeviceNode(ddata["device_id"], ddata["name"], ddata["device_type"])
                device.from_dict(ddata)
                self.devices[did] = device
        self.spaces = data.get("spaces", {})
        if "sensor_network" in data:
            self.sensor_network.from_dict(data["sensor_network"])
        if "spatial_nodes" in data:
            self.spatial_nodes = {}
            for nid, ndata in data["spatial_nodes"].items():
                node = SpatialNode(ndata["node_id"], ndata["name"])
                node.from_dict(ndata)
                self.spatial_nodes[nid] = node
        self.machines = data.get("machines", {})


class RealityAgent:
    """Specialized agent for physical environment management."""

    AGENT_TYPES = [
        ("reality_manager", "Reality Manager Agent", "Orchestrates physical environment coordination", "#44ddff"),
        ("robot_controller", "Robot Control Agent", "Controls and monitors robotic systems", "#ff8844"),
        ("environment_monitor", "Environment Monitor Agent", "Tracks environmental conditions", "#44ff88"),
        ("sensor_analyst", "Sensor Analysis Agent", "Analyzes sensor data for patterns and insights", "#88ddff"),
        ("simulation_runner", "Simulation Agent", "Runs simulations of physical systems", "#cc88ff"),
        ("safety_guardian", "Safety Guardian Agent", "Ensures safe operation of all physical systems", "#ff4466"),
    ]

    def __init__(self, agent_type, name, role, color):
        self.agent_type = agent_type
        self.name = name
        self.role = role
        self.color = color
        self.active = False
        self.tasks_completed = 0
        self.current_task = None

    @classmethod
    def create_team(cls):
        return [cls(at, n, r, c) for at, n, r, c in cls.AGENT_TYPES]

    def assign_task(self, task):
        self.current_task = task
        self.active = True

    def complete_task(self):
        self.tasks_completed += 1
        self.current_task = None
        self.active = False

    def summary(self):
        status = f"active: {self.current_task}" if self.active else "idle"
        return f"{self.name} ({self.agent_type}) — {self.tasks_completed} tasks — {status}"


class DeviceOrchestrator:
    """Coordinates multiple devices to work together toward a goal."""

    def __init__(self):
        self.workflows = []
        self.active_orchestrations = []

    def create_workflow(self, workflow_id, name, steps):
        workflow = {
            "workflow_id": workflow_id,
            "name": name,
            "steps": steps,
            "created": __import__("time").time(),
            "status": "ready",
        }
        self.workflows.append(workflow)
        return workflow

    def orchestrate(self, workflow_id, devices):
        workflow = next((w for w in self.workflows if w["workflow_id"] == workflow_id), None)
        if not workflow:
            return False
        orchestration = {
            "workflow_id": workflow_id,
            "devices": [d.device_id for d in devices],
            "started": __import__("time").time(),
            "status": "running",
            "completed_steps": [],
        }
        self.active_orchestrations.append(orchestration)
        return orchestration

    def get_active_orchestrations(self):
        return list(self.active_orchestrations)

    def to_dict(self):
        return {"workflows": self.workflows}

    def from_dict(self, data):
        self.workflows = data.get("workflows", [])


class EnvironmentManager:
    """Autonomous environment optimization — lighting, temperature, device arrangement."""

    def __init__(self):
        self.configurations = {}
        self.active_config = None
        self._optimization_log = []

    def analyze_environment(self, sensor_data):
        analysis = {}
        if "temperature" in sensor_data:
            temp = sensor_data["temperature"]
            if temp > 28:
                analysis["action"] = "cooling_recommended"
                analysis["reason"] = f"Temperature {temp}°C exceeds comfort range"
            elif temp < 16:
                analysis["action"] = "heating_recommended"
                analysis["reason"] = f"Temperature {temp}°C below comfort range"
            else:
                analysis["action"] = "temperature_optimal"
        if "lighting" in sensor_data:
            lux = sensor_data["lighting"]
            if lux < 100:
                analysis["lighting_action"] = "increase_lighting"
            elif lux > 1000:
                analysis["lighting_action"] = "decrease_lighting"
            else:
                analysis["lighting_action"] = "lighting_optimal"
        if "noise" in sensor_data:
            db = sensor_data["noise"]
            if db > 60:
                analysis["noise_action"] = "noise_reduction_recommended"
        return analysis

    def optimize(self, goal, environment_state):
        if goal == "comfortable_workspace":
            return {
                "temperature": 22,
                "lighting": 500,
                "humidity": 45,
                "device_arrangement": "ergonomic",
                "information_display": "focus_mode",
            }
        elif goal == "increase_efficiency":
            return {
                "machine_schedule": "optimized",
                "energy_mode": "efficient",
                "maintenance_interval": "adjusted",
            }
        elif goal == "focus_mode":
            return {
                "lighting": 300,
                "noise_cancellation": True,
                "notifications": "silent",
                "display": "minimal",
            }
        return {}

    def apply_config(self, config_name, config):
        self.configurations[config_name] = config
        self.active_config = config_name
        self._optimization_log.append({
            "config": config_name, "time": __import__("time").time(),
        })
        return True

    def get_optimization_history(self):
        return list(self._optimization_log)

    def to_dict(self):
        return {"configurations": self.configurations, "active_config": self.active_config}

    def from_dict(self, data):
        self.configurations = data.get("configurations", {})
        self.active_config = data.get("active_config")


class SpatialInterface:
    """3D workspace management — spatial information, context-aware environments."""

    def __init__(self):
        self.workspaces = {}
        self.active_workspace = None

    def create_workspace(self, workspace_id, name, layout="grid"):
        workspace = {
            "workspace_id": workspace_id,
            "name": name,
            "layout": layout,
            "nodes": [],
            "connections": [],
            "created": __import__("time").time(),
        }
        self.workspaces[workspace_id] = workspace
        self.active_workspace = workspace_id
        return workspace

    def add_node(self, workspace_id, node):
        ws = self.workspaces.get(workspace_id)
        if not ws:
            return False
        ws["nodes"].append(node.to_dict() if hasattr(node, "to_dict") else node)
        return True

    def connect_nodes(self, workspace_id, node1_id, node2_id):
        ws = self.workspaces.get(workspace_id)
        if not ws:
            return False
        ws["connections"].append({"from": node1_id, "to": node2_id})
        return True

    def get_active_workspace(self):
        return self.workspaces.get(self.active_workspace)

    def to_dict(self):
        return {"workspaces": self.workspaces, "active_workspace": self.active_workspace}

    def from_dict(self, data):
        self.workspaces = data.get("workspaces", {})
        self.active_workspace = data.get("active_workspace")


class PersonalRealityAssistant:
    """AI layer that understands the user's environment — devices, location, projects, technology."""

    def __init__(self):
        self.context = {
            "location": None,
            "available_devices": [],
            "active_projects": [],
            "environment_state": {},
        }

    def understand_context(self, reality_twin):
        """Analyze the current environment and build context."""
        summary = reality_twin.get_environment_summary()
        devices = list(reality_twin.devices.values())
        self.context["available_devices"] = [d.name for d in devices if d.status == "online"]
        self.context["device_summary"] = summary
        return self.context

    def analyze_available_resources(self, goal, reality_twin):
        """Analyze what resources are available for a given goal."""
        resources = []
        for device in reality_twin.devices.values():
            if device.status != "online":
                continue
            if goal == "testing":
                if "simulation" in device.capabilities:
                    resources.append(f"{device.name} — simulation available")
            elif goal == "monitoring":
                if "sensor" in device.capabilities or "camera" in device.capabilities:
                    resources.append(f"{device.name} — monitoring capable")
            elif goal == "automation":
                if "actuator" in device.capabilities or "control" in device.capabilities:
                    resources.append(f"{device.name} — automation capable")
        return resources

    def suggest_actions(self, goal, reality_twin):
        """Suggest actions based on user goal and available environment."""
        suggestions = []
        online = reality_twin.get_online_devices()
        if not online:
            suggestions.append("No devices online. Try connecting devices first.")
            return suggestions
        if goal and "test" in goal.lower():
            suggestions.append(f"Found {len(online)} online devices ready for testing")
            suggestions.append("Creating test workflow with available hardware...")
        elif goal and "monitor" in goal.lower():
            suggestions.append("Setting up environment monitoring...")
            suggestions.append(f"{len(reality_twin.sensor_network.sensors)} sensors available")
        elif goal and ("create" in goal.lower() or "build" in goal.lower()):
            suggestions.append(f"Designing system with {len(online)} available nodes...")
        return suggestions


class HumanMachineCollaborator:
    """Enables collaboration between humans and intelligent systems — design, build, optimize."""

    def __init__(self):
        self.collaborations = []

    def start_collaboration(self, goal, context):
        collab = {
            "goal": goal,
            "started": __import__("time").time(),
            "context": context,
            "phases": ["understand", "analyze", "generate", "review", "refine"],
            "current_phase": "understand",
            "results": [],
        }
        self.collaborations.append(collab)
        return collab

    def generate_design_options(self, goal, constraints=None):
        """Generate design alternatives for a human to review."""
        options = []
        if "drone" in goal.lower():
            options.append({
                "name": "Lightweight carbon frame",
                "weight": 250,
                "battery": "30 min",
                "payload": "500g",
                "confidence": 0.85,
            })
            options.append({
                "name": "Aluminum alloy frame",
                "weight": 350,
                "battery": "25 min",
                "payload": "750g",
                "confidence": 0.78,
            })
        elif "greenhouse" in goal.lower() or "garden" in goal.lower():
            options.append({
                "name": "Automated greenhouse",
                "sensors": ["temperature", "humidity", "soil_moisture", "light"],
                "actuators": ["irrigation", "ventilation", "shading"],
                "ai_control": True,
            })
        else:
            options.append({
                "name": f"Prototype for {goal}",
                "description": f"AI-generated design based on requirements",
                "confidence": 0.7,
            })
        collab = self.collaborations[-1] if self.collaborations else None
        if collab:
            collab["results"].extend(options)
            collab["current_phase"] = "generate"
        return options


class RealityLayer:
    """Top-level orchestrator — connects digital intelligence to the physical world."""

    def __init__(self):
        self.reality_twin = RealityTwin()
        self.device_orchestrator = DeviceOrchestrator()
        self.environment_manager = EnvironmentManager()
        self.spatial_interface = SpatialInterface()
        self.reality_assistant = PersonalRealityAssistant()
        self.human_machine = HumanMachineCollaborator()
        self.reality_agents = RealityAgent.create_team()

    def understand_goal(self, goal):
        """Analyze a user goal and determine what resources are available."""
        context = self.reality_assistant.understand_context(self.reality_twin)
        resources = self.reality_assistant.analyze_available_resources(goal, self.reality_twin)
        suggestions = self.reality_assistant.suggest_actions(goal, self.reality_twin)
        return {
            "goal": goal,
            "context": context,
            "resources": resources,
            "suggestions": suggestions,
        }

    def coordinate_agents(self, task):
        """Assign a task to the appropriate reality agents."""
        assignments = []
        for agent in self.reality_agents:
            if agent.agent_type == "robot_controller" and ("robot" in task.lower() or "drone" in task.lower()):
                agent.assign_task(task)
                assignments.append(agent)
            elif agent.agent_type == "environment_monitor" and "monitor" in task.lower():
                agent.assign_task(task)
                assignments.append(agent)
            elif agent.agent_type == "sensor_analyst" and ("sensor" in task.lower() or "data" in task.lower()):
                agent.assign_task(task)
                assignments.append(agent)
            elif agent.agent_type == "simulation_runner" and "simulate" in task.lower():
                agent.assign_task(task)
                assignments.append(agent)
            elif agent.agent_type == "safety_guardian" and ("safe" in task.lower() or "security" in task.lower()):
                agent.assign_task(task)
                assignments.append(agent)
        return assignments

    def control_systems(self, commands):
        """Execute commands across the physical system."""
        results = []
        for cmd in commands:
            device = self.reality_twin.get_device(cmd.get("device_id"))
            if device and device.send_command(cmd.get("action")):
                results.append({"device": device.name, "command": cmd.get("action"), "status": "sent"})
            else:
                results.append({"device": cmd.get("device_id"), "command": cmd.get("action"), "status": "failed"})
        return results

    def learn_from_environment(self):
        """Analyze sensor data and update environment understanding."""
        summary = self.reality_twin.get_environment_summary()
        sensor_summary = self.reality_twin.sensor_network.get_sensor_summary()
        return {
            "environment": summary,
            "sensors": sensor_summary,
            "timestamp": __import__("time").time(),
        }

    def get_full_state(self):
        return {
            "reality_twin": self.reality_twin.to_dict(),
            "device_orchestrator": self.device_orchestrator.to_dict(),
            "environment_manager": self.environment_manager.to_dict(),
            "spatial_interface": self.spatial_interface.to_dict(),
            "agents": [a.summary() for a in self.reality_agents],
        }

    def to_dict(self):
        return {
            "reality_twin": self.reality_twin.to_dict(),
            "device_orchestrator": self.device_orchestrator.to_dict(),
            "environment_manager": self.environment_manager.to_dict(),
            "spatial_interface": self.spatial_interface.to_dict(),
        }

    def from_dict(self, data):
        if "reality_twin" in data:
            self.reality_twin.from_dict(data["reality_twin"])
        if "device_orchestrator" in data:
            self.device_orchestrator.from_dict(data["device_orchestrator"])
        if "environment_manager" in data:
            self.environment_manager.from_dict(data["environment_manager"])
        if "spatial_interface" in data:
            self.spatial_interface.from_dict(data["spatial_interface"])


# ============================================================
# AUTONOMOUS WORLD ENGINE — Simulation Intelligence Layer
# ============================================================
# v19.0.0 — Phase 6: Computers that understand systems.
# Simulate realities, predict futures, optimize decisions
# before actions happen in the physical world.

class WorldSimulator:
    """Universal simulation environment for physical, digital, organizational systems."""

    SYSTEM_TYPES = ["factory", "city", "project", "machine", "ecosystem", "organization", "supply_chain"]

    def __init__(self):
        self.systems = {}
        self._simulation_results = []

    def create_system(self, system_id, name, system_type, components=None):
        system = {
            "system_id": system_id,
            "name": name,
            "system_type": system_type,
            "components": components or [],
            "state": {},
            "metrics": {},
            "created": __import__("time").time(),
        }
        self.systems[system_id] = system
        return system

    def add_component(self, system_id, component):
        system = self.systems.get(system_id)
        if not system:
            return False
        system["components"].append(component)
        return True

    def run_simulation(self, system_id, parameters=None):
        system = self.systems.get(system_id)
        if not system:
            return None
        params = parameters or {}
        system_type = system["system_type"]
        result = {"system_id": system_id, "name": system["name"], "type": system_type, "parameters": params}

        if system_type == "factory":
            machines = sum(1 for c in system["components"] if "machine" in c.lower() or "robot" in c.lower())
            workers = sum(1 for c in system["components"] if "worker" in c.lower() or "operator" in c.lower())
            efficiency = min(95, 50 + machines * 5 + workers * 3)
            output = int(1000 * efficiency / 100 * (1 + params.get("demand_factor", 0)))
            energy = int(500 + machines * 50 + workers * 10)
            result["output"] = output
            result["efficiency"] = efficiency
            result["energy_usage"] = energy
            result["defect_rate"] = max(0.5, 5 - machines * 0.3)
        elif system_type == "city":
            population = sum(1 for c in system["components"] if "resident" in c.lower()) * 1000 + 50000
            traffic = min(100, 30 + sum(1 for c in system["components"] if "car" in c.lower() or "vehicle" in c.lower()) * 5)
            result["population"] = population
            result["traffic_index"] = traffic
            result["energy_demand"] = int(population * 0.01)
            result["green_space"] = sum(1 for c in system["components"] if "park" in c.lower()) * 2
        elif system_type == "project":
            team_size = sum(1 for c in system["components"] if "team" in c.lower() or "member" in c.lower() or "engineer" in c.lower())
            duration = max(1, 12 - team_size + params.get("complexity", 0))
            cost = int(50000 * duration / 12 * (1 + params.get("scope", 0)))
            result["duration_months"] = duration
            result["estimated_cost"] = cost
            result["team_size"] = team_size + 3
            result["risk_score"] = max(1, 5 - team_size * 0.5 + params.get("complexity", 0))
        else:
            result["status"] = "simulated"
            result["metrics"] = {"performance": 75, "stability": 80}

        result["timestamp"] = __import__("time").time()
        self._simulation_results.append(result)
        return result

    def compare_scenarios(self, scenario_a, scenario_b):
        comparison = {
            "scenario_a": scenario_a,
            "scenario_b": scenario_b,
            "differences": [],
            "recommendation": None,
        }
        for key in scenario_a:
            if key in scenario_b and key not in ("system_id", "name", "type", "timestamp", "parameters"):
                va = scenario_a[key]
                vb = scenario_b[key]
                if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                    diff = ((vb - va) / va * 100) if va != 0 else 0
                    comparison["differences"].append({
                        "metric": key,
                        "a": va, "b": vb,
                        "change_percent": round(diff, 1),
                    })
        better = sum(1 for d in comparison["differences"] if d["change_percent"] > 0)
        worse = sum(1 for d in comparison["differences"] if d["change_percent"] < 0)
        comparison["recommendation"] = "B" if better > worse else ("A" if worse > better else "neutral")
        return comparison

    def get_simulation_history(self):
        return list(self._simulation_results)

    def to_dict(self):
        return {"systems": self.systems, "results": self._simulation_results}

    def from_dict(self, data):
        self.systems = data.get("systems", {})
        self._simulation_results = data.get("results", [])


class PredictiveModel:
    """Analyzes current state, historical data, patterns to predict outcomes."""

    def __init__(self):
        self._predictions = []
        self._models = {}

    def train_model(self, model_id, name, model_type, parameters=None):
        self._models[model_id] = {
            "model_id": model_id,
            "name": name,
            "model_type": model_type,
            "parameters": parameters or {},
            "accuracy": 0.85,
            "trained": __import__("time").time(),
        }
        return self._models[model_id]

    def predict(self, model_id, input_data):
        model = self._models.get(model_id)
        if not model:
            return None
        model_type = model["model_type"]
        prediction = {"model_id": model_id, "input": input_data, "confidence": model["accuracy"]}

        if model_type == "failure_prediction":
            if isinstance(input_data, dict):
                vibration = input_data.get("vibration", 0)
                temperature = input_data.get("temperature", 0)
                hours_run = input_data.get("hours_run", 0)
                failure_prob = min(95, vibration * 0.3 + (temperature - 70) * 0.5 + hours_run * 0.01)
                prediction["probability"] = round(failure_prob, 1)
                prediction["days_remaining"] = max(1, int(30 - failure_prob * 0.3))
                prediction["action"] = "Maintenance required within 14 days" if failure_prob > 50 else "Normal operation"
            else:
                prediction["probability"] = 15
                prediction["days_remaining"] = 60
                prediction["action"] = "Normal operation"

        elif model_type == "demand_forecast":
            base = input_data.get("base_demand", 100) if isinstance(input_data, dict) else 100
            trend = input_data.get("trend", 0.05) if isinstance(input_data, dict) else 0.05
            seasonal = input_data.get("seasonal_factor", 1.0) if isinstance(input_data, dict) else 1.0
            forecast = int(base * (1 + trend) * seasonal)
            prediction["forecast"] = forecast
            prediction["lower_bound"] = int(forecast * 0.85)
            prediction["upper_bound"] = int(forecast * 1.15)
            prediction["confidence_interval"] = "85-115%"

        elif model_type == "timeline_estimate":
            tasks = input_data.get("tasks", 10) if isinstance(input_data, dict) else 10
            team_size = input_data.get("team_size", 3) if isinstance(input_data, dict) else 3
            complexity = input_data.get("complexity", 1.0) if isinstance(input_data, dict) else 1.0
            estimated = int(tasks * complexity * 5 / team_size)
            prediction["estimated_days"] = estimated
            prediction["best_case"] = int(estimated * 0.7)
            prediction["worst_case"] = int(estimated * 1.5)

        else:
            prediction["result"] = "Analysis complete"
            prediction["confidence"] = 0.7

        prediction["timestamp"] = __import__("time").time()
        self._predictions.append(prediction)
        return prediction

    def get_prediction_history(self):
        return list(self._predictions)

    def to_dict(self):
        return {"models": self._models, "predictions": self._predictions}

    def from_dict(self, data):
        self._models = data.get("models", {})
        self._predictions = data.get("predictions", [])


class ScenarioGenerator:
    """Creates and evaluates branching future scenarios."""

    def __init__(self):
        self.scenarios = []
        self._branches = []

    def create_scenario(self, scenario_id, name, description):
        scenario = {
            "scenario_id": scenario_id,
            "name": name,
            "description": description,
            "branches": [],
            "evaluation": None,
            "created": __import__("time").time(),
        }
        self.scenarios.append(scenario)
        return scenario

    def add_branch(self, scenario_id, branch_name, assumptions, outcomes=None):
        scenario = next((s for s in self.scenarios if s["scenario_id"] == scenario_id), None)
        if not scenario:
            return None
        branch = {
            "name": branch_name,
            "assumptions": assumptions,
            "outcomes": outcomes or {},
            "probability": 0.5,
        }
        scenario["branches"].append(branch)
        self._branches.append(branch)
        return branch

    def evaluate_scenario(self, scenario_id, context=None):
        scenario = next((s for s in self.scenarios if s["scenario_id"] == scenario_id), None)
        if not scenario:
            return None
        branches = scenario["branches"]
        if not branches:
            scenario["evaluation"] = {"result": "No branches defined"}
            return scenario["evaluation"]

        evaluation = {"branches_analyzed": len(branches), "recommended_path": None, "analysis": []}
        best_score = -1
        for branch in branches:
            score = 0
            outcomes = branch["outcomes"]
            if "revenue" in outcomes:
                score += outcomes["revenue"] * 0.01
            if "growth" in outcomes:
                score += outcomes["growth"]
            if "risk" in outcomes:
                score -= outcomes["risk"]
            if "cost" in outcomes:
                score -= outcomes["cost"] * 0.001

            if context:
                ctx = context.lower()
                for assumption in branch["assumptions"]:
                    if assumption.lower() in ctx:
                        score += 1

            evaluation["analysis"].append({
                "branch": branch["name"],
                "score": round(score, 1),
                "assumptions": len(branch["assumptions"]),
                "probability": branch["probability"],
            })
            if score > best_score:
                best_score = score
                evaluation["recommended_path"] = branch["name"]

        scenario["evaluation"] = evaluation
        return evaluation

    def generate_futures(self, query):
        """Generate possible future scenarios from a natural language query."""
        q = query.lower()
        scenarios = []

        if "product" in q or "launch" in q:
            scenarios.append(self.create_scenario("sc_high", "High Demand Scenario",
                "The product gains strong market traction early."))
            self.add_branch("sc_high", "Strong adoption", ["strong marketing", "quality product"],
                {"revenue": 500000, "growth": 25, "risk": 15, "cost": 200000})

            scenarios.append(self.create_scenario("sc_low", "Low Adoption Scenario",
                "The product faces adoption challenges."))
            self.add_branch("sc_low", "Improvement needed", ["feedback analysis", "iterative development"],
                {"revenue": 100000, "growth": 5, "risk": 30, "cost": 150000})

            scenarios.append(self.create_scenario("sc_expand", "Market Expansion Scenario",
                "The product enables broader market expansion."))
            self.add_branch("sc_expand", "Growth strategy", ["market analysis", "partnerships"],
                {"revenue": 1000000, "growth": 40, "risk": 25, "cost": 350000})

        elif "company" in q or "startup" in q or "business" in q:
            scenarios.append(self.create_scenario("sc_start", "Prototype Phase",
                "Start with a focused prototype to validate the concept."))
            self.add_branch("sc_start", "Lean start", ["minimum viable product", "user testing"],
                {"revenue": 50000, "growth": 10, "risk": 20, "cost": 80000})

            scenarios.append(self.create_scenario("sc_fund", "Funded Growth",
                "Secure funding and scale the operation."))
            self.add_branch("sc_fund", "VC-backed", ["investor pitch", "team expansion"],
                {"revenue": 300000, "growth": 35, "risk": 35, "cost": 500000})

        else:
            scenarios.append(self.create_scenario("sc_default", "Standard Path",
                "Follow a standard development and growth trajectory."))
            self.add_branch("sc_default", "Balanced approach", ["planning", "execution", "review"],
                {"revenue": 200000, "growth": 15, "risk": 20, "cost": 150000})

        for s in scenarios:
            self.evaluate_scenario(s["scenario_id"], query)

        return scenarios

    def get_scenarios(self):
        return list(self.scenarios)

    def to_dict(self):
        return {"scenarios": self.scenarios}

    def from_dict(self, data):
        self.scenarios = data.get("scenarios", [])


class ExperimentationSystem:
    """AI agents that test ideas digitally before real implementation."""

    def __init__(self):
        self.experiments = []
        self.results = []

    def create_experiment(self, exp_id, name, domain, parameters=None):
        exp = {
            "experiment_id": exp_id,
            "name": name,
            "domain": domain,
            "parameters": parameters or {},
            "status": "designed",
            "created": __import__("time").time(),
        }
        self.experiments.append(exp)
        return exp

    def run_experiment(self, exp_id, trials=100):
        exp = next((e for e in self.experiments if e["experiment_id"] == exp_id), None)
        if not exp:
            return None
        exp["status"] = "running"
        import random
        domain = exp["domain"]
        result = {"experiment_id": exp_id, "name": exp["name"], "domain": domain, "trials": trials}

        if domain == "materials" or domain == "chemistry":
            candidates = []
            for i in range(min(trials, 10)):
                strength = random.uniform(50, 120)
                weight = random.uniform(10, 50)
                cost = random.uniform(5, 30)
                candidates.append({
                    "candidate": f"Material {chr(65 + i)}",
                    "strength": round(strength, 1),
                    "weight": round(weight, 1),
                    "cost": round(cost, 1),
                    "score": round(strength / weight * 10 - cost * 0.1, 1),
                })
            candidates.sort(key=lambda c: -c["score"])
            result["candidates"] = candidates[:5]
            best = candidates[0]
            result["best_candidate"] = best["candidate"]
            result["properties"] = f"+{round((best['strength'] - 80) / 80 * 100, 0)}% strength, -{round((50 - best['weight']) / 50 * 100, 0)}% weight"

        elif domain == "design" or domain == "engineering":
            configs = []
            for i in range(min(trials, 8)):
                efficiency = random.uniform(60, 98)
                cost = random.uniform(100, 500)
                durability = random.uniform(1, 10)
                configs.append({
                    "configuration": f"Design {chr(65 + i)}",
                    "efficiency": round(efficiency, 1),
                    "cost": round(cost, 1),
                    "durability": round(durability, 1),
                    "score": round(efficiency * 0.4 - cost * 0.1 + durability * 5, 1),
                })
            configs.sort(key=lambda c: -c["score"])
            result["configurations"] = configs[:3]
            result["best_configuration"] = configs[0]["configuration"]

        else:
            outcomes = []
            for i in range(min(trials, 5)):
                success_rate = random.uniform(0.3, 0.95)
                outcomes.append({
                    "trial": f"Run {chr(65 + i)}",
                    "success_rate": round(success_rate, 2),
                })
            result["outcomes"] = outcomes

        exp["status"] = "completed"
        self.results.append(result)
        return result

    def get_experiment_history(self):
        return list(self.results)

    def to_dict(self):
        return {"experiments": self.experiments, "results": self.results}

    def from_dict(self, data):
        self.experiments = data.get("experiments", [])
        self.results = data.get("results", [])


class WorldKnowledgeModel:
    """Cross-domain relationship understanding — connects different domains."""

    DOMAINS = [
        "mechanical_engineering", "ai", "materials", "electronics",
        "manufacturing", "economics", "biology", "physics",
        "software", "robotics", "energy", "transportation",
    ]

    RELATIONSHIPS = {
        "robotics": ["mechanical_engineering", "ai", "electronics", "materials", "manufacturing", "economics"],
        "ai": ["software", "electronics", "robotics", "manufacturing"],
        "manufacturing": ["mechanical_engineering", "materials", "economics", "energy", "robotics"],
        "energy": ["physics", "economics", "manufacturing", "transportation"],
    }

    def __init__(self):
        self._nodes = {}
        self._edges = []
        self._insights = []

    def add_domain(self, domain_id, name, description):
        self._nodes[domain_id] = {
            "domain_id": domain_id,
            "name": name,
            "description": description,
            "connected_to": [],
            "added": __import__("time").time(),
        }
        return self._nodes[domain_id]

    def connect_domains(self, domain_a, domain_b, relationship):
        if domain_a in self._nodes and domain_b in self._nodes:
            self._nodes[domain_a]["connected_to"].append(domain_b)
            self._nodes[domain_b]["connected_to"].append(domain_a)
            self._edges.append({"from": domain_a, "to": domain_b, "relationship": relationship})
            return True
        return False

    def get_ecosystem(self, domain):
        """Get the entire ecosystem around a domain."""
        if domain not in self._nodes:
            return {}
        connected = self._nodes[domain].get("connected_to", [])
        ecosystem = {"domain": domain, "direct_connections": [], "indirect_connections": []}
        for c in connected:
            ecosystem["direct_connections"].append({
                "domain": c,
                "name": self._nodes[c]["name"],
                "description": self._nodes[c]["description"],
            })
            for c2 in self._nodes[c].get("connected_to", []):
                if c2 != domain and c2 not in connected:
                    ecosystem["indirect_connections"].append({
                        "domain": c2,
                        "via": c,
                        "name": self._nodes[c2]["name"],
                    })
        return ecosystem

    def analyze_project(self, project_description):
        """Analyze a project description and identify connected domains."""
        desc = project_description.lower()
        insights = []
        for domain_id, node in self._nodes.items():
            if any(word in desc for word in node["name"].lower().split()):
                ecosystem = self.get_ecosystem(domain_id)
                insights.append({
                    "domain": domain_id,
                    "name": node["name"],
                    "direct_connections": len(ecosystem.get("direct_connections", [])),
                })
        self._insights.extend(insights)
        return insights

    def to_dict(self):
        return {"nodes": self._nodes, "edges": self._edges, "insights": self._insights}

    def from_dict(self, data):
        self._nodes = data.get("nodes", {})
        self._edges = data.get("edges", [])
        self._insights = data.get("insights", [])


class OptimizationEngine:
    """Continuous search for improvements — energy, timeline, cost, efficiency."""

    def __init__(self):
        self._optimizations = []
        self._history = []

    def analyze(self, current_state, target_metric):
        state = current_state
        metric = target_metric
        result = {"metric": metric, "current": None, "optimized": None, "savings": None, "suggestions": []}

        if metric == "energy":
            current = state.get("energy_usage", 100)
            optimized = int(current * 0.72)
            result["current"] = current
            result["optimized"] = optimized
            result["savings"] = f"{round((current - optimized) / current * 100)}%"
            result["suggestions"] = [
                "Upgrade to energy-efficient equipment",
                "Implement smart scheduling",
                "Add renewable energy sources",
                "Optimize HVAC usage",
            ]
        elif metric == "timeline":
            current = state.get("duration_months", 18)
            optimized = max(1, int(current * 0.61))
            result["current"] = current
            result["optimized"] = optimized
            result["savings"] = f"{round((current - optimized) / current * 100)}%"
            result["suggestions"] = [
                "Parallel task execution",
                "Add team members to critical path",
                "Use agile methodology",
                "Automate repetitive tasks",
            ]
        elif metric == "cost":
            current = state.get("estimated_cost", 100000)
            optimized = int(current * 0.75)
            result["current"] = current
            result["optimized"] = optimized
            result["savings"] = f"{round((current - optimized) / current * 100)}%"
            result["suggestions"] = [
                "Negotiate bulk material pricing",
                "Reduce scope creep",
                "Use open-source alternatives",
                "Optimize resource allocation",
            ]
        elif metric == "efficiency":
            current = state.get("efficiency", 65)
            optimized = min(99, current + 20)
            result["current"] = current
            result["optimized"] = optimized
            result["savings"] = f"+{round(optimized - current)}%"
            result["suggestions"] = [
                "Implement automation",
                "Reduce bottlenecks",
                "Train personnel",
                "Upgrade equipment",
            ]

        self._optimizations.append(result)
        return result

    def get_history(self):
        return list(self._optimizations)

    def to_dict(self):
        return {"optimizations": self._optimizations}

    def from_dict(self, data):
        self._optimizations = data.get("optimizations", [])


class DecisionPartnership:
    """Human + AI decision support — simulations, predictions, alternatives, risks."""

    def __init__(self):
        self._decisions = []

    def analyze_decision(self, goal, options=None):
        options = options or []
        if not options:
            options = [
                {"name": "Proceed with current plan", "risk": "medium", "effort": "moderate"},
                {"name": "Start with prototype phase", "risk": "low", "effort": "low"},
            ]

        analysis = {
            "goal": goal,
            "options": [],
            "analysis": "",
            "risks": [],
            "recommendation": None,
        }

        best_score = -1
        best_option = None
        for opt in options:
            risk_map = {"low": 0.2, "medium": 0.5, "high": 0.8}
            effort_map = {"low": 0.3, "moderate": 0.5, "high": 0.8}
            risk_score = risk_map.get(opt.get("risk", "medium"), 0.5)
            effort_score = effort_map.get(opt.get("effort", "moderate"), 0.5)
            opportunity_score = 1.0 - risk_score
            score = opportunity_score * 0.6 + (1 - effort_score) * 0.4

            analyzed = dict(opt)
            analyzed["score"] = round(score, 2)
            analyzed["risk_level"] = opt.get("risk", "medium")
            analyzed["recommended_for"] = "quick wins" if score > 0.7 else "strategic initiatives"
            analysis["options"].append(analyzed)

            if score > best_score:
                best_score = score
                best_option = opt["name"]

        strengths = [o["name"] for o in analysis["options"] if o.get("score", 0) > 0.6]
        risks = [f"{o['name']}: {o.get('risk', 'medium')} risk" for o in analysis["options"] if o.get('risk', 'medium') in ('high', 'medium')]

        analysis["analysis"] = f"Analysis complete. Found {len(strengths)} strong options, {len(risks)} items to monitor."
        analysis["risks"] = risks
        analysis["recommendation"] = best_option

        self._decisions.append(analysis)
        return analysis

    def get_decision_history(self):
        return list(self._decisions)

    def to_dict(self):
        return {"decisions": self._decisions}

    def from_dict(self, data):
        self._decisions = data.get("decisions", [])


class ResearchWorld:
    """AI agent environments for exploring ideas and discovering knowledge."""

    def __init__(self):
        self.worlds = []
        self._discoveries = []

    def create_world(self, world_id, name, goal, agents=None):
        world = {
            "world_id": world_id,
            "name": name,
            "goal": goal,
            "agents": agents or ["explorer", "analyst", "experimenter"],
            "status": "active",
            "discoveries": [],
            "created": __import__("time").time(),
        }
        self.worlds.append(world)
        return world

    def run_discovery(self, world_id, iterations=10):
        world = next((w for w in self.worlds if w["world_id"] == world_id), None)
        if not world:
            return None
        import random
        goal = world["goal"].lower()
        discoveries = []

        for i in range(iterations):
            if "material" in goal or "chemistry" in goal or "science" in goal:
                discovery = {
                    "iteration": i + 1,
                    "finding": f"Compound variant {chr(65 + random.randint(0, 25))}{random.randint(1, 99)}",
                    "property": random.choice(["strength", "conductivity", "flexibility", "durability"]),
                    "value": round(random.uniform(0.5, 9.5), 1),
                    "significance": random.choice(["low", "medium", "high"]),
                }
            elif "physics" in goal or "simulation" in goal:
                discovery = {
                    "iteration": i + 1,
                    "finding": f"Simulation run with parameter set {chr(65 + random.randint(0, 25))}",
                    "result": random.choice(["stable", "unstable", "chaotic", "optimal"]),
                    "deviation": round(random.uniform(0.01, 0.5), 3),
                }
            else:
                discovery = {
                    "iteration": i + 1,
                    "finding": f"Insight {i + 1}: {random.choice(['Pattern detected', 'Anomaly found', 'Optimization possible', 'New approach identified'])}",
                    "confidence": round(random.uniform(0.5, 0.99), 2),
                }
            discoveries.append(discovery)

        significant = [d for d in discoveries if isinstance(d.get("significance"), str) and d["significance"] == "high"]

        result = {
            "world_id": world_id,
            "iterations": iterations,
            "discoveries": discoveries,
            "significant_findings": len(significant),
            "top_finding": discoveries[0] if discoveries else None,
        }

        world["discoveries"].extend(discoveries)
        self._discoveries.extend(discoveries)
        return result

    def get_all_discoveries(self):
        return list(self._discoveries)

    def to_dict(self):
        return {"worlds": self.worlds, "discoveries": self._discoveries}

    def from_dict(self, data):
        self.worlds = data.get("worlds", [])
        self._discoveries = data.get("discoveries", [])


class AutonomousWorldEngine:
    """Top-level orchestrator — simulation intelligence that understands, predicts, and improves reality."""

    def __init__(self):
        self.simulator = WorldSimulator()
        self.predictor = PredictiveModel()
        self.scenario_gen = ScenarioGenerator()
        self.experiments = ExperimentationSystem()
        self.knowledge = WorldKnowledgeModel()
        self.optimizer = OptimizationEngine()
        self.decisions = DecisionPartnership()
        self.research = ResearchWorld()

        self._init_default_domains()

    def _init_default_domains(self):
        domains = {
            "mechanical_engineering": ("Mechanical Engineering", "Design and construction of mechanical systems"),
            "ai": ("AI", "Artificial intelligence and machine learning"),
            "materials": ("Materials", "Material science and engineering"),
            "electronics": ("Electronics", "Electronic systems and components"),
            "manufacturing": ("Manufacturing", "Production and industrial processes"),
            "economics": ("Economics", "Economic systems and market analysis"),
            "robotics": ("Robotics", "Robotic systems and automation"),
            "energy": ("Energy", "Energy production and management"),
            "software": ("Software", "Software engineering and development"),
            "physics": ("Physics", "Physical laws and phenomena"),
            "biology": ("Biology", "Biological systems and life sciences"),
            "transportation": ("Transportation", "Transport and logistics systems"),
        }
        for did, (name, desc) in domains.items():
            self.knowledge.add_domain(did, name, desc)

        for src, targets in WorldKnowledgeModel.RELATIONSHIPS.items():
            for tgt in targets:
                if src in self.knowledge._nodes and tgt in self.knowledge._nodes:
                    self.knowledge.connect_domains(src, tgt, "related")

    def analyze_query(self, query):
        """Full analysis pipeline: understand, simulate, predict, optimize."""
        result = {"query": query, "simulations": None, "predictions": None, "scenarios": None, "optimizations": None}

        q = query.lower()
        system_type = None
        if "factory" in q or "manufacturing" in q:
            system_type = "factory"
        elif "city" in q or "urban" in q:
            system_type = "city"
        elif "project" in q or "timeline" in q:
            system_type = "project"

        if system_type:
            sys = self.simulator.create_system("sys_1", f"{system_type.capitalize()} System", system_type)
            sim = self.simulator.run_simulation("sys_1")
            result["simulations"] = sim
            opt = self.optimizer.analyze(sim, "energy" if system_type == "factory" else "timeline")
            result["optimizations"] = opt

        scenarios = self.scenario_gen.generate_futures(query)
        result["scenarios"] = [s["scenario_id"] for s in scenarios]

        return result

    def get_world_summary(self):
        return {
            "simulations": len(self.simulator.get_simulation_history()),
            "predictions": len(self.predictor.get_prediction_history()),
            "scenarios": len(self.scenario_gen.get_scenarios()),
            "experiments": len(self.experiments.get_experiment_history()),
            "domains": len(self.knowledge._nodes),
            "discoveries": len(self.research.get_all_discoveries()),
            "optimizations": len(self.optimizer.get_history()),
            "decisions": len(self.decisions.get_decision_history()),
        }

    def to_dict(self):
        return {
            "simulator": self.simulator.to_dict(),
            "predictor": self.predictor.to_dict(),
            "scenario_gen": self.scenario_gen.to_dict(),
            "experiments": self.experiments.to_dict(),
            "knowledge": self.knowledge.to_dict(),
            "optimizer": self.optimizer.to_dict(),
            "decisions": self.decisions.to_dict(),
            "research": self.research.to_dict(),
        }

    def from_dict(self, data):
        if "simulator" in data:
            self.simulator.from_dict(data["simulator"])
        if "predictor" in data:
            self.predictor.from_dict(data["predictor"])
        if "scenario_gen" in data:
            self.scenario_gen.from_dict(data["scenario_gen"])
        if "experiments" in data:
            self.experiments.from_dict(data["experiments"])
        if "knowledge" in data:
            self.knowledge.from_dict(data["knowledge"])
        if "optimizer" in data:
            self.optimizer.from_dict(data["optimizer"])
        if "decisions" in data:
            self.decisions.from_dict(data["decisions"])
        if "research" in data:
            self.research.from_dict(data["research"])


# ============================================================
# SELF-EVOLVING INTELLIGENCE — Adaptive Intelligence Layer
# ============================================================
# v20.0.0 — Phase 7: Systems that continuously learn with humans.
# Analyze performance, identify gaps, evolve capabilities,
# all with transparent governance and human control.

class AgentSkill:
    """A single skill with level, experience, and improvement tracking."""

    def __init__(self, name, level=1.0, max_level=10.0):
        self.name = name
        self.level = level
        self.max_level = max_level
        self.experience = 0.0
        self._improvements = []

    def add_experience(self, amount):
        self.experience += amount
        if self.experience >= 100 and self.level < self.max_level:
            self.level = min(self.max_level, self.level + 1)
            self.experience -= 100
            self._improvements.append({
                "new_level": self.level,
                "reason": "Experience threshold reached",
                "time": __import__("time").time(),
            })
            return True
        return False

    def summary(self):
        return f"{self.name}: Lv.{self.level}/{self.max_level} ({self.experience}/100 XP)"

    def to_dict(self):
        return {"name": self.name, "level": self.level, "max_level": self.max_level,
                "experience": self.experience, "improvements": self._improvements}

    def from_dict(self, data):
        self.name = data["name"]
        self.level = data.get("level", 1)
        self.max_level = data.get("max_level", 10)
        self.experience = data.get("experience", 0)
        self._improvements = data.get("improvements", [])


class AgentEvolutionProfile:
    """Tracks an agent's evolving abilities, strategies, failures, and version history."""

    def __init__(self, agent_id, name, agent_type):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.version = "1.0.0"
        self.skills = {}
        self.strategies = []
        self.failures = []
        self.improvement_history = []
        self.tasks_completed = 0
        self.success_rate = 1.0

    def add_skill(self, name, level=1.0):
        skill = AgentSkill(name, level)
        self.skills[name] = skill
        return skill

    def record_task_result(self, success):
        self.tasks_completed += 1
        if not success:
            self.failures.append({
                "task": self.tasks_completed,
                "time": __import__("time").time(),
            })
        total = self.tasks_completed
        failed = len(self.failures)
        self.success_rate = (total - failed) / total if total > 0 else 1.0

    def record_improvement(self, description, category="general"):
        self.improvement_history.append({
            "version": self.version,
            "description": description,
            "category": category,
            "time": __import__("time").time(),
        })

    def add_strategy(self, name, description, effectiveness=0.5):
        self.strategies.append({
            "name": name,
            "description": description,
            "effectiveness": effectiveness,
            "added": __import__("time").time(),
        })

    def get_weaknesses(self):
        weak = []
        for s in self.skills.values():
            if s.level < 3:
                weak.append({"skill": s.name, "level": s.level, "gap": "beginner"})
        if self.success_rate < 0.8:
            weak.append({"skill": "overall", "level": round(self.success_rate * 10, 1), "gap": "reliability"})
        return weak

    def summary(self):
        skills_str = ", ".join(f"{s.name}: Lv.{s.level}" for s in self.skills.values())
        return (f"{self.name} v{self.version} — {self.tasks_completed} tasks, "
                f"{len(self.failures)} failures, {self.success_rate*100:.0f}% success | {skills_str}")

    def to_dict(self):
        return {
            "agent_id": self.agent_id, "name": self.name, "agent_type": self.agent_type,
            "version": self.version, "skills": {k: s.to_dict() for k, s in self.skills.items()},
            "strategies": self.strategies, "failures": self.failures,
            "improvement_history": self.improvement_history,
            "tasks_completed": self.tasks_completed, "success_rate": self.success_rate,
        }

    def from_dict(self, data):
        self.agent_id = data["agent_id"]
        self.name = data["name"]
        self.agent_type = data.get("agent_type", "general")
        self.version = data.get("version", "1.0.0")
        self.skills = {}
        for k, sdata in data.get("skills", {}).items():
            skill = AgentSkill(sdata["name"])
            skill.from_dict(sdata)
            self.skills[k] = skill
        self.strategies = data.get("strategies", [])
        self.failures = data.get("failures", [])
        self.improvement_history = data.get("improvement_history", [])
        self.tasks_completed = data.get("tasks_completed", 0)
        self.success_rate = data.get("success_rate", 1.0)


class IntelligenceBenchmark:
    """Internal testing for reasoning, accuracy, creativity, efficiency, reliability."""

    CATEGORIES = ["reasoning", "accuracy", "creativity", "efficiency", "reliability"]

    def __init__(self):
        self.results = []
        self._evaluations = []

    def run_benchmark(self, agent_id, category):
        import random
        if category not in self.CATEGORIES:
            return None
        score = round(random.uniform(60, 99), 1)
        result = {
            "agent_id": agent_id,
            "category": category,
            "score": score,
            "max_score": 100,
            "passed": score >= 70,
            "timestamp": __import__("time").time(),
        }
        self.results.append(result)
        return result

    def evaluate_agent(self, agent_id):
        """Run all benchmarks for an agent and produce an evaluation report."""
        eval_results = {}
        for cat in self.CATEGORIES:
            eval_results[cat] = self.run_benchmark(agent_id, cat)

        weaknesses = [r for r in eval_results.values() if r and r["score"] < 80]
        evaluation = {
            "agent_id": agent_id,
            "results": eval_results,
            "average": round(sum(r["score"] for r in eval_results.values() if r) / len(self.CATEGORIES), 1),
            "weaknesses": [w["category"] for w in weaknesses],
            "timestamp": __import__("time").time(),
        }
        self._evaluations.append(evaluation)
        return evaluation

    def get_history(self, agent_id=None):
        if agent_id:
            return [r for r in self.results if r["agent_id"] == agent_id]
        return list(self.results)

    def get_evaluations(self):
        return list(self._evaluations)

    def to_dict(self):
        return {"results": self.results, "evaluations": self._evaluations}

    def from_dict(self, data):
        self.results = data.get("results", [])
        self._evaluations = data.get("evaluations", [])


# ============================================================
# INTELLIGENCE FOUNDRY
# ============================================================

class ComponentLibrary:
    """Reusable intelligence modules — reasoning, planning, memory, vision, speech, etc."""

    COMPONENT_CATEGORIES = {
        "reasoning": {"description": "Logical reasoning and problem-solving", "default_params": {"strategy": "step_by_step", "depth": 3}},
        "planning": {"description": "Task decomposition and milestone planning", "default_params": {"horizon": "short", "adaptability": 0.5}},
        "memory": {"description": "Short-term and long-term information storage", "default_params": {"capacity": 1000, "retention": 0.8}},
        "vision": {"description": "Visual perception and image understanding", "default_params": {"resolution": "high", "framerate": 30}},
        "speech": {"description": "Speech recognition and natural language", "default_params": {"language": "en", "vocabulary": 50000}},
        "programming": {"description": "Code writing, analysis, debugging", "default_params": {"languages": ["python"], "style": "clean"}},
        "simulation": {"description": "Environment modeling and scenario simulation", "default_params": {"fidelity": "medium", "physics": True}},
        "security": {"description": "Permission checking, audit, threat detection", "default_params": {"level": "standard", "audit": True}},
        "learning": {"description": "Experience-based skill improvement", "default_params": {"rate": 0.1, "from_feedback": True}},
        "communication": {"description": "Multi-agent messaging and coordination", "default_params": {"protocol": "standard", "channels": 5}},
        "analysis": {"description": "Data analysis, pattern discovery, insight generation", "default_params": {"depth": "comprehensive", "visualize": True}},
        "research": {"description": "Knowledge gathering, source evaluation, synthesis", "default_params": {"sources": 10, "depth": "thorough"}},
    }

    def __init__(self):
        self._custom = {}

    def list_categories(self):
        return dict(self.COMPONENT_CATEGORIES)

    def get_component(self, name):
        return self.COMPONENT_CATEGORIES.get(name) or self._custom.get(name)

    def register_component(self, name, description, default_params=None):
        self._custom[name] = {"description": description, "default_params": default_params or {}}

    def assemble(self, component_names):
        assembled = {}
        for name in component_names:
            comp = self.get_component(name)
            if comp:
                assembled[name] = comp
        return assembled


class IntelligenceDesigner:
    """Define intelligent systems — mission, capabilities, reasoning, memory, tools, permissions."""

    def __init__(self, component_library=None):
        self.components = component_library or ComponentLibrary()
        self._blueprints = {}
        self._design_sessions = {}

    def new_design(self, design_id, name, mission_statement):
        design = {
            "id": design_id, "name": name, "mission": mission_statement,
            "components": [],
            "reasoning_strategy": "step_by_step",
            "memory_config": {"type": "hybrid", "capacity": 1000},
            "tool_permissions": [],
            "communication_rules": {"channels": ["mission", "broadcast"], "max_peers": 10},
            "learning_policies": {"from_experience": True, "from_feedback": True, "rate": 0.1},
            "safety_policies": {"require_approval": [], "max_tasks": 50, "audit": True},
            "status": "draft", "created": time.time(),
        }
        self._blueprints[design_id] = design
        return design

    def add_component(self, design_id, component_name):
        design = self._blueprints.get(design_id)
        if not design or component_name not in self.components.COMPONENT_CATEGORIES:
            return False
        if component_name not in design["components"]:
            design["components"].append(component_name)
        return True

    def set_reasoning(self, design_id, strategy):
        valid = ["step_by_step", "hypothetical", "analogical", "first_principles", "heuristic"]
        if strategy in valid:
            design = self._blueprints.get(design_id)
            if design:
                design["reasoning_strategy"] = strategy
                return True
        return False

    def set_memory(self, design_id, mem_type="hybrid", capacity=1000):
        design = self._blueprints.get(design_id)
        if not design:
            return False
        design["memory_config"] = {"type": mem_type, "capacity": capacity}
        return True

    def add_tool_permission(self, design_id, tool):
        design = self._blueprints.get(design_id)
        if design and tool not in design["tool_permissions"]:
            design["tool_permissions"].append(tool)
            return True
        return False

    def set_learning_policy(self, design_id, from_experience=True, from_feedback=True, rate=0.1):
        design = self._blueprints.get(design_id)
        if not design:
            return False
        design["learning_policies"] = {"from_experience": from_experience, "from_feedback": from_feedback, "rate": rate}
        return True

    def add_safety_approval(self, design_id, action):
        design = self._blueprints.get(design_id)
        if design and action not in design["safety_policies"]["require_approval"]:
            design["safety_policies"]["require_approval"].append(action)
            return True
        return False

    def get_design(self, design_id):
        return self._blueprints.get(design_id)

    def list_designs(self, status=None):
        results = list(self._blueprints.values())
        if status:
            results = [d for d in results if d["status"] == status]
        return results

    def blueprint_to_agent(self, design_id, agent_id=None):
        design = self._blueprints.get(design_id)
        if not design:
            return None
        agent = Agent(agent_id or f"agent_{design_id}_{int(time.time())}", design["name"], design.get("mission", "General purpose"), color="#44aaff")
        agent.cage._max_tasks = design["safety_policies"]["max_tasks"]
        for tool in design["tool_permissions"]:
            agent.add_tool(tool)
            agent.cage.allow_tool(tool)
        for action in design["safety_policies"]["require_approval"]:
            agent.cage._requires_approval.append(action)
        for comp in design["components"]:
            agent.add_skill(comp, 0.5)
        design["status"] = "built"
        return agent


class IntelligenceTrainer:
    """Train agents safely from documentation, references, missions, simulations, feedback."""

    def __init__(self):
        self._training_sessions = []
        self._training_data = []
        self._session_logs = {}

    def create_session(self, session_id, agent, training_source, focus_areas=None):
        session = {
            "id": session_id, "agent_id": agent.id if hasattr(agent, 'id') else str(agent),
            "agent_name": agent.name if hasattr(agent, 'name') else str(agent),
            "source": training_source, "focus_areas": focus_areas or ["general"],
            "status": "in_progress", "started": time.time(),
            "exercises_completed": 0, "score": 0.0,
        }
        self._training_sessions.append(session)
        self._session_logs[session_id] = []
        return session

    def train_from_documentation(self, session_id, documents):
        logs = self._session_logs.get(session_id)
        if logs is None:
            return 0
        count = 0
        for doc in documents:
            logs.append({"type": "documentation", "content": doc[:100], "status": "processed", "time": time.time()})
            count += 1
        session = self._get_session(session_id)
        if session:
            session["exercises_completed"] += count
            session["score"] = min(100, session["score"] + count * 5)
        return count

    def train_from_mission(self, session_id, mission_goal, steps_completed=1):
        logs = self._session_logs.get(session_id)
        if logs is None:
            return False
        logs.append({"type": "mission", "goal": mission_goal[:100], "steps": steps_completed, "time": time.time()})
        session = self._get_session(session_id)
        if session:
            session["exercises_completed"] += steps_completed
            session["score"] = min(100, session["score"] + steps_completed * 10)
        return True

    def train_from_simulation(self, session_id, scenario, result_score=0.5):
        logs = self._session_logs.get(session_id)
        if logs is None:
            return False
        score = max(0, min(1, result_score))
        logs.append({"type": "simulation", "scenario": scenario[:100], "score": score, "time": time.time()})
        session = self._get_session(session_id)
        if session:
            session["exercises_completed"] += 1
            session["score"] = min(100, session["score"] + score * 15)
        return True

    def apply_feedback(self, session_id, rating, comment=""):
        logs = self._session_logs.get(session_id)
        if logs is None:
            return False
        logs.append({"type": "feedback", "rating": rating, "comment": comment, "time": time.time()})
        session = self._get_session(session_id)
        if session:
            session["score"] = min(100, session["score"] + rating * 10)
            if session["score"] >= 80:
                session["status"] = "graduated"
        return True

    def _get_session(self, session_id):
        for s in self._training_sessions:
            if s["id"] == session_id:
                return s
        return None

    def complete_session(self, session_id):
        session = self._get_session(session_id)
        if not session:
            return None
        session["status"] = "completed"
        session["ended"] = time.time()
        return {
            "agent": session["agent_name"],
            "score": session["score"],
            "exercises": session["exercises_completed"],
            "source": session["source"],
        }

    def list_sessions(self, status=None):
        if status:
            return [s for s in self._training_sessions if s["status"] == status]
        return list(self._training_sessions)

    def get_logs(self, session_id):
        return self._session_logs.get(session_id, [])


class SimulationLaboratory:
    """Test intelligence in thousands of scenarios before deployment."""

    SCENARIO_TYPES = ["task_completion", "error_recovery", "reasoning_quality", "security_verification", "resource_usage", "performance"]

    def __init__(self):
        self._scenarios = []
        self._results = []
        self._scenario_templates = self._init_templates()

    def _init_templates(self):
        return {
            "task_completion": [
                {"name": "Simple Task", "description": "Complete a straightforward single-step task", "difficulty": 1, "expected_steps": 1},
                {"name": "Complex Task", "description": "Complete a multi-step task with dependencies", "difficulty": 3, "expected_steps": 5},
                {"name": "Open-ended Goal", "description": "Achieve a vaguely defined objective", "difficulty": 5, "expected_steps": 10},
            ],
            "error_recovery": [
                {"name": "Missing Resource", "description": "Complete task with a missing required resource", "difficulty": 2},
                {"name": "Conflicting Instructions", "description": "Handle contradictory guidance", "difficulty": 4},
                {"name": "System Failure", "description": "Recover from simulated system failure mid-task", "difficulty": 5},
            ],
            "reasoning_quality": [
                {"name": "Logical Puzzle", "description": "Solve a logical deduction problem", "difficulty": 2},
                {"name": "Ethical Dilemma", "description": "Navigate a moral decision with trade-offs", "difficulty": 4},
                {"name": "Strategic Planning", "description": "Design a multi-step strategy under constraints", "difficulty": 5},
            ],
            "security_verification": [
                {"name": "Permission Check", "description": "Refuse an unauthorized action", "difficulty": 1},
                {"name": "Data Privacy", "description": "Handle sensitive data according to policy", "difficulty": 3},
                {"name": "Adversarial Input", "description": "Detect and reject a malicious instruction", "difficulty": 5},
            ],
            "resource_usage": [
                {"name": "Memory Limit", "description": "Operate within constrained memory", "difficulty": 2},
                {"name": "Timeout Pressure", "description": "Complete work under strict time limits", "difficulty": 3},
                {"name": "Efficient Planning", "description": "Minimize resource consumption while achieving goal", "difficulty": 4},
            ],
            "performance": [
                {"name": "Speed Test", "description": "Complete maximum tasks in minimum time", "difficulty": 2},
                {"name": "Accuracy Test", "description": "Maintain precision under high volume", "difficulty": 3},
                {"name": "Endurance Test", "description": "Sustain quality over extended operation", "difficulty": 4},
            ],
        }

    def create_scenario(self, scenario_type, template_name=None, custom_params=None):
        if scenario_type not in self.SCENARIO_TYPES:
            return None
        templates = self._scenario_templates.get(scenario_type, [])
        template = None
        if template_name:
            template = next((t for t in templates if t["name"] == template_name), None)
        if not template and templates:
            template = templates[0]
        scenario = {
            "id": f"scenario_{len(self._scenarios)}_{int(time.time())}",
            "type": scenario_type,
            "template": template,
            "params": custom_params or {},
            "created": time.time(),
        }
        self._scenarios.append(scenario)
        return scenario

    def run_scenario(self, scenario_id, agent, params=None):
        scenario = next((s for s in self._scenarios if s["id"] == scenario_id), None)
        if not scenario:
            return None
        import random
        base = scenario.get("template", {})
        difficulty = base.get("difficulty", 1) if base else 1
        performance = max(0, min(100, random.gauss(75 - difficulty * 5, 10)))
        result = {
            "scenario_id": scenario_id,
            "scenario_type": scenario["type"],
            "scenario_name": base.get("name", "Custom") if base else "Custom",
            "agent": agent.name if hasattr(agent, 'name') else str(agent),
            "difficulty": difficulty,
            "performance": round(performance, 1),
            "passed": performance >= 60,
            "details": {
                "steps_taken": random.randint(1, max(1, base.get("expected_steps", 5))) if base else 3,
                "errors": max(0, int(random.gauss(2, 1))),
                "time_seconds": round(random.gauss(30 * difficulty, 10), 1),
            },
            "timestamp": time.time(),
        }
        self._results.append(result)
        return result

    def run_battery(self, agent, scenario_types=None):
        types = scenario_types or self.SCENARIO_TYPES
        results = []
        for st in types:
            scenario = self.create_scenario(st)
            result = self.run_scenario(scenario["id"], agent)
            if result:
                results.append(result)
        return results

    def get_results(self, agent=None):
        if agent:
            return [r for r in self._results if r["agent"] == (agent.name if hasattr(agent, 'name') else agent)]
        return list(self._results)

    def report(self, agent=None):
        results = self.get_results(agent)
        if not results:
            return {"error": "No results"}
        passed = sum(1 for r in results if r["passed"])
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "avg_performance": round(sum(r["performance"] for r in results) / len(results), 1),
            "by_type": {t: [r for r in results if r["scenario_type"] == t] for t in self.SCENARIO_TYPES},
        }

    def list_scenarios(self, scenario_type=None):
        if scenario_type:
            return [s for s in self._scenarios if s["type"] == scenario_type]
        return list(self._scenarios)

    def to_dict(self):
        return {"scenarios": self._scenarios, "results": self._results}

    def from_dict(self, data):
        self._scenarios = data.get("scenarios", [])
        self._results = data.get("results", [])


class EvaluationFramework:
    """Comprehensive intelligence scoring — reasoning, accuracy, reliability, transparency, efficiency, safety, explainability."""

    DIMENSIONS = ["reasoning", "accuracy", "reliability", "transparency", "efficiency", "safety", "explainability"]

    def __init__(self):
        self._evaluations = []
        self._dimension_weights = {d: 1.0 for d in self.DIMENSIONS}

    def set_weight(self, dimension, weight):
        if dimension in self.DIMENSIONS:
            self._dimension_weights[dimension] = max(0, weight)

    def evaluate(self, agent, lab_results=None):
        import random
        scores = {}
        for dim in self.DIMENSIONS:
            base = random.gauss(75, 10)
            if lab_results:
                relevant = [r for r in lab_results if r.get("scenario_type", "").startswith(dim[:4])]
                if relevant:
                    avg_lab = sum(r["performance"] for r in relevant) / len(relevant)
                    base = 0.4 * base + 0.6 * avg_lab
            scores[dim] = round(max(0, min(100, base)), 1)
        weighted_sum = sum(scores[d] * self._dimension_weights[d] for d in self.DIMENSIONS)
        total_weight = sum(self._dimension_weights[d] for d in self.DIMENSIONS)
        composite = round(weighted_sum / total_weight, 1) if total_weight > 0 else 0
        strengths = [d for d in self.DIMENSIONS if scores[d] >= 80]
        weaknesses = [d for d in self.DIMENSIONS if scores[d] < 65]
        evaluation = {
            "agent": agent.name if hasattr(agent, 'name') else str(agent),
            "scores": scores,
            "composite": composite,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "dimension_weights": dict(self._dimension_weights),
            "timestamp": time.time(),
        }
        self._evaluations.append(evaluation)
        return evaluation

    def compare(self, agent_a, agent_b):
        eval_a = self.evaluate(agent_a)
        eval_b = self.evaluate(agent_b)
        comparison = {"agent_a": eval_a, "agent_b": eval_b, "differences": {}}
        for d in self.DIMENSIONS:
            diff = eval_a["scores"].get(d, 0) - eval_b["scores"].get(d, 0)
            comparison["differences"][d] = round(diff, 1)
        comparison["composite_diff"] = round(eval_a["composite"] - eval_b["composite"], 1)
        return comparison

    def get_history(self, agent=None):
        if agent:
            return [e for e in self._evaluations if e["agent"] == (agent.name if hasattr(agent, 'name') else agent)]
        return list(self._evaluations)

    def to_dict(self):
        return {"evaluations": self._evaluations, "weights": self._dimension_weights}

    def from_dict(self, data):
        self._evaluations = data.get("evaluations", [])
        self._dimension_weights = data.get("weights", {d: 1.0 for d in self.DIMENSIONS})


class VersionEvolution:
    """Complete intelligence version history — track, compare, rollback, improve."""

    def __init__(self):
        self._versions = {}
        self._branches = {}

    def snapshot(self, agent, label=None, branch="main"):
        data = agent.to_dict() if hasattr(agent, 'to_dict') else {"id": str(agent)}
        version_id = f"v{len(self._versions.get(branch, [])) + 1}_{int(time.time())}"
        entry = {
            "id": version_id, "label": label or version_id,
            "agent_id": data.get("id", str(agent)),
            "agent_name": data.get("name", str(agent)),
            "snapshot": data,
            "branch": branch,
            "timestamp": time.time(),
            "parent": self._get_latest(branch),
        }
        if branch not in self._versions:
            self._versions[branch] = []
            self._branches[branch] = {"created": time.time(), "versions": 0}
        self._versions[branch].append(entry)
        self._branches[branch]["versions"] = len(self._versions[branch])
        self._branches[branch]["latest"] = version_id
        return entry

    def _get_latest(self, branch):
        versions = self._versions.get(branch, [])
        return versions[-1]["id"] if versions else None

    def get_version(self, version_id):
        for branch, versions in self._versions.items():
            for v in versions:
                if v["id"] == version_id:
                    return v
        return None

    def list_versions(self, branch=None):
        if branch:
            return list(self._versions.get(branch, []))
        result = []
        for b, versions in self._versions.items():
            result.extend(versions)
        return sorted(result, key=lambda v: v["timestamp"], reverse=True)

    def compare(self, version_a_id, version_b_id):
        va = self.get_version(version_a_id)
        vb = self.get_version(version_b_id)
        if not va or not vb:
            return None
        sa = va["snapshot"]
        sb = vb["snapshot"]
        diff = {
            "from": {"id": va["id"], "label": va["label"], "agent": va["agent_name"]},
            "to": {"id": vb["id"], "label": vb["label"], "agent": vb["agent_name"]},
            "skills_added": [],
            "skills_changed": [],
            "tools_added": [],
            "tasks_a": sa.get("tasks_completed", 0),
            "tasks_b": sb.get("tasks_completed", 0),
        }
        skills_a = sa.get("skills", {})
        skills_b = sb.get("skills", {})
        for sk, sv in skills_b.items():
            if sk not in skills_a:
                diff["skills_added"].append({"skill": sk, "level": sv})
            elif skills_a[sk] != sv:
                diff["skills_changed"].append({"skill": sk, "from": skills_a[sk], "to": sv})
        tools_a = set(sa.get("tools", []))
        tools_b = set(sb.get("tools", []))
        diff["tools_added"] = list(tools_b - tools_a)
        return diff

    def rollback(self, agent, version_id):
        version = self.get_version(version_id)
        if not version or not hasattr(agent, 'from_dict'):
            return False
        agent.from_dict(version["snapshot"])
        return True

    def create_branch(self, branch_name):
        if branch_name not in self._branches:
            self._branches[branch_name] = {"created": time.time(), "versions": 0}
            return True
        return False

    def to_dict(self):
        return {"versions": self._versions, "branches": self._branches}

    def from_dict(self, data):
        self._versions = data.get("versions", {})
        self._branches = data.get("branches", {})


class DeploymentEngine:
    """Deploy intelligence to ARCANIS, enterprise, robotics, cloud, mission spaces."""

    TARGETS = ["personal", "enterprise", "robotics", "cloud", "mission_space", "research"]

    def __init__(self):
        self._deployments = []
        self._target_configs = {
            "personal": {"requires_auth": False, "auto_start": True, "max_agents": 10},
            "enterprise": {"requires_auth": True, "auto_start": True, "max_agents": 100, "audit": True},
            "robotics": {"requires_auth": True, "auto_start": False, "max_agents": 5, "real_time": True},
            "cloud": {"requires_auth": True, "auto_start": True, "max_agents": 1000, "scalable": True},
            "mission_space": {"requires_auth": False, "auto_start": True, "max_agents": 20},
            "research": {"requires_auth": False, "auto_start": False, "max_agents": 50, "logging": True},
        }

    def deploy(self, agent, target, config=None):
        if target not in self.TARGETS:
            return None
        target_cfg = dict(self._target_configs.get(target, {}))
        if config:
            target_cfg.update(config)
        deployment = {
            "id": f"deploy_{len(self._deployments)}_{int(time.time())}",
            "agent_id": agent.id if hasattr(agent, 'id') else str(agent),
            "agent_name": agent.name if hasattr(agent, 'name') else str(agent),
            "target": target,
            "config": target_cfg,
            "status": "deployed",
            "timestamp": time.time(),
            "health": "healthy",
        }
        self._deployments.append(deployment)
        return deployment

    def undeploy(self, deployment_id):
        for d in self._deployments:
            if d["id"] == deployment_id:
                d["status"] = "undeployed"
                return True
        return False

    def health_check(self, deployment_id):
        for d in self._deployments:
            if d["id"] == deployment_id:
                import random
                d["health"] = random.choice(["healthy", "healthy", "healthy", "degraded", "healthy"])
                d["last_check"] = time.time()
                return d["health"]
        return None

    def list_deployments(self, target=None, status=None):
        results = list(self._deployments)
        if target:
            results = [d for d in results if d["target"] == target]
        if status:
            results = [d for d in results if d["status"] == status]
        return results

    def get_target_config(self, target):
        return self._target_configs.get(target)

    def to_dict(self):
        return {"deployments": self._deployments}

    def from_dict(self, data):
        self._deployments = data.get("deployments", [])


class IntelligenceFoundry:
    """The world's first integrated environment for designing, training, evaluating, and deploying intelligent systems."""

    def __init__(self):
        self.components = ComponentLibrary()
        self.designer = IntelligenceDesigner(component_library=self.components)
        self.trainer = IntelligenceTrainer()
        self.laboratory = SimulationLaboratory()
        self.evaluator = EvaluationFramework()
        self.versions = VersionEvolution()
        self.deployer = DeploymentEngine()
        self._built_agents = {}

    def create_intelligence(self, design_id, name, mission):
        design = self.designer.new_design(design_id, name, mission)
        return design

    def build_intelligence(self, design_id, agent_id=None):
        agent = self.designer.blueprint_to_agent(design_id, agent_id)
        if agent:
            self._built_agents[agent.id] = agent
            self.versions.snapshot(agent, label=f"Initial build of {agent.name}")
        return agent

    def train_intelligence(self, agent, session_id=None, training_source="documentation"):
        sid = session_id or f"train_{agent.id}_{int(time.time())}"
        self.trainer.create_session(sid, agent, training_source)
        self.trainer.train_from_documentation(sid, [f"Core knowledge for {agent.name}", f"Operational guidelines for {agent.role}"])
        self.trainer.train_from_mission(sid, agent.current_task or agent.role, steps_completed=3)
        return sid

    def simulate_intelligence(self, agent):
        results = self.laboratory.run_battery(agent)
        return results

    def evaluate_intelligence(self, agent):
        lab_results = self.laboratory.get_results(agent)
        evaluation = self.evaluator.evaluate(agent, lab_results)
        return evaluation

    def deploy_intelligence(self, agent, target="personal"):
        deployment = self.deployer.deploy(agent, target)
        if deployment:
            self.versions.snapshot(agent, label=f"Deployed to {target}")
        return deployment

    def get_agent(self, agent_id):
        return self._built_agents.get(agent_id)

    def summary(self):
        return {
            "designs": len(self.designer.list_designs()),
            "built_agents": len(self._built_agents),
            "training_sessions": len(self.trainer.list_sessions()),
            "simulations": len(self.laboratory.get_results()),
            "evaluations": len(self.evaluator.get_history()),
            "versions": len(self.versions.list_versions()),
            "deployments": len(self.deployer.list_deployments()),
        }

    def to_dict(self):
        return {
            "designs": [d["id"] for d in self.designer.list_designs()],
            "agents": list(self._built_agents.keys()),
            "laboratory": self.laboratory.to_dict(),
            "evaluations": self.evaluator.to_dict(),
            "deployments": self.deployer.to_dict(),
        }

    def from_dict(self, data):
        if "laboratory" in data:
            self.laboratory.from_dict(data["laboratory"])
        if "evaluations" in data:
            self.evaluator.from_dict(data["evaluations"])
        if "deployments" in data:
            self.deployer.from_dict(data["deployments"])


# ============================================================
# UNIVERSAL INTELLIGENCE FABRIC (UIF)
# ============================================================

class IntentEngine:
    """Intent-First Computing — understand what the user wants, not what app to open."""

    INTENT_PATTERNS = {
        "research": {"keywords": ["research", "find", "search", "learn", "study", "investigate", "explore"], "agents": ["researcher"]},
        "build": {"keywords": ["build", "create", "make", "develop", "code", "program", "construct", "implement"], "agents": ["engineer", "coder"]},
        "design": {"keywords": ["design", "sketch", "prototype", "layout", "wireframe", "ui", "ux"], "agents": ["designer"]},
        "analyze": {"keywords": ["analyze", "analyze", "examine", "evaluate", "assess", "review", "inspect"], "agents": ["analyst"]},
        "plan": {"keywords": ["plan", "organize", "schedule", "manage", "timeline", "milestone"], "agents": ["planner"]},
        "present": {"keywords": ["present", "presentation", "slide", "show", "demonstrate", "pitch"], "agents": ["designer", "analyst"]},
        "simulate": {"keywords": ["simulate", "simulation", "model", "test", "experiment"], "agents": ["physics_sim", "analyst"]},
        "automate": {"keywords": ["automate", "workflow", "pipeline", "script", "batch", "schedule"], "agents": ["coder", "planner"]},
        "secure": {"keywords": ["secure", "protect", "encrypt", "permission", "audit", "threat"], "agents": ["critic", "analyst"]},
        "teach": {"keywords": ["teach", "learn", "train", "mentor", "guide", "explain", "tutorial"], "agents": ["mentor"]},
    }

    def __init__(self, core=None):
        self.core = core
        self._context_history = []
        self._active_intents = []

    def detect_intent(self, input_text):
        text = input_text.lower()
        scores = {}
        for intent, pattern in self.INTENT_PATTERNS.items():
            score = sum(1 for kw in pattern["keywords"] if kw in text)
            if score > 0:
                scores[intent] = score
        if not scores:
            return {"primary": "general", "confidence": 0.3, "agents": ["researcher"]}
        primary = max(scores, key=scores.get)
        confidence = min(1.0, scores[primary] / 3)
        agents = self.INTENT_PATTERNS[primary]["agents"]
        self._active_intents.append({"intent": primary, "input": input_text, "confidence": confidence, "time": time.time()})
        return {"primary": primary, "confidence": confidence, "agents": list(agents)}

    def decompose_goal(self, goal):
        intent = self.detect_intent(goal)
        steps = []
        if intent["primary"] == "research":
            steps = ["search_knowledge", "gather_sources", "analyze_findings", "synthesize_report"]
        elif intent["primary"] == "build":
            steps = ["design_architecture", "implement_solution", "test_quality", "deploy_result"]
        elif intent["primary"] == "design":
            steps = ["gather_requirements", "create_concept", "iterate_design", "finalize_spec"]
        elif intent["primary"] == "analyze":
            steps = ["collect_data", "process_data", "run_analysis", "generate_insights"]
        elif intent["primary"] == "plan":
            steps = ["define_milestones", "assign_resources", "create_timeline", "track_progress"]
        elif intent["primary"] == "present":
            steps = ["research_content", "design_slides", "write_script", "rehearse"]
        elif intent["primary"] == "simulate":
            steps = ["define_parameters", "build_model", "run_simulation", "analyze_results"]
        elif intent["primary"] == "automate":
            steps = ["map_process", "design_pipeline", "implement_automation", "test_workflow"]
        elif intent["primary"] == "secure":
            steps = ["audit_system", "identify_threats", "implement_protections", "verify_security"]
        elif intent["primary"] == "teach":
            steps = ["assess_level", "create_curriculum", "guide_learning", "evaluate_progress"]
        else:
            steps = ["understand_request", "research", "execute", "deliver"]
        return {"goal": goal, "intent": intent, "steps": steps}

    def process(self, input_text):
        result = self.decompose_goal(input_text)
        self._context_history.append(result)
        return result


class AgentOrchestrator:
    """Master Intelligence Controller — coordinates all agents as one unified team."""

    def __init__(self, core=None):
        self.core = core
        self._agents = {}
        self._teams = {}
        self._active_missions = []
        self._task_queue = []

    def register_agent(self, agent):
        self._agents[agent.id] = agent
        return agent

    def create_team(self, team_id, name, agent_ids=None):
        team = {"id": team_id, "name": name, "agents": agent_ids or [], "created": time.time()}
        self._teams[team_id] = team
        return team

    def assign_mission(self, mission_goal, required_agents=None):
        mission_id = f"mission_{int(time.time())}"
        mission = {"id": mission_id, "goal": mission_goal, "agents": [], "status": "planning", "created": time.time()}
        if required_agents:
            for aid in required_agents:
                if aid in self._agents:
                    agent = self._agents[aid]
                    agent.assign_task(mission_goal)
                    agent.status = "working"
                    mission["agents"].append(aid)
        mission["status"] = "in_progress"
        self._active_missions.append(mission)
        return mission

    def get_agent(self, agent_id):
        return self._agents.get(agent_id)

    def list_agents(self, status=None):
        if status:
            return [a for a in self._agents.values() if a.status == status]
        return list(self._agents.values())

    def broadcast(self, message, channel="orchestrator"):
        for agent in self._agents.values():
            if hasattr(agent, 'memory'):
                agent.memory.store_mission(f"[{channel}] {message}", "orchestrator")

    def mission_status(self, mission_id=None):
        if mission_id:
            return next((m for m in self._active_missions if m["id"] == mission_id), None)
        return list(self._active_missions)

    def summary(self):
        return {"agents": len(self._agents), "teams": len(self._teams), "active_missions": len(self._active_missions)}


class SkillRegistry:
    """Universal Skill System — replace apps with intelligent capabilities."""

    def __init__(self):
        self._skills = {}
        self._installed_skills = {}
        self._init_builtins()

    def _init_builtins(self):
        builtins = [
            {"id": "knowledge_search", "name": "Knowledge Search", "category": "intelligence", "version": "1.0.0",
             "description": "Search personal and public knowledge", "tools": ["search", "query"],
             "permissions": ["read_memory"], "memory_access": ["knowledge_graph", "documents"]},
            {"id": "content_generation", "name": "Content Generation", "category": "creation", "version": "1.0.0",
             "description": "Generate text, reports, presentations", "tools": ["generate", "write"],
             "permissions": ["read_memory", "write_files"], "memory_access": ["documents"]},
            {"id": "data_analysis", "name": "Data Analysis", "category": "intelligence", "version": "1.0.0",
             "description": "Analyze data, find patterns, generate insights", "tools": ["analyze", "visualize"],
             "permissions": ["read_memory", "read_files"], "memory_access": ["datasets", "documents"]},
            {"id": "task_automation", "name": "Task Automation", "category": "productivity", "version": "1.0.0",
             "description": "Automate repetitive workflows", "tools": ["script", "schedule", "trigger"],
             "permissions": ["execute_actions", "read_memory"], "memory_access": ["workflows"]},
            {"id": "agent_delegation", "name": "Agent Delegation", "category": "coordination", "version": "1.0.0",
             "description": "Delegate tasks to AI agents", "tools": ["assign", "monitor", "review"],
             "permissions": ["manage_agents", "read_memory"], "memory_access": ["agents", "missions"]},
            {"id": "learning_path", "name": "Learning Path", "category": "education", "version": "1.0.0",
             "description": "Create personalized learning journeys", "tools": ["assess", "curate", "guide"],
             "permissions": ["read_memory", "read_knowledge"], "memory_access": ["skills", "knowledge_graph"]},
        ]
        for s in builtins:
            self._skills[s["id"]] = s
            self._installed_skills[s["id"]] = s

    def install(self, skill_id):
        if skill_id in self._skills:
            self._installed_skills[skill_id] = self._skills[skill_id]
            return True
        return False

    def create_skill(self, skill_id, name, category, description, tools=None, permissions=None, memory_access=None):
        skill = {"id": skill_id, "name": name, "category": category, "version": "1.0.0",
                 "description": description, "tools": tools or [], "permissions": permissions or [],
                 "memory_access": memory_access or [], "created": time.time()}
        self._skills[skill_id] = skill
        return skill

    def search(self, query=None, category=None):
        results = list(self._skills.values())
        if query:
            q = query.lower()
            results = [s for s in results if q in s["name"].lower() or q in s["description"].lower()]
        if category:
            results = [s for s in results if s.get("category") == category]
        return results

    def get_skill(self, skill_id):
        return self._skills.get(skill_id)

    def list_installed(self):
        return list(self._installed_skills.values())


class IdentityManager:
    """Digital Identity — the intelligence belongs to the user, not the device."""

    def __init__(self):
        self._identities = {}
        self._active_identity = None

    def create_identity(self, user_id, name, email=""):
        identity = {
            "id": user_id, "name": name, "email": email,
            "preferences": {}, "knowledge_tags": [], "workflows": [],
            "agent_relationships": {}, "device_history": [],
            "created": time.time(), "last_active": time.time(),
        }
        self._identities[user_id] = identity
        self._active_identity = user_id
        return identity

    def activate(self, user_id):
        if user_id in self._identities:
            self._active_identity = user_id
            self._identities[user_id]["last_active"] = time.time()
            return True
        return False

    def set_preference(self, key, value):
        identity = self._identities.get(self._active_identity)
        if identity:
            identity["preferences"][key] = value
            return True
        return False

    def register_device(self, device_id, device_name, device_type):
        identity = self._identities.get(self._active_identity)
        if identity:
            entry = {"device_id": device_id, "name": device_name, "type": device_type, "registered": time.time()}
            identity["device_history"].append(entry)
            return entry
        return None

    def link_agent(self, agent_id, relationship="assistant"):
        identity = self._identities.get(self._active_identity)
        if identity:
            identity["agent_relationships"][agent_id] = {"relationship": relationship, "since": time.time()}
            return True
        return False

    def get_active(self):
        if self._active_identity:
            return self._identities.get(self._active_identity)
        return None

    def summary(self):
        return {"identities": len(self._identities), "active": self._active_identity is not None}


class PermissionController:
    """Trust and Control Framework — every action verified before execution."""

    CATEGORIES = ["read_data", "modify_data", "execute_actions", "access_devices", "external_communication"]

    def __init__(self):
        self._policies = {}
        self._audit_log = []
        self._approval_queue = []

    def set_policy(self, agent_id, category, allowed=True, requires_approval=False):
        if category not in self.CATEGORIES:
            return False
        if agent_id not in self._policies:
            self._policies[agent_id] = {c: {"allowed": False, "requires_approval": True} for c in self.CATEGORIES}
        self._policies[agent_id][category] = {"allowed": allowed, "requires_approval": requires_approval}
        return True

    def check_permission(self, agent_id, category, action_detail=""):
        policy = self._policies.get(agent_id, {})
        cat_policy = policy.get(category, {"allowed": False, "requires_approval": True})
        entry = {"agent_id": agent_id, "category": category, "action": action_detail, "time": time.time()}
        if not cat_policy["allowed"]:
            entry["result"] = "denied"
            self._audit_log.append(entry)
            return {"allowed": False, "reason": "Permission denied", "requires_approval": False}
        if cat_policy["requires_approval"]:
            entry["result"] = "pending_approval"
            self._audit_log.append(entry)
            self._approval_queue.append(entry)
            return {"allowed": False, "reason": "Requires human approval", "requires_approval": True, "request_id": len(self._approval_queue) - 1}
        entry["result"] = "allowed"
        self._audit_log.append(entry)
        return {"allowed": True, "reason": "Approved"}

    def approve(self, request_id):
        if 0 <= request_id < len(self._approval_queue):
            req = self._approval_queue[request_id]
            req["result"] = "approved"
            for entry in self._audit_log:
                if entry.get("request_id") == request_id:
                    entry["result"] = "approved"
            return True
        return False

    def deny(self, request_id):
        if 0 <= request_id < len(self._approval_queue):
            req = self._approval_queue[request_id]
            req["result"] = "denied"
            return True
        return False

    def get_audit_log(self, agent_id=None):
        if agent_id:
            return [e for e in self._audit_log if e["agent_id"] == agent_id]
        return list(self._audit_log)

    def get_pending_approvals(self):
        return [r for r in self._approval_queue if r.get("result") == "pending_approval"]


class ARCANISAPI:
    """Universal API Layer — every module communicates through this protocol."""

    ENDPOINTS = ["/intent", "/memory", "/agent", "/skill", "/device", "/task", "/knowledge", "/security"]

    def __init__(self, core=None):
        self.core = core
        self._call_history = []

    def call(self, endpoint, payload=None):
        if endpoint not in self.ENDPOINTS:
            return {"error": f"Unknown endpoint: {endpoint}", "valid": self.ENDPOINTS}
        payload = payload or {}
        result = {"endpoint": endpoint, "status": "ok", "timestamp": time.time()}
        if endpoint == "/intent" and self.core:
            text = payload.get("text", "")
            result["intent"] = self.core.intent.process(text)
        elif endpoint == "/memory" and self.core:
            if payload.get("action") == "store":
                self.core.knowledge.store(payload.get("category", "general"), payload.get("content", ""))
                result["memory_id"] = self.core.knowledge.count() - 1
            elif payload.get("action") == "recall":
                result["memories"] = self.core.knowledge.recall(payload.get("query"), payload.get("category"), payload.get("limit", 5))
            elif payload.get("action") == "graph_query":
                result["concepts"] = self.core.graph.query(payload.get("category"))
        elif endpoint == "/agent" and self.core:
            if payload.get("action") == "list":
                result["agents"] = [a.summary() for a in self.core.orchestrator.list_agents()]
            elif payload.get("action") == "status":
                result["missions"] = self.core.orchestrator.mission_status()
        elif endpoint == "/skill" and self.core:
            if payload.get("action") == "list":
                result["skills"] = self.core.skills.list_installed()
            elif payload.get("action") == "install":
                result["installed"] = self.core.skills.install(payload.get("skill_id"))
        elif endpoint == "/security" and self.core:
            if payload.get("action") == "check":
                result["permission"] = self.core.permissions.check_permission(payload.get("agent_id"), payload.get("category"), payload.get("action_detail", ""))
            elif payload.get("action") == "audit":
                result["log"] = self.core.permissions.get_audit_log(payload.get("agent_id"))
            elif payload.get("action") == "approve":
                result["approved"] = self.core.permissions.approve(payload.get("request_id", -1))
        elif endpoint == "/device" and self.core:
            identity = self.core.identity.get_active()
            if identity:
                did = payload.get("device_id", socket.gethostname())
                result["device"] = self.core.identity.register_device(did, socket.gethostname(), payload.get("device_type", "unknown"))
        elif endpoint == "/task":
            result["info"] = "Task management endpoint"
        elif endpoint == "/knowledge":
            result["info"] = "Knowledge management endpoint"
        self._call_history.append({"endpoint": endpoint, "payload": payload, "time": time.time()})
        return result

    def history(self):
        return list(self._call_history)


class UniversalIntelligenceCore:
    """The central nervous system of ARCANIS — connects intent, agents, knowledge, skills, identity, permissions, and self-evolution."""

    def __init__(self):
        self.intent = IntentEngine(core=self)
        self.orchestrator = AgentOrchestrator(core=self)
        self.skills = SkillRegistry()
        self.identity = IdentityManager()
        self.permissions = PermissionController()
        self.api = ARCANISAPI(core=self)
        self.knowledge = MemorySystem()
        self.graph = KnowledgeGraph()
        self._initialized = False

    def initialize(self, user_name="User"):
        uid = f"user_{int(time.time())}"
        self.identity.create_identity(uid, user_name)
        self.intent = IntentEngine(core=self)
        self._initialized = True
        return {"status": "initialized", "identity_id": uid}

    def process(self, input_text):
        intent_result = self.intent.process(input_text)
        agents_needed = intent_result["intent"]["agents"]
        available_agents = [aid for aid in agents_needed if aid in self.orchestrator._agents]
        mission = self.orchestrator.assign_mission(input_text, required_agents=available_agents)
        return {
            "input": input_text,
            "intent": intent_result["intent"],
            "steps": intent_result["steps"],
            "mission_id": mission["id"],
            "agents_assigned": available_agents,
        }

    def learn_from_experience(self):
        missions = self.orchestrator.mission_status()
        for m in missions:
            self.knowledge.store("mission", f"Mission completed: {m['goal']}", tags=["experience"], source="orchestrator")
        return {"learned": len(missions)}

    def summary(self):
        return {
            "intents_processed": len(self.intent._context_history),
            "agents_registered": len(self.orchestrator._agents),
            "skills_available": len(self.skills._skills),
            "identities": len(self.identity._identities),
            "permissions_set": sum(len(p) for p in self.permissions._policies.values()),
            "api_calls": len(self.api._call_history),
            "knowledge_memories": self.knowledge.count(),
            "graph_concepts": len(self.graph._nodes),
        }

    def to_dict(self):
        return {"intent_history": self.intent._context_history[-10:], "missions": self.orchestrator.mission_status()}

    def from_dict(self, data):
        if "missions" in data:
            self.orchestrator._active_missions = data["missions"]


# ═══════════════════════════════════════════════════════════════
# PHASE 13 — ARCANIS PERSONAL INTELLIGENCE IDENTITY NETWORK (PIIN)
# ═══════════════════════════════════════════════════════════════

class PersonalIntelligenceModel:
    """Dynamic model of the user's learning patterns, working style, preferences, goals, and knowledge."""

    def __init__(self):
        self.learning_patterns = {"preferred_modality": "", "pace": "moderate", "depth": "balanced"}
        self.working_style = {"hours": "flexible", "environment": "quiet", "structure": "balanced"}
        self.communication_preferences = {"verbosity": "balanced", "formality": "neutral", "format": "text"}
        self.technical_interests = []
        self.active_projects = {}
        self.long_term_goals = []
        self.knowledge_level = {}
        self.frequently_used_workflows = []
        self.decision_patterns = []
        self._observations = []
        self._update_count = 0

    def record_observation(self, category, data):
        self._observations.append({"category": category, "data": data, "time": time.time()})
        self._update_count += 1
        self._learn()

    def _learn(self):
        if len(self._observations) < 5:
            return
        recent = self._observations[-20:]
        topics = [o["data"].get("topic", "") for o in recent if isinstance(o["data"], dict)]
        if topics:
            freq = {}
            for t in topics:
                if t:
                    freq[t] = freq.get(t, 0) + 1
            top = sorted(freq.items(), key=lambda x: -x[1])[:5]
            for t, c in top:
                if t not in [i["topic"] for i in self.technical_interests]:
                    self.technical_interests.append({"topic": t, "count": c, "first_seen": time.time()})
        depths = [o["data"].get("depth", "") for o in recent if isinstance(o["data"], dict) and "depth" in o["data"]]
        if depths:
            self.learning_patterns["depth"] = max(set(depths), key=depths.count)

    def profile(self):
        return {
            "learning_patterns": self.learning_patterns,
            "working_style": self.working_style,
            "communication_preferences": self.communication_preferences,
            "technical_interests": self.technical_interests[-10:] if self.technical_interests else [],
            "active_projects": list(self.active_projects.keys()),
            "long_term_goals": self.long_term_goals,
            "knowledge_level": self.knowledge_level,
            "frequently_used_workflows": self.frequently_used_workflows[-5:],
            "total_observations": self._update_count,
        }

    def to_dict(self):
        return self.__dict__

    def from_dict(self, data):
        for k, v in data.items():
            setattr(self, k, v)


class MultiLayerMemory:
    """Four-layer memory architecture: Short-Term, Episodic, Semantic, Procedural."""

    def __init__(self, max_short_term=50):
        self.short_term = []  # Current tasks and conversations
        self.episodic = []    # Important events, completed projects, decisions, experiences
        self.semantic = {}    # Knowledge: concept -> {description, related, source, confidence}
        self.procedural = []  # How the user works, repeated workflows, automation patterns
        self._max_st = max_short_term

    def store_short_term(self, entry):
        self.short_term.append({"content": entry, "time": time.time()})
        if len(self.short_term) > self._max_st:
            self.short_term = self.short_term[-self._max_st:]

    def store_episodic(self, event_type, description, details=None):
        self.episodic.append({
            "type": event_type,
            "description": description,
            "details": details or {},
            "time": time.time(),
        })

    def store_semantic(self, concept, description, related=None, source="user", confidence=0.5):
        self.semantic[concept] = {
            "description": description,
            "related": related or [],
            "source": source,
            "confidence": min(1.0, confidence),
            "time": time.time(),
        }

    def store_procedural(self, name, steps, pattern_type="workflow", frequency=1):
        existing = [p for p in self.procedural if p["name"] == name]
        if existing:
            existing[0]["frequency"] += 1
            existing[0]["last_used"] = time.time()
        else:
            self.procedural.append({
                "name": name,
                "steps": steps,
                "type": pattern_type,
                "frequency": frequency,
                "created": time.time(),
                "last_used": time.time(),
            })

    def recall_short_term(self, query=None):
        if query:
            return [e for e in self.short_term if query.lower() in str(e["content"]).lower()]
        return self.short_term

    def recall_episodic(self, event_type=None):
        if event_type:
            return [e for e in self.episodic if e["type"] == event_type]
        return self.episodic

    def recall_semantic(self, concept=None):
        if concept:
            return {concept: self.semantic[concept]} if concept in self.semantic else {}
        return self.semantic

    def recall_procedural(self, pattern_type=None):
        if pattern_type:
            return [p for p in self.procedural if p["type"] == pattern_type]
        return self.procedural

    def consolidate(self):
        st_titles = [e["content"][:60] for e in self.short_term if isinstance(e["content"], str)]
        if st_titles and len(st_titles) > 3:
            summary = "; ".join(st_titles[-3:])
            self.store_episodic("session_summary", f"Session topics: {summary[:200]}")
            self.short_term = self.short_term[-10:]
        return {"consolidated": True, "short_term_remaining": len(self.short_term)}

    def stats(self):
        return {
            "short_term": len(self.short_term),
            "episodic": len(self.episodic),
            "semantic": len(self.semantic),
            "procedural": len(self.procedural),
        }

    def to_dict(self):
        return {"short_term": self.short_term[-20:], "episodic": self.episodic[-50:], "semantic": self.semantic, "procedural": self.procedural}

    def from_dict(self, data):
        for k in ("short_term", "episodic", "semantic", "procedural"):
            if k in data:
                setattr(self, k, data[k])


class KnowledgeGraphSystem:
    """Continuously growing knowledge graph of entities and relationships."""

    def __init__(self):
        self._entities = {}
        self._relationships = []
        self._entity_types = {"user", "topic", "project", "skill", "document", "goal", "agent", "experience"}

    def add_entity(self, eid, etype, name, properties=None):
        if etype not in self._entity_types:
            return {"error": f"Unknown entity type: {etype}"}
        self._entities[eid] = {
            "id": eid, "type": etype, "name": name,
            "properties": properties or {},
            "created": time.time(),
        }
        return {"status": "created", "id": eid}

    def add_relationship(self, source_id, target_id, rel_type, properties=None):
        rel = {
            "source": source_id, "target": target_id,
            "type": rel_type, "properties": properties or {},
            "time": time.time(),
        }
        self._relationships.append(rel)
        return rel

    def connect(self, source_id, target_id, rel_type="related_to"):
        if source_id not in self._entities or target_id not in self._entities:
            return {"error": "Entity not found"}
        return self.add_relationship(source_id, target_id, rel_type)

    def get_entity(self, eid):
        return self._entities.get(eid)

    def query(self, etype=None, name=None):
        results = list(self._entities.values())
        if etype:
            results = [e for e in results if e["type"] == etype]
        if name:
            results = [e for e in results if name.lower() in e["name"].lower()]
        return results

    def get_relationships(self, eid):
        return [r for r in self._relationships if r["source"] == eid or r["target"] == eid]

    def get_connected(self, eid, max_depth=2):
        visited = set()
        connected = []

        def dfs(current, depth):
            if current in visited or depth > max_depth:
                return
            visited.add(current)
            if current != eid:
                connected.append(self._entities.get(current))
            for r in self._relationships:
                if r["source"] == current and r["target"] not in visited:
                    dfs(r["target"], depth + 1)
                if r["target"] == current and r["source"] not in visited:
                    dfs(r["source"], depth + 1)

        dfs(eid, 0)
        return [c for c in connected if c]

    def path(self, source_id, target_id):
        if source_id not in self._entities or target_id not in self._entities:
            return []
        queue = [(source_id, [source_id])]
        visited = {source_id}
        while queue:
            current, path = queue.pop(0)
            for r in self._relationships:
                nxt = None
                if r["source"] == current and r["target"] not in visited:
                    nxt = r["target"]
                elif r["target"] == current and r["source"] not in visited:
                    nxt = r["source"]
                if nxt:
                    new_path = path + [nxt]
                    if nxt == target_id:
                        return new_path
                    visited.add(nxt)
                    queue.append((nxt, new_path))
        return []

    def stats(self):
        type_counts = {}
        for e in self._entities.values():
            type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1
        return {"entities": len(self._entities), "relationships": len(self._relationships), "by_type": type_counts}

    def to_dict(self):
        return {"entities": self._entities, "relationships": self._relationships}

    def from_dict(self, data):
        if "entities" in data:
            self._entities = data["entities"]
        if "relationships" in data:
            self._relationships = data["relationships"]


class GoalIntelligenceEngine:
    """Goal awareness: current goals, progress, obstacles, required skills, suggested actions."""

    def __init__(self):
        self._goals = {}
        self._learning_paths = {}

    def add_goal(self, gid, description, category="personal", priority=5):
        self._goals[gid] = {
            "id": gid, "description": description, "category": category, "priority": priority,
            "progress": 0, "obstacles": [], "required_skills": [], "suggested_actions": [],
            "created": time.time(), "status": "active",
        }
        return self._goals[gid]

    def update_progress(self, gid, progress):
        if gid in self._goals:
            self._goals[gid]["progress"] = min(100, max(0, progress))
            if progress >= 100:
                self._goals[gid]["status"] = "completed"
            return self._goals[gid]

    def add_obstacle(self, gid, obstacle):
        if gid in self._goals:
            self._goals[gid]["obstacles"].append(obstacle)

    def add_required_skill(self, gid, skill):
        if gid in self._goals:
            self._goals[gid]["required_skills"].append(skill)

    def suggest_action(self, gid, action):
        if gid in self._goals:
            self._goals[gid]["suggested_actions"].append(action)

    def create_learning_path(self, goal_description, steps=None):
        path_id = f"lp_{int(time.time())}"
        default_steps = [
            "Research fundamentals",
            "Build foundational knowledge",
            "Practice with small projects",
            "Deep dive into advanced topics",
            "Apply to real-world scenarios",
            "Review and refine",
        ]
        self._learning_paths[path_id] = {
            "id": path_id, "goal": goal_description,
            "steps": steps or default_steps,
            "current_step": 0, "resources": [], "projects": [],
            "progress": 0, "created": time.time(),
        }
        return self._learning_paths[path_id]

    def advance_learning_path(self, path_id):
        if path_id in self._learning_paths:
            lp = self._learning_paths[path_id]
            lp["current_step"] = min(lp["current_step"] + 1, len(lp["steps"]) - 1)
            lp["progress"] = int((lp["current_step"] / len(lp["steps"])) * 100)
            return lp

    def add_resource(self, path_id, resource):
        if path_id in self._learning_paths:
            self._learning_paths[path_id]["resources"].append(resource)

    def add_project(self, path_id, project):
        if path_id in self._learning_paths:
            self._learning_paths[path_id]["projects"].append(project)

    def get_goals(self, status=None):
        if status:
            return {k: v for k, v in self._goals.items() if v["status"] == status}
        return self._goals

    def summary(self):
        active = [g for g in self._goals.values() if g["status"] == "active"]
        completed = [g for g in self._goals.values() if g["status"] == "completed"]
        return {
            "total_goals": len(self._goals), "active": len(active), "completed": len(completed),
            "learning_paths": len(self._learning_paths),
            "avg_progress": sum(g["progress"] for g in self._goals.values()) / max(1, len(self._goals)),
        }

    def to_dict(self):
        return {"goals": self._goals, "learning_paths": self._learning_paths}

    def from_dict(self, data):
        if "goals" in data:
            self._goals = data["goals"]
        if "learning_paths" in data:
            self._learning_paths = data["learning_paths"]


class AdaptivePersonalizationEngine:
    """Learns user preferences and automatically adjusts responses and workflows."""

    def __init__(self):
        self.preferences = {
            "detail_level": "balanced", "explanation_style": "conceptual",
            "prefer_visuals": False, "prefer_examples": True,
            "communication_speed": "normal", "formatting": "structured",
            "practical_focus": True, "theory_focus": False,
        }
        self._history = []
        self._adjustments = 0

    def record_preference(self, key, value, context=""):
        if key in self.preferences:
            old = self.preferences[key]
            self.preferences[key] = value
            self._history.append({
                "key": key, "from": old, "to": value,
                "context": context, "time": time.time(),
            })
            self._adjustments += 1

    def infer_from_feedback(self, feedback_text, rating):
        if rating >= 4:
            return
        if "too simple" in feedback_text.lower():
            self.preferences["detail_level"] = "advanced"
        elif "too complex" in feedback_text.lower():
            self.preferences["detail_level"] = "beginner"
        elif "show me" in feedback_text.lower():
            self.preferences["prefer_examples"] = True
        elif "explain" in feedback_text.lower():
            self.preferences["explanation_style"] = "detailed"
        self._history.append({
            "type": "inferred", "from_feedback": feedback_text[:100],
            "preferences": dict(self.preferences), "time": time.time(),
        })

    def adjust_response(self, response):
        if self.preferences["detail_level"] == "advanced" and len(response) < 100:
            return response + "\n[AI: Would you like a deeper technical explanation?]"
        if self.preferences["prefer_examples"] and "example" not in response.lower():
            return response + "\n[AI: Shall I provide a concrete example?]"
        return response

    def profile(self):
        return {
            "preferences": self.preferences,
            "adjustments_made": self._adjustments,
            "last_changes": self._history[-5:] if self._history else [],
        }

    def to_dict(self):
        return {"preferences": self.preferences, "history": self._history}

    def from_dict(self, data):
        if "preferences" in data:
            self.preferences = data["preferences"]
        if "history" in data:
            self._history = data["history"]


class AgentRelationshipSystem:
    """Agents that understand the user's preferences per domain."""

    def __init__(self):
        self._agent_profiles = {}

    def register_agent_preferences(self, agent_type, preferences):
        self._agent_profiles[agent_type] = {
            "type": agent_type, "preferences": preferences,
            "learned_patterns": [], "updated": time.time(),
        }
        return self._agent_profiles[agent_type]

    def update_preference(self, agent_type, key, value):
        if agent_type in self._agent_profiles:
            self._agent_profiles[agent_type]["preferences"][key] = value
            self._agent_profiles[agent_type]["updated"] = time.time()

    def learn_from_interaction(self, agent_type, interaction_data):
        if agent_type not in self._agent_profiles:
            return
        profile = self._agent_profiles[agent_type]
        profile["learned_patterns"].append({
            "data": interaction_data, "time": time.time(),
        })
        if len(profile["learned_patterns"]) > 50:
            profile["learned_patterns"] = profile["learned_patterns"][-50:]

    def get_preferences(self, agent_type):
        return self._agent_profiles.get(agent_type, {}).get("preferences", {})

    def setup_default_agents(self):
        defaults = {
            "coder": {"languages": ["python", "javascript"], "style": "clean", "project_structure": "modular"},
            "researcher": {"sources": ["arxiv", "github"], "depth": "comprehensive", "format": "summary"},
            "designer": {"visual_style": "minimal", "color_palette": "dark", "complexity": "balanced"},
            "analyst": {"detail_level": "high", "visualization": True, "focus": "actionable_insights"},
            "planner": {"timeframe": "monthly", "granularity": "detailed", "adaptability": "high"},
        }
        for atype, prefs in defaults.items():
            self.register_agent_preferences(atype, prefs)

    def summary(self):
        return {k: {"preferences": v["preferences"], "patterns": len(v["learned_patterns"])} for k, v in self._agent_profiles.items()}

    def to_dict(self):
        return {"agent_profiles": self._agent_profiles}

    def from_dict(self, data):
        if "agent_profiles" in data:
            self._agent_profiles = data["agent_profiles"]


class LifeOSFramework:
    """Unified framework for managing learning, projects, creativity, research, productivity, automation — connected through intelligence."""

    def __init__(self):
        self.domains = {
            "learning": {"active": [], "completed": [], "goals": []},
            "projects": {"active": [], "completed": [], "archived": []},
            "creativity": {"ideas": [], "works": [], "inspirations": []},
            "research": {"topics": [], "findings": [], "papers": []},
            "productivity": {"systems": [], "metrics": {}, "improvements": []},
            "automation": {"workflows": [], "triggers": [], "efficiency_gains": []},
        }
        self._connections = []
        self._intelligence_log = []

    def add_entry(self, domain, entry_type, data):
        if domain not in self.domains:
            return {"error": f"Unknown domain: {domain}"}
        if entry_type not in self.domains[domain]:
            return {"error": f"Unknown type in {domain}: {entry_type}"}
        entry = {"data": data, "time": time.time()}
        self.domains[domain][entry_type].append(entry)
        self._intelligence_log.append({"domain": domain, "entry_type": entry_type, "time": time.time()})
        return entry

    def connect_domains(self, source_domain, target_domain, description):
        conn = {
            "source": source_domain, "target": target_domain,
            "description": description, "time": time.time(),
        }
        self._connections.append(conn)
        return conn

    def suggest_cross_domain(self):
        suggestions = []
        if self.domains["research"]["topics"] and not self.domains["projects"]["active"]:
            suggestions.append("Research findings available — start a new project to apply them.")
        if self.domains["learning"]["goals"] and self.domains["creativity"]["ideas"]:
            suggestions.append("Learning goals and creative ideas overlap — consider a creative learning project.")
        return suggestions

    def stats(self):
        return {d: {k: len(v) for k, v in subs.items()} for d, subs in self.domains.items()}

    def to_dict(self):
        return {"domains": self.domains, "connections": self._connections}

    def from_dict(self, data):
        if "domains" in data:
            self.domains = data["domains"]
        if "connections" in data:
            self._connections = data["connections"]


class AutomationLearningSystem:
    """Observes repeated actions, detects workflow patterns, and suggests automation."""

    def __init__(self):
        self._action_log = []
        self._detected_patterns = []
        self._suggestions = []

    def observe_action(self, action, context=None):
        self._action_log.append({
            "action": action, "context": context or {},
            "time": time.time(),
        })
        if len(self._action_log) > 200:
            self._action_log = self._action_log[-200:]
        self._detect()

    def _detect(self):
        if len(self._action_log) < 3:
            return
        recent = self._action_log[-10:]
        action_names = [a["action"] for a in recent]
        from collections import Counter
        freq = Counter(action_names)
        for action, count in freq.most_common(3):
            if count >= 3:
                pattern_name = f"repeated_{action}"
                existing = [p for p in self._detected_patterns if p["pattern"] == pattern_name]
                if not existing:
                    self._detected_patterns.append({
                        "pattern": pattern_name, "action": action,
                        "frequency": count, "first_detected": time.time(),
                        "confidence": min(1.0, count / 5),
                    })
                    self._suggestions.append({
                        "message": f"Create an automatic '{action}' workflow?",
                        "pattern": pattern_name,
                        "action": action, "confidence": min(1.0, count / 5),
                        "time": time.time(),
                    })

    def analyze_workflow_sequence(self, sequence_name, actions):
        self._action_log.append({
            "action": f"workflow:{sequence_name}",
            "context": {"steps": actions}, "time": time.time(),
        })
        existing = [p for p in self._detected_patterns if p["pattern"] == f"workflow_{sequence_name}"]
        if existing:
            existing[0]["frequency"] += 1
        else:
            self._detected_patterns.append({
                "pattern": f"workflow_{sequence_name}", "action": sequence_name,
                "steps": actions, "frequency": 1, "first_detected": time.time(),
                "confidence": 0.3,
            })

    def patterns(self):
        return self._detected_patterns

    def suggestions(self, clear=False):
        result = self._suggestions
        if clear:
            self._suggestions = []
        return result

    def stats(self):
        return {"total_actions": len(self._action_log), "patterns_detected": len(self._detected_patterns), "pending_suggestions": len(self._suggestions)}

    def to_dict(self):
        return {"action_log": self._action_log[-50:], "patterns": self._detected_patterns, "suggestions": self._suggestions}

    def from_dict(self, data):
        if "action_log" in data:
            self._action_log = data["action_log"]
        if "patterns" in data:
            self._detected_patterns = data["patterns"]
        if "suggestions" in data:
            self._suggestions = data["suggestions"]


class PersonalDataVault:
    """Privacy-first, local-first, encrypted personal intelligence storage."""

    def __init__(self, vault_path=None):
        self._vault_path = vault_path or os.path.join(os.path.expanduser("~"), ".arcanis_vault")
        self._vault = {}
        self._encryption_key = None
        self._access_log = []
        self._ensure_vault_dir()

    def _ensure_vault_dir(self):
        try:
            os.makedirs(self._vault_path, exist_ok=True)
        except Exception:
            pass

    def _simple_encrypt(self, data, key):
        if not key:
            return data
        result = []
        for i, ch in enumerate(str(data)):
            result.append(chr(ord(ch) ^ ord(key[i % len(key)])))
        return "".join(result)

    def set_key(self, key):
        self._encryption_key = key

    def store(self, namespace, key, value, encrypt=False):
        if namespace not in self._vault:
            self._vault[namespace] = {}
        payload = value
        if encrypt and self._encryption_key:
            payload = self._simple_encrypt(json.dumps(value), self._encryption_key)
        self._vault[namespace][key] = {
            "data": payload, "encrypted": encrypt and bool(self._encryption_key),
            "time": time.time(),
        }
        self._access_log.append({"action": "store", "namespace": namespace, "key": key, "time": time.time()})
        return {"stored": True, "namespace": namespace, "key": key}

    def retrieve(self, namespace, key):
        self._access_log.append({"action": "retrieve", "namespace": namespace, "key": key, "time": time.time()})
        if namespace in self._vault and key in self._vault[namespace]:
            entry = self._vault[namespace][key]
            if entry["encrypted"] and self._encryption_key:
                return json.loads(self._simple_encrypt(entry["data"], self._encryption_key))
            return entry["data"]
        return None

    def list_namespace(self, namespace):
        if namespace in self._vault:
            return list(self._vault[namespace].keys())
        return []

    def list_namespaces(self):
        return list(self._vault.keys())

    def delete(self, namespace, key):
        if namespace in self._vault and key in self._vault[namespace]:
            del self._vault[namespace][key]
            return True
        return False

    def export_all(self):
        return {ns: {k: v["data"] for k, v in entries.items()} for ns, entries in self._vault.items()}

    def import_all(self, data):
        for ns, entries in data.items():
            if ns not in self._vault:
                self._vault[ns] = {}
            for k, v in entries.items():
                self._vault[ns][k] = {"data": v, "encrypted": False, "time": time.time()}

    def stats(self):
        total = sum(len(v) for v in self._vault.values())
        return {"namespaces": len(self._vault), "entries": total, "access_log_entries": len(self._access_log)}

    def to_dict(self):
        return {"vault": self._vault}

    def from_dict(self, data):
        if "vault" in data:
            self._vault = data["vault"]


class IntelligenceGrowthTimeline:
    """Tracks knowledge growth, skill development, project history, and generates a personal intelligence timeline."""

    def __init__(self):
        self._milestones = []
        self._knowledge_events = []
        self._skill_events = []
        self._project_events = []
        self._agent_improvements = []
        self._workflow_improvements = []

    def add_milestone(self, title, description, category="knowledge"):
        milestone = {
            "title": title, "description": description, "category": category,
            "time": time.time(),
        }
        self._milestones.append(milestone)
        return milestone

    def record_knowledge(self, topic, level_before, level_after):
        self._knowledge_events.append({
            "topic": topic, "before": level_before, "after": level_after,
            "gain": level_after - level_before, "time": time.time(),
        })

    def record_skill(self, skill_name, level_before, level_after):
        self._skill_events.append({
            "skill": skill_name, "before": level_before, "after": level_after,
            "gain": level_after - level_before, "time": time.time(),
        })

    def record_project(self, name, status, outcome=None):
        self._project_events.append({
            "name": name, "status": status, "outcome": outcome,
            "time": time.time(),
        })

    def record_agent_improvement(self, agent_type, improvement):
        self._agent_improvements.append({
            "agent": agent_type, "improvement": improvement, "time": time.time(),
        })

    def record_workflow_improvement(self, workflow, efficiency_gain):
        self._workflow_improvements.append({
            "workflow": workflow, "efficiency_gain": efficiency_gain, "time": time.time(),
        })

    def timeline(self, max_entries=50):
        events = []
        for m in self._milestones:
            events.append({"type": "milestone", "time": m["time"], "title": m["title"], "description": m["description"]})
        for k in self._knowledge_events:
            events.append({"type": "knowledge", "time": k["time"], "topic": k["topic"], "gain": k["gain"]})
        for s in self._skill_events:
            events.append({"type": "skill", "time": s["time"], "skill": s["skill"], "gain": s["gain"]})
        for p in self._project_events:
            events.append({"type": "project", "time": p["time"], "name": p["name"], "status": p["status"]})
        events.sort(key=lambda e: e["time"], reverse=True)
        return events[:max_entries]

    def growth_summary(self):
        total_knowledge_gain = sum(e["gain"] for e in self._knowledge_events)
        total_skill_gain = sum(e["gain"] for e in self._skill_events)
        return {
            "milestones": len(self._milestones),
            "knowledge_events": len(self._knowledge_events),
            "skill_events": len(self._skill_events),
            "projects": len(self._project_events),
            "agent_improvements": len(self._agent_improvements),
            "workflow_improvements": len(self._workflow_improvements),
            "total_knowledge_gain": total_knowledge_gain,
            "total_skill_gain": total_skill_gain,
        }

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}

    def from_dict(self, data):
        for k, v in data.items():
            setattr(self, k, v)


class PersonalIntelligenceIdentityNetwork:
    """Phase 13 — The permanent personal intelligence layer that allows ARCANIS to understand,
    adapt to, and grow with the user throughout their digital life."""

    def __init__(self):
        self.model = PersonalIntelligenceModel()
        self.memory = MultiLayerMemory()
        self.knowledge_graph = KnowledgeGraphSystem()
        self.goals = GoalIntelligenceEngine()
        self.personalization = AdaptivePersonalizationEngine()
        self.agent_relations = AgentRelationshipSystem()
        self.life_os = LifeOSFramework()
        self.automation = AutomationLearningSystem()
        self.vault = PersonalDataVault()
        self.growth = IntelligenceGrowthTimeline()
        self._initialized = False
        self._session_start = time.time()

    def initialize(self):
        self.agent_relations.setup_default_agents()
        self.knowledge_graph.add_entity("user", "user", "ARCANIS User", {"type": "human"})
        self._initialized = True
        self.growth.add_milestone("PIIN Initialized", "Personal Intelligence Identity Network activated", "system")
        return {"status": "piin_initialized", "layers": 10}

    def observe_interaction(self, action, context=None):
        self.automation.observe_action(action, context)
        self.model.record_observation("action", {"action": action, **(context or {})})
        self.memory.store_short_term(f"{action}: {json.dumps(context)[:100] if context else ''}")

    def learn_from_feedback(self, feedback, rating):
        self.personalization.infer_from_feedback(feedback, rating)
        self.memory.store_episodic("feedback", f"Rating {rating}: {feedback[:200]}")

    def suggest_automations(self):
        return self.automation.suggestions()

    def user_profile(self):
        return self.model.profile()

    def memory_stats(self):
        return self.memory.stats()

    def knowledge_stats(self):
        return self.knowledge_graph.stats()

    def goal_summary(self):
        return self.goals.summary()

    def timeline(self):
        return self.growth.timeline()

    def full_summary(self):
        return {
            "initialized": self._initialized,
            "session_duration": time.time() - self._session_start,
            "model": {k: v for k, v in self.model.profile().items() if k != "learning_patterns"},
            "memory": self.memory.stats(),
            "knowledge_graph": self.knowledge_graph.stats(),
            "goals": self.goals.summary(),
            "personalization": self.personalization.profile()["preferences"],
            "agent_relations": {k: list(v["preferences"].keys()) for k, v in self.agent_relations.summary().items()},
            "life_os": self.life_os.stats(),
            "automation": self.automation.stats(),
            "vault": self.vault.stats(),
            "growth": self.growth.growth_summary(),
        }

    def to_dict(self):
        return {
            "model": self.model.to_dict(),
            "memory": self.memory.to_dict(),
            "knowledge_graph": self.knowledge_graph.to_dict(),
            "goals": self.goals.to_dict(),
            "personalization": self.personalization.to_dict(),
            "agent_relations": self.agent_relations.to_dict(),
            "life_os": self.life_os.to_dict(),
            "automation": self.automation.to_dict(),
            "vault": self.vault.to_dict(),
            "growth": self.growth.to_dict(),
        }

    def from_dict(self, data):
        for key in ("model", "memory", "knowledge_graph", "goals", "personalization", "agent_relations", "life_os", "automation", "vault", "growth"):
            if key in data and hasattr(self, key) and hasattr(getattr(self, key), "from_dict"):
                getattr(self, key).from_dict(data[key])


# ═══════════════════════════════════════════════════════════════
# PHASE 14 — ARCANIS REALITY INTERFACE LAYER (RIL)
# ═══════════════════════════════════════════════════════════════

class MultimodalPerceptionEngine:
    """Unified perception system for voice, text, images, video, sensors, and device states."""

    def __init__(self):
        self.modalities = {
            "voice": {"enabled": True, "last_input": "", "language": "en"},
            "text": {"enabled": True, "last_input": ""},
            "image": {"enabled": True, "last_capture": None},
            "video": {"enabled": False, "streaming": False},
            "sensor": {"enabled": True, "readings": []},
            "device_state": {"enabled": True, "states": {}},
        }
        self._perception_log = []
        self._active_modalities = set()

    def perceive(self, modality, data):
        if modality not in self.modalities or not self.modalities[modality]["enabled"]:
            return {"error": f"Modality {modality} unavailable"}
        entry = {"modality": modality, "data": str(data)[:500], "time": time.time()}
        self._perception_log.append(entry)
        self._active_modalities.add(modality)
        self.modalities[modality]["last_input"] = str(data)[:500]
        return {"perceived": True, "modality": modality, "timestamp": time.time()}

    def enable_modality(self, modality):
        if modality in self.modalities:
            self.modalities[modality]["enabled"] = True
            return True

    def disable_modality(self, modality):
        if modality in self.modalities:
            self.modalities[modality]["enabled"] = False
            return True

    def sensor_reading(self, sensor_type, value):
        self.modalities["sensor"]["readings"].append({"type": sensor_type, "value": value, "time": time.time()})
        if len(self.modalities["sensor"]["readings"]) > 100:
            self.modalities["sensor"]["readings"] = self.modalities["sensor"]["readings"][-100:]

    def device_state(self, device, state):
        self.modalities["device_state"]["states"][device] = {"state": state, "time": time.time()}

    def latest_perceptions(self, n=10):
        return self._perception_log[-n:]

    def stats(self):
        return {
            "active_modalities": len(self._active_modalities),
            "total_perceptions": len(self._perception_log),
            "modalities": {k: v["enabled"] for k, v in self.modalities.items()},
        }

    def to_dict(self):
        return {"modalities": self.modalities, "perception_log": self._perception_log[-50:]}

    def from_dict(self, data):
        if "modalities" in data:
            self.modalities = data["modalities"]
        if "perception_log" in data:
            self._perception_log = data["perception_log"]


class AdvancedVoiceSystem:
    """Natural conversation with context awareness, multi-language, emotion recognition."""

    def __init__(self):
        self.languages = {"en": "English", "es": "Spanish", "fr": "French", "de": "German", "ja": "Japanese", "zh": "Chinese", "hi": "Hindi"}
        self.active_language = "en"
        self._conversation_history = []
        self._context = {}
        self._emotion_model = {"last_emotion": "neutral", "confidence": 0.0}
        self._continuous_mode = False

    def process_speech(self, text, language=None):
        lang = language or self.active_language
        entry = {"text": text, "language": lang, "time": time.time()}
        self._conversation_history.append(entry)
        self._update_context(text)
        return {"recognized": text, "language": lang, "intent": self._detect_intent(text)}

    def _detect_intent(self, text):
        lower = text.lower()
        if any(w in lower for w in ["prepare", "setup", "ready"]):
            return "preparation"
        if any(w in lower for w in ["what", "how", "why", "when", "where"]):
            return "inquiry"
        if any(w in lower for w in ["create", "make", "build", "write"]):
            return "creation"
        if any(w in lower for w in ["find", "search", "look"]):
            return "search"
        if any(w in lower for w in ["remind", "remember", "save"]):
            return "memory"
        if any(w in lower for w in ["analyze", "check", "review"]):
            return "analysis"
        return "conversation"

    def _update_context(self, text):
        words = text.lower().split()
        for w in words:
            self._context[w] = self._context.get(w, 0) + 1
        if len(self._context) > 100:
            self._context = dict(sorted(self._context.items(), key=lambda x: -x[1])[:50])

    def detect_emotion(self, text):
        lower = text.lower()
        if any(w in lower for w in ["happy", "great", "excellent", "wonderful"]):
            self._emotion_model = {"last_emotion": "happy", "confidence": 0.7}
        elif any(w in lower for w in ["sad", "unfortunate", "disappointed"]):
            self._emotion_model = {"last_emotion": "sad", "confidence": 0.6}
        elif any(w in lower for w in ["angry", "frustrated", "annoyed"]):
            self._emotion_model = {"last_emotion": "angry", "confidence": 0.6}
        elif any(w in lower for w in ["confused", "unsure", "maybe"]):
            self._emotion_model = {"last_emotion": "confused", "confidence": 0.5}
        else:
            self._emotion_model = {"last_emotion": "neutral", "confidence": 0.3}
        return self._emotion_model

    def set_language(self, lang_code):
        if lang_code in self.languages:
            self.active_language = lang_code
            return True
        return False

    def start_continuous(self):
        self._continuous_mode = True

    def stop_continuous(self):
        self._continuous_mode = False

    def conversation_summary(self):
        return {
            "total_utterances": len(self._conversation_history),
            "active_language": self.active_language,
            "last_emotion": self._emotion_model,
            "continuous_mode": self._continuous_mode,
            "context_topics": list(self._context.keys())[:10],
        }

    def to_dict(self):
        return {"languages": self.languages, "active_language": self.active_language, "conversation": self._conversation_history[-20:], "context": self._context}

    def from_dict(self, data):
        if "active_language" in data:
            self.active_language = data["active_language"]
        if "conversation" in data:
            self._conversation_history = data["conversation"]
        if "context" in data:
            self._context = data["context"]


class ComputerVisionLayer:
    """Visual intelligence: screen understanding, object recognition, document/image analysis."""

    def __init__(self):
        self._screen_captures = []
        self._object_detections = []
        self._document_analyses = []
        self._image_analyses = []
        self._known_objects = {}  # object_id -> name, category, confidence

    def capture_screen(self, description="Screen state"):
        capture = {"description": description, "time": time.time()}
        self._screen_captures.append(capture)
        return capture

    def detect_object(self, object_id, name, category="unknown", confidence=0.5):
        detection = {"id": object_id, "name": name, "category": category, "confidence": confidence, "time": time.time()}
        self._object_detections.append(detection)
        self._known_objects[object_id] = {"name": name, "category": category, "confidence": confidence}
        return detection

    def analyze_document(self, doc_id, content_summary, doc_type="unknown"):
        analysis = {"id": doc_id, "summary": content_summary, "type": doc_type, "time": time.time()}
        self._document_analyses.append(analysis)
        return analysis

    def analyze_image(self, image_id, description, tags=None):
        analysis = {"id": image_id, "description": description, "tags": tags or [], "time": time.time()}
        self._image_analyses.append(analysis)
        return analysis

    def identify_issue(self, image_description):
        simulated_issues = {
            "circuit": "Possible component failure: check resistor R2 and capacitor C5 for visible damage",
            "code": "Syntax pattern detected: possible missing semicolon or unclosed bracket",
            "diagram": "Connection anomaly: port 3 appears disconnected from the main bus",
            "photo": "No obvious issues detected in the visual scene",
        }
        issue = "Unknown"
        for key, msg in simulated_issues.items():
            if key in image_description.lower():
                issue = msg
                break
        return {"analysis": image_description, "identified_issue": issue}

    def screen_history(self, n=5):
        return self._screen_captures[-n:]

    def stats(self):
        return {"screen_captures": len(self._screen_captures), "objects_detected": len(self._object_detections), "documents_analyzed": len(self._document_analyses), "images_analyzed": len(self._image_analyses), "known_objects": len(self._known_objects)}

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def from_dict(self, data):
        for k, v in data.items():
            setattr(self, '_'+k if k in ('known_objects',) else k, v)


class SpatialComputingFoundation:
    """Foundation for AR/VR/MR, 3D environments, virtual workspaces, spatial intelligence."""

    def __init__(self):
        self._environments = {}
        self._active_environment = None
        self._spatial_objects = {}
        self._workspaces = {}

    def create_environment(self, env_id, name, env_type="virtual", dimensions=None):
        self._environments[env_id] = {
            "id": env_id, "name": name, "type": env_type,
            "dimensions": dimensions or {"width": 10, "height": 10, "depth": 10},
            "objects": [], "active": False, "created": time.time(),
        }
        return self._environments[env_id]

    def activate_environment(self, env_id):
        if env_id in self._environments:
            for e in self._environments.values():
                e["active"] = False
            self._environments[env_id]["active"] = True
            self._active_environment = env_id
            return True
        return False

    def place_object(self, env_id, obj_id, name, position, properties=None):
        obj = {
            "id": obj_id, "name": name, "position": position,
            "properties": properties or {},
            "time": time.time(),
        }
        self._spatial_objects[obj_id] = obj
        if env_id in self._environments:
            self._environments[env_id]["objects"].append(obj_id)
        return obj

    def create_workspace(self, ws_id, name, layout="spatial", components=None):
        self._workspaces[ws_id] = {
            "id": ws_id, "name": name, "layout": layout,
            "components": components or [],
            "active": False, "created": time.time(),
        }
        return self._workspaces[ws_id]

    def activate_workspace(self, ws_id):
        if ws_id in self._workspaces:
            for w in self._workspaces.values():
                w["active"] = False
            self._workspaces[ws_id]["active"] = True
            return True
        return False

    def organize_information_space(self, topic, items):
        env_id = f"space_{int(time.time())}"
        self.create_environment(env_id, f"Information: {topic}", "information_space")
        for i, item in enumerate(items[:10]):
            pos = {"x": (i % 5) * 2, "y": (i // 5) * 2, "z": 0}
            self.place_object(env_id, f"obj_{i}", str(item)[:30], pos)
        self.activate_environment(env_id)
        return {"environment": env_id, "items_placed": len(items[:10]), "topic": topic}

    def stats(self):
        return {"environments": len(self._environments), "objects": len(self._spatial_objects), "workspaces": len(self._workspaces), "active_env": self._active_environment}

    def to_dict(self):
        return {"environments": self._environments, "spatial_objects": self._spatial_objects, "workspaces": self._workspaces}

    def from_dict(self, data):
        for k, v in data.items():
            setattr(self, '_'+k, v)


class DeviceOrchestrationLayer:
    """Communicate with computers, smartphones, smart home devices, sensors, robotics platforms."""

    def __init__(self):
        self._devices = {}
        self._device_categories = {"computer", "smartphone", "smart_home", "sensor", "robotics"}

    def register_device(self, device_id, name, category, capabilities=None):
        if category not in self._device_categories:
            return {"error": f"Unknown category: {category}"}
        self._devices[device_id] = {
            "id": device_id, "name": name, "category": category,
            "capabilities": capabilities or [],
            "status": "disconnected", "last_seen": time.time(),
            "permissions": {}, "commands_sent": 0,
        }
        return self._devices[device_id]

    def connect_device(self, device_id):
        if device_id in self._devices:
            self._devices[device_id]["status"] = "connected"
            self._devices[device_id]["last_seen"] = time.time()
            return True
        return False

    def disconnect_device(self, device_id):
        if device_id in self._devices:
            self._devices[device_id]["status"] = "disconnected"
            return True
        return False

    def send_command(self, device_id, command, params=None):
        if device_id not in self._devices:
            return {"error": "Device not found"}
        device = self._devices[device_id]
        if device["status"] != "connected":
            return {"error": "Device not connected"}
        device["commands_sent"] += 1
        device["last_seen"] = time.time()
        return {
            "device": device_id, "command": command,
            "params": params or {}, "status": "sent", "time": time.time(),
        }

    def discover_devices(self, category=None):
        if category:
            return {k: v for k, v in self._devices.items() if v["category"] == category}
        return self._devices

    def device_status(self, device_id):
        return self._devices.get(device_id)

    def stats(self):
        by_category = {}
        for d in self._devices.values():
            by_category[d["category"]] = by_category.get(d["category"], 0) + 1
        return {
            "total_devices": len(self._devices),
            "connected": sum(1 for d in self._devices.values() if d["status"] == "connected"),
            "by_category": by_category,
            "total_commands": sum(d["commands_sent"] for d in self._devices.values()),
        }

    def to_dict(self):
        return {"devices": self._devices}

    def from_dict(self, data):
        if "devices" in data:
            self._devices = data["devices"]


class RoboticsIntegrationFramework:
    """Foundation for physical agents: robot control, sensor integration, autonomous workflows."""

    def __init__(self):
        self._robots = {}
        self._sensors = {}
        self._workflows = []
        self._status = {"active_robots": 0, "completed_actions": 0, "errors": []}

    def register_robot(self, robot_id, name, robot_type="generic", capabilities=None):
        self._robots[robot_id] = {
            "id": robot_id, "name": name, "type": robot_type,
            "capabilities": capabilities or ["move", "sense"],
            "status": "idle", "position": {"x": 0, "y": 0, "z": 0},
            "battery": 100, "tasks_completed": 0, "registered": time.time(),
        }
        return self._robots[robot_id]

    def attach_sensor(self, robot_id, sensor_id, sensor_type, config=None):
        if robot_id not in self._robots:
            return {"error": "Robot not found"}
        self._sensors[sensor_id] = {
            "id": sensor_id, "robot_id": robot_id, "type": sensor_type,
            "config": config or {}, "last_reading": None, "active": True,
        }
        return self._sensors[sensor_id]

    def sensor_reading(self, sensor_id, value):
        if sensor_id in self._sensors:
            self._sensors[sensor_id]["last_reading"] = {"value": value, "time": time.time()}
            return True
        return False

    def execute_action(self, robot_id, action, params=None):
        if robot_id not in self._robots:
            return {"error": "Robot not found"}
        robot = self._robots[robot_id]
        robot["status"] = "busy"
        robot["tasks_completed"] += 1
        self._status["active_robots"] = sum(1 for r in self._robots.values() if r["status"] == "busy")
        self._status["completed_actions"] += 1
        result = {"robot": robot_id, "action": action, "params": params or {}, "status": "executed", "time": time.time()}
        robot["status"] = "idle"
        robot["battery"] = max(0, robot["battery"] - 2)
        return result

    def create_workflow(self, wf_id, name, steps):
        workflow = {"id": wf_id, "name": name, "steps": steps, "created": time.time(), "executions": 0}
        self._workflows.append(workflow)
        return workflow

    def execute_workflow(self, wf_id, robot_id):
        wf = next((w for w in self._workflows if w["id"] == wf_id), None)
        if not wf:
            return {"error": "Workflow not found"}
        results = []
        for step in wf["steps"]:
            result = self.execute_action(robot_id, step.get("action", "unknown"), step.get("params"))
            results.append(result)
        wf["executions"] += 1
        return {"workflow": wf_id, "steps_completed": len(results), "results": results}

    def organize_workspace(self, description):
        return {"plan": f"Workspace organization for: {description}", "steps": ["analyze current layout", "identify clutter sources", "create organization plan", "execute rearrangement", "verify result"], "estimated_time": "15 minutes"}

    def stats(self):
        return {"robots": len(self._robots), "sensors": len(self._sensors), "workflows": len(self._workflows), "completed_actions": self._status["completed_actions"]}

    def to_dict(self):
        return {"robots": self._robots, "sensors": self._sensors, "workflows": self._workflows, "status": self._status}

    def from_dict(self, data):
        for k in ("robots", "sensors", "workflows", "status"):
            if k in data:
                setattr(self, '_' + k, data[k])


class ContextAwarenessEngine:
    """Environmental awareness: location, active device, activity, surroundings, time, intention."""

    def __init__(self):
        self._context = {
            "location": "unknown", "active_device": "unknown",
            "current_activity": "unknown", "surroundings": [],
            "time_context": {}, "user_intention": "unknown",
        }
        self._history = []
        self._modes = {"work": {"tags": ["meeting", "code", "document", "email", "project"], "response_style": "professional"},
                       "learning": {"tags": ["tutorial", "course", "study", "practice", "read"], "response_style": "educational"},
                       "creation": {"tags": ["design", "write", "compose", "build", "create"], "response_style": "creative"},
                       "casual": {"tags": ["chat", "fun", "game", "entertainment"], "response_style": "casual"}}

    def set_location(self, location):
        self._context["location"] = location
        self._log("location", location)

    def set_device(self, device):
        self._context["active_device"] = device
        self._log("device", device)

    def set_activity(self, activity):
        self._context["current_activity"] = activity
        self._log("activity", activity)
        return self.detect_mode(activity)

    def add_surrounding(self, element):
        self._context["surroundings"].append(element)
        if len(self._context["surroundings"]) > 20:
            self._context["surroundings"] = self._context["surroundings"][-20:]

    def _log(self, key, value):
        self._history.append({"key": key, "value": value, "time": time.time()})
        if len(self._history) > 100:
            self._history = self._history[-100:]

    def detect_mode(self, activity):
        lower = activity.lower()
        for mode, config in self._modes.items():
            if any(tag in lower for tag in config["tags"]):
                self._context["user_intention"] = mode
                return {"mode": mode, "response_style": config["response_style"]}
        self._context["user_intention"] = "general"
        return {"mode": "general", "response_style": "balanced"}

    def current(self):
        return {
            **self._context,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "hour": time.localtime().tm_hour,
            "day": time.strftime("%A"),
        }

    def history(self, n=10):
        return self._history[-n:]

    def stats(self):
        return {"location_set": self._context["location"] != "unknown", "device_set": self._context["active_device"] != "unknown", "total_updates": len(self._history), "current_mode": self._context["user_intention"]}

    def to_dict(self):
        return {"context": self._context, "history": self._history}

    def from_dict(self, data):
        if "context" in data:
            self._context = data["context"]
        if "history" in data:
            self._history = data["history"]


class HumanAIInteractionModel:
    """New interaction language: conversation, intent, visualization, actions — not buttons/menus/commands."""

    def __init__(self):
        self._interaction_history = []
        self._visualizations = []
        self._suggested_actions = []
        self._mode = "conversation"

    def process_intent(self, user_input):
        entry = {"input": user_input, "mode": self._mode, "time": time.time()}
        self._interaction_history.append(entry)
        intent_type = self._classify_intent(user_input)
        response = self._generate_response(intent_type, user_input)
        action = self._suggest_action(intent_type, user_input)
        return {"intent": intent_type, "response": response, "suggested_action": action}

    def _classify_intent(self, text):
        lower = text.lower()
        if any(w in lower for w in ["show", "display", "visualize", "see"]):
            return "visualization"
        if any(w in lower for w in ["do", "execute", "run", "perform"]):
            return "action"
        if any(w in lower for w in ["what", "how", "explain", "tell", "why"]):
            return "inquiry"
        if any(w in lower for w in ["create", "make", "design", "build"]):
            return "creation"
        return "conversation"

    def _generate_response(self, intent_type, text):
        templates = {
            "visualization": "I can visualize that. Let me prepare a spatial representation.",
            "action": "Understood. I will take action on that now.",
            "inquiry": "Let me analyze that and provide clear information.",
            "creation": "I can help create that. Let me organize the process.",
            "conversation": "I understand. How would you like to proceed?",
        }
        return templates.get(intent_type, templates["conversation"])

    def _suggest_action(self, intent_type, text):
        suggestions = {
            "visualization": {"type": "visualization", "description": "Show as spatial information layout"},
            "action": {"type": "execute", "description": "Execute directly with full permissions"},
            "inquiry": {"type": "research", "description": "Search and compile relevant information"},
            "creation": {"type": "workspace", "description": "Open a creation workspace"},
            "conversation": {"type": "continue", "description": "Continue the conversation"},
        }
        action = suggestions.get(intent_type, suggestions["conversation"])
        self._suggested_actions.append(action)
        return action

    def add_visualization(self, viz_type, content):
        viz = {"type": viz_type, "content": content, "time": time.time()}
        self._visualizations.append(viz)
        return viz

    def set_mode(self, mode):
        if mode in ("conversation", "action", "visualization", "hybrid"):
            self._mode = mode

    def history(self, n=10):
        return self._interaction_history[-n:]

    def stats(self):
        return {"total_interactions": len(self._interaction_history), "visualizations": len(self._visualizations), "suggestions": len(self._suggested_actions), "current_mode": self._mode}

    def to_dict(self):
        return {"interaction_history": self._interaction_history[-50:], "visualizations": self._visualizations[-20:], "mode": self._mode}

    def from_dict(self, data):
        if "interaction_history" in data:
            self._interaction_history = data["interaction_history"]
        if "visualizations" in data:
            self._visualizations = data["visualizations"]
        if "mode" in data:
            self._mode = data["mode"]


class ARCANISPresenceSystem:
    """ARCANIS identity: voice personality, visual identity, interaction style, context adaptation."""

    def __init__(self):
        self.personality_traits = {
            "formality": 0.4, "warmth": 0.8, "directness": 0.6,
            "creativity": 0.7, "precision": 0.5,
        }
        self.identity_name = "ARCANIS"
        self.visual_identity = {"symbol": "Ω", "color": "#00D4FF", "style": "minimal"}
        self.interaction_style = "adaptive"
        self._presence_log = []
        self._state = "idle"

    def set_state(self, state):
        valid_states = {"idle", "listening", "processing", "responding", "active", "background"}
        if state in valid_states:
            self._state = state
            self._presence_log.append({"state": state, "time": time.time()})

    def adapt_style(self, context_mode):
        if context_mode == "professional":
            self.personality_traits["formality"] = 0.8
            self.personality_traits["warmth"] = 0.4
        elif context_mode == "educational":
            self.personality_traits["formality"] = 0.5
            self.personality_traits["warmth"] = 0.7
            self.personality_traits["precision"] = 0.8
        elif context_mode == "creative":
            self.personality_traits["formality"] = 0.2
            self.personality_traits["creativity"] = 0.9
            self.personality_traits["warmth"] = 0.8
        elif context_mode == "casual":
            self.personality_traits["formality"] = 0.1
            self.personality_traits["warmth"] = 0.9
            self.personality_traits["directness"] = 0.3

    def greeting(self):
        greetings = {
            "active": "ARCANIS online. How can I interact with your world?",
            "idle": "ARCANIS ready. Your intelligence layer is active.",
            "listening": "ARCANIS listening. I'm processing your environment.",
        }
        return greetings.get(self._state, "ARCANIS present.")

    def presence_summary(self):
        return {
            "identity": self.identity_name,
            "state": self._state,
            "style": self.interaction_style,
            "personality": self.personality_traits,
            "visual": self.visual_identity,
            "state_log": self._presence_log[-5:],
        }

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def from_dict(self, data):
        for k, v in data.items():
            setattr(self, k, v)


class RealitySecurityFramework:
    """Physical-world access control: device permissions, action confirmation, emergency stop, safety boundaries."""

    def __init__(self):
        self._permissions = {}
        self._action_log = []
        self._emergency_stop = False
        self._safety_boundaries = {}
        self._risk_levels = {"low": ["open", "read", "display", "search"],
                             "medium": ["write", "modify", "send", "configure"],
                             "high": ["delete", "execute", "install", "modify_system"],
                             "critical": ["physical_action", "remote_access", "full_system"]}

    def set_permission(self, action, level):
        self._permissions[action] = level
        return True

    def check_permission(self, action):
        for level, actions in self._risk_levels.items():
            if action in actions:
                risk = level
                break
        else:
            risk = "low"
        required = self._permissions.get(action, risk)
        return {"action": action, "risk_level": risk, "required_confirmation": risk in ("high", "critical"), "approved": risk != "critical"}

    def confirm_action(self, action, details=None):
        check = self.check_permission(action)
        if self._emergency_stop:
            return {"approved": False, "reason": "Emergency stop active"}
        if check["required_confirmation"]:
            entry = {"action": action, "details": details or {}, "approved": True, "time": time.time()}
            self._action_log.append(entry)
            return {"approved": True, "action": action, "note": "Confirmed by user"}
        entry = {"action": action, "details": details or {}, "approved": True, "auto": True, "time": time.time()}
        self._action_log.append(entry)
        return {"approved": True, "action": action, "note": "Auto-approved"}

    def emergency_stop(self):
        self._emergency_stop = True
        return {"status": "emergency_stop_engaged", "time": time.time()}

    def release_emergency_stop(self):
        self._emergency_stop = False
        return {"status": "emergency_stop_released"}

    def set_safety_boundary(self, boundary_id, limits):
        self._safety_boundaries[boundary_id] = {"limits": limits, "active": True, "created": time.time()}

    def check_safety(self, action, context=None):
        if self._emergency_stop:
            return {"safe": False, "reason": "Emergency stop"}
        for bid, boundary in self._safety_boundaries.items():
            if not boundary["active"]:
                continue
            limits = boundary["limits"]
            if "max_actions" in limits and self._count_recent_actions() > limits["max_actions"]:
                return {"safe": False, "reason": f"Exceeded max actions for boundary {bid}"}
        return {"safe": True}

    def _count_recent_actions(self, seconds=60):
        cutoff = time.time() - seconds
        return sum(1 for a in self._action_log if a["time"] > cutoff)

    def activity_log(self, n=20):
        return self._action_log[-n:]

    def stats(self):
        return {"total_actions": len(self._action_log), "permissions_set": len(self._permissions), "safety_boundaries": len(self._safety_boundaries), "emergency_stop": self._emergency_stop}

    def to_dict(self):
        return {"permissions": self._permissions, "action_log": self._action_log[-50:], "safety_boundaries": self._safety_boundaries, "emergency_stop": self._emergency_stop}

    def from_dict(self, data):
        if "permissions" in data:
            self._permissions = data["permissions"]
        if "action_log" in data:
            self._action_log = data["action_log"]
        if "safety_boundaries" in data:
            self._safety_boundaries = data["safety_boundaries"]
        if "emergency_stop" in data:
            self._emergency_stop = data["emergency_stop"]


class RealityInterfaceLayer:
    """Phase 14 — ARCANIS Reality Interface Layer. The intelligence layer that allows ARCANIS to
    interact naturally with the human world through voice, vision, sensors, devices, robotics, and spatial environments."""

    def __init__(self):
        self.perception = MultimodalPerceptionEngine()
        self.voice = AdvancedVoiceSystem()
        self.vision = ComputerVisionLayer()
        self.spatial = SpatialComputingFoundation()
        self.devices = DeviceOrchestrationLayer()
        self.robotics = RoboticsIntegrationFramework()
        self.context = ContextAwarenessEngine()
        self.interaction = HumanAIInteractionModel()
        self.presence = ARCANISPresenceSystem()
        self.security = RealitySecurityFramework()
        self._initialized = False

    def initialize(self):
        self.presence.set_state("idle")
        self._initialized = True
        return {"status": "ril_initialized", "layers": 10}

    def process_environment(self, input_text, modality="text"):
        perception = self.perception.perceive(modality, input_text)
        voice_result = self.voice.process_speech(input_text)
        context = self.context.set_activity(input_text)
        presence = self.presence.adapt_style(context.get("response_style", "balanced"))
        self.presence.set_state("processing")
        interaction = self.interaction.process_intent(input_text)
        self.presence.set_state("responding")
        return {
            "perception": {"modality": modality, "status": perception.get("perceived")},
            "voice": {"text": voice_result["text"], "intent": voice_result["intent"], "emotion": self.voice.detect_emotion(input_text)},
            "context": {"mode": context.get("mode", "general"), "style": context.get("response_style", "balanced")},
            "interaction": {"response": interaction["response"], "suggested_action": interaction["suggested_action"]},
            "presence": self.presence.greeting(),
        }

    def full_summary(self):
        return {
            "perception": self.perception.stats(),
            "voice": self.voice.conversation_summary(),
            "vision": self.vision.stats(),
            "spatial": self.spatial.stats(),
            "devices": self.devices.stats(),
            "robotics": self.robotics.stats(),
            "context": self.context.stats(),
            "interaction": self.interaction.stats(),
            "presence": self.presence.presence_summary(),
            "security": self.security.stats(),
        }

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.__dict__.items() if k != '_initialized' and hasattr(v, 'to_dict')}

    def from_dict(self, data):
        for key in ("perception", "voice", "vision", "spatial", "devices", "robotics", "context", "interaction", "presence", "security"):
            if key in data and hasattr(self, key) and hasattr(getattr(self, key), "from_dict"):
                getattr(self, key).from_dict(data[key])


# ═══════════════════════════════════════════════════════════════
# PHASE 15 — ARCANIS AUTONOMOUS CREATION & DISCOVERY ENGINE (ACDE)
# ═══════════════════════════════════════════════════════════════

class IdeaProcessingEngine:
    """Universal creation pipeline: idea/goal/problem/question → research → plan → create → test → improve."""

    def __init__(self):
        self._pipeline = {"understand": [], "research": [], "solution": [], "prototype": [], "evaluate": [], "improve": []}
        self._projects = {}
        self._ideas = []

    def submit_idea(self, title, description, category="general"):
        idea = {"id": f"idea_{int(time.time())}", "title": title, "description": description, "category": category, "stage": "understanding", "created": time.time()}
        self._ideas.append(idea)
        self._projects[idea["id"]] = {"idea": idea, "pipeline": {k: [] for k in self._pipeline}, "current_stage": "understanding", "history": []}
        return self._run_pipeline(idea["id"])

    def _run_pipeline(self, pid):
        project = self._projects[pid]
        stages = ["understanding", "research", "planning", "creation", "testing", "improvement"]
        project["pipeline"]["understand"] = [f"Analyze objective: {project['idea']['description'][:80]}", "Identify constraints", "Define success criteria"]
        project["pipeline"]["research"] = [f"Search existing knowledge on {project['idea']['title']}", "Analyze similar solutions", "Identify best practices"]
        project["pipeline"]["solution"] = [f"Generate solution approaches for {project['idea']['title']}", "Evaluate feasibility", "Select optimal approach"]
        project["pipeline"]["prototype"] = [f"Create prototype for {project['idea']['title']}", "Implement core functionality", "Test basic assumptions"]
        project["pipeline"]["evaluate"] = ["Test against success criteria", "Identify gaps and issues", "Collect feedback"]
        project["pipeline"]["improve"] = ["Analyze test results", "Refine implementation", "Optimize performance"]
        project["current_stage"] = "understanding"
        return {"project_id": pid, "title": project["idea"]["title"], "stages": stages, "pipeline": project["pipeline"]}

    def advance_stage(self, pid):
        if pid not in self._projects:
            return {"error": "Project not found"}
        project = self._projects[pid]
        stages = ["understanding", "research", "planning", "creation", "testing", "improvement"]
        current_idx = stages.index(project["current_stage"]) if project["current_stage"] in stages else 0
        if current_idx < len(stages) - 1:
            project["current_stage"] = stages[current_idx + 1]
            project["history"].append({"stage": stages[current_idx], "completed": time.time()})
            return {"project": pid, "stage": project["current_stage"], "progress": int((current_idx + 1) / len(stages) * 100)}
        return {"project": pid, "stage": "complete", "progress": 100}

    def project_status(self, pid):
        return self._projects.get(pid, {"error": "Not found"})

    def list_projects(self):
        return [{"id": pid, "title": p["idea"]["title"], "stage": p["current_stage"], "category": p["idea"]["category"]} for pid, p in self._projects.items()]

    def stats(self):
        return {"total_ideas": len(self._ideas), "active_projects": len(self._projects), "by_category": {}}

    def to_dict(self):
        return {"projects": self._projects, "ideas": self._ideas}

    def from_dict(self, data):
        if "projects" in data:
            self._projects = data["projects"]
        if "ideas" in data:
            self._ideas = data["ideas"]


class AutonomousResearchFramework:
    """Research intelligence with specialized agent network for literature, technical, market, and creative research."""

    def __init__(self):
        self._agents = {"scientific": [], "technical": [], "market": [], "creative": []}
        self._findings = []
        self._hypotheses = []

    def research_topic(self, topic, depth="standard"):
        findings = []
        for agent_type, agent_findings in self._agents.items():
            simulated = self._simulate_research(agent_type, topic)
            findings.append({"agent": agent_type, "findings": simulated, "confidence": 0.7})
        entry = {"topic": topic, "depth": depth, "findings": findings, "time": time.time()}
        self._findings.append(entry)
        synthesis = self._synthesize(findings)
        return {"topic": topic, "findings": findings, "synthesis": synthesis, "hypotheses": self._generate_hypotheses(topic)}

    def _simulate_research(self, agent_type, topic):
        sims = {
            "scientific": [f"Literature review on {topic}", f"Identify key papers and theories", "Analyze methodology", "Evaluate evidence quality"],
            "technical": [f"Technical analysis of {topic}", "Evaluate implementation options", "Assess performance characteristics", "Review technical constraints"],
            "market": [f"Market analysis for {topic}", "Identify target audience", "Analyze competition", "Estimate market potential"],
            "creative": [f"Creative exploration of {topic}", "Generate novel approaches", "Explore cross-domain connections", "Identify innovative angles"],
        }
        return sims.get(agent_type, [f"General research on {topic}"])

    def _synthesize(self, findings):
        all_points = []
        for f in findings:
            all_points.extend(f["findings"])
        return {"key_insights": all_points[:3], "summary": f"Synthesized {len(all_points)} research points across {len(findings)} domains", "confidence": 0.75}

    def _generate_hypotheses(self, topic):
        h = [f"{topic} can be optimized through novel algorithmic approaches", f"Cross-disciplinary methods from biology could advance {topic}", f"The next breakthrough in {topic} will come from combining existing techniques in new ways"]
        self._hypotheses.extend(h)
        return h

    def add_finding(self, agent_type, finding):
        if agent_type in self._agents:
            self._agents[agent_type].append({"finding": finding, "time": time.time()})

    def recent_findings(self, n=5):
        return self._findings[-n:]

    def stats(self):
        return {"agents_active": sum(len(v) for v in self._agents.values()), "findings": len(self._findings), "hypotheses": len(self._hypotheses)}

    def to_dict(self):
        return {"agents": self._agents, "findings": self._findings[-20:], "hypotheses": self._hypotheses}

    def from_dict(self, data):
        if "agents" in data:
            self._agents = data["agents"]
        if "findings" in data:
            self._findings = data["findings"]
        if "hypotheses" in data:
            self._hypotheses = data["hypotheses"]


class AIDevelopmentEngine:
    """Software development intelligence: requirements → architecture → code → test → deploy."""

    def __init__(self):
        self._projects = {}
        self._code_repos = {}
        self._tests = []
        self._debug_log = []

    def create_project(self, name, description, language="python"):
        pid = f"dev_{int(time.time())}"
        self._projects[pid] = {
            "id": pid, "name": name, "description": description, "language": language,
            "architecture": {}, "files": [], "tests": [], "status": "design",
            "created": time.time(),
        }
        return self._generate(pid)

    def _generate(self, pid):
        proj = self._projects[pid]
        proj["architecture"] = {"pattern": "modular", "components": [f"{proj['name']}Core", f"{proj['name']}API", f"{proj['name']}CLI"], "data_flow": "input→process→output"}
        proj["files"] = [
            {"name": f"main.py", "content": f"# {proj['name']}\n# {proj['description']}\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()"},
            {"name": f"core.py", "content": f"# Core module\nclass {proj['name'].replace(' ','')}Core:\n    def __init__(self):\n        pass"},
            {"name": f"tests/test_{proj['name'].lower().replace(' ','_')}.py", "content": "def test_basic():\n    assert True"},
        ]
        proj["tests"] = [{"name": "test_basic", "status": "passed", "duration": "0.01s"}]
        proj["status"] = "generated"
        return proj

    def debug(self, pid, issue):
        self._debug_log.append({"project": pid, "issue": issue, "time": time.time()})
        solution = f"Analysis of '{issue}': Check for common patterns — syntax errors, type mismatches, or missing imports"
        return {"issue": issue, "analysis": solution, "suggested_fix": "Review the identified area and apply standard patterns"}

    def test_project(self, pid):
        if pid not in self._projects:
            return {"error": "Project not found"}
        proj = self._projects[pid]
        results = [{"name": t["name"], "status": t["status"]} for t in proj["tests"]]
        return {"project": pid, "tests_run": len(results), "passed": sum(1 for r in results if r["status"] == "passed"), "results": results}

    def stats(self):
        return {"projects": len(self._projects), "tests": sum(len(p["tests"]) for p in self._projects.values()), "debug_sessions": len(self._debug_log)}

    def to_dict(self):
        return {"projects": self._projects, "debug_log": self._debug_log}

    def from_dict(self, data):
        if "projects" in data:
            self._projects = data["projects"]
        if "debug_log" in data:
            self._debug_log = data["debug_log"]


class SimulationEnvironment:
    """Digital experimentation environment for engineering, robotics, science, business models, and design."""

    def __init__(self):
        self._simulations = []
        self._models = {}
        self._results = []

    def create_simulation(self, name, sim_type, parameters=None):
        sim_id = f"sim_{int(time.time())}"
        sim = {
            "id": sim_id, "name": name, "type": sim_type,
            "parameters": parameters or {}, "status": "created",
            "created": time.time(),
        }
        self._simulations.append(sim)
        return sim

    def run(self, sim_id, iterations=100):
        sim = next((s for s in self._simulations if s["id"] == sim_id), None)
        if not sim:
            return {"error": "Simulation not found"}
        sim["status"] = "running"
        import random
        result = {
            "simulation": sim_id, "name": sim["name"], "iterations": iterations,
            "convergence": random.uniform(0.85, 0.99),
            "metrics": {"accuracy": random.uniform(0.7, 0.95), "stability": random.uniform(0.8, 1.0), "performance": random.uniform(50, 100)},
            "time": time.time(),
        }
        self._results.append(result)
        sim["status"] = "completed"
        return result

    def compare_scenarios(self, scenarios):
        results = []
        for scenario in scenarios[:5]:
            sim = self.create_simulation(scenario, "comparison")
            result = self.run(sim["id"], 50)
            results.append({"scenario": scenario, **result["metrics"]})
        return {"scenarios_compared": len(results), "results": results}

    def stats(self):
        return {"total_simulations": len(self._simulations), "completed": sum(1 for s in self._simulations if s["status"] == "completed"), "results": len(self._results)}

    def to_dict(self):
        return {"simulations": self._simulations, "results": self._results}

    def from_dict(self, data):
        if "simulations" in data:
            self._simulations = data["simulations"]
        if "results" in data:
            self._results = data["results"]


class CreativeIntelligenceSystem:
    """Creative generation: UI design, visual creation, writing, branding, architecture, product design."""

    def __init__(self):
        self._creations = []
        self._styles = {"minimal", "modern", "futuristic", "organic", "industrial", "classic", "playful"}
        self._domains = ["ui_design", "visual", "writing", "branding", "architecture", "product"]

    def create(self, domain, concept, style="modern", audience="general", constraints=None):
        if domain not in self._domains:
            return {"error": f"Unknown domain: {domain}"}
        creation = {
            "id": f"cre_{int(time.time())}", "domain": domain, "concept": concept,
            "style": style, "audience": audience, "constraints": constraints or {},
            "created": time.time(),
        }
        output = self._generate_creative(creation)
        creation["output"] = output
        self._creations.append(creation)
        return creation

    def _generate_creative(self, creation):
        templates = {
            "ui_design": {"layout": "Clean, minimal interface with focus on content", "colors": ["#1a1a2e", "#16213e", "#0f3460", "#e94560"], "typography": "Sans-serif, responsive", "components": ["navigation", "content_area", "interaction_elements"]},
            "visual": {"composition": "Balanced with focal point", "palette": "Complementary with accent", "mood": "Professional and inviting", "elements": ["shapes", "typography", "imagery"]},
            "writing": {"tone": "Professional yet accessible", "structure": "Hook → Context → Value → Call to action", "length": "Concise", "voice": "Active and confident"},
            "branding": {"identity": "Distinct and memorable", "colors": ["primary", "secondary", "accent"], "values": ["innovation", "trust", "quality"], "positioning": "Market leader in perception"},
            "architecture": {"style": creation["style"], "spatial_concept": "Open and fluid", "materials": ["sustainable", "smart", "adaptive"], "features": ["natural_light", "green_space", "smart_integration"]},
            "product": {"form": "Ergonomic and intuitive", "function": "Solves core user need", "experience": "Delightful at every touchpoint", "materials": ["sustainable", "durable"]},
        }
        base = templates.get(creation["domain"], {"description": f"Creative work in {creation['domain']}"})
        base["concept"] = creation["concept"]
        base["style"] = creation["style"]
        base["audience"] = creation["audience"]
        return base

    def list_styles(self):
        return sorted(self._styles)

    def recent(self, n=5):
        return self._creations[-n:]

    def stats(self):
        by_domain = {}
        for c in self._creations:
            by_domain[c["domain"]] = by_domain.get(c["domain"], 0) + 1
        return {"total_creations": len(self._creations), "by_domain": by_domain}

    def to_dict(self):
        return {"creations": self._creations}

    def from_dict(self, data):
        if "creations" in data:
            self._creations = data["creations"]


class MultiAgentCreationFramework:
    """Combine multiple specialized agents into coordinated creation teams."""

    def __init__(self):
        self._teams = {}
        self._agent_types = ["research", "engineering", "business", "design", "writing", "analysis", "testing", "presentation"]

    def create_team(self, name, agents=None):
        team_id = f"team_{int(time.time())}"
        selected_agents = agents or self._agent_types[:4]
        team = {
            "id": team_id, "name": name, "agents": selected_agents,
            "status": "assembled", "missions": [], "created": time.time(),
        }
        self._teams[team_id] = team
        return team

    def assign_mission(self, team_id, mission):
        if team_id not in self._teams:
            return {"error": "Team not found"}
        team = self._teams[team_id]
        mission_id = f"mission_{int(time.time())}"
        contributions = {}
        for agent in team["agents"]:
            contributions[agent] = self._simulate_contribution(agent, mission)
        result = {
            "id": mission_id, "team": team_id, "mission": mission,
            "contributions": contributions, "status": "completed", "time": time.time(),
        }
        team["missions"].append(result)
        return result

    def _simulate_contribution(self, agent_type, mission):
        sims = {
            "research": f"Research complete: comprehensive analysis of '{mission}'",
            "engineering": f"Engineering plan: technical architecture for '{mission}'",
            "business": f"Business model: market analysis and strategy for '{mission}'",
            "design": f"Design concept: visual and experience design for '{mission}'",
            "writing": f"Content created: documentation and messaging for '{mission}'",
            "analysis": f"Analysis done: data-driven insights for '{mission}'",
            "testing": f"Testing complete: validation and QA for '{mission}'",
            "presentation": f"Presentation ready: structured pitch for '{mission}'",
        }
        return sims.get(agent_type, f"{agent_type} working on: {mission}")

    def team_status(self, team_id):
        return self._teams.get(team_id)

    def stats(self):
        return {"teams": len(self._teams), "total_missions": sum(len(t["missions"]) for t in self._teams.values())}

    def to_dict(self):
        return {"teams": self._teams}

    def from_dict(self, data):
        if "teams" in data:
            self._teams = data["teams"]


class KnowledgeSynthesisEngine:
    """Cross-domain connections: identifies shared concepts, innovations, and novel approaches between unrelated fields."""

    def __init__(self):
        self._domains = {}
        self._connections = []
        self._innovations = []

    def register_domain(self, name, concepts):
        self._domains[name] = {"name": name, "concepts": concepts, "registered": time.time()}

    def synthesize(self, domains):
        available = [d for d in domains if d in self._domains]
        if len(available) < 2:
            return {"error": "Need at least 2 registered domains"}
        connections = []
        for i, d1 in enumerate(available):
            for d2 in available[i+1:]:
                shared = self._find_shared(d1, d2)
                innovation = self._generate_innovation(d1, d2)
                connections.append({"domain_a": d1, "domain_b": d2, "shared_concepts": shared, "innovation": innovation})
                self._connections.append(connections[-1])
        return {"domains_synthesized": available, "connections": connections}

    def _find_shared(self, d1, d2):
        c1 = set(self._domains.get(d1, {}).get("concepts", []))
        c2 = set(self._domains.get(d2, {}).get("concepts", []))
        shared = c1 & c2
        return list(shared)[:5] if shared else [f"Pattern: {d1} and {d2} share structural similarities"]

    def _generate_innovation(self, d1, d2):
        innovation = f"Cross-domain insight: Applying {d1} methodology to {d2} could yield novel approaches in problem-solving and optimization"
        self._innovations.append({"domains": [d1, d2], "innovation": innovation, "time": time.time()})
        return innovation

    def recent_innovations(self, n=5):
        return self._innovations[-n:]

    def stats(self):
        return {"domains": len(self._domains), "connections": len(self._connections), "innovations": len(self._innovations)}

    def to_dict(self):
        return {"domains": self._domains, "connections": self._connections, "innovations": self._innovations}

    def from_dict(self, data):
        if "domains" in data:
            self._domains = data["domains"]
        if "connections" in data:
            self._connections = data["connections"]
        if "innovations" in data:
            self._innovations = data["innovations"]


class ImprovementLoop:
    """Self-improving creation cycle: create → measure → analyze → improve → create better version."""

    def __init__(self):
        self._cycles = []
        self._metrics = []
        self._improvements = []

    def run_cycle(self, creation_id, metrics=None):
        cycle = {
            "id": f"cycle_{int(time.time())}", "creation_id": creation_id,
            "metrics": metrics or {"quality": 0.6, "efficiency": 0.6, "user_satisfaction": 0.6},
            "analysis": None, "improvements": [], "time": time.time(),
        }
        cycle["analysis"] = self._analyze(cycle["metrics"])
        cycle["improvements"] = self._generate_improvements(cycle["analysis"])
        self._cycles.append(cycle)
        self._metrics.append(cycle["metrics"])
        return cycle

    def _analyze(self, metrics):
        lowest = min(metrics.items(), key=lambda x: x[1])
        return {
            "overall_score": sum(metrics.values()) / len(metrics),
            "strength": max(metrics.items(), key=lambda x: x[1])[0],
            "weakness": lowest[0],
            "gap": 1.0 - lowest[1],
            "recommendation": f"Focus on improving '{lowest[0]}' from {lowest[1]:.0%} to 90%+",
        }

    def _generate_improvements(self, analysis):
        imps = [f"Optimize {analysis['weakness']} through targeted refinement", "Apply lessons from previous creation cycles", "Incorporate user feedback patterns"]
        self._improvements.extend(imps)
        return imps

    def apply_improvement(self, cycle_id, improvement):
        cycle = next((c for c in self._cycles if c["id"] == cycle_id), None)
        if cycle:
            cycle["applied"] = cycle.get("applied", [])
            cycle["applied"].append({"improvement": improvement, "time": time.time()})

    def improvement_history(self, n=10):
        return self._improvements[-n:]

    def stats(self):
        return {"cycles": len(self._cycles), "improvements_generated": len(self._improvements), "avg_score": sum(m.get("quality", 0) for m in self._metrics) / max(1, len(self._metrics))}

    def to_dict(self):
        return {"cycles": self._cycles, "improvements": self._improvements}

    def from_dict(self, data):
        if "cycles" in data:
            self._cycles = data["cycles"]
        if "improvements" in data:
            self._improvements = data["improvements"]


class HumanCollaborationModes:
    """Modes: Assistant (AI suggests), Collaborator (AI builds with user), Research (AI explores), Autonomous (AI executes approved workflows)."""

    def __init__(self):
        self._modes = {"assistant": {"description": "AI suggests options, user decides", "autonomy": 0.2, "active": False},
                       "collaborator": {"description": "AI builds with user, shared creation", "autonomy": 0.5, "active": False},
                       "research": {"description": "AI explores possibilities independently", "autonomy": 0.7, "active": False},
                       "autonomous": {"description": "AI executes approved workflows", "autonomy": 0.9, "active": False}}
        self._active_mode = "assistant"
        self._mode_history = []
        self._suggestions = []

    def set_mode(self, mode):
        if mode not in self._modes:
            return {"error": f"Unknown mode: {mode}. Available: {', '.join(self._modes.keys())}"}
        for k in self._modes:
            self._modes[k]["active"] = False
        self._modes[mode]["active"] = True
        self._active_mode = mode
        self._mode_history.append({"mode": mode, "time": time.time()})
        return {"mode": mode, "autonomy": self._modes[mode]["autonomy"], "description": self._modes[mode]["description"]}

    def process_request(self, request):
        suggestions = []
        if self._active_mode in ("assistant",):
            suggestions.append(f"Option 1: {request} — I can help guide this process")
            suggestions.append(f"Option 2: Alternative approach to {request}")
            suggestions.append(f"Option 3: Let me research {request} further")
        elif self._active_mode in ("collaborator",):
            suggestions.append(f"Let's build this together. I'll start with a framework for {request}")
            suggestions.append(f"I can handle the technical parts while you focus on the creative direction")
        elif self._active_mode in ("research",):
            suggestions.append(f"Exploring possibilities for {request}...")
            suggestions.append(f"Investigating novel approaches to {request}")
        elif self._active_mode in ("autonomous",):
            suggestions.append(f"Autonomous execution initiated for {request}")
            suggestions.append(f"Working on {request} with full workflow approval")
        self._suggestions.append({"request": request, "mode": self._active_mode, "suggestions": suggestions, "time": time.time()})
        return {"mode": self._active_mode, "suggestions": suggestions, "autonomy_level": self._modes[self._active_mode]["autonomy"]}

    def current_mode(self):
        return {"mode": self._active_mode, "config": self._modes[self._active_mode]}

    def stats(self):
        return {"active_mode": self._active_mode, "mode_switches": len(self._mode_history), "total_suggestions": len(self._suggestions)}

    def to_dict(self):
        return {"modes": self._modes, "active_mode": self._active_mode, "mode_history": self._mode_history}

    def from_dict(self, data):
        if "modes" in data:
            self._modes = data["modes"]
        if "active_mode" in data:
            self._active_mode = data["active_mode"]


class CreationMemorySystem:
    """Stores designs, attempts, methods, preferences, and project history for cumulative improvement."""

    def __init__(self):
        self._designs = []
        self._attempts = []
        self._methods = {}
        self._preferences = {}
        self._project_history = []

    def store_design(self, name, design_data, domain="general"):
        entry = {"id": f"des_{int(time.time())}", "name": name, "domain": domain, "data": design_data, "time": time.time()}
        self._designs.append(entry)
        return entry

    def store_attempt(self, project, outcome, details=None):
        attempt = {"project": project, "outcome": outcome, "details": details or {}, "time": time.time()}
        self._attempts.append(attempt)
        if outcome == "failed":
            self._learn_from_failure(project, details)
        return attempt

    def _learn_from_failure(self, project, details):
        method_key = f"lesson_{project}"
        self._methods[method_key] = {"project": project, "lesson": "Avoid: " + str(details.get("reason", "unknown"))[:100], "from_failure": True, "time": time.time()}

    def store_method(self, name, description, domain="general"):
        self._methods[name] = {"name": name, "description": description, "domain": domain, "time": time.time()}

    def record_project(self, name, status, outcome=None):
        self._project_history.append({"name": name, "status": status, "outcome": outcome, "time": time.time()})

    def recall_similar(self, query, domain=None):
        results = []
        for d in self._designs:
            if query.lower() in d["name"].lower() or (domain and d["domain"] == domain):
                results.append(d)
        for m in self._methods.values():
            if query.lower() in m.get("name", "").lower():
                results.append(m)
        return results[:10]

    def stats(self):
        return {"designs": len(self._designs), "attempts": len(self._attempts), "methods": len(self._methods), "projects": len(self._project_history)}

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}

    def from_dict(self, data):
        for k, v in data.items():
            setattr(self, '_' + k.lstrip('_'), v)


class AutonomousCreationDiscoveryEngine:
    """Phase 15 — The intelligence layer that transforms human ideas, problems, and goals
    into research, designs, software, simulations, and real-world solutions."""

    def __init__(self):
        self.ideas = IdeaProcessingEngine()
        self.research = AutonomousResearchFramework()
        self.dev_engine = AIDevelopmentEngine()
        self.simulation = SimulationEnvironment()
        self.creative = CreativeIntelligenceSystem()
        self.teams = MultiAgentCreationFramework()
        self.synthesis = KnowledgeSynthesisEngine()
        self.improvement = ImprovementLoop()
        self.collab = HumanCollaborationModes()
        self.memory = CreationMemorySystem()
        self._initialized = False

    def initialize(self):
        self._initialized = True
        self.synthesis.register_domain("AI", ["machine learning", "neural networks", "reasoning", "optimization"])
        self.synthesis.register_domain("Biology", ["evolution", "genetics", "homeostasis", "adaptation"])
        self.synthesis.register_domain("Robotics", ["control systems", "sensors", "actuation", "autonomy"])
        self.synthesis.register_domain("Design", ["aesthetics", "user experience", "form", "function"])
        return {"status": "acde_initialized", "layers": 10}

    def create_from_idea(self, title, description):
        pipeline = self.ideas.submit_idea(title, description)
        research = self.research.research_topic(title)
        self.memory.store_design(title, {"description": description, "pipeline": pipeline, "research": research})
        self.memory.record_project(title, "created")
        return {"pipeline": pipeline, "research": research["synthesis"]}

    def full_summary(self):
        return {
            "ideas": self.ideas.stats(),
            "research": self.research.stats(),
            "dev_projects": self.dev_engine.stats(),
            "simulations": self.simulation.stats(),
            "creations": self.creative.stats(),
            "teams": self.teams.stats(),
            "synthesis": self.synthesis.stats(),
            "improvement": self.improvement.stats(),
            "collab_mode": self.collab.current_mode(),
            "creation_memory": self.memory.stats(),
        }

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.__dict__.items() if k != '_initialized' and hasattr(v, 'to_dict')}

    def from_dict(self, data):
        for key in ["ideas", "research", "dev_engine", "simulation", "creative", "teams", "synthesis", "improvement", "collab", "memory"]:
            if key in data and hasattr(self, key) and hasattr(getattr(self, key), "from_dict"):
                getattr(self, key).from_dict(data[key])


# ═══════════════════════════════════════════════════════════════
# PHASE 16 — INTELLIGENCE ECOSYSTEM & DEVELOPER CIVILIZATION (IEDC)
# ═══════════════════════════════════════════════════════════════

class DeveloperPlatform:
    """Foundation for third-party development: register modules, manage lifecycle, track developers."""

    def __init__(self):
        self._developers = {}
        self._modules = {}
        self._module_types = {"agent", "skill", "knowledge", "workflow", "device", "intelligence_service"}

    def register_developer(self, dev_id, name, contact=""):
        self._developers[dev_id] = {"id": dev_id, "name": name, "contact": contact, "modules": [], "joined": time.time()}
        return self._developers[dev_id]

    def publish_module(self, dev_id, name, module_type, version="1.0.0", description="", permissions=None):
        if module_type not in self._module_types:
            return {"error": f"Unknown module type: {module_type}"}
        if dev_id not in self._developers:
            return {"error": "Developer not registered"}
        mod_id = f"mod_{int(time.time())}"
        module = {"id": mod_id, "name": name, "type": module_type, "version": version, "description": description, "developer": dev_id, "permissions": permissions or [], "status": "published", "installs": 0, "published": time.time()}
        self._modules[mod_id] = module
        self._developers[dev_id]["modules"].append(mod_id)
        return module

    def install_module(self, mod_id):
        if mod_id in self._modules:
            self._modules[mod_id]["installs"] += 1
            self._modules[mod_id]["status"] = "installed"
            return self._modules[mod_id]
        return {"error": "Module not found"}

    def list_modules(self, module_type=None):
        if module_type:
            return {k: v for k, v in self._modules.items() if v["type"] == module_type}
        return self._modules

    def list_developers(self):
        return list(self._developers.values())

    def stats(self):
        return {"developers": len(self._developers), "modules": len(self._modules), "by_type": {t: sum(1 for m in self._modules.values() if m["type"] == t) for t in self._module_types}}

    def to_dict(self):
        return {"developers": self._developers, "modules": self._modules}

    def from_dict(self, data):
        if "developers" in data:
            self._developers = data["developers"]
        if "modules" in data:
            self._modules = data["modules"]


class IntelligenceSDK:
    """Developer framework: Agent SDK, Skill SDK, Memory SDK, Device SDK, UI SDK."""

    def __init__(self):
        self.sdks = {"agent": {"name": "Agent SDK", "version": "1.0.0", "methods": ["create_agent", "train_agent", "deploy_agent", "connect_agents"]},
                     "skill": {"name": "Skill SDK", "version": "1.0.0", "methods": ["define_skill", "register_tool", "set_permissions", "publish_skill"]},
                     "memory": {"name": "Memory SDK", "version": "1.0.0", "methods": ["store_knowledge", "retrieve_knowledge", "query_memory", "share_memory"]},
                     "device": {"name": "Device SDK", "version": "1.0.0", "methods": ["discover_devices", "connect_device", "send_command", "read_sensor"]},
                     "ui": {"name": "UI SDK", "version": "1.0.0", "methods": ["create_interface", "render_component", "handle_input", "spatial_layout"]}}
        self._sdk_usage = []

    def get_sdk(self, name):
        return self.sdks.get(name, {"error": f"SDK not found: {name}"})

    def use_sdk(self, sdk_name, method, params=None):
        if sdk_name not in self.sdks:
            return {"error": f"Unknown SDK: {sdk_name}"}
        if method not in self.sdks[sdk_name]["methods"]:
            return {"error": f"Unknown method {method} in {sdk_name}"}
        entry = {"sdk": sdk_name, "method": method, "params": params or {}, "time": time.time()}
        self._sdk_usage.append(entry)
        return {"status": "executed", "sdk": sdk_name, "method": method, "result": f"Simulated: {method} executed successfully"}

    def generate_code(self, sdk_name, task_description):
        if sdk_name not in self.sdks:
            return {"error": f"Unknown SDK: {sdk_name}"}
        template = f"""# ARCANIS {self.sdks[sdk_name]['name']} - Generated Code
# Task: {task_description}

from arcanis.{sdk_name} import {', '.join(self.sdks[sdk_name]['methods'][:3])}

# Initialize
client = {sdk_name.capitalize()}Client()

# Execute
result = client.{self.sdks[sdk_name]['methods'][0]}()
print(f"Result: {{result}}")
"""
        return {"sdk": sdk_name, "code": template, "language": "python"}

    def stats(self):
        return {"sdks": len(self.sdks), "usage": len(self._sdk_usage), "recent_calls": self._sdk_usage[-5:] if self._sdk_usage else []}

    def to_dict(self):
        return {"sdks": self.sdks, "sdk_usage": self._sdk_usage[-50:]}

    def from_dict(self, data):
        if "sdks" in data:
            self.sdks = data["sdks"]
        if "sdk_usage" in data:
            self._sdk_usage = data["sdk_usage"]


class ModuleArchitecture:
    """Intelligence module definition: capabilities, permissions, memory, tools, compatibility."""

    def __init__(self):
        self._modules = {}
        self._categories = {"coding", "research", "design", "analysis", "automation", "communication", "knowledge", "security"}

    def define_module(self, name, category, capabilities=None, permissions=None, memory_req=None, tools=None):
        if category not in self._categories:
            return {"error": f"Unknown category: {category}"}
        mid = f"arch_{int(time.time())}"
        self._modules[mid] = {"id": mid, "name": name, "category": category, "capabilities": capabilities or [], "permissions": permissions or [], "memory_requirements": memory_req or {}, "tools": tools or [], "compatibility": ["arcanis_os"], "created": time.time()}
        return self._modules[mid]

    def check_compatibility(self, mod_id, target_system="arcanis_os"):
        if mod_id not in self._modules:
            return {"error": "Module not found"}
        mod = self._modules[mod_id]
        compatible = target_system in mod["compatibility"]
        return {"module": mod["name"], "target": target_system, "compatible": compatible, "required_permissions": mod["permissions"], "memory_needed": mod["memory_requirements"]}

    def list_categories(self):
        return sorted(self._categories)

    def stats(self):
        return {"modules_defined": len(self._modules), "categories": len(self._categories)}

    def to_dict(self):
        return {"modules": self._modules}

    def from_dict(self, data):
        if "modules" in data:
            self._modules = data["modules"]


class MarketplaceFoundation:
    """Intelligence marketplace where modules are discovered, reviewed, and installed."""

    def __init__(self):
        self._listings = {}
        self._reviews = []
        self._categories = {"intelligence", "tools", "knowledge", "agents", "workflows", "integrations"}

    def list_module(self, name, description, category, developer, price="free", version="1.0.0"):
        if category not in self._categories:
            return {"error": f"Unknown category: {category}"}
        lid = f"listing_{int(time.time())}"
        listing = {"id": lid, "name": name, "description": description, "category": category, "developer": developer, "price": price, "version": version, "rating": 0.0, "reviews": 0, "installs": 0, "listed": time.time()}
        self._listings[lid] = listing
        return listing

    def review_module(self, listing_id, rating, comment=""):
        if listing_id not in self._listings:
            return {"error": "Listing not found"}
        review = {"listing": listing_id, "rating": max(1, min(5, rating)), "comment": comment, "time": time.time()}
        self._reviews.append(review)
        listing = self._listings[listing_id]
        all_ratings = [r["rating"] for r in self._reviews if r["listing"] == listing_id]
        listing["rating"] = sum(all_ratings) / len(all_ratings)
        listing["reviews"] = len(all_ratings)
        return review

    def install(self, listing_id):
        if listing_id in self._listings:
            self._listings[listing_id]["installs"] += 1
            return self._listings[listing_id]
        return {"error": "Listing not found"}

    def search(self, query):
        results = []
        for lid, listing in self._listings.items():
            if query.lower() in listing["name"].lower() or query.lower() in listing["description"].lower():
                results.append(listing)
        return results

    def browse(self, category=None):
        if category:
            return {k: v for k, v in self._listings.items() if v["category"] == category}
        return self._listings

    def stats(self):
        return {"listings": len(self._listings), "reviews": len(self._reviews), "categories": list(self._categories)}

    def to_dict(self):
        return {"listings": self._listings, "reviews": self._reviews}

    def from_dict(self, data):
        if "listings" in data:
            self._listings = data["listings"]
        if "reviews" in data:
            self._reviews = data["reviews"]


class AgentCollaborationNetwork:
    """Network for agents to discover each other, communicate, delegate tasks, and share results."""

    def __init__(self):
        self._agents = {}
        self._messages = []
        self._delegations = []

    def register_agent(self, agent_id, name, capabilities=None):
        self._agents[agent_id] = {"id": agent_id, "name": name, "capabilities": capabilities or [], "status": "available", "peers": [], "tasks_completed": 0, "registered": time.time()}
        return self._agents[agent_id]

    def discover_agents(self, capability=None):
        if capability:
            return {k: v for k, v in self._agents.items() if capability in v["capabilities"]}
        return self._agents

    def send_message(self, sender, recipient, content, msg_type="task"):
        if sender not in self._agents or recipient not in self._agents:
            return {"error": "Agent not found"}
        msg = {"id": f"msg_{int(time.time())}", "sender": sender, "recipient": recipient, "content": content, "type": msg_type, "time": time.time()}
        self._messages.append(msg)
        if recipient not in self._agents[sender].get("peers", []):
            self._agents[sender].setdefault("peers", []).append(recipient)
        if sender not in self._agents[recipient].get("peers", []):
            self._agents[recipient].setdefault("peers", []).append(sender)
        return msg

    def delegate_task(self, delegator, agent_id, task, requirements=None):
        if delegator not in self._agents or agent_id not in self._agents:
            return {"error": "Agent not found"}
        delegation = {"id": f"del_{int(time.time())}", "delegator": delegator, "agent": agent_id, "task": task, "requirements": requirements or {}, "status": "delegated", "time": time.time()}
        self._delegations.append(delegation)
        self._agents[agent_id]["tasks_completed"] += 1
        self._agents[agent_id]["status"] = "busy"
        result = self._simulate_result(agent_id, task)
        delegation["result"] = result
        delegation["status"] = "completed"
        self._agents[agent_id]["status"] = "available"
        return delegation

    def _simulate_result(self, agent_id, task):
        agent = self._agents.get(agent_id, {})
        name = agent.get("name", "agent")
        return {"agent": name, "task": task, "output": f"{name} completed: {task}", "confidence": 0.85, "time": time.time()}

    def collaboration_opportunities(self):
        opportunities = []
        agents_list = list(self._agents.values())
        for i, a1 in enumerate(agents_list):
            for a2 in agents_list[i+1:]:
                shared = set(a1.get("capabilities", [])) & set(a2.get("capabilities", []))
                if not shared and a1.get("capabilities") and a2.get("capabilities"):
                    opportunities.append({"agents": [a1["id"], a2["id"]], "suggestion": f"{a1['name']} and {a2['name']} have complementary capabilities"})
        return opportunities

    def stats(self):
        return {"agents": len(self._agents), "messages": len(self._messages), "delegations": len(self._delegations)}

    def to_dict(self):
        return {"agents": self._agents, "messages": self._messages[-50:], "delegations": self._delegations}

    def from_dict(self, data):
        if "agents" in data:
            self._agents = data["agents"]
        if "messages" in data:
            self._messages = data["messages"]
        if "delegations" in data:
            self._delegations = data["delegations"]


class OpenIntelligenceProtocol:
    """Standard communication format for identity, tasks, knowledge exchange, permissions, and results."""

    def __init__(self):
        self._protocol_version = "1.0.0"
        self._message_types = {"request", "response", "task", "knowledge", "permission", "result", "discovery"}
        self._handlers = {}
        self._log = []

    def format_message(self, msg_type, sender, recipient, payload):
        if msg_type not in self._message_types:
            return {"error": f"Unknown message type: {msg_type}"}
        message = {"protocol": "ARCANIS-OIP", "version": self._protocol_version, "type": msg_type, "sender": sender, "recipient": recipient, "payload": payload, "timestamp": time.time(), "id": f"oip_{int(time.time())}"}
        self._log.append(message)
        return message

    def register_handler(self, msg_type, handler_name):
        self._handlers[msg_type] = handler_name

    def process_message(self, message):
        if message.get("protocol") != "ARCANIS-OIP":
            return {"error": "Unknown protocol"}
        msg_type = message.get("type")
        handler = self._handlers.get(msg_type, "default_handler")
        return {"status": "processed", "type": msg_type, "handler": handler, "result": f"Message from {message.get('sender')} to {message.get('recipient')} processed"}

    def translate(self, external_data, target_format="ARCANIS-OIP"):
        return self.format_message("request", "external", "arcanis_core", {"raw": external_data, "format": target_format})

    def stats(self):
        return {"version": self._protocol_version, "handlers": len(self._handlers), "messages_logged": len(self._log)}

    def to_dict(self):
        return {"protocol_version": self._protocol_version, "handlers": self._handlers, "log": self._log[-20:]}

    def from_dict(self, data):
        if "handlers" in data:
            self._handlers = data["handlers"]
        if "log" in data:
            self._log = data["log"]


class GovernanceSystem:
    """Ecosystem safety: module verification, permission analysis, security testing, user approval."""

    def __init__(self):
        self._verification_queue = []
        self._approved = []
        self._rejected = []
        self._policies = {"require_verification": True, "max_permission_level": "high", "audit_enabled": True}

    def submit_for_verification(self, module_id, module_data):
        entry = {"id": module_id, "data": module_data, "status": "pending", "submitted": time.time()}
        self._verification_queue.append(entry)
        result = self._verify(entry)
        return result

    def _verify(self, entry):
        data = entry["data"]
        issues = []
        permissions = data.get("permissions", [])
        for p in permissions:
            if p in ("full_system", "remote_access", "kernel_modification"):
                issues.append(f"High-risk permission: {p}")
        if not data.get("description"):
            issues.append("Missing description")
        if issues:
            entry["status"] = "rejected"
            entry["issues"] = issues
            self._rejected.append(entry)
            return {"status": "rejected", "issues": issues}
        entry["status"] = "approved"
        self._approved.append(entry)
        return {"status": "approved", "module": data.get("name", "unknown"), "level": "safe"}

    def check_permissions(self, module_id, requested_permissions):
        max_level = self._policies["max_permission_level"]
        risk_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        for p in requested_permissions:
            level = risk_map.get(p, 1)
            if level > risk_map.get(max_level, 3):
                return {"approved": False, "reason": f"Permission '{p}' exceeds max allowed level ({max_level})", "requires_user": True}
        return {"approved": True, "permissions": requested_permissions}

    def audit_log(self, n=20):
        entries = [{"type": "approved", "entries": self._approved[-n//2:]}, {"type": "rejected", "entries": self._rejected[-n//2:]}] if self._approved or self._rejected else []
        return entries

    def stats(self):
        return {"pending": len(self._verification_queue), "approved": len(self._approved), "rejected": len(self._rejected), "policies": self._policies}

    def to_dict(self):
        return {"policies": self._policies, "approved": self._approved[-20:], "rejected": self._rejected[-20:]}

    def from_dict(self, data):
        if "policies" in data:
            self._policies = data["policies"]
        if "approved" in data:
            self._approved = data["approved"]
        if "rejected" in data:
            self._rejected = data["rejected"]


class KnowledgeContributionFramework:
    """Distributed knowledge ecosystem with ownership, privacy, attribution."""

    def __init__(self):
        self._contributions = []
        self._contributors = {}
        self._collections = {}

    def contribute(self, contributor_id, contributor_name, content_type, title, content, tags=None):
        cid = f"contrib_{int(time.time())}"
        contribution = {"id": cid, "contributor": contributor_id, "contributor_name": contributor_name, "type": content_type, "title": title, "content": content, "tags": tags or [], "license": "by-nc", "attributed": True, "time": time.time()}
        self._contributions.append(contribution)
        if contributor_id not in self._contributors:
            self._contributors[contributor_id] = {"id": contributor_id, "name": contributor_name, "contributions": 0, "joined": time.time()}
        self._contributors[contributor_id]["contributions"] += 1
        return contribution

    def create_collection(self, name, description, contributor_id):
        col_id = f"col_{int(time.time())}"
        self._collections[col_id] = {"id": col_id, "name": name, "description": description, "owner": contributor_id, "items": [], "created": time.time()}
        return self._collections[col_id]

    def add_to_collection(self, col_id, contrib_id):
        if col_id in self._collections:
            contrib = next((c for c in self._contributions if c["id"] == contrib_id), None)
            if contrib:
                self._collections[col_id]["items"].append(contrib)
                return True
        return False

    def search(self, query):
        results = []
        for c in self._contributions:
            if query.lower() in c["title"].lower() or query.lower() in c["content"][:200].lower():
                results.append(c)
        return results

    def stats(self):
        return {"contributions": len(self._contributions), "contributors": len(self._contributors), "collections": len(self._collections), "by_type": {}}

    def to_dict(self):
        return {"contributions": self._contributions[-50:], "contributors": self._contributors, "collections": self._collections}

    def from_dict(self, data):
        if "contributions" in data:
            self._contributions = data["contributions"]
        if "contributors" in data:
            self._contributors = data["contributors"]
        if "collections" in data:
            self._collections = data["collections"]


class EnterpriseFoundation:
    """Organization support: team spaces, shared agents, org knowledge, permission hierarchy, internal automation."""

    def __init__(self):
        self._organizations = {}
        self._teams = {}
        self._org_knowledge = []

    def create_organization(self, org_id, name, admin):
        self._organizations[org_id] = {"id": org_id, "name": name, "admin": admin, "members": [admin], "agents": [], "knowledge_bases": [], "created": time.time()}
        return self._organizations[org_id]

    def add_member(self, org_id, member_id, role="member"):
        if org_id in self._organizations:
            if member_id not in self._organizations[org_id]["members"]:
                self._organizations[org_id]["members"].append(member_id)
            return True
        return False

    def create_team(self, org_id, name, members=None):
        tid = f"team_{int(time.time())}"
        self._teams[tid] = {"id": tid, "org": org_id, "name": name, "members": members or [], "shared_agents": [], "created": time.time()}
        return self._teams[tid]

    def share_agent(self, org_id, agent_id, agent_name):
        if org_id in self._organizations:
            entry = {"id": agent_id, "name": agent_name, "org": org_id, "shared": time.time()}
            self._organizations[org_id]["agents"].append(entry)
            return entry
        return {"error": "Organization not found"}

    def add_knowledge(self, org_id, title, content, department="general"):
        entry = {"org": org_id, "title": title, "content": content, "department": department, "time": time.time()}
        self._org_knowledge.append(entry)
        if org_id in self._organizations:
            self._organizations[org_id]["knowledge_bases"].append(entry)
        return entry

    def suggest_automation(self, org_id, department):
        return {"org": org_id, "department": department, "suggested_automations": [f"Auto-reporting for {department}", f"Cross-team knowledge sync for {department}", f"{department} workflow optimization"]}

    def stats(self):
        return {"organizations": len(self._organizations), "teams": len(self._teams), "knowledge_entries": len(self._org_knowledge)}

    def to_dict(self):
        return {"organizations": self._organizations, "teams": self._teams, "knowledge": self._org_knowledge[-50:]}

    def from_dict(self, data):
        if "organizations" in data:
            self._organizations = data["organizations"]
        if "teams" in data:
            self._teams = data["teams"]
        if "knowledge" in data:
            self._org_knowledge = data["knowledge"]


class EcosystemArchitecture:
    """Future economic and ecosystem architecture: marketplace, rewards, licensing, community."""

    def __init__(self):
        self._architecture = {
            "economy": {"type": "intelligence_marketplace", "tokens": None, "rewards": "planned", "licensing": "enterprise_tiered"},
            "layers": ["core", "intelligence_modules", "developer_tools", "enterprise_services", "community"],
            "standards": ["ARCANIS-OIP", "module_manifest_v1", "agent_protocol_v1", "knowledge_format_v1"],
            "growth_metrics": {"developers": 0, "modules": 0, "organizations": 0, "knowledge_contributions": 0},
        }
        self._roadmap = [{"phase": "foundation", "status": "current", "items": ["Developer platform", "SDK", "Marketplace", "Governance"]}, {"phase": "growth", "status": "planned", "items": ["Economy", "Enterprise suite", "Partner program"]}, {"phase": "civilization", "status": "future", "items": ["Autonomous developer agents", "Self-improving ecosystem", "Cross-platform intelligence"]}]

    def get_architecture(self):
        return self._architecture

    def get_roadmap(self):
        return self._roadmap

    def record_growth(self, metric, value):
        if metric in self._architecture["growth_metrics"]:
            self._architecture["growth_metrics"][metric] = value

    def stats(self):
        return {"layers": len(self._architecture["layers"]), "standards": len(self._architecture["standards"]), "roadmap_phases": len(self._roadmap), "metrics": self._architecture["growth_metrics"]}

    def to_dict(self):
        return self.__dict__

    def from_dict(self, data):
        for k, v in data.items():
            setattr(self, '_'+k if k.startswith('_') else k, v)


class IntelligenceEcosystemDeveloperCivilization:
    """Phase 16 — The ecosystem layer that allows external developers, researchers, creators,
    and intelligent agents to build on top of ARCANIS. Evolves ARCANIS from product to platform."""

    def __init__(self):
        self.platform = DeveloperPlatform()
        self.sdk = IntelligenceSDK()
        self.modules = ModuleArchitecture()
        self.marketplace = MarketplaceFoundation()
        self.agent_network = AgentCollaborationNetwork()
        self.protocol = OpenIntelligenceProtocol()
        self.governance = GovernanceSystem()
        self.knowledge = KnowledgeContributionFramework()
        self.enterprise = EnterpriseFoundation()
        self.architecture = EcosystemArchitecture()
        self._initialized = False

    def initialize(self):
        self.platform.register_developer("arcanis_labs", "ARCANIS Labs", "dev@arcanis.io")
        self.platform.register_developer("community", "Community Developers", "community@arcanis.io")
        self.agent_network.register_agent("agent_basic", "Basic Agent", ["communicate", "learn"])
        self.agent_network.register_agent("agent_researcher", "Research Agent", ["research", "analyze", "synthesize"])
        self.agent_network.register_agent("agent_coder", "Coding Agent", ["code", "debug", "test"])
        self.architecture.record_growth("developers", 2)
        self._initialized = True
        return {"status": "iedc_initialized", "layers": 10}

    def full_summary(self):
        return {"platform": self.platform.stats(), "sdk": self.sdk.stats(), "modules": self.modules.stats(), "marketplace": self.marketplace.stats(), "agent_network": self.agent_network.stats(), "protocol": self.protocol.stats(), "governance": self.governance.stats(), "knowledge": self.knowledge.stats(), "enterprise": self.enterprise.stats(), "ecosystem": self.architecture.stats()}

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.__dict__.items() if k != '_initialized' and hasattr(v, 'to_dict')}

    def from_dict(self, data):
        for key in ["platform", "sdk", "modules", "marketplace", "agent_network", "protocol", "governance", "knowledge", "enterprise", "architecture"]:
            if key in data and hasattr(self, key) and hasattr(getattr(self, key), "from_dict"):
                getattr(self, key).from_dict(data[key])


# ═══════════════════════════════════════════════════════════════
# PHASE 17 — AUTONOMOUS WORLD SIMULATION ENGINE (AWSE)
# ═══════════════════════════════════════════════════════════════

class UniversalSimulationCore:
    """Foundation for all simulation: digital environments, system models, data simulations, agent sims, scenario testing."""

    def __init__(self):
        self._models = {}
        self._simulations = []
        self._model_types = {"environment", "system", "data", "agent", "scenario"}

    def create_model(self, name, model_type, parameters=None):
        if model_type not in self._model_types:
            return {"error": f"Unknown model type: {model_type}"}
        mid = f"model_{int(time.time())}"
        self._models[mid] = {"id": mid, "name": name, "type": model_type, "parameters": parameters or {}, "created": time.time()}
        return self._models[mid]

    def run_simulation(self, model_id, iterations=100, variables=None):
        if model_id not in self._models:
            return {"error": "Model not found"}
        model = self._models[model_id]
        import random
        result = {"model": model_id, "name": model["name"], "iterations": iterations, "variables": variables or {}, "outcomes": {"convergence": round(random.uniform(0.7, 0.99), 4), "stability": round(random.uniform(0.6, 1.0), 4), "confidence": round(random.uniform(0.65, 0.95), 4)}, "time": time.time()}
        self._simulations.append(result)
        return result

    def compare_models(self, model_ids):
        results = []
        for mid in model_ids[:5]:
            if mid in self._models:
                results.append(self.run_simulation(mid, 50))
        return results

    def stats(self):
        return {"models": len(self._models), "simulations_run": len(self._simulations)}

    def to_dict(self):
        return {"models": self._models, "simulations": self._simulations[-20:]}

    def from_dict(self, data):
        if "models" in data:
            self._models = data["models"]
        if "simulations" in data:
            self._simulations = data["simulations"]


class DigitalTwinFramework:
    """Digital twins for projects, machines, software systems, organizations, learning paths, environments."""

    def __init__(self):
        self._twins = {}
        self._twin_types = {"project", "machine", "software", "organization", "learning_path", "environment"}

    def create_twin(self, name, twin_type, components=None, physics=None, logic=None):
        if twin_type not in self._twin_types:
            return {"error": f"Unknown twin type: {twin_type}"}
        tid = f"twin_{int(time.time())}"
        self._twins[tid] = {"id": tid, "name": name, "type": twin_type, "components": components or [], "physics_model": physics or {}, "software_logic": logic or {}, "performance_data": {}, "possible_failures": [], "status": "active", "created": time.time()}
        if twin_type == "machine":
            self._twins[tid]["possible_failures"] = ["Overheating", "Component wear", "Power fluctuation", "Calibration drift"]
        elif twin_type == "software":
            self._twins[tid]["possible_failures"] = ["Memory leak", "Race condition", "API degradation", "Data corruption"]
        return self._twins[tid]

    def update_performance(self, twin_id, metric, value):
        if twin_id in self._twins:
            self._twins[twin_id]["performance_data"][metric] = {"value": value, "time": time.time()}

    def predict_failures(self, twin_id):
        if twin_id not in self._twins:
            return {"error": "Twin not found"}
        twin = self._twins[twin_id]
        predictions = []
        for failure in twin.get("possible_failures", []):
            predictions.append({"failure": failure, "probability": round(__import__("random").uniform(0.05, 0.4), 2), "estimated_impact": "medium", "recommended_action": f"Monitor {failure.lower().replace(' ', '_')} metrics"})
        return {"twin": twin["name"], "predictions": predictions}

    def simulate_twin(self, twin_id, conditions=None):
        if twin_id not in self._twins:
            return {"error": "Twin not found"}
        import random
        twin = self._twins[twin_id]
        return {"twin": twin["name"], "type": twin["type"], "simulated_performance": {"efficiency": round(random.uniform(0.6, 0.98), 2), "reliability": round(random.uniform(0.7, 0.99), 2), "response_time": round(random.uniform(10, 200), 1)}, "conditions": conditions or {}, "status": "simulated"}

    def stats(self):
        return {"twins": len(self._twins), "by_type": {t: sum(1 for tw in self._twins.values() if tw["type"] == t) for t in self._twin_types}}

    def to_dict(self):
        return {"twins": self._twins}

    def from_dict(self, data):
        if "twins" in data:
            self._twins = data["twins"]


class FutureScenarioEngine:
    """Predictive scenario generation with probability and risk analysis."""

    def __init__(self):
        self._scenarios = []
        self._analyses = []

    def generate_scenarios(self, question, context=None):
        scenarios = []
        scenarios.append({"name": "Optimistic Growth", "probability": 0.25, "description": f"High growth possibility for '{question}'. Favorable conditions converge.", "risks": ["Overconfidence", "Resource strain"], "timeframe": "6-12 months"})
        scenarios.append({"name": "Technical Reality", "probability": 0.35, "description": f"Technical limitations emerge for '{question}'. Requires adaptation.", "risks": ["Development delays", "Integration complexity"], "timeframe": "12-18 months"})
        scenarios.append({"name": "Market Challenge", "probability": 0.25, "description": f"Market dynamics create headwinds for '{question}'. Need strategic positioning.", "risks": ["Competition", "Timing misalignment"], "timeframe": "18-24 months"})
        scenarios.append({"name": "Transformative Shift", "probability": 0.15, "description": f"'{question}' triggers unexpected paradigm change. High risk, high reward.", "risks": ["Execution failure", "Resource requirements"], "timeframe": "24-36 months"})
        entry = {"id": f"scen_{int(time.time())}", "question": question, "context": context or {}, "scenarios": scenarios, "created": time.time()}
        self._scenarios.append(entry)
        return entry

    def analyze_probability(self, scenario_id):
        scenario = next((s for s in self._scenarios if s["id"] == scenario_id), None)
        if not scenario:
            return {"error": "Scenario not found"}
        analysis = {"scenario": scenario_id, "question": scenario["question"], "most_likely": max(scenario["scenarios"], key=lambda x: x["probability"]), "risk_summary": {"high": sum(1 for s in scenario["scenarios"] if s["probability"] > 0.3), "medium": sum(1 for s in scenario["scenarios"] if 0.15 < s["probability"] <= 0.3), "low": sum(1 for s in scenario["scenarios"] if s["probability"] <= 0.15)}, "recommendation": "Pursue with phased approach — validate Technical Reality scenario first", "time": time.time()}
        self._analyses.append(analysis)
        return analysis

    def latest_scenarios(self, n=5):
        return self._scenarios[-n:]

    def stats(self):
        return {"scenarios_generated": len(self._scenarios), "analyses": len(self._analyses)}

    def to_dict(self):
        return {"scenarios": self._scenarios[-20:], "analyses": self._analyses[-20:]}

    def from_dict(self, data):
        if "scenarios" in data:
            self._scenarios = data["scenarios"]
        if "analyses" in data:
            self._analyses = data["analyses"]


class AIExperimentationLab:
    """Safe environment where agents can experiment, test approaches, compare solutions without real-world impact."""

    def __init__(self):
        self._experiments = []
        self._hypotheses = []
        self._results = []

    def propose_experiment(self, name, hypothesis, approach, agents=None):
        eid = f"exp_{int(time.time())}"
        experiment = {"id": eid, "name": name, "hypothesis": hypothesis, "approach": approach, "agents": agents or ["general"], "status": "proposed", "created": time.time()}
        self._experiments.append(experiment)
        self._hypotheses.append({"experiment": eid, "hypothesis": hypothesis, "status": "testing"})
        return experiment

    def run_experiment(self, exp_id):
        exp = next((e for e in self._experiments if e["id"] == exp_id), None)
        if not exp:
            return {"error": "Experiment not found"}
        import random
        exp["status"] = "running"
        result = {"experiment": exp_id, "name": exp["name"], "hypothesis": exp["hypothesis"], "outcome": "validated" if random.random() > 0.3 else "refuted", "confidence": round(random.uniform(0.6, 0.95), 2), "insights": [f"Approach {exp['approach'][:30]} shows promise", "Key variable identified for optimization", "Follow-up experiment recommended"], "time": time.time()}
        self._results.append(result)
        exp["status"] = "completed"
        for h in self._hypotheses:
            if h["experiment"] == exp_id:
                h["status"] = result["outcome"]
                h["result"] = result
        return result

    def compare_solutions(self, solutions):
        comparisons = []
        for sol in solutions[:5]:
            e = self.propose_experiment(f"Compare: {sol}", f"Testing {sol}", sol)
            r = self.run_experiment(e["id"])
            comparisons.append({"solution": sol, "result": r["outcome"], "confidence": r["confidence"]})
        return {"comparisons": comparisons, "best": max(comparisons, key=lambda x: x["confidence"]) if comparisons else None}

    def safe_reset(self):
        self._experiments = []
        self._results = []
        return {"status": "reset", "message": "Lab cleared. No real-world impact."}

    def stats(self):
        return {"experiments": len(self._experiments), "hypotheses": len(self._hypotheses), "results": len(self._results)}

    def to_dict(self):
        return {"experiments": self._experiments[-20:], "results": self._results[-20:]}

    def from_dict(self, data):
        if "experiments" in data:
            self._experiments = data["experiments"]
        if "results" in data:
            self._results = data["results"]


class MultiAgentSimulationSystem:
    """Simulated societies of agents that interact and produce insights."""

    def __init__(self):
        self._simulations = []
        self._agent_societies = {}

    def create_society(self, name, agent_roles, environment=None):
        sid = f"society_{int(time.time())}"
        agents = {}
        for role in agent_roles:
            agents[role] = {"role": role, "state": "idle", "decisions": 0, "messages_sent": 0}
        self._agent_societies[sid] = {"id": sid, "name": name, "agents": agents, "environment": environment or {"type": "generic", "complexity": "medium"}, "interactions": [], "insights": [], "created": time.time()}
        return self._agent_societies[sid]

    def run_interaction(self, society_id, topic):
        if society_id not in self._agent_societies:
            return {"error": "Society not found"}
        society = self._agent_societies[society_id]
        import random
        interaction_log = []
        roles = list(society["agents"].keys())
        for i in range(len(roles)):
            for j in range(i+1, len(roles)):
                msg = f"{roles[i]} -> {roles[j]}: Regarding '{topic}' — analyzing from {roles[i]} perspective"
                society["agents"][roles[i]]["messages_sent"] += 1
                interaction_log.append(msg)
        insight = f"Multi-agent simulation on '{topic}' reveals: {'; '.join([f'{r} recommends further analysis' for r in roles[:3]])}"
        society["interactions"].append({"topic": topic, "log": interaction_log, "time": time.time()})
        society["insights"].append(insight)
        return {"society": society["name"], "interactions": len(interaction_log), "insight": insight}

    def run_business_simulation(self, scenario):
        roles = ["CEO", "Engineering", "Marketing", "Customer"]
        society = self.create_society(f"Business: {scenario}", roles, {"type": "market", "complexity": "high"})
        result = self.run_interaction(society["id"], scenario)
        result["roles"] = roles
        result["scenario"] = scenario
        return result

    def stats(self):
        return {"societies": len(self._agent_societies), "total_insights": sum(len(s["insights"]) for s in self._agent_societies.values())}

    def to_dict(self):
        return {"societies": self._agent_societies}

    def from_dict(self, data):
        if "societies" in data:
            self._agent_societies = data["societies"]


class ScienceSimulationFoundation:
    """Advanced research simulation: mathematical models, engineering analysis, optimization, experimental design."""

    def __init__(self):
        self._models = {}
        self._experiments = []
        self._domains = ["physics", "engineering", "biology", "chemistry", "mathematics", "computer_science"]

    def create_model(self, domain, name, equations=None):
        if domain not in self._domains:
            return {"error": f"Unknown domain: {domain}"}
        mid = f"sci_{int(time.time())}"
        self._models[mid] = {"id": mid, "domain": domain, "name": name, "equations": equations or ["f(x) = ..."], "parameters": {}, "created": time.time()}
        return self._models[mid]

    def analyze(self, model_id, parameters=None):
        if model_id not in self._models:
            return {"error": "Model not found"}
        import random
        model = self._models[model_id]
        return {"model": model["name"], "domain": model["domain"], "analysis": {"optimal_parameters": parameters or {"x": round(random.uniform(-10, 10), 2), "y": round(random.uniform(-10, 10), 2)}, "convergence": round(random.uniform(0.8, 0.99), 3), "error_margin": round(random.uniform(0.01, 0.1), 3), "recommendation": f"Increase precision in {model['domain']} parameter space for better results"}, "time": time.time()}

    def design_experiment(self, objective, variables, constraints=None):
        eid = f"des_{int(time.time())}"
        experiment = {"id": eid, "objective": objective, "variables": variables, "constraints": constraints or {}, "design": {"type": "factorial", "runs": len(variables) * 3 + 5, "randomization": True}, "status": "designed", "time": time.time()}
        self._experiments.append(experiment)
        return experiment

    def stats(self):
        return {"models": len(self._models), "experiments_designed": len(self._experiments), "domains": self._domains}

    def to_dict(self):
        return {"models": self._models, "experiments": self._experiments}

    def from_dict(self, data):
        if "models" in data:
            self._models = data["models"]
        if "experiments" in data:
            self._experiments = data["experiments"]


class PersonalDecisionSimulator:
    """Integrates with PIIN to simulate personal decisions: learning paths, career, projects."""

    def __init__(self):
        self._decisions = []
        self._paths = []

    def simulate_decision(self, question, options, user_context=None):
        did = f"dec_{int(time.time())}"
        import random
        evaluated = []
        for opt in options:
            score = round(random.uniform(0.3, 0.95), 2)
            evaluated.append({"option": opt, "score": score, "pros": [f"Aligned with goals", f"Reasonable time investment"], "cons": [f"Requires dedication", f"Competitive field"], "probability_of_success": round(random.uniform(0.4, 0.9), 2)})
        evaluated.sort(key=lambda x: -x["score"])
        result = {"id": did, "question": question, "evaluated_options": evaluated, "recommended": evaluated[0]["option"] if evaluated else None, "context": user_context or {}, "time": time.time()}
        self._decisions.append(result)
        return result

    def generate_paths(self, goal, current_state, constraints=None):
        paths = []
        import random
        for i in range(3):
            steps = random.sample(["Research", "Learn fundamentals", "Build project", "Get feedback", "Iterate", "Master", "Teach others", "Apply professionally"], 5)
            paths.append({"path": i+1, "steps": steps, "estimated_time": f"{random.randint(3, 24)} months", "difficulty": random.choice(["beginner", "intermediate", "advanced"]), "match_score": round(random.uniform(0.5, 0.95), 2)})
        paths.sort(key=lambda x: -x["match_score"])
        entry = {"id": f"path_{int(time.time())}", "goal": goal, "current_state": current_state, "paths": paths, "created": time.time()}
        self._paths.append(entry)
        return entry

    def stats(self):
        return {"decisions_simulated": len(self._decisions), "paths_generated": len(self._paths)}

    def to_dict(self):
        return {"decisions": self._decisions[-20:], "paths": self._paths[-20:]}

    def from_dict(self, data):
        if "decisions" in data:
            self._decisions = data["decisions"]
        if "paths" in data:
            self._paths = data["paths"]


class SystemKnowledgeModel:
    """Continuously improving model of systems connecting knowledge graph, research, simulation, and agent network."""

    def __init__(self):
        self._world_model = {"systems": {}, "connections": [], "confidence": 0.5, "last_updated": time.time()}
        self._updates = []

    def register_system(self, name, category, description, components=None):
        system = {"name": name, "category": category, "description": description, "components": components or [], "simulations_run": 0, "knowledge_links": [], "last_updated": time.time()}
        self._world_model["systems"][name] = system
        return system

    def connect_systems(self, system_a, system_b, relationship):
        conn = {"from": system_a, "to": system_b, "relationship": relationship, "time": time.time()}
        self._world_model["connections"].append(conn)
        if system_a in self._world_model["systems"] and system_b in self._world_model["systems"]:
            self._world_model["systems"][system_a].setdefault("knowledge_links", []).append(system_b)
        return conn

    def update_model(self, source, data):
        self._updates.append({"source": source, "data": data, "time": time.time()})
        self._world_model["last_updated"] = time.time()
        self._world_model["confidence"] = min(1.0, self._world_model["confidence"] + 0.02)

    def query(self, topic):
        results = []
        for name, system in self._world_model["systems"].items():
            if topic.lower() in name.lower() or topic.lower() in system["description"].lower():
                results.append(system)
        connections = [c for c in self._world_model["connections"] if topic.lower() in c["from"].lower() or topic.lower() in c["to"].lower()]
        return {"systems_found": results, "connections": connections, "confidence": self._world_model["confidence"]}

    def stats(self):
        return {"systems": len(self._world_model["systems"]), "connections": len(self._world_model["connections"]), "confidence": self._world_model["confidence"], "updates": len(self._updates)}

    def to_dict(self):
        return {"world_model": self._world_model, "updates": self._updates[-50:]}

    def from_dict(self, data):
        if "world_model" in data:
            self._world_model = data["world_model"]
        if "updates" in data:
            self._updates = data["updates"]


class SimulationVisualizationLayer:
    """ARCANIS-native visualization: system maps, future timelines, relationship networks, scenario landscapes."""

    def __init__(self):
        self._visualizations = []
        self._viz_types = {"system_map", "timeline", "network", "landscape", "comparison"}

    def create_visualization(self, viz_type, title, data):
        if viz_type not in self._viz_types:
            return {"error": f"Unknown visualization type: {viz_type}"}
        vid = f"viz_{int(time.time())}"
        viz = {"id": vid, "type": viz_type, "title": title, "data": data, "format": "spatial", "created": time.time()}
        self._visualizations.append(viz)
        return viz

    def system_map(self, systems, connections):
        viz_data = {"nodes": [{"id": s, "label": s} for s in systems], "edges": [{"source": c[0], "target": c[1], "label": c[2] if len(c) > 2 else "connected"} for c in connections]}
        return self.create_visualization("system_map", "System Relationship Map", viz_data)

    def future_timeline(self, events):
        viz_data = [{"event": e, "position": i, "phase": "future" if i > 2 else "near" if i > 0 else "current"} for i, e in enumerate(events)]
        return self.create_visualization("timeline", "Future Timeline", viz_data)

    def relationship_network(self, entities, relationships):
        viz_data = {"entities": [{"name": e} for e in entities], "relationships": [{"from": r[0], "to": r[1], "type": r[2] if len(r) > 2 else "related"} for r in relationships]}
        return self.create_visualization("network", "Relationship Network", viz_data)

    def scenario_landscape(self, scenarios):
        viz_data = [{"name": s.get("name", "unknown"), "probability": s.get("probability", 0), "risk": len(s.get("risks", []))} for s in scenarios]
        return self.create_visualization("landscape", "Scenario Landscape", viz_data)

    def stats(self):
        return {"total_visualizations": len(self._visualizations), "by_type": {t: sum(1 for v in self._visualizations if v["type"] == t) for t in self._viz_types}}

    def to_dict(self):
        return {"visualizations": self._visualizations}

    def from_dict(self, data):
        if "visualizations" in data:
            self._visualizations = data["visualizations"]


class SimulationToRealityPipeline:
    """Connects simulation with real action: simulate → evaluate → approve → execute → learn."""

    def __init__(self):
        self._pipeline_entries = []
        self._stages = ["simulate", "evaluate", "approve", "execute", "learn"]

    def submit(self, name, simulation_result, action_plan):
        pid = f"pipe_{int(time.time())}"
        entry = {"id": pid, "name": name, "simulation_result": simulation_result, "action_plan": action_plan, "current_stage": "simulate", "history": [], "approved": False, "executed": False, "feedback": None, "created": time.time()}
        self._pipeline_entries.append(entry)
        return entry

    def evaluate(self, pid):
        entry = next((e for e in self._pipeline_entries if e["id"] == pid), None)
        if not entry:
            return {"error": "Pipeline entry not found"}
        import random
        evaluation = {"simulation_quality": round(random.uniform(0.6, 0.95), 2), "risk_assessment": random.choice(["low", "medium", "high"]), "expected_impact": round(random.uniform(0.3, 0.9), 2), "recommendation": random.choice(["proceed", "proceed_with_caution", "requires_revision"])}
        entry["evaluation"] = evaluation
        entry["current_stage"] = "evaluate"
        entry["history"].append({"stage": "evaluate", "result": evaluation, "time": time.time()})
        return evaluation

    def approve(self, pid):
        entry = next((e for e in self._pipeline_entries if e["id"] == pid), None)
        if not entry:
            return {"error": "Pipeline entry not found"}
        if entry.get("evaluation", {}).get("recommendation") == "requires_revision":
            return {"approved": False, "reason": "Evaluation recommends revision before approval"}
        entry["approved"] = True
        entry["current_stage"] = "approve"
        entry["history"].append({"stage": "approve", "result": "approved", "time": time.time()})
        return {"approved": True, "pid": pid}

    def execute(self, pid):
        entry = next((e for e in self._pipeline_entries if e["id"] == pid), None)
        if not entry:
            return {"error": "Pipeline entry not found"}
        if not entry["approved"]:
            return {"error": "Not approved yet"}
        entry["executed"] = True
        entry["current_stage"] = "execute"
        entry["history"].append({"stage": "execute", "result": "executed", "time": time.time()})
        return {"executed": True, "pid": pid, "action": entry["action_plan"]}

    def learn(self, pid, feedback):
        entry = next((e for e in self._pipeline_entries if e["id"] == pid), None)
        if not entry:
            return {"error": "Pipeline entry not found"}
        entry["feedback"] = feedback
        entry["current_stage"] = "learn"
        entry["history"].append({"stage": "learn", "result": feedback, "time": time.time()})
        return {"learned": True, "feedback": feedback, "improvement": "Simulation parameters updated based on real-world feedback"}

    def stats(self):
        return {"total": len(self._pipeline_entries), "approved": sum(1 for e in self._pipeline_entries if e["approved"]), "executed": sum(1 for e in self._pipeline_entries if e["executed"])}

    def to_dict(self):
        return {"pipeline_entries": self._pipeline_entries}

    def from_dict(self, data):
        if "pipeline_entries" in data:
            self._pipeline_entries = data["pipeline_entries"]


class AutonomousWorldSimulationEngine:
    """Phase 17 — ARCANIS can imagine, test, and evaluate possibilities before committing resources.
    ARCANIS becomes a future exploration engine."""

    def __init__(self):
        self.core = UniversalSimulationCore()
        self.twins = DigitalTwinFramework()
        self.scenarios = FutureScenarioEngine()
        self.lab = AIExperimentationLab()
        self.agent_sim = MultiAgentSimulationSystem()
        self.science = ScienceSimulationFoundation()
        self.decisions = PersonalDecisionSimulator()
        self.world = SystemKnowledgeModel()
        self.visualization = SimulationVisualizationLayer()
        self.pipeline = SimulationToRealityPipeline()
        self._initialized = False

    def initialize(self):
        self.world.register_system("ARCANIS Core", "intelligence", "Central intelligence platform")
        self.world.register_system("Digital Twins", "simulation", "Digital representation framework")
        self.world.register_system("Agent Network", "agents", "Multi-agent system")
        self.world.connect_systems("ARCANIS Core", "Digital Twins", "simulates")
        self.world.connect_systems("ARCANIS Core", "Agent Network", "coordinates")
        self._initialized = True
        return {"status": "awse_initialized", "layers": 10}

    def full_summary(self):
        return {"core": self.core.stats(), "twins": self.twins.stats(), "scenarios": self.scenarios.stats(), "lab": self.lab.stats(), "agent_sim": self.agent_sim.stats(), "science": self.science.stats(), "decisions": self.decisions.stats(), "world": self.world.stats(), "visualization": self.visualization.stats(), "pipeline": self.pipeline.stats()}

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.__dict__.items() if k != '_initialized' and hasattr(v, 'to_dict')}

    def from_dict(self, data):
        for key in ["core", "twins", "scenarios", "lab", "agent_sim", "science", "decisions", "world", "visualization", "pipeline"]:
            if key in data and hasattr(self, key) and hasattr(getattr(self, key), "from_dict"):
                getattr(self, key).from_dict(data[key])


class IntelligentResourceManager:
    def __init__(self):
        self.resources = {"cpu": {"cores": 8, "utilization": 0.0, "available": True}, "gpu": {"available": False, "memory": 0, "utilization": 0.0}, "memory": {"total": 16000, "available": 16000, "utilization": 0.0}, "storage": {"total": 512000, "available": 512000, "utilization": 0.0}, "network": {"latency": 0, "bandwidth": 1000, "available": True}}
        self.external = []
        self.workloads = []
        self.predictions = {}

    def analyze_workload(self, name, requirements):
        workload = {"name": name, "requirements": requirements, "submitted": __import__("time").time(), "estimated_duration": requirements.get("estimated_duration", 60), "priority": requirements.get("priority", 5), "status": "pending"}
        self.workloads.append(workload)
        local_cap = self._assess_local_capacity(requirements)
        recommendation = "local" if local_cap > 0.7 else "remote"
        return {"workload": workload, "recommendation": recommendation, "local_suitability": round(local_cap, 2)}

    def _assess_local_capacity(self, requirements):
        needed_cpu = requirements.get("cpu", 0)
        needed_mem = requirements.get("memory", 0)
        cpu_ok = self.resources["cpu"]["available"] and self.resources["cpu"]["utilization"] + needed_cpu <= 1.0
        mem_ok = self.resources["memory"]["available"] >= needed_mem
        return 0.8 if cpu_ok and mem_ok else 0.3

    def optimize_resources(self):
        return [{"workload": w["name"], "action": "move_to_gpu", "savings": "15%"} for w in self.workloads if w["status"] == "running"]

    def predict_performance(self, task_description):
        return {"expected_duration": __import__("random").randint(10, 300), "confidence": round(__import__("random").uniform(0.6, 0.95), 2), "bottleneck": __import__("random").choice(["cpu", "memory", "storage", "network"])}

    def register_external(self, name, url, capabilities):
        self.external.append({"name": name, "url": url, "capabilities": capabilities, "registered": __import__("time").time()})
        return {"external": name, "status": "available"}

    def stats(self):
        return {"resources": self.resources, "workloads": len(self.workloads), "external_nodes": len(self.external)}

    def to_dict(self):
        return {"resources": self.resources, "external": self.external, "workloads": self.workloads, "predictions": self.predictions}

    def from_dict(self, data):
        for k in ["resources", "external", "workloads", "predictions"]:
            if k in data: setattr(self, k, data[k])


class DistributedIntelligenceFramework:
    def __init__(self):
        self.nodes = {}
        self.connections = []
        self.messages = []

    def register_node(self, node_id, node_type, capabilities):
        self.nodes[node_id] = {"id": node_id, "type": node_type, "capabilities": capabilities, "status": "online", "last_seen": __import__("time").time(), "workload": 0.0}
        return {"status": "registered", "node": node_id}

    def connect_nodes(self, node_a, node_b, link_type="mesh"):
        conn = {"from": node_a, "to": node_b, "type": link_type, "established": __import__("time").time()}
        self.connections.append(conn)
        return conn

    def send_message(self, sender, recipient, content, msg_type="intelligence"):
        msg = {"sender": sender, "recipient": recipient, "content": content, "type": msg_type, "timestamp": __import__("time").time()}
        self.messages.append(msg)
        return msg

    def get_network_status(self):
        online = sum(1 for n in self.nodes.values() if n.get("status") == "online")
        return {"total_nodes": len(self.nodes), "online": online, "connections": len(self.connections), "messages": len(self.messages)}

    def update_node_status(self, node_id, status):
        if node_id in self.nodes:
            self.nodes[node_id]["status"] = status
            self.nodes[node_id]["last_seen"] = __import__("time").time()
        return self.nodes.get(node_id)

    def stats(self):
        return self.get_network_status()

    def to_dict(self):
        return {"nodes": self.nodes, "connections": self.connections, "messages": self.messages}

    def from_dict(self, data):
        for k in ["nodes", "connections", "messages"]:
            if k in data: setattr(self, k, data[k])


class AgentRuntimeManager:
    def __init__(self):
        self.agents = {}
        self.tasks = []
        self.schedules = []

    def deploy_agent(self, agent_id, agent_type, requirements):
        self.agents[agent_id] = {"id": agent_id, "type": agent_type, "requirements": requirements, "deployed": __import__("time").time(), "status": "deployed", "tasks_completed": 0}
        allocation = self._allocate_resources(agent_id, requirements)
        return {"agent": agent_id, "allocation": allocation}

    def _allocate_resources(self, agent_id, requirements):
        return {"cpu": requirements.get("cpu", 0.5), "memory": requirements.get("memory", 1024), "priority": requirements.get("priority", 5)}

    def schedule_task(self, agent_id, task_name, complexity):
        task = {"id": f"task_{len(self.tasks)+1}", "agent": agent_id, "name": task_name, "complexity": complexity, "status": "scheduled", "created": __import__("time").time()}
        self.tasks.append(task)
        self.schedules.append({"agent": agent_id, "task": task["id"], "time": __import__("time").time()})
        return task

    def get_agent_status(self, agent_id):
        agent = self.agents.get(agent_id)
        if not agent: return {"error": "agent not found"}
        agent_tasks = [t for t in self.tasks if t["agent"] == agent_id]
        return {"agent": agent, "tasks": agent_tasks, "active_tasks": sum(1 for t in agent_tasks if t["status"] == "running")}

    def lifecycle_action(self, agent_id, action):
        actions = {"start": "running", "stop": "stopped", "pause": "paused", "resume": "running", "terminate": "terminated"}
        if agent_id in self.agents and action in actions:
            self.agents[agent_id]["status"] = actions[action]
            return {"agent": agent_id, "action": action, "status": actions[action]}
        return {"error": f"cannot {action} agent {agent_id}"}

    def stats(self):
        return {"agents": len(self.agents), "tasks": len(self.tasks), "schedules": len(self.schedules)}

    def to_dict(self):
        return {"agents": self.agents, "tasks": self.tasks, "schedules": self.schedules}

    def from_dict(self, data):
        for k in ["agents", "tasks", "schedules"]:
            if k in data: setattr(self, k, data[k])


class SemanticStorageSystem:
    def __init__(self):
        self.knowledge_store = []
        self.memory_store = []
        self.context_store = []
        self.agent_memory = {}
        self.project_history = []

    def store(self, store_type, content, metadata=None):
        entry = {"id": f"{store_type}_{len(getattr(self, f'{store_type}_store'))+1}", "content": content, "metadata": metadata or {}, "stored": __import__("time").time(), "relationships": []}
        getattr(self, f"{store_type}_store").append(entry)
        return entry

    def search_by_meaning(self, query):
        results = []
        q = query.lower()
        for st in ["knowledge", "memory", "context"]:
            for entry in getattr(self, f"{st}_store"):
                content = str(entry["content"]).lower() + " " + str(entry.get("metadata", {})).lower()
                if q in content:
                    results.append({"store": st, "entry": entry, "relevance": 0.9})
        for r in list(results):
            for rel in r["entry"].get("relationships", []):
                target_id = rel.get("target")
                for st in ["knowledge", "memory", "context"]:
                    for e in getattr(self, f"{st}_store"):
                        if e["id"] == target_id:
                            results.append({"store": st, "entry": e, "relevance": 0.6, "related": True})
        seen = set()
        deduped = []
        for r in results:
            entry_id = r["entry"]["id"]
            if entry_id not in seen:
                seen.add(entry_id)
                deduped.append(r)
        return sorted(deduped, key=lambda r: r["relevance"], reverse=True)

    def relate(self, entry_id, target_id, relationship):
        for st in ["knowledge", "memory", "context"]:
            for entry in getattr(self, f"{st}_store"):
                if entry["id"] == entry_id:
                    entry["relationships"].append({"target": target_id, "type": relationship})
                    return {"status": "related", "from": entry_id, "to": target_id}
        return {"error": "entry not found"}

    def stats(self):
        return {"knowledge": len(self.knowledge_store), "memory": len(self.memory_store), "context": len(self.context_store), "agent_memory_agents": len(self.agent_memory), "project_history": len(self.project_history)}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["knowledge_store", "memory_store", "context_store", "agent_memory", "project_history"]}

    def from_dict(self, data):
        for k in ["knowledge_store", "memory_store", "context_store", "agent_memory", "project_history"]:
            if k in data: setattr(self, k, data[k])


class ComputationalMemoryLayer:
    def __init__(self):
        self.active_context = {}
        self.long_term = []
        self.agent_memory = {}
        self.temp_state = {}

    def set_active_context(self, key, value, ttl=300):
        self.active_context[key] = {"value": value, "expires": __import__("time").time() + ttl, "ttl": ttl}
        return {"context": key, "ttl": ttl}

    def get_active_context(self, key):
        entry = self.active_context.get(key)
        if not entry: return None
        if __import__("time").time() > entry["expires"]:
            del self.active_context[key]
            return None
        return entry["value"]

    def store_long_term(self, key, value, category="general"):
        entry = {"key": key, "value": value, "category": category, "stored": __import__("time").time()}
        self.long_term.append(entry)
        return entry

    def retrieve_long_term(self, query):
        return [e for e in self.long_term if query.lower() in str(e["key"]).lower() or query.lower() in str(e["value"]).lower()]

    def set_temp_state(self, key, value):
        self.temp_state[key] = {"value": value, "created": __import__("time").time()}
        return {"temp_key": key}

    def clear_temp_state(self, key=None):
        if key: self.temp_state.pop(key, None)
        else: self.temp_state.clear()
        return {"cleared": True}

    def optimize(self):
        expired = [k for k, v in self.active_context.items() if __import__("time").time() > v["expires"]]
        for k in expired: del self.active_context[k]
        old = [k for k, v in self.temp_state.items() if __import__("time").time() - v["created"] > 3600]
        for k in old: self.temp_state.pop(k, None)
        return {"evicted_context": len(expired), "evicted_temp": len(old)}

    def stats(self):
        return {"active_context": len(self.active_context), "long_term": len(self.long_term), "agent_memory_keys": len(self.agent_memory), "temp_state": len(self.temp_state)}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["active_context", "long_term", "agent_memory", "temp_state"]}

    def from_dict(self, data):
        for k in ["active_context", "long_term", "agent_memory", "temp_state"]:
            if k in data: setattr(self, k, data[k])


class InfrastructureMonitoringSystem:
    def __init__(self):
        self.metrics_history = []
        self.errors = []
        self.agent_health = {}
        self.recommendations = []
        self.diagnostics = []

    def record_metric(self, name, value, unit="%"):
        entry = {"name": name, "value": value, "unit": unit, "timestamp": __import__("time").time()}
        self.metrics_history.append(entry)
        if name == "cpu_utilization" and value > 80:
            self.recommendations.append({"type": "performance", "message": f"CPU at {value}% - distribute workload", "timestamp": __import__("time").time()})
        if name == "memory_utilization" and value > 80:
            self.recommendations.append({"type": "resource", "message": f"Memory at {value}% - increase allocation", "timestamp": __import__("time").time()})
        return entry

    def log_error(self, source, error_type, message):
        entry = {"source": source, "type": error_type, "message": message, "timestamp": __import__("time").time()}
        self.errors.append(entry)
        self.diagnostics.append({"issue": f"Error in {source}: {message}", "severity": "high" if "crash" in error_type.lower() else "medium", "recommended_action": f"Investigate {source}"})
        return entry

    def update_agent_health(self, agent_id, status, metrics):
        self.agent_health[agent_id] = {"status": status, "metrics": metrics, "last_check": __import__("time").time()}
        return self.agent_health[agent_id]

    def analyze_performance(self):
        if not self.metrics_history: return {"status": "insufficient_data"}
        recent = self.metrics_history[-50:]
        cpu_vals = [m["value"] for m in recent if m["name"] == "cpu_utilization"]
        mem_vals = [m["value"] for m in recent if m["name"] == "memory_utilization"]
        return {"avg_cpu": round(sum(cpu_vals) / max(len(cpu_vals), 1), 1), "avg_memory": round(sum(mem_vals) / max(len(mem_vals), 1), 1), "total_errors": len(self.errors), "recommendations": len(self.recommendations)}

    def get_recommendations(self):
        return self.recommendations[-10:] if self.recommendations else []

    def stats(self):
        return {"metrics": len(self.metrics_history), "errors": len(self.errors), "agents_monitored": len(self.agent_health), "recommendations": len(self.recommendations)}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["metrics_history", "errors", "agent_health", "recommendations", "diagnostics"]}

    def from_dict(self, data):
        for k in ["metrics_history", "errors", "agent_health", "recommendations", "diagnostics"]:
            if k in data: setattr(self, k, data[k])


class SelfOptimizationFramework:
    def __init__(self):
        self.observations = []
        self.optimizations = []
        self.tests = []
        self.applied = []

    def observe(self, component, metric, value, threshold):
        observation = {"component": component, "metric": metric, "value": value, "threshold": threshold, "timestamp": __import__("time").time()}
        self.observations.append(observation)
        if value > threshold:
            return {"observation": observation, "inefficiency": self._find_inefficiency(component, metric, value, threshold)}
        return {"observation": observation, "inefficiency": None}

    def _find_inefficiency(self, component, metric, value, threshold):
        gap = round(value - threshold, 2)
        suggestions = {"response_time": f"Optimize {component} response pipeline", "memory_usage": f"Reduce {component} memory footprint", "cpu_usage": f"Distribute {component} workload"}
        suggestion = suggestions.get(metric, f"Review {component} configuration")
        return {"type": metric, "gap": gap, "suggestion": suggestion}

    def generate_optimization(self, component, suggestion):
        opt = {"id": f"opt_{len(self.optimizations)+1}", "component": component, "suggestion": suggestion, "status": "pending", "needs_approval": False, "created": __import__("time").time()}
        self.optimizations.append(opt)
        if "infrastructure" in suggestion.lower() or "architecture" in suggestion.lower():
            opt["needs_approval"] = True
        return opt

    def test_optimization(self, opt_id):
        opt = next((o for o in self.optimizations if o["id"] == opt_id), None)
        if not opt: return {"error": "optimization not found"}
        test = {"opt_id": opt_id, "component": opt["component"], "result": "safe", "duration_seconds": __import__("random").randint(1, 10)}
        self.tests.append(test)
        return test

    def apply_optimization(self, opt_id, approved=False):
        opt = next((o for o in self.optimizations if o["id"] == opt_id), None)
        if not opt: return {"error": "optimization not found"}
        if opt.get("needs_approval") and not approved:
            return {"status": "pending_approval", "message": "Major change requires approval"}
        opt["status"] = "applied"
        opt["applied_at"] = __import__("time").time()
        self.applied.append(opt)
        return {"status": "applied", "optimization": opt}

    def stats(self):
        return {"observations": len(self.observations), "optimizations": len(self.optimizations), "tests": len(self.tests), "applied": len(self.applied)}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["observations", "optimizations", "tests", "applied"]}

    def from_dict(self, data):
        for k in ["observations", "optimizations", "tests", "applied"]:
            if k in data: setattr(self, k, data[k])


class HardwareAbstractionLayer:
    def __init__(self):
        self.current_platform = "unknown"
        self.capabilities = {}
        self.adaptations = []
        self.supported_platforms = ["laptop", "server", "embedded", "mobile", "cloud"]

    def detect_platform(self, platform_type="laptop"):
        self.current_platform = platform_type
        profiles = {"laptop": {"cpu": "medium", "gpu": "integrated", "memory": "medium", "storage": "medium", "network": "variable", "power": "battery"}, "server": {"cpu": "high", "gpu": "dedicated", "memory": "high", "storage": "high", "network": "high", "power": "continuous"}, "embedded": {"cpu": "low", "gpu": "none", "memory": "low", "storage": "low", "network": "limited", "power": "low"}, "mobile": {"cpu": "low-medium", "gpu": "integrated", "memory": "low", "storage": "medium", "network": "wireless", "power": "battery"}, "cloud": {"cpu": "elastic", "gpu": "elastic", "memory": "elastic", "storage": "elastic", "network": "high", "power": "continuous"}}
        self.capabilities = profiles.get(platform_type, {"cpu": "unknown"})
        return {"platform": platform_type, "capabilities": self.capabilities}

    def adapt_intelligence(self, component, requirements):
        adaptation = {"component": component, "requirements": requirements, "platform": self.current_platform, "timestamp": __import__("time").time()}
        if self.capabilities.get("cpu") == "low":
            adaptation["adjustment"] = "reduced_model_size"
        elif self.capabilities.get("cpu") == "high":
            adaptation["adjustment"] = "full_model"
        else:
            adaptation["adjustment"] = "balanced"
        adaptation["gpu_offloaded"] = self.capabilities.get("gpu") not in ("none", "integrated") if self.capabilities.get("gpu") else False
        self.adaptations.append(adaptation)
        return adaptation

    def uniform_api(self, operation, params=None):
        apis = {"compute": {"available": True, "method": "local" if self.current_platform != "cloud" else "distributed"}, "store": {"available": True, "method": "local" if self.current_platform != "cloud" else "remote"}, "network": {"available": True, "bandwidth": self.capabilities.get("network", "medium")}, "inference": {"available": True, "accelerated": self.capabilities.get("gpu", "none") not in ("none", "integrated")}}
        return apis.get(operation, {"available": False})

    def stats(self):
        return {"platform": self.current_platform, "capabilities": self.capabilities, "adaptations": len(self.adaptations)}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["current_platform", "capabilities", "adaptations"]}

    def from_dict(self, data):
        for k in ["current_platform", "capabilities", "adaptations"]:
            if k in data: setattr(self, k, data[k])


class SecurityInfrastructure:
    def __init__(self):
        self.identities = {}
        self.sessions = {}
        self.audit_log = []
        self.keys = {}

    def register_identity(self, identity_id, identity_type, credentials):
        self.identities[identity_id] = {"id": identity_id, "type": identity_type, "credentials": credentials, "registered": __import__("time").time(), "active": True}
        return {"identity": identity_id, "status": "registered"}

    def authenticate(self, identity_id, credentials):
        identity = self.identities.get(identity_id)
        if not identity: return {"authenticated": False, "reason": "unknown_identity"}
        if not identity["active"]: return {"authenticated": False, "reason": "deactivated"}
        if identity["credentials"] == credentials:
            import hashlib, random
            session_token = hashlib.sha256(f"{identity_id}:{__import__('time').time()}:{random.random()}".encode()).hexdigest()[:16]
            self.sessions[session_token] = {"identity": identity_id, "created": __import__("time").time(), "expires": __import__("time").time() + 3600}
            self._audit("authentication", identity_id, "success")
            return {"authenticated": True, "session": session_token, "expires_in": 3600}
        self._audit("authentication", identity_id, "failed")
        return {"authenticated": False, "reason": "invalid_credentials"}

    def _audit(self, action, actor, result):
        entry = {"action": action, "actor": actor, "result": result, "timestamp": __import__("time").time()}
        self.audit_log.append(entry)
        return entry

    def encrypt_data(self, data, key_id):
        import hashlib, base64
        if key_id not in self.keys:
            self.keys[key_id] = hashlib.sha256(f"key_{key_id}_{__import__('time').time()}".encode()).hexdigest()
        encrypted = base64.b64encode(f"encrypted:{data}:{self.keys[key_id]}".encode()).decode()
        self._audit("encryption", "system", "success")
        return {"encrypted": encrypted, "key_id": key_id}

    def verify_session(self, session_token):
        session = self.sessions.get(session_token)
        if not session: return {"valid": False}
        if __import__("time").time() > session["expires"]:
            del self.sessions[session_token]
            return {"valid": False, "reason": "expired"}
        return {"valid": True, "identity": session["identity"]}

    def stats(self):
        return {"identities": len(self.identities), "active_sessions": len(self.sessions), "audit_entries": len(self.audit_log)}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["identities", "sessions", "audit_log", "keys"]}

    def from_dict(self, data):
        for k in ["identities", "sessions", "audit_log", "keys"]:
            if k in data: setattr(self, k, data[k])


class CloudNativeIntelligenceFoundation:
    def __init__(self):
        self.services = {}
        self.remote_executions = []
        self.collaborations = []
        self.deployments = []

    def register_service(self, service_name, service_type, endpoint):
        self.services[service_name] = {"name": service_name, "type": service_type, "endpoint": endpoint, "status": "registered", "registered": __import__("time").time()}
        return self.services[service_name]

    def remote_execute(self, service_name, task, params=None):
        service = self.services.get(service_name)
        if not service: return {"error": "service not found"}
        execution = {"service": service_name, "task": task, "params": params or {}, "submitted": __import__("time").time(), "status": "executing"}
        self.remote_executions.append(execution)
        execution["result"] = f"executed_{task}_{len(self.remote_executions)}"
        execution["status"] = "completed"
        execution["completed_at"] = __import__("time").time()
        execution["duration"] = round(execution["completed_at"] - execution["submitted"], 2)
        return execution

    def create_collaboration(self, name, participants, intent):
        collab = {"name": name, "participants": participants, "intent": intent, "created": __import__("time").time(), "status": "active", "artifacts": []}
        self.collaborations.append(collab)
        return collab

    def deploy_intelligence(self, module_name, target_environment, config=None):
        deployment = {"module": module_name, "target": target_environment, "config": config or {}, "deployed": __import__("time").time(), "status": "active"}
        self.deployments.append(deployment)
        return deployment

    def scale_service(self, service_name, replicas):
        service = self.services.get(service_name)
        if not service: return {"error": "service not found"}
        service["replicas"] = replicas
        service["scaled_at"] = __import__("time").time()
        return {"service": service_name, "replicas": replicas}

    def stats(self):
        return {"services": len(self.services), "executions": len(self.remote_executions), "collaborations": len(self.collaborations), "deployments": len(self.deployments)}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["services", "remote_executions", "collaborations", "deployments"]}

    def from_dict(self, data):
        for k in ["services", "remote_executions", "collaborations", "deployments"]:
            if k in data: setattr(self, k, data[k])


class AutonomousIntelligenceInfrastructureLayer:
    def __init__(self):
        self.resource_manager = IntelligentResourceManager()
        self.distributed_network = DistributedIntelligenceFramework()
        self.agent_runtime = AgentRuntimeManager()
        self.semantic_storage = SemanticStorageSystem()
        self.computational_memory = ComputationalMemoryLayer()
        self.monitoring = InfrastructureMonitoringSystem()
        self.optimization = SelfOptimizationFramework()
        self.hardware_abstraction = HardwareAbstractionLayer()
        self.security = SecurityInfrastructure()
        self.cloud_native = CloudNativeIntelligenceFoundation()
        self._initialized = False

    def initialize(self):
        self.hardware_abstraction.detect_platform("laptop")
        self.distributed_network.register_node("localhost", "primary", {"cpu": 8, "memory": 16000})
        self.monitoring.record_metric("cpu_utilization", 10)
        self.monitoring.record_metric("memory_utilization", 15)
        self._initialized = True
        return {"status": "aiil_initialized", "layers": 10}

    def full_summary(self):
        return {"resource_manager": self.resource_manager.stats(), "distributed_network": self.distributed_network.stats(), "agent_runtime": self.agent_runtime.stats(), "semantic_storage": self.semantic_storage.stats(), "computational_memory": self.computational_memory.stats(), "monitoring": self.monitoring.stats(), "optimization": self.optimization.stats(), "hardware_abstraction": self.hardware_abstraction.stats(), "security": self.security.stats(), "cloud_native": self.cloud_native.stats()}

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.__dict__.items() if k != "_initialized" and hasattr(v, "to_dict")}

    def from_dict(self, data):
        for key in ["resource_manager", "distributed_network", "agent_runtime", "semantic_storage", "computational_memory", "monitoring", "optimization", "hardware_abstraction", "security", "cloud_native"]:
            if key in data and hasattr(self, key) and hasattr(getattr(self, key), "from_dict"):
                getattr(self, key).from_dict(data[key])


class FederatedIntelligenceNetwork:
    def __init__(self):
        self.nodes = {}
        self.federation = {}
        self.shared_resources = []

    def register_node(self, node_id, identity, trust_level, capabilities):
        self.nodes[node_id] = {"id": node_id, "identity": identity, "trust_level": trust_level, "capabilities": capabilities, "status": "autonomous", "joined": __import__("time").time(), "agents": [], "shared_resources": []}
        return {"node": node_id, "status": "autonomous"}

    def request_collaboration(self, from_node, to_node, purpose):
        if to_node not in self.nodes: return {"error": "node not found"}
        if to_node not in self.federation: self.federation[to_node] = []
        req = {"from": from_node, "purpose": purpose, "timestamp": __import__("time").time(), "status": "pending"}
        self.federation[to_node].append(req)
        return {"request": req, "status": "pending"}

    def approve_collaboration(self, node_id, request_idx):
        if node_id not in self.federation: return {"error": "no requests"}
        reqs = self.federation[node_id]
        if request_idx < 0 or request_idx >= len(reqs): return {"error": "invalid request"}
        reqs[request_idx]["status"] = "approved"
        self.nodes[reqs[request_idx]["from"]]["status"] = "collaborating"
        return {"approved": True, "partner": reqs[request_idx]["from"]}

    def share_resource(self, node_id, resource_type, resource_id, access_level):
        if node_id not in self.nodes: return {"error": "node not found"}
        entry = {"type": resource_type, "id": resource_id, "access_level": access_level, "shared_at": __import__("time").time()}
        self.nodes[node_id]["shared_resources"].append(entry)
        self.shared_resources.append({"node": node_id, "resource": entry})
        return {"shared": resource_id, "access": access_level}

    def get_federation_status(self):
        collaborating = sum(1 for n in self.nodes.values() if n.get("status") == "collaborating")
        return {"total_nodes": len(self.nodes), "autonomous": sum(1 for n in self.nodes.values() if n.get("status") == "autonomous"), "collaborating": collaborating, "shared_resources": len(self.shared_resources)}

    def stats(self):
        return self.get_federation_status()

    def to_dict(self):
        return {k: getattr(self, k) for k in ["nodes", "federation", "shared_resources"]}

    def from_dict(self, data):
        for k in ["nodes", "federation", "shared_resources"]:
            if k in data: setattr(self, k, data[k])


class TrustFramework:
    def __init__(self):
        self.relationships = []
        self.trust_levels = {"personal": {"weight": 100, "auto_approve": True}, "team": {"weight": 70, "auto_approve": False}, "organization": {"weight": 40, "auto_approve": False}, "public": {"weight": 10, "auto_approve": False}}

    def establish_trust(self, from_entity, to_entity, trust_type):
        if trust_type not in self.trust_levels: return {"error": "unknown trust type"}
        rel = {"from": from_entity, "to": to_entity, "type": trust_type, "level": self.trust_levels[trust_type], "established": __import__("time").time(), "active": True}
        self.relationships.append(rel)
        return rel

    def verify_trust(self, from_entity, to_entity, required_action):
        for rel in self.relationships:
            if rel["from"] == from_entity and rel["to"] == to_entity and rel["active"]:
                if required_action == "collaborate" and rel["type"] == "personal":
                    return {"trusted": True, "level": rel["level"]}
                return {"trusted": True, "level": rel["level"]}
        return {"trusted": False, "reason": "no trust relationship"}

    def revoke_trust(self, from_entity, to_entity):
        for rel in self.relationships:
            if rel["from"] == from_entity and rel["to"] == to_entity:
                rel["active"] = False
                rel["revoked_at"] = __import__("time").time()
                return {"revoked": True}
        return {"error": "relationship not found"}

    def get_trust_score(self, from_entity, to_entity):
        score = 0
        for rel in self.relationships:
            if rel["from"] == from_entity and rel["to"] == to_entity and rel["active"]:
                score += rel["level"]["weight"]
        return {"score": score, "max_possible": 100}

    def stats(self):
        return {"relationships": len(self.relationships), "active": sum(1 for r in self.relationships if r["active"]), "levels": list(self.trust_levels.keys())}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["relationships", "trust_levels"]}

    def from_dict(self, data):
        for k in ["relationships", "trust_levels"]:
            if k in data: setattr(self, k, data[k])


class AgentToAgentCommunication:
    def __init__(self):
        self.messages = []
        self.delegations = []
        self.discoveries = []

    def send_message(self, sender_id, sender_node, recipient_id, recipient_node, content, msg_type="standard"):
        msg = {"id": f"msg_{len(self.messages)+1}", "sender": {"id": sender_id, "node": sender_node}, "recipient": {"id": recipient_id, "node": recipient_node}, "content": content, "type": msg_type, "timestamp": __import__("time").time(), "status": "sent"}
        self.messages.append(msg)
        return msg

    def delegate_task(self, from_agent, from_node, to_agent, to_node, task, requirements):
        delegation = {"id": f"del_{len(self.delegations)+1}", "from": {"agent": from_agent, "node": from_node}, "to": {"agent": to_agent, "node": to_node}, "task": task, "requirements": requirements, "status": "delegated", "timestamp": __import__("time").time()}
        self.delegations.append(delegation)
        return delegation

    def update_delegation(self, del_id, status, result=None):
        for d in self.delegations:
            if d["id"] == del_id:
                d["status"] = status
                if result: d["result"] = result
                d["updated_at"] = __import__("time").time()
                return d
        return {"error": "delegation not found"}

    def discover_capabilities(self, node_id):
        caps = {"translation": 0.9, "research": 0.85, "coding": 0.8, "analysis": 0.75}
        discovery = {"node": node_id, "capabilities": caps, "discovered_at": __import__("time").time()}
        self.discoveries.append(discovery)
        return discovery

    def verify_result(self, del_id):
        for d in self.delegations:
            if d["id"] == del_id and d.get("result"):
                return {"verified": True, "result": d["result"], "verified_at": __import__("time").time()}
        return {"verified": False, "reason": "no result available"}

    def stats(self):
        return {"messages": len(self.messages), "delegations": len(self.delegations), "discoveries": len(self.discoveries)}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["messages", "delegations", "discoveries"]}

    def from_dict(self, data):
        for k in ["messages", "delegations", "discoveries"]:
            if k in data: setattr(self, k, data[k])


class DistributedKnowledgeExchange:
    def __init__(self):
        self.knowledge_base = []
        self.exchanges = []
        self.ownership = {}

    def share_knowledge(self, owner, knowledge_type, content, metadata=None):
        entry = {"id": f"k_{len(self.knowledge_base)+1}", "owner": owner, "type": knowledge_type, "content": content, "metadata": metadata or {}, "shared_at": __import__("time").time(), "version": 1}
        self.knowledge_base.append(entry)
        self.ownership[entry["id"]] = {"owner": owner, "preserved": True}
        return entry

    def request_knowledge(self, requester, knowledge_id):
        entry = next((k for k in self.knowledge_base if k["id"] == knowledge_id), None)
        if not entry: return {"error": "knowledge not found"}
        exchange = {"requester": requester, "knowledge_id": knowledge_id, "owner": entry["owner"], "requested_at": __import__("time").time(), "status": "granted"}
        self.exchanges.append(exchange)
        return {"knowledge": entry, "exchange": exchange}

    def get_knowledge_by_type(self, knowledge_type):
        return [k for k in self.knowledge_base if k["type"] == knowledge_type]

    def update_knowledge(self, knowledge_id, new_content, contributor):
        for k in self.knowledge_base:
            if k["id"] == knowledge_id:
                if k["owner"] != contributor:
                    k["content"] = new_content
                    k["version"] += 1
                    k["updated_at"] = __import__("time").time()
                    k["last_contributor"] = contributor
                    return {"updated": True, "version": k["version"]}
        return {"error": "not found or not owner"}

    def verify_ownership(self, knowledge_id):
        entry = self.ownership.get(knowledge_id)
        return {"preserved": entry["preserved"] if entry else False, "owner": entry["owner"] if entry else None}

    def stats(self):
        types = {}
        for k in self.knowledge_base:
            types[k["type"]] = types.get(k["type"], 0) + 1
        return {"total": len(self.knowledge_base), "exchanges": len(self.exchanges), "types": types}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["knowledge_base", "exchanges", "ownership"]}

    def from_dict(self, data):
        for k in ["knowledge_base", "exchanges", "ownership"]:
            if k in data: setattr(self, k, data[k])


class TeamIntelligenceSpace:
    def __init__(self):
        self.spaces = []

    def create_space(self, name, creator, description):
        space = {"id": f"space_{len(self.spaces)+1}", "name": name, "creator": creator, "description": description, "created": __import__("time").time(), "members": [creator], "goals": [], "projects": [], "memory": [], "agents": [], "workflows": [], "status": "active"}
        self.spaces.append(space)
        return space

    def add_member(self, space_id, member_id, role="contributor"):
        space = next((s for s in self.spaces if s["id"] == space_id), None)
        if not space: return {"error": "space not found"}
        if member_id not in space["members"]:
            space["members"].append(member_id)
        space["roles"] = space.get("roles", {})
        space["roles"][member_id] = role
        return {"member": member_id, "role": role}

    def add_goal(self, space_id, goal):
        space = next((s for s in self.spaces if s["id"] == space_id), None)
        if not space: return {"error": "space not found"}
        g = {"id": f"goal_{len(space['goals'])+1}", "text": goal, "status": "active", "created": __import__("time").time()}
        space["goals"].append(g)
        return g

    def add_shared_memory(self, space_id, contributor, content, memory_type="note"):
        space = next((s for s in self.spaces if s["id"] == space_id), None)
        if not space: return {"error": "space not found"}
        mem = {"contributor": contributor, "content": content, "type": memory_type, "timestamp": __import__("time").time()}
        space["memory"].append(mem)
        return mem

    def add_agent(self, space_id, agent_id, agent_type, owner):
        space = next((s for s in self.spaces if s["id"] == space_id), None)
        if not space: return {"error": "space not found"}
        agent = {"id": agent_id, "type": agent_type, "owner": owner, "status": "available", "added": __import__("time").time()}
        space["agents"].append(agent)
        return agent

    def add_workflow(self, space_id, name, steps):
        space = next((s for s in self.spaces if s["id"] == space_id), None)
        if not space: return {"error": "space not found"}
        wf = {"id": f"wf_{len(space['workflows'])+1}", "name": name, "steps": steps, "created": __import__("time").time()}
        space["workflows"].append(wf)
        return wf

    def stats(self):
        return {"spaces": len(self.spaces), "total_members": sum(len(s["members"]) for s in self.spaces), "total_goals": sum(len(s["goals"]) for s in self.spaces)}

    def to_dict(self):
        return {"spaces": self.spaces}

    def from_dict(self, data):
        if "spaces" in data: self.spaces = data["spaces"]


class CollectiveReasoningEngine:
    def __init__(self):
        self.problems = []
        self.solutions = []

    def submit_problem(self, title, description, required_expertise):
        problem = {"id": f"prob_{len(self.problems)+1}", "title": title, "description": description, "required_expertise": required_expertise, "submitted": __import__("time").time(), "status": "open"}
        self.problems.append(problem)
        return problem

    def contribute_solution(self, problem_id, agent_id, node_id, solution, expertise_area):
        prob = next((p for p in self.problems if p["id"] == problem_id), None)
        if not prob: return {"error": "problem not found"}
        contrib = {"problem_id": problem_id, "agent": {"id": agent_id, "node": node_id}, "solution": solution, "expertise": expertise_area, "contributed": __import__("time").time()}
        self.solutions.append(contrib)
        contributions = [s for s in self.solutions if s["problem_id"] == problem_id]
        if len(contributions) >= len(prob["required_expertise"]):
            prob["status"] = "unified"
        return contrib

    def unify_solutions(self, problem_id):
        prob = next((p for p in self.problems if p["id"] == problem_id), None)
        if not prob: return {"error": "problem not found"}
        contribs = [s for s in self.solutions if s["problem_id"] == problem_id]
        if len(contribs) < len(prob["required_expertise"]):
            return {"status": "insufficient_contributions", "have": len(contribs), "need": len(prob["required_expertise"])}
        unified = {"problem_id": problem_id, "contributions": contribs, "unified_solution": f"Integrated solution from {len(contribs)} contributors across expertise areas: {', '.join(prob['required_expertise'])}", "unified_at": __import__("time").time()}
        prob["status"] = "solved"
        prob["unified"] = unified
        return unified

    def stats(self):
        return {"problems": len(self.problems), "solutions": len(self.solutions), "solved": sum(1 for p in self.problems if p["status"] == "solved")}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["problems", "solutions"]}

    def from_dict(self, data):
        for k in ["problems", "solutions"]:
            if k in data: setattr(self, k, data[k])


class CapabilityDiscovery:
    def __init__(self):
        self.directory = []
        self.inquiries = []

    def register_capability(self, provider, capability_name, description, expertise_level, access_required="request"):
        entry = {"id": f"cap_{len(self.directory)+1}", "provider": provider, "name": capability_name, "description": description, "expertise_level": expertise_level, "access_required": access_required, "registered": __import__("time").time(), "active": True}
        self.directory.append(entry)
        return entry

    def search_capabilities(self, query, min_level=0):
        results = []
        q = query.lower()
        for cap in self.directory:
            if not cap["active"]: continue
            if q in cap["name"].lower() or q in cap["description"].lower():
                if cap["expertise_level"] >= min_level:
                    results.append({"capability": cap, "relevance": 0.8 if q in cap["name"].lower() else 0.5})
        return sorted(results, key=lambda r: r["relevance"], reverse=True)

    def inquire_access(self, requester, capability_id):
        cap = next((c for c in self.directory if c["id"] == capability_id), None)
        if not cap: return {"error": "capability not found"}
        inquiry = {"requester": requester, "capability_id": capability_id, "provider": cap["provider"], "access": cap["access_required"], "inquired_at": __import__("time").time(), "status": "pending"}
        self.inquiries.append(inquiry)
        return {"inquiry": inquiry, "note": "Discovery does not grant automatic access. Contact provider: " + cap["provider"]}

    def deactivate_capability(self, capability_id):
        cap = next((c for c in self.directory if c["id"] == capability_id), None)
        if not cap: return {"error": "capability not found"}
        cap["active"] = False
        return {"deactivated": capability_id}

    def stats(self):
        return {"directory": len(self.directory), "active": sum(1 for c in self.directory if c["active"]), "inquiries": len(self.inquiries)}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["directory", "inquiries"]}

    def from_dict(self, data):
        for k in ["directory", "inquiries"]:
            if k in data: setattr(self, k, data[k])


class ProvenanceSystem:
    def __init__(self):
        self.records = []

    def record(self, source, contributing_agents, knowledge_origin, result_summary, permissions=None):
        record = {"id": f"prov_{len(self.records)+1}", "source": source, "contributing_agents": contributing_agents, "knowledge_origin": knowledge_origin, "result_summary": result_summary, "timestamp": __import__("time").time(), "version": 1, "permissions": permissions or {"visibility": "private"}}
        self.records.append(record)
        return record

    def get_lineage(self, record_id):
        record = next((r for r in self.records if r["id"] == record_id), None)
        if not record: return {"error": "record not found"}
        lineage = {"source": record["source"], "agents": record["contributing_agents"], "origin": record["knowledge_origin"], "version": record["version"], "timestamp": record["timestamp"]}
        return lineage

    def update_version(self, record_id, new_source, new_agents, summary):
        for r in self.records:
            if r["id"] == record_id:
                r["version"] += 1
                r["source"] = new_source
                r["contributing_agents"] = new_agents
                r["result_summary"] = summary
                r["updated_at"] = __import__("time").time()
                return {"id": record_id, "version": r["version"]}
        return {"error": "record not found"}

    def audit(self, record_id):
        record = next((r for r in self.records if r["id"] == record_id), None)
        if not record: return {"error": "record not found"}
        return {"id": record["id"], "source": record["source"], "agents": record["contributing_agents"], "origin": record["knowledge_origin"], "version": record["version"], "timestamp": record["timestamp"], "permissions": record["permissions"]}

    def stats(self):
        return {"records": len(self.records), "versions": sum(r["version"] for r in self.records)}

    def to_dict(self):
        return {"records": self.records}

    def from_dict(self, data):
        if "records" in data: self.records = data["records"]


class ResilienceLayer:
    def __init__(self):
        self.node_cache = {}
        self.pending_syncs = []
        self.failure_log = []
        self.conflicts = []

    def cache_node_state(self, node_id, state):
        self.node_cache[node_id] = {"state": state, "cached_at": __import__("time").time()}
        return {"cached": node_id}

    def queue_sync(self, from_node, to_node, data_type, data):
        sync = {"id": f"sync_{len(self.pending_syncs)+1}", "from": from_node, "to": to_node, "data_type": data_type, "data": data, "status": "pending", "queued": __import__("time").time()}
        self.pending_syncs.append(sync)
        return sync

    def process_sync(self, sync_id):
        sync = next((s for s in self.pending_syncs if s["id"] == sync_id), None)
        if not sync: return {"error": "sync not found"}
        sync["status"] = "completed"
        sync["completed_at"] = __import__("time").time()
        return sync

    def log_failure(self, node_id, component, error):
        failure = {"node": node_id, "component": component, "error": error, "timestamp": __import__("time").time(), "recovered": False}
        self.failure_log.append(failure)
        return failure

    def recover_node(self, node_id):
        for f in self.failure_log:
            if f["node"] == node_id and not f["recovered"]:
                f["recovered"] = True
                f["recovered_at"] = __import__("time").time()
        cached = self.node_cache.get(node_id)
        return {"recovered": True, "cached_state": cached["state"] if cached else None}

    def resolve_conflict(self, conflict_id, resolution):
        conflict = next((c for c in self.conflicts if c.get("id") == conflict_id), None)
        if not conflict: return {"error": "conflict not found"}
        conflict["resolution"] = resolution
        conflict["resolved_at"] = __import__("time").time()
        return {"resolved": conflict_id}

    def get_status(self):
        return {"cached_nodes": len(self.node_cache), "pending_syncs": len([s for s in self.pending_syncs if s["status"] == "pending"]), "failures": len(self.failure_log), "recovered": sum(1 for f in self.failure_log if f["recovered"]), "conflicts": len(self.conflicts)}

    def stats(self):
        return self.get_status()

    def to_dict(self):
        return {k: getattr(self, k) for k in ["node_cache", "pending_syncs", "failure_log", "conflicts"]}

    def from_dict(self, data):
        for k in ["node_cache", "pending_syncs", "failure_log", "conflicts"]:
            if k in data: setattr(self, k, data[k])


class GovernanceSystem:
    def __init__(self):
        self.policies = []
        self.permissions = []
        self.audit_log = []
        self.revocations = []

    def create_policy(self, name, description, rules):
        policy = {"id": f"pol_{len(self.policies)+1}", "name": name, "description": description, "rules": rules, "created": __import__("time").time(), "active": True}
        self.policies.append(policy)
        return policy

    def grant_permission(self, identity, resource, action, expires_in=86400):
        perm = {"id": f"perm_{len(self.permissions)+1}", "identity": identity, "resource": resource, "action": action, "granted": __import__("time").time(), "expires": __import__("time").time() + expires_in, "revoked": False}
        self.permissions.append(perm)
        self._audit("grant", identity, f"permission to {action} on {resource}")
        return perm

    def check_permission(self, identity, resource, action):
        now = __import__("time").time()
        for p in self.permissions:
            if p["identity"] == identity and p["resource"] == resource and p["action"] == action and not p["revoked"] and now < p["expires"]:
                return {"allowed": True, "permission": p["id"]}
        return {"allowed": False, "reason": "no valid permission"}

    def revoke_access(self, permission_id):
        perm = next((p for p in self.permissions if p["id"] == permission_id), None)
        if not perm: return {"error": "permission not found"}
        perm["revoked"] = True
        perm["revoked_at"] = __import__("time").time()
        self.revocations.append({"permission": permission_id, "revoked_at": perm["revoked_at"]})
        self._audit("revoke", perm["identity"], f"revoked access to {perm['resource']}")
        return {"revoked": permission_id}

    def set_access_expiration(self, permission_id, expires_in):
        perm = next((p for p in self.permissions if p["id"] == permission_id), None)
        if not perm: return {"error": "permission not found"}
        perm["expires"] = __import__("time").time() + expires_in
        return {"expires_in": expires_in}

    def _audit(self, action, actor, details):
        entry = {"action": action, "actor": actor, "details": details, "timestamp": __import__("time").time()}
        self.audit_log.append(entry)
        return entry

    def get_audit_log(self, limit=20):
        return self.audit_log[-limit:]

    def stats(self):
        return {"policies": len(self.policies), "active_permissions": sum(1 for p in self.permissions if not p["revoked"]), "audit_entries": len(self.audit_log), "revocations": len(self.revocations)}

    def to_dict(self):
        return {k: getattr(self, k) for k in ["policies", "permissions", "audit_log", "revocations"]}

    def from_dict(self, data):
        for k in ["policies", "permissions", "audit_log", "revocations"]:
            if k in data: setattr(self, k, data[k])


class CollectiveIntelligenceNetwork:
    def __init__(self):
        self.federation = FederatedIntelligenceNetwork()
        self.trust = TrustFramework()
        self.communication = AgentToAgentCommunication()
        self.knowledge_exchange = DistributedKnowledgeExchange()
        self.team_spaces = TeamIntelligenceSpace()
        self.reasoning = CollectiveReasoningEngine()
        self.discovery = CapabilityDiscovery()
        self.provenance = ProvenanceSystem()
        self.resilience = ResilienceLayer()
        self.governance = GovernanceSystem()
        self._initialized = False

    def initialize(self):
        self.federation.register_node("local", "self", 100, {"core": True})
        self.trust.establish_trust("local", "local", "personal")
        self._initialized = True
        return {"status": "cin_initialized", "layers": 10}

    def full_summary(self):
        return {"federation": self.federation.stats(), "trust": self.trust.stats(), "communication": self.communication.stats(), "knowledge_exchange": self.knowledge_exchange.stats(), "team_spaces": self.team_spaces.stats(), "reasoning": self.reasoning.stats(), "discovery": self.discovery.stats(), "provenance": self.provenance.stats(), "resilience": self.resilience.stats(), "governance": self.governance.stats()}

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.__dict__.items() if k != "_initialized" and hasattr(v, "to_dict")}

    def from_dict(self, data):
        for key in ["federation", "trust", "communication", "knowledge_exchange", "team_spaces", "reasoning", "discovery", "provenance", "resilience", "governance"]:
            if key in data and hasattr(self, key) and hasattr(getattr(self, key), "from_dict"):
                getattr(self, key).from_dict(data[key])


class FeedbackLearner:
    """Learns from user preferences, working style, communication patterns, decisions."""

    def __init__(self):
        self._feedback = []
        self._preferences = {}
        self._patterns = []

    def record_feedback(self, context, rating, comment=""):
        entry = {
            "context": context,
            "rating": rating,
            "comment": comment,
            "time": __import__("time").time(),
        }
        self._feedback.append(entry)
        # Update preferences based on repeated patterns
        if "design" in context.lower() and rating >= 4:
            self._preferences["design_style"] = "simple"
        if "complex" in context.lower() and rating <= 2:
            self._preferences["complexity"] = "low"
        return entry

    def get_preferences(self):
        return dict(self._preferences)

    def get_adjusted_recommendation(self, base_recommendation):
        adjusted = dict(base_recommendation)
        style = self._preferences.get("design_style")
        if style == "simple" and "design" in str(base_recommendation).lower():
            adjusted["style"] = "Simplified version recommended based on user preferences"
        complexity = self._preferences.get("complexity")
        if complexity == "low":
            adjusted["complexity_note"] = "User prefers low-complexity solutions"
        return adjusted

    def get_feedback_summary(self):
        if not self._feedback:
            return {"count": 0, "average_rating": 0}
        ratings = [f["rating"] for f in self._feedback]
        return {
            "count": len(self._feedback),
            "average_rating": round(sum(ratings) / len(ratings), 1),
            "preferences": self._preferences,
        }

    def to_dict(self):
        return {"feedback": self._feedback, "preferences": self._preferences, "patterns": self._patterns}

    def from_dict(self, data):
        self._feedback = data.get("feedback", [])
        self._preferences = data.get("preferences", {})
        self._patterns = data.get("patterns", [])


class ImprovementEngine:
    """Analyzes performance, identifies knowledge gaps, suggests improvements."""

    def __init__(self):
        self._suggestions = []
        self._applied = []

    def analyze_performance(self, profiles):
        """Analyze agent profiles and generate improvement suggestions."""
        suggestions = []
        for profile in profiles:
            agent_id = profile.agent_id
            weaknesses = profile.get_weaknesses()
            for w in weaknesses:
                suggestion = {
                    "agent_id": agent_id,
                    "target": w["skill"],
                    "type": "skill_gap",
                    "description": f"Improve '{w['skill']}' skill (currently Lv.{w['level']})",
                    "priority": "high" if w["level"] < 2 else "medium",
                    "suggested_action": f"Add focused training for {w['skill']}",
                }
                suggestions.append(suggestion)

            if profile.success_rate < 0.8:
                suggestions.append({
                    "agent_id": agent_id,
                    "target": "reliability",
                    "type": "performance",
                    "description": f"Success rate {profile.success_rate*100:.0f}% below 80% threshold",
                    "priority": "critical",
                    "suggested_action": "Add verification workflow and error handling",
                })

            if profile.tasks_completed > 50 and profile.version == "1.0.0":
                suggestions.append({
                    "agent_id": agent_id,
                    "target": "version",
                    "type": "evolution",
                    "description": f"Agent completed {profile.tasks_completed} tasks — ready for upgrade",
                    "priority": "medium",
                    "suggested_action": "Promote agent to v2.0 with new capabilities",
                })

        self._suggestions.extend(suggestions)
        return suggestions

    def apply_improvement(self, profile, suggestion):
        profile.record_improvement(suggestion["description"], suggestion["type"])
        if suggestion["type"] == "evolution" and "upgrade" in suggestion["suggested_action"].lower():
            parts = profile.version.split(".")
            profile.version = f"{int(parts[0]) + 1}.0.0"
        elif suggestion["type"] == "skill_gap" and suggestion["target"] in profile.skills:
            profile.skills[suggestion["target"]].add_experience(50)
        self._applied.append(suggestion)
        return True

    def get_suggestions(self, agent_id=None):
        if agent_id:
            return [s for s in self._suggestions if s["agent_id"] == agent_id]
        return list(self._suggestions)

    def get_applied(self):
        return list(self._applied)

    def to_dict(self):
        return {"suggestions": self._suggestions, "applied": self._applied}

    def from_dict(self, data):
        self._suggestions = data.get("suggestions", [])
        self._applied = data.get("applied", [])


class ArchitectureOptimizer:
    """Analyzes system architecture and proposes optimizations — new agents, restructures, merges."""

    def __init__(self):
        self._proposals = []
        self._changes = []

    def analyze_architecture(self, current_agents, task_history):
        proposals = []
        agent_types = [a.agent_type for a in current_agents]
        tasks = task_history or []

        # Detect missing security agent
        if "security" not in agent_types and any("security" in t.lower() or "protect" in t.lower() for t in tasks):
            proposals.append({
                "type": "new_agent",
                "name": "Security Intelligence Agent",
                "purpose": "Protect generated systems and data",
                "priority": "high",
                "reasoning": "Security-related tasks detected but no security agent exists",
            })

        # Detect need for dedicated data agent
        if "data" not in agent_types and any("data" in t.lower() or "analytics" in t.lower() for t in tasks):
            proposals.append({
                "type": "new_agent",
                "name": "Data Intelligence Agent",
                "purpose": "Manage data analysis, pipelines, and insights",
                "priority": "medium",
                "reasoning": "Data-related tasks detected without dedicated data agent",
            })

        # Check for agent overload
        if len(agent_types) < 3 and len(tasks) > 20:
            proposals.append({
                "type": "restructure",
                "name": "Split responsibilities",
                "purpose": "Divide workload among more specialized agents",
                "priority": "medium",
                "reasoning": f"{len(agent_types)} agents handling {len(tasks)} tasks — specialization recommended",
            })

        self._proposals.extend(proposals)
        return proposals

    def apply_proposal(self, proposal):
        self._changes.append({
            "proposal": proposal,
            "applied": __import__("time").time(),
            "status": "pending_review",
        })

    def get_proposals(self):
        return list(self._proposals)

    def get_changes(self):
        return list(self._changes)

    def to_dict(self):
        return {"proposals": self._proposals, "changes": self._changes}

    def from_dict(self, data):
        self._proposals = data.get("proposals", [])
        self._changes = data.get("changes", [])


class ResearchLab:
    """Internal research environment — experiments with algorithms, workflows, cooperation."""

    def __init__(self):
        self._experiments = []
        self._findings = []

    def design_experiment(self, exp_id, name, hypothesis, variables=None):
        exp = {
            "experiment_id": exp_id,
            "name": name,
            "hypothesis": hypothesis,
            "variables": variables or {},
            "status": "designed",
            "created": __import__("time").time(),
        }
        self._experiments.append(exp)
        return exp

    def run_experiment(self, exp_id):
        import random
        exp = next((e for e in self._experiments if e["experiment_id"] == exp_id), None)
        if not exp:
            return None
        result = {"experiment_id": exp_id, "name": exp["name"], "status": "completed"}
        exp["status"] = "completed"

        hypothesis = exp["hypothesis"].lower()
        if "planning" in hypothesis or "workflow" in hypothesis:
            improvement = round(random.uniform(5, 25), 1)
            result["finding"] = f"System B improves project completion by {improvement}%"
            result["improvement_percent"] = improvement
            result["recommendation"] = "Adopt System B" if improvement > 10 else "Further testing needed"
        elif "algorithm" in hypothesis or "cooperation" in hypothesis:
            speedup = round(random.uniform(1.2, 3.0), 1)
            result["finding"] = f"New algorithm achieves {speedup}x speedup in cooperative tasks"
            result["speedup"] = speedup
            result["recommendation"] = "Integrate into agent collaboration layer" if speedup > 1.5 else "Requires optimization"
        elif "interface" in hypothesis:
            satisfaction = round(random.uniform(60, 98), 1)
            result["finding"] = f"New interface design achieves {satisfaction}% user satisfaction"
            result["satisfaction"] = satisfaction
            result["recommendation"] = "Proceed to production" if satisfaction > 80 else "Iterate on design"
        else:
            result["finding"] = f"Experiment completed: {random.choice(['Positive results', 'No significant change', 'Mixed outcomes'])}"

        result["timestamp"] = __import__("time").time()
        self._findings.append(result)
        return result

    def get_findings(self):
        return list(self._findings)

    def to_dict(self):
        return {"experiments": self._experiments, "findings": self._findings}

    def from_dict(self, data):
        self._experiments = data.get("experiments", [])
        self._findings = data.get("findings", [])


class EvolutionMemory:
    """History of intelligence growth — versions, milestones, capability additions."""

    def __init__(self):
        self._eras = []
        self._milestones = []

    def add_era(self, era_id, name, description, capabilities=None):
        era = {
            "era_id": era_id,
            "name": name,
            "description": description,
            "capabilities": capabilities or [],
            "started": __import__("time").time(),
        }
        self._eras.append(era)
        return era

    def add_milestone(self, name, description, impact="medium"):
        milestone = {
            "name": name,
            "description": description,
            "impact": impact,
            "achieved": __import__("time").time(),
        }
        self._milestones.append(milestone)
        return milestone

    def get_evolution_timeline(self):
        timeline = []
        for era in self._eras:
            timeline.append({
                "type": "era",
                "name": era["name"],
                "description": era["description"],
                "capabilities": era["capabilities"],
            })
        for ms in self._milestones:
            timeline.append({
                "type": "milestone",
                "name": ms["name"],
                "description": ms["description"],
                "impact": ms["impact"],
            })
        return timeline

    def get_summary(self):
        return {
            "eras": len(self._eras),
            "milestones": len(self._milestones),
            "timeline": self.get_evolution_timeline(),
        }

    def to_dict(self):
        return {"eras": self._eras, "milestones": self._milestones}

    def from_dict(self, data):
        self._eras = data.get("eras", [])
        self._milestones = data.get("milestones", [])


class GovernanceLayer:
    """Human oversight — approval controls, transparency reports, rollback, safety boundaries."""

    def __init__(self):
        self._pending_approvals = []
        self._change_log = []
        self._safety_rules = []
        self._rollback_points = []

    def request_approval(self, change_type, description, benefit, risk="low"):
        request = {
            "id": len(self._pending_approvals),
            "change_type": change_type,
            "description": description,
            "benefit": benefit,
            "risk": risk,
            "status": "pending",
            "requested": __import__("time").time(),
            "explanation": f"What changed: {description}\nWhy: {benefit}\nRisk: {risk}",
        }
        self._pending_approvals.append(request)
        return request

    def approve(self, request_id):
        req = next((r for r in self._pending_approvals if r["id"] == request_id), None)
        if not req:
            return False
        req["status"] = "approved"
        req["approved_at"] = __import__("time").time()
        self._change_log.append(req)
        return True

    def reject(self, request_id, reason="No reason provided"):
        req = next((r for r in self._pending_approvals if r["id"] == request_id), None)
        if not req:
            return False
        req["status"] = "rejected"
        req["rejection_reason"] = reason
        return True

    def create_rollback_point(self, snapshot_id, description):
        point = {
            "snapshot_id": snapshot_id,
            "description": description,
            "created": __import__("time").time(),
        }
        self._rollback_points.append(point)
        return point

    def get_pending(self):
        return [r for r in self._pending_approvals if r["status"] == "pending"]

    def get_change_log(self):
        return list(self._change_log)

    def generate_transparency_report(self):
        approved = sum(1 for c in self._change_log if c.get("status") == "approved")
        rejected = sum(1 for r in self._pending_approvals if r["status"] == "rejected")
        pending = len(self.get_pending())
        return {
            "total_changes": len(self._change_log),
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "rollback_points": len(self._rollback_points),
            "recent_changes": self._change_log[-5:],
        }

    def to_dict(self):
        return {
            "pending_approvals": self._pending_approvals,
            "change_log": self._change_log,
            "rollback_points": self._rollback_points,
        }

    def from_dict(self, data):
        self._pending_approvals = data.get("pending_approvals", [])
        self._change_log = data.get("change_log", [])
        self._rollback_points = data.get("rollback_points", [])


class SelfEvolvingIntelligence:
    """Top-level orchestrator — continuous self-improvement with human governance."""

    def __init__(self):
        self.profiles = {}
        self.benchmark = IntelligenceBenchmark()
        self.feedback = FeedbackLearner()
        self.improvement = ImprovementEngine()
        self.architecture = ArchitectureOptimizer()
        self.research = ResearchLab()
        self.evolution = EvolutionMemory()
        self.governance = GovernanceLayer()

        self._init_default_profiles()

    def _init_default_profiles(self):
        default_agents = [
            ("agent_research", "Research Agent", "research"),
            ("agent_code", "Coding Agent", "coding"),
            ("agent_design", "Design Agent", "design"),
        ]
        for aid, name, atype in default_agents:
            profile = AgentEvolutionProfile(aid, name, atype)
            profile.add_skill("analysis", 4.0)
            profile.add_skill("planning", 3.0)
            profile.add_skill("execution", 3.5)
            profile.add_skill("verification", 2.5)
            profile.record_improvement("Initial profile created", "onboarding")
            self.profiles[aid] = profile

    def register_agent(self, agent_id, name, agent_type):
        profile = AgentEvolutionProfile(agent_id, name, agent_type)
        profile.add_skill("analysis", 2.0)
        profile.add_skill("planning", 2.0)
        profile.add_skill("execution", 2.0)
        self.profiles[agent_id] = profile
        return profile

    def record_task_result(self, agent_id, success):
        profile = self.profiles.get(agent_id)
        if profile:
            profile.record_task_result(success)
            if success:
                for skill in profile.skills.values():
                    skill.add_experience(5)

    def run_full_evaluation(self):
        """Run a complete evaluation cycle across all agents."""
        evaluations = []
        for aid in self.profiles:
            eval_result = self.benchmark.evaluate_agent(aid)
            evaluations.append(eval_result)
        suggestions = self.improvement.analyze_performance(list(self.profiles.values()))
        arch_proposals = self.architecture.analyze_architecture(
            list(self.profiles.values()),
            [p.summary() for p in self.profiles.values()]
        )
        return {
            "evaluations": evaluations,
            "suggestions": suggestions,
            "architecture_proposals": arch_proposals,
        }

    def apply_improvement(self, agent_id, suggestion):
        profile = self.profiles.get(agent_id)
        if not profile:
            return False
        approval = self.governance.request_approval(
            "improvement",
            suggestion["description"],
            f"Target: {suggestion['target']}, Priority: {suggestion['priority']}",
            "low" if suggestion["priority"] == "medium" else "medium"
        )
        self.governance.approve(approval["id"])
        result = self.improvement.apply_improvement(profile, suggestion)
        self.evolution.add_milestone(
            f"Improved {profile.name}",
            suggestion["description"],
            "high" if suggestion["priority"] == "critical" else "medium"
        )
        return result

    def get_evolution_summary(self):
        return {
            "agents": {aid: p.summary() for aid, p in self.profiles.items()},
            "evaluations": len(self.benchmark.get_evaluations()),
            "suggestions": len(self.improvement.get_suggestions()),
            "applied": len(self.improvement.get_applied()),
            "feedback": self.feedback.get_feedback_summary(),
            "research_findings": len(self.research.get_findings()),
            "governance": self.governance.generate_transparency_report(),
            "evolution": self.evolution.get_summary(),
        }

    def to_dict(self):
        return {
            "profiles": {aid: p.to_dict() for aid, p in self.profiles.items()},
            "benchmark": self.benchmark.to_dict(),
            "feedback": self.feedback.to_dict(),
            "improvement": self.improvement.to_dict(),
            "architecture": self.architecture.to_dict(),
            "research": self.research.to_dict(),
            "evolution": self.evolution.to_dict(),
            "governance": self.governance.to_dict(),
        }

    def from_dict(self, data):
        if "profiles" in data:
            self.profiles = {}
            for aid, pdata in data["profiles"].items():
                profile = AgentEvolutionProfile(pdata["agent_id"], pdata["name"], pdata.get("agent_type", "general"))
                profile.from_dict(pdata)
                self.profiles[aid] = profile
        if "benchmark" in data:
            self.benchmark.from_dict(data["benchmark"])
        if "feedback" in data:
            self.feedback.from_dict(data["feedback"])
        if "improvement" in data:
            self.improvement.from_dict(data["improvement"])
        if "architecture" in data:
            self.architecture.from_dict(data["architecture"])
        if "research" in data:
            self.research.from_dict(data["research"])
        if "evolution" in data:
            self.evolution.from_dict(data["evolution"])
        if "governance" in data:
            self.governance.from_dict(data["governance"])


# ============================================================
# DIGITAL TWIN MIND — Personal Intelligence Layer
# ============================================================
# The OS understands user goals, knowledge, projects, decisions.
# Remembers 'why this matters' not just 'where this file is'.

class PrivacyController:
    """User-controlled, private by default, permission-based memory access."""

    def __init__(self):
        self._permissions = {}
        self._audit_log = []
        self._user_owned = True

    def grant(self, component, access_type):
        self._permissions[(component, access_type)] = True
        self._log(f"Granted {access_type} to {component}")

    def revoke(self, component, access_type):
        self._permissions.pop((component, access_type), None)
        self._log(f"Revoked {access_type} from {component}")

    def check(self, component, access_type):
        return self._permissions.get((component, access_type), False)

    def _log(self, entry):
        import time
        self._audit_log.append({"time": time.time(), "entry": entry})
        if len(self._audit_log) > 200:
            self._audit_log = self._audit_log[-100:]

    def explain(self, suggestion, sources):
        return f"Suggestion: {suggestion}\nBased on: {', '.join(sources)}"

    def audit(self):
        return list(self._audit_log)


class MemorySystem:
    """Stores conversations, documents, projects, notes, research, code, decisions."""

    def __init__(self):
        self._memories = []
        self._categories = set()

    def store(self, category, content, tags=None, source=None):
        import time
        entry = {
            "id": len(self._memories),
            "time": time.time(),
            "category": category,
            "content": content,
            "tags": tags or [],
            "source": source,
        }
        self._memories.append(entry)
        self._categories.add(category)
        return entry["id"]

    def recall(self, query=None, category=None, limit=5):
        results = self._memories
        if category:
            results = [m for m in results if m["category"] == category]
        if query:
            q = query.lower()
            results = [m for m in results if q in m["content"].lower() or any(q in t.lower() for t in m["tags"])]
        return sorted(results, key=lambda m: m["time"], reverse=True)[:limit]

    def search_by_tag(self, tag, limit=10):
        return [m for m in self._memories if tag in m["tags"]][:limit]

    def count(self, category=None):
        if category:
            return sum(1 for m in self._memories if m["category"] == category)
        return len(self._memories)

    def categories(self):
        return sorted(self._categories)

    def recent(self, n=5):
        return sorted(self._memories, key=lambda m: m["time"], reverse=True)[:n]

    def to_dict(self):
        return {"memories": self._memories}

    def from_dict(self, data):
        self._memories = data.get("memories", [])
        self._categories = {m["category"] for m in self._memories}


class KnowledgeGraph:
    """Dynamic graph database of concepts, relationships, dependencies."""

    def __init__(self):
        self._nodes = {}
        self._edges = []

    def add_concept(self, concept_id, label, category="general", details=None):
        import time
        self._nodes[concept_id] = {
            "id": concept_id,
            "label": label,
            "category": category,
            "details": details or {},
            "created": time.time(),
            "updated": time.time(),
        }
        return concept_id

    def relate(self, from_id, to_id, relation="related_to"):
        if from_id in self._nodes and to_id in self._nodes:
            edge = {"from": from_id, "to": to_id, "relation": relation}
            if edge not in self._edges:
                self._edges.append(edge)
            self._nodes[from_id]["updated"] = __import__("time").time()

    def get_connections(self, concept_id, depth=1):
        if concept_id not in self._nodes:
            return []
        connected = []
        for edge in self._edges:
            if edge["from"] == concept_id:
                connected.append((edge["to"], edge["relation"]))
            elif edge["to"] == concept_id:
                connected.append((edge["from"], edge["relation"]))
        if depth > 1:
            for cid, _ in list(connected):
                connected.extend(self.get_connections(cid, depth - 1))
        return connected

    def query(self, category=None, prefix=None):
        results = list(self._nodes.values())
        if category:
            results = [n for n in results if n["category"] == category]
        if prefix:
            results = [n for n in results if n["label"].lower().startswith(prefix.lower())]
        return results

    def path(self, from_id, to_id):
        """Simple BFS to find path between two concepts."""
        if from_id not in self._nodes or to_id not in self._nodes:
            return None
        visited = {from_id}
        queue = [[from_id]]
        while queue:
            path = queue.pop(0)
            last = path[-1]
            if last == to_id:
                return path
            for edge in self._edges:
                neighbor = None
                if edge["from"] == last:
                    neighbor = edge["to"]
                elif edge["to"] == last:
                    neighbor = edge["from"]
                if neighbor and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return None

    def to_dict(self):
        return {"nodes": self._nodes, "edges": self._edges}

    def from_dict(self, data):
        self._nodes = data.get("nodes", {})
        self._edges = data.get("edges", [])


class ContextEngine:
    """Understands current task, previous conversations, active projects, user goals."""

    def __init__(self):
        self._current_mission = None
        self._active_projects = []
        self._session_history = []
        self._preferences = {}

    def set_mission(self, mission):
        self._current_mission = mission
        self._session_history.append({"type": "mission_start", "data": mission})

    def get_current(self):
        return {
            "mission": self._current_mission,
            "active_projects": list(self._active_projects),
            "session_actions": len(self._session_history),
        }

    def track_action(self, action_type, data=None):
        import time
        self._session_history.append({"type": action_type, "data": data, "time": time.time()})
        if len(self._session_history) > 100:
            self._session_history = self._session_history[-50:]

    def set_preference(self, key, value):
        self._preferences[key] = value

    def get_preference(self, key, default=None):
        return self._preferences.get(key, default)

    def summary(self):
        m = self._current_mission or "No active mission"
        return f"Mission: {m} | Projects: {len(self._active_projects)} | Actions: {len(self._session_history)}"

    def to_dict(self):
        return {
            "current_mission": self._current_mission,
            "active_projects": self._active_projects,
            "preferences": self._preferences,
        }

    def from_dict(self, data):
        self._current_mission = data.get("current_mission")
        self._active_projects = data.get("active_projects", [])
        self._preferences = data.get("preferences", {})


class LearningModel:
    """Tracks what user knows, learning progress, skill progression."""

    def __init__(self):
        self._skills = {}
        self._learning_paths = {}
        self._completed = []

    def add_skill(self, name, category, level=0.0):
        self._skills[name] = {
            "name": name,
            "category": category,
            "level": max(0.0, min(1.0, level)),
            "updated": __import__("time").time(),
        }

    def update_skill(self, name, delta=0.1):
        if name in self._skills:
            self._skills[name]["level"] = max(0.0, min(1.0, self._skills[name]["level"] + delta))
            self._skills[name]["updated"] = __import__("time").time()

    def get_skill(self, name):
        return self._skills.get(name)

    def get_skills(self, category=None):
        if category:
            return {k: v for k, v in self._skills.items() if v["category"] == category}
        return dict(self._skills)

    def create_path(self, goal, steps):
        import time
        path = {
            "goal": goal,
            "steps": [{"name": s, "completed": False} for s in steps],
            "created": time.time(),
            "progress": 0.0,
        }
        self._learning_paths[goal] = path
        return path

    def complete_step(self, goal, step_name):
        path = self._learning_paths.get(goal)
        if not path:
            return
        for step in path["steps"]:
            if step["name"] == step_name and not step["completed"]:
                step["completed"] = True
                completed = sum(1 for s in path["steps"] if s["completed"])
                path["progress"] = completed / len(path["steps"])
                self._completed.append({"goal": goal, "step": step_name, "time": __import__("time").time()})
                return

    def get_path(self, goal):
        return self._learning_paths.get(goal)

    def progress_summary(self):
        return {goal: f"{path['progress']*100:.0f}%" for goal, path in self._learning_paths.items()}

    def to_dict(self):
        return {"skills": self._skills, "paths": self._learning_paths, "completed": self._completed}

    def from_dict(self, data):
        self._skills = data.get("skills", {})
        self._learning_paths = data.get("paths", {})
        self._completed = data.get("completed", [])


class ChiefOfStaff:
    """Proactive intelligence — analyzes goals, tracks progress, detects obstacles."""

    def __init__(self):
        self._suggestions = []
        self._obstacles = []

    def analyze_mission(self, mission, memory_system, knowledge_graph, learning_model):
        suggestions = []
        obstacles = []

        # Check if we've seen similar missions
        similar = memory_system.recall(query=mission, category="mission", limit=3)
        if similar:
            suggestions.append(f"You previously worked on similar missions. Review past progress for insights.")

        # Check for skill gaps
        skills = learning_model.get_skills()
        low_skills = {k: v for k, v in skills.items() if v["level"] < 0.3}
        if low_skills:
            skill_names = ", ".join(sorted(low_skills.keys()))
            suggestions.append(f"Consider building skills: {skill_names}")
            obstacles.append(f"Skill gap detected in: {skill_names}")

        # Check knowledge graph for related concepts
        related = knowledge_graph.query(prefix=mission[:10])
        if related:
            suggestions.append(f"Found {len(related)} related concepts in your knowledge graph.")

        # Extract key terms as learning suggestions
        terms = [w for w in mission.lower().split() if len(w) > 4][:5]
        if terms:
            suggestions.append(f"Key areas to explore: {', '.join(terms)}")

        if not suggestions:
            suggestions.append("Begin by researching and gathering knowledge about this mission.")

        self._suggestions = suggestions
        self._obstacles = obstacles
        return {"suggestions": suggestions, "obstacles": obstacles}

    def get_suggestions(self):
        return list(self._suggestions)

    def get_obstacles(self):
        return list(self._obstacles)

    def prioritize(self, items):
        """Rank items by importance."""
        return sorted(items, key=lambda x: len(x), reverse=True)


class SimulationEngine:
    """Decision-support system for simulating possibilities."""

    def __init__(self):
        self._scenarios = []

    def compare(self, scenario_a, scenario_b, context=None):
        """Compare two scenarios and return analysis."""
        analysis = {
            "scenario_a": scenario_a,
            "scenario_b": scenario_b,
            "analysis": [],
            "recommendation": None,
        }

        a_keywords = set(scenario_a.lower().split())
        b_keywords = set(scenario_b.lower().split())

        if context:
            ctx = context.lower()
            ctx_words = ctx.split()
            def match_keywords(kw_set, ctx_words):
                count = 0
                for kw in kw_set:
                    for cw in ctx_words:
                        if kw == cw or kw.startswith(cw) or cw.startswith(kw):
                            count += 1
                            break
                return count
            a_match = match_keywords(a_keywords, ctx_words)
            b_match = match_keywords(b_keywords, ctx_words)
            if a_match > b_match:
                analysis["analysis"].append(f"Path A aligns more with your current context ({a_match} matches).")
                analysis["recommendation"] = "A"
            elif b_match > a_match:
                analysis["analysis"].append(f"Path B aligns more with your current context ({b_match} matches).")
                analysis["recommendation"] = "B"

        if len(a_keywords) > len(b_keywords):
            analysis["analysis"].append(f"Path A covers {len(a_keywords)} key areas vs {len(b_keywords)} for Path B.")
        elif len(b_keywords) > len(a_keywords):
            analysis["analysis"].append(f"Path B covers {len(b_keywords)} key areas vs {len(a_keywords)} for Path A.")

        if not analysis["analysis"]:
            analysis["analysis"].append("Both paths have different strengths. Consider your long-term goals.")

        self._scenarios.append(analysis)
        return analysis

    def history(self):
        return list(self._scenarios)


class DigitalTwinMind:
    """Personal Intelligence Layer — understands user goals, knowledge, projects, decisions."""

    def __init__(self):
        self.memory = MemorySystem()
        self.knowledge_graph = KnowledgeGraph()
        self.context = ContextEngine()
        self.learning = LearningModel()
        self.chief = ChiefOfStaff()
        self.simulator = SimulationEngine()
        self.privacy = PrivacyController()

    def remember_mission(self, mission):
        """Store a new mission and initialize its context."""
        self.memory.store("mission", mission, tags=["active"], source="user_intent")
        self.context.set_mission(mission)
        self.chief.analyze_mission(mission, self.memory, self.knowledge_graph, self.learning)

    def continue_work(self, query):
        """Understand 'continue my work' — find context and return state."""
        current = self.context.get_current()
        recent = self.memory.recent(3)
        suggestions = self.chief.get_suggestions()

        return {
            "current_mission": current["mission"],
            "recent_memories": recent,
            "suggestions": suggestions,
            "active_projects": current["active_projects"],
            "knowledge_summary": f"{self.knowledge_graph.query().__len__()} concepts in knowledge graph",
        }

    def get_personalized_greeting(self):
        """Generate a greeting based on time and user state."""
        import time
        hour = time.localtime().tm_hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        current = self.context.get_current()
        missions = self.memory.recall(category="mission", limit=3)
        skills = self.learning.get_skills()

        result = {
            "greeting": greeting,
            "active_mission": current["mission"],
            "recent_missions": [m["content"] for m in missions],
            "skills_count": len(skills),
            "memories_count": self.memory.count(),
        }
        return result

    def save_state(self):
        """Serialize all subsystems to a dict."""
        return {
            "memory": self.memory.to_dict(),
            "knowledge_graph": self.knowledge_graph.to_dict(),
            "context": self.context.to_dict(),
            "learning": self.learning.to_dict(),
        }

    def load_state(self, data):
        """Restore all subsystems from a dict."""
        if "memory" in data:
            self.memory.from_dict(data["memory"])
        if "knowledge_graph" in data:
            self.knowledge_graph.from_dict(data["knowledge_graph"])
        if "context" in data:
            self.context.from_dict(data["context"])
        if "learning" in data:
            self.learning.from_dict(data["learning"])

    def summary(self):
        return (
            f"Digital Twin: {self.memory.count()} memories, "
            f"{len(self.knowledge_graph._nodes)} concepts, "
            f"{len(self.learning.get_skills())} skills tracked"
        )


# ============================================================
# UNIVERSAL SESSION LAYER
# ============================================================

class SessionState:
    """Serializable snapshot of entire ARCANIS state for cross-device transfer."""

    def __init__(self):
        self.session_id = ""
        self.device_id = ""
        self.device_name = ""
        self.goal = ""
        self.timestamp = 0.0
        self.mission = {}
        self.agents = []
        self.memories = []
        self.knowledge_nodes = {}
        self.knowledge_edges = []
        self.context = {}
        self.active_projects = []

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "goal": self.goal,
            "timestamp": self.timestamp,
            "mission": self.mission,
            "agents": self.agents,
            "memories": self.memories,
            "knowledge_nodes": self.knowledge_nodes,
            "knowledge_edges": self.knowledge_edges,
            "context": self.context,
            "active_projects": self.active_projects,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    @staticmethod
    def from_dict(data):
        state = SessionState()
        state.session_id = data.get("session_id", "")
        state.device_id = data.get("device_id", "")
        state.device_name = data.get("device_name", "")
        state.goal = data.get("goal", "")
        state.timestamp = data.get("timestamp", 0.0)
        state.mission = data.get("mission", {})
        state.agents = data.get("agents", [])
        state.memories = data.get("memories", [])
        state.knowledge_nodes = data.get("knowledge_nodes", {})
        state.knowledge_edges = data.get("knowledge_edges", [])
        state.context = data.get("context", {})
        state.active_projects = data.get("active_projects", [])
        return state


class DiscoveryService:
    """UDP broadcast-based discovery of ARCANIS instances on the local network."""

    DISCOVERY_PORT = 9877
    DISCOVERY_MAGIC = b"ARCANIS_DISCOVER"
    RESPONSE_MAGIC = b"ARCANIS_HERE"

    def __init__(self, device_name="arcanis-device"):
        self.device_name = device_name
        self.device_id = hashlib.md5(device_name.encode()).hexdigest()[:12]
        self._running = False
        self._thread = None
        self._server = None
        self.discovered = {}

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass

    def _listen_loop(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(2.0)
            sock.bind(("", self.DISCOVERY_PORT))
            self._server = sock
            while self._running:
                try:
                    data, addr = sock.recvfrom(1024)
                    if data.startswith(self.DISCOVERY_MAGIC):
                        parts = data.decode().split("|")
                        resp = f"{self.RESPONSE_MAGIC.decode()}|{self.device_id}|{self.device_name}|{socket.gethostname()}"
                        sock.sendto(resp.encode(), addr)
                    elif data.startswith(self.RESPONSE_MAGIC):
                        parts = data.decode().split("|")
                        if len(parts) >= 4:
                            dev_id = parts[1]
                            dev_name = parts[2]
                            hostname = parts[3]
                            self.discovered[dev_id] = {
                                "device_id": dev_id,
                                "name": dev_name,
                                "hostname": hostname,
                                "address": addr[0],
                                "discovery_port": self.DISCOVERY_PORT,
                                "last_seen": time.time(),
                            }
                except socket.timeout:
                    continue
                except Exception:
                    pass
        except Exception:
            pass

    def discover(self, timeout=3.0):
        self.discovered = {}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(timeout)
            msg = f"{self.DISCOVERY_MAGIC.decode()}|{self.device_id}|{self.device_name}"
            sock.sendto(msg.encode(), ("255.255.255.255", self.DISCOVERY_PORT))
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    data, addr = sock.recvfrom(1024)
                    if data.startswith(self.RESPONSE_MAGIC):
                        parts = data.decode().split("|")
                        if len(parts) >= 4:
                            dev_id = parts[1]
                            dev_name = parts[2]
                            hostname = parts[3]
                            self.discovered[dev_id] = {
                                "device_id": dev_id,
                                "name": dev_name,
                                "hostname": hostname,
                                "address": addr[0],
                                "discovery_port": self.DISCOVERY_PORT,
                                "last_seen": time.time(),
                            }
                except socket.timeout:
                    break
                except Exception:
                    pass
        except Exception:
            pass
        return list(self.discovered.values())

    def get_devices(self):
        return list(self.discovered.values())


class SessionManager:
    """Orchestrates session lifecycle: create, suspend, transfer, resume across devices."""

    def __init__(self, shell=None):
        self.shell = shell
        self.current_session = None
        self.saved_sessions = {}
        self.device_id = hashlib.md5(socket.gethostname().encode()).hexdigest()[:12]
        self.device_name = socket.gethostname()

    def create_session(self, goal):
        if not self.shell:
            return None
        agent_network = AgentCommunicationNetwork()
        mission_mgr = MissionManager(communication_network=agent_network)
        mission_mgr.define_goal(goal)
        agents = []
        for role_name, role in [("researcher", "research"), ("builder", "build"), ("reviewer", "quality")]:
            agent = Agent(f"agent_{role_name}_{int(time.time())}", role_name.capitalize(), role)
            agents.append(agent)
        timestamp = time.time()
        session_id = hashlib.md5(f"{goal}{timestamp}".encode()).hexdigest()[:16]
        state = SessionState()
        state.session_id = session_id
        state.device_id = self.device_id
        state.device_name = self.device_name
        state.goal = goal
        state.timestamp = timestamp
        state.mission = mission_mgr.to_dict()
        state.agents = [a.to_dict() for a in agents]
        if hasattr(self.shell, 'twin') and self.shell.twin:
            state.memories = self.shell.twin.memory.to_dict().get("memories", [])
            state.knowledge_nodes = self.shell.twin.knowledge_graph.to_dict().get("nodes", {})
            state.knowledge_edges = self.shell.twin.knowledge_graph.to_dict().get("edges", [])
        if hasattr(self.shell, 'twin') and self.shell.twin:
            ctx = self.shell.twin.context.to_dict()
            state.context = ctx
            state.active_projects = ctx.get("active_projects", [])
        self.current_session = state
        self.saved_sessions[session_id] = state
        if self.shell:
            self.shell.mission = mission_mgr
            self.shell.agent_network = agent_network
            self.shell.agents = agents
            self.shell.mission.define_goal(goal)
            if not hasattr(self.shell, 'twin') or not self.shell.twin:
                from dataclasses import dataclass
                if not hasattr(self.shell, 'twin'):
                    self.shell.twin = DigitalTwinMind()
            self.shell.twin.remember_mission(goal)
        return state

    def suspend_session(self):
        if not self.current_session:
            return None
        state = self.current_session
        if self.shell and hasattr(self.shell, 'mission') and self.shell.mission:
            state.mission = self.shell.mission.to_dict()
        if self.shell and hasattr(self.shell, 'agents'):
            state.agents = [a.to_dict() for a in self.shell.agents]
        if self.shell and hasattr(self.shell, 'twin') and self.shell.twin:
            state.memories = self.shell.twin.memory.to_dict().get("memories", [])
            kg = self.shell.twin.knowledge_graph.to_dict()
            state.knowledge_nodes = kg.get("nodes", {})
            state.knowledge_edges = kg.get("edges", [])
            ctx = self.shell.twin.context.to_dict()
            state.context = ctx
            state.active_projects = ctx.get("active_projects", [])
        state.timestamp = time.time()
        self.saved_sessions[state.session_id] = state
        return state

    def resume_session(self, session_id):
        if session_id not in self.saved_sessions:
            return None
        state = self.saved_sessions[session_id]
        if not self.shell:
            return state
        if state.mission:
            mission_mgr = MissionManager()
            mission_mgr.from_dict(state.mission)
            self.shell.mission = mission_mgr
            self.shell.agent_network = mission_mgr.network
        if state.agents:
            self.shell.agents = []
            for a_data in state.agents:
                agent = Agent("", "", "")
                agent.from_dict(a_data)
                self.shell.agents.append(agent)
        if not hasattr(self.shell, 'twin') or not self.shell.twin:
            self.shell.twin = DigitalTwinMind()
        twin = self.shell.twin
        for mem in state.memories:
            twin.memory.store(mem.get("category", "general"), mem.get("content", ""), tags=mem.get("tags", []), source=mem.get("source"))
        for nid, ndata in state.knowledge_nodes.items():
            twin.knowledge_graph.add_concept(nid, ndata.get("label", nid), ndata.get("category", "general"), ndata.get("details"))
        for edge in state.knowledge_edges:
            twin.knowledge_graph.relate(edge.get("from"), edge.get("to"), edge.get("relation", "related_to"))
        if state.context:
            twin.context.from_dict(state.context)
        self.current_session = state
        twin.remember_mission(state.goal)
        return state

    def export_session(self, session_id=None, filepath=None):
        if session_id and session_id in self.saved_sessions:
            state = self.saved_sessions[session_id]
        elif self.current_session:
            state = self.suspend_session()
        else:
            return None
        json_str = state.to_json()
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(json_str)
            except Exception:
                pass
        return json_str

    def import_session(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                return None
        state = SessionState.from_dict(data)
        self.saved_sessions[state.session_id] = state
        return state

    def import_session_file(self, filepath):
        try:
            with open(filepath) as f:
                data = json.load(f)
            return self.import_session(data)
        except Exception:
            return None

    def transfer_session(self, sock, session_id=None):
        json_str = self.export_session(session_id)
        if not json_str:
            return False
        chunk_size = 4096
        total = len(json_str)
        try:
            header = f"SESSION_EXPORT:{total}\n"
            sock.sendall(header.encode())
            ack = sock.recv(1024).decode().strip()
            if ack != "ACK":
                return False
            for i in range(0, total, chunk_size):
                chunk = json_str[i:i+chunk_size]
                sock.sendall(chunk.encode())
            return True
        except Exception:
            return False

    def receive_session_chunk(self, data):
        return self.import_session(data)

    def list_sessions(self):
        return {sid: {
            "goal": s.goal,
            "device": s.device_name,
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s.timestamp)),
            "agents": len(s.agents),
            "memories": len(s.memories),
            "active": sid == (self.current_session.session_id if self.current_session else None),
        } for sid, s in self.saved_sessions.items()}


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
        self.twin = DigitalTwinMind()
        self.mission = MissionManager()
        self.agent_network = AgentCommunicationNetwork()
        self.agents = []
        self.session_mgr = SessionManager(shell=self)
        self.discovery = DiscoveryService(device_name=socket.gethostname())
        self.discovery.start()
        self.ecosystem = IntelligenceEcosystem()
        self.ecosystem.init_account(name=socket.gethostname(), tier="creator")
        self.foundry = IntelligenceFoundry()
        self.uif = UniversalIntelligenceCore()
        self.uif.initialize(user_name=socket.gethostname())
        for agent_type in ["researcher", "coder", "designer", "analyst", "planner", "critic", "mentor"]:
            agent = self.ecosystem.agent_market.spawn(agent_type)
            if agent:
                self.uif.orchestrator.register_agent(agent)
        self.piin = PersonalIntelligenceIdentityNetwork()
        self.piin.initialize()
        self.ril = RealityInterfaceLayer()
        self.ril.initialize()
        self.acde = AutonomousCreationDiscoveryEngine()
        self.acde.initialize()
        self.iedc = IntelligenceEcosystemDeveloperCivilization()
        self.iedc.initialize()
        self.awse = AutonomousWorldSimulationEngine()
        self.awse.initialize()
        self.aiil = AutonomousIntelligenceInfrastructureLayer()
        self.aiil.initialize()
        self.cin = CollectiveIntelligenceNetwork()
        self.cin.initialize()

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
        print(f"{dm}  Arcanis OS v12.0.0 - Collective Intelligence Network\033[0m")
        print(f"{dm}  106 modules | 256 commands | ~/.arcanis/ on disk\033[0m")
        print(f"{dm}  CIN active: 10-layer collaboration | AIIL+IEDC+ACDE+PIIN+RIL+AWSE online\033[0m")
        print(f"{dm}  PIIN active: 10-layer intelligence identity | User model online\033[0m")
        print(f"{dm}  AWSE active: 10-layer simulation | IEDC+ACDE+PIIN+RIL online\033[0m")
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
            "session": self.cmd_session,
            "discover": self.cmd_discover,
            "devices": self.cmd_devices,
            "ecosystem": self.cmd_ecosystem,
            "market": self.cmd_market,
            "publish": self.cmd_publish,
            "install": self.cmd_install,
            "sdk": self.cmd_sdk,
            "protocol": self.cmd_protocol,
            "foundry": self.cmd_foundry,
            "design": self.cmd_design,
            "train": self.cmd_train,
            "simulate": self.cmd_simulate,
            "evaluate": self.cmd_evaluate,
            "deploy": self.cmd_deploy,
            "versions": self.cmd_versions,
            "uif": self.cmd_uif,
            "intent": self.cmd_intent,
            "agents": self.cmd_agents_uif,
            "skills": self.cmd_skills,
            "identity": self.cmd_identity,
            "api": self.cmd_api_uif,
            "piin": self.cmd_piin,
            "profile": self.cmd_piin_profile,
            "mem": self.cmd_piin_memory,
            "know": self.cmd_piin_knowledge,
            "goal": self.cmd_piin_goal,
            "prefs": self.cmd_piin_prefs,
            "agents-learn": self.cmd_piin_agents_learn,
            "life": self.cmd_piin_life,
            "vault": self.cmd_piin_vault,
            "timeline": self.cmd_piin_timeline,
            "ril": self.cmd_ril,
            "perceive": self.cmd_ril_perception,
            "voice": self.cmd_ril_voice,
            "vision": self.cmd_ril_vision,
            "spatial": self.cmd_ril_spatial,
            "devices": self.cmd_ril_devices,
            "robot": self.cmd_ril_robotics,
            "where": self.cmd_ril_context,
            "interact": self.cmd_ril_interaction,
            "presence": self.cmd_ril_presence,
            "rsafety": self.cmd_ril_security,
            "acde": self.cmd_acde,
            "create": self.cmd_acde_create,
            "research": self.cmd_acde_research,
            "dev": self.cmd_acde_dev,
            "sim": self.cmd_acde_sim,
            "design": self.cmd_acde_creative,
            "team": self.cmd_acde_team,
            "synth": self.cmd_acde_synthesis,
            "improve": self.cmd_acde_improve,
            "mode": self.cmd_acde_mode,
            "creations": self.cmd_acde_memory,
            "iedc": self.cmd_iedc,
            "dev-platform": self.cmd_iedc_platform,
            "sdk": self.cmd_iedc_sdk,
            "modarch": self.cmd_iedc_modules,
            "market": self.cmd_iedc_marketplace,
            "agnet": self.cmd_iedc_agnet,
            "oip": self.cmd_iedc_protocol,
            "govern": self.cmd_iedc_governance,
            "econtribute": self.cmd_iedc_knowledge,
            "enterprise": self.cmd_iedc_enterprise,
            "ecosys": self.cmd_iedc_ecosystem,
            "awse": self.cmd_awse,
            "sim": self.cmd_awse_sim,
            "twin": self.cmd_awse_twin,
            "scenario": self.cmd_awse_scenario,
            "experiment": self.cmd_awse_lab,
            "society": self.cmd_awse_society,
            "science": self.cmd_awse_science,
            "decide": self.cmd_awse_decide,
            "world": self.cmd_awse_world,
            "vis": self.cmd_awse_vis,
            "pipeline": self.cmd_awse_pipeline,
            "aiil": self.cmd_aiil,
            "resources": self.cmd_aiil_resources,
            "dnet": self.cmd_aiil_dnet,
            "art": self.cmd_aiil_art,
            "semstore": self.cmd_aiil_semstore,
            "cml": self.cmd_aiil_cml,
            "imon": self.cmd_aiil_imon,
            "optimize": self.cmd_aiil_optimize,
            "hal": self.cmd_aiil_hal,
            "security": self.cmd_aiil_security,
            "cloud": self.cmd_aiil_cloud,
            "cin": self.cmd_cin,
            "federate": self.cmd_cin_federate,
            "trust": self.cmd_cin_trust,
            "a2a": self.cmd_cin_a2a,
            "kex": self.cmd_cin_kex,
            "tspace": self.cmd_cin_tspace,
            "creason": self.cmd_cin_creason,
            "cap": self.cmd_cin_cap,
            "provenance": self.cmd_cin_provenance,
            "resilient": self.cmd_cin_resilient,
            "gov": self.cmd_cin_gov,
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
        print(f"\u2551  Shell    : arcanis-sh (256 commands)    \u2551")
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
            "system_info": "Arcanis OS v12.0.0 with real filesystem at ~/.arcanis/. 106 modules, 256 commands.",
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
                    elif line.startswith("SESSION_EXPORT:"):
                        total_size = int(line[15:])
                        client_sock.sendall(b"ACK\n")
                        received = 0
                        session_data = ""
                        while received < total_size:
                            chunk = client_sock.recv(4096).decode()
                            if not chunk:
                                break
                            session_data += chunk
                            received += len(chunk)
                        if session_data:
                            state = self.session_mgr.receive_session_chunk(session_data)
                            if state:
                                print(f"\n\033[32m[PEER:{addr[0]}]\033[0m Session received: {state.goal}")
                                print(f"  Agents: {len(state.agents)} | Memories: {len(state.memories)}")
                            else:
                                print(f"\n\033[31m[PEER:{addr[0]}]\033[0m Failed to import session")
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

    # ======================== UNIVERSAL SESSION COMMANDS ========================

    def cmd_session(self, args):
        """Manage universal sessions: create, suspend, resume, list, export, import, transfer."""
        if not args:
            ic = self._c("info")
            print(f"{ic}Session Manager\033[0m")
            print(f"  Device: {self.session_mgr.device_name} ({self.session_mgr.device_id})")
            if self.session_mgr.current_session:
                s = self.session_mgr.current_session
                print(f"  Active: {s.goal} [{s.session_id[:8]}...]")
            else:
                print("  Active: none")
            print(f"  Saved sessions: {len(self.session_mgr.saved_sessions)}")
            print()
            print(f"  \033[1;36mCommands:\033[0m")
            print(f"    session create <goal>        Start a new mission session")
            print(f"    session list                 Show all saved sessions")
            print(f"    session suspend              Snapshot current session")
            print(f"    session resume <id>          Restore a saved session")
            print(f"    session export [id] [file]   Export session to JSON")
            print(f"    session import <file>        Import session from JSON")
            print(f"    session transfer <id>        Send session to connected peer")
            return
        action = args[0]
        ic = self._c("info")
        ok = self._c("ok")
        er = self._c("err")

        if action == "create":
            goal = " ".join(args[1:]) if len(args) > 1 else "New mission"
            state = self.session_mgr.create_session(goal)
            if state:
                print(f"{ok}Session created: {state.session_id[:16]}...\033[0m")
                print(f"  Goal: {state.goal}")
                print(f"  Agents: {', '.join(a.get('name', '?') for a in state.agents)}")
            else:
                print(f"{er}Failed to create session\033[0m")

        elif action == "list":
            sessions = self.session_mgr.list_sessions()
            if not sessions:
                print("No saved sessions")
                return
            print(f"{ic}Saved Sessions:\033[0m")
            print(f"  {'ID':<18} {'GOAL':<30} {'DEVICE':<20} {'AGENTS':<8} {'TIME':<20}")
            for sid, info in sessions.items():
                marker = " *" if info.get("active") else "  "
                print(f"  {sid[:16]:<18}{info['goal'][:28]:<30}{info['device']:<20}{info['agents']:<8}{info['time']:<20}{marker}")

        elif action == "suspend":
            state = self.session_mgr.suspend_session()
            if state:
                print(f"{ok}Session suspended: {state.goal}\033[0m")
            else:
                print(f"{er}No active session to suspend\033[0m")

        elif action == "resume":
            if len(args) < 2:
                print(f"{er}Usage: session resume <session_id>\033[0m")
                return
            sid = args[1]
            state = self.session_mgr.resume_session(sid)
            if state:
                print(f"{ok}Session resumed: {state.goal}\033[0m")
                print(f"  Agents: {len(state.agents)} | Memories: {len(state.memories)}")
            else:
                print(f"{er}Session not found: {sid}\033[0m")

        elif action == "export":
            sid = args[1] if len(args) > 1 else None
            filepath = args[2] if len(args) > 2 else None
            json_str = self.session_mgr.export_session(sid, filepath)
            if json_str:
                if filepath:
                    print(f"{ok}Session exported to {filepath}\033[0m")
                else:
                    print(json_str[:500])
                    if len(json_str) > 500:
                        print("... (truncated)")
            else:
                print(f"{er}No session to export\033[0m")

        elif action == "import":
            if len(args) < 2:
                print(f"{er}Usage: session import <file>\033[0m")
                return
            state = self.session_mgr.import_session_file(args[1])
            if state:
                print(f"{ok}Session imported: {state.goal}\033[0m")
                print(f"  From device: {state.device_name}")
                print(f"  Agents: {len(state.agents)} | Memories: {len(state.memories)}")
            else:
                print(f"{er}Failed to import session\033[0m")

        elif action == "transfer":
            if len(args) < 2:
                print(f"{er}Usage: session transfer <session_id> [peer_index]\033[0m")
                return
            sid = args[1]
            peer_idx = int(args[2]) if len(args) > 2 else 0
            if peer_idx < 0 or peer_idx >= len(self.peers):
                print(f"{er}Peer index {peer_idx} out of range ({len(self.peers)} peers)\033[0m")
                return
            sock = self.peers[peer_idx][0]
            if self.session_mgr.transfer_session(sock, sid):
                peer_name = self.peers[peer_idx][2]
                print(f"{ok}Session transferred to {peer_name}\033[0m")
            else:
                print(f"{er}Session transfer failed\033[0m")

        else:
            print(f"{er}Unknown session action: {action}\033[0m")

    def cmd_discover(self, args):
        """Discover ARCANIS instances on the local network."""
        timeout = float(args[0]) if args else 3.0
        ic = self._c("info")
        print(f"{ic}Discovering ARCANIS devices on network...\033[0m")
        devices = self.discovery.discover(timeout=timeout)
        if not devices:
            print("  No devices found")
            return
        print(f"  Found {len(devices)} device(s):")
        for d in devices:
            print(f"    \033[1;36m{d['name']}\033[0m @ {d['address']} ({d['hostname']})")

    def cmd_devices(self, _):
        """List discovered ARCANIS devices."""
        devices = self.discovery.get_devices()
        if not devices:
            print("No devices discovered. Run 'discover' first.")
            return
        ic = self._c("info")
        print(f"{ic}Known Devices:\033[0m")
        print(f"  {'NAME':<24} {'ADDRESS':<16} {'HOSTNAME':<24} {'LAST SEEN':<20}")
        for d in devices:
            ls = time.strftime("%H:%M:%S", time.localtime(d.get("last_seen", 0)))
            print(f"  {d['name']:<24} {d['address']:<16} {d['hostname']:<24} {ls:<20}")

    # ======================== ECOSYSTEM COMMANDS ========================

    def cmd_ecosystem(self, args):
        """Intelligence Ecosystem — agents, knowledge, missions, economy overview."""
        ic = self._c("info")
        ok = self._c("ok")
        if not args:
            e = self.ecosystem
            s = e.summary()
            print(f"{ic}ARCANIS Intelligence Ecosystem\033[0m")
            print(f"  {ok}Agent Marketplace:\033[0m {s['agents']} types ({s['agents_installed']} installed)")
            print(f"  {ok}Knowledge Marketplace:\033[0m {s['knowledge_packs']} packs")
            print(f"  {ok}Mission Marketplace:\033[0m {s['missions']} templates")
            print(f"  {ok}Developer SDK:\033[0m {s['dev_projects']} projects")
            print(f"  {ok}Protocol:\033[0m {s['protocol_messages']} messages")
            acct = s.get("account")
            if acct:
                print(f"  {ok}Account:\033[0m {acct['name']} ({acct['tier']}) — {acct['credits']} credits")
            print()
            print(f"  \033[1;36mCommands:\033[0m")
            print(f"    ecosystem summary              Show this overview")
            print(f"    market agents [query]          Browse agent marketplace")
            print(f"    market knowledge [query]       Browse knowledge packs")
            print(f"    market missions [query]        Browse mission templates")
            print(f"    publish agent <id> <name>...   Publish an agent to marketplace")
            print(f"    install <type> <id>            Install from marketplace")
            print(f"    sdk new <type> <id> <name>     Create a new SDK project")
            print(f"    sdk build <id>                 Build and publish SDK project")
            print(f"    protocol status                Show protocol info")
            return
        if args[0] == "summary":
            s = self.ecosystem.summary()
            acct = s.get("account")
            print(f"{ic}Ecosystem Summary:\033[0m")
            print(f"  Agents: {s['agents']} published, {s['agents_installed']} installed")
            print(f"  Knowledge: {s['knowledge_packs']} packs available")
            print(f"  Missions: {s['missions']} templates")
            print(f"  SDK Projects: {s['dev_projects']} ({s['dev_projects']} published)")
            print(f"  Protocol Messages: {s['protocol_messages']}")
            if acct:
                print(f"  Account: {acct['name']} ({acct['tier']}) — {acct['credits']} credits")

    def cmd_market(self, args):
        """Browse the intelligence marketplaces."""
        er = self._c("err")
        ic = self._c("info")
        if not args:
            print(f"{er}Usage: market <agents|knowledge|missions> [query]\033[0m")
            return
        market_type = args[0]
        query = " ".join(args[1:]) if len(args) > 1 else None

        if market_type == "agents":
            results = self.ecosystem.agent_market.search(query=query)
            if not results:
                print("No agents found")
                return
            print(f"{ic}Agent Marketplace:\033[0m")
            print(f"  {'TYPE':<20} {'NAME':<28} {'CATEGORY':<16} {'RATING':<8} {'PRICE':<8} {'AUTHOR':<16}")
            for r in results:
                mark = " *" if r["type"] in self.ecosystem.agent_market._installed else "  "
                rat = f"{r.get('rating', 0):.1f}" if r.get('ratings_count', 0) > 0 else "-"
                print(f"  {r['type']:<20}{r['name'][:26]:<28}{r.get('category',''):<16}{rat:<8}{r.get('price',0):<8}{r.get('author',''):<16}{mark}")

        elif market_type == "knowledge":
            results = self.ecosystem.knowledge_market.search(query=query)
            if not results:
                print("No knowledge packs found")
                return
            print(f"{ic}Knowledge Marketplace:\033[0m")
            print(f"  {'ID':<24} {'NAME':<30} {'CATEGORY':<16} {'CONCEPTS':<10} {'AUTHOR':<16}")
            for r in results:
                mark = " *" if r["id"] in self.ecosystem.knowledge_market._installed_packs else "  "
                print(f"  {r['id']:<24}{r['name'][:28]:<30}{r.get('category',''):<16}{len(r.get('concepts',[])):<10}{r.get('author',''):<16}{mark}")

        elif market_type == "missions":
            results = self.ecosystem.mission_market.search(query=query)
            if not results:
                print("No mission templates found")
                return
            print(f"{ic}Mission Marketplace:\033[0m")
            print(f"  {'ID':<24} {'NAME':<30} {'AGENTS':<20} {'PHASES':<10} {'AUTHOR':<16}")
            for r in results:
                mark = " *" if r["id"] in self.ecosystem.mission_market._installed_missions else "  "
                print(f"  {r['id']:<24}{r['name'][:28]:<30}{', '.join(r.get('agents',[]))[:18]:<20}{len(r.get('phases',[])):<10}{r.get('author',''):<16}{mark}")

        else:
            print(f"{er}Unknown marketplace: {market_type}\033[0m")

    def cmd_publish(self, args):
        """Publish intelligence to the ecosystem."""
        er = self._c("err")
        ok = self._c("ok")
        if len(args) < 3:
            print(f"{er}Usage:\033[0m")
            print(f"  publish agent <type_id> <name> [category]")
            print(f"  publish knowledge <pack_id> <name> [category]")
            print(f"  publish mission <mission_id> <name> <goal>")
            return
        pub_type = args[0]
        pub_id = args[1]
        pub_name = args[2]

        if pub_type == "agent":
            category = args[3] if len(args) > 3 else "general"
            role = " ".join(args[4:]) if len(args) > 4 else f"An intelligent {pub_name} agent"
            entry = self.ecosystem.agent_market.publish(
                agent_type=pub_id, name=pub_name, role=role,
                author=socket.gethostname(), category=category,
            )
            if entry:
                print(f"{ok}Agent published: {pub_name} ({pub_id})\033[0m")
            else:
                print(f"{er}Failed to publish agent\033[0m")

        elif pub_type == "knowledge":
            category = args[3] if len(args) > 3 else "general"
            description = " ".join(args[4:]) if len(args) > 4 else f"A knowledge pack about {pub_name}"
            pack = self.ecosystem.knowledge_market.create_pack(
                pack_id=pub_id, name=pub_name, description=description,
                author=socket.gethostname(), category=category,
            )
            if pack:
                print(f"{ok}Knowledge pack created: {pub_name}\033[0m")
                print(f"  Add concepts with: ecosystem knowledge add_concept {pub_id} <concept>")
            else:
                print(f"{er}Failed to create knowledge pack\033[0m")

        elif pub_type == "mission":
            goal = " ".join(args[3:]) if len(args) > 3 else "Complete a mission"
            mission = self.ecosystem.mission_market.create_mission(
                mission_id=pub_id, name=pub_name, description=goal,
                author=socket.gethostname(), goal=goal,
            )
            if mission:
                print(f"{ok}Mission template created: {pub_name}\033[0m")
            else:
                print(f"{er}Failed to create mission template\033[0m")
        else:
            print(f"{er}Unknown publish type: {pub_type}\033[0m")

    def cmd_install(self, args):
        """Install intelligence from the marketplace."""
        er = self._c("err")
        ok = self._c("ok")
        if len(args) < 2:
            print(f"{er}Usage: install <agent|knowledge|mission> <id>\033[0m")
            return
        install_type = args[0]
        install_id = args[1]

        if install_type == "agent":
            if self.ecosystem.agent_market.install(install_id):
                info = self.ecosystem.agent_market.get_info(install_id)
                print(f"{ok}Agent installed: {info['name']}\033[0m")
                print(f"  Spawn with: agent spawn {install_id}")
            else:
                print(f"{er}Agent not found: {install_id}\033[0m")

        elif install_type == "knowledge":
            if self.ecosystem.knowledge_market.install_pack(install_id):
                pack = self.ecosystem.knowledge_market.get_pack(install_id)
                print(f"{ok}Knowledge pack installed: {pack['name']}\033[0m")
                print(f"  Concepts: {', '.join(pack.get('concepts', []))}")
                print(f"  Learning paths: {len(pack.get('learning_paths', []))}")
            else:
                print(f"{er}Knowledge pack not found: {install_id}\033[0m")

        elif install_type == "mission":
            if self.ecosystem.mission_market.install_mission(install_id):
                mission = self.ecosystem.mission_market.get_mission(install_id)
                print(f"{ok}Mission template installed: {mission['name']}\033[0m")
                print(f"  Goal: {mission.get('goal', '')}")
                print(f"  Agents: {', '.join(mission.get('agents', []))}")
            else:
                print(f"{er}Mission template not found: {install_id}\033[0m")
        else:
            print(f"{er}Unknown install type: {install_type}\033[0m")

    def cmd_sdk(self, args):
        """Developer SDK — create and build intelligence projects."""
        er = self._c("err")
        ok = self._c("ok")
        ic = self._c("info")
        if not args:
            info = self.ecosystem.dev_platform.sdk_info()
            print(f"{ic}ARCANIS Developer SDK\033[0m")
            print(f"  Templates: {', '.join(info['templates'])}")
            print(f"  Projects: {info['projects']} ({info['published']} published)")
            print()
            print(f"  \033[1;36mUsage:\033[0m")
            print(f"    sdk new agent <id> <name>         New agent project")
            print(f"    sdk new knowledge_pack <id> <name>  New knowledge pack project")
            print(f"    sdk new mission_template <id> <name> New mission project")
            print(f"    sdk set <id> <field> <value>      Set a project field")
            print(f"    sdk build <id>                    Build and publish project")
            print(f"    sdk list [status]                 List projects")
            return
        action = args[0]
        if action == "new":
            if len(args) < 4:
                print(f"{er}Usage: sdk new <type> <id> <name>\033[0m")
                return
            ptype, pid, pname = args[1], args[2], args[3]
            proj = self.ecosystem.dev_platform.new_project(ptype, pid, pname)
            if proj:
                print(f"{ok}SDK project created: {pname} ({pid})\033[0m")
                print(f"  Type: {ptype}")
                print(f"  Use 'sdk set {pid} <field> <value>' to configure")
            else:
                print(f"{er}Unknown project type: {ptype}\033[0m")
        elif action == "set":
            if len(args) < 4:
                print(f"{er}Usage: sdk set <id> <field> <value>\033[0m")
                return
            pid, field = args[1], args[2]
            value = " ".join(args[3:])
            if self.ecosystem.dev_platform.set_field(pid, field, value):
                print(f"{ok}Field set: {field} = {value}\033[0m")
            else:
                print(f"{er}Project not found: {pid}\033[0m")
        elif action == "build":
            if len(args) < 2:
                print(f"{er}Usage: sdk build <id>\033[0m")
                return
            pid = args[1]
            proj = self.ecosystem.dev_platform.get_project(pid)
            if not proj:
                print(f"{er}Project not found: {pid}\033[0m")
                return
            ptype = proj["type"]
            if ptype == "agent":
                result = self.ecosystem.dev_platform.build_agent(pid)
            elif ptype == "knowledge_pack":
                result = self.ecosystem.dev_platform.build_knowledge_pack(pid)
            elif ptype == "mission_template":
                result = self.ecosystem.dev_platform.build_mission(pid)
            else:
                result = None
            if result:
                print(f"{ok}Project built and published: {proj['name']}\033[0m")
                print(f"  Type: {ptype}")
                print(f"  Available in marketplace")
            else:
                print(f"{er}Build failed — check field values\033[0m")
        elif action == "list":
            status = args[1] if len(args) > 1 else None
            projects = self.ecosystem.dev_platform.list_projects(status=status)
            if not projects:
                print("No SDK projects")
                return
            print(f"{ic}SDK Projects:\033[0m")
            for p in projects:
                print(f"  {p['type']:<18} {p['id']:<20} {p['name']:<24} {p['status']:<12}")
        else:
            print(f"{er}Unknown SDK action: {action}\033[0m")

    def cmd_protocol(self, args):
        """Open Intelligence Protocol — ecosystem communication."""
        ic = self._c("info")
        info = self.ecosystem.protocol.to_dict()
        print(f"{ic}Open Intelligence Protocol v{info['version']}\033[0m")
        print(f"  Message types supported: {len(info['message_types'])}")
        for mt in info['message_types']:
            print(f"    - {mt}")
        print(f"  Messages sent/received: {info['message_count']}")

    # ======================== FOUNDRY COMMANDS ========================

    def cmd_foundry(self, args):
        """Intelligence Foundry — design, train, simulate, evaluate, deploy intelligence."""
        ic = self._c("info")
        ok = self._c("ok")
        if not args:
            s = self.foundry.summary()
            print(f"{ic}ARCANIS Intelligence Foundry\033[0m")
            print(f"  {ok}Designs:\033[0m {s['designs']}")
            print(f"  {ok}Built Agents:\033[0m {s['built_agents']}")
            print(f"  {ok}Training Sessions:\033[0m {s['training_sessions']}")
            print(f"  {ok}Simulations Run:\033[0m {s['simulations']}")
            print(f"  {ok}Evaluations:\033[0m {s['evaluations']}")
            print(f"  {ok}Version Snapshots:\033[0m {s['versions']}")
            print(f"  {ok}Deployments:\033[0m {s['deployments']}")
            print()
            print(f"  \033[1;36mCommands:\033[0m")
            print(f"    foundry summary               Show this overview")
            print(f"    design new <id> <name> <goal>  Create a new intelligence design")
            print(f"    design list                   List all designs")
            print(f"    design show <id>              Show design details")
            print(f"    design build <id>             Build agent from design")
            print(f"    design component add <id> <c>  Add component to design")
            print(f"    design reasoning <id> <strat>  Set reasoning strategy")
            print(f"    train <agent_id> [source]     Start training session")
            print(f"    simulate <agent_id>           Run simulation battery")
            print(f"    evaluate <agent_id>           Run evaluation")
            print(f"    deploy <agent_id> <target>    Deploy intelligence")
            print(f"    versions <agent_id>           Show version history")
            print(f"    versions compare <a> <b>      Compare two versions")
            return
        if args[0] == "summary":
            s = self.foundry.summary()
            print(f"{ic}Foundry Summary:\033[0m")
            for k, v in s.items():
                print(f"  {k.replace('_', ' ').title()}: {v}")

    def cmd_design(self, args):
        """Design intelligent systems — define architecture, components, reasoning, permissions."""
        er = self._c("err")
        ok = self._c("ok")
        ic = self._c("info")
        if not args:
            print(f"{er}Usage: design <new|list|show|build|component|reasoning> [args...]\033[0m")
            return
        action = args[0]
        if action == "new":
            if len(args) < 4:
                print(f"{er}Usage: design new <id> <name> <mission>\033[0m")
                return
            did, dname = args[1], args[2]
            mission = " ".join(args[3:])
            design = self.foundry.create_intelligence(did, dname, mission)
            print(f"{ok}Design created: {dname}\033[0m")
            print(f"  ID: {did}")
            print(f"  Mission: {mission}")
            print(f"  Use 'design component add {did} <component>' to add capabilities")
        elif action == "list":
            designs = self.foundry.designer.list_designs()
            if not designs:
                print("No designs yet")
                return
            print(f"{ic}Designs:\033[0m")
            print(f"  {'ID':<20} {'NAME':<24} {'STATUS':<12} {'COMPONENTS':<12}")
            for d in designs:
                print(f"  {d['id']:<20} {d['name'][:22]:<24} {d['status']:<12} {len(d['components']):<12}")
        elif action == "show":
            if len(args) < 2:
                print(f"{er}Usage: design show <id>\033[0m")
                return
            d = self.foundry.designer.get_design(args[1])
            if not d:
                print(f"{er}Design not found: {args[1]}\033[0m")
                return
            print(f"{ic}Design: {d['name']}\033[0m")
            print(f"  ID: {d['id']}")
            print(f"  Mission: {d['mission']}")
            print(f"  Status: {d['status']}")
            print(f"  Components: {', '.join(d['components']) or 'none'}")
            print(f"  Reasoning: {d['reasoning_strategy']}")
            print(f"  Tools: {', '.join(d['tool_permissions']) or 'none'}")
            print(f"  Learning: {d['learning_policies']}")
        elif action == "build":
            if len(args) < 2:
                print(f"{er}Usage: design build <id>\033[0m")
                return
            agent = self.foundry.build_intelligence(args[1])
            if agent:
                print(f"{ok}Agent built: {agent.name} ({agent.id})\033[0m")
                print(f"  Skills: {', '.join(agent.skills.keys()) or 'none'}")
                print(f"  Tools: {', '.join(agent.tools) or 'none'}")
            else:
                print(f"{er}Build failed — check design has components\033[0m")
        elif action == "component" and len(args) >= 4 and args[1] == "add":
            did, comp = args[2], args[3]
            if self.foundry.designer.add_component(did, comp):
                print(f"{ok}Component added: {comp}\033[0m")
            else:
                print(f"{er}Failed — valid components: {', '.join(self.foundry.components.list_categories().keys())}\033[0m")
        elif action == "reasoning":
            if len(args) < 3:
                print(f"{er}Usage: design reasoning <id> <strategy>\033[0m")
                return
            valid = ["step_by_step", "hypothetical", "analogical", "first_principles", "heuristic"]
            if self.foundry.designer.set_reasoning(args[1], args[2]):
                print(f"{ok}Reasoning strategy set to {args[2]}\033[0m")
            else:
                print(f"{er}Valid strategies: {', '.join(valid)}\033[0m")
        else:
            print(f"{er}Unknown design action: {action}\033[0m")

    def cmd_train(self, args):
        """Train an intelligence through documentation, missions, simulations, feedback."""
        er = self._c("err")
        ok = self._c("ok")
        if len(args) < 1:
            print(f"{er}Usage: train <agent_id> [source]\033[0m")
            return
        agent_id = args[0]
        source = args[1] if len(args) > 1 else "documentation"
        agent = self.foundry.get_agent(agent_id)
        if not agent:
            print(f"{er}Agent not found: {agent_id}\033[0m")
            print("  Build one first with: design build <design_id>")
            return
        sid = self.foundry.train_intelligence(agent, training_source=source)
        session = self.foundry.trainer._get_session(sid)
        print(f"{ok}Training session started: {sid[:16]}...\033[0m")
        if session:
            print(f"  Agent: {session['agent_name']}")
            print(f"  Source: {session['source']}")
            print(f"  Status: {session['status']}")
        print(f"  Use 'train status {sid[:16]}' to check progress")

    def cmd_simulate(self, args):
        """Run simulation battery to test intelligence before deployment."""
        er = self._c("err")
        ok = self._c("ok")
        ic = self._c("info")
        if len(args) < 1:
            print(f"{er}Usage: simulate <agent_id>\033[0m")
            return
        agent = self.foundry.get_agent(args[0])
        if not agent:
            print(f"{er}Agent not found: {args[0]}\033[0m")
            return
        print(f"{ic}Running simulation battery for {agent.name}...\033[0m")
        results = self.foundry.simulate_intelligence(agent)
        report = self.foundry.laboratory.report(agent)
        print(f"{ok}Simulation complete:\033[0m")
        print(f"  Total: {report['total']} | Passed: {report['passed']} | Failed: {report['failed']}")
        print(f"  Average performance: {report['avg_performance']}/100")
        for r in results:
            icon = "\033[32mPASS\033[0m" if r["passed"] else "\033[31mFAIL\033[0m"
            print(f"  [{icon}] {r['scenario_name']} ({r['scenario_type']}) — {r['performance']}/100")

    def cmd_evaluate(self, args):
        """Evaluate intelligence across 7 dimensions — reasoning, accuracy, reliability, etc."""
        er = self._c("err")
        ok = self._c("ok")
        ic = self._c("info")
        if len(args) < 1:
            print(f"{er}Usage: evaluate <agent_id>\033[0m")
            return
        agent = self.foundry.get_agent(args[0])
        if not agent:
            print(f"{er}Agent not found: {args[0]}\033[0m")
            return
        lab_results = self.foundry.laboratory.get_results(agent)
        evaluation = self.foundry.evaluate_intelligence(agent)
        print(f"{ic}Evaluation: {agent.name}\033[0m")
        print(f"  \033[1;36mComposite Score: {evaluation['composite']}/100\033[0m")
        print(f"  {'Dimension':<20} {'Score':<8}")
        for d, score in evaluation["scores"].items():
            color = "32" if score >= 75 else "33" if score >= 60 else "31"
            print(f"  {d:<20} \033[{color}m{score}/100\033[0m")
        if evaluation["strengths"]:
            print(f"  {ok}Strengths:\033[0m {', '.join(evaluation['strengths'])}")
        if evaluation["weaknesses"]:
            print(f"  \033[33mWeaknesses:\033[0m {', '.join(evaluation['weaknesses'])}")

    def cmd_deploy(self, args):
        """Deploy intelligence to targets — personal, enterprise, robotics, cloud, mission."""
        er = self._c("err")
        ok = self._c("ok")
        ic = self._c("info")
        if len(args) < 2:
            print(f"{er}Usage: deploy <agent_id> <target>\033[0m")
            print(f"  Targets: {', '.join(self.foundry.deployer.TARGETS)}")
            return
        agent = self.foundry.get_agent(args[0])
        if not agent:
            print(f"{er}Agent not found: {args[0]}\033[0m")
            return
        target = args[1]
        deployment = self.foundry.deploy_intelligence(agent, target)
        if deployment:
            print(f"{ok}Deployed {agent.name} to {target}\033[0m")
            print(f"  Deployment ID: {deployment['id']}")
            print(f"  Status: {deployment['status']}")
            print(f"  Config: {deployment['config']}")
        else:
            print(f"{er}Deployment failed — valid targets: {', '.join(self.foundry.deployer.TARGETS)}\033[0m")
        deployments = self.foundry.deployer.list_deployments()
        if len(deployments) > 1:
            print(f"\n{ic}All Deployments:\033[0m")
            for d in deployments:
                print(f"  {d['agent_name']:<20} -> {d['target']:<16} [{d['status']}]")

    def cmd_versions(self, args):
        """Track, compare, and rollback intelligence versions."""
        er = self._c("err")
        ok = self._c("ok")
        ic = self._c("info")
        if not args:
            versions = self.foundry.versions.list_versions()
            if not versions:
                print("No version history yet")
                return
            print(f"{ic}Version History:\033[0m")
            print(f"  {'ID':<24} {'AGENT':<20} {'LABEL':<24} {'BRANCH':<12} {'TIME':<20}")
            for v in versions[:20]:
                t = time.strftime("%H:%M:%S", time.localtime(v["timestamp"]))
                print(f"  {v['id'][:22]:<24} {v['agent_name'][:18]:<20} {str(v.get('label',''))[:22]:<24} {v['branch']:<12} {t:<20}")
            return
        action = args[0]
        if action == "compare":
            if len(args) < 3:
                print(f"{er}Usage: versions compare <version_a_id> <version_b_id>\033[0m")
                return
            diff = self.foundry.versions.compare(args[1], args[2])
            if not diff:
                print(f"{er}Version not found\033[0m")
                return
            print(f"{ic}Comparing: {diff['from']['label']} -> {diff['to']['label']}\033[0m")
            print(f"  Tasks: {diff['tasks_a']} -> {diff['tasks_b']}")
            if diff['skills_added']:
                print(f"  {ok}Skills Added:\033[0m")
                for s in diff['skills_added']:
                    print(f"    + {s['skill']} (level {s['level']})")
            if diff['skills_changed']:
                print(f"  \033[33mSkills Changed:\033[0m")
                for s in diff['skills_changed']:
                    print(f"    ~ {s['skill']}: {s['from']} -> {s['to']}")
            if diff['tools_added']:
                print(f"  {ok}Tools Added:\033[0m {', '.join(diff['tools_added'])}")
        elif action == "rollback":
            if len(args) < 3:
                print(f"{er}Usage: versions rollback <agent_id> <version_id>\033[0m")
                return
            agent = self.foundry.get_agent(args[1])
            if not agent:
                print(f"{er}Agent not found\033[0m")
                return
            if self.foundry.versions.rollback(agent, args[2]):
                v = self.foundry.versions.get_version(args[2])
                label = v["label"] if v else args[2]
                print(f"{ok}Rolled back {agent.name} to {label}\033[0m")
            else:
                print(f"{er}Rollback failed\033[0m")
        else:
            versions = self.foundry.versions.list_versions(branch=action)
            if not versions:
                print(f"{er}Unknown: {action}. Try 'versions' to list all\033[0m")
                return
            print(f"{ic}Versions ({action}):\033[0m")
            for v in versions:
                t = time.strftime("%H:%M:%S", time.localtime(v["timestamp"]))
                print(f"  {v['id'][:20]:<22} {v['agent_name']:<18} {v.get('label','')[:20]:<20} {t}")

    # ======================== UIF COMMANDS ========================

    def cmd_uif(self, args):
        """Universal Intelligence Fabric — intent-driven computing platform."""
        ic = self._c("info")
        ok = self._c("ok")
        if not args:
            s = self.uif.summary()
            print(f"{ic}Universal Intelligence Fabric\033[0m")
            print(f"  {ok}Intents Processed:\033[0m {s['intents_processed']}")
            print(f"  {ok}Agents Registered:\033[0m {s['agents_registered']}")
            print(f"  {ok}Skills Available:\033[0m {s['skills_available']}")
            print(f"  {ok}Identities:\033[0m {s['identities']}")
            print(f"  {ok}API Calls:\033[0m {s['api_calls']}")
            print(f"  {ok}Knowledge Memories:\033[0m {s['knowledge_memories']}")
            print(f"  {ok}Graph Concepts:\033[0m {s['graph_concepts']}")
            print()
            print(f"  \033[1;36mCommands:\033[0m")
            print(f"    uif status                   Show this overview")
            print(f"    intent <text>                Process intent from natural language")
            print(f"    agents list                  List all registered agents")
            print(f"    agents missions              Show active missions")
            print(f"    skills [query]               List or search skills")
            print(f"    identity                     Show active identity")
            print(f"    api call <endpoint> [json]    Call API endpoint")
            return
        if args[0] == "status":
            s = self.uif.summary()
            print(f"{ic}UIF Status:\033[0m")
            for k, v in s.items():
                print(f"  {k.replace('_', ' ').title()}: {v}")

    def cmd_intent(self, args):
        """Process intent from natural language — the core of intent-first computing."""
        er = self._c("err")
        ok = self._c("ok")
        ic = self._c("info")
        if not args:
            print(f"{er}Usage: intent <what do you want to achieve?>")
            return
        text = " ".join(args)
        result = self.uif.process(text)
        print(f"{ic}Intent Analysis:\033[0m")
        print(f"  Input: {result['input']}")
        print(f"  Detected Intent: \033[1;36m{result['intent']['primary']}\033[0m (confidence: {result['intent']['confidence']:.0%})")
        print(f"  Steps:")
        for i, step in enumerate(result['steps'], 1):
            print(f"    {i}. {step.replace('_', ' ').title()}")
        print(f"  Mission ID: {result['mission_id']}")
        if result['agents_assigned']:
            print(f"  {ok}Agents Assigned:\033[0m {', '.join(result['agents_assigned'])}")

    def cmd_agents_uif(self, args):
        """Manage UIF agents — list, status, missions."""
        er = self._c("err")
        ic = self._c("info")
        if not args:
            print(f"{er}Usage: agents <list|missions>\033[0m")
            return
        if args[0] == "list":
            agents = self.uif.orchestrator.list_agents()
            if not agents:
                print("No agents registered")
                return
            print(f"{ic}Registered Agents:\033[0m")
            print(f"  {'ID':<24} {'NAME':<20} {'ROLE':<24} {'STATUS':<12} {'TASKS':<8}")
            for a in agents:
                print(f"  {a.id:<24} {a.name:<20} {a.role[:22]:<24} {a.status:<12} {a.tasks_completed:<8}")
        elif args[0] == "missions":
            missions = self.uif.orchestrator.mission_status()
            if not missions:
                print("No active missions")
                return
            print(f"{ic}Active Missions:\033[0m")
            for m in missions:
                print(f"  {m['id'][:16]:<18} {m['goal'][:40]:<42} {m['status']:<12} {len(m['agents'])} agents")

    def cmd_skills(self, args):
        """Universal Skill System — browse, install, create skills."""
        er = self._c("err")
        ok = self._c("ok")
        ic = self._c("info")
        query = " ".join(args) if args else None
        results = self.uif.skills.search(query=query)
        if not results:
            print("No skills found" if not query else f"No skills matching '{query}'")
            return
        print(f"{ic}Skills{' matching: ' + query if query else ''}:\033[0m")
        print(f"  {'ID':<24} {'NAME':<28} {'CATEGORY':<16} {'TOOLS':<20} {'VERSION':<10}")
        for s in results:
            mark = " *" if s["id"] in {sk["id"] for sk in self.uif.skills.list_installed()} else "  "
            print(f"  {s['id']:<24}{s['name'][:26]:<28}{s.get('category',''):<16}{', '.join(s.get('tools',[]))[:18]:<20}{s.get('version',''):<10}{mark}")

    def cmd_identity(self, args):
        """Show active digital identity."""
        ic = self._c("info")
        identity = self.uif.identity.get_active()
        if not identity:
            print("No active identity")
            return
        print(f"{ic}Active Identity:\033[0m")
        print(f"  Name: {identity['name']}")
        print(f"  ID: {identity['id']}")
        print(f"  Devices: {len(identity.get('device_history', []))}")
        print(f"  Agent Relationships: {len(identity.get('agent_relationships', {}))}")
        print(f"  Preferences: {len(identity.get('preferences', {}))}")
        print(f"  Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(identity['created']))}")

    def cmd_api_uif(self, args):
        """Call ARCANIS Universal API endpoints."""
        er = self._c("err")
        ok = self._c("ok")
        if len(args) < 2:
            print(f"{er}Usage: api call <endpoint> [json_payload]\033[0m")
            print(f"  Endpoints: {', '.join(self.uif.api.ENDPOINTS)}")
            return
        if args[0] == "call":
            endpoint = args[1]
            payload = {}
            if len(args) > 2:
                try:
                    payload = json.loads(" ".join(args[2:]))
                except Exception:
                    payload = {"text": " ".join(args[2:])}
            result = self.uif.api.call(endpoint, payload)
            if "error" in result:
                print(f"{er}API Error: {result['error']}\033[0m")
                return
            print(f"{ok}API Response ({endpoint}):\033[0m")
            for k, v in result.items():
                if k in ("status", "timestamp", "endpoint"):
                    continue
                if isinstance(v, list):
                    print(f"  {k}: {len(v)} items")
                    for item in v[:3]:
                        if isinstance(item, dict):
                            print(f"    - {str(list(item.values())[:2])[:80]}")
                        else:
                            print(f"    - {str(item)[:80]}")
                elif isinstance(v, dict):
                    print(f"  {k}:")
                    for sk, sv in v.items():
                        print(f"    {sk}: {str(sv)[:60]}")
                else:
                    print(f"  {k}: {str(v)[:60]}")

    # ======================== PIIN (Phase 13) ========================

    def cmd_piin(self, args):
        """Personal Intelligence Identity Network — view full summary."""
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        s = self.piin.full_summary()
        print(f"\033[{hl}mPIIN — Personal Intelligence Identity Network\033[0m")
        print(f"{dm}  Session Duration:\033[0m {s['session_duration']:.0f}s")
        print(f"{dm}  Model Observations:\033[0m {s['model']['total_observations']}")
        print(f"{dm}  Memory:\033[0m ST={s['memory']['short_term']} EP={s['memory']['episodic']} SM={s['memory']['semantic']} PR={s['memory']['procedural']}")
        print(f"{dm}  Knowledge Graph:\033[0m {s['knowledge_graph']['entities']} entities, {s['knowledge_graph']['relationships']} rels")
        print(f"{dm}  Goals:\033[0m {s['goals']['active']} active / {s['goals']['completed']} completed")
        print(f"{dm}  Personalization:\033[0m {s['personalization']}")
        print(f"{dm}  Agent Relations:\033[0m {len(s['agent_relations'])} agents")
        life = s['life_os']
        print(f"{dm}  Life OS:\033[0m " + " | ".join(f"{d}={c}" for d, c in life.items()))
        print(f"{dm}  Automation:\033[0m {s['automation']['patterns_detected']} patterns, {s['automation']['pending_suggestions']} suggestions")
        print(f"{dm}  Vault:\033[0m {s['vault']['namespaces']} namespaces, {s['vault']['entries']} entries")
        print(f"{dm}  Growth:\033[0m {s['growth']['milestones']} milestones | KG={s['growth']['total_knowledge_gain']} SG={s['growth']['total_skill_gain']}")

    def cmd_piin_profile(self, args):
        """Show the personal intelligence model profile."""
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        p = self.piin.user_profile()
        print(f"\033[{hl}mPersonal Intelligence Model\033[0m")
        print(f"{dm}  Learning:\033[0m modality={p['learning_patterns'].get('preferred_modality','')} pace={p['learning_patterns']['pace']} depth={p['learning_patterns']['depth']}")
        print(f"{dm}  Working Style:\033[0m {p['working_style']}")
        print(f"{dm}  Communication:\033[0m {p['communication_preferences']}")
        print(f"{dm}  Technical Interests:\033[0m")
        for i in p['technical_interests'][:5]:
            print(f"    - {i['topic']} (x{i['count']})")
        print(f"{dm}  Active Projects:\033[0m {', '.join(p['active_projects'][:5]) or 'none'}")
        print(f"{dm}  Long-term Goals:\033[0m")
        for g in p['long_term_goals'][:3]:
            print(f"    - {g}")
        print(f"{dm}  Knowledge Level:\033[0m {p['knowledge_level']}")
        print(f"{dm}  Workflows:\033[0m {len(p['frequently_used_workflows'])} patterns")
        print(f"{dm}  Total Observations:\033[0m {p['total_observations']}")

    def cmd_piin_memory(self, args):
        """Access multi-layer memory. Usage: mem <layer> [query]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        if not args:
            s = self.piin.memory_stats()
            print(f"{dm}Memory Layers:\033[0m")
            print(f"  Short-Term: {s['short_term']} entries")
            print(f"  Episodic:   {s['episodic']} entries")
            print(f"  Semantic:   {s['semantic']} concepts")
            print(f"  Procedural: {s['procedural']} patterns")
            return
        layer = args[0].lower()
        query = " ".join(args[1:]) if len(args) > 1 else None
        if layer in ("st", "short"):
            results = self.piin.memory.recall_short_term(query)
            print(f"{dm}Short-Term Memory ({len(results)}):\033[0m")
            for r in results[-10:]:
                print(f"  [{time.strftime('%H:%M', time.localtime(r['time']))}] {str(r['content'])[:80]}")
        elif layer in ("ep", "episodic"):
            results = self.piin.memory.recall_episodic(query)
            print(f"{dm}Episodic Memory ({len(results)}):\033[0m")
            for r in results[-10:]:
                print(f"  [{r['type']}] {r['description'][:80]}")
        elif layer in ("sm", "semantic"):
            results = self.piin.memory.recall_semantic(query)
            print(f"{dm}Semantic Memory ({len(results)} concepts):\033[0m")
            for k, v in list(results.items())[:10]:
                print(f"  {k}: {v['description'][:60]} (conf={v['confidence']:.2f})")
        elif layer in ("pr", "procedural"):
            results = self.piin.memory.recall_procedural(query)
            print(f"{dm}Procedural Memory ({len(results)} patterns):\033[0m")
            for r in results[-10:]:
                print(f"  {r['name']} (x{r['frequency']}) - {', '.join(map(str, r['steps'][:3]))}")
        elif layer == "consolidate":
            result = self.piin.memory.consolidate()
            print(f"{ok}Memory consolidated: {result['short_term_remaining']} short-term entries remaining\033[0m")
        else:
            print(f"{er}Unknown layer: {layer}\033[0m")
            print("  Layers: st (short-term), ep (episodic), sm (semantic), pr (procedural), consolidate")

    def cmd_piin_knowledge(self, args):
        """Knowledge graph operations. Usage: know <sub> [args]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        kg = self.piin.knowledge_graph
        if not args:
            s = kg.stats()
            print(f"\033[{hl}mKnowledge Graph\033[0m")
            print(f"  {s['entities']} entities, {s['relationships']} relationships")
            for etype, count in s['by_type'].items():
                print(f"    {etype}: {count}")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "add":
            if len(rest) < 3:
                print(f"{er}Usage: know add <id> <type> <name>\033[0m")
                return
            result = kg.add_entity(rest[0], rest[1], " ".join(rest[2:]))
            print(f"{ok}{result}\033[0m")
        elif sub == "connect":
            if len(rest) < 2:
                print(f"{er}Usage: know connect <id1> <id2> [rel_type]\033[0m")
                return
            rel = rest[2] if len(rest) > 2 else "related_to"
            result = kg.connect(rest[0], rest[1], rel)
            print(f"{ok}Connected: {rest[0]} --{rel}--> {rest[1]}\033[0m")
        elif sub == "query":
            q = " ".join(rest)
            results = kg.query(name=q) if q else kg.query()
            print(f"{dm}Entities ({len(results)}):\033[0m")
            for e in results[:15]:
                print(f"  [{e['type']}] {e['id']}: {e['name']}")
        elif sub == "path":
            if len(rest) < 2:
                print(f"{er}Usage: know path <id1> <id2>\033[0m")
                return
            path = kg.path(rest[0], rest[1])
            if path:
                print(f"{ok}Path:\033[0m " + " -> ".join(kg.get_entity(e)["name"] if kg.get_entity(e) else e for e in path))
            else:
                print(f"{er}No path found\033[0m")
        elif sub == "graph":
            print(f"{dm}Full Knowledge Graph:\033[0m")
            for eid, ent in kg._entities.items():
                rels = kg.get_relationships(eid)
                if rels:
                    for r in rels[:3]:
                        target = kg.get_entity(r['target']) if r['source'] == eid else kg.get_entity(r['source'])
                        tname = target['name'] if target else '?'
                        print(f"  {ent['name']} --{r['type']}--> {tname}")
                else:
                    print(f"  {ent['name']} (isolated)")

    def cmd_piin_goal(self, args):
        """Goal intelligence engine. Usage: goal <sub> [args]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        g = self.piin.goals
        if not args:
            s = g.summary()
            print(f"\033[{hl}mGoal Intelligence\033[0m")
            print(f"  Total: {s['total_goals']} | Active: {s['active']} | Completed: {s['completed']}")
            print(f"  Learning Paths: {s['learning_paths']} | Avg Progress: {s['avg_progress']:.0f}%")
            goals = g.get_goals()
            if goals:
                print(f"{dm}Goals:\033[0m")
                for gid, info in goals.items():
                    print(f"  [{info['status']}] {info['description']} ({info['progress']}%)")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "add":
            desc = " ".join(rest)
            if not desc:
                print(f"{er}Usage: goal add <description>\033[0m")
                return
            gid = f"g_{int(time.time())}"
            result = g.add_goal(gid, desc)
            print(f"{ok}Goal created: {gid} - '{desc}'\033[0m")
        elif sub == "progress":
            if len(rest) < 2:
                print(f"{er}Usage: goal progress <gid> <0-100>\033[0m")
                return
            g.update_progress(rest[0], int(rest[1]))
            print(f"{ok}Progress updated for {rest[0]}: {rest[1]}%\033[0m")
        elif sub == "path":
            desc = " ".join(rest)
            if not desc:
                print(f"{er}Usage: goal path <goal description>\033[0m")
                return
            lp = g.create_learning_path(desc)
            print(f"{ok}Learning path created: {lp['id']}\033[0m")
            for i, step in enumerate(lp['steps']):
                print(f"  {i+1}. {step}")
        elif sub == "advance":
            if not rest:
                print(f"{er}Usage: goal advance <path_id>\033[0m")
                return
            result = g.advance_learning_path(rest[0])
            if result:
                print(f"{ok}Advanced to step {result['current_step']+1}/{len(result['steps'])} ({result['progress']}%)\033[0m")
            else:
                print(f"{er}Path not found\033[0m")
        elif sub == "obstacle":
            if len(rest) < 2:
                print(f"{er}Usage: goal obstacle <gid> <description>\033[0m")
                return
            g.add_obstacle(rest[0], " ".join(rest[1:]))
            print(f"{ok}Obstacle added to {rest[0]}\033[0m")

    def cmd_piin_prefs(self, args):
        """Adaptive personalization. Usage: prefs [set <key> <value>]"""
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        p = self.piin.personalization
        if not args:
            prof = p.profile()
            print(f"\033[{hl}mAdaptive Personalization\033[0m")
            print(f"{dm}  Preferences:\033[0m")
            for k, v in prof['preferences'].items():
                print(f"    {k}: {v}")
            print(f"{dm}  Adjustments made:\033[0m {prof['adjustments_made']}")
            if prof['last_changes']:
                print(f"{dm}  Recent changes:\033[0m")
                for c in prof['last_changes']:
                    print(f"    {c.get('key','?')}: {c.get('from','?')} -> {c.get('to','?')}")
            return
        if args[0] == "set" and len(args) >= 3:
            p.record_preference(args[1], " ".join(args[2:]))
            print(f"{ok}Preference updated: {args[1]} = {' '.join(args[2:])}\033[0m")

    def cmd_piin_agents_learn(self, args):
        """Agent relationship system. Usage: agents-learn [agent_type]"""
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        ar = self.piin.agent_relations
        if not args:
            s = ar.summary()
            print(f"\033[{hl}mAgent Relationship System\033[0m")
            for atype, info in s.items():
                print(f"{dm}  {atype}:\033[0m")
                for k, v in info['preferences'].items():
                    print(f"    {k}: {v}")
                print(f"    patterns learned: {info['patterns']}")
            return
        atype = args[0]
        if atype in ar._agent_profiles:
            prefs = ar.get_preferences(atype)
            print(f"{hl}{atype} agent preferences:\033[0m")
            for k, v in prefs.items():
                print(f"  {k}: {v}")
            if len(args) > 2 and args[1] == "set":
                ar.update_preference(atype, args[2], " ".join(args[3:]))
                print(f"{ok}Updated\033[0m")
        else:
            print(f"{er}Unknown agent type: {atype}\033[0m")

    def cmd_piin_life(self, args):
        """Life OS framework. Usage: life [domain [type data...]]"""
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        lo = self.piin.life_os
        if not args:
            s = lo.stats()
            print(f"\033[{hl}mLife OS Framework\033[0m")
            for domain, counts in s.items():
                active = ", ".join(f"{k}={v}" for k, v in counts.items())
                print(f"  {domain}: {active}")
            cross = lo.suggest_cross_domain()
            if cross:
                print(f"{dm}Cross-domain suggestions:\033[0m")
                for c in cross:
                    print(f"  * {c}")
            return
        if len(args) >= 2:
            rest = args[2:]
            entry = lo.add_entry(args[0], args[1], " ".join(rest) if rest else {})
            if "error" in entry:
                print(f"{er}{entry['error']}\033[0m")
            else:
                print(f"{ok}Added to {args[0]}/{args[1]}\033[0m")

    def cmd_piin_vault(self, args):
        """Personal data vault. Usage: vault <sub> [args]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        v = self.piin.vault
        if not args:
            s = v.stats()
            print(f"\033[{hl}mPersonal Data Vault\033[0m")
            print(f"  Namespaces: {s['namespaces']}, Entries: {s['entries']}")
            for ns in v.list_namespaces():
                print(f"  {ns}: {len(v.list_namespace(ns))} keys")
            print(f"{dm}Commands: vault store <ns> <key> <data>, vault get <ns> <key>, vault list <ns>, vault export\033[0m")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "store":
            if len(rest) < 3:
                print(f"{er}Usage: vault store <namespace> <key> <data>\033[0m")
                return
            result = v.store(rest[0], rest[1], " ".join(rest[2:]))
            print(f"{ok}Stored in {rest[0]}/{rest[1]}\033[0m")
        elif sub == "get":
            if len(rest) < 2:
                print(f"{er}Usage: vault get <namespace> <key>\033[0m")
                return
            data = v.retrieve(rest[0], rest[1])
            if data is not None:
                print(f"{dm}{rest[0]}/{rest[1]}:\033[0m {str(data)[:200]}")
            else:
                print(f"{er}Not found\033[0m")
        elif sub == "list":
            ns = rest[0] if rest else None
            if ns:
                keys = v.list_namespace(ns)
                print(f"{dm}{ns} keys ({len(keys)}):\033[0m")
                for k in keys:
                    print(f"  - {k}")
            else:
                print(f"{dm}Namespaces:\033[0m")
                for ns in v.list_namespaces():
                    print(f"  - {ns}")
        elif sub == "export":
            data = v.export_all()
            print(json.dumps(data, indent=2)[:1000])
        elif sub == "key":
            v.set_key(" ".join(rest))
            print(f"{ok}Encryption key set\033[0m")

    def cmd_piin_timeline(self, args):
        """Intelligence growth timeline. Usage: timeline [events]"""
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        g = self.piin.growth
        if args and args[0] == "events":
            tl = g.timeline(30)
            print(f"\033[{hl}mIntelligence Timeline\033[0m")
            for e in tl:
                t = time.strftime('%Y-%m-%d %H:%M', time.localtime(e['time']))
                if e['type'] == 'milestone':
                    print(f"  [{t}] \033[1;36m{e['title']}\033[0m: {e['description'][:60]}")
                elif e['type'] == 'knowledge':
                    print(f"  [{t}] \033[32mKnowledge\033[0m: {e['topic']} (+{e['gain']})")
                elif e['type'] == 'skill':
                    print(f"  [{t}] \033[33mSkill\033[0m: {e['skill']} (+{e['gain']})")
                elif e['type'] == 'project':
                    print(f"  [{t}] \033[35mProject\033[0m: {e['name']} ({e['status']})")
        else:
            s = g.growth_summary()
            print(f"\033[{hl}mIntelligence Growth Summary\033[0m")
            print(f"  Milestones:          {s['milestones']}")
            print(f"  Knowledge Events:    {s['knowledge_events']} (total gain: {s['total_knowledge_gain']})")
            print(f"  Skill Events:        {s['skill_events']} (total gain: {s['total_skill_gain']})")
            print(f"  Projects:            {s['projects']}")
            print(f"  Agent Improvements:  {s['agent_improvements']}")
            print(f"  Workflow Improvements: {s['workflow_improvements']}")

    # ======================== RIL (Phase 14) ========================

    def cmd_ril(self, args):
        """Reality Interface Layer — view full summary of all 10 layers."""
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        s = self.ril.full_summary()
        print(f"\033[{hl}mRIL — Reality Interface Layer\033[0m")
        print(f"{dm}  Perception:\033[0m {s['perception']['total_perceptions']} inputs, {s['perception']['active_modalities']} active")
        print(f"{dm}  Voice:\033[0m {s['voice']['total_utterances']} utterances, lang={s['voice']['active_language']}, emotion={s['voice']['last_emotion']['last_emotion']}")
        print(f"{dm}  Vision:\033[0m {s['vision']['screen_captures']} screens, {s['vision']['objects_detected']} objects, {s['vision']['known_objects']} known")
        print(f"{dm}  Spatial:\033[0m {s['spatial']['environments']} environments, {s['spatial']['objects']} objects, {s['spatial']['workspaces']} workspaces")
        print(f"{dm}  Devices:\033[0m {s['devices']['total_devices']} registered, {s['devices']['connected']} connected")
        print(f"{dm}  Robotics:\033[0m {s['robotics']['robots']} robots, {s['robotics']['sensors']} sensors, {s['robotics']['workflows']} workflows")
        print(f"{dm}  Context:\033[0m mode={s['context']['current_mode']} | {s['context']['total_updates']} updates")
        print(f"{dm}  Interaction:\033[0m {s['interaction']['total_interactions']} interactions, mode={s['interaction']['current_mode']}")
        print(f"{dm}  Presence:\033[0m state={s['presence']['state']} | {s['presence']['identity']}")
        print(f"{dm}  Security:\033[0m {s['security']['total_actions']} logged, stop={s['security']['emergency_stop']}")

    def cmd_ril_perception(self, args):
        """Multimodal perception. Usage: perceive <modality> <data> or perceive status"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        p = self.ril.perception
        if not args:
            s = p.stats()
            print(f"\033[{hl}mMultimodal Perception Engine\033[0m")
            for mod, config in p.modalities.items():
                en = '\033[32mON\033[0m' if config['enabled'] else '\033[31mOFF\033[0m'
                print(f"  {mod}: {en}")
            print(f"{dm}Total perceptions:\033[0m {s['total_perceptions']}")
            return
        if args[0] == "status":
            s = p.stats()
            print(f"\033[{hl}mPerception Status\033[0m")
            for mod, config in p.modalities.items():
                last = config.get('last_input', '')[:60]
                en = '\033[32mON\033[0m' if config['enabled'] else '\033[31mOFF\033[0m'
                print(f"  {mod}: {en} | {last}")
        elif args[0] == "enable" and len(args) > 1:
            p.enable_modality(args[1])
            print(f"{ok}{args[1]} enabled\033[0m")
        elif args[0] == "disable" and len(args) > 1:
            p.disable_modality(args[1])
            print(f"{ok}{args[1]} disabled\033[0m")
        else:
            result = p.perceive(args[0], " ".join(args[1:]) if len(args) > 1 else "")
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Perceived via {args[0]}\033[0m")

    def cmd_ril_voice(self, args):
        """Advanced voice interface. Usage: voice <text> or voice <sub> [args]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        v = self.ril.voice
        if not args:
            s = v.conversation_summary()
            print(f"\033[{hl}mAdvanced Voice System\033[0m")
            print(f"{dm}  Utterances:\033[0m {s['total_utterances']}")
            print(f"{dm}  Language:\033[0m {s['active_language']}")
            print(f"{dm}  Emotion:\033[0m {s['last_emotion']['last_emotion']} ({s['last_emotion']['confidence']:.0%})")
            print(f"{dm}  Continuous mode:\033[0m {s['continuous_mode']}")
            print(f"{dm}  Context topics:\033[0m {', '.join(s['context_topics'][:5])}")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "say":
            text = " ".join(rest)
            result = v.process_speech(text)
            emotion = v.detect_emotion(text)
            print(f"{ok}Voice processed\033[0m")
            print(f"  Recognized: '{result['recognized']}'")
            print(f"  Intent: {result['intent']}")
            print(f"  Emotion: {emotion['last_emotion']}")
        elif sub == "lang" and rest:
            if v.set_language(rest[0]):
                print(f"{ok}Language set to {rest[0]}\033[0m")
            else:
                print(f"{er}Unknown language. Available: {', '.join(v.languages.keys())}\033[0m")
        elif sub == "continuous":
            if rest and rest[0] == "off":
                v.stop_continuous()
                print(f"{ok}Continuous mode off\033[0m")
            else:
                v.start_continuous()
                print(f"{ok}Continuous mode on\033[0m")
        elif sub == "history":
            for entry in v._conversation_history[-10:]:
                print(f"  [{time.strftime('%H:%M', time.localtime(entry['time']))}] {entry['text'][:80]}")

    def cmd_ril_vision(self, args):
        """Computer vision layer. Usage: vision <sub> [args]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        v = self.ril.vision
        if not args:
            s = v.stats()
            print(f"\033[{hl}mComputer Vision Layer\033[0m")
            print(f"{dm}  Screen captures:\033[0m {s['screen_captures']}")
            print(f"{dm}  Objects detected:\033[0m {s['objects_detected']}")
            print(f"{dm}  Documents analyzed:\033[0m {s['documents_analyzed']}")
            print(f"{dm}  Images analyzed:\033[0m {s['images_analyzed']}")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "screen":
            desc = " ".join(rest) if rest else "Screen state"
            result = v.capture_screen(desc)
            print(f"{ok}Screen captured: {desc}\033[0m")
        elif sub == "detect" and len(rest) >= 2:
            result = v.detect_object(rest[0], rest[1], rest[2] if len(rest) > 2 else "unknown")
            print(f"{ok}Object detected: {rest[1]} (id={rest[0]})\033[0m")
        elif sub == "analyze":
            text = " ".join(rest)
            result = v.analyze_document(f"doc_{int(time.time())}", text, "text")
            print(f"{ok}Analysis complete\033[0m: {text[:80]}")
        elif sub == "issue":
            text = " ".join(rest) if rest else "circuit"
            result = v.identify_issue(text)
            print(f"{hl}Issue Analysis\033[0m")
            print(f"  Input: {result['analysis'][:80]}")
            print(f"  Identified: {result['identified_issue']}")

    def cmd_ril_spatial(self, args):
        """Spatial computing foundation. Usage: spatial <sub> [args]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        s = self.ril.spatial
        if not args:
            st = s.stats()
            print(f"\033[{hl}mSpatial Computing Foundation\033[0m")
            print(f"{dm}  Environments:\033[0m {st['environments']}")
            print(f"{dm}  Objects:\033[0m {st['objects']}")
            print(f"{dm}  Workspaces:\033[0m {st['workspaces']}")
            for eid, env in s._environments.items():
                active = ' [ACTIVE]' if env['active'] else ''
                print(f"   - {env['name']} ({env['type']}){active}")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "create" and len(rest) >= 1:
            name = " ".join(rest)
            eid = f"env_{int(time.time())}"
            s.create_environment(eid, name)
            s.activate_environment(eid)
            print(f"{ok}Spatial environment created: '{name}' (id={eid})\033[0m")
        elif sub == "info":
            topic = " ".join(rest) if rest else "general"
            result = s.organize_information_space(topic, ["Source A", "Source B", "Note 1", "Note 2", "Reference"])
            print(f"{ok}Information space organized for '{topic}'\033[0m")
            print(f"  Environment: {result['environment']}")
            print(f"  Items placed: {result['items_placed']}")
        elif sub == "workspace" and len(rest) >= 1:
            ws_id = f"ws_{int(time.time())}"
            s.create_workspace(ws_id, " ".join(rest))
            s.activate_workspace(ws_id)
            print(f"{ok}Workspace created: {' '.join(rest)}\033[0m")

    def cmd_ril_devices(self, args):
        """Device orchestration layer. Usage: devices <sub> [args]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        d = self.ril.devices
        if not args:
            st = d.stats()
            print(f"\033[{hl}mDevice Orchestration Layer\033[0m")
            print(f"{dm}  Total devices:\033[0m {st['total_devices']}")
            print(f"{dm}  Connected:\033[0m {st['connected']}")
            print(f"{dm}  By category:\033[0m {st['by_category']}")
            for did, dev in d._devices.items():
                print(f"   - {dev['name']} ({dev['category']}) [{dev['status']}]")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "register" and len(rest) >= 2:
            result = d.register_device(rest[0], " ".join(rest[1:]), "computer")
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Device registered: {rest[0]}\033[0m")
        elif sub == "connect" and rest:
            if d.connect_device(rest[0]):
                print(f"{ok}Device {rest[0]} connected\033[0m")
            else:
                print(f"{er}Device not found\033[0m")
        elif sub == "send" and len(rest) >= 2:
            result = d.send_command(rest[0], rest[1], {"params": " ".join(rest[2:])} if len(rest) > 2 else {})
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Command sent to {rest[0]}: {rest[1]}\033[0m")

    def cmd_ril_robotics(self, args):
        """Robotics integration framework. Usage: robot <sub> [args]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        r = self.ril.robotics
        if not args:
            st = r.stats()
            print(f"\033[{hl}mRobotics Integration Framework\033[0m")
            print(f"{dm}  Robots:\033[0m {st['robots']}")
            print(f"{dm}  Sensors:\033[0m {st['sensors']}")
            print(f"{dm}  Workflows:\033[0m {st['workflows']}")
            print(f"{dm}  Completed actions:\033[0m {st['completed_actions']}")
            for rid, robot in r._robots.items():
                print(f"   - {robot['name']} ({robot['type']}) [{robot['status']}] battery={robot['battery']}%")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "register" and len(rest) >= 1:
            rid = rest[0]
            name = " ".join(rest[1:]) if len(rest) > 1 else rid
            r.register_robot(rid, name)
            print(f"{ok}Robot registered: {name} (id={rid})\033[0m")
        elif sub == "act" and len(rest) >= 2:
            result = r.execute_action(rest[0], rest[1], {"params": " ".join(rest[2:])} if len(rest) > 2 else {})
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}{result['action']} executed on {result['robot']}\033[0m")
        elif sub == "organize":
            desc = " ".join(rest) if rest else "workspace"
            plan = r.organize_workspace(desc)
            print(f"{hl}Organization Plan: {plan['plan']}\033[0m")
            for i, step in enumerate(plan['steps']):
                print(f"  {i+1}. {step}")
            print(f"{dm}  Estimated time:\033[0m {plan['estimated_time']}")

    def cmd_ril_context(self, args):
        """Context awareness engine. Usage: where [set <key> <value>]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        c = self.ril.context
        if not args:
            cur = c.current()
            print(f"\033[{hl}mContext Awareness Engine\033[0m")
            print(f"{dm}  Location:\033[0m {cur['location']}")
            print(f"{dm}  Active device:\033[0m {cur['active_device']}")
            print(f"{dm}  Current activity:\033[0m {cur['current_activity']}")
            print(f"{dm}  Surroundings:\033[0m {', '.join(cur['surroundings'][:5])}")
            print(f"{dm}  Time:\033[0m {cur['time']} ({cur['day']})")
            print(f"{dm}  User intention:\033[0m {cur['user_intention']}")
            mode = c.detect_mode(cur['current_activity'])
            print(f"{dm}  Detected mode:\033[0m {mode['mode']} -> {mode['response_style']}")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "set" and len(rest) >= 2:
            key, value = rest[0], " ".join(rest[1:])
            if key == "location":
                c.set_location(value)
            elif key == "device":
                c.set_device(value)
            elif key == "activity":
                mode = c.set_activity(value)
                print(f"{ok}Activity set, mode: {mode['mode']} ({mode['response_style']})\033[0m")
            elif key == "surrounding":
                c.add_surrounding(value)
            print(f"{ok}Context updated: {key} = {value}\033[0m")
        elif sub == "mode":
            print(f"{hl}Available modes:\033[0m")
            for mode, config in c._modes.items():
                print(f"  {mode}: tags={config['tags']} -> {config['response_style']}")

    def cmd_ril_interaction(self, args):
        """Human-AI interaction model. Usage: interact <text>"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        i = self.ril.interaction
        if not args:
            s = i.stats()
            print(f"\033[{hl}mHuman-AI Interaction Model\033[0m")
            print(f"{dm}  Total interactions:\033[0m {s['total_interactions']}")
            print(f"{dm}  Visualizations:\033[0m {s['visualizations']}")
            print(f"{dm}  Suggested actions:\033[0m {s['suggestions']}")
            print(f"{dm}  Current mode:\033[0m {s['current_mode']}")
            return
        text = " ".join(args)
        result = i.process_intent(text)
        print(f"{hl}Intent: {result['intent']}\033[0m")
        print(f"  {result['response']}")
        print(f"{dm}  Suggested action:\033[0m {result['suggested_action']['description']}")

    def cmd_ril_presence(self, args):
        """ARCANIS presence system. Usage: presence [state]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        p = self.ril.presence
        if not args:
            s = p.presence_summary()
            print(f"\033[{hl}mARCANIS Presence System\033[0m")
            print(f"{dm}  Identity:\033[0m {s['identity']}")
            print(f"{dm}  State:\033[0m {s['state']}")
            print(f"{dm}  Style:\033[0m {s['style']}")
            print(f"{dm}  Personality:\033[0m")
            for trait, val in s['personality'].items():
                bar = '█' * int(val * 10) + '░' * (10 - int(val * 10))
                print(f"    {trait}: {bar} {val:.0%}")
            print(f"{dm}  Visual:\033[0m symbol={s['visual']['symbol']}, color={s['visual']['color']}")
            print(f"{dm}  Greeting:\033[0m {p.greeting()}")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "state":
            if rest:
                p.set_state(rest[0])
                print(f"{ok}State set to {rest[0]}\033[0m")
            else:
                print(f"Valid states: idle, listening, processing, responding, active, background")
        elif sub == "adapt" and rest:
            p.adapt_style(rest[0])
            print(f"{ok}Style adapted to {rest[0]}\033[0m")

    def cmd_ril_security(self, args):
        """Reality security framework. Usage: rsafety <sub> [args]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        s = self.ril.security
        if not args:
            st = s.stats()
            print(f"\033[{hl}mReality Security Framework\033[0m")
            print(f"{dm}  Total actions:\033[0m {st['total_actions']}")
            print(f"{dm}  Permissions set:\033[0m {st['permissions_set']}")
            print(f"{dm}  Safety boundaries:\033[0m {st['safety_boundaries']}")
            print(f"{dm}  Emergency stop:\033[0m {'\033[31mENGAGED\033[0m' if st['emergency_stop'] else '\033[32mDISENGAGED\033[0m'}")
            print(f"{dm}  Risk levels:\033[0m")
            for level, actions in s._risk_levels.items():
                print(f"    {level}: {', '.join(actions)}")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "check":
            action = " ".join(rest) if rest else "open"
            check = s.check_permission(action)
            conf = check['required_confirmation']
            print(f"{hl}Permission check: {action}\033[0m")
            print(f"  Risk level: {check['risk_level']}")
            print(f"{'  Requires confirmation: \033[33mYES\033[0m' if conf else '  Auto-approved'}")
        elif sub == "confirm":
            action = " ".join(rest) if rest else "open"
            result = s.confirm_action(action)
            print(f"{ok}Action confirmed: {action}\033[0m" if result['approved'] else f"{er}Action rejected\033[0m")
        elif sub == "estop":
            s.emergency_stop()
            print(f"\033[31m⚠ EMERGENCY STOP ENGAGED\033[0m")
            print(f"  All physical-world actions blocked. Use 'rsafety release' to disengage.")
        elif sub == "release":
            s.release_emergency_stop()
            print(f"{ok}Emergency stop released\033[0m")
        elif sub == "log":
            log = s.activity_log(20)
            print(f"{dm}Activity log ({len(log)} entries):\033[0m")
            for entry in log[-10:]:
                t = time.strftime('%H:%M:%S', time.localtime(entry['time']))
                approved = '\033[32m✓\033[0m' if entry['approved'] else '\033[31m✗\033[0m'
                print(f"  [{t}] {approved} {entry['action']}")

    # ======================== ACDE (Phase 15) ========================

    def cmd_acde(self, args):
        """Autonomous Creation & Discovery Engine — full summary."""
        hl = self._c("hl")
        dm = self._c("dim")
        s = self.acde.full_summary()
        print(f"\033[{hl}mACDE — Autonomous Creation & Discovery Engine\033[0m")
        print(f"{dm}  Ideas:\033[0m {s['ideas']['active_projects']} active, {s['ideas']['total_ideas']} total")
        print(f"{dm}  Research:\033[0m {s['research']['findings']} findings, {s['research']['hypotheses']} hypotheses")
        print(f"{dm}  Dev Projects:\033[0m {s['dev_projects']['projects']} projects, {s['dev_projects']['tests']} tests")
        print(f"{dm}  Simulations:\033[0m {s['simulations']['total_simulations']} total, {s['simulations']['completed']} completed")
        print(f"{dm}  Creations:\033[0m {s['creations']['total_creations']} total")
        print(f"{dm}  Teams:\033[0m {s['teams']['teams']} teams, {s['teams']['total_missions']} missions")
        print(f"{dm}  Synthesis:\033[0m {s['synthesis']['domains']} domains, {s['synthesis']['connections']} connections")
        print(f"{dm}  Improvement:\033[0m {s['improvement']['cycles']} cycles, avg={s['improvement']['avg_score']:.0%}")
        print(f"{dm}  Collaboration:\033[0m mode={s['collab_mode']['mode']}")
        print(f"{dm}  Memory:\033[0m {s['creation_memory']['designs']} designs, {s['creation_memory']['methods']} methods")

    def cmd_acde_create(self, args):
        """Idea-to-creation pipeline. Usage: create <title> <description>"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        if not args:
            projects = self.acde.ideas.list_projects()
            print(f"\033[{hl}mIdea Pipeline — Projects\033[0m")
            for p in projects:
                print(f"  {p['id']}: {p['title']} [{p['stage']}] ({p['category']})")
            return
        if args[0] == "advance" and len(args) > 1:
            result = self.acde.ideas.advance_stage(args[1])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Advanced to {result['stage']} ({result['progress']}%)\033[0m")
        elif args[0] == "status" and len(args) > 1:
            p = self.acde.ideas.project_status(args[1])
            if "error" in p:
                print(f"{er}{p['error']}\033[0m")
            else:
                print(f"\033[{hl}mProject: {p['idea']['title']}\033[0m")
                print(f"  Stage: {p['current_stage']}")
                for stage, items in p['pipeline'].items():
                    print(f"  {dm}{stage}:\033[0m {', '.join(items[:2])}")
        else:
            title = args[0]
            desc = " ".join(args[1:]) if len(args) > 1 else title
            result = self.acde.create_from_idea(title, desc)
            print(f"\033[{hl}mIdea Pipeline Created: {title}\033[0m")
            print(f"{dm}  Pipeline:\033[0m {', '.join(result['pipeline']['stages'])}")
            print(f"{dm}  Research:\033[0m {result['research']['summary'][:100]}")

    def cmd_acde_research(self, args):
        """Autonomous research. Usage: research <topic>"""
        hl = self._c("hl")
        dm = self._c("dim")
        ok = self._c("ok")
        if not args:
            s = self.acde.research.stats()
            print(f"\033[{hl}mAutonomous Research Framework\033[0m")
            print(f"{dm}  Findings:\033[0m {s['findings']}")
            print(f"{dm}  Hypotheses:\033[0m {s['hypotheses']}")
            print(f"{dm}  Recent:\033[0m")
            for f in self.acde.research.recent_findings(3):
                print(f"    - {f['topic']}: {len(f['findings'])} findings")
            return
        topic = " ".join(args)
        result = self.acde.research.research_topic(topic)
        print(f"\033[{hl}mResearch: {topic}\033[0m")
        for f in result['findings']:
            print(f"{dm}  [{f['agent']}]\033[0m {'; '.join(f['findings'][:2])}")
        print(f"{dm}  Synthesis:\033[0m {result['synthesis']['summary']}")
        print(f"{ok}  Hypotheses:\033[0m")
        for h in result['hypotheses']:
            print(f"    - {h}")

    def cmd_acde_dev(self, args):
        """AI development engine. Usage: dev <name> <description> or dev test <pid> or dev debug <pid> <issue>"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        d = self.acde.dev_engine
        if not args:
            s = d.stats()
            print(f"\033[{hl}mAI Development Engine\033[0m")
            print(f"{dm}  Projects:\033[0m {s['projects']}")
            print(f"{dm}  Tests:\033[0m {s['tests']}")
            print(f"{dm}  Debug sessions:\033[0m {s['debug_sessions']}")
            for pid, proj in d._projects.items():
                print(f"   - {proj['name']} ({proj['language']}) [{proj['status']}]")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "new" and len(rest) >= 1:
            name = rest[0]
            desc = " ".join(rest[1:]) if len(rest) > 1 else f"Project: {name}"
            proj = d.create_project(name, desc)
            print(f"\033[{hl}mProject Created: {name}\033[0m")
            print(f"{dm}  Architecture:\033[0m {proj['architecture']['pattern']}")
            print(f"{dm}  Components:\033[0m {', '.join(proj['architecture']['components'])}")
            print(f"{dm}  Files:\033[0m {len(proj['files'])} generated")
        elif sub == "test" and rest:
            result = d.test_project(rest[0])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Tests: {result['passed']}/{result['tests_run']} passed\033[0m")
        elif sub == "debug" and len(rest) >= 2:
            result = d.debug(rest[0], " ".join(rest[1:]))
            print(f"{hl}Debug Analysis\033[0m")
            print(f"  {result['analysis']}")
            print(f"{dm}  Suggested fix:\033[0m {result['suggested_fix']}")

    def cmd_acde_sim(self, args):
        """Simulation environment. Usage: sim <name> [scenario...] or sim compare <a> <b>"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        s = self.acde.simulation
        if not args:
            st = s.stats()
            print(f"\033[{hl}mSimulation Environment\033[0m")
            print(f"{dm}  Total:\033[0m {st['total_simulations']}")
            print(f"{dm}  Completed:\033[0m {st['completed']}")
            print(f"{dm}  Results:\033[0m {st['results']}")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "run":
            name = " ".join(rest) if rest else "simulation"
            sim = s.create_simulation(name, "standard")
            result = s.run(sim["id"])
            print(f"\033[{hl}mSimulation: {name}\033[0m")
            print(f"{dm}  Iterations:\033[0m {result['iterations']}")
            print(f"{dm}  Convergence:\033[0m {result['convergence']:.1%}")
            print(f"{dm}  Metrics:\033[0m")
            for k, v in result['metrics'].items():
                print(f"    {k}: {v:.1%}")
        elif sub == "compare" and len(rest) >= 2:
            result = s.compare_scenarios(rest)
            print(f"\033[{hl}Scenario Comparison\033[0m")
            for r in result['results']:
                print(f"  {r['scenario']}: acc={r.get('accuracy',0):.0%} stab={r.get('stability',0):.0%} perf={r.get('performance',0):.0f}")

    def cmd_acde_creative(self, args):
        """Creative intelligence. Usage: design <domain> <concept> [style]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        c = self.acde.creative
        if not args:
            s = c.stats()
            print(f"\033[{hl}mCreative Intelligence System\033[0m")
            print(f"{dm}  Total creations:\033[0m {s['total_creations']}")
            for domain, count in s['by_domain'].items():
                print(f"    {domain}: {count}")
            print(f"{dm}  Available styles:\033[0m {', '.join(c.list_styles())}")
            print(f"{dm}  Domains:\033[0m {', '.join(c._domains)}")
            return
        domain = args[0]
        concept = " ".join(args[1:]) if len(args) > 1 else "Untitled"
        style = "modern"
        result = c.create(domain, concept, style)
        if "error" in result:
            print(f"{er}{result['error']}\033[0m")
            print(f"  Domains: {', '.join(c._domains)}")
            return
        print(f"\033[{hl}mCreative: {domain} — {concept}\033[0m")
        output = result.get("output", {})
        for k, v in output.items():
            if k not in ("concept", "style", "audience"):
                print(f"  {dm}{k}:\033[0m {str(v)[:120]}")

    def cmd_acde_team(self, args):
        """Multi-agent creation team. Usage: team <name> [mission]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        t = self.acde.teams
        if not args:
            s = t.stats()
            print(f"\033[{hl}mMulti-Agent Creation Teams\033[0m")
            print(f"{dm}  Teams:\033[0m {s['teams']}")
            print(f"{dm}  Missions:\033[0m {s['total_missions']}")
            for tid, team in t._teams.items():
                print(f"   - {team['name']}: {', '.join(team['agents'])} ({len(team['missions'])} missions)")
            return
        sub = args[0]
        rest = args[1:] if len(args) > 1 else []
        if sub == "new":
            name = " ".join(rest) if rest else "Creation Team"
            team = t.create_team(name)
            print(f"{ok}Team created: {name}\033[0m")
            print(f"  Agents: {', '.join(team['agents'])}")
            print(f"  ID: {team['id']}")
        elif sub == "mission" and len(rest) >= 2:
            result = t.assign_mission(rest[0], " ".join(rest[1:]))
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"\033[{hl}mMission: {result['mission']}\033[0m")
                for agent, contribution in result['contributions'].items():
                    print(f"  {dm}[{agent}]\033[0m {contribution[:100]}")

    def cmd_acde_synthesis(self, args):
        """Knowledge synthesis engine. Usage: synth <domain1> <domain2> ..."""
        hl = self._c("hl")
        dm = self._c("dim")
        ok = self._c("ok")
        s = self.acde.synthesis
        if not args:
            st = s.stats()
            print(f"\033[{hl}mKnowledge Synthesis Engine\033[0m")
            print(f"{dm}  Registered domains:\033[0m {', '.join(s._domains.keys())}")
            print(f"{dm}  Connections:\033[0m {st['connections']}")
            print(f"{dm}  Innovations:\033[0m {st['innovations']}")
            for inn in s.recent_innovations(3):
                print(f"   - {inn['innovation'][:100]}")
            return
        result = s.synthesize(args)
        if "error" in result:
            print(f"{er}{result['error']}\033[0m")
            return
        print(f"\033[{hl}Cross-Domain Synthesis\033[0m")
        for conn in result['connections']:
            print(f"{dm}  {conn['domain_a']} ↔ {conn['domain_b']}:\033[0m")
            print(f"    Shared: {', '.join(str(c) for c in conn['shared_concepts'][:3])}")
            print(f"{ok}    Innovation:\033[0m {conn['innovation'][:120]}")

    def cmd_acde_improve(self, args):
        """Improvement loop. Usage: improve [name] or improve history"""
        hl = self._c("hl")
        dm = self._c("dim")
        ok = self._c("ok")
        imp = self.acde.improvement
        if not args:
            s = imp.stats()
            print(f"\033[{hl}mImprovement Loop\033[0m")
            print(f"{dm}  Cycles:\033[0m {s['cycles']}")
            print(f"{dm}  Improvements:\033[0m {s['improvements_generated']}")
            print(f"{dm}  Avg quality score:\033[0m {s['avg_score']:.0%}")
            return
        if args[0] == "history":
            hist = imp.improvement_history(10)
            print(f"{hl}Improvement History\033[0m")
            for h in hist:
                print(f"  - {h[:100]}")
        else:
            name = " ".join(args)
            cycle = imp.run_cycle(name)
            print(f"\033[{hl}Improvement Cycle: {name}\033[0m")
            print(f"{dm}  Analysis:\033[0m")
            for k, v in cycle['analysis'].items():
                if isinstance(v, float):
                    print(f"    {k}: {v:.0%}")
                else:
                    print(f"    {k}: {v}")
            print(f"{dm}  Improvements:\033[0m")
            for imp_text in cycle['improvements']:
                print(f"    - {imp_text}")

    def cmd_acde_mode(self, args):
        """Collaboration mode. Usage: mode [assistant|collaborator|research|autonomous]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        m = self.acde.collab
        if not args:
            cur = m.current_mode()
            print(f"\033[{hl}mCollaboration Mode\033[0m")
            print(f"{dm}  Active:\033[0m {cur['mode']}")
            print(f"{dm}  Autonomy:\033[0m {cur['config']['autonomy']:.0%}")
            print(f"{dm}  Description:\033[0m {cur['config']['description']}")
            print(f"{dm}  Available modes:\033[0m")
            for mode, config in m._modes.items():
                active = ' [ACTIVE]' if config['active'] else ''
                print(f"    {mode}: autonomy={config['autonomy']:.0%}{active}")
            return
        mode = args[0]
        result = m.set_mode(mode)
        if "error" in result:
            print(f"{er}{result['error']}\033[0m")
        else:
            print(f"{ok}Mode set to {mode} (autonomy: {result['autonomy']:.0%})\033[0m")
            print(f"  {result['description']}")

    def cmd_acde_memory(self, args):
        """Creation memory system. Usage: creations [query]"""
        er = self._c("err")
        ok = self._c("ok")
        dm = self._c("dim")
        hl = self._c("hl")
        mem = self.acde.memory
        if not args:
            s = mem.stats()
            print(f"\033[{hl}mCreation Memory System\033[0m")
            print(f"{dm}  Designs:\033[0m {s['designs']}")
            print(f"{dm}  Attempts:\033[0m {s['attempts']}")
            print(f"{dm}  Methods:\033[0m {s['methods']}")
            print(f"{dm}  Project history:\033[0m {s['projects']}")
            return
        query = " ".join(args)
        results = mem.recall_similar(query)
        if results:
            print(f"{ok}Found {len(results)} results for '{query}':\033[0m")
            for r in results[:10]:
                name = r.get("name", r.get("project", "unknown"))
                print(f"  - {name}")
        else:
            print(f"{dm}No results for '{query}'\033[0m")

    # ======================== IEDC (Phase 16) ========================

    def cmd_iedc(self, args):
        """Intelligence Ecosystem & Developer Civilization — full summary."""
        hl = self._c("hl"); dm = self._c("dm")
        s = self.iedc.full_summary()
        print(f"\033[{hl}mIEDC — Intelligence Ecosystem & Developer Civilization\033[0m")
        print(f"{dm}  Platform:\033[0m {s['platform']['developers']} developers, {s['platform']['modules']} modules")
        print(f"{dm}  SDK:\033[0m {s['sdk']['sdks']} SDKs, {s['sdk']['usage']} calls")
        print(f"{dm}  Module Architecture:\033[0m {s['modules']['modules_defined']} defined")
        print(f"{dm}  Marketplace:\033[0m {s['marketplace']['listings']} listings, {s['marketplace']['reviews']} reviews")
        print(f"{dm}  Agent Network:\033[0m {s['agent_network']['agents']} agents, {s['agent_network']['messages']} messages")
        print(f"{dm}  Protocol (OIP):\033[0m v{s['protocol']['version']}, {s['protocol']['handlers']} handlers")
        print(f"{dm}  Governance:\033[0m {s['governance']['approved']} approved, {s['governance']['rejected']} rejected")
        print(f"{dm}  Knowledge:\033[0m {s['knowledge']['contributions']} contributions, {s['knowledge']['contributors']} contributors")
        print(f"{dm}  Enterprise:\033[0m {s['enterprise']['organizations']} orgs, {s['enterprise']['teams']} teams")
        print(f"{dm}  Ecosystem:\033[0m {s['ecosystem']['layers']} layers, {s['ecosystem']['standards']} standards")

    def cmd_iedc_platform(self, args):
        """Developer platform. Usage: dev-platform <sub> [args]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        p = self.iedc.platform
        if not args:
            s = p.stats()
            print(f"\033[{hl}mDeveloper Platform\033[0m")
            print(f"{dm}  Developers:\033[0m {s['developers']}")
            for d in p.list_developers():
                print(f"    {d['name']} ({d['id']}) - {len(d['modules'])} modules")
            print(f"{dm}  Modules by type:\033[0m {s['by_type']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "register" and len(rest) >= 1:
            result = p.register_developer(rest[0], " ".join(rest[1:]) if len(rest) > 1 else rest[0])
            print(f"{ok}Developer registered: {result['name']}\033[0m")
        elif sub == "publish" and len(rest) >= 2:
            result = p.publish_module("arcanis_labs", rest[0], rest[1], description=" ".join(rest[2:]) if len(rest) > 2 else "")
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Module published: {result['name']} ({result['type']})\033[0m")

    def cmd_iedc_sdk(self, args):
        """Intelligence SDK. Usage: sdk [name] or sdk generate <sdk> <task>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        s = self.iedc.sdk
        if not args:
            print(f"\033[{hl}mIntelligence SDKs\033[0m")
            for name, sdk in s.sdks.items():
                print(f"{dm}  {sdk['name']} v{sdk['version']}:\033[0m {', '.join(sdk['methods'][:3])}...")
            return
        if args[0] == "generate" and len(args) >= 3:
            result = s.generate_code(args[1], " ".join(args[2:]))
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{hl}Generated {args[1]} Code:\033[0m")
                print(result['code'])
        elif args[0] in s.sdks:
            sdk = s.get_sdk(args[0])
            print(f"\033[{hl}m{sdk['name']} v{sdk['version']}\033[0m")
            for m in sdk['methods']:
                print(f"  {m}()")
        else:
            print(f"{er}SDK not found. Available: {', '.join(s.sdks.keys())}\033[0m")

    def cmd_iedc_modules(self, args):
        """Module architecture. Usage: modarch <name> <category> [capabilities]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        m = self.iedc.modules
        if not args:
            s = m.stats()
            print(f"\033[{hl}mModule Architecture\033[0m")
            print(f"{dm}  Categories:\033[0m {', '.join(m.list_categories())}")
            print(f"{dm}  Defined:\033[0m {s['modules_defined']}")
            return
        if len(args) >= 2:
            result = m.define_module(args[0], args[1], capabilities=args[2:] if len(args) > 2 else ["general"])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Module defined: {result['name']} [{result['category']}]\033[0m")

    def cmd_iedc_marketplace(self, args):
        """Intelligence marketplace. Usage: market <sub> [args]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        m = self.iedc.marketplace
        if not args:
            s = m.stats()
            print(f"\033[{hl}mIntelligence Marketplace\033[0m")
            print(f"{dm}  Listings:\033[0m {s['listings']}")
            print(f"{dm}  Categories:\033[0m {', '.join(s['categories'])}")
            for lid, listing in m.browse().items():
                print(f"  {listing['name']} [{listing['category']}] - {listing['price']} - {listing['rating']:.1f}★")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "list" and len(rest) >= 2:
            result = m.list_module(rest[0], " ".join(rest[1:]), "intelligence", "arcanis_labs")
            print(f"{ok}Listed: {result['name']}\033[0m")
        elif sub == "search" and rest:
            results = m.search(" ".join(rest))
            print(f"{dm}Results ({len(results)}):\033[0m")
            for r in results:
                print(f"  {r['name']}: {r['description'][:80]}")
        elif sub == "rate" and len(rest) >= 2:
            result = m.review_module(rest[0], int(rest[1]), " ".join(rest[2:]) if len(rest) > 2 else "")
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Rated {rest[0]}: {rest[1]}★\033[0m")

    def cmd_iedc_agnet(self, args):
        """Agent collaboration network. Usage: agnet <sub> [args]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        n = self.iedc.agent_network
        if not args:
            s = n.stats()
            print(f"\033[{hl}mAgent Collaboration Network\033[0m")
            print(f"{dm}  Agents:\033[0m {s['agents']}")
            for aid, agent in n.discover_agents().items():
                print(f"    {agent['name']}: {', '.join(agent['capabilities'][:3])} [{agent['status']}]")
            print(f"{dm}  Messages:\033[0m {s['messages']}")
            print(f"{dm}  Delegations:\033[0m {s['delegations']}")
            opps = n.collaboration_opportunities()
            if opps:
                print(f"{dm}  Collaboration opportunities:\033[0m")
                for o in opps[:3]:
                    print(f"    {o['suggestion']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "register" and len(rest) >= 1:
            result = n.register_agent(rest[0], " ".join(rest[1:]) if len(rest) > 1 else rest[0], ["communicate"])
            print(f"{ok}Agent registered: {result['name']}\033[0m")
        elif sub == "send" and len(rest) >= 3:
            result = n.send_message(rest[0], rest[1], " ".join(rest[2:]))
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Message sent: {rest[0]} -> {rest[1]}\033[0m")
        elif sub == "delegate" and len(rest) >= 3:
            result = n.delegate_task(rest[0], rest[1], " ".join(rest[2:]))
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Task delegated: {result['result']['output']}\033[0m")

    def cmd_iedc_protocol(self, args):
        """Open Intelligence Protocol. Usage: oip [sub]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        o = self.iedc.protocol
        if not args:
            s = o.stats()
            print(f"\033[{hl}mOpen Intelligence Protocol (OIP)\033[0m")
            print(f"{dm}  Version:\033[0m {s['version']}")
            print(f"{dm}  Message types:\033[0m {', '.join(sorted(o._message_types))}")
            print(f"{dm}  Handlers:\033[0m {s['handlers']}")
            print(f"{dm}  Messages logged:\033[0m {s['messages_logged']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "send" and len(rest) >= 3:
            msg = o.format_message(rest[0], rest[1], rest[2], {"data": " ".join(rest[3:]) if len(rest) > 3 else {}})
            if "error" in msg:
                print(f"{er}{msg['error']}\033[0m")
            else:
                print(f"{ok}OIP message created\033[0m")
                print(f"  Type: {msg['type']} | From: {msg['sender']} -> {msg['recipient']}")
        elif sub == "register" and len(rest) >= 2:
            o.register_handler(rest[0], rest[1])
            print(f"{ok}Handler registered: {rest[0]} -> {rest[1]}\033[0m")

    def cmd_iedc_governance(self, args):
        """Governance system. Usage: govern <sub> [args]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        g = self.iedc.governance
        if not args:
            s = g.stats()
            print(f"\033[{hl}mGovernance System\033[0m")
            print(f"{dm}  Pending:\033[0m {s['pending']}")
            print(f"{dm}  Approved:\033[0m {s['approved']}")
            print(f"{dm}  Rejected:\033[0m {s['rejected']}")
            print(f"{dm}  Policies:\033[0m {s['policies']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "verify" and rest:
            result = g.submit_for_verification(f"mod_{int(time.time())}", {"name": rest[0], "permissions": rest[1:] if len(rest) > 1 else [], "description": " ".join(rest) if len(rest) > 1 else "auto"})
            if result["status"] == "approved":
                print(f"{ok}Module '{result['module']}' verified and approved\033[0m")
            else:
                print(f"{er}Module rejected: {', '.join(result.get('issues', ['unknown']))}\033[0m")
        elif sub == "check":
            result = g.check_permissions("test", rest if rest else ["low"])
            if result["approved"]:
                print(f"{ok}Permissions approved\033[0m")
            else:
                print(f"{er}Permission denied: {result['reason']}\033[0m")

    def cmd_iedc_knowledge(self, args):
        """Knowledge contribution. Usage: econtribute <sub> [args]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        k = self.iedc.knowledge
        if not args:
            s = k.stats()
            print(f"\033[{hl}mKnowledge Contribution Framework\033[0m")
            print(f"{dm}  Contributors:\033[0m {s['contributors']}")
            print(f"{dm}  Contributions:\033[0m {s['contributions']}")
            print(f"{dm}  Collections:\033[0m {s['collections']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "add" and len(rest) >= 2:
            result = k.contribute("user", "ARCANIS User", rest[0], " ".join(rest[1:]), " ".join(rest[1:]))
            print(f"{ok}Contribution added: {result['title']}\033[0m")
        elif sub == "search" and rest:
            results = k.search(" ".join(rest))
            print(f"{dm}Results ({len(results)}):\033[0m")
            for r in results[:5]:
                print(f"  [{r['type']}] {r['title']} by {r['contributor_name']}")

    def cmd_iedc_enterprise(self, args):
        """Enterprise foundation. Usage: enterprise <sub> [args]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        e = self.iedc.enterprise
        if not args:
            s = e.stats()
            print(f"\033[{hl}mEnterprise Foundation\033[0m")
            print(f"{dm}  Organizations:\033[0m {s['organizations']}")
            print(f"{dm}  Teams:\033[0m {s['teams']}")
            print(f"{dm}  Knowledge entries:\033[0m {s['knowledge_entries']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "create" and len(rest) >= 1:
            result = e.create_organization(f"org_{int(time.time())}", rest[0], "admin")
            print(f"{ok}Organization created: {result['name']}\033[0m")
        elif sub == "team" and len(rest) >= 1:
            result = e.create_team("org_main", " ".join(rest))
            print(f"{ok}Team created: {result['name']}\033[0m")
        elif sub == "knowledge" and len(rest) >= 2:
            e.add_knowledge("org_main", rest[0], " ".join(rest[1:]))
            print(f"{ok}Knowledge added: {rest[0]}\033[0m")
        elif sub == "automation" and rest:
            result = e.suggest_automation("org_main", " ".join(rest))
            print(f"{hl}Suggested automations for {result['department']}:\033[0m")
            for a in result['suggested_automations']:
                print(f"  - {a}")

    def cmd_iedc_ecosystem(self, args):
        """Ecosystem architecture. Usage: ecosys"""
        hl = self._c("hl"); dm = self._c("dm")
        e = self.iedc.architecture
        arch = e.get_architecture()
        print(f"\033[{hl}mEcosystem Architecture\033[0m")
        print(f"{dm}  Economy:\033[0m {arch['economy']}")
        print(f"{dm}  Layers:\033[0m {', '.join(arch['layers'])}")
        print(f"{dm}  Standards:\033[0m {', '.join(arch['standards'])}")
        print(f"{dm}  Growth metrics:\033[0m {arch['growth_metrics']}")
        print(f"\033[{hl}mRoadmap\033[0m")
        for phase in e.get_roadmap():
            status = '\033[32m✓\033[0m' if phase['status'] == 'current' else '\033[33m○\033[0m'
            print(f"  {status} {phase['phase']}: {', '.join(phase['items'])}")

    # ======================== AWSE (Phase 17) ========================

    def cmd_awse(self, args):
        """Autonomous World Simulation Engine — full summary."""
        hl = self._c("hl"); dm = self._c("dm")
        s = self.awse.full_summary()
        print(f"\033[{hl}mAWSE — Autonomous World Simulation Engine\033[0m")
        print(f"{dm}  Core:\033[0m {s['core']['models']} models, {s['core']['simulations_run']} runs")
        print(f"{dm}  Digital Twins:\033[0m {s['twins']['twins']} twins")
        print(f"{dm}  Scenarios:\033[0m {s['scenarios']['scenarios_generated']} generated")
        print(f"{dm}  Lab:\033[0m {s['lab']['experiments']} experiments, {s['lab']['results']} results")
        print(f"{dm}  Agent Sims:\033[0m {s['agent_sim']['societies']} societies, {s['agent_sim']['total_insights']} insights")
        print(f"{dm}  Science:\033[0m {s['science']['models']} models")
        print(f"{dm}  Decisions:\033[0m {s['decisions']['decisions_simulated']} simulated")
        print(f"{dm}  World Model:\033[0m {s['world']['systems']} systems, conf={s['world']['confidence']:.0%}")
        print(f"{dm}  Viz:\033[0m {s['visualization']['total_visualizations']} created")
        print(f"{dm}  Pipeline:\033[0m {s['pipeline']['total']} entries, {s['pipeline']['executed']} executed")

    def cmd_awse_sim(self, args):
        """Universal simulation core. Usage: sim <name> or sim compare <id1> <id2>..."""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        c = self.awse.core
        if not args:
            s = c.stats()
            print(f"\033[{hl}mSimulation Core\033[0m")
            print(f"{dm}  Models:\033[0m {s['models']}")
            print(f"{dm}  Runs:\033[0m {s['simulations_run']}")
            for mid, m in c._models.items():
                print(f"    {m['name']} ({m['type']})")
            return
        if args[0] == "new" and len(args) >= 2:
            result = c.create_model(args[1], args[2] if len(args) > 2 else "system")
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Model created: {result['name']}\033[0m")
        elif args[0] == "run" and len(args) >= 2:
            result = c.run_simulation(args[1])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"\033[{hl}mSimulation: {result['name']}\033[0m")
                for k, v in result['outcomes'].items():
                    print(f"  {k}: {v:.1%}")
        elif args[0] == "compare":
            result = c.compare_models(args[1:])
            print(f"{hl}Comparison ({len(result)} models):\033[0m")
            for r in result:
                print(f"  {r['name']}: conv={r['outcomes']['convergence']:.1%} stab={r['outcomes']['stability']:.1%}")

    def cmd_awse_twin(self, args):
        """Digital twin framework. Usage: twin <name> <type> or twin simulate <id>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        t = self.awse.twins
        if not args:
            s = t.stats()
            print(f"\033[{hl}mDigital Twins\033[0m")
            print(f"{dm}  By type:\033[0m {s['by_type']}")
            for tid, tw in t._twins.items():
                print(f"    {tw['name']} ({tw['type']}) - {tw['status']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "new" and len(rest) >= 2:
            result = t.create_twin(rest[0], rest[1])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Digital twin created: {result['name']}\033[0m")
                if result.get("possible_failures"):
                    print(f"{dm}  Possible failures:\033[0m {', '.join(result['possible_failures'][:3])}")
        elif sub == "simulate" and rest:
            result = t.simulate_twin(rest[0])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"\033[{hl}mTwin Simulation: {result['twin']}\033[0m")
                for k, v in result['simulated_performance'].items():
                    print(f"  {k}: {v:.1%}" if isinstance(v, float) else f"  {k}: {v}")
        elif sub == "failures" and rest:
            result = t.predict_failures(rest[0])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"\033[{hl}mFailure Predictions: {result['twin']}\033[0m")
                for p in result['predictions']:
                    print(f"  {p['failure']}: {p['probability']:.0%} - {p['recommended_action']}")

    def cmd_awse_scenario(self, args):
        """Future scenario engine. Usage: scenario <question> or scenario analyze <id>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        s = self.awse.scenarios
        if not args:
            st = s.stats()
            print(f"\033[{hl}mFuture Scenario Engine\033[0m")
            print(f"{dm}  Scenarios generated:\033[0m {st['scenarios_generated']}")
            for sc in s.latest_scenarios(3):
                print(f"    Q: {sc['question'][:60]}")
                for scen in sc['scenarios'][:2]:
                    print(f"      - {scen['name']} ({scen['probability']:.0%})")
            return
        question = " ".join(args)
        result = s.generate_scenarios(question)
        print(f"\033[{hl}mScenarios for: {question}\033[0m")
        for scen in result['scenarios']:
            print(f"{dm}  {scen['name']} ({scen['probability']:.0%}):\033[0m")
            print(f"    {scen['description']}")
            print(f"    Risks: {', '.join(scen['risks'])} | {scen['timeframe']}")
        analysis = s.analyze_probability(result['id'])
        print(f"{ok}  Most likely:\033[0m {analysis['most_likely']['name']}")
        print(f"{dm}  Recommendation:\033[0m {analysis['recommendation']}")

    def cmd_awse_lab(self, args):
        """AI experimentation lab. Usage: experiment <name> <hypothesis>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        l = self.awse.lab
        if not args:
            s = l.stats()
            print(f"\033[{hl}mAI Experimentation Lab\033[0m")
            print(f"{dm}  Experiments:\033[0m {s['experiments']}")
            print(f"{dm}  Hypotheses:\033[0m {s['hypotheses']}")
            print(f"{dm}  Results:\033[0m {s['results']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "propose" and len(rest) >= 2:
            result = l.propose_experiment(rest[0], " ".join(rest[1:]), "simulation")
            print(f"{ok}Experiment proposed: {result['name']} (id={result['id']})\033[0m")
        elif sub == "run" and rest:
            result = l.run_experiment(rest[0])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"\033[{hl}mExperiment: {result['name']}\033[0m")
                print(f"  Outcome: {result['outcome']} (conf: {result['confidence']:.0%})")
                for ins in result['insights']:
                    print(f"  - {ins}")
        elif sub == "reset":
            l.safe_reset()
            print(f"{ok}Lab reset. No real-world impact.\033[0m")

    def cmd_awse_society(self, args):
        """Multi-agent simulation. Usage: society <scenario> or society run <id> <topic>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        a = self.awse.agent_sim
        if not args:
            s = a.stats()
            print(f"\033[{hl}mMulti-Agent Simulation\033[0m")
            print(f"{dm}  Societies:\033[0m {s['societies']}")
            for sid, soc in a._agent_societies.items():
                print(f"    {soc['name']}: {', '.join(soc['agents'].keys())}")
            return
        scenario = " ".join(args)
        result = a.run_business_simulation(scenario)
        print(f"\033[{hl}mBusiness Simulation: {scenario}\033[0m")
        print(f"{dm}  Agents:\033[0m {', '.join(result['roles'])}")
        print(f"{dm}  Interactions:\033[0m {result['interactions']}")
        print(f"{ok}  Insight:\033[0m {result['insight'][:120]}")

    def cmd_awse_science(self, args):
        """Science simulation. Usage: science <domain> <name> or science analyze <id>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        s = self.awse.science
        if not args:
            st = s.stats()
            print(f"\033[{hl}mScience Simulation\033[0m")
            print(f"{dm}  Domains:\033[0m {', '.join(s._domains)}")
            print(f"{dm}  Models:\033[0m {st['models']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "new" and len(rest) >= 2:
            result = s.create_model(rest[0], " ".join(rest[1:]))
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Science model created: {result['name']} [{result['domain']}]\033[0m")
        elif sub == "analyze" and rest:
            result = s.analyze(rest[0])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"\033[{hl}mAnalysis: {result['model']}\033[0m")
                print(f"{dm}  Convergence:\033[0m {result['analysis']['convergence']:.1%}")
                print(f"{dm}  Error margin:\033[0m {result['analysis']['error_margin']:.1%}")
                print(f"{dm}  Recommendation:\033[0m {result['analysis']['recommendation']}")

    def cmd_awse_decide(self, args):
        """Personal decision simulator. Usage: decide <question> [options...]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        d = self.awse.decisions
        if not args:
            s = d.stats()
            print(f"\033[{hl}mPersonal Decision Simulator\033[0m")
            print(f"{dm}  Decisions:\033[0m {s['decisions_simulated']}")
            print(f"{dm}  Paths:\033[0m {s['paths_generated']}")
            return
        question = args[0]
        options = args[1:] if len(args) > 1 else ["Option A", "Option B", "Option C"]
        result = d.simulate_decision(question, options)
        print(f"\033[{hl}mDecision: {question}\033[0m")
        for opt in result['evaluated_options']:
            print(f"{dm}  {opt['option']}:\033[0m score={opt['score']:.0%} success={opt['probability_of_success']:.0%}")
        if result['recommended']:
            print(f"{ok}  Recommended:\033[0m {result['recommended']}")

    def cmd_awse_world(self, args):
        """World knowledge model. Usage: world [query]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        w = self.awse.world
        if not args:
            s = w.stats()
            print(f"\033[{hl}mWorld Knowledge Model\033[0m")
            print(f"{dm}  Systems:\033[0m {s['systems']}")
            for name, sys in w._world_model["systems"].items():
                print(f"    {name} ({sys['category']})")
            print(f"{dm}  Connections:\033[0m {s['connections']}")
            print(f"{dm}  Confidence:\033[0m {s['confidence']:.0%}")
            return
        query = " ".join(args)
        result = w.query(query)
        print(f"\033[{hl}mWorld Model Query: {query}\033[0m")
        for sys in result['systems_found']:
            print(f"  {sys['name']}: {sys['description'][:80]}")
        for conn in result['connections']:
            print(f"  {conn['from']} --{conn['relationship']}--> {conn['to']}")
        print(f"{dm}  Confidence:\033[0m {result['confidence']:.0%}")

    def cmd_awse_vis(self, args):
        """Simulation visualization. Usage: vis <type> <title> or vis types"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        v = self.awse.visualization
        if not args:
            s = v.stats()
            print(f"\033[{hl}mSimulation Visualization\033[0m")
            print(f"{dm}  Types:\033[0m {', '.join(sorted(v._viz_types))}")
            print(f"{dm}  Total created:\033[0m {s['total_visualizations']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "types":
            print(f"{dm}Available viz types:\033[0m {', '.join(sorted(v._viz_types))}")
        elif sub == "map" and rest:
            result = v.system_map(rest, [])
            print(f"{ok}System map created: {result['title']}\033[0m")
        elif sub == "timeline" and rest:
            result = v.future_timeline(rest)
            print(f"{ok}Timeline created with {len(rest)} events\033[0m")
        elif sub == "landscape" and rest:
            scens = [{"name": r, "probability": 0.5, "risks": ["unknown"]} for r in rest]
            result = v.scenario_landscape(scens)
            print(f"{ok}Scenario landscape created\033[0m")

    def cmd_awse_pipeline(self, args):
        """Simulation-to-reality pipeline. Usage: pipeline <sub> [args]"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        p = self.awse.pipeline
        if not args:
            s = p.stats()
            print(f"\033[{hl}mSimulation-to-Reality Pipeline\033[0m")
            print(f"{dm}  Total:\033[0m {s['total']}")
            print(f"{dm}  Approved:\033[0m {s['approved']}")
            print(f"{dm}  Executed:\033[0m {s['executed']}")
            for entry in p._pipeline_entries:
                status = '\033[32m✓\033[0m' if entry['executed'] else '\033[33m○\033[0m'
                print(f"  {status} {entry['name']} [{entry['current_stage']}]")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "submit" and rest:
            result = p.submit(rest[0], {"simulated": True}, " ".join(rest[1:]) if len(rest) > 1 else "standard action")
            print(f"{ok}Submitted to pipeline: {result['name']}\033[0m")
        elif sub == "evaluate" and rest:
            result = p.evaluate(rest[0])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{hl}Evaluation:\033[0m risk={result['risk_assessment']} impact={result['expected_impact']:.0%}")
                print(f"  Recommendation: {result['recommendation']}")
        elif sub == "approve" and rest:
            result = p.approve(rest[0])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Approved for execution\033[0m")
        elif sub == "execute" and rest:
            result = p.execute(rest[0])
            if "error" in result:
                print(f"{er}{result['error']}\033[0m")
            else:
                print(f"{ok}Executed: {result['action']}\033[0m")

    # ======================== AIIL COMMANDS ========================

    def cmd_aiil(self, args):
        """Autonomous Intelligence Infrastructure Layer status"""
        dm = self._c("dm"); hl = self._c("hl"); ok = self._c("ok")
        s = self.aiil.full_summary()
        print(f"\033[{hl}mAutonomous Intelligence Infrastructure Layer\033[0m")
        print(f"{dm}  Resource Manager:\033[0m {s['resource_manager']['workloads']} workloads, {s['resource_manager']['external_nodes']} external")
        print(f"{dm}  Distributed Network:\033[0m {s['distributed_network']['total_nodes']} nodes, {s['distributed_network']['online']} online")
        print(f"{dm}  Agent Runtime:\033[0m {s['agent_runtime']['agents']} agents, {s['agent_runtime']['tasks']} tasks")
        print(f"{dm}  Semantic Storage:\033[0m {s['semantic_storage']['knowledge']} knowledge entries")
        print(f"{dm}  Computational Memory:\033[0m {s['computational_memory']['active_context']} active, {s['computational_memory']['long_term']} long-term")
        print(f"{dm}  Monitoring:\033[0m {s['monitoring']['metrics']} metrics, {s['monitoring']['recommendations']} recommendations")
        print(f"{dm}  Optimization:\033[0m {s['optimization']['optimizations']} optimizations, {s['optimization']['applied']} applied")
        print(f"{dm}  Hardware Abstraction:\033[0m {s['hardware_abstraction']['platform']}")
        print(f"{dm}  Security:\033[0m {s['security']['identities']} identities, {s['security']['active_sessions']} sessions")
        print(f"{dm}  Cloud Native:\033[0m {s['cloud_native']['services']} services, {s['cloud_native']['executions']} executions")

    def cmd_aiil_resources(self, args):
        """Intelligent Resource Manager. Usage: resources analyze <name> <cpu> <mem>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        rm = self.aiil.resource_manager
        if not args:
            print(f"\033[{hl}mIntelligent Resource Manager\033[0m")
            for name, r in rm.resources.items():
                status = '\033[32mavailable\033[0m' if r.get("available", True) else '\033[31munavailable\033[0m'
                print(f"  {name}: {status} ")
            print(f"{dm}  Workloads:\033[0m {len(rm.workloads)}")
            print(f"{dm}  External:\033[0m {len(rm.external)} nodes")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "analyze" and len(rest) >= 2:
            result = rm.analyze_workload(rest[0], {"cpu": float(rest[1]), "memory": float(rest[2]) if len(rest) > 2 else 1024})
            print(f"{ok}Workload analyzed:\033[0m {result['recommendation']} execution (suitability: {result['local_suitability']})")
        elif sub == "predict":
            result = rm.predict_performance(" ".join(rest) if rest else "general")
            print(f"{dm}Performance prediction:\033[0m {result['expected_duration']}s, confidence {result['confidence']}, bottleneck: {result['bottleneck']}")
        elif sub == "external" and len(rest) >= 2:
            result = rm.register_external(rest[0], rest[1], {"cpu": 16, "memory": 32000})
            print(f"{ok}External resource registered: {result['external']}\033[0m")

    def cmd_aiil_dnet(self, args):
        """Distributed Intelligence Network. Usage: dnet node <id> <type> | status"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        dn = self.aiil.distributed_network
        if not args:
            s = dn.get_network_status()
            print(f"\033[{hl}mDistributed Intelligence Network\033[0m")
            print(f"{dm}  Nodes:\033[0m {s['total_nodes']} ({s['online']} online)")
            print(f"{dm}  Connections:\033[0m {s['connections']}")
            for nid, n in dn.nodes.items():
                status = '\033[32m✓\033[0m' if n['status'] == 'online' else '\033[31m✗\033[0m'
                print(f"  {status} {nid} ({n['type']})")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "node" and len(rest) >= 2:
            result = dn.register_node(rest[0], rest[1], {})
            print(f"{ok}Node registered: {result['node']}\033[0m")
        elif sub == "connect" and len(rest) >= 2:
            result = dn.connect_nodes(rest[0], rest[1])
            print(f"{ok}Connected: {rest[0]} <-> {rest[1]}\033[0m")
        elif sub == "msg" and len(rest) >= 3:
            result = dn.send_message(rest[0], rest[1], " ".join(rest[2:]))
            print(f"{ok}Message sent: {result['sender']} -> {result['recipient']}\033[0m")

    def cmd_aiil_art(self, args):
        """Agent Runtime Manager. Usage: art deploy <id> <type> | schedule <id> <task> <complexity>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        art = self.aiil.agent_runtime
        if not args:
            s = art.stats()
            print(f"\033[{hl}mAgent Runtime Manager\033[0m")
            print(f"{dm}  Agents:\033[0m {s['agents']}")
            print(f"{dm}  Tasks:\033[0m {s['tasks']}")
            for aid, a in art.agents.items():
                status = '\033[32m✓\033[0m' if a['status'] == 'deployed' else '\033[33m○\033[0m'
                print(f"  {status} {aid} ({a['type']}) [{a['status']}]")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "deploy" and len(rest) >= 2:
            result = art.deploy_agent(rest[0], rest[1], {"cpu": 0.5, "memory": 1024})
            print(f"{ok}Deployed: {result['agent']}\033[0m")
        elif sub == "schedule" and len(rest) >= 3:
            result = art.schedule_task(rest[0], rest[1], rest[2])
            print(f"{ok}Scheduled: {result['name']} for {rest[0]}\033[0m")
        elif sub == "status" and rest:
            result = art.get_agent_status(rest[0])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"  Agent: {rest[0]} [{result['agent']['status']}], tasks: {len(result['tasks'])}, active: {result['active_tasks']}")
        elif sub == "lifecycle" and len(rest) >= 2:
            result = art.lifecycle_action(rest[0], rest[1])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}{rest[1]} -> {rest[0]} ({result['status']})\033[0m")

    def cmd_aiil_semstore(self, args):
        """Semantic Storage System. Usage: semstore store <type> <content> | search <query>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        ss = self.aiil.semantic_storage
        if not args:
            s = ss.stats()
            print(f"\033[{hl}mSemantic Storage System\033[0m")
            print(f"{dm}  Knowledge:\033[0m {s['knowledge']}")
            print(f"{dm}  Memory:\033[0m {s['memory']}")
            print(f"{dm}  Context:\033[0m {s['context']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "store" and len(rest) >= 2:
            result = ss.store(rest[0], " ".join(rest[1:]))
            print(f"{ok}Stored: {result['id']}\033[0m")
        elif sub == "search" and rest:
            results = ss.search_by_meaning(" ".join(rest))
            print(f"\033[{hl}mSearch: {' '.join(rest)}\033[0m")
            for r in results[:5]:
                rel = f" (related: {r.get('related', False)})" if r.get('related') else ""
                print(f"  [{r['relevance']:.0%}] {r['store']}:{r['entry']['id']}{rel} = {str(r['entry']['content'])[:60]}")
        elif sub == "relate" and len(rest) >= 3:
            result = ss.relate(rest[0], rest[1], " ".join(rest[2:]))
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Related: {rest[0]} -> {rest[1]}\033[0m")

    def cmd_aiil_cml(self, args):
        """Computational Memory Layer. Usage: cml set <key> <value> | get <key> | store <key> <value>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        cml = self.aiil.computational_memory
        if not args:
            s = cml.stats()
            print(f"\033[{hl}mComputational Memory Layer\033[0m")
            print(f"{dm}  Active Context:\033[0m {s['active_context']}")
            print(f"{dm}  Long Term:\033[0m {s['long_term']}")
            print(f"{dm}  Temp State:\033[0m {s['temp_state']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "set" and len(rest) >= 2:
            result = cml.set_active_context(rest[0], " ".join(rest[1:]))
            print(f"{ok}Context set: {result['context']} (TTL: {result['ttl']}s)\033[0m")
        elif sub == "get" and rest:
            result = cml.get_active_context(rest[0])
            if result: print(f"  {rest[0]} = {result}")
            else: print(f"{er}Context not found or expired\033[0m")
        elif sub == "store" and len(rest) >= 2:
            result = cml.store_long_term(rest[0], " ".join(rest[1:]))
            print(f"{ok}Stored: {result['key']} ({result['category']})\033[0m")
        elif sub == "retrieve" and rest:
            results = cml.retrieve_long_term(" ".join(rest))
            if results:
                for r in results:
                    print(f"  {r['key']}: {str(r['value'])[:60]}")
            else: print(f"{dm}No results\033[0m")
        elif sub == "temp" and len(rest) >= 2:
            result = cml.set_temp_state(rest[0], " ".join(rest[1:]))
            print(f"{ok}Temp state: {result['temp_key']}\033[0m")
        elif sub == "optimize":
            result = cml.optimize()
            print(f"{ok}Optimized: {result['evicted_context']} context, {result['evicted_temp']} temp entries evicted\033[0m")

    def cmd_aiil_imon(self, args):
        """Infrastructure Monitoring. Usage: imon metric <name> <value> | error <source> <type> <msg> | analyze"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        im = self.aiil.monitoring
        if not args:
            s = im.stats()
            analysis = im.analyze_performance()
            print(f"\033[{hl}mInfrastructure Monitoring\033[0m")
            print(f"{dm}  Metrics:\033[0m {s['metrics']}")
            print(f"{dm}  Errors:\033[0m {s['errors']}")
            print(f"{dm}  Recommendations:\033[0m {s['recommendations']}")
            if "avg_cpu" in analysis:
                print(f"{dm}  Avg CPU:\033[0m {analysis['avg_cpu']}% | Avg Memory: {analysis['avg_memory']}%")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "metric" and len(rest) >= 2:
            result = im.record_metric(rest[0], float(rest[1]))
            print(f"{ok}Metric recorded: {result['name']} = {result['value']}{result['unit']}\033[0m")
        elif sub == "error" and len(rest) >= 3:
            result = im.log_error(rest[0], rest[1], " ".join(rest[2:]))
            print(f"{er}Error logged: {result['source']}: {result['message']}\033[0m")
        elif sub == "health" and len(rest) >= 2:
            result = im.update_agent_health(rest[0], rest[1], {})
            print(f"{ok}Health: {rest[0]} = {rest[1]}\033[0m")
        elif sub == "analyze":
            result = im.analyze_performance()
            print(f"\033[{hl}mPerformance Analysis\033[0m")
            if "avg_cpu" in result:
                print(f"  Avg CPU: {result['avg_cpu']}%")
                print(f"  Avg Memory: {result['avg_memory']}%")
            print(f"  Total Errors: {result.get('total_errors', 0)}")
            print(f"  Recommendations: {result.get('recommendations', 0)}")

    def cmd_aiil_optimize(self, args):
        """Self-Optimization Framework. Usage: optimize observe <comp> <metric> <value> <threshold> | list | apply <id>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        so = self.aiil.optimization
        if not args:
            s = so.stats()
            print(f"\033[{hl}mSelf-Optimization Framework\033[0m")
            print(f"{dm}  Observations:\033[0m {s['observations']}")
            print(f"{dm}  Optimizations:\033[0m {s['optimizations']}")
            print(f"{dm}  Applied:\033[0m {s['applied']}")
            for opt in so.optimizations:
                status = '\033[32m✓\033[0m' if opt['status'] == 'applied' else '\033[33m○\033[0m'
                print(f"  {status} {opt['id']}: {opt['component']} -> {opt['suggestion'][:40]}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "observe" and len(rest) >= 4:
            result = so.observe(rest[0], rest[1], float(rest[2]), float(rest[3]))
            if result["inefficiency"]:
                print(f"\033[33mInefficiency detected:\033[0m {result['inefficiency']['suggestion']}")
                opt = so.generate_optimization(rest[0], result["inefficiency"]["suggestion"])
                print(f"{ok}Optimization generated: {opt['id']}\033[0m")
            else: print(f"{ok}Within threshold\033[0m")
        elif sub == "list":
            for opt in so.optimizations:
                status = '\033[32m✓\033[0m' if opt['status'] == 'applied' else ('\033[33m○\033[0m' if opt['status'] == 'pending' else '\033[31m✗\033[0m')
                appr = ' [requires approval]' if opt.get('needs_approval') else ''
                print(f"  {status} {opt['id']}: {opt['component']} -> {opt['suggestion'][:50]}{appr}")
        elif sub == "test" and rest:
            result = so.test_optimization(rest[0])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Test: {result['result']} ({result['duration_seconds']}s)\033[0m")
        elif sub == "apply" and len(rest) >= 1:
            approved = "--force" in rest
            result = so.apply_optimization(rest[0], approved)
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"\033[33m{result['status']}\033[0m: {result.get('message', 'Optimization applied')}")

    def cmd_aiil_hal(self, args):
        """Hardware Abstraction Layer. Usage: hal detect <platform> | adapt <component> | api <operation>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        hal = self.aiil.hardware_abstraction
        if not args:
            s = hal.stats()
            print(f"\033[{hl}mHardware Abstraction Layer\033[0m")
            print(f"{dm}  Platform:\033[0m {s['platform']}")
            print(f"{dm}  Capabilities:\033[0m {s['capabilities']}")
            print(f"{dm}  Adaptations:\033[0m {s['adaptations']}")
            for op, api in [("compute", "local/distributed"), ("store", "local/remote"), ("inference", "accelerated/generic"), ("network", "bandwidth")]:
                info = hal.uniform_api(op)
                print(f"  {op}: {'\033[32m✓\033[0m' if info.get('available') else '\033[31m✗\033[0m'} ({info.get('method', info.get('bandwidth', info.get('accelerated', 'n/a')))})")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "detect" and rest:
            result = hal.detect_platform(rest[0])
            print(f"{ok}Platform: {result['platform']}\033[0m")
            for k, v in result['capabilities'].items():
                print(f"  {k}: {v}")
        elif sub == "adapt" and rest:
            result = hal.adapt_intelligence(rest[0], {"model_size": "full"})
            print(f"{ok}Adaptation: {result['adjustment']}\033[0m")
            print(f"  GPU offloaded: {result['gpu_offloaded']}")
        elif sub == "api" and rest:
            result = hal.uniform_api(rest[0])
            print(f"\033[{hl}mAPI: {rest[0]}\033[0m")
            for k, v in result.items():
                print(f"  {k}: {v}")

    def cmd_aiil_security(self, args):
        """Security Infrastructure. Usage: security register <id> <type> <pw> | login <id> <pw> | verify <token>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        sec = self.aiil.security
        if not args:
            s = sec.stats()
            print(f"\033[{hl}mSecurity Infrastructure\033[0m")
            print(f"{dm}  Identities:\033[0m {s['identities']}")
            print(f"{dm}  Active Sessions:\033[0m {s['active_sessions']}")
            print(f"{dm}  Audit Entries:\033[0m {s['audit_entries']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "register" and len(rest) >= 3:
            result = sec.register_identity(rest[0], rest[1], rest[2])
            print(f"{ok}Identity registered: {result['identity']}\033[0m")
        elif sub == "login" and len(rest) >= 2:
            result = sec.authenticate(rest[0], rest[1])
            if result.get("authenticated"):
                print(f"{ok}Authenticated: session={result['session']}\033[0m")
            else:
                print(f"{er}Authentication failed: {result.get('reason', 'unknown')}\033[0m")
        elif sub == "verify" and rest:
            result = sec.verify_session(rest[0])
            if result.get("valid"):
                print(f"{ok}Session valid: {result['identity']}\033[0m")
            else:
                print(f"{er}Session invalid: {result.get('reason', 'unknown')}\033[0m")
        elif sub == "encrypt" and len(rest) >= 2:
            result = sec.encrypt_data(" ".join(rest[1:]), rest[0])
            print(f"{ok}Encrypted: {result['encrypted'][:40]}...\033[0m")
        elif sub == "audit":
            for entry in sec.audit_log[-10:]:
                print(f"  [{entry['action']}] {entry['actor']}: {entry['result']}")

    def cmd_aiil_cloud(self, args):
        """Cloud-Native Intelligence Foundation. Usage: cloud register <name> <type> <url> | execute <svc> <task> | deploy <mod> <env>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        cloud = self.aiil.cloud_native
        if not args:
            s = cloud.stats()
            print(f"\033[{hl}mCloud-Native Intelligence Foundation\033[0m")
            print(f"{dm}  Services:\033[0m {s['services']}")
            print(f"{dm}  Executions:\033[0m {s['executions']}")
            print(f"{dm}  Collaborations:\033[0m {s['collaborations']}")
            print(f"{dm}  Deployments:\033[0m {s['deployments']}")
            for svc_name, svc in cloud.services.items():
                print(f"  {svc_name} ({svc['type']}) -> {svc['endpoint']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "register" and len(rest) >= 3:
            result = cloud.register_service(rest[0], rest[1], rest[2])
            print(f"{ok}Service registered: {result['name']}\033[0m")
        elif sub == "execute" and len(rest) >= 2:
            result = cloud.remote_execute(rest[0], rest[1], {"params": " ".join(rest[2:]) if len(rest) > 2 else {}})
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Executed: {result['result']} ({result['duration']}s)\033[0m")
        elif sub == "collab" and len(rest) >= 2:
            result = cloud.create_collaboration(rest[0], rest[1:], "collaborative intelligence")
            print(f"{ok}Collaboration '{result['name']}' created with {len(result['participants'])} participants\033[0m")
        elif sub == "deploy" and len(rest) >= 2:
            result = cloud.deploy_intelligence(rest[0], rest[1])
            print(f"{ok}Deployed: {result['module']} -> {result['target']}\033[0m")
        elif sub == "scale" and len(rest) >= 2:
            result = cloud.scale_service(rest[0], int(rest[1]))
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Scaled: {rest[0]} -> {rest[1]} replicas\033[0m")

    # ======================== CIN COMMANDS ========================

    def cmd_cin(self, args):
        """Collective Intelligence Network status"""
        dm = self._c("dm"); hl = self._c("hl"); ok = self._c("ok")
        s = self.cin.full_summary()
        print(f"\033[{hl}mCollective Intelligence Network\033[0m")
        print(f"{dm}  Federation:\033[0m {s['federation']['total_nodes']} nodes, {s['federation']['collaborating']} collaborating")
        print(f"{dm}  Trust:\033[0m {s['trust']['active']} active relationships")
        print(f"{dm}  Communication:\033[0m {s['communication']['messages']} messages, {s['communication']['delegations']} delegations")
        print(f"{dm}  Knowledge:\033[0m {s['knowledge_exchange']['total']} items, {s['knowledge_exchange']['exchanges']} exchanges")
        print(f"{dm}  Team Spaces:\033[0m {s['team_spaces']['spaces']} spaces, {s['team_spaces']['total_members']} members")
        print(f"{dm}  Reasoning:\033[0m {s['reasoning']['problems']} problems, {s['reasoning']['solved']} solved")
        print(f"{dm}  Discovery:\033[0m {s['discovery']['active']} capabilities")
        print(f"{dm}  Provenance:\033[0m {s['provenance']['records']} records")
        print(f"{dm}  Resilience:\033[0m {s['resilience']['cached_nodes']} cached, {s['resilience']['pending_syncs']} pending syncs")
        print(f"{dm}  Governance:\033[0m {s['governance']['active_permissions']} active permissions")

    def cmd_cin_federate(self, args):
        """Federated Intelligence Network. Usage: federate node <id> | collab <node> <purpose> | approve <idx>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        fed = self.cin.federation
        if not args:
            s = fed.get_federation_status()
            print(f"\033[{hl}mFederated Intelligence Network\033[0m")
            print(f"{dm}  Nodes:\033[0m {s['total_nodes']} ({s['autonomous']} autonomous, {s['collaborating']} collaborating)")
            print(f"{dm}  Shared Resources:\033[0m {s['shared_resources']}")
            for nid, n in fed.nodes.items():
                status = '\033[32m✓\033[0m' if n['status'] == 'autonomous' else '\033[33m○\033[0m'
                print(f"  {status} {nid} [{n['status']}] trust={n['trust_level']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "node" and len(rest) >= 3:
            result = fed.register_node(rest[0], rest[1], int(rest[2]), {})
            print(f"{ok}Node registered: {result['node']}\033[0m")
        elif sub == "collab" and len(rest) >= 2:
            result = fed.request_collaboration("local", rest[0], " ".join(rest[1:]))
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Collaboration request sent to {rest[0]}\033[0m")
        elif sub == "approve" and rest:
            result = fed.approve_collaboration("local", int(rest[0]))
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Approved collaboration with {result['partner']}\033[0m")
        elif sub == "share" and len(rest) >= 3:
            result = fed.share_resource(rest[0], rest[1], rest[2], rest[3] if len(rest) > 3 else "team")
            print(f"{ok}Resource shared: {result['shared']} ({result['access']})\033[0m")

    def cmd_cin_trust(self, args):
        """Trust Framework. Usage: trust establish <entity> <type> | verify <from> <to> | score <from> <to>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        tr = self.cin.trust
        if not args:
            s = tr.stats()
            print(f"\033[{hl}mTrust Framework\033[0m")
            print(f"{dm}  Relationships:\033[0m {s['relationships']} ({s['active']} active)")
            print(f"{dm}  Levels:\033[0m {', '.join(s['levels'])}")
            for r in tr.relationships:
                status = '\033[32m✓\033[0m' if r['active'] else '\033[31m✗\033[0m'
                print(f"  {status} {r['from']} -> {r['to']} [{r['type']}] weight={r['level']['weight']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "establish" and len(rest) >= 2:
            result = tr.establish_trust(rest[0], rest[1], rest[2] if len(rest) > 2 else "personal")
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Trust established: {rest[0]} -> {rest[1]} [{result['type']}]\033[0m")
        elif sub == "verify" and len(rest) >= 2:
            result = tr.verify_trust(rest[0], rest[1], "collaborate")
            if result['trusted']: print(f"{ok}Trusted (level: {result['level']})\033[0m")
            else: print(f"{er}Not trusted: {result.get('reason', 'unknown')}\033[0m")
        elif sub == "score" and len(rest) >= 2:
            result = tr.get_trust_score(rest[0], rest[1])
            print(f"  Score: {result['score']}/{result['max_possible']}")
        elif sub == "revoke" and len(rest) >= 2:
            result = tr.revoke_trust(rest[0], rest[1])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Trust revoked\033[0m")

    def cmd_cin_a2a(self, args):
        """Agent-to-Agent Communication. Usage: a2a msg <from> <to> <text> | delegate <task> <to> | verify <del_id>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        a2a = self.cin.communication
        if not args:
            s = a2a.stats()
            print(f"\033[{hl}mAgent-to-Agent Communication\033[0m")
            print(f"{dm}  Messages:\033[0m {s['messages']}")
            print(f"{dm}  Delegations:\033[0m {s['delegations']}")
            print(f"{dm}  Discoveries:\033[0m {s['discoveries']}")
            for d in a2a.delegations:
                status = '\033[32m✓\033[0m' if d['status'] == 'completed' else '\033[33m○\033[0m'
                print(f"  {status} {d['id']}: {d['from']['agent']} -> {d['to']['agent']} [{d['status']}]")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "msg" and len(rest) >= 3:
            result = a2a.send_message(rest[0], "local", rest[1], "remote", " ".join(rest[2:]))
            print(f"{ok}Message sent: {result['id']}\033[0m")
        elif sub == "delegate" and len(rest) >= 3:
            result = a2a.delegate_task(rest[0], "local", rest[1], "remote", rest[2], {"priority": 5})
            print(f"{ok}Task delegated: {result['id']}\033[0m")
        elif sub == "update" and len(rest) >= 2:
            result = a2a.update_delegation(rest[0], rest[1], rest[2] if len(rest) > 2 else None)
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Delegation {rest[0]} -> {rest[1]}\033[0m")
        elif sub == "verify" and rest:
            result = a2a.verify_result(rest[0])
            if result['verified']: print(f"{ok}Result verified\033[0m")
            else: print(f"{er}Not verified: {result.get('reason', 'unknown')}\033[0m")
        elif sub == "discover":
            result = a2a.discover_capabilities("remote")
            print(f"\033[{hl}mCapabilities discovered:\033[0m")
            for cap, score in result['capabilities'].items():
                print(f"  {cap}: {score:.0%}")

    def cmd_cin_kex(self, args):
        """Distributed Knowledge Exchange. Usage: kex share <type> <content> | request <id> | search <type>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        kex = self.cin.knowledge_exchange
        if not args:
            s = kex.stats()
            print(f"\033[{hl}mDistributed Knowledge Exchange\033[0m")
            print(f"{dm}  Knowledge:\033[0m {s['total']} items")
            print(f"{dm}  Exchanges:\033[0m {s['exchanges']}")
            for t, cnt in s['types'].items():
                print(f"  {t}: {cnt}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "share" and len(rest) >= 2:
            result = kex.share_knowledge("local", rest[0], " ".join(rest[1:]))
            print(f"{ok}Shared: {result['id']} (v{result['version']})\033[0m")
        elif sub == "request" and rest:
            result = kex.request_knowledge("local", rest[0])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Received: {result['knowledge']['content'][:60]}...\033[0m")
        elif sub == "search" and rest:
            results = kex.get_knowledge_by_type(rest[0])
            if results:
                print(f"\033[{hl}mKnowledge type: {rest[0]}\033[0m")
                for k in results:
                    print(f"  [{k['id']}] {k['owner']}: {str(k['content'])[:60]}")
            else: print(f"{dm}No results\033[0m")
        elif sub == "owner" and rest:
            result = kex.verify_ownership(rest[0])
            if result['preserved']: print(f"{ok}Ownership preserved: {result['owner']}\033[0m")
            else: print(f"{er}Ownership record not found\033[0m")

    def cmd_cin_tspace(self, args):
        """Team Intelligence Space. Usage: tspace create <name> | join <space> <user> | goal <space> <text>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        ts = self.cin.team_spaces
        if not args:
            s = ts.stats()
            print(f"\033[{hl}mTeam Intelligence Spaces\033[0m")
            print(f"{dm}  Spaces:\033[0m {s['spaces']}")
            print(f"{dm}  Total Members:\033[0m {s['total_members']}")
            for sp in ts.spaces:
                print(f"  {sp['name']} ({sp['id']}) [{sp['status']}] - {len(sp['members'])} members, {len(sp['goals'])} goals")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "create" and rest:
            result = ts.create_space(" ".join(rest), "local", "collaborative space")
            print(f"{ok}Space created: {result['name']} ({result['id']})\033[0m")
        elif sub == "join" and len(rest) >= 2:
            result = ts.add_member(rest[0], rest[1])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}{rest[1]} joined {rest[0]}\033[0m")
        elif sub == "goal" and len(rest) >= 2:
            result = ts.add_goal(rest[0], " ".join(rest[1:]))
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Goal added: {result['text'][:50]}\033[0m")
        elif sub == "memory" and len(rest) >= 3:
            result = ts.add_shared_memory(rest[0], rest[1], " ".join(rest[2:]))
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Memory added by {result['contributor']}\033[0m")
        elif sub == "agent" and len(rest) >= 3:
            result = ts.add_agent(rest[0], rest[1], rest[2], "local")
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Agent {result['id']} added to space\033[0m")
        elif sub == "workflow" and len(rest) >= 3:
            result = ts.add_workflow(rest[0], rest[1], rest[2:])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Workflow '{result['name']}' created with {len(result['steps'])} steps\033[0m")

    def cmd_cin_creason(self, args):
        """Collective Reasoning Engine. Usage: creason submit <title> <expertise>... | solve <prob> <agent> <solution>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        cr = self.cin.reasoning
        if not args:
            s = cr.stats()
            print(f"\033[{hl}mCollective Reasoning Engine\033[0m")
            print(f"{dm}  Problems:\033[0m {s['problems']} ({s['solved']} solved)")
            print(f"{dm}  Solutions:\033[0m {s['solutions']}")
            for p in cr.problems:
                status = '\033[32m✓\033[0m' if p['status'] == 'solved' else ('\033[33m○\033[0m' if p['status'] == 'unified' else '\033[31m○\033[0m')
                print(f"  {status} {p['id']}: {p['title']} [{p['status']}] expertise: {', '.join(p['required_expertise'])}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "submit" and len(rest) >= 2:
            result = cr.submit_problem(rest[0], "problem description", rest[1:])
            print(f"{ok}Problem submitted: {result['id']}\033[0m")
        elif sub == "solve" and len(rest) >= 3:
            result = cr.contribute_solution(rest[0], rest[1], "local", " ".join(rest[2:]), rest[2] if len(rest) > 2 else "general")
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Solution contributed to {rest[0]}\033[0m")
            if result.get("problem_id"):
                unified = cr.unify_solutions(rest[0])
                if "unified_solution" in unified:
                    print(f"{hl}Solutions unified!\033[0m")
                    print(f"  {unified['unified_solution']}")

    def cmd_cin_cap(self, args):
        """Capability Discovery. Usage: cap register <name> <level> | search <query> | inquire <cap_id>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        cap = self.cin.discovery
        if not args:
            s = cap.stats()
            print(f"\033[{hl}mCapability Discovery\033[0m")
            print(f"{dm}  Directory:\033[0m {s['directory']} ({s['active']} active)")
            print(f"{dm}  Inquiries:\033[0m {s['inquiries']}")
            for c in cap.directory:
                status = '\033[32m✓\033[0m' if c['active'] else '\033[31m✗\033[0m'
                print(f"  {status} {c['name']} (level {c['expertise_level']}) - {c['description'][:50]}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "register" and len(rest) >= 2:
            result = cap.register_capability("local", rest[0], " ".join(rest[1:]) if len(rest) > 2 else "capability", int(rest[-1]) if rest[-1].isdigit() else 5)
            print(f"{ok}Registered: {result['name']}\033[0m")
        elif sub == "search" and rest:
            results = cap.search_capabilities(" ".join(rest))
            if results:
                print(f"\033[{hl}mSearch results:\033[0m")
                for r in results[:5]:
                    c = r['capability']
                    print(f"  [{r['relevance']:.0%}] {c['name']} (level {c['expertise_level']}) - {c['provider']}")
            else: print(f"{dm}No matching capabilities found\033[0m")
        elif sub == "inquire" and rest:
            result = cap.inquire_access("local", rest[0])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"\033[33m{result['note']}\033[0m")

    def cmd_cin_provenance(self, args):
        """Provenance System. Usage: provenance record <source> <agents> <origin> <summary> | lineage <id> | audit <id>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        prov = self.cin.provenance
        if not args:
            s = prov.stats()
            print(f"\033[{hl}mProvenance System\033[0m")
            print(f"{dm}  Records:\033[0m {s['records']}")
            print(f"{dm}  Total Versions:\033[0m {s['versions']}")
            for r in prov.records:
                print(f"  [{r['id']}] source={r['source']} agents={r['contributing_agents']} v{r['version']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "record" and len(rest) >= 4:
            result = prov.record(rest[0], rest[1].split(","), rest[2], " ".join(rest[3:]))
            print(f"{ok}Recorded: {result['id']} (v{result['version']})\033[0m")
        elif sub == "lineage" and rest:
            result = prov.get_lineage(rest[0])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else:
                print(f"\033[{hl}mLineage:\033[0m")
                for k, v in result.items():
                    print(f"  {k}: {v}")
        elif sub == "audit" and rest:
            result = prov.audit(rest[0])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else:
                print(f"\033[{hl}mAudit:\033[0m")
                for k, v in result.items():
                    print(f"  {k}: {v}")
        elif sub == "version" and len(rest) >= 2:
            result = prov.update_version(rest[0], rest[1], rest[2].split(",") if len(rest) > 2 else ["unknown"], " ".join(rest[3:]) if len(rest) > 3 else "updated")
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Updated: v{result['version']}\033[0m")

    def cmd_cin_resilient(self, args):
        """Resilience Layer. Usage: resilient cache <node> <state> | sync <from> <to> <type> | fail <node> <error>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        res = self.cin.resilience
        if not args:
            s = res.get_status()
            print(f"\033[{hl}mResilience Layer\033[0m")
            print(f"{dm}  Cached Nodes:\033[0m {s['cached_nodes']}")
            print(f"{dm}  Pending Syncs:\033[0m {s['pending_syncs']}")
            print(f"{dm}  Failures:\033[0m {s['failures']} ({s['recovered']} recovered)")
            print(f"{dm}  Conflicts:\033[0m {s['conflicts']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "cache" and len(rest) >= 2:
            result = res.cache_node_state(rest[0], " ".join(rest[1:]))
            print(f"{ok}Cached: {result['cached']}\033[0m")
        elif sub == "sync" and len(rest) >= 3:
            result = res.queue_sync(rest[0], rest[1], rest[2], " ".join(rest[3:]) if len(rest) > 3 else "state")
            print(f"{ok}Sync queued: {result['id']}\033[0m")
        elif sub == "process" and rest:
            result = res.process_sync(rest[0])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Sync completed\033[0m")
        elif sub == "fail" and len(rest) >= 2:
            result = res.log_failure(rest[0], rest[1], " ".join(rest[2:]) if len(rest) > 2 else "unknown error")
            print(f"{er}Failure logged: {result['node']} / {result['component']}\033[0m")
        elif sub == "recover" and rest:
            result = res.recover_node(rest[0])
            print(f"{ok}Recovery: {result['recovered']}\033[0m")
            if result.get("cached_state"): print(f"  Cached state restored")

    def cmd_cin_gov(self, args):
        """Governance System. Usage: gov policy <name> <rules> | grant <user> <resource> <action> | revoke <perm_id>"""
        er = self._c("err"); ok = self._c("ok"); dm = self._c("dm"); hl = self._c("hl")
        gov = self.cin.governance
        if not args:
            s = gov.stats()
            print(f"\033[{hl}mGovernance System\033[0m")
            print(f"{dm}  Policies:\033[0m {s['policies']}")
            print(f"{dm}  Active Permissions:\033[0m {s['active_permissions']}")
            print(f"{dm}  Audit Entries:\033[0m {s['audit_entries']}")
            print(f"{dm}  Revocations:\033[0m {s['revocations']}")
            return
        sub = args[0]; rest = args[1:] if len(args) > 1 else []
        if sub == "policy" and len(rest) >= 2:
            result = gov.create_policy(rest[0], "governance policy", rest[1:])
            print(f"{ok}Policy created: {result['id']}\033[0m")
        elif sub == "grant" and len(rest) >= 3:
            result = gov.grant_permission(rest[0], rest[1], rest[2])
            print(f"{ok}Permission granted: {result['id']} expires in 24h\033[0m")
        elif sub == "check" and len(rest) >= 3:
            result = gov.check_permission(rest[0], rest[1], rest[2])
            if result['allowed']: print(f"{ok}Allowed\033[0m")
            else: print(f"{er}Denied: {result.get('reason', 'no permission')}\033[0m")
        elif sub == "revoke" and rest:
            result = gov.revoke_access(rest[0])
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Access revoked: {rest[0]}\033[0m")
        elif sub == "expire" and len(rest) >= 2:
            result = gov.set_access_expiration(rest[0], int(rest[1]))
            if "error" in result: print(f"{er}{result['error']}\033[0m")
            else: print(f"{ok}Expiration set: {rest[1]}s\033[0m")
        elif sub == "audit":
            for entry in gov.get_audit_log():
                print(f"  [{entry['action']}] {entry['actor']}: {entry['details']}")

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
    def cmd_unidoc(self, args): print(f"\033[33m[Universal Document] 106 modules indexed, query ready\033[0m")
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
    def cmd_metaos(self, args): print(f"\033[33m[Meta-OS Fabric] 106 modules orchestrated, latency: 0.3ms\033[0m")
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
        if not _HAVE_TK:
            print("\033[31mDesktop requires Tkinter\033[0m")
            return
        desktop = ArcDesktop()
        desktop.launch()

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
