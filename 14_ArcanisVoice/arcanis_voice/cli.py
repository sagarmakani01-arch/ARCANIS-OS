"""Command-line entry points for ArcanisVoice."""
from __future__ import annotations

import argparse
import sys
import threading

from . import test_tools
from .api import create_app
from .config import load_config
from .pipeline import VoicePipeline
from .utils import setup_logging, logger


def _build_pipeline(cfg) -> VoicePipeline:
    return VoicePipeline(cfg)


def cmd_run(args, cfg) -> None:
    pipe = _build_pipeline(cfg)
    pipe.run()


def cmd_api(args, cfg) -> None:
    import uvicorn
    pipe = _build_pipeline(cfg)
    t = threading.Thread(target=pipe.run, daemon=True)
    t.start()
    app = create_app(pipe)
    uvicorn.run(app, host=cfg.api.host, port=cfg.api.port, log_level="info")


def cmd_test(args, cfg) -> None:
    which = args.which
    if which == "mic":
        test_tools.test_microphone(cfg)
    elif which == "noise":
        test_tools.test_noise_filter(cfg)
    elif which == "wake":
        test_tools.test_wake_word(cfg)
    elif which == "latency":
        test_tools.bench_latency(cfg)
    elif which == "selftest":
        test_tools.run_self_test(cfg)
    else:
        print("unknown test:", which)


def main(argv=None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(prog="arcanis-voice", description="ArcanisVoice CLI")
    parser.add_argument("-c", "--config", default=None, help="path to config.yaml")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run", help="run the voice pipeline (mic -> speak)")
    sub.add_parser("api", help="run pipeline + REST/WS API server")

    p_test = sub.add_parser("test", help="testing tools")
    p_test.add_argument("which", choices=["mic", "noise", "wake", "latency", "selftest"])

    args = parser.parse_args(argv)
    cfg = load_config(args.config)

    if args.command == "run":
        cmd_run(args, cfg)
    elif args.command == "api":
        cmd_api(args, cfg)
    elif args.command == "test":
        cmd_test(args, cfg)
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
