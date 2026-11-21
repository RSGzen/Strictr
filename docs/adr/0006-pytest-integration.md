# ADR 0006: Pytest integration and full-suite policy

- Status: accepted; JUnit format refined by [ADR 0009](0009-v0-1-execution-refinements.md)
- Date: 2026-11-21
- Decision makers: Ge Rui Sen

## Context

Tier 2 is the only tier that can catch algorithmic and boundary errors. The
product needs compact failure evidence without losing correctness. Test
selection is tempting for speed but can produce false passes in dynamic Python.
Strictr must also integrate with pytest without adding a runtime dependency.

## Decision drivers

- Never produce a false pass.
- Preserve the project's pytest configuration and plugins.
- Compact diagnostics for agents.
- No third-party runtime dependency.
- Windows and Linux compatibility.

## Considered options

1. **JUnit XML via `--junitxml`.**
   Built into pytest, stable enough, includes testcase file/line and failure
   text. Limited locals and assertion detail.
2. **A custom pytest plugin.**
   Richer reports and locals, but more integration surface and version coupling.
3. **`pytest-json-report` or another third-party plugin.**
   Convenient, but an extra dependency and plugin compatibility risk.
4. **Parse raw pytest stdout.**
   Brittle and noisy.
5. **Test selection (testmon/TIA).**
   Faster, but dynamic Python false negatives are a release blocker for v0.1.

## Decision

Use built-in JUnit XML in v0.1 and run the full test suite by default:

- Command: `python -m pytest -q -o junit_family=xunit1 --junitxml=<temporary
  path>`.
- Parse the XML with the standard library.
- Map testcase `file`, `line`, failure/error text, and node IDs into compact
  diagnostics.
- No test selection, coverage, or test-impact analysis in v0.1.
- If no tests are collected (`pytest` exit 5), tier status is `skipped` with
  reason `no tests collected`; it does not make the result `partial`.
- If pytest exits 2, 3, or 4, the tier is `error`.
- If pytest is missing and tests exist, the tier is `error`.
- If tests fail, the tier is `fail`; the first failures are kept up to the
  contract cap.
- A custom pytest plugin can replace JUnit later for locals and assertion
  details; it is not part of v0.1.

## Consequences

Good:

- No runtime dependency and no plugin injection.
- Full suite protects against false passes.
- Failure evidence is compact but sufficient for the first repair loop.

Bad:

- JUnit XML lacks locals and some assertion detail.
- Full suites can be slow; the evaluation will measure the real cost.
- A later plugin will need its own compatibility and security work.

## Confirmation

- Fixture projects cover pass, assertion failure, exception, collection error,
  no tests, skipped tests, and missing pytest.
- Parser tests use canned JUnit XML across Windows and Linux.
- Any future selection feature requires a full-suite oracle and a false-pass
  evaluation before it can be enabled.
