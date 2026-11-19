---
id: "000"
title: "SDD bootstrap and repository governance"
status: in-progress
owner: "Ge Rui Sen"
created: 2026-11-19
updated: 2026-11-19
branch: "docs/000-sdd-bootstrap"
---

# SDD bootstrap and repository governance

## Context

Strictr is a new repository with only a license, a Python `.gitignore`, and
local vision notes. Before product code is written, the project needs a working
SDD protocol: governance documents, spec and blueprint templates, a traceability
check, a test strategy, and CI that can verify them.

This is a process change, not a product feature. It is the first dogfood of the
protocol.

## Goals

- Establish a small, enforceable SDD workflow for a solo developer with an AI
  agent.
- Make every later change traceable from spec to branch, commit, PR, test, and
  release.
- Keep the process lighter than the change it governs.

## Non-goals

- No product CLI or verification engine.
- No Docker sandbox, daemon pool, MCP server, fuzzing, or LLM integration.
- No automated GitHub repository settings; those are a manual checklist.
- No issue tracker duplication; the spec folder is the tracker.
- No coverage gate, benchmark suite, or release publishing.

## Scenarios

- A developer writes a spec, gets it approved, implements it on a short-lived
  branch, and merges a small PR with evidence.
- An agent starts with no context, reads `AGENTS.md`, finds the active spec, and
  knows what not to do.
- CI rejects a PR whose branch, title, spec, commit trailers, or AC tests do not
  match.
- A future project can copy the governance and templates without copying
  Strictr-specific product details.

## Acceptance criteria

- **AC-1:** The repository SHALL contain `AGENTS.md`, `docs/constitution.md`,
  `docs/architecture/system-overview.md`, and `docs/adr/0001-python-toolchain.md`,
  each with the operational, normative, or architectural sections required by
  the SDD guide.
- **AC-2:** The repository SHALL contain reusable spec and blueprint templates
  plus this in-progress bootstrap spec and its blueprint.
- **AC-3:** The traceability checker SHALL validate branch names, PR titles,
  spec status, commit subjects and `Spec:` trailers, and AC-to-test coverage,
  and its unit tests SHALL cover valid and invalid cases.
- **AC-4:** The repository SHALL have a runnable Python project configuration and
  CI that runs format checks, lint, strict types, tests, and traceability.
- **AC-5:** The repository SHALL contain a pull request template, a commit-msg
  hook that adds the spec trailer from the branch name, and a repository setup
  checklist.
- **AC-6:** The repository SHALL contain a testing guide covering AC markers,
  test layers, fixtures, failure modes, and determinism.
- **AC-7:** The repository SHALL contain a README describing project status,
  quick-start commands, the repository map, and documentation links.

## Constraints

- Python 3.12+; development on 3.13.
- Windows and Linux must both work.
- No runtime third-party dependencies in the package.
- CI must remain useful on GitHub Free; public-repo standard runners are free,
  but runs should stay fast.
- The traceability checker must be testable without invoking GitHub or git for
  its core logic.

## Open questions

None. The following are explicitly deferred:

- Whether to add CODEOWNERS and required approvals: when a second maintainer
  exists.
- Whether to add coverage gating: after the first product slice.
- Whether to move the SDD guide from `internal-docs/` to `docs/`: when the guide
  is stable and should be versioned.

## Revision log

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-11-19 | 0.1 | Initial bootstrap spec | Ge Rui Sen |
| 2026-11-19 | 0.2 | Artifacts implemented and verified locally; awaiting PR | Ge Rui Sen |
