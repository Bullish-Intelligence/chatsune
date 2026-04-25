from __future__ import annotations

import shlex


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
