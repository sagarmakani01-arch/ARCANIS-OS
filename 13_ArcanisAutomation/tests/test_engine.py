"""Tests for the ArcanisAutomation engine and features."""

from __future__ import annotations

import os
import tempfile

import pytest

from arcanis_automation.config import AutomationConfig
from arcanis_automation.api.python_api import Automation
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
)


@pytest.fixture
def auto():
    tmp = tempfile.mkdtemp()
    cfg = AutomationConfig(
        workspace_dir=tmp,
        storage_dir=os.path.join(tmp, "store"),
        log_dir=os.path.join(tmp, "logs"),
        enable_scheduler=False,
    )
    return Automation(cfg)


def test_create_and_run_notify(auto):
    wid = auto.create(
        "hello",
        steps=[{"id": "s1", "action": {"action": "notify", "params": {"message": "hi"}}}],
    )
    results = auto.run(wid)
    assert results[0].success
    assert results[0].output["notified"] == "hi"


def test_chain_dependencies(auto):
    steps = [
        {"id": "a", "action": {"action": "notify", "params": {"message": "A"}}},
        {"id": "b", "action": {"action": "notify", "params": {"message": "B"}},
         "run_after": ["a"]},
    ]
    wid = auto.create("chain", steps)
    results = auto.run(wid)
    assert all(r.success for r in results)
    assert [r.step_id for r in results] == ["a", "b"]


def test_permission_denied(auto):
    auto.engine.security.permissions = [Permission(PermissionLevel.DENY, "shell")]
    wid = auto.create(
        "bad",
        steps=[{"id": "s", "action": {"action": "shell", "params": {"command": "echo x"}}}],
    )
    results = auto.run(wid)
    assert not results[0].success
    assert "denied" in results[0].error.lower()


def test_workflow_from_dict_roundtrip():
    data = {
        "name": "x",
        "triggers": [{"type": "manual"}],
        "steps": [{"id": "s1", "action": {"action": "notify", "params": {}}}],
        "schedule": {"interval_seconds": 60},
    }
    wf = Workflow.from_dict(data)
    assert wf.schedule.interval_seconds == 60
    assert wf.to_dict()["name"] == "x"


def test_ai_heuristic_generate(auto):
    wf = auto.engine.ai.generate("organize my downloads folder and notify me")
    assert wf.steps
    kinds = [s.action.action for s in wf.steps]
    assert "file.organize" in kinds
    assert "notify" in kinds


def test_failure_detection(auto):
    wid = auto.create(
        "f",
        steps=[{"id": "s", "action": {"action": "notify", "params": {"message": "x"}}}],
    )
    auto.run(wid)
    auto.engine._running[wid] = []  # simulate no results
    report = auto.engine.detect_failures(wid)
    assert report["healthy"] is True


def test_persistence(auto):
    wid = auto.create("persist", steps=[
        {"id": "s1", "action": {"action": "notify", "params": {"message": "p"}}}])
    auto2 = Automation(auto.engine.config)
    assert auto2.get(wid) is not None
