# Blueprint: Verification hardening and edge-case coverage

- Spec: `specs/active/004-verification-hardening/spec.md`
- Status: approved
- Revised: 2026-11-22 — adds AC-9/T-9 for discovery-error target normalization
- Owner: Ge Rui Sen

## Approach

Treat `004` as a coverage-and-hardening slice, not a new feature slice. Most
behavior already exists in `003`; write the missing acceptance/regression tests
first, then fix only the paths where those tests expose a real gap.

Order of work:

1. Lock nested-cwd and symlink display semantics with tests; no production code
   expected.
2. Add non-UTF8 output tests; add one surrogate-safe output helper and apply it
   to both renderers.
3. Add human-output visibility tests; extend the human renderer.
4. Normalize discovery-error targets in `app.py`; add acceptance coverage.
5. Add real config-parity, redaction, and truncation coverage; change production
   code only if a test exposes a defect.
6. Cover traceability entry-point I/O; keep policy behavior unchanged.
7. Run the full gate and update the changelog.

`003` is merged to `main`; this branch is rebased on `main` at `5897fc5`. Do not
edit `003` frozen tests; add new test modules.

## Modules and boundaries

| Module | Responsibility | Change |
|---|---|---|
| `src/strictr/core/text.py` | Redaction, caps, and surrogate-safe output text | Modified: add a small internal helper |
| `src/strictr/output/json_output.py` | Compact JSON rendering | Modified: safe UTF-8 output |
| `src/strictr/output/human.py` | Concise human rendering | Modified: skipped count, error evidence, safe output |
| `src/strictr/app.py` | Discovery result assembly | Modified: normalize discovery-error targets |
| `src/strictr/cli.py` | Output switch and exit code | Unchanged unless renderers need wiring |
| `tests/acceptance/test_scope_paths.py` | Nested-cwd and absolute-target CLI behavior | New |
| `tests/acceptance/test_discovery_error_paths.py` | Discovery-error target normalization | New |
| `tests/unit/test_path_display.py` | In-root symlink display semantics | New |
| `tests/unit/test_output_non_utf8.py` | Synthetic surrogate rendering and schema validity | New |
| `tests/acceptance/test_non_utf8_paths.py` | POSIX non-UTF8 filename through the CLI | New |
| `tests/unit/test_human_hardening.py` | Skipped count and error-evidence formatting | New |
| `tests/acceptance/test_human_errors.py` | Real collection-error human output | New |
| `tests/acceptance/test_type_config.py` | Config-selected mypy, both configured, fake pyright, unavailable checker | New |
| `tests/acceptance/test_pytest_config.py` | `testpaths` parity | New |
| `tests/acceptance/test_redaction_truncation.py` | Real pytest secret/long message and 21 ruff findings | New |
| `tests/unit/test_traceability_entry.py` | Traceability environmental and git failure paths | New |
| `CHANGELOG.md` | Record the hardening slice | Modified |

Do not change the v1 contract, schema, status model, exit codes, or `003`
module boundaries. `output` may import `core`.

## Contracts

### CLI and JSON

No CLI flags or JSON fields change. JSON remains one compact, newline-terminated
UTF-8 object that validates against the v1 schema. Valid Unicode stays readable;
lone surrogate characters are escaped as JSON `\uDCxx` sequences so the byte
stream remains valid UTF-8. Redaction and caps run before the final escape.

### Human output

Keep the existing status and tier lines. Additive changes:

- When `files_skipped == 0`, the status line is unchanged:
  `PASS  3 files checked in 1200 ms`.
- When `files_skipped > 0`:
  `PASS  3 files checked, 1 skipped in 1200 ms`.
- For every tier with status `fail` or `error`, print at most the first five
  diagnostics using the existing diagnostic line format.
- For an `error` tier with no diagnostics and a non-empty `meta.error` whose
  first line differs from `skipped_reason`, print one indented evidence line:
  `  <tier-id>: <first line of meta.error>`.
  The value is already redacted and capped by the pipeline.
- Extend the existing truncation notice to `fail` and `error` tiers:
  `  ... N more diagnostics (use --json)` or
  `  ... some text truncated`.

This keeps existing `003` human tests valid: zero skipped files and the generic
error paths do not gain unexpected exact-output changes.

### Nested-cwd and symlink ledger

No behavior change is planned.

- From `project/src` with no targets: `root` is `..`, `targets` is `["src"]`;
  the checked files are under `src`.
- An in-root symlink is reported by its link path. Resolution is used only for
  confinement checks.

If the owner chooses the alternative `targets: ["."]` semantics, stop and
revise the spec/blueprint before writing T-1.

### Discovery errors

No success-path behavior changes. `scope.root` and the existing error reason stay
as they are. `scope.targets` is normalized relative to that root, sorted, and
de-duplicated, with `/` separators. On Windows, separator backslashes become
`/`; on POSIX, a literal backslash is part of the filename and is preserved. The
error envelope still validates against the v1 schema and exits 2.

### Type-checker and pytest parity

No behavior change is planned; tests use the real CLI and real mypy/pytest.

- Config-selected mypy: a fixture with `[tool.mypy]` and a type error; the CLI
  records `selection: "config"`.
