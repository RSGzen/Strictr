# Repository Setup Checklist

These settings are manual GitHub configuration, not code. Review them after the
bootstrap PR merges.

## Main branch

- [x] Require a pull request before merging.
- [x] Require status checks: `quality`, `test (ubuntu-latest, 3.13)`,
      `test (windows-latest, 3.13)`, `traceability`.
- [x] Block force pushes.
- [x] Require linear history.
- [x] Automatically delete head branches.

## Actions

- [x] Default workflow permissions: read-only.
- [x] Allow GitHub Actions to create and approve pull requests: off.
- [x] Keep standard runners; no larger runners.
- [x] Set concurrency on workflows (already in `ci.yml`).

## Security

- [x] Secret scanning enabled.
- [x] Push protection enabled.
- [x] Dependabot alerts enabled.
- [x] Dependabot security updates enabled.
- [x] Third-party actions pinned; Dependabot updates them.
- [ ] No secrets in `pull_request` workflows from forks.

## Ownership

- [ ] CODEOWNERS added when a second maintainer joins.
- [ ] Review requirement enabled only when a second person can review.
- [ ] Administrators limited to the repository owner.
- [ ] Release tags created manually from `main`.

## Cost

- [ ] Pull-request CI uses Linux.
- [ ] Windows runs on pull requests while the repository is public; otherwise
      move Windows to `main` or a nightly/manual workflow.
- [ ] Benchmark and evaluation jobs run manually only.

## Local setup

```powershell
uv sync
git config core.hooksPath .githooks
```

The hook adds `Spec: NNN` from the branch name. Hooks are convenience; CI is the
enforcement.

## Traceability environment

The traceability script expects these variables in CI:

- `HEAD_REF` — pull request head branch
- `PR_TITLE` — pull request title
- `BASE_REF` — pull request base branch

Run it locally against the current branch with a temporary title:

```powershell
$env:HEAD_REF = (git branch --show-current)
$env:PR_TITLE = "docs: add SDD bootstrap [000]"
$env:BASE_REF = "main"
uv run pytest --collect-only -q
uv run python scripts/check_traceability.py
```
