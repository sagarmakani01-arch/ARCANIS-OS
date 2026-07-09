"""CLI entry point for ArcanisInference."""

import argparse
import json
import sys
from arcanis_inference.engine import InferenceEngine
from arcanis_inference.config import InferenceConfig


def main():
    parser = argparse.ArgumentParser(
        description="ArcanisInference - On-device AI inference engine"
    )
    sub = parser.add_subparsers(dest="command")

    status_p = sub.add_parser("status", help="Show engine status")
    status_p.add_argument("--model", type=str, help="Path to model file")

    classify_p = sub.add_parser("classify", help="Classify intent")
    classify_p.add_argument("text", type=str, help="Text to classify")

    generate_p = sub.add_parser("generate", help="Generate text")
    generate_p.add_argument("prompt", type=str, help="Prompt text")
    generate_p.add_argument("--context", type=str, help="Context string")
    generate_p.add_argument("--max-tokens", type=int, default=256)
    generate_p.add_argument("--model", type=str, required=True)

    plan_p = sub.add_parser("plan", help="Generate a task plan")
    plan_p.add_argument("task", type=str, help="Task description")
    plan_p.add_argument("--model", type=str, required=True)

    args = parser.parse_args()

    config = InferenceConfig()
    engine = InferenceEngine(config)
    engine.initialize()

    if args.command == "status":
        info = engine.get_status()
        print(json.dumps(info, indent=2))

    elif args.command == "classify":
        result = engine.classify_intent(args.text)
        print(json.dumps(result, indent=2))

    elif args.command == "generate":
        engine.load_model(args.model)
        response = engine.generate(args.prompt, context=args.context)
        print(response)
        engine.shutdown()

    elif args.command == "plan":
        engine.load_model(args.model)
        plan = engine.generate_plan(args.task)
        print(plan)
        engine.shutdown()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
