"""Tests for configuration parsing."""

import json
import os
import tempfile
import unittest

from arcanis_build.config import load_config, BuildConfig, TargetConfig


class TestConfigLoading(unittest.TestCase):
    def test_default_config(self):
        config = load_config("nonexistent.json")
        self.assertIsInstance(config, BuildConfig)
        self.assertEqual(config.project_name, os.path.basename(os.getcwd()))

    def test_load_json_config(self):
        data = {
            "project_name": "test-project",
            "version": "1.0.0",
            "build_dir": "out",
            "targets": [
                {"name": "app", "type": "executable", "sources": ["src/main.arc"]}
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            config_path = f.name

        try:
            config = load_config(config_path)
            self.assertEqual(config.project_name, "test-project")
            self.assertEqual(config.version, "1.0.0")
            self.assertEqual(config.build_dir, "out")
            self.assertEqual(len(config.targets), 1)
            self.assertEqual(config.targets[0].name, "app")
        finally:
            os.unlink(config_path)

    def test_target_config_defaults(self):
        target = TargetConfig(name="lib")
        self.assertEqual(target.type, "executable")
        self.assertEqual(target.compiler, "arcanisc")
        self.assertEqual(target.sources, [])

    def test_config_with_test_settings(self):
        data = {
            "project_name": "p",
            "test": {"enabled": True, "timeout": 60},
            "docs": {"enabled": False},
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            config_path = f.name

        try:
            config = load_config(config_path)
            self.assertTrue(config.test.enabled)
            self.assertEqual(config.test.timeout, 60)
            self.assertFalse(config.docs.enabled)
        finally:
            os.unlink(config_path)


class TestYamlConfig(unittest.TestCase):
    def test_load_yaml_config(self):
        yaml_content = """
project_name: my-app
version: "2.0.0"
targets:
  - name: server
    type: executable
    sources:
      - src/server.arc
      - src/utils.arc
test:
  enabled: true
  timeout: 45
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            config_path = f.name

        try:
            config = load_config(config_path)
            self.assertEqual(config.project_name, "my-app")
            self.assertEqual(config.version, "2.0.0")
            self.assertEqual(len(config.targets), 1)
            self.assertEqual(config.targets[0].name, "server")
            self.assertEqual(len(config.targets[0].sources), 2)
            self.assertEqual(config.test.timeout, 45)
        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    unittest.main()
