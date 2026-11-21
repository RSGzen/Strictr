# Blueprint: Check command

- Spec: `specs/active/003-check-command/spec.md`
- Status: approved
- Owner: Ge Rui Sen

## Approach

Build the full v0.1 vertical slice in contract order:

1. Lock the machine-readable contract with a JSON Schema and golden fixtures.
2. Build the pure core (models, status/fail-fast, limits, redaction, discovery).
3. Build the subprocess runner and the four tiers behind the `Tier` and
   `ToolRunner` ports.
4. Wire output and the CLI, then prove the public surface with black-box
   acceptance tests against real tools.

The implementation is deliberately a modular monolith. No plugin registry,
generic engine, async runtime, cache, daemon, or sandbox. Fail-closed semantics
are tested at every boundary. A worker may not invent a public interface or
change the contract; the blueprint and schema are the shared interface.

Durable role scopes, read/write ranges, test ownership, and handoff rules are
defined in `docs/sdd-workflow.md`. This blueprint records only the 003-specific
work units, commands, and decisions.

### Milestones

Do not wait for all four tiers before proving the command end to end. After
T-7, run a walking skeleton against a real fixture with discovery, the runner,
Tier 0, ruff, and minimal JSON output. T-8 and T-9 add types and tests to that
working path; T-10 and T-11 harden output and wiring. T-12 is the final
black-box pass, not the first integration attempt.

Open the draft PR after WU-2 (the first end-to-end Tier 0 + ruff slice).
Traceability may stay red until every AC-tagged test exists near the end; do not
merge until WU-6 passes.

### Work units

Tasks are numbered for reference; execution follows these units. T-10 and T-11
start against the two-tier pipeline and are extended as T-8 and T-9 land.

| Unit | Tasks | Outcome |
|---|---|---|
| WU-1 | T-2, T-3, T-4, T-5 | Contract, core, discovery, and runner foundation |
| WU-2 | T-6, T-7, T-10, T-11 | First end-to-end command: Tier 0, ruff, JSON/human output, CLI; open draft PR |
| WU-3 | T-8 | Type-checker selection, parsers, and tier added to the pipeline |
| WU-4 | T-9 | Full pytest tier added to the pipeline |
| WU-5 | T-12 | Acceptance, failure-mode, path, and timeout coverage |
| WU-6 | T-13 | Docs, full gate, traceability, convergence check |

### PR and integration policy

- One spec, one integration branch (`feat/003-check-command`), one PR.
- Sequential workers commit to the integration branch; do not run parallel
  workers on overlapping files.
- The draft PR opens after WU-2. A red traceability check before all AC tests
  exist is expected and must not be worked around by weakening the checker.
- Do not merge until the WU-6 full gate, acceptance suite, and traceability
  check pass. The human owner merges.
- If the single integration PR becomes unreviewable, split the work into
  separate specs with independent AC sets. Do not open partial PRs for one spec:
  the traceability checker requires every AC in the spec on every PR.

## Modules and boundaries

