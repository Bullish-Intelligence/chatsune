# Configuration and Secret Management Strategy for a Generic vLLM + Tailscale Server

## Purpose

This document explains the tradeoffs of using a `.env` file for configuration in a generic vLLM server that runs alongside a Tailscale sidecar, and proposes a more robust configuration model.

The goal is to keep the system:

- easy to deploy with Docker Compose
- safe to operate on a single host or small fleet
- clear to debug
- flexible enough for model-specific and environment-specific behavior
- structured enough to avoid brittle shell parsing and accidental secret exposure

This document focuses on four configuration channels:

1. `.env` files
2. regular configuration files such as YAML or JSON
3. secret files
4. runtime environment overrides

The recommended design is to use all four, but for different purposes.

---

## Executive summary

A `.env` file should not be the only source of configuration in this system.

It is good for:

- simple scalar settings
- local development
- predictable Docker Compose substitution
- operator-friendly defaults

It is weak for:

- secrets
- nested or structured configuration
- long values
- certificates, tokens, and JSON payloads
- auditability and safe rotation

A stronger design is:

- use `.env` for simple non-sensitive deployment settings
- use a structured config file for application behavior
- use secret files for credentials and sensitive values
- allow explicit runtime overrides for debugging and automation

That model is a better fit for a system that combines:

- a vLLM server
- one or more model/provider credentials
- optional LoRA configuration
- Tailscale node registration and policy knobs
- possible future support for TLS assets, templates, and auth policies

---

## Why `.env` alone becomes a problem

### 1. Everything is a string

A `.env` file has no real type system.

Values like these all arrive as strings:

```env
ENABLE_LORA=false
VLLM_MAX_MODEL_LEN=32768
TS_EXTRA_ARGS=--ssh --accept-routes
LORA_MODULES=sql=/models/sql,tools=/models/tools
```

That means the application has to parse:

- booleans
- integers
- lists
- maps
- paths
- JSON blobs

This creates fragility:

- `false`, `False`, `0`, and an empty string may be treated differently
- typos in variable names are often silently ignored
- malformed list syntax is only caught late, usually during container startup
- shell parsing and application parsing may disagree

For a simple container this is manageable. For a server platform with adapters, templates, and sidecars, it becomes a recurring source of bugs.

### 2. Flat env vars do not scale to nested config

A vLLM + Tailscale setup naturally wants grouped settings:

- model selection and vLLM flags
- hardware/resource limits
- adapter configuration
- chat templates and parser settings
- Tailscale identity and networking behavior
- health and observability settings
- secret references

Flattening that into environment variables eventually leads to names like:

```env
VLLM_ENABLE_AUTO_TOOL_CHOICE=true
VLLM_TOOL_CALL_PARSER=hermes
TAILSCALE_ENABLE_HEALTH_CHECK=true
TAILSCALE_LOCAL_ADDR_PORT=9002
LORA_MODULES_JSON={"sql":"/models/sql","tools":"/models/tools"}
```

This is workable, but it becomes hard to validate, document, and evolve.

### 3. Secret values are easy to mishandle

Operators often put all credentials into `.env` because it is convenient:

```env
TS_AUTHKEY=tskey-auth-...
HF_TOKEN=hf_...
VLLM_API_KEY=...
```

That works, but it creates several risks:

- accidental commit to source control
- broad file-system exposure on the host
- leakage into container metadata or diagnostics
- secrets copied into archives and backups with the rest of the project directory
- confusion about which values are production credentials

The more `.env` becomes a catch-all, the easier it is for sensitive values to spread into places they should not be.

### 4. Docker Compose behavior can be surprising

Docker Compose uses `.env` in two related but different ways:

- for variable substitution in the Compose file
- for injecting environment variables into containers when using `environment:` or `env_file:`

These are easy to conflate.

Potential problems include:

- unset versus empty values behaving differently
- quoting assumptions that do not behave like shell scripts
- special characters such as `$`, `#`, and spaces causing unexpected parsing behavior
- an operator believing a value is reaching the container when it is only being used at Compose render time

### 5. `.env` is poor for multiline or file-like material

Some values are naturally files, not strings:

- private keys
- TLS certificates
- OAuth credentials
- JSON config snippets
- prompt templates
- chat templates

You can squeeze them into env vars with escaping or base64 encoding, but that is usually harder to read, harder to rotate, and harder to validate than mounting a file.

### 6. It is hard to express ownership and lifecycle

Different settings change at different times:

