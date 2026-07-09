"""Core utilities — Python implementations for the Arcanis shell."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TextIO


def grep(pattern: str, paths: list[str] | None = None, ignore_case: bool = False,
         invert: bool = False, count: bool = False, line_number: bool = False) -> str:
    flags = re.IGNORECASE if ignore_case else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error:
        return f"grep: invalid pattern: {pattern}"

    lines_out: list[str] = []
    match_count = 0
    sources = [(None, sys.stdin)] if not paths else [(p, open(p, "r", errors="replace")) for p in paths]

    for source_name, fh in sources:
        for i, line in enumerate(fh, 1):
            match = bool(regex.search(line))
            if invert:
                match = not match
            if match:
                match_count += 1
                if not count:
                    prefix = ""
                    if source_name and len(paths or []) > 1:
                        prefix = f"{source_name}:"
                    if line_number:
                        prefix += f"{i}:"
                    lines_out.append(prefix + line.rstrip("\n"))
        if source_name:
            fh.close()

    if count:
        return str(match_count)
    return "\n".join(lines_out)


def sed(expression: str, text: str) -> str:
    """Simple s/old/new/g substitution."""
    m = re.match(r'^s(.)(.+?)\1(.+?)\1([gwi]*)$', expression)
    if not m:
        return f"sed: unsupported expression: {expression}"
    sep, pattern, replacement, flags = m.group(1), m.group(2), m.group(3), m.group(4)
    count = 0 if 'g' in flags else 1
    try:
        result = re.sub(pattern, replacement, text, count=count)
    except re.error:
        return f"sed: invalid pattern: {pattern}"
    return result


def sort_lines(text: str, numeric: bool = False, reverse: bool = False,
               unique: bool = False, key: int | None = None) -> str:
    lines = text.splitlines()
    if numeric:
        lines.sort(key=lambda l: float(l.split()[key - 1] if key and l.split() else l) if l.strip() else 0, reverse=reverse)
    else:
        lines.sort(reverse=reverse)
    if unique:
        seen: set[str] = set()
        filtered = []
        for l in lines:
            if l not in seen:
                seen.add(l)
                filtered.append(l)
        lines = filtered
    return "\n".join(lines)


def wc(text: str) -> str:
    lines = text.count("\n")
    words = len(text.split())
    chars = len(text)
    return f"{lines}\t{words}\t{chars}"


def head(text: str, n: int = 10) -> str:
    return "\n".join(text.splitlines()[:n])


def tail(text: str, n: int = 10) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-n:])


def diff(file1: str, file2: str) -> str:
    lines1 = Path(file1).read_text(errors="replace").splitlines() if Path(file1).exists() else []
    lines2 = Path(file2).read_text(errors="replace").splitlines() if Path(file2).exists() else []
    result: list[str] = []
    max_lines = max(len(lines1), len(lines2))
    for i in range(max_lines):
        l1 = lines1[i] if i < len(lines1) else None
        l2 = lines2[i] if i < len(lines2) else None
        if l1 != l2:
            result.append(f"--- line {i + 1}")
            if l1 is not None:
                result.append(f"- {l1}")
            if l2 is not None:
                result.append(f"+ {l2}")
    return "\n".join(result) if result else "Files identical"


def touch(path: str) -> str:
    p = Path(path)
    if p.exists():
        p.touch()
        return ""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()
    return ""


def chmod(mode: str, path: str) -> str:
    """Stub — permission model is capability-based, not POSIX perms."""
    return f"chmod: {path}: permissions managed by capabilities"


def ln(target: str, link_name: str, symbolic: bool = False) -> str:
    if symbolic:
        Path(link_name).symlink_to(target)
    else:
        import os
        os.link(target, link_name)
    return ""


def uptime_str() -> str:
    """Return formatted uptime string."""
    import time as _time
    try:
        up = _time.time() - _time.monotonic()
    except AttributeError:
        up = 0
    hours = int(up // 3600)
    minutes = int((up % 3600) // 60)
    return f"up {hours}h {minutes}m"


def date_str(fmt: str = "") -> str:
    import datetime
    now = datetime.datetime.now()
    if fmt:
        return now.strftime(fmt)
    return now.strftime("%Y-%m-%d %H:%M:%S")


def cut(delimiter: str, fields: list[int], text: str) -> str:
    result: list[str] = []
    for line in text.splitlines():
        parts = line.split(delimiter)
        selected = [parts[f - 1] for f in fields if 0 < f <= len(parts)]
        result.append(delimiter.join(selected))
    return "\n".join(result)


def tr(set1: str, set2: str, text: str) -> str:
    table = str.maketrans(set1, set2)
    return text.translate(table)


def uniq(lines: list[str]) -> str:
    result: list[str] = []
    for line in lines:
        if not result or result[-1] != line:
            result.append(line)
    return "\n".join(result)


def rev(text: str) -> str:
    return "\n".join(line[::-1] for line in text.splitlines())


def seq(first: int, last: int | None = None, step: int = 1) -> str:
    if last is None:
        first, last = 1, first
    return "\n".join(str(i) for i in range(first, last + 1, step))


def paste(file1: str, file2: str, delimiter: str = "\t") -> str:
    lines1 = Path(file1).read_text(errors="replace").splitlines() if Path(file1).exists() else []
    lines2 = Path(file2).read_text(errors="replace").splitlines() if Path(file2).exists() else []
    max_lines = max(len(lines1), len(lines2))
    result: list[str] = []
    for i in range(max_lines):
        l1 = lines1[i] if i < len(lines1) else ""
        l2 = lines2[i] if i < len(lines2) else ""
        result.append(f"{l1}{delimiter}{l2}")
    return "\n".join(result)
