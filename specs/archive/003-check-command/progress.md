# Progress: Check command

- Phase: Complete (merged and archived)
- Work unit: WU-6 complete; T-13 docs, full gate, and traceability pass
- Task: T-13 complete at `b2fef75`; Phase 5 closeout at `26fd58e`; PR #11 merged
  to `main` at `5897fc5`; spec archived
- Spec: 003
- Branch: feat/003-check-command (merged and deleted)
- PR: #11 https://github.com/RSGzen/Strictr/pull/11 (merged)
- Phase 1 gate: complete; spec 1.6 and blueprint approved and archived (see git log)
- History: the owner approved rewording the T-3 commit on 2026-11-22; every
  commit hash below was remapped to the rebased commit.
- Phase 2 gate: T-3 frozen at `12dfa43`; T-4 frozen at `4ce53ca`; T-5 frozen at
  `2b6a779`; T-6 frozen at `d9300b1`; T-7 frozen at `45a156e`; T-10 frozen at
  `7f3b21e`; T-11 frozen at `c568da0`; T-8 frozen at `87984c3`; T-9 frozen at
  `1cb2c03`; T-12 frozen at `8e7fb42`; T-12b frozen at `ffcbb92`; T-13 frozen
  at `b0796c1`
- Frozen tests: `tests/unit/test_contract.py` (Phase 1/T-2);
  `tests/unit/test_core.py` at `12dfa43`; `tests/unit/test_discovery.py`
  at `4ce53ca`; `tests/unit/test_runner.py` at `2b6a779`;
  `tests/unit/test_tier0.py` at `d9300b1`; `tests/unit/test_ruff.py`
  at `45a156e`; `tests/unit/test_output.py` at `7f3b21e`;
  `tests/acceptance/test_cli_contract.py`, `test_human_output.py`, and
  `test_exit_codes.py` at `c568da0`
- T-8 tests: `tests/unit/test_types.py` at `87984c3` (frozen)
- T-9 tests: `tests/unit/test_pytest.py` at `1cb2c03` (frozen)
- T-12 tests: `tests/acceptance/test_discovery.py`, `test_tiers.py`, and
  `test_timeout.py` at `8e7fb42` (frozen)
- T-12b tests: `tests/unit/test_runner_hardening.py` and
  `tests/unit/test_cli_hardening.py` at `ffcbb92` (frozen);
  `tests/acceptance/test_envelope_schema.py` at `a69b046` (Phase 4)
- T-13 tests: `tests/unit/test_check_docs.py` at `b0796c1` (frozen)
- T-3 gate: complete at `671c2f0`; `uv run pytest tests/unit/test_core.py -q`
  -> 38 passed; `uv run ruff format --check .`, `uv run ruff check .`,
  `uv run mypy`, and `uv run pytest -q` pass (106 passed)
- T-4 gate: complete at `90a4794`; `uv run pytest tests/unit/test_discovery.py -q`
  -> 19 passed, 2 skipped; full gate `uv run pytest -q` -> 125 passed,
  2 skipped; format, lint, and strict types pass
- T-5 gate: complete at `a48f1d2`; `uv run pytest tests/unit/test_runner.py -q`
  -> 8 passed; full gate `uv run pytest -q` -> 133 passed, 2 skipped; format,
  lint, and strict types pass
- T-6 gate: complete at `8a06721`; `uv run pytest tests/unit/test_tier0.py -q`
  -> 7 passed; full gate `uv run pytest -q` -> 146 passed, 2 skipped; format,
  lint, and strict types pass
- T-7 gate: complete at `8cb9a6b`; `uv run pytest tests/unit/test_ruff.py -q`
  -> 18 passed; full gate `uv run pytest -q` -> 164 passed, 2 skipped; format,
  lint, and strict types pass
- T-10 gate: complete at `10c215e`; `uv run pytest tests/unit/test_output.py -q`
  -> 11 passed; full gate `uv run pytest -q` -> 175 passed, 2 skipped; format,
  lint, and strict types pass
- T-11 gate: complete at `c1e9e5b`;
  `uv run pytest tests/acceptance/test_cli_contract.py tests/acceptance/test_human_output.py tests/acceptance/test_exit_codes.py -q`
  -> 32 passed; `uv run strictr --version` -> 0.0.0; full gate
  `uv run pytest -q` -> 207 passed, 2 skipped; format, lint, and strict types
  pass
