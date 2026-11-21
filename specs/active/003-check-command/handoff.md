# Handoff: Check command after T-2

- Branch: `feat/003-check-command`
- Base: `main`
- T-2 commit: `6737891`
- Current tip: run `git log --oneline -1` before starting
- Spec: `specs/active/003-check-command/spec.md` (`in-progress`)
- Blueprint: `specs/active/003-check-command/blueprint.md`
- Completed: T-1, T-2
- Next: T-3
- Import boundary: ADR 0008; execution refinements: ADR 0009
- Remote branch: pushed and tracking `origin/feat/003-check-command`

T-2 evidence: `uv run pytest tests/unit/test_contract.py -q` → 11 passed.
Full suite at T-2: `uv run pytest -q` → 68 passed.
Format, lint, and strict types pass.

## How to run a session

One session per task. WU is a checkpoint, not a worker scope. Do not run
workers in parallel on this branch.

1. Start a new session with the role and task below.
2. Read `AGENTS.md`, `docs/sdd-workflow.md`, the spec, the blueprint, the
   contract, and the task's linked modules/tests.
3. Follow the comment and docstring policy in `docs/sdd-workflow.md`: no
   redundant inline comments; docstrings only for public contracts and
   non-obvious invariants; explain why, not what.
4. Check `git status --short` and `git log --oneline -1`. Stop if the worktree
   is dirty or the commit is not the expected latest commit.
5. Write the failing test first. Run the exact command and record the expected
   failure. A test that has never failed is not evidence.
6. Implement the minimum. Rerun the exact command.
7. Run format, lint, and types for touched code.
8. Update only the task checkbox in the blueprint.
9. Commit atomically with `Spec: 003` and `Refs: AC-n`.
10. Report the commit hash, exact commands/results, files changed, and risks.
11. Push at the end of each work unit or after a substantial session.

Do not edit the spec, contract, schema, public interfaces, `AGENTS.md`, the
constitution, `.github/`, `internal-docs/`, or `specs/archive/`.

## Session order

| # | Role | Task | WU | Exact verify |
|---|---|---|---|---|
| 1 | Task Worker | T-3 core models and pipeline | WU-1 | `uv run pytest tests/unit/test_core.py -q` |
| 2 | Task Worker | T-4 discovery | WU-1 | `uv run pytest tests/unit/test_discovery.py -q` |
| 3 | Task Worker | T-5 subprocess runner | WU-1 | `uv run pytest tests/unit/test_runner.py -q` |
| 4 | Task Worker | T-6 Tier 0 | WU-2 | `uv run pytest tests/unit/test_tier0.py -q` |
| 5 | Task Worker | T-7 ruff | WU-2 | `uv run pytest tests/unit/test_ruff.py -q` |
| 6 | Task Worker | T-10 output renderers | WU-2 | `uv run pytest tests/unit/test_output.py -q` |
| 7 | Planner | P-1 CLI contract tests | WU-2 | `uv run pytest tests/acceptance/test_cli_contract.py -q` (expected red until T-11) |
| 8 | Task Worker | T-11 app and CLI | WU-2 | CLI contract/human/exit tests and `uv run strictr --version` |
| — | Human/Planner | Push and open draft PR | WU-2 | PR URL; CI may be red |
| 9 | Task Worker | T-8 types | WU-3 | `uv run pytest tests/unit/test_types.py -q` |
| 10 | Task Worker | T-9 pytest | WU-4 | `uv run pytest tests/unit/test_pytest.py -q` |
| 11 | Task Worker | T-12 acceptance and failure modes | WU-5 | `uv run pytest tests/acceptance -q` |
| 12 | Planner | P-2 docs contract test | WU-6 | `uv run pytest tests/unit/test_check_docs.py -q` (expected red until T-13) |
| 13 | **Integrator** | T-13 full gate and traceability | WU-6 | Full gate + traceability |

T-10 and T-11 may share one session with two commits. Keep T-3..T-5 separate.
P-1 and P-2 are short Planner sessions that write the contract tests the workers
must not weaken.

## Task briefs

### T-3 — Core models and pipeline

