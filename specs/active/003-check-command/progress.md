# Progress: Check command

- Phase: 2 Stub & Test (T-11 written; awaiting test freeze)
- Work unit: WU-2 in progress (T-6, T-7, T-10 complete; T-11 Phase 2 written)
- Task: T-11 Phase 2 written; awaiting freeze
- Spec: 003
- Branch: feat/003-check-command
- Phase 1 gate: complete; spec 1.4 and blueprint approved (see git log)
- Phase 2 gate: T-3 frozen at `d2f85f9`; T-4 frozen at `85536ef`; T-5 frozen at
  `5a58bd9`; T-6 frozen at `a080b62`; T-7 frozen at `1ee081c`; T-10 frozen at
  `47099f4`; T-11 candidate at `f15bc2d`
- Frozen tests: `tests/unit/test_contract.py` (Phase 1/T-2);
  `tests/unit/test_core.py` at `d2f85f9`; `tests/unit/test_discovery.py`
  at `85536ef`; `tests/unit/test_runner.py` at `5a58bd9`;
  `tests/unit/test_tier0.py` at `a080b62`; `tests/unit/test_ruff.py`
  at `1ee081c`; `tests/unit/test_output.py` at `47099f4`; none for T-11 yet
  (candidate: `tests/acceptance/` at `f15bc2d`)
- T-3 gate: complete at `7e47daa`; `uv run pytest tests/unit/test_core.py -q`
  -> 38 passed; `uv run ruff format --check .`, `uv run ruff check .`,
  `uv run mypy`, and `uv run pytest -q` pass (106 passed)
- T-4 gate: complete at `6fb7d9a`; `uv run pytest tests/unit/test_discovery.py -q`
  -> 19 passed, 2 skipped; full gate `uv run pytest -q` -> 125 passed,
  2 skipped; format, lint, and strict types pass
- T-5 gate: complete at `a931278`; `uv run pytest tests/unit/test_runner.py -q`
  -> 8 passed; full gate `uv run pytest -q` -> 133 passed, 2 skipped; format,
  lint, and strict types pass
- T-6 gate: complete at `a23aebe`; `uv run pytest tests/unit/test_tier0.py -q`
  -> 7 passed; full gate `uv run pytest -q` -> 146 passed, 2 skipped; format,
  lint, and strict types pass
- T-7 gate: complete at `013cbb0`; `uv run pytest tests/unit/test_ruff.py -q`
  -> 18 passed; full gate `uv run pytest -q` -> 164 passed, 2 skipped; format,
  lint, and strict types pass
- T-10 gate: complete at `00cb02d`; `uv run pytest tests/unit/test_output.py -q`
  -> 11 passed; full gate `uv run pytest -q` -> 175 passed, 2 skipped; format,
  lint, and strict types pass
- WU-1 Phase 4 evidence at `bd67d2c`:
  `uv run pytest tests/unit/test_wu1_integration.py -q` -> 6 passed; full gate
  `uv run pytest -q` -> 139 passed, 2 skipped; format, lint, and strict types
  pass. Coverage: discovery-to-envelope scope, real subprocess fail-fast,
  timeout, missing tool, Unicode paths, warning aggregation
- Next command: owner review and T-11 freeze at `f15bc2d`; then Phase 3 with
  `uv run pytest tests/acceptance/test_cli_contract.py tests/acceptance/test_human_output.py tests/acceptance/test_exit_codes.py -q`
- Spec changes: none; owner approved correcting the T-2 error golden from
  `earlier_tier_error` to `earlier_tier_failed` to match AC-12
- Size exception: ADR 0010 (one spec/one PR); future specs return to default
- Open items: real pyright is not in CI; the timeout acceptance test needs a
  generous bound; process-tree termination is proven by the Phase 4/T-12
  acceptance test; discovery-failure envelope mapping stays with T-11.
  T-11 tests exercise only the WU-2 two-tier pipeline (Tier 0 + ruff); pass
  paths use `--type-checker none` so they stay valid when T-8/T-9 extend it.
  A CLI-level `partial` exit code is not reachable until T-8; AC-4's
  partial/error mapping remains covered by the frozen T-3 unit test.
- Session state: no `handoff.md`; task briefs are in `blueprint.md`

## Phase log

- 2026-11-21: Phase 1 complete. Spec 003 revision 1.4, blueprint, schema, and
  contract tests approved.
- 2026-11-21: Switched to the single-agent phase workflow. Separate
  contract-test sessions folded into Phase 2 of WU-2 and WU-6.
- 2026-11-21: ADR 0010 records the owner-approved one-time size exception.
- 2026-11-21: Phase 2 frozen at `d2f85f9`; `tests/unit/test_core.py` is the
  T-3 frozen suite. Phase 3 starts from that commit.
