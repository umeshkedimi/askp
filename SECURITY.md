# Security Policy

ASKP is security-focused infrastructure: it brokers access to AI providers so that
applications never hold raw provider credentials. We take the security of the project, and of
the people who run it, seriously.

## Supported versions

ASKP is in **pre-alpha (design phase)**. There is no released, supported version yet. Once we
publish releases, this table will list which versions receive security fixes.

| Version | Supported |
|---|---|
| `0.x` (pre-release) | Best-effort, no guarantees |

## Reporting a concern

**Please do not report security issues through public GitHub issues, discussions, or pull
requests.** Public disclosure before a fix is available puts users at risk.

Instead, report privately through either of:

1. **GitHub private advisory** — go to the repository's **Security → Advisories → Report a
   vulnerability** page (GitHub Private Vulnerability Reporting). This is preferred.
2. **Email** — **umesh836@gmail.com** with the subject line `ASKP SECURITY`.

Please include, as far as you can:

- A description of the issue and the component affected (e.g. Issuer, Gateway, Vault).
- Steps to reproduce, or a proof of concept.
- The impact you believe it has (e.g. credential exposure, token forgery, tenant crossover).
- Any suggested remediation.

## What to expect

- **Acknowledgement** within **3 business days**.
- An initial assessment and severity rating within **10 business days**.
- We will keep you informed of progress and coordinate a disclosure timeline with you.
- With your consent, we will credit you in the advisory and release notes.

We follow **coordinated disclosure**: we ask that you give us a reasonable window to release a
fix before any public discussion. We will not pursue or support legal action against
researchers who act in good faith and in line with this policy.

## Scope

In scope: the ASKP protocol specification and the reference implementation in this repository
(Issuer, Gateway, Vault, Policy Engine, Admin API, SDKs).

Out of scope: vulnerabilities in upstream AI providers, third-party dependencies (report those
upstream), and issues that require a misconfigured or already-compromised host.

## Security-relevant design

The protocol's core security guarantees are written into the specification as invariants — for
example, provider credentials are never returned to clients, policy and budget are enforced
before a request reaches a provider, and tokens can be revoked instantly. See
[`spec/askp-protocol-v1.md` §3.2 and §9](spec/askp-protocol-v1.md). The full Security Model and
Threat Model are forthcoming design deliverables (Batch 2).
