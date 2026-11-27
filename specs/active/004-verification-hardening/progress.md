# Progress: Verification hardening and edge-case coverage

- Phase: 3 Implement & Reconcile for T-4 and T-9; T-1..T-3 and T-5..T-8 are
  implemented/frozen, with POSIX evidence pending for T-2 and T-3
- Spec: 004
- Branch: feat/004-verification-hardening
- Base: main at `5897fc5`
- Dependency: `003-check-command` is merged; this branch is rebased onto `main`.
- Last gate: Phase 1 approved by the owner on 2026-11-22 at `6010728`;
  T-1 freeze approved at `558dfde`; T-2 freeze approved at `ae77ab2`;
  T-3 freeze approved at `585bfd6`; T-4..T-9 freeze approved at `ac7818c`
  on 2026-11-27.
- Frozen tests: `tests/acceptance/test_scope_paths.py` at `558dfde` (AC-1);
  `tests/unit/test_path_display.py` at `ae77ab2` (AC-2);
  `tests/unit/test_output_non_utf8.py` and
  `tests/acceptance/test_non_utf8_paths.py` at `585bfd6` (AC-3);
  `tests/unit/test_human_hardening.py` and
  `tests/acceptance/test_human_errors.py` (AC-4);
  `tests/acceptance/test_type_config.py` (AC-5);
  `tests/acceptance/test_pytest_config.py` (AC-6);
  `tests/acceptance/test_redaction_truncation.py` (AC-7);
  `tests/unit/test_traceability_entry.py` (AC-8); and
  `tests/acceptance/test_discovery_error_paths.py` (AC-9) all at `ac7818c`.
- Next command: Phase 3 for T-4 and T-9 only:
  `uv run pytest tests/unit/test_human_hardening.py tests/acceptance/test_human_errors.py -q`
  and `uv run pytest tests/acceptance/test_discovery_error_paths.py -q`.
  T-5..T-8 need no production change; their exact commands already pass.
  Before T-10, POSIX CI must run the T-2 and T-3 acceptance modules.
- Spec changes: revision 1.1 adds AC-9 for discovery-error target normalization
  and rebases the branch after `003` merged.
- Open items: spec 003 archive closeout is pending; T-1 has no Phase 3 because
  no production change was needed. T-2 tests remain skipped locally on Windows
  (`WinError 1314`); its completion checkbox and AC-2 pass status await real
  POSIX execution evidence. T-3 is implemented at `bf9d277`; its checkbox and
  AC-3 pass status await the frozen acceptance tests on POSIX CI. No PR is open
  yet, and CI only runs on pull requests, so a draft PR is required for that
  evidence. The POSIX FIFO acceptance case is omitted because ruff reads the
  FIFO; the human skipped-count unit test is the AC-4 evidence.

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
- 2026-11-22: Owner lifted the T-3 hold and assigned T-3 Phase 2. Wrote
  `tests/unit/test_output_non_utf8.py` and
  `tests/acceptance/test_non_utf8_paths.py` at `585bfd6`. The exact command
  `uv run pytest tests/unit/test_output_non_utf8.py tests/acceptance/test_non_utf8_paths.py -q`
  -> 2 failed (`UnicodeEncodeError` in both renderers), 2 skipped (POSIX-only).
  Format, lint, and strict types pass. No production code changed; the
  surrogate-safe helper belongs to Phase 3. Awaiting owner review and freeze.
- 2026-11-22: Owner approved the T-3 freeze at `585bfd6` and assigned Phase 3.
  Implemented `escape_surrogates` in `core/text.py` and applied it in
  `render_json` and `render_human` at `bf9d277`. Exact command -> 2 passed,
  2 skipped on Windows. A stdlib-only POSIX smoke check in Ubuntu WSL passed:
  JSON strictly decoded as UTF-8 with `\udcff` escaped and `módulo.py` readable;
  human mode exited 1 without a traceback. Full suite -> 343 passed, 8 skipped;
  format, lint, and strict types pass. The T-3 checkbox and AC-3 pass status
  stay open until the frozen acceptance tests run on POSIX CI.
- 2026-11-27: Phase 2 grouped slice T-4..T-9 wrote seven test modules at
  `ac7818c`. `uv run pytest -q` -> 10 failed, 361 passed, 8 skipped; the ten
  failures are the expected T-4 human-rendering (6) and T-9 discovery-target
  (4) gaps. T-5..T-8 pass against current behavior and need no Phase 3 unless
  freeze review finds a defect. Format, lint, and strict types pass;
  collect-only -> 379 tests; local traceability -> ok with a placeholder PR
  title.
- 2026-11-27: Owner approved the T-4..T-9 freeze at `ac7818c` with no changes.
  T-5..T-8 are complete with no production change. Phase 3 starts for T-4
  (`output/human.py`) and T-9 (`app.py`) only.
