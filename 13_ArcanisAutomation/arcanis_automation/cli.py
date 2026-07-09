"""Command-line interface for ArcanisAutomation."""

from __future__ import annotations

import argparse
import json
import sys

from arcanis_automation.api.python_api import Automation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arcanis-automation", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List workflows")

    p_create = sub.add_parser("create", help="Create from JSON file")
    p_create.add_argument("file", help="Path to workflow JSON")

    p_run = sub.add_parser("run", help="Trigger a workflow")
    p_run.add_argument("id")
    p_run.add_argument("--context", default="{}")

    p_gen = sub.add_parser("generate", help="Generate workflow from description")
    p_gen.add_argument("description")

    p_opt = sub.add_parser("optimize", help="Optimize a workflow")
    p_opt.add_argument("id")

    p_fail = sub.add_parser("failures", help="Detect failures for last run")
    p_fail.add_argument("id")

    sub.add_parser("serve", help="Start REST API server")

    args = parser.parse_args(argv)

    auto = Automation()

    if args.cmd == "list":
        for wf in auto.list():
            print(f"{wf.id}  {wf.name}  [{wf.status.value}]")
    elif args.cmd == "create":
        with open(args.file, "r", encoding="utf-8") as fh:
            wf = auto.engine.create_workflow(json.load(fh))
        print(f"created {wf.id}")
    elif args.cmd == "run":
        results = auto.run(args.id, json.loads(args.context))
        print(json.dumps([r.to_dict() for r in results], indent=2))
    elif args.cmd == "generate":
        wid = auto.generate(args.description)
        print(f"generated {wid}")
    elif args.cmd == "optimize":
        wf = auto.engine.optimize_workflow(args.id)
        print(json.dumps(wf.to_dict(), indent=2))
    elif args.cmd == "failures":
        print(json.dumps(auto.engine.detect_failures(args.id), indent=2))
    elif args.cmd == "serve":
        from arcanis_automation.api.rest_api import run_server
        run_server()
    return 0


if __name__ == "__main__":
    sys.exit(main())
