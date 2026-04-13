# CONFIG_SECRETS_IMPLEMENTATION_PLAN

## Table of Contents

1. Objective and Scope
   - Defines what this plan implements and what it intentionally avoids.
2. Operating Context and Security Posture
   - Tailors controls for personal hardware on a private Tailnet.
3. Final Target Architecture
   - Presents the clean end-state for config and secrets flow.
4. Configuration Ownership Model
   - Assigns each setting family to one canonical source.
5. Deterministic Precedence Rules
   - Defines exact merge behavior for env, config file, and secret files.
6. File and Directory Standards
   - Specifies required files, paths, git policy, and permissions.
7. Secrets Standard (Personal-Hardware Optimized)
   - Defines practical, secure secret handling without enterprise overhead.
8. Compose Integration Design
   - Details how Compose should pass only required values and mounts.
9. Bootstrap Implementation Design
   - Defines the Python bootstrap contract to validate and launch vLLM.
10. Config Schema Design (`server-config.yaml`)
    - Provides a minimal schema with clear extensibility.
11. Environment Variable Contract
    - Declares which env vars are allowed and for what purpose.
12. Migration Plan From Current Chatsune State
    - Maps concrete file-level changes from current implementation to target.
13. Validation and Test Plan
    - Defines unit/integration/smoke checks to lock in behavior.
14. Operational Runbook
    - Provides lifecycle tasks: first setup, rotate, debug, recover.
15. Rollout Phases and Milestones
    - Breaks delivery into pragmatic implementation phases.
16. Acceptance Criteria
    - Establishes concrete done conditions for this initiative.
17. Non-Goals
    - Clarifies what is intentionally excluded from this iteration.
## 1. Objective and Scope

This plan implements a clean configuration and secret management system for Chatsune that is:
- deterministic,
- easy to operate on personal hardware,
- secure enough for private Tailnet use,
- simple to debug,
- and easy to evolve.

Scope includes:
- Compose wiring,
- bootstrap config loading/validation,
- secret-file integration,
- file layout + permission policy,
- tests and operational docs.

Scope excludes:
- external cloud secret managers,
- multi-tenant policy engines,
- enterprise compliance controls.

## 2. Operating Context and Security Posture

Assumptions for this deployment model:
- single operator or small trusted household/team,
- personal host with local Docker engine,
- private Tailnet exposure only,
- no direct public internet ingress for vLLM API.

Security posture for this context:
- prioritize preventing accidental leakage over enterprise-grade compartmentalization,
- eliminate raw secrets from `.env`,
- keep secrets out of git and standard logs,
- enforce least exposure between services,
- keep operations lightweight (no mandatory vault dependency).

## 3. Final Target Architecture

Recommended clean architecture:

1. `.env` (non-sensitive deployment knobs only)
- hostnames, ports, feature toggles, file references, profile selection.

2. `config/server-config.yaml` (behavioral runtime configuration)
- nested vLLM settings, adapter map, template references, health/logging options.

3. secret files (token/key material only)
- mounted read-only into only the container that needs them.

4. Python bootstrap (`chatsune.bootstrap`)
- loads sources,
- applies precedence rules,
- validates types and conflicts,
- resolves secrets from `*_FILE`,
- renders final `vllm serve ...` argv,
- executes vLLM.

5. Compose as wiring layer only
- mounts config/secrets,
- passes explicit env vars,
- does not carry business logic.

## 4. Configuration Ownership Model

To keep the system elegant, each setting class has one owner.

Owner: `.env`
- `TS_HOSTNAME`, `TS_USERSPACE`, `TS_EXTRA_ARGS`
- `CONFIG_PATH`
- secret file path references (`HF_TOKEN_FILE`, `VLLM_API_KEY_FILE`, `TS_AUTHKEY_FILE`)
- optional runtime override toggles

Owner: `config/server-config.yaml`
- vLLM behavior and model/runtime tunables
- adapter configuration
- template/parser defaults
- health/logging defaults

Owner: secret files
- HF token
- vLLM API key
- Tailscale auth key
- future TLS/private keys

Owner: runtime explicit env overrides (rare)
- one-off override use only (`docker compose run -e ...`)
- no persistent operational reliance.

Conflict policy:
- dual-definition of the same non-secret key in both env and YAML is an error unless the key is explicitly marked overrideable.

## 5. Deterministic Precedence Rules

Precedence must be defined against values visible inside the container.

Non-secret setting precedence:
1. explicit runtime env override (container runtime)
2. `server-config.yaml`
3. bootstrap defaults

Secret-backed setting precedence:
1. explicit raw secret env (debug only; gated)
2. `*_FILE` path value -> file content
3. secret file path from YAML (optional future)
4. fail if required and unresolved

Hard rule:
- if both `FOO` and `FOO_FILE` are present, `FOO` wins only when `ALLOW_INSECURE_ENV_SECRETS=true`; otherwise bootstrap fails fast.

Rationale:
- deterministic,
- debuggable,
- avoids accidental fallback to insecure paths.

