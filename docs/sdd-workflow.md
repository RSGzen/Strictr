# SDD Workflow: Single Agent, Phase Gates

Status: approved · Owner: Ge Rui Sen · Last updated: 2026-11-22

This is the tracked operational workflow for spec-driven work. It replaces the
former multi-role split with one writer agent and five phase gates. The human
owner remains the approval authority.

The governing rules remain in `AGENTS.md`, `docs/constitution.md`, and the active
spec. If this document conflicts with them, they win.

## Core rules

1. **One writer agent.** Implementation, tests, and docs are authored by one
   agent. There are no role handoffs.
2. **Fresh context per phase.** A new session starts at every phase gate. Within
   a phase, start a new session at the context threshold below.
3. **Artifacts carry state.** The spec, blueprint, tests, code, git history, and
   `progress.md` are the handoff. Prose in a chat is not.
4. **Executable contracts beat prose.** Phase 2 freezes interfaces and failing
   tests. Phase 3 implements against those tests, not a written description of
   intended internals.
5. **Human gates are explicit.** The human approves intent, freezes tests,
   approves spec/scope changes, and merges.
6. **No silent scope or test changes.** A frozen test or an AC changes only with
   human approval.
7. **No `handoff.md`.** `progress.md` is the only session-state file. The
   blueprint owns durable task briefs.

## Comments and docstrings

Write comments only for the reason behind non-obvious code: constraints,
tradeoffs, and surprising behavior. Explain why, not what. Public modules and
functions have docstrings that state their contract. Delete stale or duplicated
comments instead of leaving them for later.

## Artifacts

| Artifact | Responsibility | Changes |
|---|---|---|
| `spec.md` | Behavior, non-goals, ACs, constraints, decisions affecting scope | Versioned until done |
| `blueprint.md` | Design, modules, interfaces, failure modes, test plan, task briefs, commands | During planning; updated when design changes |
| `progress.md` | Current phase, branch, commit, frozen tests, next command, open items | Every phase gate and session |
| Tests | Executable proof of ACs; frozen in Phase 2 | Phase 2; later only with approval |
| Code | Implementation | Phase 3 and targeted Phase 4 fixes |
| Contract, architecture, ADRs | Durable design truth | Separate documents; linked, not duplicated |

Do not copy the verification contract, architecture, or ADRs into the spec. The
spec folder holds the working state; durable documents stay authoritative.

## Phase model

| Phase | Agent action | Human gate | Context |
|---|---|---|---|
| **1. Specify & Plan** | Write `spec.md`, `blueprint.md`, and `progress.md`; read-only on `src/` | Hard: review the spec/blueprint until intent is exact | Session 1 |
| **2. Stub & Test** | Write annotated stubs/interfaces, schemas, `NotImplementedError` bodies, and failing AC-tagged tests | Hard: interfaces compile; tests reflect the spec; freeze tests at a commit | New session |
| **3. Implement & Reconcile** | Implement until the frozen tests pass; no test edits | Exception only: spec or test change | New session by default; continue only below 60% |
| **4. Integrate & Verify** | Write and run cross-module/acceptance tests; fix edge cases; update docs/changelog | Soft: review coverage and failure modes | Continue if below 60%, otherwise new session |
| **5. Closeout & Audit** | Fresh read-only review, full gate, traceability, PR readiness | Final: review diff and merge | New session |

### Phase 1 — Specify & Plan

Write:

- `spec.md`: context, goals, non-goals, scenarios, numbered ACs, constraints,
  resolved open questions, revision log.
- `blueprint.md`: approach, module boundaries, public contracts, failure modes,
  security, test plan, ordered task briefs with exact commands, rollback.
- `progress.md`: phase, branch, last gate, next command.

Read-only on `src/` and tests. Do not write product code.

Gate:

- Every AC is observable and testable.
- Every AC maps to at least one task and one test.
- Non-goals and open questions are explicit.
- Public interfaces and the task order are clear enough to stub.

Commit the Phase 1 artifacts. Record the commit in `progress.md`.

