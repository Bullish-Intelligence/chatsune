from __future__ import annotations

from pathlib import Path

import pytest

from chatsune.config_loader import ConfigError, load_runtime_config


def _write_yaml(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _base_yaml() -> str:
    return """
vllm:
  model: test/model
  host: 0.0.0.0
  port: 8000
  trust_remote_code: false
  disable_log_requests: false
  enable_auto_tool_choice: false
  enable_lora: false
  lora_modules: []
  extra_args: []
paths:
  download_dir: /models/cache
  adapter_dir: /models/adapters
health:
  check_path: /v1/models
""".strip()


def test_rejects_unknown_top_level_key(tmp_path: Path) -> None:
    config_path = tmp_path / "server-config.yaml"
    _write_yaml(config_path, _base_yaml() + "\nunknown: true\n")

    with pytest.raises(ConfigError, match="unknown top-level keys"):
        load_runtime_config(env={"CONFIG_PATH": str(config_path)})


def test_secret_file_resolution(tmp_path: Path) -> None:
    config_path = tmp_path / "server-config.yaml"
    _write_yaml(config_path, _base_yaml())

    token_path = tmp_path / "hf_token"
    token_path.write_text("secret-token\n", encoding="utf-8")
    token_path.chmod(0o600)

    cfg = load_runtime_config(
        env={
            "CONFIG_PATH": str(config_path),
            "HF_TOKEN_FILE": str(token_path),
        }
    )

    assert cfg.hf_token == "secret-token"


def test_rejects_env_secret_when_file_exists_without_override(tmp_path: Path) -> None:
    config_path = tmp_path / "server-config.yaml"
    _write_yaml(config_path, _base_yaml())

    token_path = tmp_path / "hf_token"
    token_path.write_text("secret-token\n", encoding="utf-8")
    token_path.chmod(0o600)

    with pytest.raises(ConfigError, match="both HF_TOKEN and HF_TOKEN_FILE"):
        load_runtime_config(
            env={
                "CONFIG_PATH": str(config_path),
                "HF_TOKEN": "raw-secret",
                "HF_TOKEN_FILE": str(token_path),
                "ALLOW_INSECURE_ENV_SECRETS": "false",
            }
        )


def test_build_vllm_command_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "server-config.yaml"
    _write_yaml(
        config_path,
        """
vllm:
  model: test/model
  host: 127.0.0.1
  port: 9000
  enable_auto_tool_choice: true
  tool_call_parser: qwen3_xml
  enable_lora: true
  max_loras: 2
  max_lora_rank: 32
  lora_modules:
    - a=/models/adapters/a
  extra_args:
    - --seed
    - "7"
paths:
  download_dir: /models/cache
  adapter_dir: /models/adapters
health:
  check_path: /v1/models
""".strip(),
    )

    cfg = load_runtime_config(env={"CONFIG_PATH": str(config_path)})
    cmd = cfg.build_vllm_command()

    assert cmd[:3] == ["vllm", "serve", "test/model"]
    assert "--enable-auto-tool-choice" in cmd
    assert "--tool-call-parser" in cmd
    assert "--enable-lora" in cmd
    assert "--lora-modules" in cmd
    assert "a=/models/adapters/a" in cmd
    assert "--seed" in cmd
    assert "7" in cmd


def test_rejects_removed_startup_timeout_config_key(tmp_path: Path) -> None:
    config_path = tmp_path / "server-config.yaml"
    _write_yaml(
        config_path,
        """
vllm:
  model: test/model
paths: {}
health:
  startup_timeout_seconds: 900
""".strip(),
    )

    with pytest.raises(ConfigError, match="unknown health keys: startup_timeout_seconds"):
        load_runtime_config(env={"CONFIG_PATH": str(config_path)})


def test_rejects_removed_logging_section(tmp_path: Path) -> None:
    config_path = tmp_path / "server-config.yaml"
    _write_yaml(
        config_path,
        """
vllm:
  model: test/model
paths: {}
health: {}
logging:
  level: info
""".strip(),
    )

    with pytest.raises(ConfigError, match="unknown top-level keys: logging"):
        load_runtime_config(env={"CONFIG_PATH": str(config_path)})
