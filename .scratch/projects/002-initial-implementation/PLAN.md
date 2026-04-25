# PLAN — 002 Initial Implementation

## Reminders
- NO SUBAGENTS. Do all work directly.

## Goal
Implement the first working version of the standalone Chatsune repository based on `CHATSUNE_CONCEPT.md`.

## Steps
1. Establish baseline repo structure (`images/`, `config/`, `examples/`, `scripts/`, `docs/`, optional `src/`, `tests/`).
2. Implement base `compose.yaml` with `tailscale` + `vllm` topology.
3. Implement generic vLLM entrypoint and image wiring.
4. Create `.env.example` with documented defaults/placeholders.
5. Migrate/adapt helper scripts (`smoke_test.py`, `adapter_manager.py`).
6. Add initial docs (`README.md`, architecture/operations/security stubs).
7. Validate stack configuration and smoke flow.
8. Record progress and decisions.

## Acceptance Criteria
- Base stack starts with env-driven model selection.
- Tailnet-private access pattern is preserved.
- No remora-specific hard-coded defaults remain in baseline runtime.
- Initial docs and scripts are consistent with the implementation.

## Final Reminder
- NO SUBAGENTS. Do all work directly.
