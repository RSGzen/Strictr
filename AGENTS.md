# AGENTS.md

## Purpose

Strictr is a deterministic verification tool for LLM-generated Python code. It
parses candidate code, runs static checks, optionally runs tests, and returns
compact machine-readable diagnostics.

Current phase: spec `003-check-command` is in progress. T-1 and T-2 are
complete; T-3 is next. There is no product CLI yet.

## Read order

1. `docs/constitution.md`
2. `docs/sdd-workflow.md`
3. `docs/product/vision.md`
4. `docs/product/evaluation.md`
5. `docs/architecture/system-overview.md`
6. `docs/architecture/verification-contract.md`
7. The active spec in `specs/active/` with status `approved` or `in-progress`
8. Its `blueprint.md`

Architecture decisions live in `docs/adr/`; read the ones linked from the system
overview when changing a boundary or execution policy.

If there is no approved or in-progress spec for the requested behavior, stop and
write or clarify the spec first.

## Repository map

- `src/strictr/` — production package code
- `tests/unit/` — unit tests
- `tests/acceptance/` — black-box CLI tests (from `003` onward)
- `tests/fixtures/` — small fixture projects
- `specs/active/` — in-flight specs
- `specs/archive/` — frozen, completed specs
- `docs/product/` — durable product vision and evaluation plan
- `docs/architecture/` — system overview, verification contract, ADRs
- `docs/sdd-workflow.md` — Planner, Task Worker, and Integrator scopes
- `docs/` — constitution, testing and setup guides
- `scripts/` — repository tooling
- `internal-docs/` — local notes, git-ignored, do not edit

## Commands

- Setup: `uv sync`
- Test: `uv run pytest`
- Collect-only (traceability): `uv run pytest --collect-only -q`
- Lint: `uv run ruff check .`
- Format check: `uv run ruff format --check .`
- Format: `uv run ruff format .`
- Types: `uv run mypy`
- Traceability: `uv run python scripts/check_traceability.py` (requires PR environment variables; see `docs/repo-setup.md`)

There is no `strictr` CLI yet. Add the command here when `003` lands.

## Workflow

- Do not write behavior code without an approved spec.
- Read `docs/sdd-workflow.md` before acting as Planner, Task Worker, or
  Integrator.
- Follow the comment and docstring policy in `docs/sdd-workflow.md`; explain why,
  not what.
- Plan first if the change touches more than one file or has ambiguity.
- Work one blueprint task at a time; run its exact verification command.
- For behavior changes, write or update the failing test before the implementation.
- Update the blueprint checkbox only after the command passes.
- Run the full local gate before opening a PR.
- Stop and ask when the spec is ambiguous; record the question in the spec.
- Do not expand scope; propose a new spec instead.

## Git protocol

- Branch from `main`: `<type>/<NNN>-<slug>`.
  - Spec-required types: `feat`, `fix`, `refactor`, `test`, `perf`.
  - Non-behavioral types: `docs`, `ci`, `chore` (spec ID optional).
- One spec uses one integration branch and PR. If it grows too large, split the
  spec into separate specs with independent ACs; do not open partial PRs for one
  spec.
- Commit: Conventional Commits with a `Spec: NNN` trailer and optional
  `Refs: AC-n`.
- PR title: `type(scope): summary [NNN]` when a spec is required.
- Never push directly to `main`.
- Use `--force-with-lease` only on your own unmerged branch.
- Rebase on `main`; squash merge; delete the branch.

Example commit:

```text
feat(check): add tier 0 syntax gate

Parse target files before invoking external tools.

Spec: 003
Refs: AC-1, AC-2
```

## Boundaries

- Do not edit `AGENTS.md`, `docs/constitution.md`, `.github/`, or release
  configuration without human approval.
- Do not add a runtime dependency without an ADR.
- Do not change the verification contract or a module boundary without an ADR
  and a spec revision.
- Do not commit secrets, credentials, or local environment files.
- Do not run destructive git commands without explicit approval.
- Do not edit `internal-docs/` or `specs/archive/`.
- Do not modify unrelated files.
- Do not treat a missing tool, crash, or timeout as a pass.

## Honesty rules

- Never weaken, skip, or delete a failing test to get green.
- Never suppress a type or lint error without a written justification.
- Never claim completion without the exact command and result.
- If a required tool is missing or crashes, report it; do not invent success.
- Do not present unmeasured performance or detection claims as facts. Label
  them as hypotheses and link to `docs/product/evaluation.md`.

## Definition of Done

- [ ] Every AC has a passing tagged test.
- [ ] Failure modes are tested.
- [ ] Format, lint, types, and full tests pass.
- [ ] Traceability check passes.
- [ ] Docs/ADR/changelog updated.
- [ ] Spec archived; branch deleted.

## Decisions

- Durable decisions go to `docs/adr/`.
- The verification contract is binding; implementation follows it.
- Ephemeral design details go to the blueprint.
- Behavior changes go to the spec first.
