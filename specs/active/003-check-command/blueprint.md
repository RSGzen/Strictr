# Blueprint: Check command

- Spec: `specs/active/003-check-command/spec.md`
- Status: approved
- Revised: 2026-11-21 — frozen core interfaces, warnings, truncation, counts, ADR 0008/0009/0010, single-agent phase workflow
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

The single-agent phase workflow is defined in `docs/sdd-workflow.md`. This
blueprint records 003-specific design, task briefs, and verification commands;
`progress.md` records the current phase and session state.

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

Tasks are numbered for reference; WUs are checkpoints, not session scope.
Phases 2–4 run per task or small slice. T-10 and T-11 start against the two-tier
pipeline and are extended as T-8 and T-9 land.

| Unit | Tasks | Outcome |
|---|---|---|
| WU-1 | T-2, T-3, T-4, T-5 | Contract, core, discovery, and runner foundation |
| WU-2 | T-6, T-7, T-10, T-11 | First end-to-end command: Tier 0, ruff, JSON/human output, CLI; open draft PR |
| WU-3 | T-8 | Type-checker selection, parsers, and tier added to the pipeline |
| WU-4 | T-9 | Full pytest tier added to the pipeline |
| WU-5 | T-12 | Acceptance, failure-mode, path, and timeout coverage |
| WU-6 | T-13 | Docs, full gate, traceability, convergence check |

### Phase execution

Phases 2–4 run per task or small slice, not across the whole spec at once.
WUs are checkpoints. Phase 1 and Phase 5 cover the whole spec.

| Phase | Scope | Output |
|---|---|---|
| 1 Specify & Plan | Whole spec | `spec.md`, `blueprint.md`, `progress.md`; no `src/` writes |
| 2 Stub & Test | Each task/slice | Annotated stubs, failing AC-tagged tests, frozen test commit |
| 3 Implement & Reconcile | Each task/slice | Implementation until frozen tests pass |
| 4 Integrate & Verify | Task/slice plus WU-5 | Acceptance and failure-mode tests; docs/changelog; PR readiness |
| 5 Closeout & Audit | Whole spec | Read-only audit, full gate, traceability; archive after merge |

WU-2 Phase 2 also writes the CLI contract/human/exit tests. WU-6 Phase 2 writes
the docs contract test. Separate contract-test sessions are folded into those
Phase 2 steps.

### PR and integration policy

- One spec, one integration branch (`feat/003-check-command`), one PR.
- ADR 0010 records the owner-approved one-time size exception for 003. The
  default size and branch-age targets return for later specs.
- Sequential work; do not run parallel writers on overlapping files.
- The draft PR opens after WU-2. A red traceability check before all AC tests
  exist is expected and must not be worked around by weakening the checker.
- Do not merge until the WU-6 full gate, acceptance suite, and traceability
  check pass. The human owner merges.
- If this single integration PR becomes unreviewable, split the work into
  separate specs with independent AC sets. Do not open partial PRs for one spec:
  the traceability checker requires every AC in the spec on every PR.

## Modules and boundaries

