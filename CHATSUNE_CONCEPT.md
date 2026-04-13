# CHATSUNE Concept

## Table of Contents

1. Purpose and Scope
   - Defines what this repository will become and the boundaries of the initial release.
2. Current-State Baseline (From `.context/server`)
   - Captures what exists today in the copied reference implementation.
3. Target Product Vision
   - Describes the standalone, reusable Chatsune runtime and its core outcomes.
4. Design Principles
   - Lists the key architecture and product principles guiding all implementation decisions.
5. Proposed Runtime Architecture
   - Details service topology, networking model, and storage design.
6. Configuration Model
   - Specifies a clean env-first contract and translation strategy to vLLM/Tailscale flags.
7. Repository Structure Proposal
   - Outlines file and folder organization for runtime, examples, docs, and optional helpers.
8. Container and Entrypoint Strategy
   - Defines image strategy and generic entrypoint behavior for model-agnostic serving.
9. Security and Access Model
   - Documents default security posture, secrets handling, and privilege choices.
10. Operations and Observability
   - Defines health checks, diagnostics workflow, and expected runbook behavior.
11. Extension Patterns
   - Describes optional overlays for LoRA, chat templates, static assets, and admin tooling.
12. Migration Plan From Reference Stack
   - Breaks migration into phases with concrete file-level transitions.
13. Testing and Validation Strategy
   - Defines unit, integration, and smoke testing for the standalone repo.
14. Risks and Mitigations
   - Enumerates key migration/product risks and practical mitigations.
15. Initial Milestones and Acceptance Criteria
   - Defines done conditions for the first production-ready release.
16. Out of Scope (Initial Version)
   - Clarifies what will not be built in v1.
## 1. Purpose and Scope

Chatsune will be a standalone repository for running a private, Tailnet-accessible vLLM server stack. It is a deployment product first, with optional helper code where it improves operator experience.

Primary scope for the first implementation in this repo:
- Provide a generic, model-agnostic vLLM runtime.
- Provide built-in private networking through a Tailscale sidecar.
- Keep deployment centered on Docker Compose with clear defaults.
- Keep project-specific behavior out of the base stack.
- Support optional extensions (LoRA, templates, static bundles) as overlays/examples.

## 2. Current-State Baseline (From `.context/server`)

The copied reference stack demonstrates a working pattern:
- `docker-compose.yml` uses a `tailscale` container and `vllm-server` with `network_mode: service:tailscale`.
- `entrypoint.sh` hard-codes `Qwen/Qwen3-4B-Instruct-2507-FP8` and parser flags.
- `Dockerfile` wraps `vllm/vllm-openai:latest` and injects the shell entrypoint.
- `Dockerfile.tailscale` adds `git` and `docker-cli` to support in-container self-update (`update.sh`).
- `agents-server` and supporting files provide optional static serving for `agents/`.
- `adapter_manager.py` supports runtime LoRA adapter loading via `/v1/load_lora_adapter`.

Constraints and issues visible in current state:
- Model and parser behavior are hard-coded in runtime script.
- Tailscale container has broader privileges than necessary for a generic baseline (`/var/run/docker.sock`, repo bind mount, SSH-oriented workflow).
- `test_connection.py` default model is stale (`google/functiongemma-270m-it`) versus current entrypoint model.
- Naming remains legacy (`vllm-gemma`) and is not product-neutral.

## 3. Target Product Vision

Chatsune should be a reusable private inference stack that teams can deploy without exposing public ingress.

Expected user outcome:
- Start a stack.
- Node joins Tailnet.
- OpenAI-compatible API is reachable privately via Tailscale DNS or tailnet IP.
- Operator can choose model/config via environment rather than editing runtime scripts.

Core v1 outcomes:
- Generic `vllm serve` startup from env-driven configuration.
- Default two-service architecture (`tailscale`, `vllm`) with optional service overlays.
- Persistent model/cache/state volumes.
- Clear operations runbook and smoke checks.

## 4. Design Principles

- Product over framework: optimize for deployability, not heavy abstraction.
- Generic defaults: no hard-coded model, parser, or hostname assumptions.
- Least privilege by default: avoid privileged mounts/capabilities unless required.
- Extension by composition: optional features through overlays/profiles, not base complexity.
- Operational clarity: explicit health checks, startup logs, and simple diagnostics.
- Stable migration path: preserve what works from the reference stack while removing project coupling.

## 5. Proposed Runtime Architecture

