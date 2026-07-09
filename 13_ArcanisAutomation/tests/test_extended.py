from __future__ import annotations

import json
import logging
import os
import tempfile
import time

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
    ExecutionResult,
    _gen_id,
)
from arcanis_automation.core.engine import AutomationEngine, _interpolate, _resolve
from arcanis_automation.security.guard import (
    SecurityContext,
    SecurityError,
    AuditLogger,
)
from arcanis_automation.scheduler.loop import Scheduler, ScheduledTask
from arcanis_automation.ai.capabilities import WorkflowAI
from arcanis_automation.ai.providers import LocalHeuristicProvider, get_provider


@pytest.fixture
def tmp_dirs():
    root = tempfile.mkdtemp()
    dirs = {
        "root": root,
        "workspace": os.path.join(root, "ws"),
        "storage": os.path.join(root, "store"),
        "logs": os.path.join(root, "logs"),
    }
    yield dirs
    _close_audit_handlers()
    import shutil
    shutil.rmtree(root, ignore_errors=True)


def _close_audit_handlers():
    logger = logging.getLogger("arcanis_automation.audit")
    for h in logger.handlers[:]:
        try:
            h.close()
        except Exception:
            pass
        logger.handlers.remove(h)


@pytest.fixture
def cfg(tmp_dirs):
    return AutomationConfig(
        workspace_dir=tmp_dirs["workspace"],
        storage_dir=tmp_dirs["storage"],
        log_dir=tmp_dirs["logs"],
        enable_scheduler=False,
    )


@pytest.fixture
def engine(cfg):
    return AutomationEngine(cfg)


@pytest.fixture
def auto(cfg):
    return Automation(cfg)


@pytest.fixture
def security():
    return SecurityContext(safe_mode=True, allowed_paths=[tempfile.mkdtemp()])


@pytest.fixture
def scheduler():
    return Scheduler(poll_interval=0.1)


@pytest.fixture
def ai():
    return WorkflowAI(LocalHeuristicProvider())


# ------------------------------------------------------------------
# Models serialization roundtrips
# ------------------------------------------------------------------

class TestActionSpecRoundtrip:
    def test_basic(self):
        spec = ActionSpec(action="notify", params={"message": "hi"}, timeout=10.0, retries=2)
        d = spec.to_dict()
        restored = ActionSpec.from_dict(d)
        assert restored.action == "notify"
        assert restored.params == {"message": "hi"}
        assert restored.timeout == 10.0
        assert restored.retries == 2

    def test_defaults(self):
        d = ActionSpec(action="shell").to_dict()
        restored = ActionSpec.from_dict(d)
        assert restored.params == {}
        assert restored.timeout == 30.0
        assert restored.retries == 0

    def test_missing_optional_fields(self):
        restored = ActionSpec.from_dict({"action": "http"})
        assert restored.timeout == 30.0
        assert restored.retries == 0

    def test_none_params_becomes_dict(self):
        restored = ActionSpec.from_dict({"action": "notify", "params": None})
        assert restored.params == {}


class TestTriggerRoundtrip:
    def test_manual(self):
        t = Trigger(type=TriggerType.MANUAL)
        d = t.to_dict()
        restored = Trigger.from_dict(d)
        assert restored.type == TriggerType.MANUAL
        assert restored.spec == {}

    def test_event_with_spec(self):
        t = Trigger(type=TriggerType.EVENT, spec={"name": "file.created"})
        d = t.to_dict()
        restored = Trigger.from_dict(d)
        assert restored.type == TriggerType.EVENT
        assert restored.spec == {"name": "file.created"}

    def test_all_trigger_types(self):
        for tt in TriggerType:
            t = Trigger(type=tt, spec={"key": "val"})
            restored = Trigger.from_dict(t.to_dict())
            assert restored.type == tt

    def test_none_spec_becomes_dict(self):
        restored = Trigger.from_dict({"type": "manual", "spec": None})
        assert restored.spec == {}


class TestScheduleRoundtrip:
    def test_interval(self):
        s = Schedule(interval_seconds=60.0, timezone="US/Eastern")
        restored = Schedule.from_dict(s.to_dict())
        assert restored.interval_seconds == 60.0
        assert restored.timezone == "US/Eastern"

    def test_cron(self):
        s = Schedule(cron="*/5 * * * *")
        restored = Schedule.from_dict(s.to_dict())
        assert restored.cron == "*/5 * * * *"

    def test_at_timestamp(self):
        ts = time.time() + 3600
        s = Schedule(at_timestamp=ts)
        restored = Schedule.from_dict(s.to_dict())
        assert restored.at_timestamp == ts

    def test_defaults(self):
        restored = Schedule.from_dict({})
        assert restored.cron is None
        assert restored.interval_seconds is None
        assert restored.at_timestamp is None
        assert restored.timezone == "UTC"

    def test_next_run_interval(self):
        s = Schedule(interval_seconds=30.0)
        now = time.time()
        nxt = s.next_run(now)
        assert nxt == now + 30.0

    def test_next_run_at_timestamp_future(self):
        ts = time.time() + 100
        s = Schedule(at_timestamp=ts)
        nxt = s.next_run()
        assert nxt == ts

    def test_next_run_at_timestamp_past(self):
        s = Schedule(at_timestamp=100.0)
        nxt = s.next_run(time.time())
        assert nxt is None

    def test_next_run_none(self):
        s = Schedule()
        nxt = s.next_run()
        assert nxt is None