| Module | Responsibility | Change |
|---|---|---|
| `src/strictr/core/__init__.py` | Core package marker | New |
| `src/strictr/core/models.py` | Statuses, diagnostics, tier/scope/envelope models, `DiscoveryResult`, `ToolResult` | New |
| `src/strictr/core/paths.py` | Root-relative POSIX path normalization | New |
| `src/strictr/core/text.py` | Message truncation and secret redaction | New |
| `src/strictr/core/protocols.py` | `Tier` and `ToolRunner` ports | New |
| `src/strictr/core/errors.py` | Discovery, config, and tool errors | New |
| `src/strictr/core/pipeline.py` | Ordered execution, fail-fast, status precedence | New |
| `src/strictr/core/discovery.py` | Root resolution, targets, Git/walk discovery, counters | New |
| `src/strictr/tools/__init__.py` | Tools package marker | New |
| `src/strictr/tools/runner.py` | Subprocess execution, timeout, process tree, UTF-8 capture | New |
| `src/strictr/tools/parsers/__init__.py` | Parsers package marker | New |
| `src/strictr/tools/parsers/ruff.py` | Pure ruff JSON parser | New |
| `src/strictr/tools/parsers/mypy.py` | Pure mypy JSON Lines parser | New |
| `src/strictr/tools/parsers/pyright.py` | Pure pyright JSON parser | New |
| `src/strictr/tools/parsers/pytest_junit.py` | Pure JUnit XML parser | New |
| `src/strictr/tiers/__init__.py` | Tiers package marker | New |
| `src/strictr/tiers/ast_tier.py` | Tier 0 syntax parsing | New |
| `src/strictr/tiers/ruff_tier.py` | Tier 1a ruff integration | New |
| `src/strictr/tiers/types_tier.py` | Type-checker selection, execution, normalization | New |
| `src/strictr/tiers/pytest_tier.py` | Tier 2 full-suite pytest integration | New |
| `src/strictr/output/__init__.py` | Output package marker | New |
| `src/strictr/output/json_output.py` | Contract envelope serialization | New |
| `src/strictr/output/human.py` | Concise human rendering | New |
| `src/strictr/app.py` | Explicit wiring of discovery, tiers, and result assembly | New |
| `src/strictr/cli.py` | argparse, output switch, exit codes | New |
| `src/strictr/__main__.py` | `python -m strictr` entry point | New |
| `docs/architecture/verification-contract.schema.json` | Machine-readable v1 schema | New |
| `docs/sdd-workflow.md` | Single-agent phase workflow and context gates | New |
| `specs/active/003-check-command/progress.md` | Current phase, frozen tests, next command | New |
| `tests/conftest.py` | Ignore fixture projects during collection | Modified |
| `pyproject.toml` | Console script, ruff fixture exclude, test-only `jsonschema` | Modified |
| `README.md`, `CHANGELOG.md`, `AGENTS.md`, architecture docs | Usage and status | Modified |

Import rules: `core` imports only the standard library; `tiers` may import
`core` and `tools`; `tools` may import `core.models`, `core.paths`, and
`core.errors` per ADR 0008, but never `core.pipeline`, `core.discovery`,
`tiers`, `output`, or `cli`; `output` may import `core`; `cli`/`app` wire
everything.

### Frozen core interfaces (T-3)

T-3 records these interfaces in code and docstrings; later tasks consume them
without redefining them.

- Errors: `StrictrError`, `DiscoveryError`, `ConfigError`, `ToolError`,
  `ToolNotFoundError`, `ToolTimeoutError`, `InvalidToolOutput`.
- `ToolResult`: `command: tuple[str, ...]`, `returncode: int`, `stdout: str`,
  `stderr: str`, `duration_ms: int`.
- `ToolRunner`: `run(command: Sequence[str], *, cwd: Path, timeout: float)
  -> ToolResult` and `which(name: str) -> str | None`. Missing executable and
  timeout raise the named errors.
- `Tier`: `id`, `name`, `run(CheckContext) -> TierResult`.
- `CheckContext`: `root: Path`, `targets: tuple[str, ...]` (root-relative
  POSIX), `files: tuple[Path, ...]` (absolute), `timeout: float | None`,
  `type_checker: Literal["mypy", "pyright", "none"] | None`.
- `TierResult`: the contract fields plus an internal
  `warnings: tuple[str, ...]`, excluded from JSON serialization.
- `CheckResult`: `schema_version`, `tool`, `status`, `scope`, `tiers`, `timings`,
  `environment`, `trust`, `warnings`, plus `to_envelope()`. Warnings aggregate
  discovery warnings first, then tier warnings in execution order, deduplicated
  by exact string.
- `DiscoveryResult`: `root`, `targets`, `files`, `files_skipped`, `warnings`.
- `Scope`: test counts default to 0. Pipeline copies exactly
  `tests_collected`, `tests_run`, and `tests_skipped` from `tier2-pytest` meta;
  no other tier sets them.
