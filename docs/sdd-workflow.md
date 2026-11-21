# SDD Workflow: Planner, Task Worker, Integrator

Status: approved · Owner: Ge Rui Sen · Last updated: 2026-11-21

This document is the tracked operational contract for multi-session work. The
full method guide remains in `internal-docs/`; this file defines the role scopes
that every session can rely on. Changes to this file require owner approval.

The governing rules remain in `AGENTS.md`, `docs/constitution.md`, and the active
spec. If this document conflicts with them, they win.

## Roles

| Role | Owns | Does not own |
|---|---|---|
| **Human owner** | Spec approval, governance changes, ADRs, dependencies, merge | Implementation tasks |
| **Planner** | Intent, scope, ACs, public contract, blueprint, test strategy, handoffs | Production implementation |
| **Task Worker** | One blueprint task at a time: failing test, implementation, evidence | Spec scope, public interfaces, other tasks |
| **Integrator** | Full gate, cross-task review, acceptance, traceability, PR/archive readiness | Quiet behavior changes, test weakening |

## Read/write matrix

Read broadly; write narrowly. Broad read access is required to avoid conflicting
assumptions. Narrow write access is what makes concurrent sessions reviewable.

| Path | Planner | Task Worker | Integrator |
|---|---|---|---|
| `AGENTS.md`, `docs/constitution.md`, `.github/`, release config | Read | Read | Read |
| `internal-docs/`, `specs/archive/` | Read | Read | Read |
| `docs/architecture/`, `docs/adr/` | Read; write only with owner approval | Read | Read |
| `specs/active/NNN-*/spec.md` | Write | Read | Read; status/archive after approval |
| `specs/active/NNN-*/blueprint.md` | Write | Update own task checkbox | Write statuses, test plan, integration notes |
| `docs/sdd-workflow.md` | Read | Read | Read |
| Planner-owned contract tests and schema | Write | Read; never weaken | Read; integration glue only |
| `src/strictr/` | Read | Write only task-scoped files | Write integration fixes only |
| Task unit/acceptance tests | Read | Write for own task | Write integration glue |
| `README.md`, `CHANGELOG.md`, usage docs | Write when the spec requires | Read | Write final updates |
| `pyproject.toml`, `uv.lock` | Propose dependency changes | Only with prior approval | Only mechanical integration with approval |
| `build/ac-tests.json` | Read | Generate by test collection; never hand-edit | Read |

No role may edit `internal-docs/` or `specs/archive/`. `AGENTS.md`, the
constitution, `.github/`, and release configuration require explicit human
approval.

The matrix is enforced by task briefs, review, and CI. It is not a security
boundary; do not claim otherwise.

## Planner scope

Responsibilities:

- Write `spec.md` and `blueprint.md`; keep non-goals binding.
- Lock public interfaces before workers start: CLI shape, status model, JSON
  Schema, module boundaries, and error semantics.
- Write the cross-cutting contract tests: schema validation, CLI/exit-code
  acceptance, and the AC-to-test map. Do not pre-write every unit test; that
  encodes guessed internals.
- Ensure every AC maps to at least one task and one test, and every failure mode
  maps to a test.
- Resolve ambiguity or record an explicit deferral with an owner and trigger.
- Schedule a Planner prep session when a cross-cutting contract test must exist
  before a worker task; the worker implements against the frozen test.
- Issue one task brief per worker; review contract-impacting changes.

Definition of Ready:

- Spec is approved; ACs are observable and numbered.
- Every AC has a task and a test; every task maps to an AC.
- Public interfaces and the test ownership split are locked.
- Open questions are resolved or explicitly deferred.
- The work is either within the size budget or has an approved exception/split.

The Planner does not mark its own governance changes approved. The human owner
approves the spec; the Planner records that approval.

## Task Worker scope

Responsibilities:

- Implement exactly one blueprint task per session.
- Write the failing test first. Run it and confirm it fails for the expected
  reason, not an import error.
- Implement the minimum, rerun the exact command, then refactor under green.
- Add unit tests for new branches and failure-mode tests for changed trust
  boundaries. Add an acceptance test when the task changes public behavior.
- Keep the diff inside the task's file list. Do not refactor unrelated code.
- Update only the task checkbox after the exact command passes.
- Commit atomically with `Spec: NNN` and `Refs: AC-n`.
- Report evidence: failing output, passing output, command, commit hash, and any
  residual risk.

Forbidden:

- Editing the spec, contract, schema, or public interfaces to make a test pass.
- Weakening, skipping, or deleting tests.
- Editing planner-owned contract tests.
- Adding runtime dependencies without an ADR.
- Changing `AGENTS.md`, the constitution, `.github/`, release config,
  `internal-docs/`, or `specs/archive/`.
- Expanding scope. New scope needs a new spec.

Definition of Done for a task:

- Failing-test evidence exists.
- The exact verification command passes.
- Format, lint, and strict types pass for touched code.
- No skipped or weakened tests.
- Comments and docstrings follow the policy; no redundant narration.
- Checkbox updated; commit trailer present.
- Files changed match the task brief.

Stop and escalate when the task needs an interface change, a new dependency, a
cross-cutting refactor, a file outside the allowed range, or a change to an AC.

## Comment and docstring policy

