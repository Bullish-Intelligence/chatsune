# CONTEXT

Completed Step 2 bootstrap implementation:
- Added `src/chatsune/config_loader.py` with YAML loading, schema checks, defaults merge, secret-file resolution, and vLLM argv rendering.
- Added `src/chatsune/bootstrap.py` runtime entrypoint with redacted command logging and `execvpe` handoff.
- Updated CLI/config exports to use the new loader model.
- Added unit tests for unknown-key rejection, secret precedence/conflicts, command rendering, and redaction.

Validation status:
- `python -m compileall -q src tests scripts` passed.
- `python -m pytest ...` could not run because `pytest` is not installed in this environment.

Next:
- Cut over Compose + image entrypoint to bootstrap and `*_FILE` mounts.
