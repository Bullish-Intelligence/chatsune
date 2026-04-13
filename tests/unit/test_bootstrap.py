from __future__ import annotations

from chatsune.bootstrap import redact_command


def test_redact_command_hides_api_key_value() -> None:
    cmd = ["vllm", "serve", "m", "--api-key", "super-secret", "--host", "0.0.0.0"]
    rendered = redact_command(cmd)
    assert "super-secret" not in rendered
    assert "***REDACTED***" in rendered
