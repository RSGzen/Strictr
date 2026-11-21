# Progress: Verification hardening and edge-case coverage

- Phase: 1 Specify & Plan (approved; branch rebased)
- Spec: 004
- Branch: feat/004-verification-hardening
- Base: main at `5897fc5`
- Dependency: `003-check-command` is merged; this branch is rebased onto `main`.
- Last gate: Phase 1 approved by the owner on 2026-11-22 at `6010728`;
  spec revision 1.1 adds AC-9.
- Frozen tests: none
- Next command: start T-1 Phase 2 with
  `uv run pytest tests/acceptance/test_scope_paths.py -q`.
- Spec changes: revision 1.1 adds AC-9 for discovery-error target normalization
  and rebases the branch after `003` merged.
- Open items: spec 003 archive closeout is pending; 004 implementation starts
  with T-1.

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
