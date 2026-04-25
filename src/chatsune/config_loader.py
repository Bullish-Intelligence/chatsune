from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import stat
from typing import Any

import yaml


class ConfigError(ValueError):
    pass


_ALLOWED_TOP_LEVEL = {"vllm", "paths", "health"}
_ALLOWED_VLLM_KEYS = {
    "model",
    "host",
    "port",
    "dtype",
    "max_model_len",
    "max_num_seqs",
    "gpu_memory_utilization",
    "tensor_parallel_size",
    "trust_remote_code",
    "disable_log_requests",
    "enable_auto_tool_choice",
    "tool_call_parser",
    "chat_template",
    "response_role",
    "enable_lora",
    "max_loras",
    "max_lora_rank",
    "lora_modules",
    "extra_args",
}
_ALLOWED_PATH_KEYS = {"download_dir", "adapter_dir"}
_ALLOWED_HEALTH_KEYS = {"check_path"}

_DEFAULTS: dict[str, Any] = {
    "vllm": {
        "host": "0.0.0.0",
        "port": 8000,
        "dtype": "auto",
        "max_model_len": 32768,
        "max_num_seqs": 32,
        "gpu_memory_utilization": 0.95,
        "tensor_parallel_size": 1,
        "trust_remote_code": False,
        "disable_log_requests": False,
        "enable_auto_tool_choice": False,
        "tool_call_parser": None,
        "chat_template": None,
        "response_role": "assistant",
        "enable_lora": False,
        "max_loras": 4,
        "max_lora_rank": 64,
        "lora_modules": [],
        "extra_args": [],
    },
    "paths": {
        "download_dir": "/models/cache",
        "adapter_dir": "/models/adapters",
    },
    "health": {
        "check_path": "/v1/models",
    },
}


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ConfigError("config file must be a mapping")
    return raw


def _validate_shape(cfg: dict[str, Any]) -> None:
    unknown_top = set(cfg) - _ALLOWED_TOP_LEVEL
    if unknown_top:
        keys = ", ".join(sorted(unknown_top))
        raise ConfigError(f"unknown top-level keys: {keys}")

    sections = [
        ("vllm", _ALLOWED_VLLM_KEYS),
        ("paths", _ALLOWED_PATH_KEYS),
        ("health", _ALLOWED_HEALTH_KEYS),
    ]
    for section, allowed in sections:
        data = cfg.get(section, {})
        if not isinstance(data, dict):
            raise ConfigError(f"{section} must be a mapping")
        unknown = set(data) - allowed
        if unknown:
            keys = ", ".join(sorted(unknown))
            raise ConfigError(f"unknown {section} keys: {keys}")


def _merge_with_defaults(cfg: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "vllm": dict(_DEFAULTS["vllm"]),
        "paths": dict(_DEFAULTS["paths"]),
        "health": dict(_DEFAULTS["health"]),
    }
    for section in merged:
        incoming = cfg.get(section, {})
        if incoming:
            merged[section].update(incoming)
    return merged


def _validate_types(cfg: dict[str, Any]) -> None:
    v = cfg["vllm"]
    if not isinstance(v.get("model"), str) or not v["model"].strip():
        raise ConfigError("vllm.model is required and must be a non-empty string")
    if not isinstance(v["port"], int):
        raise ConfigError("vllm.port must be an integer")
    if not isinstance(v["trust_remote_code"], bool):
        raise ConfigError("vllm.trust_remote_code must be a boolean")
    if not isinstance(v["disable_log_requests"], bool):
        raise ConfigError("vllm.disable_log_requests must be a boolean")
    if not isinstance(v["enable_auto_tool_choice"], bool):
        raise ConfigError("vllm.enable_auto_tool_choice must be a boolean")
    if not isinstance(v["enable_lora"], bool):
        raise ConfigError("vllm.enable_lora must be a boolean")
    if not isinstance(v["lora_modules"], list):
        raise ConfigError("vllm.lora_modules must be a list")
    if not isinstance(v["extra_args"], list):
        raise ConfigError("vllm.extra_args must be a list")


