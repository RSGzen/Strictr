# ADR 0003: Subprocess tool execution and project environment

- Status: accepted
- Date: 2026-11-21
- Decision makers: Ge Rui Sen

## Context

Strictr wraps `ruff`, a Python type checker, and `pytest`. It must preserve their
configuration, plugins, and version behavior. The tools can be used through
Python APIs or as subprocesses. The target project may have its own virtual
environment, and Strictr may be installed in that environment or elsewhere.

## Decision drivers

- Parity with the commands a developer or CI would run.
- No reimplementation of tool behavior.
- Avoid coupling Strictr's dependency versions to the project's.
- Windows and Linux compatibility.
- Actionable errors when a tool is missing.

## Considered options

1. **Import tool APIs directly.**
   Faster in theory, but couples to internal APIs, bypasses CLI configuration,
   and risks different plugin behavior.
2. **Bundle specific tool versions with Strictr.**
   Reproducible, but can disagree with the project's environment and lock users
   into versions.
3. **Run project tools as subprocesses in the project environment.**
   Preserves parity and configuration; accepts process startup cost.
4. **Use shell command strings.**
   Convenient, but quoting, injection, and Windows behavior are worse.

## Decision

Run tools as subprocesses, using the project environment:

- Execute from the project root with the project's configuration.
- Use `sys.executable -m mypy` and `sys.executable -m pytest` so the current
  interpreter and site-packages are used.
- Resolve `ruff` and `pyright` with `shutil.which` from the current environment.
- Use argument lists, never `shell=True`.
- Capture stdout/stderr as UTF-8 with replacement on decoding errors.
- Record the resolved tool version in the result.
- Never import ruff/mypy/pyright/pytest as libraries in the product path.

Commands for v0.1:

```text
ruff check --output-format=json --no-fix <targets>
python -m mypy --output=json <targets>
pyright --outputjson <targets>
python -m pytest -q --junitxml=<temp>
```

Exact parser compatibility is covered by canned-output tests. A configured tool
that is not installed is an `error`. A tool that is not configured is handled by
the tier policy (ADR 0005 for types, ADR 0006 for tests).

## Consequences

Good:

- Findings match the project's own toolchain.
- Tool upgrades do not require a Strictr release.
- The subprocess runner is a single testable seam.

Bad:

- Process startup is a real cost; v0.1 accepts it.
- Users must install Strictr in an environment where the tools are available.
- Output formats can change between tool versions and must be tested.

## Confirmation

- Parity tests compare Strictr's normalized findings with direct tool runs.
- Missing-tool tests assert `error`, not `pass`.
- Windows and Linux CI run the same command construction tests.
- Installation documentation says to run Strictr inside the project's dev
  environment.
