"""ArcanisBuild CLI - command-line interface."""

import argparse
import os
import sys
from typing import List

from arcanis_build.config import load_config
from arcanis_build.engine import BuildEngine
from arcanis_build.errors import BuildError


def find_config() -> str:
    candidates = ["arcanis.json", "build.yaml", "build.yml"]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "arcanis.json"


def cmd_build(args: argparse.Namespace) -> int:
    config_path = args.config or find_config()
    if not os.path.exists(config_path):
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 1

    config = load_config(config_path)

    if args.verbose:
        config.verbose = True
    if args.jobs:
        config.parallel_jobs = args.jobs

    engine = BuildEngine(config)

    try:
        result = engine.build(
            targets=args.targets,
            run_tests=not args.no_test,
            gen_docs=not args.no_docs,
        )
        return 0 if result.success else 1
    except BuildError as e:
        print(f"Build error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        engine.cancel()
        print("\nBuild cancelled")
        return 130


def cmd_clean(args: argparse.Namespace) -> int:
    config_path = args.config or find_config()
    config = load_config(config_path) if os.path.exists(config_path) else None

    if config is None:
        import shutil
        for d in ["build", ".arcanis-cache"]:
            if os.path.exists(d):
                shutil.rmtree(d)
                print(f"Removed: {d}")
        return 0

    engine = BuildEngine(config)
    engine.clean()
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    from arcanis_build.tester import TestRunner

    runner = TestRunner(
        source_dir=args.source_dir,
        pattern=args.pattern,
        timeout=args.timeout,
    )

    def on_result(result):
        status = "\u2713" if result.passed else "\u2717"
        print(f"  {status} {result.name} ({result.duration:.2f}s)")
        if not result.passed and result.error:
            print(f"    Error: {result.error}")

    suite = runner.run_all(parallel=not args.serial, progress_callback=on_result)
    print(f"\nResults: {suite.summary()}")

    return 0 if suite.failed == 0 else 1


def cmd_docs(args: argparse.Namespace) -> int:
    from arcanis_build.docsgen import DocGenerator

    generator = DocGenerator(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        fmt=args.format,
    )

    files = generator.generate()
    for f in files:
        print(f"Generated: {f}")
    print(f"\n{len(files)} file(s) generated")

    return 0


def cmd_init(args: argparse.Namespace) -> int:
    import json

    config = {
        "project_name": args.name or os.path.basename(os.getcwd()),
        "version": "0.1.0",
        "compiler": "arcanisc",
        "build_dir": "build",
        "cache_dir": ".arcanis-cache",
        "parallel_jobs": 0,
        "verbose": False,
        "targets": [
            {
                "name": "main",
                "type": "executable",
                "sources": ["src/**/*.arc"],
                "dependencies": [],
                "compiler_flags": [],
            }
        ],
        "test": {
            "enabled": True,
            "framework": "arcanist",
            "source_dir": "tests",
            "pattern": "test_*.arc",
            "timeout": 30,
        },
        "docs": {
            "enabled": True,
            "output_dir": "docs/build",
            "format": "markdown",
            "source_dir": "src",
        },
    }

    output = args.config or "arcanis.json"
    with open(output, "w") as f:
        json.dump(config, f, indent=2)

    os.makedirs("src", exist_ok=True)
    os.makedirs("tests", exist_ok=True)

    if args.create_example:
        example_dir = "src"
        example_file = os.path.join(example_dir, "main.arc")
        if not os.path.exists(example_file):
            with open(example_file, "w") as f:
                f.write("""/// Entry point for the Arcanis application
fn main() {
    // Application logic here
    print("Hello from Arcanis!");
}
""")

    print(f"Initialized ArcanisBuild project: {config['project_name']}")
    print(f"Config: {output}")
    return 0


def cmd_cache(args: argparse.Namespace) -> int:
    config_path = args.config or find_config()
    config = load_config(config_path) if os.path.exists(config_path) else None

    from arcanis_build.cache import BuildCache
    cache = BuildCache(config.cache_dir if config else ".arcanis-cache")

    if args.clear:
        cache.clear()
        print("Cache cleared")
        return 0

    stats = cache.stats()
    print(f"Cache directory: {stats['cache_dir']}")
    print(f"Entries: {stats['entries']}")
    print(f"Size: {stats['size_bytes']} bytes")
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    from arcanis_build import __version__
    print(f"ArcanisBuild v{__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arcanis-build",
        description="ArcanisBuild - Modern build automation system",
    )
    parser.add_argument("--version", action="store_true", help="Show version")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    build_parser = subparsers.add_parser("build", help="Build the project")
    build_parser.add_argument("-c", "--config", help="Path to build config")
    build_parser.add_argument("-j", "--jobs", type=int, help="Parallel jobs")
    build_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    build_parser.add_argument("--no-test", action="store_true", help="Skip tests")
    build_parser.add_argument("--no-docs", action="store_true", help="Skip docs")
    build_parser.add_argument("targets", nargs="*", help="Specific targets to build")

    clean_parser = subparsers.add_parser("clean", help="Clean build artifacts")
    clean_parser.add_argument("-c", "--config", help="Path to build config")

    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--source-dir", default="tests", help="Test source directory")
    test_parser.add_argument("--pattern", default="test_*.arc", help="Test file pattern")
    test_parser.add_argument("--timeout", type=int, default=30, help="Test timeout (seconds)")
    test_parser.add_argument("--serial", action="store_true", help="Run tests sequentially")

    docs_parser = subparsers.add_parser("docs", help="Generate documentation")
    docs_parser.add_argument("--source-dir", default="src", help="Source directory")
    docs_parser.add_argument("--output-dir", default="docs/build", help="Output directory")
    docs_parser.add_argument("--format", default="markdown", choices=["markdown", "json"],
                            help="Output format")

    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.add_argument("-n", "--name", help="Project name")
    init_parser.add_argument("-c", "--config", help="Config file to create")
    init_parser.add_argument("--create-example", action="store_true",
                            help="Create example source file")

    cache_parser = subparsers.add_parser("cache", help="Manage build cache")
    cache_parser.add_argument("-c", "--config", help="Path to build config")
    cache_parser.add_argument("--clear", action="store_true", help="Clear the cache")

    return parser


def main(argv: List[str] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if hasattr(args, 'version') and args.version:
        return cmd_version(args)

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "build": cmd_build,
        "clean": cmd_clean,
        "test": cmd_test,
        "docs": cmd_docs,
        "init": cmd_init,
        "cache": cmd_cache,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
