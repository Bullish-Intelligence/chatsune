from __future__ import annotations

from pathlib import Path

from chatsune.config_loader import load_runtime_config


def test_requires_model_field(tmp_path: Path) -> None:
    config_path = tmp_path / "server-config.yaml"
    config_path.write_text(
        """
vllm:
  host: 0.0.0.0
paths: {}
health: {}
""".strip(),
        encoding="utf-8",
    )

    try:
        load_runtime_config({"CONFIG_PATH": str(config_path)})
        assert False, "expected error"
    except ValueError as exc:
        assert "vllm.model" in str(exc)