- Role: Task Worker.
- ACs: AC-4, AC-12, AC-14.
- Read: `AGENTS.md`, `docs/sdd-workflow.md`, spec, blueprint, contract,
  `docs/testing.md`, architecture overview.
- Write: `src/strictr/core/__init__.py`, `core/models.py`, `core/paths.py`,
  `core/text.py`, `core/protocols.py`, `core/errors.py`, `core/pipeline.py`,
  `tests/unit/test_core.py`, blueprint T-3 checkbox.
- Forbidden: `tiers/`, `tools/`, `output/`, `cli.py`, `app.py`, schema,
  contract, other tests.
- Verify: `uv run pytest tests/unit/test_core.py -q`.
- Notes: freeze the interfaces in the blueprint:
  `StrictrError`/`DiscoveryError`/`ConfigError`/`ToolError`/
  `ToolNotFoundError`/`ToolTimeoutError`/`InvalidToolOutput`;
  `ToolResult(command, returncode, stdout: str, stderr: str, duration_ms)`;
  `ToolRunner.run` and `which`; `Tier`; `CheckContext`; `TierResult` with
  internal `warnings`; `CheckResult.to_envelope`; `DiscoveryResult`; pipeline
  signature. Pipeline implements status precedence and fail-fast, catches
  `Exception` (not `BaseException`), uses `internal error`, and stops later
  tiers with `earlier_tier_failed`. Project `tier2-pytest` meta counts into
  `scope`. Aggregate discovery and tier warnings. Cap 20 diagnostics per tier.
  Redact before capping; message 2,000 and `meta.error` 500 include
  `" [truncated]"`; `meta.truncated` for count or text caps;
  `meta.total_diagnostics` only for dropped counts. `relative_posix` is pure and
  never resolves symlinks. Comment policy: one-line docstrings on public models,
  protocols, and pipeline only; no field-by-field narration.

### T-4 — Discovery

- Role: Task Worker.
- ACs: AC-5, AC-6.
- Read: T-3 core models/paths/errors; architecture data flow; ADR 0002/0003.
- Write: `src/strictr/core/discovery.py`, `tests/unit/test_discovery.py`,
  blueprint T-4 checkbox.
- Forbidden: tiers, tools, output, app/CLI, schema, contract.
- Verify: `uv run pytest tests/unit/test_discovery.py -q`.
- Notes: root algorithm from blueprint; target confinement; explicit files even
  if Gitignored; `git ls-files -co --exclude-standard -z`; fallback walk with
  pruned directories; empty project is an error; `files_skipped` semantics.
  Escaping symlinks are errors, not skipped; resolve only for confinement and
  record/display original paths. `DiscoveryResult` carries warnings. Use a
  temporary `git init` fixture, no network.

### T-5 — Subprocess runner

- Role: Task Worker.
- AC: AC-13.
- Read: T-3 `models.py`, `errors.py`, `protocols.py`; ADR 0003/0007.
- Write: `src/strictr/tools/__init__.py`, `tools/runner.py`,
  `tests/unit/test_runner.py`, blueprint T-5 checkbox.
- Forbidden: tiers, parsers, output, app/CLI, contract, schema.
- Verify: `uv run pytest tests/unit/test_runner.py -q`.
- Notes: no shell; cwd root; byte capture decoded to `str` with UTF-8
  replacement; timeout; Windows new process group plus `taskkill /T /F`; POSIX
  new session plus `killpg`; missing executable raises `ToolNotFoundError`;
  timeout raises `ToolTimeoutError`. Use fakes for command construction. T-12
  owns the one real timeout fixture.

### T-6 — Tier 0

- Role: Task Worker.
- AC: AC-7.
- Read: T-3 models/pipeline; architecture Tier 0; `docs/testing.md`.
- Write: `src/strictr/tiers/__init__.py`, `tiers/ast_tier.py`,
  `tests/unit/test_tier0.py`, blueprint T-6 checkbox.
- Forbidden: other tiers, tools, output, app/CLI, contract, schema.
- Verify: `uv run pytest tests/unit/test_tier0.py -q`.
- Notes: parse bytes with `ast.parse` so PEP 263 encodings work; map syntax
  error location; in-process budget checked between files; stop later tiers.

### T-7 — Ruff

