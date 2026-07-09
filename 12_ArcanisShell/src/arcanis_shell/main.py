"""ArcanisShell — CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ShellConfig
from .engine import repl
from .errors import PlanRejectedError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="arcanisshell", description="ArcanisShell — AI-native shell."
    )
    parser.add_argument("-c", "--command", help="Execute a single command and exit.")
    parser.add_argument("--config", type=Path, help="Path to a TOML config file.")
    parser.add_argument(
        "--sandbox-root", type=Path, help="Restrict filesystem access to this directory."
    )
    parser.add_argument("--version", action="version", version="arcanisshell 0.1.0")
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Auto-approve AI plans (use with care; respects permission policy).",
    )
    args = parser.parse_args(argv)

    config = ShellConfig.from_file(args.config) if args.config else ShellConfig.default()
    if args.sandbox_root:
        config.sandbox_root = args.sandbox_root.resolve()

    if args.command:
        from .engine import ShellEngine

        try:
            engine = ShellEngine(config=config)
            if args.yes:
                engine.approval_fn = lambda plan: True
            result = engine.execute(args.command)
        except PlanRejectedError:
            print("plan rejected; no actions taken.", file=sys.stderr)
            return 130
        if result.stdout:
            print(result.stdout)
        if not result.success and result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.exit_code

    repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