- T-8 gate: complete at `18d0747`; `uv run pytest tests/unit/test_types.py -q`
  -> 53 passed; full gate `uv run pytest -q` -> 260 passed, 2 skipped; format,
  lint, and strict types pass. Real CLI smoke: explicit mypy reports a
  diagnostic and exits 1, auto selects mypy, `none` skips with exit 0, and
  missing pyright errors with `pyright not found` and exit 2
- T-9 gate: complete at `c619c3c`; `uv run pytest tests/unit/test_pytest.py -q`
  -> 48 passed; full gate `uv run pytest -q` -> 308 passed, 2 skipped; format,
  lint, and strict types pass. Real CLI smoke on a failing test reports tier2
  `fail`, node ID, line 7, `AssertionError`, and counts 2/2/0
- T-12 gate: complete at `70335bf`; `uv run pytest tests/acceptance -q`
  -> 47 passed, 1 skipped; full gate `uv run pytest -q` -> 323 passed,
  3 skipped; format, lint, and strict types pass
- T-12b gate: complete at `a69b046`; target command
  `uv run pytest tests/unit/test_runner_hardening.py tests/unit/test_cli_hardening.py tests/acceptance/test_envelope_schema.py -q`
  -> 11 passed; `uv run pytest tests/acceptance -q` -> 54 passed, 1 skipped;
  full gate `uv run pytest -q` -> 334 passed, 3 skipped; format, lint, and
  strict types pass
- T-13 gate: complete at `b2fef75`; `uv run pytest tests/unit/test_check_docs.py -q`
  -> 4 passed; full gate `uv run pytest -q` -> 338 passed, 3 skipped; format,
  lint, and strict types pass. Traceability passes after the T-3 subject reword.
  T-13 checkbox marked.
- Phase 5 gate: closeout at `26fd58e`; `uv run ruff format --check .`,
  `uv run ruff check .`, and `uv run mypy` pass; `uv run pytest -q` -> 338
  passed, 3 skipped; `uv run pytest tests/acceptance -q` -> 54 passed,
  1 skipped; traceability passes. The audit's discovery-error path finding is
  documented for spec 004; no code or test changes were made for it.
- WU-1 Phase 4 evidence at `fbdc25c`:
  `uv run pytest tests/unit/test_wu1_integration.py -q` -> 6 passed; full gate
  `uv run pytest -q` -> 139 passed, 2 skipped; format, lint, and strict types
  pass. Coverage: discovery-to-envelope scope, real subprocess fail-fast,
  timeout, missing tool, Unicode paths, warning aggregation
- Next command: none. Spec 003 is complete; spec 004 verification hardening is
  the active slice and owns the deferred discovery-error target normalization as
  AC-9.
- Spec changes: revision 1.5 records the spec 004 deferral of discovery-error
  `scope.targets` normalization and the traceability history reword; an earlier
  owner correction aligned the T-2 error golden with AC-12
- Size exception: ADR 0010 (one spec/one PR); future specs return to default
- Open items: real pyright is not in CI; T-8 parser and selection tests use a
  fake runner, and the real CLI smoke covered mypy only. The T-12 timeout test
  uses a 45 s bound; process-tree termination is proven by it. The pipeline is
  now four tiers (Tier 0, ruff, types, pytest); the frozen T-11 tests stay valid
  because pass paths use `--type-checker none`. A CLI-level `partial` exit code is reachable through
  auto-selection when neither checker is installed. PR #11 merged at `5897fc5`;
  the branch is deleted and this spec is archived. Traceability passed after
  rewording the T-3 subject to Conventional Commits; all freeze hashes in this
  file were remapped. Deferred to spec 004: discovery-error target normalization
  for Windows separators (AC-9), type-checker config/pyright parity, real pytest
  redaction/cap tests, nested-cwd ledger semantics, non-UTF8 paths, human-output
  polish, and traceability main/git path tests.
- T-12 resolution: Phase 3 made CLI stdout/stderr UTF-8 in `cli.py`; the
  Unicode path test passes. The frozen acceptance command is 47 passed,
  1 skipped (symlink creation unavailable locally); the full suite is
  323 passed, 3 skipped.
