# Contributing to ASKP

First — thank you. ASKP aims to become an open standard for secure AI provider access, and a
standard is only as good as the community that scrutinizes and implements it. Whether you're
fixing a typo in the spec, proposing a new provider adapter, or reimplementing `askp/v1` in
another language, you're welcome here.

> ASKP is in **pre-alpha design phase**. Right now the most valuable contributions are
> **review of and proposals against the protocol specification and design docs.**

## Code of Conduct

This project is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you
agree to uphold it. Report unacceptable behavior to **umesh836@gmail.com**.

## Two kinds of contribution

ASKP is deliberately split into a **protocol** and a **reference implementation**
(see [`docs/README.md`](docs/README.md)). Contributions are reviewed against whichever they touch:

| You're changing… | Lives in | Held to |
|---|---|---|
| **The protocol** | [`spec/`](spec/) | Must be language-agnostic, normative (RFC 2119), and implementable from the text alone. Changes go through an **ASKP Proposal** (see below). |
| **Design docs** | [`docs/`](docs/) | Must stay consistent with the six locked decisions and the spec. |
| **Reference implementation** | `src/askp/`, `sdk/` *(later)* | Must conform to the spec and pass the conformance checklist. |

## ASKP Proposals (changes to the protocol)

Because other people will implement `askp/v1`, the protocol does **not** change casually.
Non-trivial protocol changes follow a lightweight proposal process:

1. Open an issue using the **ASKP Proposal** template describing the problem, the proposed
   change, alternatives considered, and backward-compatibility impact.
2. Discussion happens on the issue. Maintainers label it `proposal:accepted`,
   `proposal:declined`, or `proposal:needs-info`.
3. Accepted proposals are merged as a new spec **draft** (`draft-02`, …) within the current
   major version, or scheduled for the next major version if backward-incompatible.

Editorial fixes (typos, clarifications that don't change meaning) can skip the proposal and go
straight to a PR.

## Development workflow

1. **Fork** the repo and create a topic branch off `main`:
   `git checkout -b docs/clarify-scope-grammar` or `feat/anthropic-adapter`.
2. Make your change. Keep PRs **focused and small** — one concern per PR.
3. Ensure docs render (Mermaid diagrams, links) and any code passes lint/tests (when code exists).
4. Open a Pull Request using the PR template; link the issue it closes.

### Branch naming

`<type>/<short-description>` where `<type>` is one of:
`feat`, `fix`, `docs`, `spec`, `refactor`, `test`, `chore`, `ci`.

### Commit messages — Conventional Commits

We use [Conventional Commits](https://www.conventionalcommits.org/). Format:

```
<type>(<optional scope>): <description>

[optional body]

[optional footer]
```

Examples:
```
docs(spec): clarify wildcard semantics in scope matching
feat(gateway): enforce per-project rate limit before credential resolve
fix(issuer): reject tokens requesting scopes outside policy
```

Types: `feat`, `fix`, `docs`, `spec`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.
This history drives our changelog and [semantic versioning](#versioning).

### Developer Certificate of Origin (DCO)

We use the [DCO](https://developercertificate.org/) instead of a CLA. It certifies you wrote
the contribution or have the right to submit it. Sign off every commit:

```
git commit -s -m "docs(spec): clarify wildcard semantics"
```

This appends `Signed-off-by: Your Name <your@email>` to the commit message. Unsigned commits
will be asked to amend.

## Versioning

- The **protocol** is versioned `askp/vN` with drafts inside each major version (§10 of the spec).
- The **implementation and SDKs** follow [Semantic Versioning 2.0.0](https://semver.org/):
  `MAJOR.MINOR.PATCH`. While we are `0.x`, minor versions may include breaking changes; we will
  document them clearly in [CHANGELOG.md](CHANGELOG.md).

## Style

- **Docs:** Markdown, wrapped at a readable width, Mermaid for diagrams, American English,
  cross-link related docs.
- **Spec:** RFC 2119 keywords in ALL CAPS only when normative; keep it implementation-neutral.
- **Code:** Python 3.13+, `ruff` for formatting and linting, `mypy --strict` for type-checking,
  `pytest` for tests. Idiomatic, fully async, fully typed; run `make lint typecheck test`
  before opening a PR.

## Reporting bugs & requesting features

Use the issue templates. For **security vulnerabilities, do NOT open a public issue** — follow
[SECURITY.md](SECURITY.md).

## Questions

Open a [Discussion](https://github.com/umeshkedimi/askp/discussions) (once enabled) or an issue
with the `question` label.

## License of contributions

By contributing, you agree that your contributions will be licensed under the
[Apache License 2.0](LICENSE), the same license as the project.
