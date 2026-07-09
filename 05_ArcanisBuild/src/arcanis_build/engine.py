"""ArcanisBuild Engine - core build orchestration."""

import os
import time
import json
from typing import Dict, List, Optional, Set, Callable

from arcanis_build.config import BuildConfig, TargetConfig
from arcanis_build.dependency import DependencyGraph
from arcanis_build.cache import BuildCache
from arcanis_build.parallel import ParallelExecutor
from arcanis_build.logger import BuildLogger
from arcanis_build.errors import ErrorReporter, BuildError
from arcanis_build.tester import TestRunner, TestSuite
from arcanis_build.docsgen import DocGenerator


class BuildResult:
    def __init__(self):
        self.targets_built: List[str] = []
        self.targets_cached: List[str] = []
        self.targets_failed: List[str] = []
        self.errors: List[str] = []
        self.duration: float = 0.0
        self.test_suite: Optional[TestSuite] = None
        self.docs_generated: List[str] = []

    @property
    def success(self) -> bool:
        return len(self.targets_failed) == 0

    @property
    def summary(self) -> str:
        parts = [f"Build completed in {self.duration:.2f}s"]
        if self.targets_built:
            parts.append(f"built: {len(self.targets_built)}")
        if self.targets_cached:
            parts.append(f"cached: {len(self.targets_cached)}")
        if self.targets_failed:
            parts.append(f"failed: {len(self.targets_failed)}")
        if self.test_suite:
            parts.append(f"tests: {self.test_suite.summary()}")
        return ", ".join(parts)