- model selection might change occasionally
- Tailscale tags might change rarely
- auth keys may rotate on a security schedule
- API keys may rotate immediately after suspected exposure
- templates may change with application behavior

A single `.env` file encourages all of these values to live together, even though they have different owners, different rotation needs, and different security sensitivity.

---

## What secret files are

A secret file is a file mounted into a container that contains a sensitive value or sensitive structured content.

Instead of storing the secret directly in an environment variable, the container receives a path to a file that contains the secret.

Examples:

- `/run/secrets/ts_authkey`
- `/run/secrets/hf_token`
- `/run/secrets/vllm_api_key`
- `/run/secrets/tls_cert.pem`
- `/run/secrets/tls_key.pem`

The content of the file might be:

- a single token string
- a password
- a private key
- a certificate
- a JSON credential object

### Why secret files are better than plain env vars for secrets

#### 1. Better separation of concerns

A secret file clearly communicates: this value is sensitive and should be handled differently from ordinary config.

That makes the system easier to reason about. Operators know that:

- `.env` is for normal deployment settings
- `/run/secrets/*` is for credentials and sensitive material

#### 2. Easier permission control

A secret file can be mounted read-only and exposed only to the containers that need it.

This is better than a project-wide `.env` file that every operator, script, or accidental backup may touch.

#### 3. Better fit for multiline or structured secrets

Some secrets are not a single line token. For example:

- PEM-encoded private keys
- service account JSON
- Tailscale serve config fragments
- custom auth material

These are naturally represented as files.

#### 4. Easier rotation workflows

A secret can be replaced independently of the main configuration file. That makes rotation cleaner:

- update the secret file
- restart the affected service
- validate behavior

This avoids editing a giant `.env` file where both ordinary config and critical secrets live together.

#### 5. Less accidental leakage in tooling

Environment variables are often surfaced by:

- process inspection
- container inspection
- crash logs
- support bundles
- debugging commands

A file path such as `/run/secrets/hf_token` is much less sensitive to expose than the secret value itself.

That does not eliminate all risk, but it reduces how often the raw value gets echoed or copied around.

---

## Important clarification: secret files are not magic

Using secret files does not automatically secure the system.

They still need correct handling:

- the source secret files on the host must have restricted permissions
- mounted secret files should be read-only
- logs must never print their contents
- application code must avoid echoing the loaded values
- backup and deployment processes must still protect the original source files

Secret files are a safer interface, not a complete security solution.

---

## Recommended configuration model

Use a layered model.

### Layer 1: `.env` for non-sensitive deployment settings

This file is for simple values that an operator may reasonably edit during setup.

Examples:

```env
COMPOSE_PROJECT_NAME=vllm-tailnet
VLLM_PORT=8000
VLLM_HOST=0.0.0.0
VLLM_MODEL=Qwen/Qwen3-4B-Instruct-2507-FP8
VLLM_MAX_MODEL_LEN=32768
VLLM_ENABLE_PREFIX_CACHING=true
TS_HOSTNAME=vllm-server
TS_EXTRA_ARGS=--advertise-tags=tag:llm
CONFIG_PATH=/app/config/server-config.yaml
HF_TOKEN_FILE=/run/secrets/hf_token
TS_AUTHKEY_FILE=/run/secrets/ts_authkey
VLLM_API_KEY_FILE=/run/secrets/vllm_api_key
```

Good candidates for `.env`:

- ports
- hostnames
- model names
- numeric limits
- feature flags
- filesystem paths
- references to secret file paths
- references to config file paths

Bad candidates for `.env`:

- raw auth keys
- private keys
- long JSON blobs
- certificates
- multiline templates

### Layer 2: structured config file for behavior

Use a YAML file such as `server-config.yaml` for behavior that is naturally grouped or nested.

Example:

```yaml
vllm:
  model: Qwen/Qwen3-4B-Instruct-2507-FP8
  host: 0.0.0.0
  port: 8000
  max_model_len: 32768
  max_num_seqs: 16
  enable_prefix_caching: true
  enable_auto_tool_choice: true
  tool_call_parser: hermes
  chat_template: /app/config/chat-templates/default.jinja

adapters:
  enabled: true
  modules:
    sql: /models/adapters/sql
    tools: /models/adapters/tools

tailscale:
  hostname: vllm-server
  extra_args:
    - --advertise-tags=tag:llm
  userspace: true
  serve_config: null

health:
  readiness_path: /health
  startup_timeout_seconds: 600

logging:
  level: info
  redact_secrets: true
```

