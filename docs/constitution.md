# Engineering Constitution

Version 1.0 · Last amended 2026-11-19

Every article states a rule, the risk it prevents, and how compliance is
checked. Amendments require an ADR, explicit human approval, and a version bump.

## I. Specification before code

Behavior-changing work requires an approved spec. Non-goals are binding.

**Why:** prevents unrequested scope, silent behavior changes, and untestable
intent.

**Check:** every code PR references an approved or in-progress spec.

## II. Executable acceptance criteria

Every acceptance criterion maps to an automated check. Missing data, a crashed
tool, or a timeout is an error, never a pass.

**Why:** a verifier that reports success without data is worse than no verifier.

**Check:** traceability check and test suite.

## III. Truth over green

Do not weaken, skip, or delete tests to make CI pass. Do not suppress type or
lint errors without a documented justification.

**Why:** a green pipeline that lies destroys trust in every future result.

**Check:** review and CI diff.

## IV. Typed and versioned contracts

Public interfaces are annotated and checked with strict typing. Machine-readable
output has a versioned schema.

**Why:** agents and tools depend on exact shapes, not prose.

**Check:** mypy and schema tests.

## V. Small, reversible changes

One spec per branch; branches live about two days; PRs stay reviewable. Risky
changes have a rollback plan.

**Why:** large changes are hard to review, test, and revert safely.

**Check:** branch age, PR size, blueprint rollback section.

## VI. Dependency discipline

The standard library comes first. A new runtime dependency requires an ADR and a
justification. Lockfiles are committed.

**Why:** every dependency adds supply-chain, licensing, and maintenance cost.

**Check:** dependency review.

## VII. Explicit trust boundaries

Executing untrusted code requires isolation or an explicit statement that no
isolation exists. Timeouts are mandatory. Diagnostics never include secrets.

**Why:** generated code is arbitrary code execution.

**Check:** failure-mode tests and review.

## VIII. End-to-end traceability

The spec ID appears in the branch, commit trailer, PR title, and release notes.
No direct pushes to the protected `main` branch.

**Why:** every change must answer why it exists and where its evidence is.

**Check:** traceability CI and branch protection.

## IX. Recorded, amendable decisions

Durable choices become ADRs. The constitution is stable, versioned, and
amendable, not immutable.

**Why:** an unamendable process is ignored or routed around.

**Check:** ADR log and amendment history.

## Amendment process

1. Write an ADR describing the change and its consequences.
2. Get explicit human approval.
3. Update this file, bump the version, and record the date.
4. Update dependent templates or CI checks in the same PR.
