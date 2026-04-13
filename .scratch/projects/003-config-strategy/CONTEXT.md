# CONTEXT

Completed Step 3 compose/image cutover:
- vLLM image entrypoint now runs `python -m chatsune.bootstrap`.
- Compose no longer passes broad `VLLM_*`/raw secret env sets.
- Compose now passes explicit config and secret-file env vars only (`CONFIG_PATH`, `*_FILE`, strictness toggles).
- Secret files are mounted read-only and separated by service responsibility.
- Tun profile was updated to remove `env_file` and use `TS_AUTHKEY_FILE` mount model.

Validation status:
- `docker compose -f compose.yaml -f compose.profiles.yaml config` passed.

Next:
- Complete docs, tests, and cleanup/verification for final acceptance.