- `run_pipeline(tiers, context, scope, initial_warnings) -> CheckResult` catches
  `Exception` per tier, not `BaseException`.
- `relative_posix(path, root)` is pure: it never resolves symlinks and never
  raises `DiscoveryError`. T-4 owns confinement and resolved-vs-display paths.
- Text helpers redact before capping. Message cap 2,000 and `meta.error` cap 500
  include the `" [truncated]"` marker.

## Contracts

### CLI

```text
strictr check [paths ...] [--json] [--type-checker mypy|pyright|none]
              [--timeout SECONDS]
strictr --version
python -m strictr check ...
```

- No paths means `.`.
- `--timeout` is one finite positive float that overrides every subprocess tier
  and version check for the run. Defaults remain ADR 0007: Tier 0 10 s, ruff
  30 s, types 180 s, pytest 300 s.
- Top-level `strictr --version` prints the package version and exits 0; the
  `check` parser does not accept `--version`.
- `--json` writes one compact UTF-8 JSON object plus a newline to stdout and
  nothing else to stdout.
- Human output is concise and never colored in v0.1.
- Argparse usage errors write to stderr and exit 2.
- `KeyboardInterrupt` and `SystemExit` are not converted to check results. A
  Ctrl+C exits 130 with a stderr message; no JSON envelope is emitted.

### Root and targets

1. Walk up from the current directory to the first directory containing
   `pyproject.toml` or `.git`. That is the root. This root wins for nested
   projects; targets inside it use this root.
2. If no marker exists above the current directory, inspect each target's
   nearest marker; for a file target, start at its parent. Exactly one unique
   root may be selected; multiple roots are a discovery error.
3. If no marker exists for any target, use the common ancestor of the targets
   (file targets use their parent), or the current directory when there are no
   targets.
4. Resolve targets for confinement and reject missing paths or paths outside the
   root. Resolution is for the confinement check only.
5. Record the original target paths, not resolved symlink targets, normalized to
   root-relative POSIX paths, sorted and de-duplicated. A no-path invocation
   records `["."]`.

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
  symlinks are not followed. Display paths are not resolved through symlinks.
- `files_checked` is the number of discovered Python files in the requested
  scope, including files offered to Tier 0 before a budget abort.
- `files_skipped` counts enumerated candidate files rejected by Strictr's own
  ignore rules or explicit filters, such as non-regular files. Escaping symlinks
  are errors, not skipped. Gitignored files are outside the candidate set and
  are not counted.
- Zero discovered files is an error, not a pass.

### Tier IDs and tools

| Tier | ID | Command |
|---|---|---|
| 0 | `tier0` | stdlib `ast.parse` |
| 1a | `tier1-ruff` | `ruff check --output-format=json --no-fix -- <targets>` |
| 1b | `tier1-types` | `sys.executable -m mypy --output=json -- <targets>` or `sys.executable -m pyright --outputjson <targets>` |
| 2 | `tier2-pytest` | `sys.executable -m pytest -q -o junit_family=xunit1 --junitxml=<temp>` |

All commands run from the project root with the inherited environment and an
argument list; never a shell. Pyright uses the module form when the Python
wrapper is importable, otherwise the `pyright` executable from `shutil.which`.

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
`meta.checker` and `meta.selection` (`explicit`, `config`, or `available`). The
checker name and version go in the tier `tool`; `environment` stays
`python`, `platform`, and `root`.

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
- `tests_collected`, `tests_run`, and `tests_skipped` are written to the tier
  `meta` under those exact keys; the pipeline copies them into `scope`.
- A testcase line of 0 or missing is normalized to 1; if the failure text gives
  a better `file:line`, use it.
- The test node ID is reconstructed from `file`, `classname`, and `name`:
  derive the module path from `file`; if `classname` equals the module, use
  `file::name`; if `classname` starts with the module plus `.`, use
  `file::<class path joined by ::>::name`; otherwise use `classname::name`.
