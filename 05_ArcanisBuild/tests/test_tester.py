"""Tests for test runner."""

import os
import tempfile
import unittest

from arcanis_build.tester import TestRunner, TestResult, TestSuite


class TestTestResult(unittest.TestCase):
    def test_passing_result(self):
        r = TestResult(name="test_foo", passed=True, duration=0.5)
        self.assertEqual(r.status, "PASS")
        self.assertTrue(r.passed)

    def test_failing_result(self):
        r = TestResult(name="test_bar", passed=False, duration=0.3, error="assertion failed")
        self.assertEqual(r.status, "FAIL")
        self.assertFalse(r.passed)
        self.assertEqual(r.error, "assertion failed")


class TestTestSuite(unittest.TestCase):
    def test_suite_summary(self):
        suite = TestSuite(name="core")
        suite.results.append(TestResult("t1", True, 0.1))
        suite.results.append(TestResult("t2", True, 0.2))
        suite.results.append(TestResult("t3", False, 0.3, "fail"))
        self.assertEqual(suite.passed, 2)
        self.assertEqual(suite.failed, 1)
        self.assertEqual(suite.total, 3)
        self.assertIn("2/3", suite.summary())


class TestTestRunner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = os.path.join(self.temp_dir, "tests")
        os.makedirs(self.test_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discover_no_tests(self):
        runner = TestRunner(source_dir=self.test_dir)
        tests = runner.discover_tests()
        self.assertEqual(len(tests), 0)

    def test_discover_tests(self):
        test_file = os.path.join(self.test_dir, "test_something.arc")
        with open(test_file, "w") as f:
            f.write("// test")

        runner = TestRunner(source_dir=self.test_dir)
        tests = runner.discover_tests()
        self.assertEqual(len(tests), 1)
        self.assertTrue(tests[0].endswith("test_something.arc"))

    def test_discover_with_pattern(self):
        for fname in ["test_a.arc", "test_b.arc", "helper.arc"]:
            with open(os.path.join(self.test_dir, fname), "w") as f:
                f.write("//")

        runner = TestRunner(source_dir=self.test_dir, pattern="test_*.arc")
        tests = runner.discover_tests()
        self.assertEqual(len(tests), 2)

    def test_run_single_missing_compiler(self):
        test_file = os.path.join(self.test_dir, "test_missing.arc")
        with open(test_file, "w") as f:
            f.write("// test")

        runner = TestRunner(source_dir=self.test_dir)
        result = runner.run_single(test_file)
        self.assertFalse(result.passed)
        self.assertIn("not found", result.error.lower())

    def test_run_all_empty_dir(self):
        runner = TestRunner(source_dir=self.test_dir)
        suite = runner.run_all(parallel=False)
        self.assertEqual(suite.failed, 1)
        self.assertIn("No tests found", suite.results[0].error)


if __name__ == "__main__":
    unittest.main()