def _validate_secret_file(path: Path, strict: bool) -> None:
    if not path.exists():
        raise ConfigError(f"secret file not found: {path}")
    if not path.is_file():
        raise ConfigError(f"secret path is not a file: {path}")

    if os.name == "posix":
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o022:
            msg = f"secret file must not be group/world writable: {path} (mode {oct(mode)})"
            if strict:
                raise ConfigError(msg)


def _read_secret(path: Path) -> str:
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ConfigError(f"secret file is empty: {path}")
    return value


def _resolve_secret(name: str, env: dict[str, str], strict: bool) -> str | None:
    raw_name = name
    file_name = f"{name}_FILE"
    raw = env.get(raw_name)
    file_path = env.get(file_name)
    allow_insecure = _truthy(env.get("ALLOW_INSECURE_ENV_SECRETS"))

    if raw and file_path and not allow_insecure:
        raise ConfigError(
            f"both {raw_name} and {file_name} are set; set ALLOW_INSECURE_ENV_SECRETS=true to allow raw env"
        )

    if raw:
        if not allow_insecure:
            raise ConfigError(f"{raw_name} is set but ALLOW_INSECURE_ENV_SECRETS is false")
        return raw.strip()

    if not file_path:
        return None

    path = Path(file_path)
    _validate_secret_file(path, strict=strict)
    return _read_secret(path)


@dataclass(frozen=True)
class RuntimeConfig:
    data: dict[str, Any]
    hf_token: str | None
    vllm_api_key: str | None

    def build_vllm_command(self) -> list[str]:
        v = self.data["vllm"]
        paths = self.data["paths"]

        cmd = ["vllm", "serve", v["model"], "--host", v["host"], "--port", str(v["port"])]

        def add(flag: str, value: Any) -> None:
            if value is None or value == "":
                return
            cmd.extend([flag, str(value)])

        add("--dtype", v.get("dtype"))
        add("--max-model-len", v.get("max_model_len"))
        add("--max-num-seqs", v.get("max_num_seqs"))
        add("--gpu-memory-utilization", v.get("gpu_memory_utilization"))
        add("--tensor-parallel-size", v.get("tensor_parallel_size"))
        add("--download-dir", paths.get("download_dir"))
        add("--tool-call-parser", v.get("tool_call_parser"))
        add("--chat-template", v.get("chat_template"))
        add("--response-role", v.get("response_role"))
        add("--api-key", self.vllm_api_key)

        if v.get("enable_auto_tool_choice"):
            cmd.append("--enable-auto-tool-choice")
        if v.get("trust_remote_code"):
            cmd.append("--trust-remote-code")
        if v.get("disable_log_requests"):
            cmd.append("--disable-log-requests")

        if v.get("enable_lora"):
            cmd.append("--enable-lora")
            add("--max-loras", v.get("max_loras"))
            add("--max-lora-rank", v.get("max_lora_rank"))
            modules = [str(x) for x in v.get("lora_modules", []) if str(x).strip()]
            if modules:
                cmd.append("--lora-modules")
                cmd.extend(modules)

        extra_args = [str(x) for x in v.get("extra_args", [])]
        cmd.extend(extra_args)

        return cmd

    def environment(self) -> dict[str, str]:
        out: dict[str, str] = {}
        if self.hf_token:
            out["HF_TOKEN"] = self.hf_token
            out["HUGGING_FACE_HUB_TOKEN"] = self.hf_token
        return out


def load_runtime_config(env: dict[str, str] | None = None) -> RuntimeConfig:
    source = dict(os.environ if env is None else env)

    strict = source.get("CHATSUNE_STRICT_CONFIG", "true").strip().lower() != "false"
    config_path = Path(source.get("CONFIG_PATH", "/app/config/server-config.yaml"))

    cfg = _load_yaml(config_path)
    _validate_shape(cfg)
    merged = _merge_with_defaults(cfg)
    _validate_types(merged)

    hf_token = _resolve_secret("HF_TOKEN", source, strict=strict)
    vllm_api_key = _resolve_secret("VLLM_API_KEY", source, strict=strict)

    return RuntimeConfig(data=merged, hf_token=hf_token, vllm_api_key=vllm_api_key)


def format_command(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)
