# REVIEW_REFACTORING

## Table of Contents
1. Purpose and Scope
2. Baseline Findings (Validated)
3. Refactoring Principles
4. Delivery Plan (Phased)
5. Phase P0: Security and Contract Alignment
6. Phase P1: Config Honesty and Hardening
7. Phase P2: Test Expansion and Positioning
8. File-by-File Change Plan
9. Devenv-Based Verification Workflow
10. Acceptance Criteria
11. Risk Management and Rollback
12. Suggested PR Slicing
13. Definition of Done
14. Appendix: Command Checklist

## 1) Purpose and Scope
This document is a detailed refactoring guide derived from:
- `.scratch/projects/004-review/CHATSUNE_REVIEW.md` (intern review)
- `.scratch/projects/004-review/REVIEW_REVIEW.md` (validated meta-review)

The goal is to convert review findings into a practical, staged implementation plan that improves:
- runtime security
- docs/runtime consistency
- config contract honesty
- reproducibility
- verification reliability

This guide is implementation-oriented and assumes changes will be made in the current repository, verified through `devenv`.

## 2) Baseline Findings (Validated)
Validated as real:
1. CLI secret leak path: `python -m chatsune.cli print-config --show-command` prints plaintext API key.
2. Config fields defined but not behaviorally wired: `health.*`, `logging.*`.
3. Optional API key docs do not match compose wiring (unconditional secret file mount).
4. Secret permission checks only reject writable group/world bits; readable bits still pass.
5. Floating image references reduce reproducibility (`latest`, `stable`).
6. Docs mismatches:
- `docs/security.md` says secrets expected via `.env` (conflicts with `*_FILE` model).
- `examples/lora/README.md` uses env vars that are not consumed by loader path.

Validated as inaccurate in intern review:
1. "No visible test suite" is false; tests exist and pass.

## 3) Refactoring Principles
1. Security before ergonomics for secret-bearing paths.
2. Prefer honest configuration surfaces over aspirational schemas.
3. Keep the architecture (sidecar + bootstrap) intact; tighten contracts.
4. Preserve backward compatibility when cheap; otherwise break clearly and document.
5. Every behavior change must have targeted tests.
6. Use `devenv` for all verification commands.

## 4) Delivery Plan (Phased)
- **P0 (immediate)**: eliminate secret exposure and align key operator contracts.
- **P1 (soon)**: harden config and security semantics, tighten reproducibility.
- **P2 (next)**: extend tests and clarify project positioning.

Recommended sequence:
1. P0.1 CLI redaction fix + tests
2. P0.2 optional API key contract alignment
3. P0.3 docs mismatch cleanup (security + LoRA)
4. P1.1 config field wire/remove decision + implementation
5. P1.2 secret permission hardening + tests
6. P1.3 image pinning policy + docs
7. P2 test expansion + README/metadata positioning cleanup

## 5) Phase P0: Security and Contract Alignment

### P0.1 Fix secret leakage in CLI command output

#### Problem
- `src/chatsune/cli.py` uses `format_command(cmd)` directly for `--show-command`.
- `src/chatsune/config_loader.py` includes `--api-key` when configured.
- `src/chatsune/bootstrap.py` already redacts, but CLI path bypasses it.

#### Refactoring approach
Option A (recommended): move redaction helper to shared module and consume from both CLI and bootstrap.

Suggested structure:
- New module: `src/chatsune/redaction.py`
- Export:
- `SECRET_FLAGS = {"--api-key"}`
- `redact_command(cmd: list[str]) -> str`

Then:
- `src/chatsune/bootstrap.py`: import shared `redact_command`.
- `src/chatsune/cli.py`: replace `format_command(cmd)` with `redact_command(cmd)` for human output.

#### Test requirements
- Add/extend CLI test to assert:
- raw secret not present in CLI `print-config --show-command` output.
- `***REDACTED***` present when secret flag exists.
- Keep existing bootstrap redaction test.

#### Acceptance check
- Repro command with temp `VLLM_API_KEY_FILE` no longer prints plaintext.

### P0.2 Align optional vLLM API key behavior

#### Problem
- Docs say API key optional.
- `compose.yaml` mounts `./.secrets/vllm_api_key` unconditionally.

