from __future__ import annotations

import os
import sys

from .config_loader import ConfigError, load_runtime_config
from .redaction import redact_command


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
