# ASSUMPTIONS

- Deployment target is personal hardware on a private Tailnet.
- Primary operator is trusted and has shell access to host.
- Secrets should not be committed, echoed, or stored in `.env`.
- Compose remains the deployment entrypoint.
- vLLM runtime behavior should be YAML-driven, not broad env-driven.