### Phase 2 — Stub & Test

Create executable contracts:

- Real modules with annotated classes, Protocols, function signatures, and
  `raise NotImplementedError` bodies where behavior is not implemented.
- JSON schema or typed data contracts where a public shape exists.
- Failing unit/acceptance tests tagged with `pytest.mark.spec("NNN")` and
  `pytest.mark.ac("AC-n")`.
- Stub wiring that imports cleanly.

Run:

- `uv run mypy` — the stubs must type-check.
- `uv run ruff check .` — no lint errors.
- The target test command — tests must fail for the expected reason, not an
  import error.

Gate:

- Interfaces compile and match the blueprint.
- Every AC assigned to the current task/slice has a tagged failing test.
- Tests reflect the spec, not the intended implementation.
- The human reviews the diff and freezes the tests at a commit.
- Record the freeze commit in `progress.md`.

Phase 3 must not edit frozen tests.

### Phase 3 — Implement & Reconcile

Start a new session from the freeze commit. Read `progress.md`, the frozen tests,
and the blueprint task brief.

Implement the minimum until the frozen tests pass. Do not edit tests to make
them pass. Do not add public interfaces that are absent from the blueprint.

If a spec flaw surfaces:

- **Clarification** with no AC, non-goal, or contract change: update the spec,
  add a revision entry, and continue.
- **Behavior or scope change**: stop. The human approves a spec revision or a
  new spec; then update the blueprint and tests before implementing.

Run the task's exact command after every change. Commit at green checkpoints.
When the phase ends, record the commit and next command in `progress.md`.

### Phase 4 — Integrate & Verify

Write integration, end-to-end, and failure-mode tests across module boundaries.
Fix edge-case bugs in implementation. Do not weaken or delete frozen unit tests.
Update docs, changelog, and statuses so the final audit has nothing to edit.

Gate:

- Failure modes in the blueprint have tests.
- Cross-module contracts hold.
- Paths, Unicode, timeouts, and error envelopes are exercised.
- Full acceptance suite passes.
- Docs, changelog, and PR evidence are ready.

Update `progress.md` with the integration result and the next action.

### Phase 5 — Closeout & Audit

Use a **fresh, read-only session**. It must not edit code, tests, or docs.

Run:

- format, lint, strict types, full tests, acceptance tests;
- traceability for the active spec;
- a diff review against `spec.md`, `blueprint.md`, the contract, and the
  constitution.

Check:

- every AC has a passing tagged test;
- no hidden skips or weakened tests;
- no scope creep outside the non-goals;
- docs, changelog, and statuses are consistent;
- no stale or duplicated comments.

Report findings. The human owner approves the merge.

**Post-merge closeout:** the owner or a delegated agent moves the spec to
`specs/archive/`, sets status `done`, records the retrospective, updates the
changelog/release notes, and deletes the branch. Do not archive before the final
gate.

## `progress.md` template

Keep it short and factual. It is not a narrative.

```md
# Progress: <Spec title>

- Phase: 2 Stub & Test
- Spec: 003
- Branch: feat/003-check-command
- Last gate: Phase 1 passed at <commit>
- Frozen tests: none yet / tests/unit/test_core.py at <commit>
- Next command: uv run pytest tests/unit/test_core.py -q
- Spec changes: none
- Open items: none

## Phase log

- 2026-11-21: Phase 1 complete; spec 1.3 and blueprint approved.
```

Update it at every phase gate and before ending a session.

## Session protocol

At session start:

1. Read `AGENTS.md`, this workflow, `spec.md`, `blueprint.md`, and `progress.md`.
2. Run `git status --short` and `git log --oneline -1`.
3. Stop if the worktree is dirty or HEAD is not the expected commit.
4. Confirm the phase and next command in `progress.md`.
5. Do not do work from a later phase.

At session end:

1. Run the phase's verify command.
2. Commit the phase work atomically with `Spec: NNN` and `Refs: AC-n`.
3. Update `progress.md` with the new commit and next command.
4. Commit the progress update separately (for example,
   `docs: record phase state`) or amend the phase commit before pushing.
