# ASKP — Problem Statement

**Status:** Draft · **Audience:** Engineers, security architects, decision makers

---

## 1. The shape of the problem

AI provider access today is secured the way web API access was secured **before OAuth**: with
long-lived, full-access, shared secrets pasted wherever they're needed.

A typical OpenAI or Anthropic key is:

- **Long-lived** — it works until a human remembers to rotate it.
- **Full-access** — it can call any model, any endpoint, with no scoping.
- **Unattributable** — every request looks identical; you cannot tell which app, user, or agent made it.
- **Unbudgeted** — there is no per-key spend cap; a loop or a leak can run up unbounded cost.
- **Widely copied** — it ends up in `.env` files, CI secrets, container images, agent configs, and Slack messages.
- **Slow to revoke** — "revoking" means rotating the single shared key and redeploying everything that used it.

This was tolerable when one backend called one model occasionally. It is **not** tolerable now
that fleets of services, autonomous agents, and MCP servers hold and use these keys at machine
speed, across many providers, spending real money.

## 2. Concrete failure modes

These are the situations ASKP exists to prevent:

1. **The leaked key.** A provider key is committed to a public repo, pasted into a log, or
   exfiltrated from a compromised container. It is valid, full-access, and long-lived. By the
   time anyone notices, an attacker has run up thousands of dollars of inference — and you
   can't even prove which calls were theirs.

2. **The runaway agent.** An autonomous agent enters a retry loop or is prompt-injected into
   making expensive calls. With a raw key it has no spend ceiling and no scope limit. It burns
   the budget before a human is in the loop.

3. **The over-privileged service.** A small internal tool only needs `gpt-4o-mini` for
   classification. It holds a key that can also call the most expensive models, fine-tuning,
   and the files/assistants APIs — far more authority than its job requires.

4. **The blast radius of rotation.** You suspect a key is compromised. To revoke it you must
   rotate the *one shared key* and redeploy *every* service that used it. Fear of the outage
   delays the rotation — exactly when speed matters most.

5. **The attribution void.** Finance asks "which team/app/customer drove last month's
   $40k OpenAI bill?" There is no answer, because every request used the same anonymous key.

6. **The multi-provider sprawl.** The org now uses OpenAI, Anthropic, and Groq. That's three
   key-management stories, three rotation procedures, three places a secret can leak, and zero
   common policy.

7. **The MCP / tool hand-off.** An MCP server or third-party tool needs model access. Today
   that means handing it a raw provider key — granting a piece of software you don't control
   full, lasting access to your provider account.

## 3. Why existing tools don't solve it

People reach for adjacent tools. Each covers part of the problem and leaves the core gap open:

| Tool class | What it does | Why it's not enough |
|---|---|---|
| **Secrets managers** (Vault, AWS/GCP Secret Manager, Doppler) | Store and distribute secrets securely. | They still *hand the raw key to the app*. Once delivered, it's long-lived, full-access, unscoped, and unattributable. They secure storage, not *use*. |
| **API gateways** (Kong, Apigee, NGINX) | Auth, rate-limit, proxy generic HTTP. | Provider-agnostic in the wrong way — no concept of AI providers, models, token-cost budgets, or provider credential brokering. You'd build all the AI-specific logic yourself. |
| **LLM proxies / routers** (various OSS) | Route requests across providers; sometimes track cost. | Built for routing and cost optimization, not as a *security protocol*. Typically single-tenant, weak on credential custody, scoping, instant revocation, and audit. Not a standard. |
| **Provider-native controls** (project keys, usage limits) | Some per-key limits, per-project keys. | Provider-specific, inconsistent, not portable across providers, and not a control plane you own. No cross-provider standard. |
| **DIY internal proxy** | Exactly what teams build. | Reinvented at every company, brittle, undocumented, unowned, insecure by default, and impossible to standardize an ecosystem around. |

The honest summary: **secrets managers secure the key at rest; gateways secure the request in
transit; nobody secures the *delegation of provider access itself.*** That delegation layer —
scoped, short-lived, attributable, budgeted, revocable, provider-agnostic — is missing. It is
exactly the layer OAuth introduced for the web.

## 4. The gap, stated precisely

There is **no open standard** for:

> Granting a piece of software *least-privilege, time-boxed, budgeted, attributable, and
> instantly-revocable* access to an AI provider, without giving it the provider's raw
> credentials — in a way that is portable across providers and implementable by anyone.

That gap is the entire reason ASKP exists.

## 5. Requirements that follow

The problem analysis dictates the requirements. ASKP must provide:

**Credential custody**
- R1. Provider credentials are stored encrypted and are **never returned to clients**.
- R2. The provider key crosses the trust boundary only between the Gateway and the provider.

**Delegated, least-privilege access**
- R3. Access is granted via **short-lived tokens**, not long-lived keys.
- R4. Tokens are **scoped** — to provider, model, and capability — and default to least privilege.
- R5. Tokens are bound to a tenant (organization/project) and an identity (user/agent).

**Governance on the hot path**
- R6. Every request is checked against **policy** (is this scope allowed?) before forwarding.
- R7. Every request is checked against **budget and rate limits** (per token, project, org).
- R8. A request that violates policy or budget is rejected *before* it reaches the provider.

**Accountability**
- R9. Every request is **attributable** to an org, project, and identity, and is **audited**.
- R10. **Usage and cost** are tracked per token, project, and organization.

**Control**
- R11. Any token can be **revoked instantly**, without rotating provider keys or redeploying.
- R12. Revocation takes effect on the very next request.

**Portability & openness**
- R13. The mechanism is **provider-agnostic**; new providers are adapters.
- R14. The mechanism is an **open, versioned spec** anyone can implement and interoperate with.

**Adoptability**
- R15. Existing provider SDKs work with **a one-line change** (`base_url` + token).
- R16. First secure call is achievable **self-hosted, in minutes.**

## 6. Out of scope (problem boundary)

To keep the mission sharp, ASKP does **not** try to solve:

- Choosing the *best/cheapest* model for a request (routing/optimization).
- Running inference itself.
- Prompt-level content safety / moderation (may be a future hook, not the core problem).
- Replacing your secrets manager for *non-provider* secrets.

These are deliberately excluded so the core delegation problem is solved well rather than
everything solved poorly.

---

*Next: [Core Concepts](../concepts/core-concepts.md) — the vocabulary and domain model that the requirements above turn into.*
