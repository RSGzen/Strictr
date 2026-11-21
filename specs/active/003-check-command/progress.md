# Progress: Check command

- Phase: 2 Stub & Test
- Work unit: WU-1
- Task: T-3 core models and pipeline
- Spec: 003
- Branch: feat/003-check-command
- Phase 1 gate: complete; spec 1.3 and blueprint approved at `fdc01dd`
- Frozen tests: `tests/unit/test_contract.py` (Phase 1/T-2)
- Next command: write T-3 stubs and failing tests; run `uv run mypy` and
  `uv run ruff check .`, then `uv run pytest tests/unit/test_core.py -q`
  (expected red); commit the freeze
- Spec changes: none
- Open items: real pyright is not in CI; the timeout acceptance test needs a
  generous bound
- Session state: no `handoff.md`; task briefs are in `blueprint.md`

## Phase log

- 2026-11-21: Phase 1 complete. Spec 003 revision 1.3, blueprint, schema, and
  contract tests approved.
- 2026-11-21: Switched to the single-agent phase workflow. Separate
  contract-test sessions folded into Phase 2 of WU-2 and WU-6.
- Next: Phase 2 for T-3. Write `core` stubs/interfaces and failing
  `tests/unit/test_core.py`; `mypy` and `ruff` must pass; freeze at a commit.
  Then start a new session for Phase 3.
