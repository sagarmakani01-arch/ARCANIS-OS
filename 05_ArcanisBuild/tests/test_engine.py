"""Tests for build engine."""

import os
import tempfile
import unittest
from unittest.mock import patch

from arcanis_build.config import BuildConfig, TargetConfig, TestConfig, DocConfig
from arcanis_build.engine import BuildEngine, BuildResult


class TestBuildEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

        self.config = BuildConfig(
            project_name="test-project",
            build_dir=os.path.join(self.temp_dir, "build"),
            cache_dir=os.path.join(self.temp_dir, ".cache"),
            targets=[
                TargetConfig(
                    name="test-target",
                    type="executable",
                    sources=[os.path.join(self.temp_dir, "src", "main.arc")],
                )
            ],
            test=TestConfig(enabled=False),
            docs=DocConfig(enabled=False),
        )

        os.makedirs(os.path.join(self.temp_dir, "src"))
        with open(os.path.join(self.temp_dir, "src", "main.arc"), "w") as f:
            f.write("fn main() { print('hello'); }")

        self.engine = BuildEngine(self.config)

    def tearDown(self):
        import shutil
        os.chdir(os.path.dirname(self.temp_dir))
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_engine_initialization(self):
        self.assertEqual(self.engine.config.project_name, "test-project")
        self.assertIsNotNone(self.engine.graph)
        self.assertIsNotNone(self.engine.cache)
        self.assertIsNotNone(self.engine.logger)

    def test_build_result_defaults(self):
        result = BuildResult()
        self.assertTrue(result.success)
        self.assertEqual(len(result.targets_failed), 0)
        self.assertEqual(len(result.targets_built), 0)

    def test_build_result_with_failures(self):
        result = BuildResult()
        result.targets_failed.append("bad-target")
        self.assertFalse(result.success)

    @patch.object(BuildEngine, '_compile_target')
    def test_build_single_target_success(self, mock_compile):
        target = self.config.targets[0]
        mock_compile.return_value = None

        result = self.engine.build(targets=["test-target"], run_tests=False, gen_docs=False)
        self.assertTrue(result.success)

    def test_build_with_no_targets(self):
        config = BuildConfig(project_name="empty")
        engine = BuildEngine(config)
        result = engine.build(run_tests=False, gen_docs=False)
        self.assertTrue(result.success)

    def test_clean(self):
        os.makedirs(os.path.join(self.temp_dir, "build"))
        self.engine.clean()
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, "build")))
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, ".cache")))


if __name__ == "__main__":
    unittest.main()
