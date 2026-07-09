"""Built-in automation actions.

Each handler receives (spec: ActionSpec, ctx: SecurityContext, engine, log)
and returns a JSON-serializable result. Handlers are registered with the
engine so custom actions can be added at runtime.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from typing import Any

from arcanis_automation.core.models import ActionSpec, ExecutionResult
from arcanis_automation.security.guard import SecurityError


# --------------------------------------------------------------------------
# File organization
# --------------------------------------------------------------------------

_FILE_CATEGORIES = {
    "images": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp"},
    "documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt"},
    "spreadsheets": {".xls", ".xlsx", ".csv", ".tsv"},
    "audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a"},
    "video": {".mp4", ".mkv", ".mov", ".avi", ".webm"},
    "archives": {".zip", ".tar", ".gz", ".7z", ".rar"},
    "code": {".py", ".js", ".ts", ".go", ".rs", ".c", ".cpp", ".java", ".json"},
}


def _file_organize(spec: ActionSpec, ctx, engine, log) -> Any:
    source = ctx.guard_path(spec.params["source"])
    if not os.path.isdir(source):
        raise SecurityError(f"Not a directory: {source}")
    by_ext = bool(spec.params.get("by_extension", False))
    prefix = spec.params.get("prefix", "")
    moved: dict[str, str] = {}
    for name in os.listdir(source):
        full = os.path.join(source, name)
        if not os.path.isfile(full):
            continue
        _, ext = os.path.splitext(name)
        ext = ext.lower()
        if by_ext:
            folder = ext[1:] or "unknown"
        else:
            folder = "misc"
            for cat, exts in _FILE_CATEGORIES.items():
                if ext in exts:
                    folder = cat
                    break
        dest_dir = ctx.guard_path(os.path.join(source, prefix + folder))
        os.makedirs(dest_dir, exist_ok=True)
        target = os.path.join(dest_dir, name)
        shutil.move(full, target)
        moved[name] = target
    return {"organized": len(moved), "map": moved}


def _file_move(spec: ActionSpec, ctx, engine, log) -> Any:
    src = ctx.guard_path(spec.params["source"])
    dst = ctx.guard_path(spec.params["destination"])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    return {"moved": dst}


def _file_copy(spec: ActionSpec, ctx, engine, log) -> Any:
    src = ctx.guard_path(spec.params["source"])
    dst = ctx.guard_path(spec.params["destination"])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return {"copied": dst}


def _file_delete(spec: ActionSpec, ctx, engine, log) -> Any:
    target = ctx.guard_path(spec.params["target"])
    if spec.params.get("recursive"):
        shutil.rmtree(target)
    else:
        os.remove(target)
    return {"deleted": target}


# --------------------------------------------------------------------------
# Application control
# --------------------------------------------------------------------------

def _app_launch(spec: ActionSpec, ctx, engine, log) -> Any:
    import subprocess
    ctx.require("app.launch")
    cmd = spec.params["command"]
    detached = spec.params.get("detached", True)
    if detached:
        popen = subprocess.Popen(
            cmd, shell=isinstance(cmd, str), stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
            start_new_session=(sys.platform != "win32"),
        )
        pid = popen.pid
    else:
        proc = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True)
        pid = proc.pid
    return {"launched": cmd, "pid": pid}


def _app_kill(spec: ActionSpec, ctx, engine, log) -> Any:
    import subprocess
    ctx.require("app.kill")
    ident = spec.params["target"]
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/PID", str(ident) if str(ident).isdigit() else "/IM", str(ident)],
                       capture_output=True, text=True)
    else:
        subprocess.run(["kill", "-9", str(ident)], capture_output=True, text=True)
    return {"killed": ident}


def _app_focus(spec: ActionSpec, ctx, engine, log) -> Any:
    # Best-effort; platform GUI focus requires native libs.
    ctx.require("app.focus")
    return {"focus_requested": spec.params.get("window")}


# --------------------------------------------------------------------------
# Data processing
# --------------------------------------------------------------------------

def _data_transform(spec: ActionSpec, ctx, engine, log) -> Any:
    ctx.require("data.transform")
    source = ctx.guard_path(spec.params["source"])
    with open(source, "r", encoding="utf-8") as fh:
        if source.endswith(".json"):
            data = json.load(fh)
        else:
            data = fh.read()
    op = spec.params.get("operation", "uppercase")
    if op == "uppercase" and isinstance(data, str):
        out = data.upper()
    elif op == "lowercase" and isinstance(data, str):
        out = data.lower()
    elif op == "to_json" and not isinstance(data, str):
        out = json.dumps(data, indent=2)
    elif op == "filter" and isinstance(data, list):
        key = spec.params["key"]
        val = spec.params.get("value")
        out = [r for r in data if r.get(key) == val]
    else:
        out = data
    dest = spec.params.get("destination")
    if dest:
        dest = ctx.guard_path(dest)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(out if isinstance(out, str) else json.dumps(out, indent=2))
    return {"transformed": op, "bytes": len(str(out))}


def _data_aggregate(spec: ActionSpec, ctx, engine, log) -> Any:
    ctx.require("data.aggregate")
    source = ctx.guard_path(spec.params["source"])
    with open(source, "r", encoding="utf-8") as fh:
        if source.endswith(".json"):
            rows = json.load(fh)
        else:
            import csv
            rows = list(csv.DictReader(fh))
    group_by = spec.params.get("group_by")
    metric = spec.params.get("metric")
    result: dict[str, Any] = {}
    for row in rows:
        key = row.get(group_by, "_all") if group_by else "_all"
        val = float(row.get(metric, 0) or 0) if metric else 1
        result[key] = result.get(key, 0) + val
    return {"aggregated": result}


# --------------------------------------------------------------------------
# Research workflows
# --------------------------------------------------------------------------

def _research_query(spec: ActionSpec, ctx, engine, log) -> Any:
    ctx.require("research.query")
    query = spec.params["query"]
    # Delegates to the AI research capability if available; otherwise records.
    ai = getattr(engine, "ai", None)
    if ai is not None:
        return ai.research(query, spec.params.get("depth", 1))
    return {"query": query, "note": "AI research provider not configured."}


def _research_fetch(spec: ActionSpec, ctx, engine, log) -> Any:
    ctx.require("research.fetch")
    from arcanis_automation.ai.providers import fetch_url
    url = spec.params["url"]
    return {"url": url, "content": fetch_url(url)}


# --------------------------------------------------------------------------
# Generic
# --------------------------------------------------------------------------

def _shell(spec: ActionSpec, ctx, engine, log) -> Any:
    proc = ctx.run_shell(spec.params["command"], timeout=spec.timeout)
    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def _http(spec: ActionSpec, ctx, engine, log) -> Any:
    ctx.require("http")
    import urllib.request
    url = spec.params["url"]
    method = spec.params.get("method", "GET")
    data = spec.params.get("body")
    req = urllib.request.Request(url, data=data.encode() if data else None, method=method)
    with urllib.request.urlopen(req, timeout=spec.timeout) as resp:
        return {"status": resp.status, "body": resp.read().decode("utf-8", "replace")[:4096]}


def _notify(spec: ActionSpec, ctx, engine, log) -> Any:
    message = spec.params.get("message", "")
    log.record("notify", message=message)
    engine.audit.record("notify.sent", message=message)
    return {"notified": message}


HANDLERS = {
    "file.organize": _file_organize,
    "file.move": _file_move,
    "file.copy": _file_copy,
    "file.delete": _file_delete,
    "app.launch": _app_launch,
    "app.kill": _app_kill,
    "app.focus": _app_focus,
    "data.transform": _data_transform,
    "data.aggregate": _data_aggregate,
    "research.query": _research_query,
    "research.fetch": _research_fetch,
    "shell": _shell,
    "http": _http,
    "notify": _notify,
}