- Pytest diagnostics use `source: "pytest"` and one of the stable codes
  `test-failure`, `test-error`, or `collection-error`; the `test` field is the
  node ID and `exception` is the exception class.
- Parsed test counts are copied to `scope` even when pytest exits 2/3/4 and XML
  is available; otherwise they remain 0. A collection error without a usable
  path uses `meta.error`, not a pathless diagnostic.

### Status and exit model

- Tier statuses: `pass`, `fail`, `skipped`, `error`.
- Overall: `error > fail > partial > pass`.
- A required skipped tier makes the result `partial`; a deliberate
  `disabled_by_user` skip or `no tests collected` does not.
- Fail-fast stops after the first `fail` or `error`. Later tiers are `skipped`
  with `earlier_tier_failed`; the overall status records whether the stop was a
  fail or an error.
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
| Unexpected tier exception | `error` | `internal error` |
| Discovery failure | `error` on `tier0` | `discovery failed` |
| No Python files | `error` on `tier0` | `no Python files found` |

`ToolNotFoundError` maps to `<tool> not found`, `ToolTimeoutError` to
`tool timeout`, and `InvalidToolOutput` to `invalid tool output`. `meta.error`
is redacted, capped at 500 characters, and included with the marker
`" [truncated]"` when capped. The pipeline catches `Exception`, not
`BaseException`, and stops after an internal error.

### Envelope and schema

- `schema_version` is `"1"`; `tool.version` is `strictr.__version__` (`0.0.0`).
- All four tiers appear in execution order, including skipped tiers. A
  discovery failure yields `tier0` `error` with `discovery failed` or
  `no Python files found`, and the other three tiers `skipped` with
  `earlier_tier_failed`.
- `scope` always contains `root`, `targets`, `files_checked`, `files_skipped`,
  `tests_collected`, `tests_run`, and `tests_skipped`; unrun counts are 0. The
  three test counts come only from `tier2-pytest` meta.
- `trust` is always present with `sandboxed: false` and the approved warning.
- `warnings` aggregates discovery and tier warnings in that order, deduplicated
  by exact string. It is non-fatal and does not change `status`. Human and JSON
  modes write warnings to stderr; JSON also carries the array. The trust warning
  is printed only in human mode.
- Argparse usage errors write stderr and exit 2 without an envelope.
- JSON is compact (`separators=(",", ":")`), UTF-8, and newline-terminated.
- The schema lives at
  `docs/architecture/verification-contract.schema.json` and is test-only; it is
  not loaded at runtime.

### Truncation and redaction

- Redact known secrets before any cap so truncation cannot split a secret.
- Cap each diagnostic message at 2,000 characters and each `meta.error` at 500,
  including a `" [truncated]"` marker in the cap. Sort after redaction/capping,
  then keep the first 20 diagnostics.
- `meta.truncated` is true when diagnostics are dropped or any message or
  `meta.error` is capped. `meta.total_diagnostics` is set only when diagnostics
  are dropped and records the pre-cap count; the contract's
  `total_diagnostics` is interpreted as the diagnostic-count limit only.
- Human output shows `N more diagnostics` when `total_diagnostics` exists and
  `some text truncated` otherwise.
- Fixed redaction patterns:
  - PEM private-key blocks:
    `-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----`
    with DOTALL.
  - AWS access-key IDs: `AKIA[0-9A-Z]{16}`.
  - GitHub tokens: `gh[pousr]_[A-Za-z0-9]{36,}` and
    `github_pat_[A-Za-z0-9_]{20,}`.
  - `sk-` keys: `sk-[A-Za-z0-9]{20,}`.
  - Slack tokens: `xox[baprs]-[A-Za-z0-9-]{10,}`.
  - JWTs: `eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`.
  - Bearer tokens: `(?i)\bBearer\s+[A-Za-z0-9._~+/-]{16,}=*`.
  - Key=value credentials:
    `(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd|secret)\b\s*[:=]\s*["']?([A-Za-z0-9_./+=-]{8,})`.
  - URL credentials: `(?i)\bhttps?://[^/\s:@]+:[^/\s@]+@`.
  Replace matches with `[REDACTED]`. These are the complete v0.1 patterns; no
  broader matching. Tests include negative cases such as `token budget`,
  `password policy`, and `sk-learn`.

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
Print `... N more diagnostics (use --json)` when count-truncated; print
`... some text truncated` when only messages or `meta.error` were capped.
Human mode prints warnings and the trust warning to stderr; JSON mode prints
warnings to stderr but not the trust warning. Exit code follows the contract.

