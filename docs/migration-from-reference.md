# Migration From Reference Stack

Reference code source: `.context/server`.

Key migrations:
- `docker-compose.yml` -> `compose.yaml`
- shell entrypoint flag mapping -> Python bootstrap (`src/chatsune/bootstrap.py`) + YAML loader (`src/chatsune/config_loader.py`)
- `test_connection.py` -> `scripts/smoke_test.py`
- `adapter_manager.py` moved to `scripts/adapter_manager.py` with chatsune defaults
- Tailscale Docker socket + repo bind removed from default architecture

Optional behaviors (for example static assets serving) now live in profile overlays.