| Module | Responsibility | Change |
|---|---|---|
| `src/strictr/core/models.py` | Statuses, diagnostics, tier results, scope, envelope dataclasses | New |
| `src/strictr/core/paths.py` | Root-relative POSIX path normalization | New |
| `src/strictr/core/text.py` | Message truncation and secret redaction | New |
| `src/strictr/core/protocols.py` | `Tier` and `ToolRunner` ports | New |
| `src/strictr/core/errors.py` | Discovery, config, tool, and output errors | New |
| `src/strictr/core/pipeline.py` | Ordered execution, fail-fast, status precedence | New |
| `src/strictr/core/discovery.py` | Root resolution, targets, Git/walk discovery, counters | New |
| `src/strictr/tools/runner.py` | Subprocess execution, timeout, process tree, UTF-8 capture | New |
| `src/strictr/tools/parsers/ruff.py` | Pure ruff JSON parser | New |
| `src/strictr/tools/parsers/mypy.py` | Pure mypy JSON Lines parser | New |
| `src/strictr/tools/parsers/pyright.py` | Pure pyright JSON parser | New |
| `src/strictr/tools/parsers/pytest_junit.py` | Pure JUnit XML parser | New |
| `src/strictr/tiers/ast_tier.py` | Tier 0 syntax parsing | New |
| `src/strictr/tiers/ruff_tier.py` | Tier 1a ruff integration | New |
| `src/strictr/tiers/types_tier.py` | Type-checker selection, execution, normalization | New |
| `src/strictr/tiers/pytest_tier.py` | Tier 2 full-suite pytest integration | New |
| `src/strictr/output/json_output.py` | Contract envelope serialization | New |
| `src/strictr/output/human.py` | Concise human rendering | New |
| `src/strictr/app.py` | Explicit wiring of discovery, tiers, and result assembly | New |
| `src/strictr/cli.py` | argparse, output switch, exit codes | New |
| `src/strictr/__main__.py` | `python -m strictr` entry point | New |
| `docs/architecture/verification-contract.schema.json` | Machine-readable v1 schema | New |
| `docs/sdd-workflow.md` | Durable Planner/Task Worker/Integrator contract | New |
| `tests/conftest.py` | Ignore fixture projects during collection | Modified |
| `pyproject.toml` | Console script, ruff fixture exclude, test-only `jsonschema` | Modified |
| `README.md`, `CHANGELOG.md`, `AGENTS.md`, architecture docs | Usage and status | Modified |

Import rules remain as approved: `core` imports only the standard library;
`tiers` may import `core` and `tools`; `tools` may import `core.errors` and
`core.models`; `output` may import `core`; `cli`/`app` wire everything.

## Contracts

### CLI

```text
strictr check [paths ...] [--json] [--type-checker mypy|pyright|none]
              [--timeout SECONDS]
strictr --version
python -m strictr check ...
```

- No paths means `.`.
- `--timeout` is one positive float that overrides every subprocess tier and
  version check for the run. Defaults remain ADR 0007: Tier 0 10 s, ruff 30 s,
  types 180 s, pytest 300 s.
- `--json` writes one compact UTF-8 JSON object plus a newline to stdout and
  nothing else to stdout.
- Human output is concise and never colored in v0.1.
- Argparse usage errors write to stderr and exit 2.

### Root and targets

1. Walk up from the current directory to the first directory containing
   `pyproject.toml` or `.git`. That is the root.
2. If no marker exists above the current directory, inspect each target's
   nearest marker. Exactly one unique root may be selected; multiple roots are
   a discovery error.
3. If no marker exists for any target, use the common ancestor of the targets
   (file targets use their parent), or the current directory when there are no
   targets.
4. Resolve targets and reject missing paths or paths outside the root.
5. Normalize targets to root-relative POSIX paths, sorted and de-duplicated. A
   no-path invocation records `["."]`.

### Discovery

- Explicit file targets are included even when Git ignores them.
- Directory targets inside a Git root use
  `git -C <root> ls-files -co --exclude-standard -z -- <targets>` and parse
  NUL-delimited bytes with `os.fsdecode`.
- Without Git, use `os.walk(followlinks=False)` and prune `.git`, `.hg`, `.svn`,
  `.venv`, `venv`, `env`, `__pycache__`, `.mypy_cache`, `.pytest_cache`,
  `.ruff_cache`, `.tox`, `.nox`, `build`, `dist`, `node_modules`, `.eggs`, and
  `*.egg-info`.
- A failing Git command falls back to the walk and adds a warning.
- Include only existing `.py` and `.pyi` files. Deleted tracked files are
  ignored. Symlinked files that resolve outside the root are an error; directory
  symlinks are not followed.
- `files_checked` is the number of discovered Python files.
- `files_skipped` counts enumerated candidate files rejected by Strictr's own
  filters, such as escaping symlinks or non-regular files. Gitignored files are
  outside the candidate set and are not counted.
- Zero discovered files is an error, not a pass.

### Tier IDs and tools

