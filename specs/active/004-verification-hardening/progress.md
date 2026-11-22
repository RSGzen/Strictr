# Progress: Verification hardening and edge-case coverage

- Phase: 2 Stub & Test — T-2 frozen; T-3 on hold per owner
- Spec: 004
- Branch: feat/004-verification-hardening
- Base: main at `5897fc5`
- Dependency: `003-check-command` is merged; this branch is rebased onto `main`.
- Last gate: Phase 1 approved by the owner on 2026-11-22 at `6010728`;
  T-1 freeze approved at `558dfde`; T-2 freeze approved at `ae77ab2`.
- Frozen tests: `tests/acceptance/test_scope_paths.py` at `558dfde` (AC-1);
  `tests/unit/test_path_display.py` at `ae77ab2` (AC-2)
- Next command: POSIX CI run of
  `uv run pytest tests/unit/test_path_display.py -q`; T-3 is on hold per the
  owner and must not start.
- Spec changes: revision 1.1 adds AC-9 for discovery-error target normalization
  and rebases the branch after `003` merged.
- Open items: spec 003 archive closeout is pending; T-1 has no Phase 3 because
  no production change was needed. T-2 tests remain skipped locally on Windows
  (`WinError 1314`); its completion checkbox and AC-2 pass status await real
  POSIX execution evidence. T-3 not started.

## Phase log

- 2026-11-22: Initial spec 004 v0.1 and blueprint draft. No product code or
  tests changed. The draft is based on the post-`003` audit and intentionally
  excludes pyright fallback, config-error policy, `.pyi` CLI coverage, and
  performance work.
- 2026-11-22: Owner approved Phase 1 at `6010728` and resolved all three
  questions: nested-cwd ledger semantics, human-output format, and non-UTF8
  escaping. Spec 1.0 and blueprint are approved.
- 2026-11-22: `003-check-command` merged to `main` at `5897fc5`; this branch was
  rebased onto `main`. Spec revision 1.1 adds AC-9 and T-9 for discovery-error
  target normalization, moved out of the `003` deferral. No code or tests
  changed yet; T-1 Phase 2 is next.
- 2026-11-22: T-1 Phase 2 wrote `tests/acceptance/test_scope_paths.py` at
  `558dfde`. `uv run pytest tests/acceptance/test_scope_paths.py -q` -> 3
  passed; format, lint, and strict types pass. The tests pass against existing
  `003` behavior, so T-1 needs no production change. Awaiting owner review and
  the T-1 freeze.
- 2026-11-22: Owner approved the T-1 freeze at `558dfde` and confirmed no Phase 3
  is needed. T-1 is complete and the blueprint checkbox is marked. Next is T-2
  Phase 2; no work started on it.
- 2026-11-22: T-2 Phase 2 wrote `tests/unit/test_path_display.py` at `ae77ab2`.
  `uv run pytest tests/unit/test_path_display.py -q` -> 3 skipped: this Windows
  session cannot create symlinks (`WinError 1314`). The tests cover discovered
  `.py`/`.pyi` links and an explicitly targeted link, asserting link display
  paths in discovery and Tier 0 diagnostics. Format, lint, and strict types
  pass. Awaiting owner review and the T-2 freeze; POSIX CI must run the tests.
- 2026-11-22: Owner approved the T-2 freeze at `ae77ab2` and put T-3 on hold.
  The freeze is recorded. T-2's checkbox and AC-2 pass status stay open until a
  POSIX run exercises the symlink tests; a local skip is not treated as a pass.
  No T-3 work started.
