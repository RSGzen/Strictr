# Progress: Check command

- Phase: 4 Integrate & Verify (WU-1 complete; next WU-2/T-6 Phase 2)
- Work unit: WU-1 complete (T-2..T-5)
- Task: WU-1 Phase 4 integration complete
- Spec: 003
- Branch: feat/003-check-command
- Phase 1 gate: complete; spec 1.4 and blueprint approved (see git log)
- Phase 2 gate: T-3 frozen at `d2f85f9`; T-4 frozen at `85536ef`; T-5 frozen at
  `5a58bd9`
- Frozen tests: `tests/unit/test_contract.py` (Phase 1/T-2);
  `tests/unit/test_core.py` at `d2f85f9`; `tests/unit/test_discovery.py`
  at `85536ef`; `tests/unit/test_runner.py` at `5a58bd9`
- T-3 gate: complete at `7e47daa`; `uv run pytest tests/unit/test_core.py -q`
  -> 38 passed; `uv run ruff format --check .`, `uv run ruff check .`,
  `uv run mypy`, and `uv run pytest -q` pass (106 passed)
- T-4 gate: complete at `6fb7d9a`; `uv run pytest tests/unit/test_discovery.py -q`
  -> 19 passed, 2 skipped; full gate `uv run pytest -q` -> 125 passed,
  2 skipped; format, lint, and strict types pass
- T-5 gate: complete at `a931278`; `uv run pytest tests/unit/test_runner.py -q`
  -> 8 passed; full gate `uv run pytest -q` -> 133 passed, 2 skipped; format,
  lint, and strict types pass
- WU-1 Phase 4 evidence at `bd67d2c`:
  `uv run pytest tests/unit/test_wu1_integration.py -q` -> 6 passed; full gate
  `uv run pytest -q` -> 139 passed, 2 skipped; format, lint, and strict types
  pass. Coverage: discovery-to-envelope scope, real subprocess fail-fast,
  timeout, missing tool, Unicode paths, warning aggregation
- Next command: Phase 2 for T-6; write the Tier 0 stub and failing
  `tests/unit/test_tier0.py`, then run `uv run pytest tests/unit/test_tier0.py -q`
- Spec changes: none; owner approved correcting the T-2 error golden from
  `earlier_tier_error` to `earlier_tier_failed` to match AC-12
- Size exception: ADR 0010 (one spec/one PR); future specs return to default
- Open items: real pyright is not in CI; the timeout acceptance test needs a
  generous bound; process-tree termination is proven by the Phase 4/T-12
  acceptance test; discovery-failure envelope mapping stays with T-11
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
- Next: start T-6 Phase 2 (Tier 0 stub and failing unit tests).