- T-12b resolution: timeout cleanup is bounded even when tree termination fails,
  Ctrl+C terminates the child tree, and CLI partial exit 2 plus non-pass schema
  validation are covered. Deferred to spec 004: type-checker config/pyright
  parity, real pytest redaction/cap tests, nested-cwd ledger semantics,
  non-UTF8 paths, human-output polish, and traceability main/git path tests.
- T-12 test infrastructure: added `tests/unit/__init__.py` and
  `tests/acceptance/__init__.py` so the duplicate `test_discovery.py` basename
  collects in both packages; no product behavior changes.
- T-9 implementation notes: `tests_run` is collected minus skipped; xunit2 paths
  are derived from the testcase classname; pathless failures and collection
  errors use the parser `error` for `meta.error`; collection errors use
  `collection-error` with the test file path as `test`.
- Session state: no `handoff.md`; task briefs are in `blueprint.md`

## Phase log

- 2026-11-21: Phase 1 complete. Spec 003 revision 1.4, blueprint, schema, and
  contract tests approved.
- 2026-11-21: Switched to the single-agent phase workflow. Separate
  contract-test sessions folded into Phase 2 of WU-2 and WU-6.
- 2026-11-21: ADR 0010 records the owner-approved one-time size exception.
- 2026-11-21: Phase 2 frozen at `12dfa43`; `tests/unit/test_core.py` is the
  T-3 frozen suite. Phase 3 starts from that commit.
- 2026-11-21: Owner approved aligning `tests/fixtures/contract/error.json` with
  AC-12 (`earlier_tier_failed`); the fixture is corrected and the frozen
  contract tests still pass.
- 2026-11-21: T-3 Phase 3 complete at `671c2f0`. All 38 frozen tests pass;
  full gate `uv run pytest -q` 106 passed; format, lint, and strict types pass.
  T-3 checkbox marked.
- 2026-11-21: T-4 Phase 2 stubs and `tests/unit/test_discovery.py` written.
  mypy and ruff pass; the target command fails only with `NotImplementedError`.
  Awaiting owner review and the T-4 test freeze commit.
- 2026-11-21: Owner approved the T-4 freeze at `4ce53ca`. Phase 3 implemented
  `core/discovery.py` at `90a4794`; 19 frozen tests pass and 2 platform tests
  skip. Full gate `uv run pytest -q` 125 passed, 2 skipped; format, lint, and
  strict types pass. T-4 checkbox marked.
- 2026-11-21: T-5 Phase 2 stubs and `tests/unit/test_runner.py` written.
  mypy and ruff pass; the target command fails only with `NotImplementedError`.
  Awaiting owner review and the T-5 test freeze commit.
- 2026-11-21: Owner approved the T-5 freeze at `2b6a779`. Phase 3 implemented
  `tools/runner.py` at `a48f1d2`; 8 frozen tests pass. Full gate
  `uv run pytest -q` 133 passed, 2 skipped; format, lint, and strict types pass.
  T-5 checkbox marked.
- 2026-11-21: WU-1 Phase 4 integration complete at `fbdc25c`.
  `tests/unit/test_wu1_integration.py` adds 6 cross-module tests; full gate
  139 passed, 2 skipped; format, lint, and strict types pass. No implementation
  defects surfaced.
- 2026-11-21: T-6 Phase 2 stubs and `tests/unit/test_tier0.py` written at
  `d9300b1`. `uv run ruff format --check .` and `uv run ruff check .` pass;
  `uv run mypy` reports no issues in 15 source files. The target command fails
  7/7 as expected: 5 direct `NotImplementedError` and 2 pipeline assertions
  against the stub.
- 2026-11-21: Owner approved the T-6 freeze at `d9300b1`. Phase 3 implemented
  `tiers/ast_tier.py` at `8a06721`; all 7 frozen tests pass. Full gate
  `uv run pytest -q` 146 passed, 2 skipped; format, lint, and strict types pass.
  T-6 checkbox marked.
- 2026-11-21: T-7 Phase 2 stubs (`tools/parsers/ruff.py`,
  `tiers/ruff_tier.py`) and `tests/unit/test_ruff.py` written at `45a156e`.
  `uv run ruff format --check .` and `uv run ruff check .` pass; `uv run mypy`
  reports no issues in 18 source files. The target command fails 18/18 as
  expected: 17 `NotImplementedError` and one pipeline assertion against the
  stub. Awaiting owner review and the T-7 test freeze.
