# ADR 0004: Verification contract, statuses, and exit codes

- Status: accepted
- Date: 2026-11-21
- Decision makers: Ge Rui Sen

## Context

Agents need a stable, compact result. The raw tools emit different formats and
exit codes. The result must state what ran, what failed, what was skipped, and
whether the verification was complete. A false `pass` is the most damaging
failure mode.

## Decision drivers

- Machine-readable and versioned.
- Fail-closed semantics.
- Compact diagnostics with explicit truncation.
- Stable exit codes for scripts.
- Future SARIF/MCP compatibility without making them v0.1 dependencies.

## Considered options

1. **SARIF as the primary output.**
   Standard for static analysis, but not designed for test results, scope
   ledgers, or tier statuses; verbose for agent context.
2. **Plain text only.**
   Human-friendly, but not reliably parseable.
3. **Custom JSON envelope v1, with SARIF later.**
   Fits all tiers, can be compact, and can be adapted to SARIF.
4. **One JSON object per tool, no shared envelope.**
   Preserves tool detail but recreates the original orchestration problem.

## Decision

Use a custom, versioned JSON envelope (`schema_version: "1"`) as the primary
contract. SARIF is a later output adapter.

Statuses:

- Overall: `pass`, `fail`, `partial`, `error`.
- Tier: `pass`, `fail`, `skipped`, `error`.

Exit codes:

- `0` — `pass`
- `1` — `fail`
- `2` — `partial` or `error`

Rules:

- A requested required tier that does not run makes the result `partial` unless
  the user explicitly disabled it.
- A missing required tool, crash, timeout, or invalid tool output is `error`.
- A skipped optional tier (no tests) does not make the result `partial`.
- Fail-fast stops after the first failing tier; later tiers are recorded as
  skipped with a reason.
- Diagnostics are capped at 20 per tier and 2,000 characters per message.
  Truncation is explicit.
- Ordering is deterministic: tier, path, line, column, code, message.
- Paths are relative POSIX paths.
- `--json` writes one object to stdout; logs and warnings go to stderr.
- `trust.sandboxed` is always `false` in v0.1.

The full field definitions and examples are in
[verification-contract.md](../architecture/verification-contract.md).

## Consequences

Good:

- One stable interface for CLI, SDK, MCP, and future SARIF export.
- Agents can trust `status` and `scope` without parsing logs.
- Truncation and skips are visible.

Bad:

- A custom schema must be maintained and versioned.
- SARIF consumers need an adapter later.
- Some tool-specific detail is lost in the compact view.

## Confirmation

- JSON Schema and golden fixture tests validate the envelope.
- Tests cover every status/exit-code transition.
- A contract change requires a schema version bump and an ADR.