#### Decision required
Pick one explicit contract and enforce it everywhere.

Option 1 (recommended): **Truly optional API key**
- Compose baseline must run without key file.
- Mount/variable wiring for key moves to opt-in profile or override compose file.

Option 2: **Required key file**
- Update docs to require key file and remove "optional" language.

#### Recommended implementation (Option 1)
- In `compose.yaml`, remove unconditional `./.secrets/vllm_api_key` mount and default `VLLM_API_KEY_FILE` wiring.
- Add an overlay (e.g., `compose.auth.yaml`) that introduces mount + env for authenticated mode.
- Update docs quickstart with two paths:
- anonymous/private-network mode
- key-protected mode

#### Test requirements
- Add policy/layout tests for whichever contract is chosen.
- If optional path chosen, include test asserting baseline compose does not hard-require API key file.

### P0.3 Correct high-impact docs mismatches

#### Targets
- `docs/security.md`
- `examples/lora/README.md`

#### Required corrections
1. `docs/security.md`
- replace "Secrets expected via `.env`" with file-based secret references (`*_FILE`) and local secret files.

2. `examples/lora/README.md`
- remove env-var-only instructions that loader ignores.
- provide YAML-based LoRA enablement example matching `config/server-config.yaml` shape.

#### Acceptance check
- Operator can follow docs without hitting contract mismatches.

## 6) Phase P1: Config Honesty and Hardening

### P1.1 Resolve declared-but-unused config fields

#### Current mismatch
Defined and validated in loader but not controlling behavior:
- `health.startup_timeout_seconds`
- `health.check_path`
- `logging.level`
- `logging.redact_secrets`

#### Decision framework
- If feature behavior is needed within next cycle: wire it.
- If not needed: remove from schema/defaults/docs immediately.

#### Recommended path
- **Wire `health.check_path`** into `chatsune.cli smoke-test` as first probe endpoint (fallback list optional).
- **Deprecate/remove `health.startup_timeout_seconds`** unless startup orchestration actually consumes it.
- **Remove `logging.level` and `logging.redact_secrets`** for now unless full logging system is being introduced.

Rationale: smallest honest surface with real behavior.

#### Implementation notes
- `src/chatsune/diagnostics.py` currently probes hardcoded endpoints.
- Update smoke-test command plumbing to accept configured `check_path` from loaded config when appropriate.
- Ensure command still supports explicit `--server-url` overrides.

#### Test requirements
- Add tests validating configured check path is honored.
- Add tests ensuring removed keys fail validation (if removed).

### P1.2 Harden strict secret file permission validation

#### Current behavior
- Rejects writable group/world bits (`0o022`).
- Does not reject group/world readable bits (`0o044`).

#### Recommended behavior in strict mode
- Reject any group/world permissions on secret files.
- Equivalent policy: require owner-only mode (`0o600`/`0o400` acceptable).

Suggested check:
- reject if `mode & 0o077 != 0` in strict mode.

#### Compatibility behavior
- In non-strict mode, allow but optionally warn (if warning path exists).

#### Test requirements
- Add test that `0644` secret file fails strict validation.
- Keep test that `0600` passes.

### P1.3 Pin runtime image versions

#### Current state
- `images/vllm/Dockerfile`: `FROM vllm/vllm-openai:latest`
- `compose.yaml`: `tailscale/tailscale:stable`

#### Recommended approach
- Pin to explicit tags (or digests for stronger immutability).
- Introduce update policy in docs:
- monthly review cadence
- manual bump + smoke test + changelog note

#### Implementation suggestions
- Replace `latest`/`stable` with pinned tags in Docker/Compose.
- Add short section in `docs/operations.md` or `README.md` named "Runtime image update policy".

## 7) Phase P2: Test Expansion and Positioning

### P2.1 Add regression tests for high-risk behavior
Prioritize:
1. CLI redaction regression (new).
2. Strict permission readable-bit regression (new).
3. Optional API key contract behavior (new).
4. Health check path behavior (if wired).

### P2.2 Clarify project positioning
Current repo identity is runtime toolkit + helper library, not broad reusable SDK.

