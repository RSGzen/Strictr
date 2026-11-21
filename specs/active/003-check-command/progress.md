# Progress: Check command

- Phase: 2 Stub & Test (next: T-4; T-3 complete)
- Work unit: WU-1
- Task: T-4 discovery (T-3 complete)
- Spec: 003
- Branch: feat/003-check-command
- Phase 1 gate: complete; spec 1.4 and blueprint approved (see git log)
- Phase 2 gate: frozen at `d2f85f9`
- Frozen tests: `tests/unit/test_contract.py` (Phase 1/T-2);
  `tests/unit/test_core.py` at `d2f85f9`
- T-3 gate: complete at `7e47daa`; `uv run pytest tests/unit/test_core.py -q`
  -> 38 passed; `uv run ruff format --check .`, `uv run ruff check .`,
  `uv run mypy`, and `uv run pytest -q` pass (106 passed)
- Next command: Phase 2 for T-4; write `core/discovery.py` stubs and failing
  `tests/unit/test_discovery.py`, then run
  `uv run pytest tests/unit/test_discovery.py -q`
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
- 2026-11-21: T-3 Phase 3 complete at `7e47daa`. All 38 frozen tests pass;
  full gate `uv run pytest -q` 106 passed; format, lint, and strict types pass.
  T-3 checkbox marked.
- Next: start T-4 Phase 2 (discovery stubs and failing unit tests).
