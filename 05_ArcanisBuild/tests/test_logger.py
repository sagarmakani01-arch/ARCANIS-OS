"""Tests for build logger."""

import os
import tempfile
import unittest
import json

from arcanis_build.logger import BuildLogger, LogEntry


class TestLogEntry(unittest.TestCase):
    def test_entry_creation(self):
        entry = LogEntry("info", "build started", "main")
        self.assertEqual(entry.level, "info")
        self.assertEqual(entry.message, "build started")
        self.assertEqual(entry.target, "main")

    def test_entry_to_dict(self):
        entry = LogEntry("error", "compilation failed", "app", "compile")
        data = entry.to_dict()
        self.assertIn("timestamp", data)
        self.assertEqual(data["level"], "error")
        self.assertEqual(data["phase"], "compile")

    def test_format_console(self):
        entry = LogEntry("warn", "deprecated API", "lib")
        formatted = entry.format_console()
        self.assertIn("WARN", formatted)
        self.assertIn("[lib]", formatted)
        self.assertIn("deprecated API", formatted)


class TestBuildLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logger_creation(self):
        logger = BuildLogger(log_dir=self.log_dir)
        self.assertEqual(logger.log_dir, self.log_dir)
        self.assertEqual(len(logger._entries), 0)

    def test_logging(self):
        logger = BuildLogger(log_dir=self.log_dir)
        logger.info("message1")
        logger.warn("message2")
        logger.error("message3")
        self.assertEqual(len(logger._entries), 3)

    def test_log_file_output(self):
        logger = BuildLogger(log_dir=self.log_dir)
        path = logger.open_log("test-build")
        self.assertTrue(os.path.exists(path))

        logger.info("test message")
        logger.close_log()

        with open(path, "r") as f:
            lines = f.readlines()

        entries = [json.loads(l.strip()) for l in lines]
        test_entry = next(e for e in entries if e["message"] == "test message")
        self.assertEqual(test_entry["level"], "info")

    def test_phase_tracking(self):
        logger = BuildLogger(log_dir=self.log_dir)
        logger.start_phase("compile")
        self.assertEqual(logger._current_phase, "compile")
        logger.info("compiling...")
        logger.end_phase()
        self.assertIsNone(logger._current_phase)

    def test_summary(self):
        logger = BuildLogger(log_dir=self.log_dir)
        logger.info("i1")
        logger.error("e1")
        logger.error("e2")
        logger.warn("w1")
        summary = logger.summary()
        self.assertEqual(summary["total_entries"], 4)
        self.assertEqual(summary["errors"], 2)
        self.assertEqual(summary["warnings"], 1)
        self.assertEqual(summary["info"], 1)

    def test_export_json(self):
        logger = BuildLogger(log_dir=self.log_dir)
        logger.info("test")
        exported = logger.export("json")
        data = json.loads(exported)
        self.assertEqual(len(data), 1)

    def test_export_text(self):
        logger = BuildLogger(log_dir=self.log_dir)
        logger.info("test")
        exported = logger.export("text")
        self.assertIn("test", exported)


if __name__ == "__main__":
    unittest.main()
