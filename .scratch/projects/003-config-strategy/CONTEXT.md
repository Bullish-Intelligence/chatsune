# CONTEXT

Completed Step 1 foundations:
- Added `config/server-config.example.yaml` schema baseline.
- Redesigned `.env.example` to non-sensitive runtime vars and `*_FILE` secret references.
- Added gitignore policy for `.secrets/*` and local `config/server-config.yaml`.
- Added `.secrets/.gitkeep` placeholder.

Next:
- Implement Python bootstrap/config loader with precedence, schema validation, secret resolution, and argv rendering.
