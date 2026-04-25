# DECISIONS — 002 Initial Implementation

1. Base runtime keeps Tailscale as stock image (`tailscale/tailscale:stable`) in default path.
   - Rationale: minimizes maintenance and follows concept recommendation for generic baseline.

2. `env_file` removed from container runtime definitions.
   - Rationale: explicit per-service environment mapping is clearer and reduces accidental secret/env leakage.

3. Kept helper Python library minimal and operationally focused.
   - Rationale: concept positions this as a deployment-first repository, with helper package as secondary tooling.

4. Static assets and tun-specific setup provided as optional overlays (`compose.profiles.yaml`).
   - Rationale: keeps default deployment path simple while preserving extension paths.

5. Added both shell entrypoint flag rendering and Python config command rendering.
   - Rationale: improves operator debugging and enables future testability around env->flag mapping.
