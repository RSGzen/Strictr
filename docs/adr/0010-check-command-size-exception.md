# ADR 0010: One-time size exception for spec 003

- Status: accepted
- Date: 2026-11-21
- Decision makers: Ge Rui Sen
- Related: [ADR 0004](0004-verification-contract-and-statuses.md), spec `003`

## Context

The constitution targets branches of about two days, and the SDD guide targets
about seven tasks or two days per spec. Spec `003-check-command` has 13 tasks
and one integration branch/PR.

The owner approved a one-time exception because the command-chaining feature
cannot be split more atomically without shipping a partial command that risks
misleading compatibility behavior. The type, tier, parser, and output
infrastructure are also being built from the ground up. Future specs are
expected to be smaller once that infrastructure exists.

## Decision

Spec `003-check-command` is allowed to exceed the default size and branch-age
targets as one spec with one integration branch and one PR.

This is a **one-time exception**, not a policy change:

- The exception is recorded in the spec, blueprint, and PR.
- The default size and branch-age targets remain in force for later specs.
- The exception does not relax test freeze, traceability, review, or merge
  gates.
- Future specs that cannot fit the default must either split or record a new
  approved exception; this ADR does not cover them.

## Consequences

Good:

- The first product slice ships as one coherent command instead of a misleading
  partial command.
- Contract, tier, and output compatibility are tested together.
- The work remains traceable to one spec.

Bad:

- The branch and PR are larger than the default and need more review time.
- Branch-age tooling will flag the exception until merge.
- The exception must not become the normal path for large specs.

## Confirmation

- Spec 003 and its blueprint reference this ADR.
- The PR description repeats the one-time exception.
- The next spec starts from the default size and branch-age targets.
- No CI or traceability rule is weakened by this exception.
