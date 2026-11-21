# Progress: Verification hardening and edge-case coverage

- Phase: 1 Specify & Plan (draft)
- Spec: 004
- Branch: feat/004-verification-hardening
- Base: main at `00faf89`
- Dependency: `003-check-command` must merge to `main` first; rebase this branch
  on `main` after `003` lands. This branch intentionally starts from `main` so
  the `003` and `004` PRs stay separate.
- Last gate: none
- Frozen tests: none
- Next command: owner reviews spec 004 v0.1 and resolves the three Phase 1
  questions; then start T-1 Phase 2.
- Spec changes: none
- Open items: nested-cwd ledger semantics, human-output wording, and
  non-UTF8 escaping representation need owner confirmation; `003` must merge
  before implementation.

## Phase log

- 2026-11-22: Initial spec 004 v0.1 and blueprint draft. No product code or
  tests changed. The draft is based on the post-`003` audit and intentionally
  excludes pyright fallback, config-error policy, `.pyi` CLI coverage, and
  performance work.