## Failure modes

| Failure | Behavior | Test |
|---|---|---|
| Target missing or outside root | `error`, tier0 `discovery failed`, later tiers skipped, exit 2 | `test_target_outside_root` |
| No Python files | `error`, `no Python files found`, later tiers skipped, exit 2 | `test_empty_project_is_error` |
| Syntax error | `fail` with path/line/column, later tiers skipped | `test_syntax_error` |
| Tier 0 budget exceeded | `error`, later tiers skipped | unit Tier 0 test |
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
| Unexpected tier exception | `error`, `internal error`, later tiers skipped | unit pipeline test |
| Invalid CLI arguments | stderr message, exit 2, no JSON envelope | `test_cli_usage_error` |

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

## Phase ownership and test method

The workflow is defined in `docs/sdd-workflow.md`; this section records how 003
applies it.

- **Phase 1:** spec, blueprint, `progress.md`, JSON Schema, golden fixtures, and
  the contract test. T-2 is complete and frozen.
- **Phase 2:** for each work unit, write annotated stubs/interfaces and failing
  AC-tagged tests. Run `mypy`, `ruff`, and the target test command. Freeze the
  tests at a commit and record it in `progress.md`.
- **Phase 3:** implement until the frozen tests pass. Do not edit frozen tests.
- **Phase 4:** add integration, acceptance, failure-mode, path, and timeout
  tests; fix implementation edge cases.
- **Phase 5:** fresh read-only audit, full gate, traceability, and PR readiness.

The former separate contract-test sessions are folded into Phase 2 of the
relevant work unit. `progress.md` is the only session-state file;
`blueprint.md` owns the durable task briefs.

One task or small slice at a time, sequential by default. A WU is a checkpoint,
not a session scope. Parallel work is acceptable only with disjoint files and
locked interfaces; this spec is too integrated for safe parallel execution.

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
| AC-15 | unit | `tests/unit/test_contract.py` | `uv run pytest tests/unit/test_contract.py -q` | pass |
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
- [x] T-2: Add the contract JSON Schema, golden envelope fixtures, and
  `tests/unit/test_contract.py`; add test-only `jsonschema` — verify:
  `uv run pytest tests/unit/test_contract.py -q` — AC: AC-2, AC-15
- [x] T-3: Add `core/__init__.py`, models, path/text helpers, errors, limits,
  redaction, and the pipeline with fake tiers; freeze the interfaces above —
  verify: `uv run pytest tests/unit/test_core.py -q` — AC: AC-4, AC-12, AC-14
- [x] T-4: Add root resolution, target confinement, Git/walk discovery, and
  counters — verify: `uv run pytest tests/unit/test_discovery.py -q` —
  AC: AC-5, AC-6
- [ ] T-5: Add `tools/__init__.py` and the subprocess runner with UTF-8 capture,
  timeouts, process-tree termination, `ToolResult`, and the T-3 error types —
  verify: `uv run pytest tests/unit/test_runner.py -q` — AC: AC-13
- [ ] T-6: Add Tier 0 syntax parsing — verify:
  `uv run pytest tests/unit/test_tier0.py -q` — AC: AC-7
- [ ] T-7: Add the ruff parser and tier — verify:
  `uv run pytest tests/unit/test_ruff.py -q` — AC: AC-8