- 2026-11-21: Owner approved the T-7 freeze at `45a156e`. Phase 3 implemented
  `tools/parsers/ruff.py` and `tiers/ruff_tier.py` at `8cb9a6b`; all 18 frozen
  tests pass. Full gate `uv run pytest -q` 164 passed, 2 skipped; format, lint,
  and strict types pass. T-7 checkbox marked.
- 2026-11-21: T-10 Phase 2 stubs (`output/json_output.py`,
  `output/human.py`) and `tests/unit/test_output.py` written at `7f3b21e`.
  `uv run ruff format --check .` and `uv run ruff check .` pass; `uv run mypy`
  reports no issues in 21 source files. The target command fails 11/11 as
  expected with `NotImplementedError`; full suite is 164 passed, 2 skipped,
  11 expected failures. Awaiting owner review and the T-10 test freeze.
- 2026-11-21: Owner approved the T-10 freeze at `7f3b21e`. Phase 3 implemented
  `output/json_output.py` and `output/human.py` at `10c215e`; all 11 frozen
  tests pass. Full gate `uv run pytest -q` 175 passed, 2 skipped; format, lint,
  and strict types pass. T-10 checkbox marked.
- 2026-11-21: T-11 Phase 2 stubs (`app.py`, `cli.py`, `__main__.py`), console
  script, and `tests/acceptance/test_cli_contract.py`,
  `test_human_output.py`, and `test_exit_codes.py` written at `c568da0`.
  `uv run ruff format --check .` and `uv run ruff check .` pass; `uv run mypy`
  reports no issues in 24 source files. The target command fails 32/32 with
  `NotImplementedError`; the console script is installed and reachable.
  Awaiting owner review and the T-11 test freeze.
- 2026-11-21: Owner approved the T-11 freeze at `c568da0`. Phase 3 wired
  `app.py` and `cli.py` at `c1e9e5b`; all 32 frozen acceptance tests pass,
  `uv run strictr --version` prints 0.0.0, and the full gate
  `uv run pytest -q` is 207 passed, 2 skipped. Format, lint, and strict types
  pass. T-11 checkbox marked; WU-2 complete.
- 2026-11-21: Draft PR #11 opened by the owner. Traceability fails on the
  expected missing AC-9/AC-10/AC-11/AC-16 tests and on the non-Conventional
  subject of the T-3 freeze commit `12dfa43`. A local run with
  `HEAD_REF=feat/003-check-command`,
  `PR_TITLE=feat(check): add check command for tier 0 and ruff [003]`, and
  `BASE_REF=main` reproduces both.
- 2026-11-21: Owner chose to leave branch history as-is. The T-3 commit-subject
  blocker remains open; no rewrite, no T-8 work in this session.
- 2026-11-21: T-8 Phase 2 stubs (`tools/parsers/mypy.py`,
  `tools/parsers/pyright.py`, `tiers/types_tier.py`) and
  `tests/unit/test_types.py` written at `87984c3`.
  `uv run ruff format --check .` and `uv run ruff check .` pass; `uv run mypy`
  reports no issues in 27 source files. The target command fails 53/53 as
  expected: 50 `NotImplementedError` and 3 pipeline assertions against the
  stub. Full suite is 207 passed, 2 skipped, 53 expected failures. Awaiting
  owner review and the T-8 test freeze.
- 2026-11-22: Owner approved the T-8 freeze at `87984c3` (Q1-Q5). Phase 3
  implemented `tools/parsers/mypy.py`, `tools/parsers/pyright.py`, and
  `tiers/types_tier.py`, and wired `TypesTier` into `app._pipeline_tiers` at
  `18d0747`. All 53 frozen tests pass; full gate `uv run pytest -q` is
  260 passed, 2 skipped; format, lint, and strict types pass. Real CLI smoke
  covered explicit/auto mypy, `none`, and missing pyright. T-8 checkbox marked;
  WU-3 complete.
- 2026-11-22: T-9 Phase 2 stubs (`tools/parsers/pytest_junit.py`,
  `tiers/pytest_tier.py`) and `tests/unit/test_pytest.py` written at `1cb2c03`.
  `uv run ruff format --check .` and `uv run ruff check .` pass;
  `uv run mypy` reports no issues in 29 source files. The target command fails
  48/48 as expected. Awaiting owner review and the T-9 test freeze.