## 6. File and Directory Standards

Required files:
- `.env.example`
- `.gitignore` entries for local secrets and local env files
- `config/server-config.yaml`
- `config/server-config.example.yaml`
- `src/chatsune/bootstrap.py`
- `src/chatsune/config_loader.py` (or equivalent)
- `docs/configuration.md`

Recommended local-only paths:
- `.secrets/` (repo-local, gitignored) for personal hardware simplicity
- optional stronger isolation: `${HOME}/.config/chatsune/secrets/`

Git policy:
- commit `.env.example` only,
- never commit `.env`, `.secrets/*`, or any token-containing generated file.

Permission policy:
- secret files: `chmod 600`
- secret dirs: `chmod 700`
- bootstrap validates readability and rejects group/world-writable secret files on Linux/macOS.

## 7. Secrets Standard (Personal-Hardware Optimized)

Primary mode (default): file-based secrets with local filesystem permissions.

Recommended secret files:
- `.secrets/ts_authkey`
- `.secrets/hf_token`
- `.secrets/vllm_api_key` (optional)

Compose passes only file paths, not raw secret values.

Practical controls for this context:
- keep `.secrets/` in `.gitignore`,
- avoid printing env dump commands in docs,
- never echo secret values in bootstrap logs,
- rotate by overwriting file, then restarting affected service.

Optional hardening for advanced users:
- move secrets outside repo root,
- encrypted disk/home directory,
- bind mount with `:ro`,
- avoid shell history leaks during setup.

## 8. Compose Integration Design

Compose design rules:
- no `env_file:` injection into services,
- explicit `environment:` mapping only,
- mount secret files read-only,
- mount config read-only,
- keep vLLM and tailscale secrets separated.

Service-specific secret exposure:
- `tailscale` gets only `TS_AUTHKEY_FILE` secret mount.
- `vllm` gets only `HF_TOKEN_FILE` and optional `VLLM_API_KEY_FILE`.

Example target compose pattern:

```yaml
services:
  tailscale:
    image: tailscale/tailscale:stable
    environment:
      TS_STATE_DIR: /var/lib/tailscale
      TS_AUTHKEY_FILE: /run/secrets/ts_authkey
      TS_EXTRA_ARGS: ${TS_EXTRA_ARGS:-}
      TS_USERSPACE: ${TS_USERSPACE:-true}
    volumes:
      - tailscale_state:/var/lib/tailscale
      - ./.secrets/ts_authkey:/run/secrets/ts_authkey:ro

  vllm:
    build:
      context: .
      dockerfile: images/vllm/Dockerfile
    network_mode: service:tailscale
    environment:
      CONFIG_PATH: /app/config/server-config.yaml
      HF_TOKEN_FILE: /run/secrets/hf_token
      VLLM_API_KEY_FILE: /run/secrets/vllm_api_key
      ALLOW_INSECURE_ENV_SECRETS: ${ALLOW_INSECURE_ENV_SECRETS:-false}
    volumes:
      - ./config/server-config.yaml:/app/config/server-config.yaml:ro
      - ./config/chat-templates:/app/config/chat-templates:ro
      - ./.secrets/hf_token:/run/secrets/hf_token:ro
      - ./.secrets/vllm_api_key:/run/secrets/vllm_api_key:ro
```

## 9. Bootstrap Implementation Design

Implement `src/chatsune/bootstrap.py` as the runtime entrypoint.

Bootstrap responsibilities:
1. read allowed env vars,
2. parse `CONFIG_PATH` YAML,
3. apply precedence/ownership rules,
4. resolve secret files (`*_FILE`),
5. validate schema/types/required values,
6. redact and log effective non-sensitive config,
7. generate argv list for `vllm serve`,
8. `execvp` into vLLM.

Logging requirements:
- never log token/key contents,
- log which source won for key settings (`env`, `yaml`, `default`),
- include final effective command with secret values redacted.

Failure behavior:
- fail fast with actionable errors for:
  - missing required model,
  - missing required secret file,
  - invalid file permissions (warning or error based on strict mode),
  - invalid numeric/boolean parsing,
  - forbidden source conflicts.

## 10. Config Schema Design (`server-config.yaml`)

Define a minimal schema first:

```yaml
vllm:
  model: Qwen/Qwen3-4B-Instruct-2507-FP8
  host: 0.0.0.0
  port: 8000
  dtype: auto
  max_model_len: 32768
  max_num_seqs: 32
  gpu_memory_utilization: 0.95
  tensor_parallel_size: 1
  trust_remote_code: false
  disable_log_requests: false
  enable_auto_tool_choice: false
  tool_call_parser: null
  chat_template: null
  response_role: assistant
  enable_lora: false
  max_loras: 4
  max_lora_rank: 64
  lora_modules: []
  extra_args: []

paths:
  download_dir: /models/cache
  adapter_dir: /models/adapters

health:
  startup_timeout_seconds: 900
  check_path: /v1/models

logging:
  level: info
  redact_secrets: true
```

