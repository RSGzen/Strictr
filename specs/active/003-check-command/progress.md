# Progress: Check command

- Phase: 3 Implement & Reconcile
- Work unit: WU-1
- Task: T-3 core models and pipeline
- Spec: 003
- Branch: feat/003-check-command
- Phase 1 gate: complete; spec 1.4 and blueprint approved (see git log)
- Phase 2 gate: frozen at `d2f85f9`
- Frozen tests: `tests/unit/test_contract.py` (Phase 1/T-2);
  `tests/unit/test_core.py` at `d2f85f9`
- T-3 Phase 2 evidence: `uv run mypy` pass; `uv run ruff format --check .` pass;
  `uv run ruff check .` pass; `uv run pytest tests/unit/test_core.py -q`
  -> 38 failed, all `NotImplementedError` from the T-3 stubs; no import errors
- Next command: implement `core` (pipeline, text, paths, models) until
  `uv run pytest tests/unit/test_core.py -q` passes
- Spec changes: none; owner approved correcting the T-2 error golden from
  `earlier_tier_error` to `earlier_tier_failed` to match AC-12
- Size exception: ADR 0010 (one spec/one PR); future specs return to default
- Open items: real pyright is not in CI; the timeout acceptance test needs a
  generous bound
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
- Next: implement T-3 `core` behavior, then mark the T-3 checkbox when
  `uv run pytest tests/unit/test_core.py -q` passes.
