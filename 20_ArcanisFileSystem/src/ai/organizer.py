"""Smart file organizer for ArcanisFileSystem.

Automatically organizes files based on rules and AI analysis.
"""

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


class OrganizeAction(enum.Enum):
    MOVE = "move"
    COPY = "copy"
    TAG = "tag"
    RENAME = "rename"
    ARCHIVE = "archive"
    DELETE = "delete"


class MatchCondition(enum.Enum):
    EXTENSION = "extension"
    MIME_TYPE = "mime_type"
    NAME_PATTERN = "name_pattern"
    SIZE_RANGE = "size_range"
    DATE_RANGE = "date_range"
    CONTENT_KEYWORD = "content_keyword"
    TAG = "tag"
    PATH_PATTERN = "path_pattern"


@dataclass
class OrganizationRule:
    """Defines a rule for automatic file organization."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    description: str = ""
    enabled: bool = True
    priority: int = 0
    conditions: List[Tuple[MatchCondition, str]] = field(default_factory=list)
    action: OrganizeAction = OrganizeAction.MOVE
    target_path: str = ""
    action_params: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def matches(self, file_info: Dict) -> bool:
        for condition_type, condition_value in self.conditions:
            if not self._check_condition(condition_type, condition_value, file_info):
                return False
        return True

    def _check_condition(self, condition_type: MatchCondition, value: str, file_info: Dict) -> bool:
        import fnmatch

        if condition_type == MatchCondition.EXTENSION:
            ext = file_info.get("extension", "").lower()
            return ext == value.lower().lstrip(".")

        elif condition_type == MatchCondition.MIME_TYPE:
            return file_info.get("mime_type", "") == value

        elif condition_type == MatchCondition.NAME_PATTERN:
            return fnmatch.fnmatch(file_info.get("name", ""), value)

        elif condition_type == MatchCondition.SIZE_RANGE:
            size = file_info.get("size", 0)
            return self._check_size_range(value, size)

        elif condition_type == MatchCondition.DATE_RANGE:
            date = file_info.get("modified_at", 0)
            return self._check_date_range(value, date)

        elif condition_type == MatchCondition.CONTENT_KEYWORD:
            keywords = file_info.get("keywords", [])
            return value.lower() in [k.lower() for k in keywords]

        elif condition_type == MatchCondition.TAG:
            tags = file_info.get("tags", set())
            return value.lower() in [t.lower() for t in tags]

        elif condition_type == MatchCondition.PATH_PATTERN:
            return fnmatch.fnmatch(file_info.get("path", ""), value)

        return False

    def _check_size_range(self, value: str, size: int) -> bool:
        try:
            if value.startswith("<"):
                return size < self._parse_size(value[1:])
            elif value.startswith(">"):
                return size > self._parse_size(value[1:])
            elif "-" in value:
                min_str, max_str = value.split("-")
                return self._parse_size(min_str) <= size <= self._parse_size(max_str)
            else:
                return size == self._parse_size(value)
        except Exception:
            return False

    def _parse_size(self, size_str: str) -> int:
        size_str = size_str.strip().upper()
        multipliers = {"B": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}

        for suffix, mult in multipliers.items():
            if size_str.endswith(suffix):
                return int(float(size_str[:-1]) * mult)

        return int(size_str)

    def _check_date_range(self, value: str, timestamp: float) -> bool:
        import time as time_mod
        now = time_mod.time()

        if value.startswith("last_"):
            days = int(value.split("_")[1])
            return timestamp > now - (days * 86400)
        elif value.startswith("before_"):
            days = int(value.split("_")[1])
            return timestamp < now - (days * 86400)

        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "priority": self.priority,
            "conditions": [(c.value, v) for c, v in self.conditions],
            "action": self.action.value,
            "target": self.target_path,
            "params": self.action_params,
        }


@dataclass
class OrganizationAction:
    """Result of an organization action."""

    rule_id: str
    file_inode_id: uuid.UUID
    file_path: str
    action: OrganizeAction
    target_path: str
    success: bool = True
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class SmartOrganizer:
    """Automatically organizes files based on rules."""

    def __init__(self):
        self._rules: Dict[str, OrganizationRule] = {}
        self._action_log: List[OrganizationAction] = []
        self._auto_organize_enabled = True
        self._callbacks: List[Callable[[OrganizationAction], None]] = []

    def add_rule(self, rule: OrganizationRule) -> None:
        self._rules[rule.id] = rule

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[OrganizationRule]:
        return self._rules.get(rule_id)

    def list_rules(self, enabled_only: bool = True) -> List[OrganizationRule]:
        rules = list(self._rules.values())
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return sorted(rules, key=lambda r: r.priority, reverse=True)

    def find_matching_rules(self, file_info: Dict) -> List[OrganizationRule]:
        matching = []
        for rule in self.list_rules(enabled_only=True):
            if rule.matches(file_info):
                matching.append(rule)
        return sorted(matching, key=lambda r: r.priority, reverse=True)

    def organize_file(self, inode_id: uuid.UUID, file_info: Dict) -> List[OrganizationAction]:
        if not self._auto_organize_enabled:
            return []

        actions = []
        matching_rules = self.find_matching_rules(file_info)

        for rule in matching_rules:
            action = OrganizationAction(
                rule_id=rule.id,
                file_inode_id=inode_id,
                file_path=file_info.get("path", ""),
                action=rule.action,
                target_path=self._resolve_target(rule, file_info),
            )

            self._action_log.append(action)
            actions.append(action)

            for callback in self._callbacks:
                try:
                    callback(action)
                except Exception:
                    pass

            if rule.action in (OrganizeAction.DELETE,):
                break

        return actions

    def _resolve_target(self, rule: OrganizationRule, file_info: Dict) -> str:
        target = rule.target_path
        name = file_info.get("name", "unknown")
        ext = file_info.get("extension", "")

        target = target.replace("{name}", name)
        target = target.replace("{ext}", ext)
        target = target.replace("{year}", str(int(time.time() // (365.25 * 86400)) + 1970))
        target = target.replace("{month}", time.strftime("%m"))
        target = target.replace("{mime_type}", file_info.get("mime_type", "unknown"))

        return target

    def create_default_rules(self) -> None:
        document_rule = OrganizationRule(
            name="Documents",
            description="Organize document files",
            priority=10,
            conditions=[(MatchCondition.EXTENSION, "pdf"),
                       (MatchCondition.EXTENSION, "doc"),
                       (MatchCondition.EXTENSION, "docx")],
            action=OrganizeAction.MOVE,
            target_path="/Documents/{name}{ext}",
        )
        self.add_rule(document_rule)

        image_rule = OrganizationRule(
            name="Images",
            description="Organize image files",
            priority=10,
            conditions=[(MatchCondition.EXTENSION, "jpg"),
                       (MatchCondition.EXTENSION, "png"),
                       (MatchCondition.EXTENSION, "gif")],
            action=OrganizeAction.MOVE,
            target_path="/Images/{year}/{month}/{name}{ext}",
        )
        self.add_rule(image_rule)

        archive_rule = OrganizationRule(
            name="Archives",
            description="Organize archive files",
            priority=5,
            conditions=[(MatchCondition.EXTENSION, "zip"),
                       (MatchCondition.EXTENSION, "tar"),
                       (MatchCondition.EXTENSION, "gz")],
            action=OrganizeAction.MOVE,
            target_path="/Archives/{name}{ext}",
        )
        self.add_rule(archive_rule)

        large_rule = OrganizationRule(
            name="Large Files",
            description="Archive large files",
            priority=3,
            conditions=[(MatchCondition.SIZE_RANGE, ">100M")],
            action=OrganizeAction.MOVE,
            target_path="/Archive/Large/{name}{ext}",
        )
        self.add_rule(large_rule)

    def add_callback(self, callback: Callable[[OrganizationAction], None]) -> None:
        self._callbacks.append(callback)

    def get_action_log(self, limit: int = 100) -> List[OrganizationAction]:
        return self._action_log[-limit:]

    def get_statistics(self) -> Dict[str, int]:
        action_counts = {}
        for action in self._action_log:
            key = action.action.value
            action_counts[key] = action_counts.get(key, 0) + 1
        return {
            "total_rules": len(self._rules),
            "enabled_rules": len([r for r in self._rules.values() if r.enabled]),
            "total_actions": len(self._action_log),
            "action_counts": action_counts,
        }

    def clear_log(self) -> int:
        count = len(self._action_log)
        self._action_log.clear()
        return count
