# DECISIONS

No implementation decisions recorded yet.

## 2026-04-13 — Keep `config/server-config.yaml` local-only
- `config/server-config.example.yaml` is tracked as source template.
- `config/server-config.yaml` is gitignored to keep per-host runtime tuning local.
- This matches the personal-hardware operator model while preserving deterministic schema via template + loader validation.
