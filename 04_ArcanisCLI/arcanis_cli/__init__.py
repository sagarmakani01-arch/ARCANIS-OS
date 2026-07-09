"""Unified Arcanis CLI — single entry point for all ecosystem commands."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence


def cmd_version(args: argparse.Namespace) -> int:
    print("Arcanis v0.6.0")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    print("Arcanis Ecosystem Status")
    print("========================")
    modules = [
        ("Kernel", "18_ArcanisKernel"),
        ("Shell", "12_ArcanisShell"),
        ("Inference", "60_ArcanisInference"),
        ("Security", "50_ArcanisSecurity"),
        ("SemanticFS", "41_ArcanisSemanticFS"),
        ("HAL", "90_ArcanisHAL"),
        ("AIScheduler", "22_ArcanisAIScheduler"),
        ("PackageManager", "06_ArcanisPackageManager"),
        ("Runtime", "30_ArcanisRuntime"),
        ("DevAPI", "33_ArcanisDevAPI"),
        ("DriverSynth", "91_ArcanisDriverSynth"),
        ("Federated", "62_ArcanisFederated"),
        ("AgentSDK", "10_ArcanisAgentSDK"),
        ("Experiments", "27_ArcanisExperiments"),
        ("Research", "28_ArcanisResearch"),
        ("Assets", "29_ArcanisAssets"),
    ]
    for name, path in modules:
        print(f"  [{name:16s}] {path}")
    return 0


def cmd_kernel(args: argparse.Namespace) -> int:
    print("Kernel subsystem status")
    return 0


def cmd_shell(args: argparse.Namespace) -> int:
    print("Shell subsystem status")
    return 0


def cmd_inference(args: argparse.Namespace) -> int:
    print("Inference engine status")
    return 0


def cmd_security(args: argparse.Namespace) -> int:
    print("Security subsystem status")
    return 0


def cmd_experiment(args: argparse.Namespace) -> int:
    if args.exp_action == "list":
        print("No active experiments")
    elif args.exp_action == "run":
        print(f"Would run experiment: {args.exp_id}")
    else:
        print("Usage: arcanis experiment [list|run]")
    return 0


def cmd_research(args: argparse.Namespace) -> int:
    if args.research_action == "list":
        print("No research topics")
    elif args.research_action == "add":
        print(f"Would add topic: {args.title}")
    else:
        print("Usage: arcanis research [list|add]")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arcanis",
        description="Arcanis — AI-native Operating System CLI",
    )
    parser.add_argument("--version", action="version", version="Arcanis 0.6.0")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Show version")
    sub.add_parser("status", help="Show ecosystem status")
    sub.add_parser("kernel", help="Kernel subsystem")
    sub.add_parser("shell", help="Shell subsystem")
    sub.add_parser("inference", help="Inference engine")
    sub.add_parser("security", help="Security subsystem")

    exp = sub.add_parser("experiment", help="Experiment runner")
    exp.add_argument("exp_action", nargs="?", default="list", choices=["list", "run"])
    exp.add_argument("exp_id", nargs="?", default="")

    res = sub.add_parser("research", help="Research tracker")
    res.add_argument("research_action", nargs="?", default="list", choices=["list", "add"])
    res.add_argument("title", nargs="?", default="")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "version": cmd_version,
        "status": cmd_status,
        "kernel": cmd_kernel,
        "shell": cmd_shell,
        "inference": cmd_inference,
        "security": cmd_security,
        "experiment": cmd_experiment,
        "research": cmd_research,
    }
    handler = dispatch.get(args.command)
    if handler:
        return handler(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