| Tier | ID | Command |
|---|---|---|
| 0 | `tier0` | stdlib `ast.parse` |
| 1a | `tier1-ruff` | `ruff check --output-format=json --no-fix -- <targets>` |
| 1b | `tier1-types` | `sys.executable -m mypy --output=json -- <targets>` or `sys.executable -m pyright --outputjson <targets>` |
| 2 | `tier2-pytest` | `sys.executable -m pytest -q -o junit_family=xunit1 --junitxml=<temp>` |

All commands run from the project root with the inherited environment and an
argument list; never a shell.

### Type-checker selection

Follow ADR 0005 exactly:

1. `--type-checker` wins.
2. Mypy config: `mypy.ini`, `.mypy.ini`, `pyproject.toml [tool.mypy]`, or
   `setup.cfg [mypy]`.
3. Pyright config: `pyrightconfig.json` or `pyproject.toml [tool.pyright]`.
4. Mypy available (`sys.executable -m mypy --version` succeeds).
5. Pyright available (`sys.executable -m pyright --version`, then
   `shutil.which("pyright")`).
6. Otherwise `skipped` with `no type checker found`; overall `partial`.

Both configured selects mypy plus a warning. A configured but unavailable
checker is `error`. `--type-checker none` is `skipped` with
`disabled_by_user`, is recorded, and does not make the result `partial`. Record
`meta.checker` and `meta.selection` (`explicit`, `config`, or `available`).

### pytest behavior

- Always run the full suite; targets do not narrow pytest.
- JUnit XML goes to a `tempfile.TemporaryDirectory` outside the repository and
  is deleted after parsing.
- `-o junit_family=xunit1` is required so testcase `file` and `line`
  attributes exist. The parser also tolerates xunit2 and missing attributes.
- Exit 0 passes unless parsed diagnostics contain errors.
- Exit 1 fails when diagnostics contain errors; exit 1 with no error evidence
  is invalid output and therefore `error`.
- Exit 5 is `skipped` with `no tests collected`.
- Exit 2, 3, or 4 is `error`; parse any available error diagnostics.
- Missing pytest: if a discovered file matches `test_*.py` or `*_test.py`, or a
  pytest config exists (`pytest.ini`, `tox.ini [pytest]`, `setup.cfg
  [tool:pytest]`, `pyproject.toml [tool.pytest.ini_options]`), the tier is
  `error`; otherwise it is `skipped` with `no tests collected`.
- Invalid or missing XML when pytest did not exit 5 is `error`.

### Status and exit model

- Tier statuses: `pass`, `fail`, `skipped`, `error`.
- Overall: `error > fail > partial > pass`.
- A required skipped tier makes the result `partial`; a deliberate
  `disabled_by_user` skip or `no tests collected` does not.
- Fail-fast stops after the first `fail` or `error`. Later tiers are `skipped`
  with `earlier_tier_failed` or `earlier_tier_error`.
- Exit codes: `pass` 0; `fail` 1; `partial` and `error` 2.

### Tool-level errors

Diagnostics with no file location are not invented. Tier-level tool failures
use `skipped_reason` plus a capped, redacted `meta.error`:

| Failure | Tier status | `skipped_reason` |
|---|---|---|
| Missing executable | `error` | `<tool> not found` |
| Timeout | `error` | `tool timeout` |
| Non-zero fatal exit | `error` | `tool failed` |
| Invalid JSON/XML | `error` | `invalid tool output` |
| Discovery failure | `error` on `tier0` | `discovery failed` |
| No Python files | `error` on `tier0` | `no Python files found` |

### Envelope and schema

- `schema_version` is `"1"`; `tool.version` is `strictr.__version__` (`0.0.0`).
- All four tiers appear in execution order, including skipped tiers.
- `scope` always contains `root`, `targets`, `files_checked`, `files_skipped`,
  `tests_collected`, `tests_run`, and `tests_skipped`; unrun counts are 0.
- `trust` is always present with `sandboxed: false` and the approved warning.
- `warnings` contains non-fatal messages only.
- JSON is compact (`separators=(",", ":")`), UTF-8, and newline-terminated.
- The schema lives at
  `docs/architecture/verification-contract.schema.json` and is test-only; it is
  not loaded at runtime.

### Human output

