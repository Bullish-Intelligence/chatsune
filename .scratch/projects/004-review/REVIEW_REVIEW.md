# REVIEW_REVIEW

## Scope and Method
I reviewed the intern write-up in `.scratch/projects/004-review/CHATSUNE_REVIEW.md` and re-audited the repository directly (compose files, docs, Python package, scripts, examples, and tests).

Verification was performed in the project `devenv` environment:
- `devenv shell -- test-unit` -> `8 passed`
- `devenv shell -- test-smoke` -> `1 passed`
- `devenv shell -- test` -> `9 passed`

## Executive Assessment
The review is directionally good and catches several real issues, but it has one clear factual miss and it omits a couple of important repo mismatches.

My assessment: **mostly accurate (about 75-80%), with high-value findings mixed with one significant false claim**.

## Claim-by-Claim Accuracy

1. `print-config --show-command` can leak the API key: **Accurate (P0)**.
- `src/chatsune/cli.py` prints `format_command(cmd)` directly.
- `src/chatsune/config_loader.py` includes `--api-key` when configured.
- Reproduced via `devenv shell -- python -m chatsune.cli print-config --show-command` with a test key; output contained `--api-key super-secret`.
- `bootstrap.py` already has redaction, but CLI path does not.

2. Several config fields are declared but not wired: **Accurate**.
- `health.check_path`, `health.startup_timeout_seconds`, and `logging.*` are defined/validated/defaulted in `src/chatsune/config_loader.py`.
- They are not consumed by runtime behavior in `src/chatsune/diagnostics.py`, compose healthchecks, or bootstrap logging behavior.

3. Optional vLLM API key story is inconsistent with Compose: **Mostly accurate**.
- Docs mark API key as optional.
- `compose.yaml` always bind-mounts `./.secrets/vllm_api_key` into the container.
- This is an ergonomics mismatch and can fail if operators follow docs literally and skip the file.

4. Secret permission checks are weaker than docs imply: **Accurate**.
- `_validate_secret_file` only rejects group/world writable (`0o022`) and does not reject group/world readable bits.

5. LoRA operator experience incomplete: **Partially accurate, but underspecified in review**.
- The runtime YAML path for LoRA exists and is wired.
- However, `examples/lora/README.md` references env vars (`VLLM_ENABLE_LORA`, `VLLM_LORA_MODULES`) that are not consumed by current loader code. This is a concrete docs/runtime mismatch not called out clearly.

6. Reproducibility concerns due floating image tags: **Accurate**.
- `compose.yaml` uses `tailscale/tailscale:stable`.
- `images/vllm/Dockerfile` uses `vllm/vllm-openai:latest`.

7. "No visible test suite" and recommendation to add tests: **Inaccurate**.
- There is a visible test suite under `tests/` (unit + smoke).
- Existing tests already cover unknown keys, secret resolution behavior, command rendering, bootstrap redaction, and policy contracts.
- The intern's own "Files Reviewed" appendix excludes all test files, which likely caused this miss.

## Additional Issues Missed by the Intern Review

1. `docs/security.md` contradicts implementation guidance.
- It says "Secrets expected via `.env`", which conflicts with the repo's `*_FILE` secret-file model.

2. LoRA example docs are stale/misaligned.
- Example uses env-var toggles not recognized by the config loader path.

3. Current default `pytest` discovery can collect `scripts/smoke_test.py` (depends on `openai`) and fail in lean environments.
- Test invocation should target `tests/` explicitly in standard verification commands.

## My Determination of Library Status
The repo is a solid **runtime toolkit with helper Python modules**, not yet a broad reusable library package. The architecture and core config-loader design are good. Main risks are consistency and hardening gaps, not fundamental design flaws.

## Recommended Next Steps

### P0 (immediate)
1. Redact CLI command output in `print-config --show-command` using shared redaction logic.
2. Align optional API-key behavior across docs + compose wiring (truly optional mount or explicit required file contract).
3. Fix docs mismatches:
- `docs/security.md` secret source statement.
- `examples/lora/README.md` to match YAML-based configuration.

### P1 (soon)
1. Either wire or remove currently unused `health.*` and `logging.*` config fields.
2. Strengthen strict secret permission validation to reject group/world-readable files.
3. Pin runtime images to explicit versions (or digests) and document update cadence.

### P2 (next)
1. Expand tests where risk is highest:
- CLI redaction regression test.
- Secret-file readable-bit enforcement test.
- Optional API-key compose/operator contract test.
2. Clarify project positioning in README/package metadata as runtime toolkit vs reusable library.

## Final Verdict on CHATSUNE_REVIEW.md
The intern review is a useful first pass and correctly identifies the most serious operational/security issue (CLI secret leakage). However, it should not be treated as authoritative until corrected for the test-suite miss and expanded to include the additional docs/runtime mismatches above.