class TestStepRoundtrip:
    def test_basic(self):
        step = Step(
            id="s1",
            action=ActionSpec(action="notify", params={"message": "x"}),
            name="Notify",
            run_after=["s0"],
            on_failure="continue",
            condition="true",
            captures={"msg": "output.message"},
        )
        d = step.to_dict()
        restored = Step.from_dict(d)
        assert restored.id == "s1"
        assert restored.name == "Notify"
        assert restored.action.action == "notify"
        assert restored.run_after == ["s0"]
        assert restored.on_failure == "continue"
        assert restored.condition == "true"
        assert restored.captures == {"msg": "output.message"}

    def test_defaults(self):
        restored = Step.from_dict({"id": "x", "action": {"action": "notify"}})
        assert restored.name == ""
        assert restored.run_after == []
        assert restored.on_failure == "stop"
        assert restored.condition is None
        assert restored.captures == {}


class TestPermissionRoundtrip:
    def test_deny(self):
        p = Permission(level=PermissionLevel.DENY, scope="shell")
        d = p.to_dict()
        restored = Permission.from_dict(d)
        assert restored.level == PermissionLevel.DENY
        assert restored.scope == "shell"

    def test_all_levels(self):
        for lvl in PermissionLevel:
            p = Permission(level=lvl, scope="test")
            restored = Permission.from_dict(p.to_dict())
            assert restored.level == lvl

    def test_defaults(self):
        restored = Permission.from_dict({})
        assert restored.level == PermissionLevel.EXECUTE
        assert restored.scope == "*"

    def test_allows_wildcard(self):
        p = Permission(level=PermissionLevel.EXECUTE, scope="*")
        assert p.allows("anything") is True

    def test_allows_deny(self):
        p = Permission(level=PermissionLevel.DENY, scope="shell")
        assert p.allows("shell") is False
        assert p.allows("other") is False

    def test_allows_prefix(self):
        p = Permission(level=PermissionLevel.EXECUTE, scope="file.*")
        assert p.allows("file.move") is True
        assert p.allows("file.delete") is True
        assert p.allows("app.launch") is False

    def test_allows_exact(self):
        p = Permission(level=PermissionLevel.EXECUTE, scope="app.launch")
        assert p.allows("app.launch") is True
        assert p.allows("app.kill") is False


class TestWorkflowRoundtrip:
    def test_full_workflow(self):
        wf = Workflow(
            id="wf_test",
            name="Test WF",
            description="A test",
            status=WorkflowStatus.ACTIVE,
            triggers=[Trigger(type=TriggerType.MANUAL)],
            steps=[Step(id="s1", action=ActionSpec(action="notify", params={"message": "hi"}))],
            schedule=Schedule(interval_seconds=60),
            permissions=[Permission(level=PermissionLevel.EXECUTE, scope="*")],
            owner="tester",
            tags=["test", "unit"],
            metadata={"key": "val"},
        )
        d = wf.to_dict()
        restored = Workflow.from_dict(d)
        assert restored.id == "wf_test"
        assert restored.name == "Test WF"
        assert restored.status == WorkflowStatus.ACTIVE
        assert len(restored.triggers) == 1
        assert len(restored.steps) == 1
        assert restored.schedule.interval_seconds == 60
        assert len(restored.permissions) == 1
        assert restored.owner == "tester"
        assert restored.tags == ["test", "unit"]
        assert restored.metadata == {"key": "val"}

    def test_minimal_workflow(self):
        d = {"name": "minimal"}
        wf = Workflow.from_dict(d)
        assert wf.name == "minimal"
        assert wf.id.startswith("wf_")
        assert wf.status == WorkflowStatus.DRAFT
        assert wf.triggers == []
        assert wf.steps == []
        assert wf.schedule is None
        assert wf.permissions == []
        assert wf.owner == "system"
        assert wf.tags == []
        assert wf.metadata == {}

    def test_no_schedule_roundtrip(self):
        wf = Workflow(id="w1", name="no sched")
        d = wf.to_dict()
        assert d["schedule"] is None
        restored = Workflow.from_dict(d)
        assert restored.schedule is None

    def test_to_dict_idempotent(self):
        wf = Workflow(id="w1", name="x", steps=[Step(id="s1", action=ActionSpec(action="notify"))])
        d1 = wf.to_dict()
        d2 = Workflow.from_dict(d1).to_dict()
        assert d1 == d2


class TestExecutionResultRoundtrip:
    def test_to_dict(self):
        er = ExecutionResult(step_id="s1", success=True, output={"k": "v"})
        d = er.to_dict()
        assert d["step_id"] == "s1"
        assert d["success"] is True
        assert d["output"] == {"k": "v"}
        assert d["error"] is None

    def test_failure(self):
        er = ExecutionResult(step_id="s2", success=False, error="boom", attempts=3)
        d = er.to_dict()
        assert d["success"] is False
        assert d["error"] == "boom"
        assert d["attempts"] == 3


class TestGenId:
    def test_format(self):
        gid = _gen_id()
        assert gid.startswith("wf_")
        assert len(gid) == 15

    def test_unique(self):
        ids = {_gen_id() for _ in range(100)}
        assert len(ids) == 100


# ------------------------------------------------------------------
# Engine edge cases
# ------------------------------------------------------------------

