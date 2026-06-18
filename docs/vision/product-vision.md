# ASKP — Product Vision

**Status:** Draft · **Audience:** Everyone · **Owner:** Umesh Kedimi

---

## 1. Name & tagline

**ASKP — AI Secure Key Protocol.**

> *OAuth for AI Provider Access.*

## 2. Mission

Create a secure, provider-agnostic protocol that lets applications, agents, services, MCP
servers, and organizations access AI providers **without ever holding raw provider API keys.**

Provider credentials live in one place. Everything else gets a **short-lived, scoped,
revocable token** — and ASKP enforces who can use which model, how much they may spend, and
keeps a complete record of every call.

## 3. The idea in one sentence

> An application presents an **ASKP token** (scoped, short-lived, references credentials it
> never sees); the **ASKP Gateway** validates it against policy and budget, swaps it for the
> real provider key server-side, and proxies the request — so the provider key never crosses
> the application boundary.

Everything ASKP does — multi-tenancy, budgets, auditing, instant revocation — hangs off that
single exchange.

## 4. North star

When a developer reaches for an AI provider, the secure path should be the **easy** path:

```bash
# Instead of pasting a long-lived sk-... key into the app:
export OPENAI_API_KEY="sk-...real-key-with-full-access-forever..."

# they point the existing SDK at ASKP and use a scoped, expiring token:
export OPENAI_BASE_URL="https://askp.mycompany.com/v1/providers/openai"
export OPENAI_API_KEY="askp_at_...10-minute-scoped-token..."
```

The existing OpenAI / Anthropic SDK keeps working. The only thing that changed is that the
app no longer holds a key that can do everything, forever, untracked.

## 5. Why now

- **Agents changed the threat model.** Autonomous agents and MCP servers now hold and *use*
  provider keys at machine speed. A leaked key is no longer "rotate it next sprint" — it's
  unbounded spend in minutes, with no attribution.
- **AI spend became real money.** Token costs are now a budget line. There is no standard way
  to cap, attribute, or govern that spend at the credential level.
- **Providers multiplied.** OpenAI, Anthropic, Gemini, Groq, OpenRouter, Bedrock, Azure,
  Ollama — every team now juggles many keys across many services with no common control plane.
- **There is no standard.** Each company reinvents a brittle internal proxy. OAuth solved the
  analogous problem for the web by becoming a *standard*, not a product.

## 6. Who it's for

| Audience | What they get |
|---|---|
| **Solo developers** | Stop pasting keys into `.env`. Get a scoped, expiring token in 5 minutes with `docker compose up`. |
| **Small teams / startups** | One vault for provider keys; per-project tokens; spend caps so a runaway loop can't drain the account. |
| **Platform / infra teams** | A real control plane: per-tenant isolation, policy, quotas, audit, instant revocation. |
| **Enterprises** | Centralized governance, attribution, cost allocation, and a self-hosted trust boundary they control. |
| **Agent & MCP builders** | A native way to give an agent *least-privilege, time-boxed, budgeted* model access instead of a raw key. |

**Adoption is bottom-up.** Enterprises don't adopt protocols — their engineers adopt them on
a side project and pull them in. So the reference implementation optimizes for the solo-dev
first-run, while the data model and protocol are multi-tenant from line one.

## 7. Design principles

1. **Security first.** Least privilege, short-lived credentials, instant revocation, defense in depth.
2. **Protocol before product.** If it can't be reimplemented from the spec alone, it isn't part of the protocol.
3. **Provider agnostic.** No provider is special. New providers are adapters, not forks.
4. **Multi-tenant from line one.** Tenant isolation is in the schema, not bolted on later.
5. **Zero trust.** The Gateway trusts nothing it cannot cryptographically and policy-verify per request.
6. **API first.** Every capability is an API; the dashboard is just a client.
7. **Open source first.** Designed in the open, self-hostable, no "open core" bait-and-switch on the core protocol.
8. **Agent & MCP native.** Non-human identities are first-class, not an afterthought.
9. **Boring where it counts.** Proven primitives (JWT, Redis, Postgres, RFC 2119 spec language) over novelty.
10. **Drop-in adoption.** Existing provider SDKs should work by changing only `base_url` and the key.

## 8. What success looks like

- A developer secures their first provider key in **under 5 minutes**, self-hosted.
- An existing OpenAI/Anthropic SDK works against ASKP with **a one-line change**.
- A second, independent implementation of `askp/v1` (e.g. in Go or Rust) **interoperates** with the reference Gateway.
- Teams cite "we put it behind ASKP" the way they say "we put it behind OAuth."
- The `spec/` is referenced by people who never run our code.

## 9. Explicit non-goals (for now)

- **Not** a model router optimizing for price/quality across providers. (Passthrough first; routing is a possible future layer.)
- **Not** an inference provider. ASKP never runs models; it governs access to those that do.
- **Not** a prompt firewall / content-moderation product. Hooks may allow it later; it is not the core mission.
- **Not** a request *normalization* layer in v1. The Gateway passes provider-native shapes through. One-shape-fits-all translation is an opt-in future feature, not a prerequisite.
- **Not** SaaS-first. Managed hosting may come later, but the canonical, fully-featured deployment is self-hosted.

## 10. Positioning

ASKP borrows the best idea from each of these and adapts it to AI infrastructure:

| Inspiration | What we take |
|---|---|
| **OAuth 2.0** | Delegated, scoped, token-based access; a spec that outlives implementations. |
| **Auth0 / Keycloak / Okta** | The "spec + great implementation" model; short-lived tokens + revocation. |
| **HashiCorp Vault** | Credentials are stored, encrypted, and *brokered* — never handed out raw. |
| **Kong / API gateways** | A policy-enforcing proxy on the hot path: auth, rate limit, observe. |
| **Stripe Connect** | Multi-tenant by design; clean SDKs; spend you can attribute and cap. |

What none of them are: **a provider-agnostic standard for delegated AI provider access.**
That is the space ASKP is built to own.

## 11. The wedge

The fastest path to adoption is the **drop-in passthrough**: an org stores its OpenAI key in
ASKP, an app changes `base_url` + key, and *nothing else breaks*. From that beachhead, scopes,
budgets, audit, and multi-provider support become features teams turn on — not migrations they
have to survive.

---

*Next: [Problem Statement](problem-statement.md) · [Core Concepts](../concepts/core-concepts.md) · [Protocol Spec](../../spec/askp-protocol-v1.md)*
