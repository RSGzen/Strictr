# ADR 0005: Type-checker selection and configuration

- Status: accepted; version recording clarified by [ADR 0009](0009-v0-1-execution-refinements.md)
- Date: 2026-11-21
- Decision makers: Ge Rui Sen

## Context

Python projects may use mypy, pyright, both, or neither. Each has different
configuration files, output schemas, speed, and diagnostics. Strictr must choose
one checker deterministically without inventing a new configuration file. The
choice affects latency, parity, and the meaning of a `pass`.

## Decision drivers

- Parity with the project's existing type-checking gate.
- Deterministic behavior when both tools are installed.
- Zero new configuration.
- Speed matters in the agent loop, but correctness and trust come first.
- Missing tools must not become silent passes.

## Considered options

1. **Always run mypy.**
   Common and strict, but ignores pyright-only projects.
2. **Always run pyright.**
   Fast, but ignores mypy configuration and strictness.
3. **Always run both.**
   Maximum coverage, but doubles latency and produces duplicate/conflicting
   diagnostics.
4. **Auto-detect with an explicit override.**
   Uses project configuration and offers deterministic fallback.

## Decision

Use auto-detection with explicit override:

1. `--type-checker mypy|pyright|none` wins.
2. Mypy configuration present: `mypy.ini`, `.mypy.ini`,
   `pyproject.toml [tool.mypy]`, or `setup.cfg [mypy]`.
3. Pyright configuration present: `pyrightconfig.json` or
   `pyproject.toml [tool.pyright]`.
4. Mypy executable available.
5. Pyright executable available.
6. Otherwise the type tier is `skipped` and the overall result is `partial`.

If both mypy and pyright are configured, use mypy and emit a warning. Rationale:
mypy is the stricter common CI baseline; the user can override with
`--type-checker pyright`.

If a configured checker is not installed, the tier is `error`, not skipped.
`--type-checker none` is an explicit reduction of scope, recorded as
`skipped_reason: "disabled_by_user"`; it does not make the run `partial`.

The selected checker and its version are recorded in the tier result's `tool`
object. `environment` remains `python`, `platform`, and `root` (ADR 0009).

## Consequences

Good:

- Projects get the checker they configured.
- Behavior is deterministic when both are configured.
- Users can override without editing config.
- Missing type checking is visible, not a silent pass.

Bad:

- Mypy is slower than pyright; the target loop may prefer pyright.
- Projects using pyright as their CI gate must override if both are configured.
- Supporting two output schemas adds parser maintenance.

## Confirmation

- Fixture tests cover: only mypy, only pyright, both, neither, configured but
  missing, explicit override, and explicit `none`.
- Parity tests compare normalized diagnostics with the selected tool.
- The result includes the selected checker and reason.