class TestEngineWorkflowLifecycle:
    def test_create_and_get(self, engine):
        wf = engine.create_workflow({"name": "test", "steps": [{"id": "s1", "action": {"action": "notify", "params": {"message": "x"}}}]})
        assert engine.get_workflow(wf.id) is not None

    def test_get_nonexistent(self, engine):
        assert engine.get_workflow("no_such_id") is None

    def test_list_workflows(self, engine):
        assert engine.list_workflows() == []
        engine.create_workflow({"name": "a", "steps": []})
        engine.create_workflow({"name": "b", "steps": []})
        assert len(engine.list_workflows()) == 2

    def test_update_workflow(self, engine):
        wf = engine.create_workflow({"name": "old", "steps": []})
        updated = engine.update_workflow(wf.id, {"name": "new", "steps": []})
        assert updated.name == "new"
        assert engine.get_workflow(wf.id).name == "new"

    def test_delete_workflow(self, engine):
        wf = engine.create_workflow({"name": "del", "steps": []})
        engine.delete_workflow(wf.id)
        assert engine.get_workflow(wf.id) is None

    def test_delete_nonexistent_no_error(self, engine):
        engine.delete_workflow("does_not_exist")

    def test_create_persists_to_disk(self, engine, tmp_dirs):
        wf = engine.create_workflow({"name": "persist", "steps": []})
        path = os.path.join(tmp_dirs["storage"], wf.id + ".json")
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert data["name"] == "persist"

    def test_load_store_on_init(self, tmp_dirs):
        wf_data = Workflow(id="wf_loaded", name="preloaded", steps=[]).to_dict()
        path = os.path.join(tmp_dirs["storage"], "wf_loaded.json")
        os.makedirs(tmp_dirs["storage"], exist_ok=True)
        with open(path, "w") as f:
            json.dump(wf_data, f)
        e = AutomationEngine(AutomationConfig(
            workspace_dir=tmp_dirs["workspace"],
            storage_dir=tmp_dirs["storage"],
            log_dir=tmp_dirs["logs"],
            enable_scheduler=False,
        ))
        assert e.get_workflow("wf_loaded") is not None

    def test_load_store_corrupt_json_skipped(self, tmp_dirs):
        os.makedirs(tmp_dirs["storage"], exist_ok=True)
        with open(os.path.join(tmp_dirs["storage"], "bad.json"), "w") as f:
            f.write("NOT JSON")
        e = AutomationEngine(AutomationConfig(
            workspace_dir=tmp_dirs["workspace"],
            storage_dir=tmp_dirs["storage"],
            log_dir=tmp_dirs["logs"],
            enable_scheduler=False,
        ))
        assert e.get_workflow("bad") is None


class TestEngineTriggerAndRun:
    def test_trigger_nonexistent_raises(self, engine):
        with pytest.raises(KeyError, match="Unknown workflow"):
            engine.trigger("no_such_id")

    def test_run_notify(self, engine):
        wf = engine.create_workflow({"name": "n", "steps": [{"id": "s1", "action": {"action": "notify", "params": {"message": "hello"}}}]})
        results = engine.trigger(wf.id)
        assert len(results) == 1
        assert results[0].success
        assert results[0].output["notified"] == "hello"

    def test_trigger_with_event(self, engine):
        wf = engine.create_workflow({"name": "n", "steps": [{"id": "s1", "action": {"action": "notify", "params": {"message": "ev"}}}]})
        results = engine.trigger(wf.id, {"type": "event", "name": "test"})
        assert results[0].success

    def test_chain_dependencies(self, engine):
        wf = engine.create_workflow({
            "name": "chain",
            "steps": [
                {"id": "a", "action": {"action": "notify", "params": {"message": "A"}}},
                {"id": "b", "action": {"action": "notify", "params": {"message": "B"}}, "run_after": ["a"]},
            ],
        })
        results = engine.trigger(wf.id)
        assert all(r.success for r in results)
        assert [r.step_id for r in results] == ["a", "b"]

    def test_step_failure_stops_downstream(self, engine):
        engine.security.permissions = [Permission(PermissionLevel.DENY, "*")]
        wf = engine.create_workflow({
            "name": "fail",
            "steps": [
                {"id": "a", "action": {"action": "notify", "params": {}}},
                {"id": "b", "action": {"action": "notify", "params": {}}, "run_after": ["a"]},
            ],
        })
        results = engine.trigger(wf.id)
        assert not any(r.success for r in results)

    def test_on_failure_continue(self, engine):
        engine.security.permissions = [Permission(PermissionLevel.DENY, "*")]
        wf = engine.create_workflow({
            "name": "cont",
            "steps": [
                {"id": "a", "action": {"action": "notify", "params": {}}, "on_failure": "continue"},
                {"id": "b", "action": {"action": "notify", "params": {}}, "on_failure": "continue"},
            ],
        })
        results = engine.trigger(wf.id)
        assert all(not r.success for r in results)

    def test_unknown_action_handler(self, engine):
        wf = engine.create_workflow({"name": "x", "steps": [{"id": "s1", "action": {"action": "nonexistent.action", "params": {}}}]})
        results = engine.trigger(wf.id)
        assert not results[0].success
        assert "no handler" in results[0].error.lower()

    def test_retry_on_failing_handler(self, engine):
        call_count = [0]

        def flaky_handler(spec, ctx, engine, log):
            call_count[0] += 1
            raise RuntimeError("transient error")

        engine.register_action("flaky.action", flaky_handler)
        wf = engine.create_workflow({
            "name": "retry",
            "steps": [{"id": "s1", "action": {"action": "flaky.action", "params": {}, "retries": 2}, "on_failure": "retry"}],
        })
        results = engine.trigger(wf.id)
        assert not results[0].success
        assert results[0].attempts == 3
        assert call_count[0] == 3


