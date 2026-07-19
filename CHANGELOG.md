# Changelog

All notable changes to ASKP are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for the implementation
and SDKs once released. The **protocol** is versioned separately as `askp/vN` with drafts
(see [`spec/askp-protocol-v1.md` §10](spec/askp-protocol-v1.md)).

## [Unreleased]

### Changed
- **Reference implementation relanguaged to Go.** The reference implementation is now written
  in **Go** (Gin · GORM · Redis · Viper · Zap · Prometheus · OpenTelemetry) and lives in
  `cmd/`, `internal/`, and `pkg/`. The protocol spec (`spec/`) and design docs are unchanged
  and remain language-agnostic; only the implementation language and its production tooling
  changed. The previous Python/FastAPI implementation (Increments 0–5 below) is retired but
  preserved in git history under the `python-reference-final` tag. Docs, `.env.example`, the
  architecture technology mapping (§10), and contribution/governance references were updated
  to match the Go layout.

### Added
- **Reference implementation (Go) — Increment 0: project foundation.**
  - Go module `github.com/umeshkedimi/askp` with a clean-architecture layout
    (`cmd/askp`, `internal/{config,logging,middleware,metrics,api,app,cli}`, `pkg/apierrors`).
  - Viper-backed configuration (`ASKP_` env prefix) with fail-closed validation; Zap
    structured logging (JSON in prod, console in dev).
  - Gin HTTP server via a dependency-injected app factory: request-id / recovery / logging
    middleware, Prometheus `/metrics`, `/health` (dependency-free liveness) and `/ready`
    (checker-based readiness), graceful shutdown, and the `askp serve` cobra command.
  - Stable error vocabulary (`pkg/apierrors`, spec §8) as an importable, framework-agnostic
    package.
  - Tooling: multi-stage distroless Dockerfile, `golangci-lint` config, Makefile, and a
    GitHub Actions CI workflow (build · vet · test · lint).

### Added (Python reference — retired, kept for history)
- **Reference implementation — Increment 5: control plane (Issuer + Admin APIs).**
  - `POST /v1/tokens` — mints scoped Access Tokens via the Issuer (OAuth-style response).
  - `PUT`/`DELETE /v1/admin/providers/{provider}/credential` — write/rotate/delete Vault
    credentials; write-only (no GET) per §7.4.
  - `POST /v1/admin/revocations` — revoke a `jti` and/or token-family `tf` (§7.3).
  - All gated by `require_admin` (constant-time bearer-key check, `ASKP_ADMIN_API_KEY`); fails
    closed with 503 when unconfigured. Placeholder for real principal auth (a later batch).
  - Config: `admin_api_key`.
- **Reference implementation — Increment 4: the Vault (encrypted credentials).**
  - Envelope encryption (AES-256-GCM): a master KEK wraps a per-credential DEK, with
    `AAD="<org>:<provider>"` binding each ciphertext to its tenant (`askp.security.encryption`).
  - `ProviderCredential` model + Alembic migration 0002 — stores ciphertext only, keyed by a
    unique `(org, provider)`.
  - `askp.vault.Vault`: `put()` encrypts and upserts (write/rotate); `resolve()` decrypts
    in-boundary and satisfies the Gateway's `CredentialResolver` protocol, replacing the
    Increment 3 environment-variable placeholder.
  - Config: `vault_kek` (required in production; ephemeral in dev).
- **Reference implementation — Increment 3: the Gateway (pre-flight pipeline + proxy).**
  - Scope grammar + matching with `*` wildcards and default-deny (`askp.security.scopes`, §5).
  - Redis-backed revocation list with self-expiring entries (`askp.security.revocation`, §7.3).
  - Provider registry mapping native paths to capabilities and holding upstream URL + auth
    conventions (OpenAI Bearer, Anthropic `x-api-key`) (`askp.gateway.providers`, §5.4/§6.1).
  - Proxy route `POST /v1/providers/{provider}/{path}` running the §6.3 pipeline (verify token →
    revocation → resolve operation → scope authorize → resolve credential in-org → stream
    upstream), substituting the provider credential for the ASKP token (INV-1) and passing SSE
    through unbuffered (§6.6).
  - Stable §8 error vocabulary; `CredentialResolver` Protocol with an env-backed placeholder
    pending the Vault.
- **Reference implementation — Increment 2: the Issuer (token core).**
  - Ed25519 (`EdDSA`) signing keys with a deterministic `kid`; PEM loading or ephemeral
    generation (`askp.security.keys`).
  - `TokenIssuer` mints short-lived (≤15 min), `askp_at_`-prefixed JWT Access Tokens carrying
    the spec §4.2 claim set, and verifies them with the algorithm pinned to `EdDSA`
    (rejecting `alg:none` and alg-confusion forgeries).
  - Config: `issuer`, `gateway_audience`, `access_token_ttl_seconds`, `signing_key_path`.
- **Reference implementation — Increment 1: data layer.**
  - Async SQLAlchemy (SQLModel) engine + session factory; `get_session` dependency.
  - Async Redis client (revocation list / counters store) with health check.
  - Readiness probe (`/ready`) now verifies PostgreSQL and Redis connectivity.
  - Tenancy models: `Organization` and `Project` (UUID PKs, TIMESTAMPTZ timestamps,
    org-scoped unique project slug).
  - Alembic async migrations + initial schema (verified zero drift via `alembic check`).
  - `docker-compose.yml` for local Postgres + Redis.
- **Reference implementation — Increment 0: project foundation.**
  - uv project, `src/` layout, Pydantic Settings config, structlog logging.
  - FastAPI app-factory with lifespan; `/health` and `/ready` endpoints; `askp serve` CLI.
  - Test suite (pytest), lint (ruff), and type-checking (mypy --strict).
- **Batch 1 — Foundational design package.**
  - Product Vision (`docs/vision/product-vision.md`).
  - Problem Statement (`docs/vision/problem-statement.md`).
  - Core Concepts and normative glossary (`docs/concepts/core-concepts.md`).
  - ASKP Protocol Specification v1, draft-01 (`spec/askp-protocol-v1.md`) — roles, token
    format, scope grammar, gateway validation pipeline, revocation, errors, security
    considerations, conformance checklist.
  - System Architecture (`docs/architecture/system-architecture.md`).
  - Recorded the six foundational design decisions (`docs/README.md`).
- **Open-source scaffolding.** Apache-2.0 `LICENSE`, `NOTICE`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `SECURITY.md`, `GOVERNANCE.md`,
  GitHub issue/PR templates, `CODEOWNERS`, and `.gitignore`.

### Notes
- ASKP is **pre-alpha**. The protocol is a working draft and is not yet stable. Nothing here is
  released or production-ready.

---

<!--
Release sections will be added here as versions are tagged, e.g.:

## [0.1.0] - YYYY-MM-DD
### Added / Changed / Deprecated / Removed / Fixed / Security
-->

[Unreleased]: https://github.com/umeshkedimi/askp/commits/main
