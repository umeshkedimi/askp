# ASKP — AI Secure Key Protocol

> **OAuth for AI Provider Access.**
> Applications should never hold raw OpenAI, Anthropic, or other provider API keys.

ASKP is an **open protocol** plus a **reference implementation** that lets applications,
agents, services, and MCP servers access AI providers through **short-lived, scoped tokens**
instead of long-lived provider credentials.

Organizations store provider credentials once, inside ASKP. ASKP issues scoped access tokens.
Applications authenticate with ASKP tokens — never with the underlying provider key. ASKP
validates permissions, enforces budgets and quotas, records every request, and forwards the
call to the provider.

```
App ──ASKP token──▶ ASKP Gateway ──real provider key──▶ OpenAI / Anthropic / …
                         │
                  policy · budget · audit · revocation
```

---

## Why ASKP exists

Today, provider API keys are pasted into `.env` files, baked into containers, shared across
services, and handed to autonomous agents. A single leaked key is a long-lived, full-access,
unattributable credential that can run up unbounded cost. There is no standard for scoping,
attributing, budgeting, or instantly revoking AI provider access.

ASKP aims to be for AI providers what OAuth became for the web: a **provider-agnostic
standard** for delegated, least-privilege access.

See [`docs/vision/problem-statement.md`](docs/vision/problem-statement.md) for the full problem analysis.

---

## Two artifacts, one project

| Artifact | Lives in | What it is |
|---|---|---|
| **The ASKP Protocol** | [`spec/`](spec/) | A language-agnostic, versioned specification. Anyone can implement it in any language and interoperate. |
| **The Reference Implementation** | `services/` *(later batches)* | A Python / FastAPI implementation: Issuer, Vault, Gateway, Policy Engine. Proves the protocol and gives you something to run on day one. |

The protocol is the headline. The implementation proves it.

---

## Documentation

**Batch 1 — Foundations (this milestone)**

1. [Product Vision](docs/vision/product-vision.md)
2. [Problem Statement](docs/vision/problem-statement.md)
3. [Core Concepts](docs/concepts/core-concepts.md)
4. [ASKP Protocol Specification — v1 Draft](spec/askp-protocol-v1.md)
5. [System Architecture](docs/architecture/system-architecture.md)

See [`docs/README.md`](docs/README.md) for the full deliverables roadmap.

---

## Status

🚧 **Pre-alpha — design phase.** The protocol is a working draft (`askp/v1`, draft-01).
Nothing here is stable yet. We are designing in the open.

## Contributing

ASKP is built in public and welcomes contributors — especially review of and proposals against
the protocol spec. Start here:

- [CONTRIBUTING.md](CONTRIBUTING.md) — workflow, Conventional Commits, DCO sign-off, the ASKP Proposal process
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Contributor Covenant 2.1
- [GOVERNANCE.md](GOVERNANCE.md) — how decisions are made
- [SECURITY.md](SECURITY.md) — report a vulnerability privately (please do **not** open a public issue)

## License

Licensed under the [Apache License 2.0](LICENSE). Contributions are accepted under the same
license. The Apache-2.0 patent grant is deliberate: it suits a project intended to become an
open standard.