- [ ] T-10: Add JSON and human renderers; start with the two-tier pipeline and
  extend as later tiers land — verify:
  `uv run pytest tests/unit/test_output.py -q` — AC: AC-2, AC-3, AC-14
- [ ] T-11: Phase 2 writes `tests/acceptance/test_cli_contract.py`,
  `test_human_output.py`, and `test_exit_codes.py`, tagged with `spec("003")`
  and the covered ACs. Phase 3 wires the app, CLI, `__main__`, and console
  script, starting with Tier 0 and ruff, and makes those tests pass. Implement
  the discovery/internal error envelope, warnings-to-stderr behavior, and
  argparse/no-envelope behavior — verify:
  `uv run pytest tests/acceptance/test_cli_contract.py tests/acceptance/test_human_output.py tests/acceptance/test_exit_codes.py -q`
  and `uv run strictr --version` — AC: AC-1..AC-4
- [ ] T-8: Add type-checker selection, mypy/pyright parsers, and the type tier to
  the pipeline — verify: `uv run pytest tests/unit/test_types.py -q` —
  AC: AC-9, AC-10
- [ ] T-9: Add the JUnit parser and pytest tier to the pipeline; write counts
  to `meta`, reconstruct node IDs, and normalize missing lines — verify:
  `uv run pytest tests/unit/test_pytest.py -q` — AC: AC-11
- [ ] T-12: Add fixture excludes to `pyproject.toml` and `tests/conftest.py`,
  then add acceptance fixtures and black-box tests for tiers, discovery, failure
  modes, paths, and timeout — verify: `uv run pytest tests/acceptance -q` —
  AC: AC-1..AC-15
- [ ] T-13: Phase 2 writes `tests/unit/test_check_docs.py`, tagged with
  `spec("003")` and AC-16. Phase 4 closeout updates docs, makes that test pass,
  and runs the full gate; Phase 5 is the read-only audit — verify:
  `uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest -q`
  and the traceability command — AC: AC-16

## Task briefs

All tasks read `AGENTS.md`, `docs/sdd-workflow.md`, the spec, this blueprint, the
contract, `docs/testing.md`, and the linked modules/tests. Write only the listed
files plus the task checkbox and `progress.md`. Do not edit the spec, contract,
schema, frozen tests, or another task's modules to make a test pass.

| Task | Stubs/tests (Phase 2/4) | Implementation/docs (Phase 3/4/5) | Verify | ACs |
|---|---|---|---|---|
| T-3 | `core/__init__.py`; models, paths, text, protocols, errors, pipeline stubs; `tests/unit/test_core.py` | Fill the pipeline, limits, redaction, warnings, counts, and `internal error` behavior | `uv run pytest tests/unit/test_core.py -q` | AC-4, AC-12, AC-14 |
| T-4 | `core/discovery.py` stub; `tests/unit/test_discovery.py` | Root/targets, Git/walk discovery, symlink confinement, counters, warnings | `uv run pytest tests/unit/test_discovery.py -q` | AC-5, AC-6 |
| T-5 | `tools/__init__.py`; `tools/runner.py` stub; `tests/unit/test_runner.py` | Subprocess, UTF-8 capture, timeouts, process tree, T-3 error types | `uv run pytest tests/unit/test_runner.py -q` | AC-13 |
| T-6 | `tiers/__init__.py`; Tier 0 stub; `tests/unit/test_tier0.py` | `ast.parse`, syntax diagnostics, in-process budget → `error` | `uv run pytest tests/unit/test_tier0.py -q` | AC-7 |
| T-7 | parsers package; ruff parser/tier stubs; `tests/unit/test_ruff.py` | Ruff command, JSON normalization, version, failures | `uv run pytest tests/unit/test_ruff.py -q` | AC-8 |
| T-10 | output package; renderer stubs; `tests/unit/test_output.py` | Compact JSON, human output, warnings, truncation notices | `uv run pytest tests/unit/test_output.py -q` | AC-2, AC-3, AC-14 |
| T-11 | app/CLI/`__main__` stubs; console script; CLI contract/human/exit tests | Wire the two-tier pipeline, error envelope, argparse behavior, then extend | CLI tests + `uv run strictr --version` | AC-1..AC-4 |
| T-8 | mypy/pyright parser and type-tier stubs; `tests/unit/test_types.py` | Selection, execution, normalization, warnings, `--type-checker none` | `uv run pytest tests/unit/test_types.py -q` | AC-9, AC-10 |
| T-9 | JUnit parser and pytest-tier stubs; `tests/unit/test_pytest.py` | Full suite, xunit1, counts, node IDs, exit mapping, errors | `uv run pytest tests/unit/test_pytest.py -q` | AC-11 |
| T-12 | Fixtures and acceptance tests | Integration, failure modes, paths, timeout, exit codes | `uv run pytest tests/acceptance -q` | AC-1..AC-15 |
| T-13 | `tests/unit/test_check_docs.py` | Docs, full gate, traceability | Full gate + traceability | AC-16 |