Schema rules:
- strict key validation (unknown top-level keys -> error),
- explicit nullable fields where needed,
- lora modules represented as list entries (not free-form comma map string),
- convert to vLLM CLI flags in one deterministic function.

## 11. Environment Variable Contract

Allowed env vars in vLLM container (initial):
- `CONFIG_PATH`
- `HF_TOKEN_FILE`
- `VLLM_API_KEY_FILE`
- `HF_TOKEN` (debug-only override)
- `VLLM_API_KEY` (debug-only override)
- `ALLOW_INSECURE_ENV_SECRETS`
- `CHATSUNE_STRICT_CONFIG` (default true)

Allowed env vars in tailscale container:
- `TS_STATE_DIR`
- `TS_AUTHKEY_FILE`
- `TS_EXTRA_ARGS`
- `TS_USERSPACE`
- `TS_HOSTNAME`

Disallowed pattern:
- passing broad unrelated env sets into services,
- raw secrets persisted in `.env` for normal operation.

## 12. Migration Plan From Current Chatsune State

Current state summary:
- shell entrypoint maps many `VLLM_*` env vars directly,
- `.env.example` currently includes raw secret fields,
- no unified YAML behavior config yet,
- compose is explicit-env mapped (good baseline).

File-level migration steps:

1. Add config assets
- create `config/server-config.example.yaml`
- create `config/server-config.yaml` (local, gitignored) from example

2. Add bootstrap loader
- add `src/chatsune/bootstrap.py`
- add `src/chatsune/config_loader.py`
- add helper for secret resolution and redaction

3. Switch container entrypoint
- update `images/vllm/Dockerfile` to run bootstrap module
- keep shell entrypoint only as compatibility fallback or remove it

4. Update compose
- pass `CONFIG_PATH` and `*_FILE` vars
- mount `.secrets/*` read-only
- remove raw secret env pass-throughs

5. Update `.env.example`
- replace raw token fields with path references and comments
- document debug-only insecure override path

6. Add policy files
- update `.gitignore` with `.env`, `.secrets/`, local config files
- add `.secrets/.gitkeep` optional placeholder

7. Documentation
- add `docs/configuration.md` with setup/rotation/debug procedures
- update README quickstart to new flow

## 13. Validation and Test Plan

Unit tests:
- precedence resolution tests,
- conflict detection tests,
- secret file read + permission checks,
- schema validation tests,
- CLI argument render tests from merged config.

Integration tests:
- `docker compose config` render with sample `.env`,
- bootstrap dry-run command rendering,
- missing secret file failure behavior,
- successful startup path with fake local secrets.

Smoke tests:
- existing `scripts/smoke_test.py` against running stack,
- verify tailscale and vLLM health checks,
- verify no secret value appears in logs.

Regression guardrails:
- add tests to ensure `env_file` is not used in runtime services,
- add test that `.env.example` contains `*_FILE` and not raw secret defaults.

## 14. Operational Runbook

First-time setup:
1. copy `.env.example` -> `.env`
2. create `.secrets/` with permissions `700`
3. create token files with permissions `600`
4. copy `config/server-config.example.yaml` -> `config/server-config.yaml`
5. run `docker compose up -d --build`
6. run smoke test from tailnet client

Rotate secret:
1. overwrite relevant `.secrets/*` file
2. restart only affected service
3. verify health and smoke test

Debug override (temporary):
1. run with `-e HF_TOKEN=... -e ALLOW_INSECURE_ENV_SECRETS=true`
2. do not persist in `.env`
3. remove override immediately after test

Recovery:
- if bootstrap fails, error output should identify missing/invalid source and required fix.

## 15. Rollout Phases and Milestones

Phase A: Foundations
- add schema example, `.gitignore` policy, `.env.example` redesign.

Phase B: Bootstrap
- implement config + secret loader and command renderer.

Phase C: Compose cutover
- wire services to `CONFIG_PATH` + `*_FILE` mounts and remove raw secret envs.

Phase D: Verification + docs
- complete tests and publish operator runbook.

Phase E: Cleanup
- remove legacy shell-path assumptions and stale variables.

## 16. Acceptance Criteria

Configuration correctness:
- startup configuration is deterministic and tested.
- unknown config keys fail in strict mode.
- source precedence behavior is documented and verified.

Secret handling:
- normal workflow requires no raw secret values in `.env`.
- all secrets are file-backed and mounted read-only.
- logs and diagnostics do not expose secret content.

Operational quality:
- first-time setup can be completed in under 10 minutes with docs.
- rotate-and-restart flow is documented and works.
- smoke tests pass with the new model.

Code quality:
- unit tests cover merge logic and secret resolution.
- integration checks validate compose wiring and bootstrap behavior.

## 17. Non-Goals

- mandatory external secret manager integration,
- cluster-scale secret distribution,
- enterprise policy/compliance framework,
- remote centralized control plane.

This plan intentionally optimizes for a clean, safe, low-friction personal-hardware deployment on a private Tailnet.
