# Blueprint: Product discovery

- Spec: `specs/active/001-product-discovery/spec.md`
- Status: in-progress
- Owner: Ge Rui Sen

## Approach

Create two durable product documents and one docs test:

- `docs/product/vision.md` — product source of truth.
- `docs/product/evaluation.md` — falsifiable evaluation plan.
- `tests/unit/test_product_docs.py` — verifies required sections and links.

Update repository entry points and the old spec numbering, then run the local
gates and traceability check. No product code, architecture, or benchmark
execution is added.

## Modules and boundaries

| Module | Responsibility | Change |
|---|---|---|
| `docs/product/vision.md` | Problem, users, gap, scope, non-goals | New |
| `docs/product/evaluation.md` | Metrics, baselines, targets, kill criteria | New |
| `tests/unit/test_product_docs.py` | Documentation contract checks | New |
| `AGENTS.md` | Read order, repo map, numbering, claim discipline | Modified |
| `README.md` | Product links and status | Modified |
| `docs/architecture/system-overview.md` | Spec numbering only | Modified |
| `CHANGELOG.md` | Discovery entry | Modified |

## Contracts

No runtime contracts. The durable document sections are the contract:

- Vision: positioning, problem, evidence/assumptions, users, alternatives/gap,
  principles, locked decisions, goals, non-goals, scope, adoption, risks, open
  questions, success/kill criteria.
- Evaluation: metrics, baselines, workloads/corpus, measurement protocol,
  conditional targets, kill criteria, public-benchmark caveats, reporting.

## Failure modes

| Failure | Behavior | Test |
|---|---|---|
| Missing required section | Docs test fails | `test_vision_has_required_sections`, `test_evaluation_has_required_sections` |
| Old `001-check-command` reference remains | Docs test fails | `test_entry_points_use_new_numbering` |
| Product docs not linked from entry points | Docs test fails | `test_entry_points_link_product_docs` |
| Changelog missing | Docs test fails | `test_changelog_records_product_discovery` |
| Unmeasured claim presented as fact | Review checklist catches it | Manual review; not automated |
| Architecture leaks into discovery | Review checklist catches it | Manual review |

## Security and trust boundaries

No code execution or runtime behavior. The documents lock the v0.1 trust stance:
local execution, no sandbox claim, isolation deferred to a later spec.

## Test plan

| AC | Layer | Test | Command | Status |
|---|---|---|---|---|
| AC-1 | docs | `test_vision_has_required_sections` | `uv run pytest tests/unit/test_product_docs.py -q` | pass |
| AC-2 | docs | `test_evaluation_has_required_sections` and `test_targets_are_conditional` | same | pass |
| AC-3 | docs | `test_entry_points_use_new_numbering` and `test_entry_points_link_product_docs` | same | pass |
| AC-4 | docs | `test_changelog_records_product_discovery` and link checks | same | pass |

## Tasks

- [x] T-1: Write `docs/product/vision.md` — verify: `uv run pytest tests/unit/test_product_docs.py -q` — AC: AC-1
- [x] T-2: Write `docs/product/evaluation.md` — verify: same — AC: AC-2
- [x] T-3: Update `AGENTS.md`, `README.md`, and architecture numbering — verify: same — AC: AC-3
- [x] T-4: Update `CHANGELOG.md` — verify: same — AC: AC-4
- [x] T-5: Add documentation tests — verify: `uv run pytest tests/unit/test_product_docs.py -q` — AC: AC-1..AC-4
- [x] T-6: Run the full gate and traceability check — verify: `uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest -q` — AC: AC-1..AC-4

## Review checklist

- [ ] Every numeric claim is sourced or labeled a conditional hypothesis.
- [ ] The locked decisions are present and internally consistent.
- [ ] No architecture, tech-stack, or implementation details leaked in.
- [ ] The non-goals are explicit and do not contradict the scope.
- [ ] The primary user is agent-first; secondary and non-users are clear.
- [ ] The trust stance is local-only with an explicit warning.
- [ ] v0.1 scope is Tier 0–1 plus compact pytest.
- [ ] Links resolve and old numbering is gone.

## Rollback

Revert the discovery commit and delete the branch. No runtime behavior or data is
affected.

## Open technical questions

None for this spec. Deferred product/technical questions are listed in the spec
and vision document.

## Retrospective

Fill after merge.