Key notes:

- T-3 freezes the interfaces in the section above. Later tasks consume them.
- T-4 resolves targets only for confinement; display original paths. Escaping
  symlinks are errors, not `files_skipped`.
- T-5 raises `ToolNotFoundError` and `ToolTimeoutError`; it does not encode
  failures in magic messages.
- T-6 over-budget is `error`, not `fail`.
- T-7/T-8/T-9 use `core.text` for redaction/truncation and return contract
  diagnostics; no pathless tool diagnostics.
- T-9 writes counts to tier meta, reconstructs node IDs, and copies parsed
  counts even on pytest error when XML exists.
- T-11 starts with Tier 0 + ruff; T-8/T-9 extend the pipeline later. Do not
  assert a final four-tier pass at WU-2; T-12 owns the complete envelope.
- T-13 runs in Phase 5 and is read-only on code/tests except docs.

## Phase protocol

Follow `docs/sdd-workflow.md` and `progress.md`. Each session:

1. Read `AGENTS.md`, `docs/sdd-workflow.md`, the spec, this blueprint, the
   contract, and `progress.md`.
2. Confirm the phase, branch `feat/003-check-command`, expected commit, and a
   clean worktree.
3. Do only the work of the current phase for one task or small slice. A WU is a
   checkpoint. Phase 2 writes stubs and failing tests; Phase 3 implements against
   frozen tests; Phase 4 writes integration tests; Phase 5 is read-only.
4. Run the exact task command. In Phase 2, record the expected failure. In
   Phase 3/4, it must pass.
5. Run `uv run ruff format .`, `uv run ruff check .`, and `uv run mypy` for
   touched code before committing.
6. Commit atomically with `Spec: 003` and `Refs: AC-n`; update `progress.md` and
   the task checkbox only at the appropriate gate.
7. At a phase gate, stop and record the result in `progress.md`.

Do not edit frozen tests in Phase 3. Do not change an AC, non-goal, contract, or
module boundary without human approval. Do not create a `handoff.md`;
`progress.md` is the only session-state file.

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
- [x] The Tier 0 10 s budget is checked between files and cannot interrupt a
  single pathological `ast.parse`; a subprocess parser worker is deferred —
  accepted in ADR 0009.
- [x] `files_skipped` does not count Gitignored files; the owner approved this
  interpretation. Escaping symlinks are errors, not skipped — resolved by spec
  1.2 and the owner decision on 2026-11-21.
- [ ] The timeout acceptance test must assert a generous bound to avoid CI
  flakiness and is the single deliberate `sleep()` exception in the suite —
  Phase 4/T-12.
- [x] Nested-project root selection uses the current directory's marker first;
  nested targets use the outer root — accepted 2026-11-21.
- [x] Tools may import pure core types; execution refinements are recorded in
  ADR 0008 and ADR 0009.

## Retrospective

Fill after completion: what worked, what did not, one change.
