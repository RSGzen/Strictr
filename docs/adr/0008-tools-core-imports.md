# ADR 0008: Tools may import pure core types

- Status: accepted
- Date: 2026-11-21
- Decision makers: Ge Rui Sen
- Related: [ADR 0002](0002-verification-pipeline.md), [system overview](../architecture/system-overview.md), spec `003`

## Context

The approved architecture says the `tools` layer may import only the standard
library and `core.errors`. That table is too narrow for the approved design:

- The subprocess runner returns a `ToolResult` type used by the `ToolRunner`
  protocol, which lives in `core`.
- Pure parsers return `Diagnostic` objects and normalize paths with the core path
  helper.
- The `core` layer must not import `tools`, so moving the shared types downward
  is not possible without a larger redesign.

Without a decision, T-5, T-7, T-8, and T-9 would either violate the import table
or duplicate core models and path logic.

## Decision drivers

- Keep one diagnostic and result model.
- Keep parsers pure and independently testable.
- Preserve the dependency direction: `core` knows nothing about tools.
- Avoid a speculative plugin or adapter framework.
- Keep the change small and reversible.

## Considered options

1. **Strictly allow only `core.errors`.**
   Requires duplicate parser DTOs and a conversion layer, or moving parser
   output types into a third namespace. More code and two representations of a
   diagnostic.
2. **Move parsers into `tiers`.**
   Breaks the approved separation between pure parsers and execution policy.
3. **Allow `tools` to import pure core types.**
   Keeps one model, one path helper, and one error hierarchy while preserving
   the direction `core` does not import `tools`.
4. **Introduce a shared `contracts` package.**
   Adds a new layer for one language and a handful of dataclasses; premature.

## Decision

The `tools` layer may import the standard library plus:

- `core.models`
- `core.paths`
- `core.errors`

It must not import `core.pipeline`, `core.discovery`, `tiers`, `output`, or
`cli`. `core` must not import `tools`. Parsers remain pure functions: text,
JSON, or XML in, diagnostics out.

The architecture module table and tree are updated to match this decision. Any
further widening needs a new ADR.

## Consequences

Good:

- One diagnostic model and one path-normalization rule.
- The runner and parsers remain unit-testable with fakes.
- The dependency direction stays acyclic.

Bad:

- `tools` now has three allowed core dependencies, not one.
- A future split into separately versioned packages would need a contracts
  package.

## Confirmation

- The system overview lists the allowed imports.
- Code review checks that `tools` does not import `tiers`, `output`, or `cli`.
- Unit tests exercise the parsers and runner without a real project.