Default services:
- `tailscale`: network identity, tailnet join, state persistence.
- `vllm`: OpenAI-compatible inference server sharing the tailscale namespace.

Optional services:
- `assets` (or `agents-server`): static artifact serving as profile/overlay.
- `diagnostics` helper container for advanced troubleshooting.

Networking:
- `vllm` uses `network_mode: service:tailscale`.
- No default host port exposure.
- Access expected through Tailnet identity only.

Storage:
- `tailscale_state` volume.
- `hf_cache` volume.
- optional `model_store` volume.
- optional `adapters` mount.
- optional read-only `config` mount for templates.

## 6. Configuration Model

The repo will expose a documented env contract split by concern.

vLLM core:
- `VLLM_MODEL` (required)
- `VLLM_HOST` (default `0.0.0.0`)
- `VLLM_PORT` (default `8000`)
- `VLLM_DTYPE`
- `VLLM_MAX_MODEL_LEN`
- `VLLM_MAX_NUM_SEQS`
- `VLLM_GPU_MEMORY_UTILIZATION`
- `VLLM_TENSOR_PARALLEL_SIZE`
- `VLLM_TRUST_REMOTE_CODE`
- `VLLM_DOWNLOAD_DIR`
- `VLLM_EXTRA_ARGS` (escape hatch)

Tooling/template options:
- `VLLM_ENABLE_AUTO_TOOL_CHOICE`
- `VLLM_TOOL_CALL_PARSER`
- `VLLM_CHAT_TEMPLATE`
- `VLLM_RESPONSE_ROLE`

LoRA options:
- `VLLM_ENABLE_LORA`
- `VLLM_MAX_LORAS`
- `VLLM_MAX_LORA_RANK`
- `VLLM_LORA_MODULES`
- `VLLM_ADAPTER_DIR`

Tailscale:
- `TS_AUTHKEY` (required)
- `TS_HOSTNAME`
- `TS_STATE_DIR`
- `TS_EXTRA_ARGS`
- `TS_USERSPACE`
- `TS_ENABLE_HEALTH_CHECK`
- `TS_ENABLE_METRICS`

Token/auth related:
- `HUGGING_FACE_HUB_TOKEN` / `HF_TOKEN` as needed.
- optional `VLLM_API_KEY` for API protection model.

## 7. Repository Structure Proposal

```text
chatsune/
├── CHATSUNE_CONCEPT.md
├── README.md
├── LICENSE
├── .env.example
├── compose.yaml
├── compose.profiles.yaml
├── images/
│   ├── vllm/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── tailscale/
│       └── Dockerfile
├── config/
│   ├── models/
│   │   ├── qwen3.env
│   │   ├── llama.env
│   │   └── mistral.env
│   └── chat-templates/
├── examples/
│   ├── basic/
│   ├── lora/
│   ├── static-assets/
│   └── userspace-networking/
├── scripts/
│   ├── smoke_test.py
│   └── adapter_manager.py
├── src/
│   └── chatsune/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       └── diagnostics.py
├── tests/
│   ├── unit/
│   └── smoke/
└── docs/
    ├── architecture.md
    ├── operations.md
    ├── security.md
    └── migration-from-reference.md
```

Rationale:
- Keeps default runtime path small (`compose.yaml`, `images/`, `.env.example`).
- Isolates non-default behaviors into examples/profiles.
- Allows helper Python package without forcing framework-style runtime design.

## 8. Container and Entrypoint Strategy

vLLM image strategy:
- Start with a thin wrapper around upstream `vllm/vllm-openai`.
- Add a generic entrypoint that constructs CLI args from env.
- Avoid embedding model-specific logic into the base image.

Tailscale image strategy:
- Prefer stock image for base runtime.
- Do not include Docker CLI + repo self-update behavior in default mode.
- Keep SSH/admin behavior as optional profile if needed later.

Entrypoint behavior requirements:
- Fail fast if required env (for example `VLLM_MODEL`) is missing.
- Build command using array semantics, not string concatenation.
- Include only configured flags.
- Log effective configuration safely (without exposing secrets).
- Execute `vllm serve` as PID 1.

## 9. Security and Access Model

Default posture:
- Private-only access through Tailscale.
- No public port mapping by default.
- Persistent node identity via named volume.
- No Docker socket mount in base profile.
- Read-only config mounts where possible.