- Both configured: `[tool.mypy]` and `[tool.pyright]`; mypy runs and the warning
  appears exactly once in JSON and stderr.
- Fake pyright: a test module named `pyright` on `PYTHONPATH` handles
  `--version` and `--outputjson`; the CLI runs it via `python -m pyright`,
  normalizes its diagnostics, and records its version.
- Configured but unavailable: a configured pyright plus a fake module that exits
  nonzero; the type tier is `error`.
- Pytest `testpaths`: a fixture whose config points at `checks/`, with a decoy
  failing test under `tests/`; only `checks/` is collected.

The fake pyright module is a test double, not evidence of real pyright parity.

Inline fixture projects that are not testing ruff should pin
`[tool.ruff.lint] select = ["E", "F"]`. Otherwise a newer ruff default rule can
fail the lint tier before the tier under test runs.

## Failure modes

| Failure | Behavior | Test |
|---|---|---|
| CLI run from a subdirectory | Ledger records `root` and `targets` relative to the correct roots | `test_nested_cwd_ledger` |
| In-root symlink | Display path is the link, not the resolved target | `test_in_root_symlink_uses_link_path` |
| Discovery error with Windows separators | Targets are normalized, sorted, de-duplicated POSIX paths; schema valid; exit 2 | `test_discovery_error_targets` |
| Non-UTF8 POSIX filename | JSON is valid UTF-8; no renderer crash | `test_non_utf8_path_json`, `test_non_utf8_json_render` |
| Skipped non-regular file | Human output shows skipped count; JSON records it | `test_human_reports_skipped_files` |
| Pytest collection error | Human output includes collection evidence | `test_human_collection_error_shows_evidence` |
| Tool error without diagnostics | Human output shows the redacted `meta.error` line | `test_human_tool_error_shows_meta_error` |
| Config-selected checker | Selection and warning are recorded correctly | type-config tests |
| Configured checker unavailable | Tier is `error`, not pass | `test_configured_checker_unavailable` |
| Pytest `testpaths` | Only configured tests are collected | `test_pytest_testpaths_is_honored` |
| Secret in pytest failure | Secret is redacted in JSON | `test_real_pytest_secret_is_redacted` |
| Long real message | Message is capped and marked truncated | `test_real_pytest_message_is_capped` |
| >20 ruff findings | 20 kept, total recorded, human count shown | `test_ruff_count_cap` |
| Traceability missing env/git failure | Exit 1 with stderr | traceability entry tests |

## Security and trust boundaries

- No sandbox or network isolation is added. The trust object remains unchanged.
- Non-UTF8 escaping must not leak raw bytes or bypass redaction; redaction and
  caps run first.
- Human error evidence uses the already-redacted `meta.error`; tests must not
  introduce a second unredacted path.
- Traceability tests use fakes or local temporary repositories and no network.
- Fixture projects are created under `tmp_path`; no tools run in the repository.

## Test plan

| AC | Layer | Test module | Command | Status |
|---|---|---|---|---|
| AC-1 | acceptance | `tests/acceptance/test_scope_paths.py` | `uv run pytest tests/acceptance/test_scope_paths.py -q` | pass |
| AC-2 | unit | `tests/unit/test_path_display.py` | `uv run pytest tests/unit/test_path_display.py -q` | todo |
| AC-3 | unit, acceptance | `tests/unit/test_output_non_utf8.py`, `tests/acceptance/test_non_utf8_paths.py` | `uv run pytest tests/unit/test_output_non_utf8.py tests/acceptance/test_non_utf8_paths.py -q` | todo |
| AC-4 | unit, acceptance | `tests/unit/test_human_hardening.py`, `tests/acceptance/test_human_errors.py` | `uv run pytest tests/unit/test_human_hardening.py tests/acceptance/test_human_errors.py -q` | todo |
| AC-5 | acceptance | `tests/acceptance/test_type_config.py` | `uv run pytest tests/acceptance/test_type_config.py -q` | todo |
| AC-6 | acceptance | `tests/acceptance/test_pytest_config.py` | `uv run pytest tests/acceptance/test_pytest_config.py -q` | todo |
| AC-7 | acceptance | `tests/acceptance/test_redaction_truncation.py` | `uv run pytest tests/acceptance/test_redaction_truncation.py -q` | todo |
| AC-8 | unit | `tests/unit/test_traceability_entry.py` | `uv run pytest tests/unit/test_traceability_entry.py -q` | todo |
| AC-9 | acceptance | `tests/acceptance/test_discovery_error_paths.py` | `uv run pytest tests/acceptance/test_discovery_error_paths.py -q` | todo |

Full gate:

`uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest -q`

## Tasks

- [x] T-1: Add nested-cwd and absolute-target acceptance tests — verify:
  `uv run pytest tests/acceptance/test_scope_paths.py -q` — AC: AC-1
- [ ] T-2: Add in-root symlink display tests — verify:
  `uv run pytest tests/unit/test_path_display.py -q` — AC: AC-2
