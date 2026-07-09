"""Build configuration parsing - supports arcanis.json and build.yaml formats."""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TargetConfig:
    name: str
    type: str = "executable"
    sources: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    compiler: str = "arcanisc"
    compiler_flags: List[str] = field(default_factory=list)
    linker_flags: List[str] = field(default_factory=list)
    output: Optional[str] = None


@dataclass
class TestConfig:
    enabled: bool = True
    framework: str = "arcanist"
    source_dir: str = "tests"
    pattern: str = "test_*.arc"
    timeout: int = 30


@dataclass
class DocConfig:
    enabled: bool = True
    output_dir: str = "docs/build"
    format: str = "markdown"
    source_dir: str = "src"


@dataclass
class BuildConfig:
    project_name: str = "arcanis-project"
    version: str = "0.1.0"
    targets: List[TargetConfig] = field(default_factory=list)
    test: TestConfig = field(default_factory=TestConfig)
    docs: DocConfig = field(default_factory=DocConfig)
    build_dir: str = "build"
    cache_dir: str = ".arcanis-cache"
    parallel_jobs: int = 0
    verbose: bool = False
    compiler: str = "arcanisc"

    @classmethod
    def default(cls, project_name: str = "arcanis-project") -> "BuildConfig":
        return cls(project_name=project_name)


def load_config(path: str) -> BuildConfig:
    if not os.path.exists(path):
        return BuildConfig.default(os.path.basename(os.getcwd()))

    ext = os.path.splitext(path)[1].lower()
    parsers = {".json": _load_json, ".yaml": _load_yaml, ".yml": _load_yaml}

    parser = parsers.get(ext)
    if not parser:
        raise ValueError(f"Unsupported config format: {ext}")

    data = parser(path)
    return _parse_config(data)


def _load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def _load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        text = f.read()

    try:
        import yaml as _yaml
        return _yaml.safe_load(text)
    except ImportError:
        return _yaml_simple_parse(text)


def _yaml_simple_parse(text: str) -> dict:
    result = {}
    current_key = None
    current_list = None
    in_list = False

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if ":" in stripped and not stripped.startswith("-"):
            parts = stripped.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip()
            current_key = key
            in_list = False

            if value == "" or value == "[]":
                result[key] = [] if value == "[]" else {}
                current_list = []
            elif value.startswith('"') and value.endswith('"'):
                result[key] = value[1:-1]
            elif value.isdigit():
                result[key] = int(value)
            elif value == "true":
                result[key] = True
            elif value == "false":
                result[key] = False
            else:
                result[key] = value

        elif stripped.startswith("- ") and current_key:
            item = stripped[2:]
            if item.startswith('"') and item.endswith('"'):
                item = item[1:-1]
            if current_key not in result or not isinstance(result.get(current_key), list):
                result[current_key] = []
            result[current_key].append(item)

    return result


def _parse_config(data: dict) -> BuildConfig:
    config = BuildConfig()
    config.project_name = data.get("project_name", config.project_name)
    config.version = data.get("version", config.version)
    config.build_dir = data.get("build_dir", config.build_dir)
    config.cache_dir = data.get("cache_dir", config.cache_dir)
    config.parallel_jobs = data.get("parallel_jobs", config.parallel_jobs)
    config.verbose = data.get("verbose", config.verbose)
    config.compiler = data.get("compiler", config.compiler)

    targets_data = data.get("targets", [])
    if isinstance(targets_data, list):
        for t in targets_data:
            config.targets.append(TargetConfig(**t))
    elif isinstance(targets_data, dict):
        for name, t in targets_data.items():
            config.targets.append(TargetConfig(name=name, **t))

    test_data = data.get("test", {})
    if test_data:
        config.test = TestConfig(**test_data)

    docs_data = data.get("docs", {})
    if docs_data:
        config.docs = DocConfig(**docs_data)

    return config