class TestEngineRegisterAndEvents:
    def test_register_custom_action(self, engine):
        def my_handler(spec, ctx, engine, log):
            return {"custom": True}
        engine.register_action("custom.action", my_handler)
        wf = engine.create_workflow({"name": "x", "steps": [{"id": "s1", "action": {"action": "custom.action", "params": {}}}]})
        results = engine.trigger(wf.id)
        assert results[0].output == {"custom": True}

    def test_on_event_subscribe(self, engine):
        events = []
        engine.on_event("workflow.created", lambda e: events.append(e.name))
        engine.create_workflow({"name": "x", "steps": []})
        assert "workflow.created" in events

    def test_emit_event_triggers_matching_workflows(self, engine):
        wf = engine.create_workflow({
            "name": "ev",
            "triggers": [{"type": "event", "spec": {"name": "file.created"}}],
            "steps": [{"id": "s1", "action": {"action": "notify", "params": {"message": "ev"}}}],
        })
        engine.emit_event("file.created", {"path": "/tmp/test.txt"})
        assert engine.get_workflow(wf.id) is not None


class TestEngineInterpolation:
    def test_string_interpolation(self):
        ctx = {"name": "world"}
        result = _interpolate("hello {{name}}", ctx, {})
        assert result == "hello world"

    def test_dict_interpolation(self):
        result = _interpolate({"a": "{{x}}"}, {}, {"x": "42"})
        assert result == {"a": "42"}

    def test_list_interpolation(self):
        result = _interpolate(["{{a}}", "b"], {"a": "1"}, {})
        assert result == ["1", "b"]

    def test_non_string_passthrough(self):
        result = _interpolate(42, {}, {})
        assert result == 42

    def test_captured_overrides_context(self):
        result = _interpolate("{{k}}", {"k": "ctx"}, {"k": "cap"})
        assert result == "cap"

    def test_resolve_nested(self):
        output = {"a": {"b": {"c": 42}}}
        assert _resolve(output, "a.b.c") == 42

    def test_resolve_missing(self):
        assert _resolve({"a": 1}, "b") is None

    def test_resolve_non_dict(self):
        assert _resolve("string", "a") is None


# ------------------------------------------------------------------
# Security guard
# ------------------------------------------------------------------

class TestSecurityContext:
    def test_default_allows_everything(self):
        ctx = SecurityContext()
        assert ctx.check("anything") is True

    def test_deny_blocks(self):
        ctx = SecurityContext(permissions=[Permission(PermissionLevel.DENY, "shell")])
        assert ctx.check("shell") is False

    def test_require_raises_on_deny(self):
        ctx = SecurityContext(permissions=[Permission(PermissionLevel.DENY, "shell")])
        with pytest.raises(SecurityError, match="denied"):
            ctx.require("shell")

    def test_admin_level_allows(self):
        ctx = SecurityContext(permissions=[Permission(PermissionLevel.ADMIN, "app.launch")])
        assert ctx.check("app.launch") is True

    def test_read_level_does_not_allow_execute(self):
        ctx = SecurityContext(permissions=[Permission(PermissionLevel.READ, "file.*")])
        assert ctx.check("file.move") is False

    def test_deny_without_grant_blocks(self):
        perms = [
            Permission(PermissionLevel.DENY, "shell"),
            Permission(PermissionLevel.EXECUTE, "notify"),
        ]
        ctx = SecurityContext(permissions=perms)
        assert ctx.check("shell") is False
        assert ctx.check("notify") is True

    def test_guard_path_safe_mode_inside(self):
        allowed = tempfile.mkdtemp()
        ctx = SecurityContext(safe_mode=True, allowed_paths=[allowed])
        inner = os.path.join(allowed, "sub", "file.txt")
        result = ctx.guard_path(inner)
        assert result == os.path.abspath(inner)

    def test_guard_path_safe_mode_outside(self):
        allowed = tempfile.mkdtemp()
        ctx = SecurityContext(safe_mode=True, allowed_paths=[allowed])
        outside = os.path.join(os.path.dirname(allowed), "outside")
        with pytest.raises(SecurityError, match="outside allowed"):
            ctx.guard_path(outside)

    def test_guard_path_unsafe_mode(self):
        ctx = SecurityContext(safe_mode=False)
        result = ctx.guard_path("/any/path")
        assert result == os.path.abspath("/any/path")

    def test_guard_path_expanduser(self):
        ctx = SecurityContext(safe_mode=False)
        result = ctx.guard_path("~/test")
        assert result.startswith(os.path.expanduser("~"))

    def test_run_shell_safe_mode(self):
        ctx = SecurityContext(safe_mode=True, permissions=[Permission(PermissionLevel.EXECUTE, "shell")])
        proc = ctx.run_shell("echo hello", timeout=5.0)
        assert proc.returncode == 0
        assert "hello" in proc.stdout

    def test_run_shell_safe_mode_dangerous_operator(self):
        ctx = SecurityContext(safe_mode=True, permissions=[Permission(PermissionLevel.EXECUTE, "shell")])
        with pytest.raises(SecurityError, match="Dangerous"):
            ctx.run_shell("echo a ; rm -rf /")

    def test_run_shell_safe_mode_pipe(self):
        ctx = SecurityContext(safe_mode=True, permissions=[Permission(PermissionLevel.EXECUTE, "shell")])
        with pytest.raises(SecurityError, match="Dangerous"):
            ctx.run_shell("echo a | cat")

    def test_run_shell_safe_mode_ampersand(self):
        ctx = SecurityContext(safe_mode=True, permissions=[Permission(PermissionLevel.EXECUTE, "shell")])
        with pytest.raises(SecurityError, match="Dangerous"):
            ctx.run_shell("echo a & echo b")

    def test_run_shell_empty_command(self):
        ctx = SecurityContext(safe_mode=True, permissions=[Permission(PermissionLevel.EXECUTE, "shell")])
        with pytest.raises(SecurityError, match="Empty"):
            ctx.run_shell("")

    def test_run_shell_denied(self):
        ctx = SecurityContext(safe_mode=True, permissions=[Permission(PermissionLevel.DENY, "shell")])
        with pytest.raises(SecurityError, match="denied"):
            ctx.run_shell("echo x")

    def test_run_shell_unsafe_mode(self):
        ctx = SecurityContext(safe_mode=False, permissions=[Permission(PermissionLevel.EXECUTE, "shell")])
        proc = ctx.run_shell("echo safe_off", timeout=5.0)
        assert proc.returncode == 0

    def test_raise_denied_static(self):
        with pytest.raises(SecurityError, match="test.action"):
            SecurityContext.raise_denied("test.action")


