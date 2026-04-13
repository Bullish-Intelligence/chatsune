# PLAN

## Step 1
Foundation files and policy:
- Add server config example.
- Redesign `.env.example` to file-based secret refs.
- Add gitignore and secrets directory policy.

## Step 2
Bootstrap implementation:
- Add `config_loader` and `bootstrap` modules.
- Add schema validation, precedence, secret resolution.
- Add/replace unit tests.

## Step 3
Compose and image cutover:
- Switch vLLM container entrypoint to bootstrap.
- Rewire compose env + mounts to YAML + `*_FILE` contract.

## Step 4
Documentation and verification:
- Add `docs/configuration.md`.
- Update README and smoke/layout tests.
- Run tests and compose config validation.
