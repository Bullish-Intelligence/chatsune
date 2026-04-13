from __future__ import annotations

import os
import shlex
import sys

from .config_loader import ConfigError, format_command, load_runtime_config


SECRET_FLAGS = {"--api-key"}


def redact_command(cmd: list[str]) -> str:
    redacted: list[str] = []
    skip_next = False
    for idx, part in enumerate(cmd):
        if skip_next:
            skip_next = False
            continue
        redacted.append(part)
        if part in SECRET_FLAGS and idx + 1 < len(cmd):
            redacted.append("***REDACTED***")
            skip_next = True
    return " ".join(shlex.quote(p) for p in redacted)


def main() -> int:
    try:
        cfg = load_runtime_config()
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    cmd = cfg.build_vllm_command()
    print("Starting vLLM with effective command:", file=sys.stderr)
    print(f"  {redact_command(cmd)}", file=sys.stderr)

    env = dict(os.environ)
    env.update(cfg.environment())
    os.execvpe(cmd[0], cmd, env)


if __name__ == "__main__":
    raise SystemExit(main())