- Role: Task Worker.
- AC: AC-8.
- Read: T-3 models, T-5 runner, ADR 0003.
- Write: `src/strictr/tools/parsers/__init__.py`,
  `tools/parsers/ruff.py`, `tiers/ruff_tier.py`, `tests/unit/test_ruff.py`,
  blueprint T-7 checkbox.
- Forbidden: other tiers, output, app/CLI, contract, schema.
- Verify: `uv run pytest tests/unit/test_ruff.py -q`.
- Notes: `ruff check --output-format=json --no-fix -- <targets>`; version
  capture; missing/crash/timeout/invalid JSON are `error`; any finding fails;
  normalize paths; sort and truncate.

### T-10 — Output renderers

- Role: Task Worker.
- ACs: AC-2, AC-3, AC-14.
- Read: T-3 envelope models, contract human/JSON sections.
- Write: `src/strictr/output/__init__.py`, `output/json_output.py`,
  `output/human.py`, `tests/unit/test_output.py`, blueprint T-10 checkbox.
- Forbidden: app/CLI before T-11, tiers, contract, schema.
- Verify: `uv run pytest tests/unit/test_output.py -q`.
- Notes: compact UTF-8 JSON plus newline; human status/scope/first failures to
  stdout; warnings to stderr in both modes; trust warning in human mode only; no
  color; five diagnostics in human mode, 20 in JSON; distinguish count
  truncation (`N more diagnostics`) from text truncation (`some text
  truncated`).

### P-1 — Planner: CLI contract tests

- Role: Planner.
- ACs: AC-1..AC-4.
- Read: contract, spec, blueprint, CLI contracts, human-output section.
- Write: `tests/acceptance/test_cli_contract.py`,
  `tests/acceptance/test_human_output.py`, `tests/acceptance/test_exit_codes.py`.
- Forbidden: product code, schema, contract, tier tests.
- Verify: `uv run pytest tests/acceptance/test_cli_contract.py tests/acceptance/test_human_output.py tests/acceptance/test_exit_codes.py -q`
  is expected red until T-11.
- Notes: black-box subprocess tests only; no internals. Cover JSON schema,
  stdout-only JSON, warnings/trust on stderr, exit codes, argparse errors without
  an envelope, and the discovery/internal error envelope. Do not assert a final
  four-tier pass at WU-2.

### T-11 — App and CLI

- Role: Task Worker.
- ACs: AC-1..AC-4.
- Read: all completed core/tiers/tools/output modules; contract; spec scenarios.
- Write: `src/strictr/app.py`, `cli.py`, `__main__.py`, `pyproject.toml`
  `[project.scripts]` only, blueprint T-11 checkbox. P-1 owns
  `tests/acceptance/test_cli_contract.py`, `test_human_output.py`, and
  `test_exit_codes.py`; make them pass without weakening them.
- Forbidden: schema, contract, real tool fixtures (T-12), runtime dependencies.
- Verify: `uv run pytest tests/acceptance/test_cli_contract.py tests/acceptance/test_human_output.py tests/acceptance/test_exit_codes.py -q`
  and `uv run strictr --version`.
- Notes: start with the Tier 0 + ruff pipeline; add types and pytest tiers in
  T-8/T-9. Implement the discovery/internal error envelope with all four tiers,
  warnings to stderr, and argparse errors without a JSON envelope. Do not assert
  a final four-tier pass at WU-2; T-12 owns the complete envelope. Invalid
  arguments exit 2. No direct main push.

### T-8 — Types

- Role: Task Worker.
- ACs: AC-9, AC-10.
- Read: ADR 0005, T-3 models, T-5 runner, app tier wiring.
- Write: `src/strictr/tools/parsers/mypy.py`, `parsers/pyright.py`,
  `tiers/types_tier.py`, `tests/unit/test_types.py`, `app.py` type-tier wiring,
  blueprint T-8 checkbox.
- Forbidden: pytest tier, output, contract, schema.
- Verify: `uv run pytest tests/unit/test_types.py -q`.
- Notes: selection precedence; both configured → mypy + warning via
  `TierResult.warnings`; configured missing → error; none available → partial;
  `none` → `disabled_by_user`; mypy JSONL; pyright zero-based JSON; version
  capture; invalid output is error.

