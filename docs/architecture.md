# Architecture

Chatsune runs two default services:
- `tailscale`: joins the tailnet and owns network identity.
- `vllm`: inference runtime sharing tailscale's network namespace.

The `vllm` service is reachable through Tailscale DNS/IP only by default.

Optional features are provided via compose profiles in `compose.profiles.yaml`.
