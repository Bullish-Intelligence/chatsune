from __future__ import annotations

from pathlib import Path


def test_compose_services_do_not_use_env_file() -> None:
    compose = Path("compose.yaml").read_text(encoding="utf-8")
    profiles = Path("compose.profiles.yaml").read_text(encoding="utf-8")
    assert "env_file:" not in compose
    assert "env_file:" not in profiles


def test_env_example_uses_file_based_secret_vars() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")
    lines = [line.strip() for line in env_example.splitlines() if line.strip() and not line.strip().startswith("#")]

    assert any(line.startswith("HF_TOKEN_FILE=") for line in lines)
    assert any(line.startswith("VLLM_API_KEY_FILE=") for line in lines)
    assert any(line.startswith("TS_AUTHKEY_FILE=") for line in lines)
    assert not any(line.startswith("HF_TOKEN=") for line in lines)
    assert not any(line.startswith("VLLM_API_KEY=") for line in lines)
    assert not any(line.startswith("TS_AUTHKEY=") for line in lines)