class TestAuditLogger:
    def _clear_audit_logger(self):
        logger = logging.getLogger("arcanis_automation.audit")
        logger.handlers.clear()

    def test_record_and_read(self, tmp_dirs):
        self._clear_audit_logger()
        log = AuditLogger(tmp_dirs["logs"], enabled=True)
        log.record("test_event", key="value")
        for h in log._logger.handlers:
            h.flush()
        lines = log.read()
        assert any("test_event" in l for l in lines)

    def test_disabled_logger_no_output(self, tmp_dirs):
        self._clear_audit_logger()
        log = AuditLogger(tmp_dirs["logs"], enabled=False)
        log.record("should_not_appear")
        lines = log.read()
        assert lines == []

    def test_read_no_file(self, tmp_dirs):
        self._clear_audit_logger()
        log = AuditLogger(os.path.join(tmp_dirs["logs"], "empty"), enabled=False)
        lines = log.read()
        assert lines == []

    def test_read_limit(self, tmp_dirs):
        self._clear_audit_logger()
        log = AuditLogger(tmp_dirs["logs"], enabled=True)
        for i in range(10):
            log.record(f"event_{i}")
        for h in log._logger.handlers:
            h.flush()
        lines = log.read(limit=3)
        assert len(lines) == 3


# ------------------------------------------------------------------
# Scheduler
# ------------------------------------------------------------------

class TestScheduler:
    def test_register_returns_task_id(self, scheduler):
        wf = Workflow(id="w1", name="s", schedule=Schedule(interval_seconds=1))
        tid = scheduler.register(wf, lambda wid: None)
        assert tid is not None
        assert tid.startswith("task_")

    def test_register_no_schedule_returns_none(self, scheduler):
        wf = Workflow(id="w1", name="s")
        tid = scheduler.register(wf, lambda wid: None)
        assert tid is None

    def test_unregister(self, scheduler):
        wf = Workflow(id="w1", name="s", schedule=Schedule(interval_seconds=1))
        tid = scheduler.register(wf, lambda wid: None)
        scheduler.unregister(tid)
        assert scheduler.list_tasks() == []

    def test_unregister_nonexistent_no_error(self, scheduler):
        scheduler.unregister("task_nope")

    def test_disable_and_enable(self, scheduler):
        wf = Workflow(id="w1", name="s", schedule=Schedule(interval_seconds=1))
        tid = scheduler.register(wf, lambda wid: None)
        scheduler.disable(tid)
        tasks = scheduler.list_tasks()
        assert tasks[0]["enabled"] is False
        scheduler.enable(tid)
        tasks = scheduler.list_tasks()
        assert tasks[0]["enabled"] is True

    def test_disable_nonexistent_no_error(self, scheduler):
        scheduler.disable("task_nope")

    def test_enable_nonexistent_no_error(self, scheduler):
        scheduler.enable("task_nope")

    def test_list_tasks(self, scheduler):
        wf = Workflow(id="w1", name="s", schedule=Schedule(interval_seconds=1))
        scheduler.register(wf, lambda wid: None)
        tasks = scheduler.list_tasks()
        assert len(tasks) == 1
        assert tasks[0]["workflow_id"] == "w1"
        assert tasks[0]["next_run"] is not None

    def test_start_and_stop(self, scheduler):
        scheduler.start()
        assert scheduler._thread is not None
        assert scheduler._thread.is_alive()
        scheduler.stop()
        assert not scheduler._thread.is_alive()

    def test_start_idempotent(self, scheduler):
        scheduler.start()
        t1 = scheduler._thread
        scheduler.start()
        assert scheduler._thread is t1
        scheduler.stop()

    def test_callback_executed(self, scheduler):
        executed = []
        wf = Workflow(id="w1", name="s", schedule=Schedule(interval_seconds=0.05))
        scheduler.register(wf, lambda wid: executed.append(wid))
        scheduler.start()
        time.sleep(0.3)
        scheduler.stop()
        assert "w1" in executed


class TestScheduledTask:
    def test_task_fields(self):
        wf = Workflow(id="w1", name="s", schedule=Schedule(interval_seconds=10))
        cb = lambda wid: None
        task = ScheduledTask(wf.id, wf.schedule, cb)
        assert task.workflow_id == "w1"
        assert task.enabled is True
        assert task.last_run is None
        assert task.next_run is not None


# ------------------------------------------------------------------
# AI capabilities
# ------------------------------------------------------------------

