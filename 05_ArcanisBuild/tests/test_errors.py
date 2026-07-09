"""Tests for error reporting."""

import unittest
from io import StringIO
import sys

from arcanis_build.errors import (
    BuildError,
    CompilationError,
    ConfigError,
    ErrorReporter,
    Diagnostic,
)


class TestBuildError(unittest.TestCase):
    def test_basic_error(self):
        err = BuildError("something went wrong")
        self.assertEqual(str(err), "something went wrong")

    def test_error_with_target(self):
        err = BuildError("failed", target="app")
        self.assertIn("(app)", str(err))

    def test_error_with_file(self):
        err = BuildError("syntax error", file="main.arc", line=42)
        self.assertIn("[main.arc:42]", str(err))

    def test_compilation_error(self):
        err = CompilationError("undefined variable", file="test.arc", line=10, code="E001")
        self.assertIn("E001", str(err))

    def test_config_error(self):
        err = ConfigError("missing field", field="compiler")
        self.assertEqual(str(err), "missing field")


class TestDiagnostic(unittest.TestCase):
    def test_diagnostic_formatting(self):
        d = Diagnostic("error", "fail", "app", "main.arc", 10, 5, "E100")
        text = str(d)
        self.assertIn("main.arc(10,5)", text)
        self.assertIn("ERROR", text)
        self.assertIn("E100", text)
        self.assertIn("fail", text)


class TestErrorReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = ErrorReporter()

    def test_initial_state(self):
        self.assertFalse(self.reporter.has_errors())
        self.assertEqual(len(self.reporter.diagnostics), 0)

    def test_report_error(self):
        self.reporter.error("test error", target="main")
        self.assertTrue(self.reporter.has_errors())
        self.assertEqual(len(self.reporter.diagnostics), 1)

    def test_report_warning(self):
        self.reporter.warning("test warning", target="lib")
        self.assertFalse(self.reporter.has_errors())
        self.assertEqual(len(self.reporter.diagnostics), 1)

    def test_report_info(self):
        self.reporter.info("info message")
        self.assertEqual(len(self.reporter.diagnostics), 1)

    def test_summary(self):
        self.reporter.error("e1")
        self.reporter.error("e2")
        self.reporter.warning("w1")
        summary = self.reporter.summary()
        self.assertIn("2 error", summary)
        self.assertIn("1 warning", summary)


if __name__ == "__main__":
    unittest.main()