### T-9 — Pytest

- Role: Task Worker.
- AC: AC-11.
- Read: ADR 0006, T-3 models, T-5 runner, app tier wiring.
- Write: `src/strictr/tools/parsers/pytest_junit.py`,
  `tiers/pytest_tier.py`, `tests/unit/test_pytest.py`, `app.py` pytest-tier
  wiring, blueprint T-9 checkbox.
- Forbidden: types tier, output, contract, schema.
- Verify: `uv run pytest tests/unit/test_pytest.py -q`.
- Notes: full suite; `-q -o junit_family=xunit1 --junitxml=<temp>`; temp outside
  repo; exit 5 skipped; exit 2/3/4 error; invalid XML error; write
  `tests_collected`/`tests_run`/`tests_skipped` to tier meta; reconstruct node
  IDs from file/classname/name; normalize line 0/missing to 1 and prefer a
  failure-text `file:line`; missing pytest heuristic. No pathless collection
  diagnostics; use `meta.error`.

### T-12 — Acceptance and failure modes

- Role: Task Worker.
- ACs: AC-1..AC-15.
- Read: everything above; blueprints fixtures table; testing guide.
- Write: `tests/conftest.py` `collect_ignore`, `pyproject.toml` ruff fixture
  exclude, `tests/fixtures/projects/**`, `tests/acceptance/**`,
  blueprint T-12 checkbox and test-plan statuses.
- Forbidden: product behavior changes beyond integration glue; contract; schema.
- Verify: `uv run pytest tests/acceptance -q`.
- Notes: copy fixtures to `tmp_path`; real ruff/mypy/pytest; no network. One
  deliberate timeout `sleep()` is allowed. Test paths with spaces/Unicode,
  gitignored files, missing ruff, no tests, invalid output, and exit codes.

### P-2 — Planner: docs contract test

- Role: Planner.
- AC: AC-16.
- Read: spec, blueprint, README, AGENTS, system overview, changelog.
- Write: `tests/unit/test_check_docs.py`.
- Forbidden: product code, contract, schema.
- Verify: `uv run pytest tests/unit/test_check_docs.py -q` is expected red until
  T-13.
- Notes: assert the CLI command/status in README and AGENTS, the architecture
  implementation note, and the changelog entry. Do not test exact prose.

### T-13 — Integrator

- Role: Integrator.
- AC: AC-16.
- Read: entire repo, spec, blueprint, contract, workflow, CI logs.
- Write: `README.md`, `CHANGELOG.md`, `AGENTS.md` CLI command/status,
  `docs/architecture/system-overview.md` implementation note,
  blueprint T-13 and test-plan statuses. P-2 owns
  `tests/unit/test_check_docs.py`; make it pass without weakening it.
- Forbidden: behavior changes; send defects back to a Task Worker.
- Verify: full gate, acceptance, local traceability.
- Notes: review AC coverage and orphan tags; no hidden skips; docs consistent;
  prepare PR readiness. Do not archive the spec until after merge.

## Integrator commands

```powershell
git fetch origin main
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest -q
uv run pytest tests/acceptance -q

$env:HEAD_REF = (git branch --show-current)
$env:PR_TITLE = "feat(check): implement check command [003]"
$env:BASE_REF = "main"
uv run pytest --collect-only -q
uv run python scripts/check_traceability.py
```

## Git commands

Use explicit paths, not `git add -A`.

```powershell
git status --short
git log --oneline -1
git switch feat/003-check-command
git pull --ff-only

git add src/strictr/core/models.py tests/unit/test_core.py
git commit -m "feat(core): add models and pipeline" -m "Spec: 003" -m "Refs: AC-4, AC-12, AC-14"

# Push at a work-unit boundary or after a substantial session.
git push
```

After WU-2, open the draft PR. `gh` is not installed; use the GitHub web link or
install it. Never push directly to `main`.

```text
Base: main
Head: feat/003-check-command
Title: feat(check): implement check command [003]
Draft: yes
```

Traceability may be red until all AC-tagged tests exist. Merge only after WU-6
passes. The human owner merges with a squash merge, then a follow-up docs PR
moves the spec to `specs/archive/003-check-command/` and sets status `done`.
