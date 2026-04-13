# Security

Default security posture:
- No public port publishing in the base compose stack.
- Tailnet-private access via sidecar topology.
- No Docker socket mount in baseline services.
- Secrets expected via `.env` (not committed).

If using tun mode, review additional capability and device requirements before enabling.