- 2026-11-21: Owner approved aligning `tests/fixtures/contract/error.json` with
  AC-12 (`earlier_tier_failed`); the fixture is corrected and the frozen
  contract tests still pass.
- 2026-11-21: T-3 Phase 3 complete at `7e47daa`. All 38 frozen tests pass;
  full gate `uv run pytest -q` 106 passed; format, lint, and strict types pass.
  T-3 checkbox marked.
- 2026-11-21: T-4 Phase 2 stubs and `tests/unit/test_discovery.py` written.
  mypy and ruff pass; the target command fails only with `NotImplementedError`.
  Awaiting owner review and the T-4 test freeze commit.
- 2026-11-21: Owner approved the T-4 freeze at `85536ef`. Phase 3 implemented
  `core/discovery.py` at `6fb7d9a`; 19 frozen tests pass and 2 platform tests
  skip. Full gate `uv run pytest -q` 125 passed, 2 skipped; format, lint, and
  strict types pass. T-4 checkbox marked.
- 2026-11-21: T-5 Phase 2 stubs and `tests/unit/test_runner.py` written.
  mypy and ruff pass; the target command fails only with `NotImplementedError`.
  Awaiting owner review and the T-5 test freeze commit.
- 2026-11-21: Owner approved the T-5 freeze at `5a58bd9`. Phase 3 implemented
  `tools/runner.py` at `a931278`; 8 frozen tests pass. Full gate
  `uv run pytest -q` 133 passed, 2 skipped; format, lint, and strict types pass.
  T-5 checkbox marked.
- 2026-11-21: WU-1 Phase 4 integration complete at `bd67d2c`.
  `tests/unit/test_wu1_integration.py` adds 6 cross-module tests; full gate
  139 passed, 2 skipped; format, lint, and strict types pass. No implementation
  defects surfaced.
- 2026-11-21: T-6 Phase 2 stubs and `tests/unit/test_tier0.py` written at
  `a080b62`. `uv run ruff format --check .` and `uv run ruff check .` pass;
  `uv run mypy` reports no issues in 15 source files. The target command fails
  7/7 as expected: 5 direct `NotImplementedError` and 2 pipeline assertions
  against the stub.
- 2026-11-21: Owner approved the T-6 freeze at `a080b62`. Phase 3 implemented
  `tiers/ast_tier.py` at `a23aebe`; all 7 frozen tests pass. Full gate
  `uv run pytest -q` 146 passed, 2 skipped; format, lint, and strict types pass.
  T-6 checkbox marked.
- 2026-11-21: T-7 Phase 2 stubs (`tools/parsers/ruff.py`,
  `tiers/ruff_tier.py`) and `tests/unit/test_ruff.py` written at `1ee081c`.
  `uv run ruff format --check .` and `uv run ruff check .` pass; `uv run mypy`
  reports no issues in 18 source files. The target command fails 18/18 as
  expected: 17 `NotImplementedError` and one pipeline assertion against the
  stub. Awaiting owner review and the T-7 test freeze.
- 2026-11-21: Owner approved the T-7 freeze at `1ee081c`. Phase 3 implemented
  `tools/parsers/ruff.py` and `tiers/ruff_tier.py` at `013cbb0`; all 18 frozen
  tests pass. Full gate `uv run pytest -q` 164 passed, 2 skipped; format, lint,
  and strict types pass. T-7 checkbox marked.
- 2026-11-21: T-10 Phase 2 stubs (`output/json_output.py`,
  `output/human.py`) and `tests/unit/test_output.py` written at `47099f4`.
  `uv run ruff format --check .` and `uv run ruff check .` pass; `uv run mypy`
  reports no issues in 21 source files. The target command fails 11/11 as
  expected with `NotImplementedError`; full suite is 164 passed, 2 skipped,
  11 expected failures. Awaiting owner review and the T-10 test freeze.
- 2026-11-21: Owner approved the T-10 freeze at `47099f4`. Phase 3 implemented
  `output/json_output.py` and `output/human.py` at `00cb02d`; all 11 frozen
  tests pass. Full gate `uv run pytest -q` 175 passed, 2 skipped; format, lint,
  and strict types pass. T-10 checkbox marked.
- 2026-11-21: T-11 Phase 2 stubs (`app.py`, `cli.py`, `__main__.py`), console
  script, and `tests/acceptance/test_cli_contract.py`,
  `test_human_output.py`, and `test_exit_codes.py` written at `f15bc2d`.
  `uv run ruff format --check .` and `uv run ruff check .` pass; `uv run mypy`
  reports no issues in 24 source files. The target command fails 32/32 with
  `NotImplementedError`; the console script is installed and reachable.
  Awaiting owner review and the T-11 test freeze.
- Next: owner review and T-11 freeze, then Phase 3 CLI wiring.
