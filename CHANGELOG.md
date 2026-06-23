# Changelog

All notable changes to ASKP are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for the implementation
and SDKs once released. The **protocol** is versioned separately as `askp/vN` with drafts
(see [`spec/askp-protocol-v1.md` §10](spec/askp-protocol-v1.md)).

## [Unreleased]

### Added
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
