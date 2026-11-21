# Changelog

All notable changes to this project are documented here.

The format is based on Keep a Changelog, and the project follows Semantic
Versioning once a public release exists.

## [Unreleased]

### Changed

- Spec `003-check-command` implements the `strictr check` command; the Phase 5
  audit passed and the branch is ready for merge.
- Discovery-error `scope.targets` normalization for Windows separators is
  deferred to spec 004; discovery failures still return a valid error envelope.
- Architecture is approved; spec 002 is archived, while
  `docs/architecture/` and `docs/adr/` remain living documents.
- Product discovery is approved; spec 001 is archived and its durable documents
  remain in `docs/product/`.

### Added

- `strictr check` command with Tier 0 syntax parsing, ruff, mypy or pyright, and
  the full pytest suite, plus human/JSON output, fail-closed envelopes, and exit
  codes (`003-check-command`).
- ADR 0008 (tools may import pure core types), ADR 0009 (v0.1 execution
  refinements for pyright, pytest `xunit1`, Tier 0 budget, and timeout scope),
  and ADR 0010 (owner-approved one-time size exception for spec 003).
- SDD workflow replaced role handoffs with a single-agent phase model:
  specify/plan, stub/test, implement, integrate, and audit, with human gates,
  frozen tests, `progress.md` state, and 60%/70% context thresholds.
- Removed the separate `handoff.md`; `progress.md` is the only session-state
  file and the blueprint owns task briefs.
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