```text
PASS  12 files checked in 1200 ms
  tier0        pass      12 ms
  tier1-ruff   pass      84 ms
  tier1-types  pass     300 ms
  tier2-pytest pass     804 ms
```

For a failure, print the status line, tier lines, and up to the first five
diagnostics of the failing tier. Print `skipped` reasons for partial/error.
Print `... N more diagnostics (use --json)` when truncated. Warnings and the
trust warning go to stderr. Exit code follows the contract.

## Failure modes

| Failure | Behavior | Test |
|---|---|---|
| Target missing or outside root | `error`, tier0 `discovery failed`, exit 2 | `test_target_outside_root` |
| No Python files | `error`, `no Python files found`, exit 2 | `test_empty_project_is_error` |
| Syntax error | `fail` with path/line/column, later tiers skipped | `test_syntax_error` |
| Ruff findings | `fail`, later tiers skipped | `test_ruff_failure` |
| Ruff missing/crash/timeout/invalid JSON | `error`, later tiers skipped | unit runner/parser tests |
| Type errors | `fail`, pytest skipped | `test_type_failure` |
| No type checker | `partial`, exit 2 | unit selection test |
| Configured checker missing | `error`, exit 2 | unit selection test |
| `--type-checker none` | `skipped: disabled_by_user`, not partial | unit selection test |
| Test failures | `fail` with test node IDs and file/line | `test_pytest_failure` |
| No tests | `skipped: no tests collected`, pass possible | `test_no_tests` |
| pytest exit 2/3/4 | `error` | unit pytest tier test |
| Invalid JUnit XML | `error` | unit parser/tier test |
| Tool timeout | `error`, process tree terminated | `test_timeout` |
| Unexpected tier exception | `error`, fail closed | unit pipeline test |
| Invalid CLI arguments | stderr message, exit 2 | `test_cli_usage_error` |

## Security and trust boundaries

- v0.1 is local execution and explicitly not a sandbox. The trust warning is
  mandatory in human mode; JSON always carries the trust object.
- No shell, no `shell=True`, no command strings.
- Targets are confined to the root; escaping symlinks are rejected.
- Temporary JUnit files live outside the repository and are cleaned up.
- Diagnostics and `meta.error` are capped and redacted for common credentials.
- No telemetry, no network access, no secret persistence.
- Running pytest or a type checker can execute arbitrary code with the user's
  privileges. This is documented and must not be described as isolation.

## Test ownership and method

Durable role definitions and handoff rules are in `docs/sdd-workflow.md`. SDD
works best here as a hybrid, not as a planner pre-writing every test:

- **Planner-owned, written before implementation:** the spec, blueprint, JSON
  Schema, golden fixtures, AC-to-test map, and the cross-cutting black-box
  contract tests (`tests/unit/test_contract.py`,
  `tests/acceptance/test_cli_contract.py`, `tests/acceptance/test_exit_codes.py`,
  `tests/unit/test_check_docs.py`). These define the public surface and must not
  be weakened by a worker.
- **Worker-owned, test-first per task:** each task worker writes or extends the
  failing tests for its own task, runs them, implements the minimum, reruns,
  and updates the blueprint checkbox. Examples: discovery, runner, parsers,
  tiers, output rendering.
- **Integrator-owned:** the full acceptance suite, failure-mode pass, format,
  lint, types, full tests, traceability, and docs.

Pre-writing every unit test before the interfaces exist tends to encode
guessed internals and then force the implementation to match the guess. Writing
no tests first lets workers weaken the contract. The split above keeps the
contract fixed and lets each vertical slice prove itself.

One worker per task, sequential by default. Parallel workers are acceptable only
when their files are disjoint and they share the locked interfaces; this spec
is too integrated for safe parallel execution. A final integration pass is
mandatory but is not the first time the suite runs: every task runs its exact
command, and the full gate runs after each merge-sized task group.

## Test plan

