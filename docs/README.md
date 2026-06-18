# ASKP Documentation

This directory holds the ASKP design package. Documents are produced **incrementally, in
batches**. Each batch is internally consistent and builds on the previous one.

## Foundational design decisions

Before any document was written, six load-bearing decisions were locked. They are recorded
here because every document inherits them:

| # | Decision | Choice |
|---|---|---|
| 1 | Protocol vs. implementation | **Hard separation.** `spec/` is language-agnostic and is the headline. `services/` merely implements it. |
| 2 | Access token model | **Hybrid:** short-lived signed JWT (~10 min) + Redis revocation list for instant kill; opaque long-lived refresh token. |
| 3 | Day-one user | **Solo devs / small teams** for DX; **multi-tenant schema from line one** so enterprises grow in without a rewrite. |
| 4 | Hosting | **Self-hosted is canonical**; managed SaaS comes later on the same code. Operator ≠ protocol author. |
| 5 | Gateway behavior | **Transparent passthrough** of provider-native request shapes (incl. SSE streaming); normalization is a later, opt-in layer. |
| 6 | Scope grammar | **Hierarchical, colon-delimited, OAuth-familiar:** `provider:<name>:model:<model>:<capability>`. |

## Deliverables roadmap

| Batch | Documents | Status |
|---|---|---|
| **1 — Foundations** | Product Vision, Problem Statement, Core Concepts, Protocol Spec Draft, System Architecture | ✅ this milestone |
| 2 — Security & tokens | Security Model, Threat Model, Token Structure, Permission Model, Scope Design | ⬜ planned |
| 3 — Data & API | Database/ER Design, Multi-Tenant Design, API Design, OpenAPI Spec, Microservice Boundaries | ⬜ planned |
| 4 — Runtime & ops | Deployment Architecture, Docker, Kubernetes, Event Flow, Cost Tracking, Provider Abstraction | ⬜ planned |
| 5 — Ecosystem | Python SDK, JS SDK, MCP Integration, Agent Auth, Roadmap, OSS scaffolding (monorepo, CONTRIBUTING, versioning) | ⬜ planned |

## Layout

```
docs/
  vision/        product vision, problem statement
  concepts/      core concepts & domain glossary
  architecture/  system & component architecture
spec/
  askp-protocol-v1.md   the normative protocol (RFC-style)
```