- 2026-11-22: Owner approved the T-9 freeze at `1cb2c03`. Phase 3 implemented
  `tools/parsers/pytest_junit.py` and `tiers/pytest_tier.py`, and wired
  `PytestTier` into `app._pipeline_tiers` at `c619c3c`. All 48 frozen tests
  pass; full gate `uv run pytest -q` is 308 passed, 2 skipped; format, lint, and
  strict types pass. Real CLI smoke on a failing test reports tier2 `fail`, node
  ID, line 7, `AssertionError`, and counts 2/2/0. T-9 checkbox marked; WU-4
  complete.
- 2026-11-22: T-12 Phase 2 fixtures and acceptance tests written at `8e7fb42`.
  Added `tests/fixtures/projects/` (clean, syntax-error, ruff-error, type-error,
  test-failure, no-tests, empty, `path with space-ü`, timeout), fixture excludes
  in `tests/conftest.py` and Ruff `extend-exclude`, and acceptance modules
  `test_discovery.py`, `test_tiers.py`, and `test_timeout.py`.
  `uv run ruff format --check .`, `uv run ruff check .`, and `uv run mypy` pass.
  Target command `uv run pytest tests/acceptance -q` fails only at
  `test_path_with_spaces_and_unicode`: locale-encoded stdout violates AC-2's
  UTF-8 requirement. Full suite is 322 passed, 3 skipped, 1 expected failure.
  Awaiting owner review and the T-12 freeze.
- 2026-11-22: Owner approved the T-12 freeze at `8e7fb42`. Phase 3 made CLI
  stdout/stderr UTF-8 at `70335bf`, fixing locale-dependent JSON paths without
  changing the frozen tests. `uv run pytest tests/acceptance -q` -> 47 passed,
  1 skipped; full gate `uv run pytest -q` -> 323 passed, 3 skipped; format,
  lint, and strict types pass. T-12 checkbox marked; WU-5 complete.
- 2026-11-22: T-12b Phase 2 hardening tests frozen at `ffcbb92`.
  `tests/unit/test_runner_hardening.py` fails 3/3 as expected: unbounded cleanup
  when tree termination does nothing, `OSError` escaping when termination fails,
  and no child cleanup on `KeyboardInterrupt`. The CLI 130 test passes.
  Format, lint, and strict types pass. Awaiting Phase 3.
- 2026-11-22: Owner approved the T-12b hardening slice. Phase 3 implemented
  bounded timeout cleanup and interrupt termination in `tools/runner.py` at
  `94b30c2`. Phase 4 added `tests/acceptance/test_envelope_schema.py` at
  `a69b046`; target command -> 11 passed, acceptance -> 54 passed, 1 skipped,
  full gate -> 334 passed, 3 skipped; format, lint, and strict types pass.
  T-12b checkbox marked.
- 2026-11-22: T-13 Phase 2 docs contract test written at `b0796c1`.
  `tests/unit/test_check_docs.py` covers AC-16 for README, CHANGELOG, AGENTS,
  and the system overview. `uv run ruff format --check .`, `uv run ruff check .`,
  and `uv run mypy` pass. The target command fails 4/4 on assertions, not import
  errors.
- 2026-11-22: Owner approved the T-13 freeze and Phase 4. Docs updated at
  `b2fef75`; `tests/unit/test_check_docs.py` -> 4 passed; full gate
  `uv run pytest -q` -> 338 passed, 3 skipped; format, lint, and strict types
  pass. Traceability AC coverage passed; only the known T-3 commit subject
  failed.
- 2026-11-22: Owner approved the Phase 5 cleanup. The T-3 commit subject was
  reworded to `test(core): add stubs and tests for T-3`, all freeze hashes in
  this file were remapped, documentation bookkeeping was updated, and the path
  normalization gap found in the audit was deferred to spec 004. Closeout at
  `26fd58e`; full gate and traceability pass; T-13 checkbox marked. Ready for
  the owner to merge.
- 2026-11-22: PR #11 merged to `main` at `5897fc5`; the branch was deleted and
  the spec was moved to `specs/archive/003-check-command/`. The deferred
  discovery-error target normalization is now in spec 004 as AC-9.
- Next: none. Spec 004 is active.
