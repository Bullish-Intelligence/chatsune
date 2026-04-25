# CONTEXT — 002 Initial Implementation

The initial standalone Chatsune implementation has been created from the concept doc.

Implemented:
- Baseline runtime stack (`compose.yaml`) with `tailscale` + `vllm` services.
- Optional overlays (`compose.profiles.yaml`) for static-assets and tun variant.
- Generic env-driven vLLM entrypoint (`images/vllm/entrypoint.sh`).
- Model/config templates (`.env.example`, `config/models/*.env`, chat template placeholder).
- Helper scripts (`scripts/smoke_test.py`, `scripts/adapter_manager.py`).
- Python helper library/CLI (`src/chatsune/*`, `pyproject.toml`).
- Documentation set (`README.md`, `docs/*`).
- Initial tests (`tests/unit`, `tests/smoke`).

Key implementation adjustment made during validation:
- Removed `env_file` injection from `compose.yaml` services to avoid passing unrelated env vars/secrets into containers.

Current status:
- Core implementation complete.
- Runtime start not executed here (would require Docker runtime and valid secrets/GPU/model access).
- Pytest execution blocked only by missing pytest package in the local environment.
