"""POSIX-compatible permission system for ArcanisFileSystem.

Implements standard Unix permissions with extensions for ArcanisOS.
"""

import enum
import stat
from dataclasses import dataclass


class PermissionMode(enum.IntEnum):
    """Standard permission bits."""
    READ = 4
    WRITE = 2
    EXECUTE = 1


@dataclass
class PosixPermissions:
    """Represents POSIX-style permissions for a file."""

    mode: int = 0o644

    @property
    def owner_read(self) -> bool:
        return bool(self.mode & stat.S_IRUSR)

    @property
    def owner_write(self) -> bool:
        return bool(self.mode & stat.S_IWUSR)

    @property
    def owner_execute(self) -> bool:
        return bool(self.mode & stat.S_IXUSR)

    @property
    def group_read(self) -> bool:
        return bool(self.mode & stat.S_IRGRP)

    @property
    def group_write(self) -> bool:
        return bool(self.mode & stat.S_IWGRP)

    @property
    def group_execute(self) -> bool:
        return bool(self.mode & stat.S_IXGRP)

    @property
    def other_read(self) -> bool:
        return bool(self.mode & stat.S_IROTH)

    @property
    def other_write(self) -> bool:
        return bool(self.mode & stat.S_IWOTH)

    @property
    def other_execute(self) -> bool:
        return bool(self.mode & stat.S_IXOTH)

    @property
    def is_setuid(self) -> bool:
        return bool(self.mode & stat.S_ISUID)

    @property
    def is_setgid(self) -> bool:
        return bool(self.mode & stat.S_ISGID)

    @property
    def is_sticky(self) -> bool:
        return bool(self.mode & stat.S_ISVTX)

    def check_read(self, uid: int, gid: int, file_uid: int, file_gid: int) -> bool:
        if uid == file_uid:
            return self.owner_read
        elif gid == file_gid:
            return self.group_read
        else:
            return self.other_read

    def check_write(self, uid: int, gid: int, file_uid: int, file_gid: int) -> bool:
        if uid == file_uid:
            return self.owner_write
        elif gid == file_gid:
            return self.group_write
        else:
            return self.other_write

    def check_execute(self, uid: int, gid: int, file_uid: int, file_gid: int) -> bool:
        if uid == file_uid:
            return self.owner_execute
        elif gid == file_gid:
            return self.group_execute
        else:
            return self.other_execute

    def set_owner(self, read: bool, write: bool, execute: bool) -> None:
        self.mode = (self.mode & ~0o700) | (read << 6) | (write << 5) | (execute << 4)

    def set_group(self, read: bool, write: bool, execute: bool) -> None:
        self.mode = (self.mode & ~0o070) | (read << 3) | (write << 2) | (execute << 1)

    def set_other(self, read: bool, write: bool, execute: bool) -> None:
        self.mode = (self.mode & ~0o007) | (read << 0) | (write << 1) | (execute << 0)

    def set_setuid(self, enable: bool) -> None:
        if enable:
            self.mode |= stat.S_ISUID
        else:
            self.mode &= ~stat.S_ISUID

    def set_setgid(self, enable: bool) -> None:
        if enable:
            self.mode |= stat.S_ISGID
        else:
            self.mode &= ~stat.S_ISGID

    def set_sticky(self, enable: bool) -> None:
        if enable:
            self.mode |= stat.S_ISVTX
        else:
            self.mode &= ~stat.S_ISVTX

    def to_octal(self) -> str:
        return oct(self.mode)

    def to_symbolic(self) -> str:
        def convert(r, w, x, special=False):
            chars = ["r" if r else "-", "w" if w else "-"]
            if special:
                chars.append("s" if x else "S")
            else:
                chars.append("x" if x else "-")
            return "".join(chars)

        owner = convert(self.owner_read, self.owner_write, self.owner_execute, self.is_setuid)
        group = convert(self.group_read, self.group_write, self.group_execute, self.is_setgid)
        other = convert(self.other_read, self.other_write, self.other_execute, self.is_sticky)

        return f"{owner}{group}{other}"

    @classmethod
    def from_symbolic(cls, symbolic: str) -> "PosixPermissions":
        if len(symbolic) != 9:
            raise ValueError(f"Invalid symbolic mode: {symbolic}")

        mode = 0
        for i, char in enumerate(symbolic):
            if char == "s" and i in (2, 5):
                mode |= stat.S_ISUID if i == 2 else stat.S_ISGID
            elif char in ("r", "s", "S"):
                mode |= 1 << (8 - i)
            elif char in ("w", "x", "t", "T"):
                mode |= 1 << (8 - i)
            elif char == "t":
                mode |= stat.S_ISVTX

        return cls(mode=mode & 0o7777)

    def __repr__(self) -> str:
        return f"<PosixPerms {self.to_octal()} {self.to_symbolic()}>"