class TestWorkflowAI:
    def test_heuristic_generate_organize(self, ai):
        wf = ai.generate("organize my downloads folder")
        assert wf.steps
        kinds = [s.action.action for s in wf.steps]
        assert "file.organize" in kinds

    def test_heuristic_generate_notify(self, ai):
        wf = ai.generate("notify me when done")
        kinds = [s.action.action for s in wf.steps]
        assert "notify" in kinds

    def test_heuristic_generate_research(self, ai):
        wf = ai.generate("research the latest AI trends")
        kinds = [s.action.action for s in wf.steps]
        assert "research.query" in kinds

    def test_heuristic_generate_launch(self, ai):
        wf = ai.generate("launch the app")
        kinds = [s.action.action for s in wf.steps]
        assert "app.launch" in kinds

    def test_heuristic_generate_fallback(self, ai):
        wf = ai.generate("do something random with no keywords")
        assert wf.steps
        assert wf.triggers[0].type == TriggerType.MANUAL

    def test_generate_owner(self, ai):
        wf = ai.generate("test", owner="custom_owner")
        assert wf.owner == "custom_owner"

    def test_optimize_removes_duplicates(self, ai):
        wf = Workflow(id="w1", name="dup", steps=[
            Step(id="s1", action=ActionSpec(action="notify", params={"message": "a"})),
            Step(id="s2", action=ActionSpec(action="notify", params={"message": "a"})),
            Step(id="s3", action=ActionSpec(action="notify", params={"message": "b"})),
        ])
        optimized = ai.optimize(wf)
        assert len(optimized.steps) == 2

    def test_optimize_keeps_unique(self, ai):
        wf = Workflow(id="w1", name="uniq", steps=[
            Step(id="s1", action=ActionSpec(action="notify", params={"message": "a"})),
            Step(id="s2", action=ActionSpec(action="shell", params={"command": "echo"})),
        ])
        optimized = ai.optimize(wf)
        assert len(optimized.steps) == 2

    def test_detect_failures_healthy(self, ai):
        results = [
            {"step_id": "s1", "success": True},
            {"step_id": "s2", "success": True},
        ]
        report = ai.detect_failures(results)
        assert report["healthy"] is True
        assert report["failed"] == 0
        assert report["total"] == 2
        assert report["diagnosis"] == "No failures detected."

    def test_detect_failures_unhealthy(self, ai):
        results = [
            {"step_id": "s1", "success": True},
            {"step_id": "s2", "success": False, "error": "timeout"},
        ]
        report = ai.detect_failures(results)
        assert report["healthy"] is False
        assert report["failed"] == 1
        assert report["failures"][0]["step_id"] == "s2"
        assert report["failures"][0]["error"] == "timeout"

    def test_detect_failures_empty(self, ai):
        report = ai.detect_failures([])
        assert report["healthy"] is True
        assert report["total"] == 0

    def test_suggest_optimizations_missing_dep(self, ai):
        wf = Workflow(id="w1", name="x", steps=[
            Step(id="s1", action=ActionSpec(action="notify"), run_after=["missing"]),
        ])
        suggestions = ai.suggest_optimizations(wf)
        assert any("missing" in s for s in suggestions)

    def test_suggest_optimizations_no_trigger(self, ai):
        wf = Workflow(id="w1", name="x", steps=[
            Step(id="s1", action=ActionSpec(action="notify")),
        ])
        suggestions = ai.suggest_optimizations(wf)
        assert any("No trigger" in s for s in suggestions)

    def test_suggest_optimizations_many_stop_on_failure(self, ai):
        steps = [Step(id=f"s{i}", action=ActionSpec(action="notify"), on_failure="stop") for i in range(5)]
        wf = Workflow(id="w1", name="x", steps=steps)
        suggestions = ai.suggest_optimizations(wf)
        assert any("stop on failure" in s for s in suggestions)

    def test_extract_json_valid(self):
        result = WorkflowAI._extract_json('Here is {"name": "test"} the json')
        assert result == {"name": "test"}

    def test_extract_json_none(self):
        assert WorkflowAI._extract_json("no json here") is None

    def test_extract_json_invalid(self):
        assert WorkflowAI._extract_json("{not valid json}") is None


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

class TestAutomationConfig:
    def test_defaults(self):
        cfg = AutomationConfig()
        assert cfg.enable_scheduler is True
        assert cfg.safe_mode is True
        assert cfg.max_concurrent_steps == 8
        assert cfg.audit_all is True
        assert cfg.ai_provider == "local"
        assert cfg.default_permission_level == "execute"
        assert cfg.metadata == {}

    def test_custom_values(self):
        cfg = AutomationConfig(
            enable_scheduler=False,
            safe_mode=False,
            max_concurrent_steps=4,
            ai_provider="openai",
            metadata={"env": "test"},
        )
        assert cfg.enable_scheduler is False
        assert cfg.safe_mode is False
        assert cfg.max_concurrent_steps == 4
        assert cfg.ai_provider == "openai"
        assert cfg.metadata == {"env": "test"}

    def test_ensure_dirs(self, tmp_dirs):
        cfg = AutomationConfig(
            workspace_dir=tmp_dirs["workspace"],
            storage_dir=tmp_dirs["storage"],
            log_dir=tmp_dirs["logs"],
        )
        assert not os.path.exists(tmp_dirs["workspace"])
        cfg.ensure_dirs()
        assert os.path.isdir(tmp_dirs["workspace"])
        assert os.path.isdir(tmp_dirs["storage"])
        assert os.path.isdir(tmp_dirs["logs"])

    def test_ensure_dirs_idempotent(self, tmp_dirs):
        cfg = AutomationConfig(
            workspace_dir=tmp_dirs["workspace"],
            storage_dir=tmp_dirs["storage"],
            log_dir=tmp_dirs["logs"],
        )
        cfg.ensure_dirs()
        cfg.ensure_dirs()
        assert os.path.isdir(tmp_dirs["workspace"])


