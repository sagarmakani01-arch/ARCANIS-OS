"""Test automation - discovery, execution, and reporting."""

import os
import glob
import time
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    error: Optional[str] = None
    output: Optional[str] = None

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass
class TestSuite:
    name: str
    results: List[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def duration(self) -> float:
        return sum(r.duration for r in self.results)

    def summary(self) -> str:
        return f"{self.passed}/{self.total} passed ({self.duration:.2f}s)"


class TestRunner:
    def __init__(self, source_dir: str = "tests", pattern: str = "test_*.arc", timeout: int = 30):
        self.source_dir = source_dir
        self.pattern = pattern
        self.timeout = timeout

    def discover_tests(self) -> List[str]:
        search_path = os.path.join(self.source_dir, self.pattern)
        return sorted(glob.glob(search_path))

    def run_single(self, test_path: str) -> TestResult:
        name = os.path.splitext(os.path.basename(test_path))[0]
        start = time.time()

        try:
            result = subprocess.run(
                ["arcanisc", "run", "--test", test_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            duration = time.time() - start
            passed = result.returncode == 0
            return TestResult(
                name=name,
                passed=passed,
                duration=duration,
                error=result.stderr if not passed else None,
                output=result.stdout,
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            return TestResult(
                name=name,
                passed=False,
                duration=duration,
                error="Test timed out",
            )
        except FileNotFoundError:
            duration = time.time() - start
            return TestResult(
                name=name,
                passed=False,
                duration=duration,
                error="ArcanisLang compiler not found (arcanisc)",
            )

    def run_all(self, parallel: bool = True, max_workers: int = 4,
                progress_callback: Callable = None) -> TestSuite:
        tests = self.discover_tests()
        suite = TestSuite(name=os.path.basename(self.source_dir))

        if not tests:
            suite.results.append(TestResult(
                name="discovery",
                passed=False,
                duration=0,
                error=f"No tests found matching '{self.pattern}' in '{self.source_dir}'",
            ))
            return suite

        if parallel and len(tests) > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(self.run_single, t): t for t in tests}
                for future in as_completed(futures):
                    result = future.result()
                    suite.results.append(result)
                    if progress_callback:
                        progress_callback(result)
        else:
            for test_path in tests:
                result = self.run_single(test_path)
                suite.results.append(result)
                if progress_callback:
                    progress_callback(result)

        return suite