5. If at a phase gate, write the gate result and stop.

## Session commands

Use explicit paths, not `git add -A`.

```powershell
git status --short
git log --oneline -1
git add <explicit paths>
git commit -m "type(scope): summary" -m "Spec: NNN" -m "Refs: AC-n"
git push
```

Never push directly to `main`. Open the branch as a draft PR after the first
end-to-end vertical slice.

## Test and spec freeze

- Phase 2 freezes the test set at a commit. Record that commit.
- Phase 3 does not edit frozen tests. A test correction needs human approval and
  a new freeze commit.
- The spec is approved at Phase 1. Clarifications are allowed in Phase 3; AC,
  non-goal, contract, or module-boundary changes require human approval.
- A large scope change becomes a new spec, not an expanded Phase 3.

## Context windows and sessions

Use **tokens used / model context window** as the measure.

| Situation | Threshold | Action |
|---|---:|---|
| Phase boundary | any % | Commit, update `progress.md`, new session |
| New vertical slice/task | any % | New session |
| Mid-phase implementation | 60% | Finish the atomic step, commit, new session |
| Mid-phase, no clean commit | 70% | Stop, commit/stash, new session |
| Read-only audit | 70% | New session regardless |
| Small context window (<64k) | 50–55% | Reset earlier |

**New session is the default.** Compaction is a fallback for mid-phase work with
no clean commit point. OpenCode V2 compaction is lossy: it summarizes older
conversation and keeps about 15,000 recent tokens by default. For coding, raise
`keep.tokens` to about 24,000.

If auto-compaction is used as a safety net, trigger it around 70% rather than
the default ~85%:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "compaction": {
    "auto": true,
    "buffer": "30%",
    "keep": { "tokens": 24000 }
  }
}
```

After any compaction, re-read `progress.md`, `spec.md`, and `blueprint.md`, then
run the next command. Do not trust the summary as a contract.

## Large specs

Apply Phases 2–4 per **task or small vertical slice**, not across the whole
spec and not necessarily per work unit. A work unit is a checkpoint, not a
session scope. WU-1's tasks can be stubbed, implemented, and integrated one at a
time before WU-2 starts.

Phase 1 covers the whole spec. Phase 5 covers the whole spec after all slices.

### One-time size exceptions

The default size and branch-age targets remain in force. A spec may exceed them
only with an explicit owner-approved ADR and a note in the spec and PR. Spec 003
uses ADR 0010 for this one-time exception. Future specs return to the default;
large work splits into separate specs.

## PR and integration policy

This repository's traceability checker requires every AC in the active spec to
have a tagged test on every PR. Therefore:

- One spec, one integration branch, one PR.
- Open the PR as a draft after the first end-to-end vertical slice. Draft checks
  may be red until all AC tests and code exist.
- Run the full local gate before marking the PR ready for review.
- Traceability may be red on the draft until all AC tests exist. Never weaken
  the checker, add fake tests, or merge a red gate.
- Merge only after the Phase 5 gate passes.
- If the PR is too large to review, split the work into separate specs with
  independent ACs. Do not open partial PRs for one spec.

The human owner merges. Agents do not self-approve governance or merge their own
PR unless explicitly delegated.

## Integration gate

Before the Phase 5 audit marks the work ready:

- [ ] Every AC has at least one passing tagged test.
- [ ] Every blueprint failure mode has a test.
- [ ] Unit, acceptance, contract, and failure-mode tests pass.
- [ ] Windows and Linux CI pass.
- [ ] Format, lint, and strict types pass.
- [ ] Traceability passes for the active spec.
- [ ] Golden files contain no absolute paths or volatile versions.
- [ ] Comments and docstrings follow the policy.
- [ ] No hidden skips, weakened tests, or unexplained exclusions.
- [ ] Docs, changelog, and spec/blueprint/progress statuses are consistent.
- [ ] The human owner has the exact commands and results.
