# Blueprint: SDD bootstrap and repository governance

- Spec: `specs/active/000-sdd-bootstrap/spec.md`
- Status: in-progress (all tasks verified locally; awaiting PR)
- Owner: Ge Rui Sen

## Approach

Create the minimum governance and automation needed to run the SDD protocol on
the next spec:

- Human-owned governance: `AGENTS.md`, constitution, architecture, ADR.
- Spec and blueprint templates, plus this bootstrap spec as the first example.
- A small Python package with uv, ruff, mypy, and pytest.
- A traceability checker with pure functions and unit tests.
- CI that runs quality, tests, and traceability.
- PR and commit conventions that keep the spec ID attached to the change.

No product code is added. The package contains only the version marker and the
traceability module, which is repository tooling.

## Modules and boundaries

| Module | Responsibility | Change |
|---|---|---|
| `strictr.traceability` | Validate branch/title/spec/commit/AC policy | New |
| `scripts/check_traceability.py` | Thin CLI wrapper for CI | New |
| `tests/unit/test_traceability.py` | Unit tests for policy logic | New |
| `tests/unit/test_bootstrap.py` | Verify bootstrap artifacts exist | New |
| `tests/conftest.py` | Write AC collection report | New |

## Contracts

### Traceability checker

Inputs via environment:

- `HEAD_REF` — PR head branch
- `PR_TITLE` — PR title
- `BASE_REF` — base branch

Output: exit `0` when valid, `1` with error lines when invalid.

### AC report

`pytest --collect-only` writes `build/ac-tests.json`:

```json
{
  "AC-1": ["tests/unit/test_bootstrap.py::test_governance_documents_exist"]
}
```

The checker compares this report with the ACs in the spec.

## Failure modes

| Failure | Behavior | Test |
|---|---|---|
| Malformed branch name | Exit 1 with branch error | `test_parse_branch_rejects_malformed` |
| Missing spec ID for a feature branch | Exit 1 | `test_parse_branch_requires_id_for_feature` |
| PR title missing or mismatched ID | Exit 1 | `test_validate_pr_rejects_title_mismatch` |
| Spec missing or draft with code changes | Exit 1 | `test_validate_pr_rejects_draft_spec_with_code` |
| Commit subject not Conventional Commits | Exit 1 | `test_validate_commits_rejects_bad_subject` |
| Missing `Spec:` trailer | Exit 1 | `test_validate_commits_rejects_missing_trailer` |
| AC without test | Exit 1 | `test_validate_pr_rejects_missing_ac_test` |
| Orphan AC marker | Exit 1 | `test_validate_pr_rejects_orphan_ac` |
| Bot branch | Exempt | `test_parse_branch_bot_is_exempt` |

## Security and trust boundaries

The checker reads the PR title and commit messages, which are untrusted input.
It treats them as data, never executes them, and prints them as plain text. CI
uses read-only permissions. No secrets are required.

## Test plan

| AC | Layer | Test | Command | Status |
|---|---|---|---|---|
| AC-1 | unit | `test_governance_documents_exist_and_have_required_sections` | `uv run pytest tests/unit/test_bootstrap.py -q` | pass |
| AC-2 | unit | `test_spec_templates_and_bootstrap_spec_exist` | same | pass |
| AC-3 | unit | `tests/unit/test_traceability.py` (module marker) | `uv run pytest tests/unit/test_traceability.py -q` | pass |
| AC-4 | unit | `test_project_config_and_ci_exist` | `uv run pytest tests/unit/test_bootstrap.py -q` | pass |
| AC-5 | unit | `test_pr_template_hook_and_setup_checklist_exist` | same | pass |
| AC-6 | unit | `test_testing_guide_covers_required_topics` | same | pass |
| AC-7 | unit | `test_readme_describes_status_and_quickstart` | same | pass |

## Tasks

- [x] T-1: Add governance documents — verify: `uv run pytest tests/unit/test_bootstrap.py -q` — AC: AC-1
- [x] T-2: Add spec and blueprint templates plus bootstrap spec — verify: `uv run pytest tests/unit/test_bootstrap.py -q` — AC: AC-2
- [x] T-3: Add Python project config and package skeleton — verify: `uv sync --locked` — AC: AC-4
- [x] T-4: Add traceability module, script, and unit tests — verify: `uv run pytest tests/unit/test_traceability.py -q` — AC: AC-3
- [x] T-5: Add CI workflow for quality, tests, and traceability — verify: `uv run ruff check . && uv run mypy` — AC: AC-4
- [x] T-6: Add PR template, commit-msg hook, and repo setup checklist — verify: `uv run pytest tests/unit/test_bootstrap.py -q` — AC: AC-5
- [x] T-7: Add testing guide, README, and changelog — verify: `uv run pytest -q` — AC: AC-6, AC-7

## Rollback

Revert the bootstrap commit and delete the branch. No product code or data is
affected. Removing the traceability workflow and script restores the previous
state.

## Open technical questions

None.

## Retrospective

Fill after merge. Candidate questions:

- Did the envelope/CLI contract stay small enough?
- Did the traceability check catch a real mistake?
- Was any governance section unused or unclear?
