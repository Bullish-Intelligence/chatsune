from __future__ import annotations

from pathlib import Path


def test_compose_services_do_not_use_env_file() -> None:
    compose = Path("compose.yaml").read_text(encoding="utf-8")
    profiles = Path("compose.profiles.yaml").read_text(encoding="utf-8")
    auth = Path("compose.auth.yaml").read_text(encoding="utf-8")
    assert "env_file:" not in compose
    assert "env_file:" not in profiles
    assert "env_file:" not in auth


def test_baseline_compose_does_not_require_vllm_api_key_file() -> None:
    compose = Path("compose.yaml").read_text(encoding="utf-8")
    assert "VLLM_API_KEY_FILE=" not in compose
    assert "./.secrets/vllm_api_key:/run/secrets/vllm_api_key:ro" not in compose


def test_auth_overlay_adds_vllm_api_key_file_wiring() -> None:
    auth = Path("compose.auth.yaml").read_text(encoding="utf-8")
    assert "VLLM_API_KEY_FILE=" in auth
    assert "./.secrets/vllm_api_key:/run/secrets/vllm_api_key:ro" in auth


def test_env_example_uses_file_based_secret_vars() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")
    lines = [line.strip() for line in env_example.splitlines() if line.strip() and not line.strip().startswith("#")]

    assert any(line.startswith("HF_TOKEN_FILE=") for line in lines)
    assert any(line.startswith("VLLM_API_KEY_FILE=") for line in lines)
    assert any(line.startswith("TS_AUTHKEY_FILE=") for line in lines)
    assert not any(line.startswith("HF_TOKEN=") for line in lines)
    assert not any(line.startswith("VLLM_API_KEY=") for line in lines)
    assert not any(line.startswith("TS_AUTHKEY=") for line in lines)


def test_runtime_images_are_pinned_and_not_floating_tags() -> None:
    compose = Path("compose.yaml").read_text(encoding="utf-8")
    profiles = Path("compose.profiles.yaml").read_text(encoding="utf-8")
    vllm_dockerfile = Path("images/vllm/Dockerfile").read_text(encoding="utf-8")
    tailscale_dockerfile = Path("images/tailscale/Dockerfile").read_text(encoding="utf-8")

    assert ":stable" not in compose
    assert ":stable" not in profiles
    assert ":latest" not in vllm_dockerfile
    assert ":stable" not in tailscale_dockerfile

    assert "tailscale/tailscale:${TAILSCALE_IMAGE_TAG:-" in compose
    assert "tailscale/tailscale:${TAILSCALE_IMAGE_TAG:-" in profiles
    assert "FROM vllm/vllm-openai:v" in vllm_dockerfile
    assert "FROM tailscale/tailscale:v" in tailscale_dockerfile
