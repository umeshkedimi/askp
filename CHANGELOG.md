# Changelog

All notable changes to ASKP are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for the implementation
and SDKs once released. The **protocol** is versioned separately as `askp/vN` with drafts
(see [`spec/askp-protocol-v1.md` §10](spec/askp-protocol-v1.md)).

## [Unreleased]

### Added
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
