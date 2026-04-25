# Configuration and Secrets

This runtime uses three configuration inputs:

1. `.env` for non-sensitive wiring values.
2. `config/server-config.yaml` for vLLM behavior.
3. `*_FILE` secret paths for tokens and keys.

## First-time Setup

1. Copy environment template:
   - `cp .env.example .env`
2. Create local secret directory and lock permissions:
   - `mkdir -p .secrets && chmod 700 .secrets`
3. Create required secret files:
   - `printf '%s\n' '<tailscale-auth-key>' > .secrets/ts_authkey`
   - `printf '%s\n' '<hf-token>' > .secrets/hf_token`
4. Lock secret file permissions:
   - `chmod 600 .secrets/ts_authkey .secrets/hf_token`
5. Copy runtime config template:
   - `cp config/server-config.example.yaml config/server-config.yaml`
6. Edit `config/server-config.yaml` for your model/runtime tuning.
7. Start baseline services:
   - `docker compose up -d --build`
8. Optional: enable API key auth for vLLM:
   - `printf '%s\n' '<vllm-api-key>' > .secrets/vllm_api_key`
   - `chmod 600 .secrets/vllm_api_key`
   - `docker compose -f compose.yaml -f compose.auth.yaml up -d --build`

## Secret Rotation

1. Overwrite the target secret file in `.secrets/`.
2. Restart only affected service:
   - `docker compose restart tailscale` for `ts_authkey`
   - `docker compose restart vllm` for `hf_token` or `vllm_api_key`
3. Validate health:
   - `python -m chatsune.cli smoke-test --server-url http://127.0.0.1:8000`

## Debug-only Raw Secret Override

Normal operations should not use raw secret env vars.

Temporary debug override is allowed only with:
- `ALLOW_INSECURE_ENV_SECRETS=true`
- a one-off runtime command (not persisted in `.env`)

Example:
- `docker compose run --rm -e ALLOW_INSECURE_ENV_SECRETS=true -e HF_TOKEN='<token>' vllm`

## Validation Commands

- Render compose:
  - `docker compose -f compose.yaml -f compose.profiles.yaml config`
  - `docker compose -f compose.yaml -f compose.auth.yaml config` (if using API key auth)
- Validate config:
  - `python -m chatsune.cli validate-env`
- Print effective config and command:
  - `python -m chatsune.cli print-config --show-command`

## Security Notes (Private Tailnet Context)

- Keep services private to Tailnet.
- Do not store secrets in `.env`.
- Keep `.secrets` gitignored and permission-locked.
- Bootstrap redacts command output when secrets are present.