Why a config file helps:

- nested structure is explicit
- documentation is easier
- validation is easier
- future expansion is cleaner
- operators can understand intent more quickly

### Layer 3: secret files for credentials and sensitive assets

Mount sensitive values as files.

Examples:

- `/run/secrets/ts_authkey`
- `/run/secrets/hf_token`
- `/run/secrets/vllm_api_key`
- `/run/secrets/tls_key.pem`
- `/run/secrets/oauth_client_secret.json`

The main application should read the contents of those files at startup.

### Layer 4: runtime overrides for debugging or automation

Allow explicit environment variable overrides at runtime for specific cases.

Example use cases:

- temporary model override in CI
- one-off smoke test with a different port
- local debugging with a staging token file path

These should have the highest precedence, but should be used sparingly.

---

## Recommended precedence order

The application should use a clearly documented precedence rule.

A good default:

1. explicit runtime env vars
2. secret file values for secret-backed settings
3. structured config file values
4. `.env` defaults
5. internal application defaults

For example:

- if `VLLM_MODEL` is set at runtime, use it
- otherwise read `vllm.model` from `server-config.yaml`
- otherwise fall back to an internal default or fail validation

For a secret-backed setting such as the Hugging Face token:

1. if `HF_TOKEN` is set explicitly, use it only for debug or emergency override
2. otherwise if `HF_TOKEN_FILE` is set, read the token from that file
3. otherwise fail if the selected model requires authentication

This pattern gives the system flexibility while preserving a preferred secure path.

---

## Integration design for the vLLM + Tailscale stack

The cleanest design is to have a small startup layer in the vLLM container that loads and validates configuration before starting the vLLM server.

### Components

#### 1. Docker Compose

Compose is responsible for:

- mounting the config file
- mounting secret files
- setting simple environment variables
- wiring the vLLM container to the Tailscale sidecar network
- declaring volumes and healthchecks

#### 2. Entrypoint script or small Python bootstrap

The bootstrap layer should:

- load `.env`-supplied references such as `CONFIG_PATH` and `*_FILE`
- read the structured config file
- read secret files
- validate types and required fields
- construct the final vLLM command
- export only the minimal env vars needed for child processes
- avoid printing secret contents

A small Python bootstrap is usually better than a shell-only parser because it can validate and merge config safely.

#### 3. vLLM runtime

The vLLM process should receive:

- concrete command-line flags
- any truly necessary environment variables
- mounted model/config/template directories

#### 4. Tailscale sidecar

The Tailscale sidecar should receive:

- `TS_AUTHKEY_FILE` or another secret-file-backed credential path
- non-sensitive node settings from env or config
- persistent state volume

The Tailscale container should not need access to unrelated application secrets.

---

## Example Compose integration

Below is an illustrative Compose pattern.

```yaml
services:
  tailscale:
    image: tailscale/tailscale:latest
    hostname: ${TS_HOSTNAME}
    environment:
      TS_STATE_DIR: /var/lib/tailscale
      TS_AUTHKEY_FILE: /run/secrets/ts_authkey
      TS_EXTRA_ARGS: ${TS_EXTRA_ARGS:-}
      TS_USERSPACE: ${TS_USERSPACE:-true}
    volumes:
      - tailscale-state:/var/lib/tailscale
      - ./secrets/ts_authkey:/run/secrets/ts_authkey:ro
    healthcheck:
      test: ["CMD", "tailscale", "status"]
      interval: 30s
      timeout: 10s
      retries: 5

  vllm:
    build:
      context: .
      dockerfile: images/vllm/Dockerfile
    network_mode: service:tailscale
    depends_on:
      tailscale:
        condition: service_started
    environment:
      CONFIG_PATH: /app/config/server-config.yaml
      HF_TOKEN_FILE: /run/secrets/hf_token
      VLLM_API_KEY_FILE: /run/secrets/vllm_api_key
      VLLM_MODEL: ${VLLM_MODEL}
      VLLM_PORT: ${VLLM_PORT:-8000}
    volumes:
      - ./config/server-config.yaml:/app/config/server-config.yaml:ro
      - ./config/chat-templates:/app/config/chat-templates:ro
      - ./secrets/hf_token:/run/secrets/hf_token:ro
      - ./secrets/vllm_api_key:/run/secrets/vllm_api_key:ro
      - model-cache:/root/.cache/huggingface
    command: ["python", "-m", "vllm_tailnet.bootstrap"]

volumes:
  tailscale-state:
  model-cache:
```