class BuildEngine:
    def __init__(self, config: BuildConfig):
        self.config = config
        self.graph = DependencyGraph()
        self.cache = BuildCache(config.cache_dir)
        self.logger = BuildLogger(
            log_dir=os.path.join(config.build_dir, "logs"),
            verbose=config.verbose,
        )
        self.reporter = ErrorReporter(verbose=config.verbose)
        self.executor = ParallelExecutor(
            max_workers=config.parallel_jobs if config.parallel_jobs > 0 else None
        )
        self._cancelled = False

    def _resolve_target(self, target: TargetConfig) -> TargetConfig:
        if target.output is None:
            target.output = os.path.join(
                self.config.build_dir, "bin", target.name
            )
        resolved_sources = []
        for src_pattern in target.sources:
            import glob as gmod
            matched = gmod.glob(src_pattern, recursive=True)
            if matched:
                resolved_sources.extend(matched)
            else:
                resolved_sources.append(src_pattern)
        target.sources = sorted(set(resolved_sources))
        return target

    def _build_single_target(self, target: TargetConfig) -> bool:
        target = self._resolve_target(target)

        self.logger.info(f"Building target: {target.name}", target.name)

        input_hashes = {}
        all_inputs = list(target.sources)

        for src in all_inputs:
            if os.path.exists(src):
                h = DependencyGraph.compute_file_hash(src)
                input_hashes[src] = h
                self.graph.add_node(src, "file")
                self.graph.add_edge(target.name, src)

        for dep_name in target.dependencies:
            self.graph.add_edge(target.name, dep_name)

        cached_path = self.cache.get(target.name, input_hashes)
        if cached_path:
            self.logger.info(f"Cache hit for {target.name}", target.name)
            self._restore_from_cache(target, cached_path)
            return True

        self.logger.info(f"Compiling {len(target.sources)} source(s)", target.name)
        try:
            self._compile_target(target, input_hashes)
            self.logger.info(f"Target built: {target.name}", target.name)

            if os.path.exists(target.output):
                self.cache.put(target.name, input_hashes, target.output, {
                    "timestamp": time.time(),
                })
            return True
        except BuildError as e:
            self.reporter.error(str(e), target=target.name)
            return False

    def _restore_from_cache(self, target: TargetConfig, cache_path: str):
        os.makedirs(os.path.dirname(target.output), exist_ok=True)
        import shutil
        if os.path.isdir(cache_path):
            if os.path.exists(target.output):
                shutil.rmtree(target.output)
            shutil.copytree(cache_path, target.output)
        else:
            shutil.copy2(cache_path, target.output)

    def _compile_target(self, target: TargetConfig, input_hashes: Dict[str, str]):
        output_dir = os.path.dirname(target.output)
        os.makedirs(output_dir, exist_ok=True)

        all_sources = list(target.sources)
        if not all_sources:
            raise BuildError("No source files to compile", target=target.name)

        missing = [s for s in all_sources if not os.path.exists(s)]
        if missing:
            raise BuildError(
                f"Missing source files: {', '.join(missing)}",
                target=target.name,
            )

        cmd_parts = [
            target.compiler or self.config.compiler,
            "-o", target.output,
        ]
        cmd_parts.extend(target.compiler_flags)
        cmd_parts.extend(target.includes)
        cmd_parts.extend(all_sources)

        if target.type == "library":
            cmd_parts.append("--build-lib")
        elif target.type == "executable":
            cmd_parts.append("--build-exe")
        elif target.type == "object":
            cmd_parts.append("--build-obj")

        if target.linker_flags:
            cmd_parts.append("--")
            cmd_parts.extend(target.linker_flags)

        compiled_path = target.output + ".arcanisbc"
        try:
            with open(compiled_path, "w") as f:
                f.write(f"# ArcanisBuild compiled target: {target.name}\n")
                f.write(f"# Sources: {', '.join(all_sources)}\n")
                f.write(f"# Type: {target.type}\n")
                f.write(f"# Output: {target.output}\n")
                for src in all_sources:
                    if os.path.exists(src):
                        with open(src, "r") as sf:
                            f.write(f"\n# --- {src} ---\n")
                            f.write(sf.read())
            self.logger.debug(f"Compiled {target.name} -> {compiled_path}",
                              target.name)

            import shutil
            if os.path.exists(target.output):
                os.remove(target.output)
            shutil.copy2(compiled_path, target.output)

        except IOError as e:
            raise BuildError(f"Compilation failed: {e}", target=target.name)

    def _build_all_targets(self, target_names: List[str] = None) -> BuildResult:
        result = BuildResult()
        targets_to_build = []

        if target_names:
            name_map = {t.name: t for t in self.config.targets}
            for name in target_names:
                if name in name_map:
                    targets_to_build.append(name_map[name])
                else:
                    self.reporter.error(f"Unknown target: {name}")
                    result.targets_failed.append(name)
        else:
            targets_to_build = list(self.config.targets)

        if not targets_to_build:
            self.logger.info("No targets configured")
            return result

        self.logger.start_phase("compile")

        def progress_callback(task_id, completed, total, error):
            if error:
                self.logger.error(f"Failed: {task_id} - {error}", task_id)
                result.targets_failed.append(task_id)
            else:
                self.logger.info(f"Completed: {task_id} ({completed}/{total})",
                                task_id)
                result.targets_built.append(task_id)

        for target in targets_to_build:
            self.executor.submit(
                target.name,
                self._build_single_target,
                target,
            )

        wait_result = self.executor.wait_all(progress_callback)

        for task_id, error in wait_result["errors"]:
            result.targets_failed.append(task_id)
            result.errors.append(f"{task_id}: {error}")

        self.logger.end_phase()
        return result

    def _run_tests(self) -> Optional[TestSuite]:
        if not self.config.test.enabled:
            return None

        self.logger.start_phase("test")
        self.logger.info(f"Running tests from {self.config.test.source_dir}")

        runner = TestRunner(
            source_dir=self.config.test.source_dir,
            pattern=self.config.test.pattern,
            timeout=self.config.test.timeout,
        )

        def on_result(result):
            self.logger.info(
                f"{result.status}: {result.name} ({result.duration:.2f}s)",
                result.name,
            )

        suite = runner.run_all(
            parallel=True,
            progress_callback=on_result,
        )

        self.logger.info(f"Tests: {suite.summary()}")
        self.logger.end_phase()
        return suite

    def _generate_docs(self) -> List[str]:
        if not self.config.docs.enabled:
            return []

        self.logger.start_phase("docs")
        self.logger.info(f"Generating docs from {self.config.docs.source_dir}")

        generator = DocGenerator(
            source_dir=self.config.docs.source_dir,
            output_dir=self.config.docs.output_dir,
            fmt=self.config.docs.format,
        )

        output_files = generator.generate()
        for f in output_files:
            self.logger.info(f"Generated: {f}")

        self.logger.end_phase()
        return output_files

    def build(self, targets: List[str] = None,
              run_tests: bool = True,
              gen_docs: bool = True) -> BuildResult:
        start_time = time.time()
        result = BuildResult()

        self.logger.open_log()
        self.logger.info(f"ArcanisBuild v{self.__class__.__module__.split('.')[0]}")
        self.logger.info(f"Project: {self.config.project_name} v{self.config.version}")
        self.logger.info(f"Targets: {len(self.config.targets)}, "
                        f"Workers: {self.executor.max_workers}")

        build_result = self._build_all_targets(targets)
        result.targets_built = build_result.targets_built
        result.targets_cached = build_result.targets_cached
        result.targets_failed = build_result.targets_failed
        result.errors = build_result.errors

        if run_tests:
            test_suite = self._run_tests()
            result.test_suite = test_suite

        if gen_docs and not self.reporter.has_errors():
            docs = self._generate_docs()
            result.docs_generated = docs

        result.duration = time.time() - start_time
        self.logger.info(result.summary)
        self.reporter.print_summary()
        self.logger.close_log()

        return result

    def clean(self):
        import shutil

        self.logger.open_log()
        self.logger.info(f"Cleaning build artifacts")
        self.logger.close_log()

        if os.path.exists(self.config.build_dir):
            shutil.rmtree(self.config.build_dir, ignore_errors=True)
            self.logger.info(f"Removed: {self.config.build_dir}")

        if os.path.exists(self.config.cache_dir):
            self.cache.clear()
            self.logger.info(f"Cleared: {self.config.cache_dir}")

        self.logger.close_log()

    def cancel(self):
        self._cancelled = True
        self.executor.shutdown(wait=False)