Privilege strategy:
- Support both userspace and tun-based approaches.
- Document userspace as default path where feasible.
- If tun mode is required, explicitly document capability and `/dev/net/tun` requirements.

Secrets strategy:
- Do not commit runtime secrets.
- Provide `.env.example` with placeholders.
- Document integration with external secret delivery later (out of v1 implementation).

## 10. Operations and Observability

Minimum operations baseline:
- Service health checks in Compose.
- Startup logs that identify selected model and core toggles.
- Documented checklist for:
  - tailnet join success,
  - vLLM listen status,
  - model load state,
  - GPU visibility,
  - remote tailnet connectivity test.

Initial tooling:
- `scripts/smoke_test.py` to validate chat completion path.
- retained/adapted `adapter_manager.py` for runtime LoRA loading.
- optional `chatsune diagnostics` CLI command in later phase.

## 11. Extension Patterns

LoRA:
- Static declaration at boot through env flags.
- Runtime load/unload operations via vLLM endpoints and helper scripts.

Custom templates:
- Mount template directory and select via `VLLM_CHAT_TEMPLATE`.
- Keep parser/template coupling in model profile examples, not base defaults.

Static assets:
- Keep agents/static server as optional profile (`static-assets`), not default runtime.

Admin workflows:
- Avoid coupling deployment to in-container `git pull` and Docker socket control.
- Prefer external CI/CD or host-side orchestration for updates.

## 12. Migration Plan From Reference Stack

Phase 1: Foundation extraction
- Copy and rename baseline files into Chatsune structure.
- Replace legacy names (`vllm-gemma`, remora-specific host hints).
- Preserve working sidecar topology.

Phase 2: Generic runtime conversion
- Rewrite `entrypoint.sh` to env-driven command construction.
- Replace hard-coded model/parser settings with profile/env examples.
- Normalize `.env.example` to generic options.

Phase 3: Security tightening
- Remove Docker socket and repo bind from default tailscale setup.
- Move SSH/self-update behavior to optional profile or deprecate.
- Clarify tun/userspace paths and required capabilities.

Phase 4: Extension extraction
- Move `agents-server` into optional overlay.
- Keep `adapter_manager.py`, updating defaults/naming for Chatsune.
- Add template and LoRA examples under `examples/`.

Phase 5: Test and docs hardening
- Align smoke tests with default model selection contract.
- Ensure docs and examples reflect actual command paths and names.
- Add migration doc mapping old server files to new Chatsune equivalents.

## 13. Testing and Validation Strategy

Unit tests (targeted):
- env-to-flag translation logic.
- required env validation and error handling.
- profile parsing/merging if implemented.

Smoke tests:
- bring-up test for compose stack.
- health endpoint checks.
- chat completion roundtrip.
- optional LoRA load call integration path.

Manual validation matrix:
- GPU host with tun mode.
- GPU host with userspace mode (if supported in environment).
- tailnet reachability from a second client machine.

## 14. Risks and Mitigations

Risk: upstream vLLM image changes break runtime assumptions.
- Mitigation: pin tested image tags; maintain compatibility notes.

Risk: overgeneralization causes poor defaults.
- Mitigation: provide curated model profiles and documented recommended starting configs.

Risk: security regressions from legacy operational shortcuts.
- Mitigation: keep privileged admin behavior out of base stack.

Risk: model-specific parser/template behavior is brittle.
- Mitigation: isolate model-specific settings into per-model examples and tests.

Risk: migration drift between docs and runtime behavior.
- Mitigation: make smoke tests part of acceptance and keep docs tied to executable examples.

## 15. Initial Milestones and Acceptance Criteria

Milestone A: Generic private runtime
- `compose up` starts tailscale + vllm with env-selected model.
- API reachable over Tailnet without public port publishing.
- Basic smoke test passes.

Milestone B: Secure baseline
- Default stack excludes Docker socket and repo bind mounts.
- Documented secrets handling and least-privilege defaults.

Milestone C: Extension-ready v1
- Optional static-assets profile available.
- LoRA loading helper works against running server.
- Model profile examples included and documented.

Milestone D: Documentation complete
- README quickstart works end-to-end.
- `docs/architecture.md`, `docs/operations.md`, `docs/security.md`, and migration mapping are complete and consistent.

## 16. Out of Scope (Initial Version)

- Multi-node distributed inference orchestration.
- Full cluster scheduling and autoscaling.
- Multi-tenant quota/control-plane features.
- Rich web administration UI.
- Broad model lifecycle management platform features.