| AC | Layer | Test module | Command | Status |
|---|---|---|---|---|
| AC-1 | acceptance | `tests/acceptance/test_cli_contract.py` | `uv run pytest tests/acceptance/test_cli_contract.py -q` | todo |
| AC-2 | acceptance, contract | `tests/acceptance/test_cli_contract.py`, `tests/unit/test_contract.py` | same | todo |
| AC-3 | acceptance | `tests/acceptance/test_human_output.py` | `uv run pytest tests/acceptance/test_human_output.py -q` | todo |
| AC-4 | acceptance | `tests/acceptance/test_exit_codes.py` | `uv run pytest tests/acceptance/test_exit_codes.py -q` | todo |
| AC-5 | unit, acceptance | `tests/unit/test_discovery.py`, `tests/acceptance/test_discovery.py` | `uv run pytest tests/unit/test_discovery.py tests/acceptance/test_discovery.py -q` | todo |
| AC-6 | unit, acceptance | same | same | todo |
| AC-7 | unit, acceptance | `tests/unit/test_tier0.py`, `tests/acceptance/test_tiers.py` | `uv run pytest tests/unit/test_tier0.py -q` | todo |
| AC-8 | unit, acceptance | `tests/unit/test_ruff.py`, `tests/acceptance/test_tiers.py` | `uv run pytest tests/unit/test_ruff.py -q` | todo |
| AC-9 | unit | `tests/unit/test_types.py` | `uv run pytest tests/unit/test_types.py -q` | todo |
| AC-10 | unit, acceptance | `tests/unit/test_types.py`, `tests/acceptance/test_tiers.py` | same | todo |
| AC-11 | unit, acceptance | `tests/unit/test_pytest.py`, `tests/acceptance/test_tiers.py` | `uv run pytest tests/unit/test_pytest.py -q` | todo |
| AC-12 | unit, acceptance | `tests/unit/test_core.py`, `tests/acceptance/test_exit_codes.py` | same | todo |
| AC-13 | unit, acceptance | `tests/unit/test_runner.py`, `tests/acceptance/test_timeout.py` | `uv run pytest tests/unit/test_runner.py -q` | todo |
| AC-14 | unit | `tests/unit/test_core.py` | `uv run pytest tests/unit/test_core.py -q` | todo |
| AC-15 | unit | `tests/unit/test_contract.py` | `uv run pytest tests/unit/test_contract.py -q` | todo |
| AC-16 | unit | `tests/unit/test_check_docs.py` | `uv run pytest tests/unit/test_check_docs.py -q` | todo |

Fixture projects:

| Fixture | Purpose |
|---|---|
| `tests/fixtures/projects/clean` | Source plus passing test; full pass |
| `tests/fixtures/projects/syntax-error` | Tier 0 failure |
| `tests/fixtures/projects/ruff-error` | Tier 1a failure |
| `tests/fixtures/projects/type-error` | Tier 1b failure with mypy |
| `tests/fixtures/projects/test-failure` | Tier 2 failure |
| `tests/fixtures/projects/no-tests` | pytest exit 5 skip |
| `tests/fixtures/projects/empty` | No Python files |
| `tests/fixtures/projects/path with space-ü` | Path handling |
| `tests/fixtures/projects/timeout` | Hung test for timeout |

All fixture projects are copied to `tmp_path` before any tool runs. No fixture
is executed in place. Fixture discovery is tested with a temporary Git
repository created with `git init`.

## Tasks

- [x] T-1: Finalize the spec and blueprint, resolve owner questions, and set the
  spec status to `approved` — verify: owner approval and
  `uv run pytest tests/unit/test_architecture_docs.py -q` — AC: AC-1..AC-16
- [ ] T-2: Add the contract JSON Schema, golden envelope fixtures, and
  `tests/unit/test_contract.py`; add test-only `jsonschema` — verify:
  `uv run pytest tests/unit/test_contract.py -q` — AC: AC-2, AC-15
- [ ] T-3: Add models, path/text helpers, limits, redaction, and the pipeline
  with fake tiers — verify: `uv run pytest tests/unit/test_core.py -q` —
  AC: AC-4, AC-12, AC-14
- [ ] T-4: Add root resolution, target confinement, Git/walk discovery, and
  counters — verify: `uv run pytest tests/unit/test_discovery.py -q` —
  AC: AC-5, AC-6
