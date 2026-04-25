# ASSUMPTIONS — 002 Initial Implementation

- This repo is now the source-of-truth standalone implementation (not a copy of Remora server).
- `CHATSUNE_CONCEPT.md` defines architectural direction for v1 implementation.
- Docker Compose is the primary deployment interface for initial milestones.
- Tailscale sidecar + `network_mode: service:tailscale` remains the baseline connectivity model.
- Optional features (static assets/admin extras) should start as overlays/examples, not base defaults.