This pattern keeps the responsibilities separated:

- `.env` supplies simple values
- files provide secrets and structured config
- the bootstrap resolves everything into the final runtime state

---

## Directory layout recommendation

A clean repository layout could look like this:

```text
.
├── .env.example
├── compose.yaml
├── config/
│   ├── server-config.yaml
│   └── chat-templates/
│       └── default.jinja
├── secrets/
│   ├── .gitignore
│   ├── hf_token
│   ├── ts_authkey
│   └── vllm_api_key
├── images/
│   └── vllm/
│       ├── Dockerfile
│       └── docker-entrypoint.py
└── src/
    └── vllm_tailnet/
        ├── bootstrap.py
        ├── config.py
        └── models.py
```

### Notes on the `secrets/` directory

The `secrets/` directory should:

- be excluded from version control
- have restrictive host permissions
- contain only runtime secret material
- not contain generated logs or caches

Example `.gitignore` inside `secrets/`:

```gitignore
*
!.gitignore
```

That ensures the directory exists in the repo, but the contents are never committed.

---

## How the bootstrap should work

A robust bootstrap process is central to making this system safe and maintainable.

### Step 1: load non-sensitive env vars

Read variables such as:

- `CONFIG_PATH`
- `VLLM_MODEL`
- `VLLM_PORT`
- `TS_HOSTNAME`
- `HF_TOKEN_FILE`
- `TS_AUTHKEY_FILE`
- `VLLM_API_KEY_FILE`

### Step 2: load the structured config file

Parse `server-config.yaml` and validate it against a schema.

This is where a typed config model helps. The bootstrap should reject invalid values early.

Examples of validation:

- `port` must be an integer in a valid range
- `max_model_len` must be positive
- adapter paths must exist if adapters are enabled
- mutually incompatible flags should fail fast

### Step 3: load secret files

For each secret-backed setting:

- check whether a `*_FILE` path is provided
- verify the file exists and is readable
- read its contents
- trim only the final newline if appropriate
- keep the value in memory only as long as necessary
- never log the raw contents

For example:

- `HF_TOKEN_FILE` loads the Hugging Face token used for authenticated model pulls
- `TS_AUTHKEY_FILE` loads the Tailscale auth key for node registration
- `VLLM_API_KEY_FILE` loads the API key for the OpenAI-compatible endpoint

### Step 4: merge precedence layers

Resolve the final values based on the precedence rules.

### Step 5: construct the runtime command

Example output command:

```bash
vllm serve Qwen/Qwen3-4B-Instruct-2507-FP8 \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 32768 \
  --enable-prefix-caching \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

If an API key is required by the child process, pass it in memory or via the minimal required environment variable, not by writing a new file containing the secret.

### Step 6: start and monitor

After launch:

- expose readiness and liveness checks
- redact secrets in logs
- fail clearly when secret files are missing or malformed

---

## Specific secret files in this system

### 1. `ts_authkey`

This file contains the Tailscale auth key used to register the sidecar node.

Why it should be a secret file:

- it is a credential, not a normal setting
- it may need periodic rotation
- it should not be echoed in logs or stored alongside normal app config

Integration:

- mounted into the Tailscale container only
- referenced through `TS_AUTHKEY_FILE=/run/secrets/ts_authkey`
- not exposed to the vLLM container unless there is a specific need

### 2. `hf_token`

This file contains the Hugging Face token used to pull gated or private models.

Why it should be a secret file:

- it is sensitive
- it should be restricted to the workload that fetches models
- it may differ by environment or model source

Integration:

- mounted into the vLLM container only
- referenced through `HF_TOKEN_FILE=/run/secrets/hf_token`
- read by bootstrap and exported only if required by the downstream tooling

### 3. `vllm_api_key`

This file contains the API key required for clients calling the OpenAI-compatible server.

Why it should be a secret file:

- it protects access to the model API
- it may rotate more often than ordinary deployment config
- it should not be committed or mixed with public defaults

Integration:

- mounted into the vLLM container only
- bootstrap reads it and passes it to the vLLM server configuration
- logs should never print whether the key value is set beyond a boolean statement like `api_key_configured=true`

### 4. TLS certificate and private key files

If TLS termination is ever handled in this stack directly, certificate and private key material should be mounted as files.

Why they should be files:

- they are multiline assets
- they already exist in file formats that tools understand
- private keys especially should never be embedded into env vars

### 5. Future provider credentials

If the stack later supports:

- object storage for model artifacts
- external metrics or logging backends
- cloud KMS or vault integration

those credentials should also be file-backed where feasible.

---

## Security and operational considerations

### Host permissions

The source files in `./secrets` should have restrictive permissions.

Examples of good practice:

- owned by the deployment user or service account
- readable only by that account
- not world-readable
- excluded from broad archive and backup patterns unless intentionally protected

### Container mount scope

Mount each secret only into the container that needs it.

Do not mount all secrets into all services by default.

For example:

- Tailscale should receive `ts_authkey`
- vLLM should receive `hf_token` and `vllm_api_key`
- an optional static file server should receive neither unless required

### Logging discipline

The bootstrap and application logs should:

- never print secret values
- avoid printing full environment dumps
- avoid stack traces that include token strings
- redact file contents in validation errors

Good error:

- `failed to read HF_TOKEN_FILE at /run/secrets/hf_token: permission denied`

Bad error:

- `HF token abcdef123... is invalid`

### Rotation strategy

A reasonable operational model is:

1. replace the file contents securely
2. restart the affected service
3. verify readiness and authentication behavior
4. invalidate old credentials upstream if applicable

Document which secrets can be rotated independently and which require coordinated changes.

### Backups

If project directories are backed up automatically, ensure secret directories are handled intentionally.

Do not assume `.gitignore` protects secrets from backups. It only protects them from git.

### Support bundles and diagnostics

If the system ever adds a `debug` or `support` command, make sure it does not collect:

- secret file contents
- full environment dumps
- unredacted config snapshots

---

## Validation recommendations

The system should fail fast on startup with clear messages.

Recommended checks:

### `.env` and env-derived checks

- required simple variables are present
- numeric values parse correctly
- boolean flags normalize correctly
- referenced paths are syntactically valid

### structured config checks

- schema validation passes
- unsupported keys are rejected or warned
- model/adapters/settings combinations are valid

### secret file checks

- file exists
- file is readable
- file content is non-empty when required
- file content matches expected basic shape where possible

Examples:

- `TS_AUTHKEY_FILE` must not be empty
- `HF_TOKEN_FILE` must be present if the selected model needs authentication
- TLS key/cert paths must both exist if TLS is enabled

---

## What should live where

A practical policy table:

| Kind of value | Best location | Why |
|---|---|---|
| port number | `.env` or config file | simple, non-sensitive |
| model name | `.env` or config file | simple deployment choice |
| max sequence length | config file | typed behavior setting |
| LoRA module map | config file | structured data |
| Tailscale hostname | `.env` | simple deployment identity |
| Tailscale auth key | secret file | sensitive credential |
| Hugging Face token | secret file | sensitive credential |
| API key for inference endpoint | secret file | sensitive credential |
| PEM private key | secret file | multiline sensitive asset |
| chat template path | config file | behavior reference |
| chat template contents | normal file mount | not a secret, but file-shaped |
| debug override for model | runtime env | temporary override |

---

## Suggested implementation plan

### Phase 1: introduce the config split

- keep `.env` for simple values only
- add `server-config.yaml`
- add `secrets/` directory conventions
- add a bootstrap layer that supports `*_FILE`

### Phase 2: validate and document

- implement typed config validation
- add startup checks for missing secret files
- add operator documentation and examples
- add `.env.example` with comments and safe defaults

### Phase 3: improve operations

- add redaction-aware diagnostics
- add health and readiness checks
- add a rotation runbook
- add optional support for Docker secrets or external secret managers

### Phase 4: external secret backends

If the repo later grows beyond small-host Compose deployments, add optional integrations for:

- Docker Swarm secrets
- Kubernetes secrets
- HashiCorp Vault
- cloud secret managers

The internal application contract should stay the same:

- it reads a secret value from a file path or explicit env override

That way the external secret backend can change without changing the core bootstrap logic.

---

## Final recommendation

For this vLLM + Tailscale server, do not rely on a `.env` file as the sole configuration system.

Use this split:

- `.env` for simple non-sensitive deployment settings
- `server-config.yaml` for structured server behavior
- secret files for credentials and sensitive assets
- runtime env overrides only for explicit operational needs

That gives you:

- better safety for credentials
- better clarity for operators
- cleaner startup validation
- easier future growth as the stack becomes more generic and reusable

The key architectural rule is simple:

**ordinary settings should be editable, structured behavior should be typed, and secrets should be file-backed.**
