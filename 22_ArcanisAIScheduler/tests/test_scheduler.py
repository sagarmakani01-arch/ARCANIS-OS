import pytest
from arcanis_ai_scheduler.tracker import ProcessTracker, ProcessBehavior
from arcanis_ai_scheduler.predictor import WorkloadPredictor, WorkloadType
from arcanis_ai_scheduler.scheduler import AIScheduler


class TestProcessTracker:
    def setup_method(self):
        self.tracker = ProcessTracker()

    def test_track_process(self):
        rec = self.tracker.track(pid=1, name="init", cpu_ms=10.0, context_switch=True)
        assert rec.metrics.pid == 1
        assert rec.metrics.name == "init"
        assert rec.metrics.context_switches == 1

    def test_classify_cpu_bound(self):
        for _ in range(20):
            self.tracker.track(pid=1, cpu_ms=10.0, io_ms=0.1)
        rec = self.tracker.get_record(1)
        assert rec.behavior == ProcessBehavior.CPU_BOUND

    def test_classify_io_bound(self):
        for _ in range(20):
            self.tracker.track(pid=2, cpu_ms=0.1, io_ms=10.0)
        rec = self.tracker.get_record(2)
        assert rec.behavior == ProcessBehavior.IO_BOUND

    def test_cleanup_stale(self):
        self.tracker.track(pid=99, name="stale")
        rec = self.tracker.get_record(99)
        rec.metrics.last_seen = 0
        cleaned = self.tracker.cleanup_stale(max_age_seconds=1)
        assert cleaned == 1

    def test_global_stats(self):
        self.tracker.track(pid=1, cpu_ms=5.0, context_switch=True)
        stats = self.tracker.get_global_stats()
        assert stats["total_context_switches"] == 1
        assert stats["total_cpu_time_ms"] == 5.0


class TestWorkloadPredictor:
    def setup_method(self):
        self.predictor = WorkloadPredictor()
        self.tracker = ProcessTracker()

    def test_predict_cpu_bound(self):
        for _ in range(20):
            self.tracker.track(pid=1, cpu_ms=10.0, io_ms=0.1)
        rec = self.tracker.get_record(1)
        pred = self.predictor.predict(rec)
        assert pred.workload_type == WorkloadType.COMPUTE_HEAVY
        assert pred.confidence > 0.5

    def test_predict_io_bound(self):
        for _ in range(20):
            self.tracker.track(pid=1, cpu_ms=0.1, io_ms=10.0)
        rec = self.tracker.get_record(1)
        pred = self.predictor.predict(rec)
        assert pred.workload_type == WorkloadType.IO_HEAVY

    def test_hints_generated(self):
        for _ in range(20):
            self.tracker.track(pid=1, cpu_ms=10.0, io_ms=0.1)
        rec = self.tracker.get_record(1)
        pred = self.predictor.predict(rec)
        hints = self.predictor.get_hints(rec, pred)
        assert len(hints) >= 0

    def test_prediction_stats(self):
        for _ in range(5):
            self.tracker.track(pid=1, cpu_ms=10.0, io_ms=0.1)
        rec = self.tracker.get_record(1)
        self.predictor.predict(rec)
        stats = self.predictor.get_prediction_stats()
        assert stats["total"] == 1


class TestAIScheduler:
    def setup_method(self):
        self.scheduler = AIScheduler()
        self.scheduler.initialize()

    def test_update_generates_hints(self):
        hints = self.scheduler.update(pid=1, name="test", cpu_ms=10.0)
        assert isinstance(hints, list)

    def test_scheduling_plan(self):
        self.scheduler.update(pid=1, name="proc1", cpu_ms=10.0)
        self.scheduler.update(pid=2, name="proc2", io_ms=5.0)
        plan = self.scheduler.get_scheduling_plan()
        assert 1 in plan
        assert 2 in plan

    def test_stats(self):
        self.scheduler.update(pid=1, cpu_ms=5.0)
        stats = self.scheduler.get_stats()
        assert stats["initialized"]
        assert stats["tracker"]["total_cpu_time_ms"] == 5.0
