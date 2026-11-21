# ADR 0009: v0.1 execution refinements

- Status: accepted
- Date: 2026-11-21
- Decision makers: Ge Rui Sen
- Related: [ADR 0003](0003-subprocess-tool-execution.md), [ADR 0005](0005-type-checker-selection.md), [ADR 0006](0006-pytest-integration.md), [ADR 0007](0007-trust-boundary-and-timeouts.md), spec `003`

## Context

Implementation research for the `check` command exposed five places where the
accepted v0.1 decisions need a precise refinement:

- The PyPI `pyright` wrapper supports `python -m pyright`, which is more reliable
  on Windows than a `.cmd` shim.
- pytest's default JUnit `xunit2` format omits `testcase file` and `line`;
  `xunit1` includes them.
- Tier 0 runs `ast.parse` in-process, so a hard process kill is not available.
- The CLI timeout override was specified for tiers but also has to bound version
  checks, or a hung version command can block the run.
- Tool versions belong in the tier result; the contract's `environment` object
  remains python, platform, and root.

These refinements preserve the original decisions and do not change the public
verification contract.

## Decision drivers

- Parity with the project's tools.
- Fail-closed behavior on Windows and Linux.
- No runtime dependencies.
- Honest claims about timeouts and isolation.
- A stable envelope.

## Considered options

1. **Keep the ADR text unchanged.**
   Simple, but the implementation would contradict the accepted records.
2. **Replace all four ADRs.**
   Clean history, but these are refinements, not reversals; four replacements
   add ceremony without changing the decisions.
3. **One refinement ADR.**
   Records the implementation-level corrections and points the original ADRs at
   it.

## Decision

Adopt one refinement ADR:

1. **Pyright invocation.** Prefer `sys.executable -m pyright` when the Python
   wrapper is importable; otherwise resolve `pyright` with `shutil.which` and
   run the executable. Record the resolved version in the tier result.
2. **pytest JUnit format.** Run
   `python -m pytest -q -o junit_family=xunit1 --junitxml=<temp>`. The parser
   also tolerates xunit2 and missing attributes.
3. **Tier 0 budget.** Tier 0 is an in-process budget checked between files. It
   cannot interrupt a single pathological `ast.parse`; a subprocess parser
   worker is deferred. The tier is never reported as `pass` after exceeding the
   budget.
4. **Timeout scope.** A single `--timeout` value bounds every subprocess tier and
   its version check. Tier 0 uses the same budget between files.
5. **Version location.** Tool versions are recorded in each tier's `tool`
   object. `environment` stays `python`, `platform`, and `root`; the contract is
   not widened.

## Consequences

Good:

- Windows pyright invocations avoid `.cmd` quoting surprises.
- Pytest failures carry file and line information.
- Timeout claims are honest: hard kills apply only to subprocess tools.
- Tool version capture does not require an envelope change.

Bad:

- Tier 0 is not hard-killable; a pathological parse can still hang.
- The parser must support two JUnit shapes.
- Version checks add a process startup when a tool runs.

## Confirmation

- Tests cover pyright module and executable resolution.
- Canned XML tests cover xunit1 and xunit2.
- Tier 0 budget tests cover the over-budget path.
- Timeout tests cover a hung subprocess.
- Contract tests still validate against schema version 1.
