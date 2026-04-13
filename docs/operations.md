# Operations

## Bring Up
1. Copy `.env.example` to `.env`.
2. Create local secret files under `.secrets/` (`ts_authkey`, `hf_token`, optional `vllm_api_key`).
3. Copy `config/server-config.example.yaml` to `config/server-config.yaml` and tune model/runtime values.
4. Run: `docker compose up -d --build`

## Validate
- Check tailscale health: `docker compose ps`
- Check vLLM logs: `docker logs -f chatsune-vllm`
- Run smoke test from a tailnet-connected machine:
  - `uv run scripts/smoke_test.py`

## Common Tasks
- Print effective config: `python -m chatsune.cli print-config --show-command`
- Validate configuration and secret wiring: `python -m chatsune.cli validate-env`
- Load LoRA adapter: `python scripts/adapter_manager.py --name lint --path /models/adapters/lint`
