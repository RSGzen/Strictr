# Changelog

All notable changes to this project are documented here.

The format is based on Keep a Changelog, and the project follows Semantic
Versioning once a public release exists.

## [Unreleased]

### Changed

- Spec `003-check-command` is in progress; T-1 and T-2 are complete and the
  spec is at revision 1.2.
- Architecture is approved; spec 002 is archived, while
  `docs/architecture/` and `docs/adr/` remain living documents.
- Product discovery is approved; spec 001 is archived and its durable documents
  remain in `docs/product/`.

### Added

- ADR 0008 (tools may import pure core types) and ADR 0009 (v0.1 execution
  refinements for pyright, pytest `xunit1`, Tier 0 budget, and timeout scope).
- SDD workflow roles for Planner, Task Worker, and Integrator, including
  read/write ranges, test ownership, handoffs, the integration gate, and the
  comment/docstring policy.
- Architecture: modular verification pipeline, verification contract v1, and
  ADRs 0002–0007 for execution, statuses, type-checker selection, pytest
  integration, and local trust/timeouts.
- SDD bootstrap: `AGENTS.md`, engineering constitution, system overview, ADR
  0001, spec and blueprint templates.
- Traceability checker with unit tests and AC collection report.
- CI for format, lint, strict types, tests on Linux and Windows, and
  traceability.
- Pull request template, commit-msg hook, repository setup checklist, and
  testing guide.
- Product discovery: `docs/product/vision.md` and
  `docs/product/evaluation.md`, with locked users, scope, non-goals, evaluation
  metrics, conditional targets, and kill criteria.
