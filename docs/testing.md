# Testing Guide

## Principle

Tests are derived from acceptance criteria, not from source files. A spec is
implemented when every AC has a passing automated test and the regression suite
is green.

Phase 2 of `docs/sdd-workflow.md` writes and freezes the failing AC-tagged tests.
Phase 3 implements against them and does not edit them. Phase 4 adds integration,
path, timeout, and failure-mode tests.

Each test module declares the spec that owns it, and each AC test carries the AC:

```python
pytestmark = pytest.mark.spec("003")


@pytest.mark.ac("AC-1")
def test_syntax_error_reports_location(): ...
```

`tests/conftest.py` writes a spec-scoped `build/ac-tests.json` at collection. The
traceability check reads only the current spec's entries, so AC IDs may repeat
across specs. It fails when an AC has no test or a tag in that spec has no
matching AC.

This proves a test exists, not that it is good. Review still matters.

## Layers

| Layer | Purpose | Location |
|---|---|---|
| Acceptance | Prove public behavior from an AC | `tests/acceptance/` |
| Unit | Cover parsers, branches, normalization | `tests/unit/` |
| Contract | Protect the JSON envelope and schema | `tests/unit/`, `tests/acceptance/` |
| Failure mode | Prove trust boundaries fail safely | `tests/unit/`, `tests/acceptance/` |
| Regression | Keep a fixed bug fixed | Near the affected layer |

Do not re-test `ruff`, `mypy`, or `pytest`. Use canned output for parsers and
one real smoke test per integration.

## Test-first evidence

For behavior changes:

1. Write the acceptance test.
2. Run it. It must fail for the expected assertion, not an import error.
3. Record the command and failure in the blueprint or PR.
4. Implement the minimum.
5. Run it again; it passes.
6. Refactor under green.
7. Add unit and failure-mode tests.

A test that has never failed is not evidence.

## Fixtures

- Keep fixture projects tiny and self-contained under `tests/fixtures/projects/`.
- Copy fixtures to `tmp_path` before running tools. Tools write caches; never
  dirty the repository.
- No network access.
- No shared mutable state between tests.
- No `sleep()`; use timeouts and stub commands.
- Test paths with spaces, Unicode, and non-UTF8 input.

## Failure modes

At minimum, test:

- missing tool
- tool crash
- timeout
- invalid JSON from a tool
- empty project
- unreadable or missing path
- partial verification (a skipped tier must not be reported as a pass)

## Determinism

- Do not assert timings.
- Do not put versions or absolute paths in golden files.
- Normalize paths to `/` in machine-readable output.
- Sort diagnostics deterministically before comparing.
- Run tests on Windows and Linux in CI.

## Commands

```powershell
uv run pytest
uv run pytest -q
uv run pytest --collect-only -q
uv run pytest tests/unit/test_traceability.py -q
```

Coverage is a signal, not a gate. When introduced, review uncovered branches in
parsers, error handling, and security paths rather than chasing 100%.