# ------------------------------------------------------------------
# AI providers
# ------------------------------------------------------------------

class TestProviders:
    def test_local_provider_complete(self):
        p = LocalHeuristicProvider()
        result = p.complete("test prompt")
        assert "Local heuristic" in result

    def test_local_provider_research(self):
        p = LocalHeuristicProvider()
        result = p.research("AI trends", depth=2)
        assert result["query"] == "AI trends"
        assert result["depth"] == 2
        assert len(result["findings"]) > 0

    def test_get_provider_local(self):
        p = get_provider("local")
        assert isinstance(p, LocalHeuristicProvider)

    def test_get_provider_unknown_falls_back(self):
        p = get_provider("nonexistent_provider")
        assert isinstance(p, LocalHeuristicProvider)


# ------------------------------------------------------------------
# CLI parsing
# ------------------------------------------------------------------

class TestCLI:
    def test_list_command(self):
        from arcanis_automation.cli import main
        import io
        import sys

        captured = io.StringIO()
        sys.stdout = captured
        try:
            main(["list"])
        finally:
            sys.stdout = sys.__stdout__
        assert isinstance(captured.getvalue(), str)

    def test_create_command(self, tmp_dirs):
        wf_data = {"name": "cli_create", "steps": [{"id": "s1", "action": {"action": "notify", "params": {"message": "hi"}}}]}
        wf_file = os.path.join(tmp_dirs["root"], "wf.json")
        with open(wf_file, "w") as f:
            json.dump(wf_data, f)
        from arcanis_automation.cli import main
        import io
        import sys

        captured = io.StringIO()
        sys.stdout = captured
        try:
            main(["create", wf_file])
        finally:
            sys.stdout = sys.__stdout__
        assert "created" in captured.getvalue()

    def test_generate_command(self):
        from arcanis_automation.cli import main
        import io
        import sys

        captured = io.StringIO()
        sys.stdout = captured
        try:
            main(["generate", "notify me when done"])
        finally:
            sys.stdout = sys.__stdout__
        assert "generated" in captured.getvalue()


# ------------------------------------------------------------------
# Integration: full workflow with file operations
# ------------------------------------------------------------------

class TestFileActions:
    def test_file_move(self, auto, tmp_dirs):
        src = os.path.join(tmp_dirs["workspace"], "src.txt")
        dst = os.path.join(tmp_dirs["workspace"], "dst.txt")
        with open(src, "w") as f:
            f.write("hello")
        wid = auto.create("move", [{"id": "s1", "action": {"action": "file.move", "params": {"source": src, "destination": dst}}}])
        results = auto.run(wid)
        assert results[0].success
        assert os.path.exists(dst)
        assert not os.path.exists(src)

    def test_file_copy(self, auto, tmp_dirs):
        src = os.path.join(tmp_dirs["workspace"], "src2.txt")
        dst = os.path.join(tmp_dirs["workspace"], "dst2.txt")
        with open(src, "w") as f:
            f.write("data")
        wid = auto.create("copy", [{"id": "s1", "action": {"action": "file.copy", "params": {"source": src, "destination": dst}}}])
        results = auto.run(wid)
        assert results[0].success
        assert os.path.exists(src)
        assert os.path.exists(dst)

    def test_file_delete(self, auto, tmp_dirs):
        target = os.path.join(tmp_dirs["workspace"], "to_delete.txt")
        with open(target, "w") as f:
            f.write("bye")
        wid = auto.create("del", [{"id": "s1", "action": {"action": "file.delete", "params": {"target": target}}}])
        results = auto.run(wid)
        assert results[0].success
        assert not os.path.exists(target)

    def test_file_organize(self, auto, tmp_dirs):
        ws = tmp_dirs["workspace"]
        for name in ["a.png", "b.pdf", "c.mp3"]:
            with open(os.path.join(ws, name), "w") as f:
                f.write("x")
        wid = auto.create("org", [{"id": "s1", "action": {"action": "file.organize", "params": {"source": ws}}}])
        results = auto.run(wid)
        assert results[0].success
        assert results[0].output["organized"] == 3

    def test_file_organize_by_extension(self, auto, tmp_dirs):
        ws = tmp_dirs["workspace"]
        for name in ["x.py", "y.js"]:
            with open(os.path.join(ws, name), "w") as f:
                f.write("c")
        wid = auto.create("org", [{"id": "s1", "action": {"action": "file.organize", "params": {"source": ws, "by_extension": True}}}])
        results = auto.run(wid)
        assert results[0].success