- [ ] T-3: Add non-UTF8 output tests and the surrogate-safe renderer helper —
  verify:
  `uv run pytest tests/unit/test_output_non_utf8.py tests/acceptance/test_non_utf8_paths.py -q`
  — AC: AC-3
- [ ] T-4: Add human skipped/error evidence tests and renderer changes — verify:
  `uv run pytest tests/unit/test_human_hardening.py tests/acceptance/test_human_errors.py -q`
  — AC: AC-4
- [ ] T-5: Add type-checker configuration and fake-pyright acceptance tests —
  verify: `uv run pytest tests/acceptance/test_type_config.py -q` — AC: AC-5
- [ ] T-6: Add pytest `testpaths` parity acceptance test — verify:
  `uv run pytest tests/acceptance/test_pytest_config.py -q` — AC: AC-6
- [ ] T-7: Add real redaction/truncation acceptance tests — verify:
  `uv run pytest tests/acceptance/test_redaction_truncation.py -q` — AC: AC-7
- [ ] T-8: Add traceability entry-point failure-path tests — verify:
  `uv run pytest tests/unit/test_traceability_entry.py -q` — AC: AC-8
- [ ] T-9: Normalize discovery-error targets and add acceptance coverage —
  verify: `uv run pytest tests/acceptance/test_discovery_error_paths.py -q` —
  AC: AC-9
- [ ] T-10: Update `CHANGELOG.md`, run the full gate, and open the PR — verify:
  the full gate above — AC: AC-1..AC-9

## Task briefs

| Task | Stubs/tests (Phase 2/4) | Implementation/docs (Phase 3/4) | Verify | ACs |
|---|---|---|---|---|
| T-1 | `tests/acceptance/test_scope_paths.py` | None expected; no product behavior change | `uv run pytest tests/acceptance/test_scope_paths.py -q` | AC-1 |
| T-2 | `tests/unit/test_path_display.py` | None expected | `uv run pytest tests/unit/test_path_display.py -q` | AC-2 |
| T-3 | `tests/unit/test_output_non_utf8.py`, `tests/acceptance/test_non_utf8_paths.py` | Surrogate-safe helper in `core/text.py`; apply in both renderers | `uv run pytest tests/unit/test_output_non_utf8.py tests/acceptance/test_non_utf8_paths.py -q` | AC-3 |
| T-4 | `tests/unit/test_human_hardening.py`, `tests/acceptance/test_human_errors.py` | `output/human.py` skipped count, error evidence, truncation for error tiers | `uv run pytest tests/unit/test_human_hardening.py tests/acceptance/test_human_errors.py -q` | AC-4 |
| T-5 | `tests/acceptance/test_type_config.py` | Fix only if a parity defect appears | `uv run pytest tests/acceptance/test_type_config.py -q` | AC-5 |
| T-6 | `tests/acceptance/test_pytest_config.py` | Fix only if a parity defect appears | `uv run pytest tests/acceptance/test_pytest_config.py -q` | AC-6 |
| T-7 | `tests/acceptance/test_redaction_truncation.py` | Fix only if a redaction/cap defect appears | `uv run pytest tests/acceptance/test_redaction_truncation.py -q` | AC-7 |
| T-8 | `tests/unit/test_traceability_entry.py` | Fix only if an entry-path defect appears; no policy change | `uv run pytest tests/unit/test_traceability_entry.py -q` | AC-8 |
| T-9 | `tests/acceptance/test_discovery_error_paths.py` | `app.py` discovery-error target normalization | `uv run pytest tests/acceptance/test_discovery_error_paths.py -q` | AC-9 |
| T-10 | None | `CHANGELOG.md`, full gate, PR evidence | Full gate | AC-1..AC-9 |

## Phase protocol

Follow `docs/sdd-workflow.md`. `003` is merged and this branch is rebased on
`main`.

- Do not edit `003` frozen tests.
- For each task, write or update the test first, run its exact command, then
  implement only what the test requires.
- Mark the task checkbox only after its command passes.
- Use a new test module rather than editing a `003` test module.
- If a test exposes a contract or module-boundary change, stop and propose a
  spec revision or a new spec.

## Rollback

Revert the `004` branch. All changes are additive tests and output hardening; no
data, schema, or persisted state changes. If the human-output format causes a
consumer problem, keep the tests and revert the renderer change separately.

## Open technical questions

Phase 1 approved 2026-11-22:

- [x] Nested-cwd ledger semantics: `root` is relative to the invocation
  directory and `targets` is relative to the root — owner.
- [x] Human output wording and error-evidence indentation: approved as written
  above — owner.
- [x] Surrogate escaping representation: JSON `\uDCxx` escapes with readable
  valid Unicode are approved — owner.

Deferred:

- [x] Pyright wrapper-to-executable fallback is deferred; do not add it in `004`.
- [x] Config parse errors (`ConfigError`) are deferred; do not change fail-open
  behavior in `004`.
- [x] Real pyright is not in CI; do not claim parity beyond the fake-module
  boundary.
- [x] Discovery-error targets are normalized relative to the recorded root,
  sorted, de-duplicated, and POSIX-normalized; no root-selection change —
  accepted 2026-11-22.

## Retrospective

Fill after completion: what worked, what did not, one change.
