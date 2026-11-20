---
id: "001"
title: "Product discovery: agent-first verification gateway"
status: in-progress
owner: "Ge Rui Sen"
created: 2026-11-20
updated: 2026-11-20
branch: "docs/001-product-discovery"
---

# Product discovery: agent-first verification gateway

## Context

The product concept has been discussed, but it exists only in conversation. The
repository needs a durable, reviewable statement of the problem, users, gap,
scope, non-goals, and evaluation plan before architecture or product code is
written.

This spec records the decisions already made and creates the product documents
that later specs must follow.

## Goals

- Establish a single source of truth for the product vision.
- Lock the primary user, trust stance, v0.1 scope, and non-goals.
- Define an evaluation plan with conditional hypotheses and kill criteria.
- Update repository entry points and numbering so `003-check-command` is the
  first product slice.

## Non-goals

- No architecture or tech-stack decisions. Those belong to `002`.
- No product CLI, engines, diagnostics, or runtime behavior.
- No benchmark execution or measured performance claims.
- No full competitor market report.
- No MCP, Docker, daemon, fuzzing, or test-selection design.
- No new runtime dependencies.

## Scenarios

- An agent harness builder reads `docs/product/vision.md` and understands
  whether Strictr is a fit, what v0.1 verifies, and what it deliberately does
  not do.
- A future spec writer uses the vision and evaluation docs to constrain
  architecture and acceptance criteria.
- A reviewer checks that unmeasured claims are labeled as hypotheses and that
  the locked decisions have not drifted.

## Acceptance criteria

- **AC-1:** `docs/product/vision.md` SHALL contain sections for positioning,
  problem, evidence and assumptions, target users, current alternatives and gap,
  product principles, locked decisions, goals, non-goals, scope/phases, adoption
  path, risks, open questions, and success/kill criteria.
- **AC-2:** `docs/product/evaluation.md` SHALL define metrics, baselines,
  workloads and corpus, measurement protocol, conditional targets, kill
  criteria, public-benchmark caveats, and a reporting template; all numeric
  targets SHALL be labeled as conditional hypotheses.
- **AC-3:** `AGENTS.md`, `README.md`, and
  `docs/architecture/system-overview.md` SHALL link to the product documents and
  use `003-check-command` for the first product slice, with no remaining
  `001-check-command` references.
- **AC-4:** `CHANGELOG.md` SHALL record the product discovery documents, and the
  repository SHALL contain an automated check for the required document sections
  and links.

## Constraints

- The locked decisions from the concept review are binding:
  - agent-first primary user
  - local-only v0.1 execution with an explicit not-a-sandbox warning
  - Tier 0–1 plus compact pytest in v0.1
  - metrics as conditional hypotheses
  - the non-goals list in `vision.md`
- Documentation only, plus tests that verify the documentation.
- No architectural commitments. `002` owns the design.
- Keep the durable product surface to two files: `vision.md` and
  `evaluation.md`.

## Open questions

- Exact benchmark corpus and threshold values. The evaluation plan defines the
  method; measurement belongs to a later spec.
- Default type checker selection when both mypy and pyright are available.
- Packaging and distribution.
- Timing of SARIF, MCP, and sandbox work.
- Telemetry and privacy model.

These do not block 001 because they are explicitly deferred to 002 or later.

## Revision log

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-11-20 | 0.1 | Initial product discovery spec | Ge Rui Sen |
| 2026-11-20 | 0.2 | Product docs and tests implemented; awaiting PR | Ge Rui Sen |
