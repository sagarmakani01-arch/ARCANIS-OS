"""Arcanis Integration Tests — cross-module integration verification."""

from __future__ import annotations

import sys
import time
from typing import Any


class TestResult:
    def __init__(self, name: str, passed: bool, message: str = "", duration_ms: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration_ms = duration_ms


class IntegrationTestSuite:
    def __init__(self):
        self._results: list[TestResult] = []
        self._setup_complete = False

    def setup(self) -> None:
        self._setup_complete = True

    def _record(self, name: str, passed: bool, message: str = "", start: float = 0.0) -> None:
        duration = (time.time() - start) * 1000 if start else 0.0
        self._results.append(TestResult(name=name, passed=passed, message=message, duration_ms=duration))

    def test_security_capability_model(self) -> None:
        start = time.time()
        try:
            from arcanis_security.capability import Capability
            from arcanis_security.manager import CapabilityManager
            cm = CapabilityManager()
            cap = Capability(name="test", description="test")
            cm.register(cap)
            granted = cm.grant("subject", cap)
            self._record("security_capability_model", granted, start=start)
        except Exception as e:
            self._record("security_capability_model", False, str(e), start)

    def test_hal_device_enumeration(self) -> None:
        start = time.time()
        try:
            from arcanis_hal.hal import HardwareAbstractionLayer
            hal = HardwareAbstractionLayer()
            hal.initialize()
            self._record("hal_device_enumeration", True, start=start)
        except Exception as e:
            self._record("hal_device_enumeration", False, str(e), start)

    def test_inference_engine(self) -> None:
        start = time.time()
        try:
            from arcanis_inference.engine import InferenceEngine
            engine = InferenceEngine()
            self._record("inference_engine", True, start=start)
        except Exception as e:
            self._record("inference_engine", False, str(e), start)

    def test_shell_inference_bridge(self) -> None:
        start = time.time()
        try:
            from arcanis_shell.inference_adapter import ShellInferenceBridge
            bridge = ShellInferenceBridge()
            self._record("shell_inference_bridge", True, start=start)
        except Exception as e:
            self._record("shell_inference_bridge", False, str(e), start)

    def test_ai_scheduler(self) -> None:
        start = time.time()
        try:
            from arcanis_ai_scheduler.scheduler import AIScheduler
            scheduler = AIScheduler()
            scheduler.initialize()
            self._record("ai_scheduler", True, start=start)
        except Exception as e:
            self._record("ai_scheduler", False, str(e), start)

    def test_semantic_fs(self) -> None:
        start = time.time()
        try:
            from arcanis_semantic_fs.engine import SemanticFSEngine
            engine = SemanticFSEngine()
            engine.initialize()
            self._record("semantic_fs", True, start=start)
        except Exception as e:
            self._record("semantic_fs", False, str(e), start)

    def test_driver_synth(self) -> None:
        start = time.time()
        try:
            from arcanis_driver_synth import DriverSynthesizer, HardwareSpec
            ds = DriverSynthesizer()
            spec = HardwareSpec(device_class="network", vendor_id=0x1234, product_id=0x5678)
            ds.analyze(spec)
            self._record("driver_synth", True, start=start)
        except Exception as e:
            self._record("driver_synth", False, str(e), start)

    def test_federated_learning(self) -> None:
        start = time.time()
        try:
            from arcanis_federated import FederatedCoordinator
            fc = FederatedCoordinator()
            fc.initialize()
            self._record("federated_learning", True, start=start)
        except Exception as e:
            self._record("federated_learning", False, str(e), start)

    def test_agent_sdk(self) -> None:
        start = time.time()
        try:
            from arcanis_agent_sdk import AgentSDK
            sdk = AgentSDK()
            sdk.initialize()
            self._record("agent_sdk", True, start=start)
        except Exception as e:
            self._record("agent_sdk", False, str(e), start)

    def test_experiments(self) -> None:
        start = time.time()
        try:
            from arcanis_experiments import ExperimentRunner, ExperimentConfig
            runner = ExperimentRunner()
            config = ExperimentConfig(name="test", execute=lambda: "ok")
            exp_id = runner.register(config)
            result = runner.run(exp_id)
            self._record("experiments", result.passed if hasattr(result, 'passed') else result.status.value == "completed", start=start)
        except Exception as e:
            self._record("experiments", False, str(e), start)

    def test_research_tracker(self) -> None:
        start = time.time()
        try:
            from arcanis_research import KnowledgeBase
            kb = KnowledgeBase()
            topic_id = kb.add_topic("Test Topic", "Description")
            self._record("research_tracker", True, start=start)
        except Exception as e:
            self._record("research_tracker", False, str(e), start)

    def test_assets_registry(self) -> None:
        start = time.time()
        try:
            from arcanis_assets import AssetRegistry
            registry = AssetRegistry()
            asset_id = registry.register_asset("test.png", category="image")
            self._record("assets_registry", True, start=start)
        except Exception as e:
            self._record("assets_registry", False, str(e), start)

    def test_unified_cli(self) -> None:
        start = time.time()
        try:
            from arcanis_cli import main
            result = main(["version"])
            self._record("unified_cli", result == 0, start=start)
        except Exception as e:
            self._record("unified_cli", False, str(e), start)

    def run_all(self) -> list[TestResult]:
        if not self._setup_complete:
            self.setup()
        tests = [
            self.test_security_capability_model,
            self.test_hal_device_enumeration,
            self.test_inference_engine,
            self.test_shell_inference_bridge,
            self.test_ai_scheduler,
            self.test_semantic_fs,
            self.test_driver_synth,
            self.test_federated_learning,
            self.test_agent_sdk,
            self.test_experiments,
            self.test_research_tracker,
            self.test_assets_registry,
            self.test_unified_cli,
        ]
        for test_fn in tests:
            test_fn()
        return self._results

    def summary(self) -> dict:
        passed = sum(1 for r in self._results if r.passed)
        failed = sum(1 for r in self._results if not r.passed)
        total_ms = sum(r.duration_ms for r in self._results)
        return {
            "total": len(self._results),
            "passed": passed,
            "failed": failed,
            "total_ms": round(total_ms, 2),
            "results": [{"name": r.name, "passed": r.passed, "message": r.message, "ms": round(r.duration_ms, 2)}
                        for r in self._results],
        }
