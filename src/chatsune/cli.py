from __future__ import annotations

import argparse
import json
import os
import sys

from .config_loader import ConfigError, format_command, load_runtime_config
from .diagnostics import check_health


def cmd_validate_env(_: argparse.Namespace) -> int:
    load_runtime_config()
    print("Configuration is valid.")
    return 0


def cmd_print_config(args: argparse.Namespace) -> int:
    cfg = load_runtime_config()
    print(json.dumps(cfg.data, indent=2, sort_keys=True))
    if args.show_command:
        cmd = cfg.build_vllm_command()
        print("\nCommand:")
        print(format_command(cmd))
    return 0


def cmd_smoke_test(args: argparse.Namespace) -> int:
    ok, detail = check_health(args.server_url, timeout=args.timeout)
    print(detail)
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chatsune", description="Chatsune helper CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-env", help="Validate runtime config and secret wiring")
    validate.set_defaults(func=cmd_validate_env)

    show = sub.add_parser("print-config", help="Print effective runtime config")
    show.add_argument("--show-command", action="store_true", help="Show rendered vLLM command")
    show.set_defaults(func=cmd_print_config)

    smoke = sub.add_parser("smoke-test", help="Run lightweight health check")
    smoke.add_argument("--server-url", default=os.environ.get("SERVER_URL", "http://127.0.0.1:8000"))
    smoke.add_argument("--timeout", type=int, default=5)
    smoke.set_defaults(func=cmd_smoke_test)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
