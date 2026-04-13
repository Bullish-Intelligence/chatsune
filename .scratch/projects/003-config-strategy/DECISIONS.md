# DECISIONS

No implementation decisions recorded yet.

## 2026-04-13 — Keep `config/server-config.yaml` local-only
- `config/server-config.example.yaml` is tracked as source template.
- `config/server-config.yaml` is gitignored to keep per-host runtime tuning local.
- This matches the personal-hardware operator model while preserving deterministic schema via template + loader validation.

## 2026-04-13 — Single loader owns config merge and secret resolution
- Implemented strict schema validation in Python (`config_loader.py`) instead of shell parsing.
- Runtime now has one deterministic path from YAML + env contract to final vLLM argv.
- Secret-file and raw-env conflict behavior is enforced centrally (`ALLOW_INSECURE_ENV_SECRETS` gate).

## 2026-04-13 — Remove `env_file` usage from runtime services
- Compose runtime services now use explicit `environment` mappings only.
- This prevents accidental environment bleed and keeps secret/config provenance explicit.
- Applied to both baseline and tun profile variants.

## 2026-04-13 — Remove legacy shell entrypoint from active path
- Runtime now starts through `python -m chatsune.bootstrap` from the vLLM image.
- This centralizes schema/precedence/security logic in Python and eliminates duplicated env parsing logic.