Required updates:
- README opening paragraph
- `pyproject.toml` description (optional refinement)
- docs language consistency around importable API expectations

Target framing:
- "internal runtime toolkit for private vLLM over Tailscale"

## 8) File-by-File Change Plan

### Core code
- `src/chatsune/cli.py`
- `src/chatsune/bootstrap.py`
- `src/chatsune/config_loader.py`
- `src/chatsune/diagnostics.py`
- `src/chatsune/__init__.py` (if shared redaction helper is exported)
- `src/chatsune/redaction.py` (new, recommended)

### Runtime wiring
- `compose.yaml`
- possibly new `compose.auth.yaml` (if optional API key mode adopted)
- `compose.profiles.yaml` (only if this is where auth overlay is placed)

### Docs and examples
- `README.md`
- `docs/configuration.md`
- `docs/security.md`
- `docs/operations.md` (if image policy documented here)
- `examples/lora/README.md`
- `.env.example` (if contract changes)

### Tests
- `tests/unit/test_bootstrap.py` (or split into redaction module tests)
- `tests/unit/test_config_loader.py`
- add `tests/unit/test_cli.py` (recommended)
- `tests/unit/test_policy_contract.py`

## 9) Devenv-Based Verification Workflow
Run all checks through `devenv`.

Primary commands:
- `devenv shell -- test-unit`
- `devenv shell -- test-smoke`
- `devenv shell -- test`

For targeted checks during refactor:
- `devenv shell -- uv run --with pytest pytest tests/unit/test_cli.py -q`
- `devenv shell -- uv run --with pytest pytest tests/unit/test_config_loader.py -q`
- `devenv shell -- uv run --with pytest pytest tests/unit/test_policy_contract.py -q`

Manual security regression probe:
- run `python -m chatsune.cli print-config --show-command` with a temp `VLLM_API_KEY_FILE` and confirm plaintext key is absent.

## 10) Acceptance Criteria

### P0 acceptance
1. CLI no longer prints plaintext API key in show-command path.
2. API key optional/required contract is explicit and consistent across compose + docs.
3. Security and LoRA docs no longer contradict implementation.

### P1 acceptance
1. No config keys remain declared without owning behavior (or they are removed).
2. Strict mode rejects group/world-readable secret files.
3. Runtime images are pinned and update policy is documented.

### P2 acceptance
1. New regression tests exist for all major fixes.
2. README/package positioning reflects actual project shape.

## 11) Risk Management and Rollback

### Main risks
1. Breaking operator workflows by changing API key wiring abruptly.
2. Over-tight permission checks causing surprise on existing dev setups.
3. Removing config fields without migration notice.

### Mitigations
1. Introduce compatibility window (deprecation notes) where feasible.
2. Document migration steps in `docs/migration-from-reference.md` or new migration note.
3. Keep changes sliced into small PRs to reduce blast radius.

### Rollback strategy
- Revert PRs per phase independently.
- Keep security fix (redaction) isolated so it can stay even if other refactors roll back.

## 12) Suggested PR Slicing
PR 1 (P0 security):
- shared redaction helper + CLI fix + tests

PR 2 (P0 contract/docs):
- API key contract alignment + docs updates (security + LoRA)

PR 3 (P1 config honesty):
- wire/remove health/logging keys + tests

PR 4 (P1 hardening/repro):
- secret permission strictness + image pinning + update policy docs

PR 5 (P2 polish):
- additional regression tests + positioning text refinement

## 13) Definition of Done
Refactoring is complete when:
1. All P0 items are merged and verified in `devenv`.
2. P1 config/security/repro gaps are closed with tests.
3. P2 tests and positioning are updated.
4. `devenv shell -- test` is green.
5. A fresh operator following docs can stand up runtime without ambiguity.

## 14) Appendix: Command Checklist

### Baseline
- `devenv shell -- test`

### During redaction changes
- `devenv shell -- uv run --with pytest pytest tests/unit -q`
- manual `print-config --show-command` secret probe

### During compose/docs contract changes
- `devenv shell -- uv run --with pytest pytest tests/unit/test_policy_contract.py -q`

### Final gate
- `devenv shell -- test-unit`
- `devenv shell -- test-smoke`
- `devenv shell -- test`
