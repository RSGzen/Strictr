# Progress: Verification hardening and edge-case coverage

- Phase: 1 Specify & Plan (approved)
- Spec: 004
- Branch: feat/004-verification-hardening
- Base: main at `00faf89`
- Dependency: `003-check-command` must merge to `main` first; rebase this branch
  on `main` after `003` lands. This branch intentionally starts from `main` so
  the `003` and `004` PRs stay separate.
- Last gate: Phase 1 approved by the owner on 2026-11-22 at `4a479a2`
- Frozen tests: none
- Next command: after `003` merges and this branch is rebased, start T-1 Phase 2
  with `uv run pytest tests/acceptance/test_scope_paths.py -q`.
- Spec changes: Phase 1 approved; nested-cwd, human-output, and non-UTF8
  decisions are recorded in spec 1.0.
- Open items: blocked on `003` merging and this branch rebasing on `main`.

## Phase log

- 2026-11-22: Initial spec 004 v0.1 and blueprint draft. No product code or
  tests changed. The draft is based on the post-`003` audit and intentionally
  excludes pyright fallback, config-error policy, `.pyi` CLI coverage, and
  performance work.
- 2026-11-22: Owner approved Phase 1 at `4a479a2` and resolved all three
  questions: nested-cwd ledger semantics, human-output format, and non-UTF8
  escaping. Spec 1.0 and blueprint are approved. Implementation remains blocked
  until `003` merges and this branch rebases on `main`.