- [ ] T-5: Add the subprocess runner with UTF-8 capture, timeouts, and process
  tree termination — verify: `uv run pytest tests/unit/test_runner.py -q` —
  AC: AC-13
- [ ] T-6: Add Tier 0 syntax parsing — verify:
  `uv run pytest tests/unit/test_tier0.py -q` — AC: AC-7
- [ ] T-7: Add the ruff parser and tier — verify:
  `uv run pytest tests/unit/test_ruff.py -q` — AC: AC-8
- [ ] T-10: Add JSON and human renderers; start with the two-tier pipeline and
  extend as later tiers land — verify:
  `uv run pytest tests/unit/test_output.py -q` — AC: AC-2, AC-3, AC-14
- [ ] T-11: Wire the app, CLI, `__main__`, and console script; start with Tier 0
  and ruff, then extend as later tiers land — verify:
  `uv run pytest tests/acceptance/test_cli_contract.py -q` and
  `uv run strictr --version` — AC: AC-1..AC-4
- [ ] T-8: Add type-checker selection, mypy/pyright parsers, and the type tier to
  the pipeline — verify: `uv run pytest tests/unit/test_types.py -q` —
  AC: AC-9, AC-10
- [ ] T-9: Add the JUnit parser and pytest tier to the pipeline — verify:
  `uv run pytest tests/unit/test_pytest.py -q` — AC: AC-11
- [ ] T-12: Add fixture excludes to `pyproject.toml` and `tests/conftest.py`,
  then add acceptance fixtures and black-box tests for tiers, discovery, failure
  modes, paths, and timeout — verify: `uv run pytest tests/acceptance -q` —
  AC: AC-1..AC-15
- [ ] T-13: Add docs, then run the full gate and traceability — verify:
  `uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest -q`
  and the traceability command — AC: AC-16

## Work unit protocol

Role scopes, read/write ranges, and the task brief template are in
`docs/sdd-workflow.md`. Each worker session:

1. Read `AGENTS.md`, `docs/sdd-workflow.md`, the spec, this blueprint, the
   contract, and the task's linked modules/tests.
2. Confirm the branch is `feat/003-check-command` and the worktree is clean.
3. Write or extend the failing test first; run the exact task command and record
   the expected failure. A test that has never failed is not evidence.
4. Implement the minimum; rerun the exact command; do not weaken, skip, or
   delete tests.
5. Run `uv run ruff format .`, `uv run ruff check .`, and `uv run mypy` for
   touched modules before committing.
6. Update only the T-task checkbox after its command passes.
7. Commit with a Conventional Commit subject and a `Spec: 003` trailer; include
   `Refs: AC-n` for the covered criteria.

Workers must not edit the spec, blueprint, contract, schema, or public module
interfaces to make a test pass. Raise the conflict to the planner instead.

## Rollback

Revert the feature-branch commits. The CLI is additive, there is no persisted
data or migration, and no existing user behavior is replaced. If only the
console script causes trouble, remove `[project.scripts]` and the entry point
while keeping the library modules. Archive the spec only after the full gate,
traceability, and acceptance suite pass.

## Open technical questions

- [ ] Real pyright is not available in CI; pyright coverage is parser unit tests
  plus a fake runner. Document this limitation rather than claiming parity —
  owner, before AC-10 is marked done.
- [ ] The Tier 0 10 s budget is checked between files and cannot interrupt a
  single pathological `ast.parse`; a subprocess parser worker is deferred —
  owner, accept or upgrade before release.
- [ ] `files_skipped` does not count Gitignored files; confirm the contract
  interpretation is acceptable or propose an ADR — owner, before AC-5 is
  marked done.
- [ ] The timeout acceptance test must assert a generous bound to avoid CI
  flakiness and is the single deliberate `sleep()` exception in the suite —
  integrator, T-12.
- [ ] Nested-project root selection uses the current directory's marker first;
  confirm this is the intended monorepo behavior — owner, before AC-5 is
  marked done.

## Retrospective

Fill after completion: what worked, what did not, one change.
