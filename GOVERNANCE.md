# ASKP Governance

This document describes how decisions are made in the ASKP project. ASKP aims to become an open
standard, so governance is written down from the start — a standard needs a clear, predictable
process for how it evolves.

## Project structure

ASKP is two things under one roof:

- **The protocol** — a versioned specification in [`spec/`](spec/) that anyone may implement.
- **The reference implementation** — the Go code in `cmd/`, `internal/`, `pkg/` (and future SDKs in `sdk/`) that conforms to the protocol.

The protocol is intended to outlive any single implementation. Changes to it are held to a
higher bar than changes to the implementation.

## Roles

| Role | Who | Responsibility |
|---|---|---|
| **Lead Maintainer (BDFL for now)** | Umesh Kedimi | Final decision authority during the early phase. Stewards the vision and the protocol. |
| **Maintainers** | Added over time | Review and merge PRs, triage issues, shepherd proposals. |
| **Contributors** | Anyone | Submit issues, PRs, proposals, reviews. |

While ASKP is young, it operates under a **benevolent-dictator** model with the Lead Maintainer
as the final authority. As the community grows, we intend to move toward a **Technical Steering
Committee** with a documented voting process. This document will be updated when that happens.

## Decision making

We prefer **lazy consensus**: a proposal that sees no sustained objection within a reasonable
review window is accepted. When there is disagreement:

1. Discussion happens in the open (issue or discussion thread).
2. Maintainers seek consensus.
3. If consensus cannot be reached, the Lead Maintainer decides, and records the rationale.

## Changing the protocol

Protocol changes follow the **ASKP Proposal** process described in
[CONTRIBUTING.md](CONTRIBUTING.md):

- Backward-**compatible** changes (new providers, scopes, optional claims, clarifications) may be
  accepted into a new **draft** of the current major version.
- Backward-**incompatible** changes are deferred to the next **major** version (`askp/v2`) and
  require explicit Lead Maintainer sign-off.
- The protocol's stability commitments (core invariants and the error-code vocabulary) will not
  change incompatibly within a major version.

## Changing the implementation

Implementation and SDK changes follow ordinary code review:

- At least one maintainer approval is required to merge.
- Changes must conform to the protocol (the conformance checklist in the spec appendix).
- Breaking changes while in `0.x` are allowed but must be documented in
  [CHANGELOG.md](CHANGELOG.md).

## Adding maintainers

Contributors who show sustained, high-quality involvement — reviews, well-scoped PRs,
thoughtful proposals — may be invited to become maintainers by the Lead Maintainer. There is no
fixed quota; trust is earned through the work.

## Code of Conduct

All participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

## Amending this document

Changes to governance are themselves proposals, made via PR against this file, and require Lead
Maintainer approval.