class TestDataActions:
    def test_data_transform_uppercase(self, auto, tmp_dirs):
        src = os.path.join(tmp_dirs["workspace"], "in.txt")
        with open(src, "w") as f:
            f.write("hello world")
        wid = auto.create("dt", [{"id": "s1", "action": {"action": "data.transform", "params": {"source": src, "operation": "uppercase"}}}])
        results = auto.run(wid)
        assert results[0].success

    def test_data_transform_with_destination(self, auto, tmp_dirs):
        src = os.path.join(tmp_dirs["workspace"], "in2.txt")
        dst = os.path.join(tmp_dirs["workspace"], "out2.txt")
        with open(src, "w") as f:
            f.write("hello")
        wid = auto.create("dt", [{"id": "s1", "action": {"action": "data.transform", "params": {"source": src, "operation": "uppercase", "destination": dst}}}])
        results = auto.run(wid)
        assert results[0].success
        assert os.path.exists(dst)

    def test_data_transform_json(self, auto, tmp_dirs):
        src = os.path.join(tmp_dirs["workspace"], "data.json")
        with open(src, "w") as f:
            json.dump({"key": "value"}, f)
        wid = auto.create("dt", [{"id": "s1", "action": {"action": "data.transform", "params": {"source": src, "operation": "uppercase"}}}])
        results = auto.run(wid)
        assert results[0].success

    def test_data_aggregate(self, auto, tmp_dirs):
        src = os.path.join(tmp_dirs["workspace"], "agg.json")
        with open(src, "w") as f:
            json.dump([{"cat": "a", "val": "10"}, {"cat": "a", "val": "20"}, {"cat": "b", "val": "5"}], f)
        wid = auto.create("da", [{"id": "s1", "action": {"action": "data.aggregate", "params": {"source": src, "group_by": "cat", "metric": "val"}}}])
        results = auto.run(wid)
        assert results[0].success
        assert results[0].output["aggregated"]["a"] == 30.0
        assert results[0].output["aggregated"]["b"] == 5.0


# ------------------------------------------------------------------
# Engine with scheduler enabled
# ------------------------------------------------------------------

class TestEngineWithScheduler:
    def test_start_registers_scheduled_workflows(self, tmp_dirs):
        cfg = AutomationConfig(
            workspace_dir=tmp_dirs["workspace"],
            storage_dir=tmp_dirs["storage"],
            log_dir=tmp_dirs["logs"],
            enable_scheduler=True,
        )
        e = AutomationEngine(cfg)
        e.create_workflow({
            "name": "scheduled",
            "schedule": {"interval_seconds": 60},
            "steps": [{"id": "s1", "action": {"action": "notify", "params": {"message": "x"}}}],
        })
        e.start()
        assert e.scheduler is not None
        tasks = e.scheduler.list_tasks()
        assert len(tasks) >= 1
        e.stop()

    def test_stop_without_scheduler(self, engine):
        engine.stop()

    def test_start_without_scheduler(self, engine):
        engine.start()


# ------------------------------------------------------------------
# Security path sandboxing edge cases
# ------------------------------------------------------------------

class TestPathSandboxing:
    def test_multiple_allowed_paths(self, tmp_dirs):
        allowed1 = tempfile.mkdtemp()
        allowed2 = tempfile.mkdtemp()
        ctx = SecurityContext(safe_mode=True, allowed_paths=[allowed1, allowed2])
        f1 = os.path.join(allowed1, "file.txt")
        f2 = os.path.join(allowed2, "file.txt")
        assert ctx.guard_path(f1) == os.path.abspath(f1)
        assert ctx.guard_path(f2) == os.path.abspath(f2)

    def test_symlink_like_path_traversal(self, tmp_dirs):
        allowed = tempfile.mkdtemp()
        ctx = SecurityContext(safe_mode=True, allowed_paths=[allowed])
        traversal = os.path.join(allowed, "..", "outside")
        with pytest.raises(SecurityError):
            ctx.guard_path(traversal)

    def test_relative_path_inside(self, tmp_dirs):
        allowed = tempfile.mkdtemp()
        ctx = SecurityContext(safe_mode=True, allowed_paths=[allowed])
        inner = os.path.join(allowed, "sub")
        result = ctx.guard_path(inner)
        assert os.path.abspath(inner) == result


# ------------------------------------------------------------------
# Engine event system
# ------------------------------------------------------------------

class TestEngineEvents:
    def test_emit_captures_event(self, engine):
        received = []
        engine.on_event("workflow.created", lambda e: received.append(e))
        engine.create_workflow({"name": "x", "steps": []})
        assert len(received) == 1
        assert received[0].payload["name"] == "x"

    def test_subscriber_exception_does_not_crash(self, engine):
        def bad_subscriber(e):
            raise RuntimeError("oops")
        engine.on_event("workflow.created", bad_subscriber)
        engine.create_workflow({"name": "x", "steps": []})

    def test_multiple_subscribers(self, engine):
        a, b = [], []
        engine.on_event("workflow.created", lambda e: a.append(1))
        engine.on_event("workflow.created", lambda e: b.append(1))
        engine.create_workflow({"name": "x", "steps": []})
        assert len(a) == 1
        assert len(b) == 1


# ------------------------------------------------------------------
# Engine: AI helpers via engine
# ------------------------------------------------------------------

class TestEngineAIHelpers:
    def test_generate_workflow(self, engine):
        wf = engine.generate_workflow("organize my files and notify me")
        assert wf.steps
        assert engine.get_workflow(wf.id) is not None

    def test_optimize_workflow(self, engine):
        wf = engine.create_workflow({
            "name": "opt",
            "steps": [
                {"id": "s1", "action": {"action": "notify", "params": {"message": "a"}}},
                {"id": "s2", "action": {"action": "notify", "params": {"message": "a"}}},
                {"id": "s3", "action": {"action": "notify", "params": {"message": "b"}}},
            ],
        })
        optimized = engine.optimize_workflow(wf.id)
        assert len(optimized.steps) == 2

    def test_detect_failures_healthy(self, engine):
        wf = engine.create_workflow({"name": "f", "steps": [{"id": "s1", "action": {"action": "notify", "params": {"message": "x"}}}]})
        engine.trigger(wf.id)
        report = engine.detect_failures(wf.id)
        assert report["healthy"] is True
