"""ArcanisAutomation — workflow automation for the Arcanis ecosystem.

ArcanisAutomation provides an automation engine, a declarative workflow
format, a scheduler, a permission/security layer, and AI-assisted workflow
generation, optimization, and failure detection.

Project ID: 13-automation
Layer: 3 (AI / Automation)
Status: Alpha
"""

from arcanis_automation.core.engine import AutomationEngine
from arcanis_automation.core.models import (
    Workflow,
    Step,
    Trigger,
    TriggerType,
    ActionSpec,
    Schedule,
    Permission,
    PermissionLevel,
    WorkflowStatus,
    ExecutionResult,
)
from arcanis_automation.config import AutomationConfig

__version__ = "0.1.0"

__all__ = [
    "AutomationEngine",
    "Workflow",
    "Step",
    "Trigger",
    "TriggerType",
    "ActionSpec",
    "Schedule",
    "Permission",
    "PermissionLevel",
    "WorkflowStatus",
    "ExecutionResult",
    "AutomationConfig",
]