All roles follow these rules. Comments explain why; code explains what.

- Do not restate code or duplicate the spec, contract, blueprint, or ADR.
- Public modules, classes, protocols, and functions get a concise docstring when
  their contract or invariant is not obvious. Follow the existing one-line style
  in `src/strictr/traceability.py`.
- Private helpers need no docstring when names, types, and tests make behavior
  clear.
- Inline comments are for non-obvious constraints, invariants, platform
  workarounds, or ADR/spec references. Keep them to one line where possible.
- No commented-out code. No TODO without a spec or task reference. No
  attribution or changelog comments.
- If a comment conflicts with code, tests, the contract, or the docs, treat the
  comment as a bug and update or delete it in the same change.
- Do not copy contract fields, status tables, or blueprint decisions into
  comments. Link to the path or ADR instead.

Class-level implementation details are not documented step by step. Document the
public contract and non-obvious invariants; otherwise improve names, types,
structure, and tests.

## Integrator scope

Responsibilities:

- Own the integration branch/PR and the full gate.
- Run acceptance, unit, contract, and failure-mode tests on the supported
  matrix; review flakiness, paths, Unicode, and timeout behavior.
- Verify every AC has a tagged passing test, every blueprint failure mode has a
  test, and no orphan tags exist.
- Review the diff for scope creep, hidden skips, weakened tests, absolute paths,
  versions in golden files, stale or duplicated comments, and missing docs.
- Resolve mechanical conflicts and integration glue. Send behavior defects back
  to a worker; do not quietly rewrite behavior.
- Update the blueprint statuses, changelog, usage docs, and PR evidence.
- Prepare the archive package after merge: spec status `done`, archive move,
  convergence check, retrospective.

Definition of Done for integration:

- Every AC has a passing tagged test.
- Every failure mode in the blueprint has a test.
- Format, lint, types, full tests, acceptance, and traceability pass.
- Docs and changelog are updated.
- The spec and blueprint are internally consistent; no silent scope drop.
- The human owner approves the merge. Agents do not self-approve governance or
  merge their own PR unless explicitly delegated.

The Integrator does not add behavior beyond the approved spec. If a fix changes
behavior, it needs a task and a worker, or a spec revision.

## Task handoff template

The Planner gives each worker a brief with this shape:

```text
Role: Task Worker
Task: T-4
Spec: 003
ACs: AC-5, AC-6
Work unit: WU-1
Read: AGENTS.md, docs/sdd-workflow.md, spec.md, blueprint.md,
      docs/architecture/verification-contract.md, docs/testing.md,
      core/models.py, core/paths.py
Write: core/discovery.py, tests/unit/test_discovery.py,
       blueprint T-4 checkbox
Forbidden: spec, blueprint scope, schema, contract, other tiers, pyproject
Verify: uv run pytest tests/unit/test_discovery.py -q
Evidence: failing test output, passing output, commit hash
Stop if: interface change, new dependency, ambiguity, out-of-scope file
```

The worker returns the commit hash, exact commands and results, files changed,
remaining risks, and any question that needs a spec or blueprint decision.

## Task lifecycle

1. **Ready** — Planner has issued the brief; interfaces are frozen.
2. **In progress** — Worker writes the failing test first.
3. **Verified** — Exact task command passes; worker commits and updates the
   checkbox.
4. **Integrated** — Integrator runs the full gate and cross-task checks.
5. **Done** — Human owner approves merge; spec is archived after merge.

A worker never moves a spec to `done`. The Integrator prepares the archive; the
human owner approves it.

## Parallelism

Sequential by default. One writer per integration branch prevents merge
conflicts and ambiguous blame. If parallel work is unavoidable:

- Give each worker a separate worktree and a disjoint file set.
- Lock shared interfaces before starting.
- Keep one integrator and one merge order.
- Do not open partial PRs for one spec. Split the spec into separate specs with
  independent AC sets instead.

## PR and integration policy

This repository's traceability checker requires every AC in the active spec to
have a tagged test on every PR. A partial PR for one spec therefore cannot pass.
The default is:

- One spec, one integration branch, one PR.
- Open the PR as a draft after the first end-to-end vertical slice.
- It is acceptable for traceability to be red on the draft until all AC tests
  exist. Never weaken the checker, add fake tests, or merge a red gate.
- Merge only after the full gate, acceptance suite, and traceability pass.
- If the PR is too large to review, split the work into separate specs with
  independent ACs. Do not open partial PRs for one spec.

This is a deliberate, documented deviation from generic "one spec, many PRs"
advice because the traceability implementation is spec-global.

## Integration gate

Before the Integrator marks integration ready:

- [ ] Every AC has at least one passing tagged test.
- [ ] Every blueprint failure mode has a test.
- [ ] Unit, acceptance, contract, and failure-mode tests pass.
- [ ] Windows and Linux CI pass.
- [ ] Format, lint, and strict types pass.
- [ ] Traceability passes for the active spec.
- [ ] Golden files contain no absolute paths or volatile versions.
- [ ] Comments and docstrings follow the policy; no stale or duplicated comments.
- [ ] No hidden skips, weakened tests, or unexplained exclusions.
- [ ] Docs, changelog, and spec/blueprint statuses are consistent.
- [ ] The human owner has the exact commands and results.
