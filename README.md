# chatsune

Standalone private vLLM + Tailscale sidecar runtime.

## What this repository provides
- Deterministic YAML-based runtime configuration (`config/server-config.yaml`).
- File-based secret handling via `*_FILE` references.
- Tailnet-private access via sidecar network topology.
- Docker Compose baseline with optional feature profiles.
- Helper scripts and Python CLI for config diagnostics.

## Quickstart
1. Copy env file:
   - `cp .env.example .env`
2. Create and secure local secrets directory:
   - `mkdir -p .secrets && chmod 700 .secrets`
3. Add required secrets (and lock file perms):
   - `printf '%s\n' '<tailscale-auth-key>' > .secrets/ts_authkey`
   - `printf '%s\n' '<hf-token>' > .secrets/hf_token`
   - `chmod 600 .secrets/ts_authkey .secrets/hf_token`
4. Copy runtime config template:
   - `cp config/server-config.example.yaml config/server-config.yaml`
5. Start baseline stack (no API key required):
   - `docker compose up -d --build`
6. Optional: enable API-key-protected mode:
   - `printf '%s\n' '<vllm-api-key>' > .secrets/vllm_api_key`
   - `chmod 600 .secrets/vllm_api_key`
   - `docker compose -f compose.yaml -f compose.auth.yaml up -d --build`
7. Check logs:
   - `docker logs -f chatsune-vllm`
8. Smoke test (from a tailnet-connected machine):
   - `uv run scripts/smoke_test.py`

## Optional profiles
- Static assets:
  - `docker compose -f compose.yaml -f compose.profiles.yaml --profile static-assets up -d`
- Tun networking variant:
  - `docker compose -f compose.yaml -f compose.profiles.yaml --profile tun up -d`
- API key auth overlay:
  - `docker compose -f compose.yaml -f compose.auth.yaml up -d`

## Helper commands
- Validate config/secrets: `python -m chatsune.cli validate-env`
- Print effective config: `python -m chatsune.cli print-config --show-command`
- Health smoke: `python -m chatsune.cli smoke-test --server-url http://127.0.0.1:8000`
  - Uses configured `health.check_path` first by default
- Load LoRA: `python scripts/adapter_manager.py --name <name> --path <path>`

## Repo layout
- `compose.yaml`: baseline runtime stack
- `compose.auth.yaml`: optional API-key overlay for vLLM
- `compose.profiles.yaml`: optional overlays
- `config/server-config.example.yaml`: tracked runtime config template
- `docs/configuration.md`: setup, rotation, debug, validation runbook
- `src/chatsune/bootstrap.py`: config+secret bootstrap entrypoint
- `src/chatsune/config_loader.py`: schema validation and argv rendering
