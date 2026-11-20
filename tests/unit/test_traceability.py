from __future__ import annotations

from pathlib import Path

import pytest

from strictr.traceability import (
    BranchInfo,
    SpecInfo,
    TraceabilityError,
    code_change,
    extract_ac_ids,
    load_ac_report,
    load_spec,
    parse_branch,
    parse_front_matter,
    parse_title,
    validate_commits,
    validate_pr,
)

pytestmark = [pytest.mark.spec("000"), pytest.mark.ac("AC-3")]

COMMIT = "feat(check): add gate\n\nSpec: 001"


def spec(status: str = "approved") -> SpecInfo:
    return SpecInfo(
        "001",
        Path("specs/active/001-demo/spec.md"),
        status,
        frozenset({"AC-1", "AC-2"}),
    )


def ac_report() -> dict[str, dict[str, list[str]]]:
    return {
        "001": {
            "AC-1": ["tests/unit/test_demo.py::test_one"],
            "AC-2": ["tests/unit/test_demo.py::test_two"],
        }
    }


def pr_errors(changed: list[str] | None = None) -> list[str]:
    return validate_pr(
        parse_branch("feat/001-demo"),
        parse_title("feat(check): add gate [001]"),
        spec(),
        ac_report(),
        [COMMIT],
        changed if changed is not None else ["src/strictr/demo.py"],
    )


def test_parse_branch_accepts_spec_branch() -> None:
    branch = parse_branch("feat/001-check-command")
    assert branch.type == "feat"
    assert branch.spec_id == "001"
    assert branch.slug == "check-command"
    assert branch.exempt is False


def test_parse_branch_requires_id_for_feature() -> None:
    with pytest.raises(TraceabilityError, match="requires a three-digit spec ID"):
        parse_branch("feat/check-command")


def test_parse_branch_allows_chore_without_id() -> None:
    branch = parse_branch("chore/update-dependencies")
    assert branch.type == "chore"
    assert branch.spec_id is None


def test_parse_branch_bot_is_exempt() -> None:
    branch = parse_branch("dependabot/pip/ruff-0.11")
    assert branch.exempt is True


@pytest.mark.parametrize(
    "name",
    [
        "feature/001-demo",
        "feat/001-Demo",
        "feat/001--demo",
        "feat/001-demo-",
        "feat/001_demo",
    ],
)
def test_parse_branch_rejects_malformed(name: str) -> None:
    with pytest.raises(TraceabilityError):
        parse_branch(name)


def test_parse_title_accepts_spec_id() -> None:
    title = parse_title("feat(check): add gate [001]")
    assert title.type == "feat"
    assert title.scope == "check"
    assert title.summary == "add gate"
    assert title.spec_id == "001"


def test_parse_title_allows_optional_id() -> None:
    title = parse_title("chore: update dependencies")
    assert title.spec_id is None
    assert title.summary == "update dependencies"


def test_parse_title_rejects_malformed() -> None:
    with pytest.raises(TraceabilityError):
        parse_title("updated some things")


def test_parse_front_matter() -> None:
    text = '---\nid: "001"\nstatus: approved\n---\n\nbody\n'
    assert parse_front_matter(text) == {"id": "001", "status": "approved"}


def test_parse_front_matter_absent() -> None:
    assert parse_front_matter("# Spec\n") == {}


def test_parse_front_matter_handles_utf8_bom() -> None:
    text = '\ufeff---\nid: "001"\nstatus: approved\n---\n'
    assert parse_front_matter(text) == {"id": "001", "status": "approved"}


def test_extract_ac_ids_only_from_acceptance_section() -> None:
    text = (
        "# Spec\n\n"
        "## Acceptance criteria\n\n"
        "- **AC-1:** first\n"
        "- **AC-2:** second\n\n"
        "## Revision log\n\n"
        "AC-9 was mentioned here.\n"
    )
    assert extract_ac_ids(text) == frozenset({"AC-1", "AC-2"})


def test_load_spec_reads_status_and_acs(tmp_path: Path) -> None:
    path = tmp_path / "specs" / "active" / "001-demo" / "spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        '---\nid: "001"\nstatus: in-progress\n---\n\n## Acceptance criteria\n\n- **AC-1:** first\n',
        encoding="utf-8",
    )

    loaded = load_spec("001", tmp_path)
    assert loaded is not None
    assert loaded.status == "in-progress"
    assert loaded.ac_ids == frozenset({"AC-1"})


def test_load_spec_missing_returns_none(tmp_path: Path) -> None:
    assert load_spec("001", tmp_path) is None


def test_load_spec_without_acs_fails(tmp_path: Path) -> None:
    path = tmp_path / "specs" / "active" / "001-demo" / "spec.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nstatus: approved\n---\n\n# Spec\n", encoding="utf-8")

    with pytest.raises(TraceabilityError, match="no acceptance criteria"):
        load_spec("001", tmp_path)


def test_load_ac_report_missing_returns_empty(tmp_path: Path) -> None:
    assert load_ac_report(tmp_path / "missing.json") == {}


def test_load_ac_report_reads_spec_scoped_json(tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    path.write_text('{"001": {"AC-1": ["test_one"]}}', encoding="utf-8")
    assert load_ac_report(path) == {"001": {"AC-1": ["test_one"]}}


def test_code_change_detection() -> None:
    assert code_change(["docs/testing.md", "specs/active/001-demo/spec.md"]) is False
    assert code_change(["src/strictr/demo.py"]) is True
    assert code_change(["README.md"]) is False


def test_validate_commits_accepts_conventional_with_trailer() -> None:
    assert validate_commits([COMMIT], "001") == []


def test_validate_commits_rejects_bad_subject() -> None:
    errors = validate_commits(["updated stuff\n\nSpec: 001"], "001")
    assert any("not Conventional Commits" in error for error in errors)


def test_validate_commits_rejects_missing_trailer() -> None:
    errors = validate_commits(["feat(check): add gate"], "001")
    assert any("missing 'Spec: 001'" in error for error in errors)


def test_validate_commits_skips_fixup() -> None:
    assert validate_commits([COMMIT, "fixup! feat(check): add gate"], "001") == []


def test_validate_pr_happy_path() -> None:
    assert pr_errors() == []


def test_validate_pr_ignores_other_spec_ac_tags() -> None:
    report = ac_report()
    report["000"] = {"AC-5": ["tests/unit/test_other.py::test_five"]}
    errors = validate_pr(
        parse_branch("feat/001-demo"),
        parse_title("feat(check): add gate [001]"),
        spec(),
        report,
        [COMMIT],
        ["src/strictr/demo.py"],
    )
    assert errors == []


def test_validate_pr_rejects_title_mismatch() -> None:
    errors = validate_pr(
        parse_branch("feat/001-demo"),
        parse_title("feat(check): add gate [002]"),
        spec(),
        ac_report(),
        [COMMIT],
        ["src/strictr/demo.py"],
    )
    assert any("does not match branch spec ID" in error for error in errors)


def test_validate_pr_rejects_draft_spec_with_code() -> None:
    errors = validate_pr(
        parse_branch("feat/001-demo"),
        parse_title("feat(check): add gate [001]"),
        spec("draft"),
        ac_report(),
        [COMMIT],
        ["src/strictr/demo.py"],
    )
    assert any("not allowed for a code change" in error for error in errors)


def test_validate_pr_allows_draft_spec_for_docs_only() -> None:
    errors = pr_errors(["specs/active/001-demo/spec.md"])
    assert errors == []


def test_validate_pr_rejects_missing_ac_test() -> None:
    errors = validate_pr(
        parse_branch("feat/001-demo"),
        parse_title("feat(check): add gate [001]"),
        spec(),
        {"001": {"AC-1": ["tests/unit/test_demo.py::test_one"]}},
        [COMMIT],
        ["src/strictr/demo.py"],
    )
    assert any("AC-2 has no tagged test" in error for error in errors)


def test_validate_pr_rejects_orphan_ac() -> None:
    report = ac_report()
    report["001"]["AC-9"] = ["tests/unit/test_demo.py::test_nine"]
    errors = validate_pr(
        parse_branch("feat/001-demo"),
        parse_title("feat(check): add gate [001]"),
        spec(),
        report,
        [COMMIT],
        ["src/strictr/demo.py"],
    )
    assert any("AC-9 does not exist in the spec" in error for error in errors)


def test_validate_pr_rejects_missing_spec() -> None:
    errors = validate_pr(
        parse_branch("feat/001-demo"),
        parse_title("feat(check): add gate [001]"),
        None,
        ac_report(),
        [COMMIT],
        ["src/strictr/demo.py"],
    )
    assert any("no spec found" in error for error in errors)


def test_validate_pr_rejects_chore_with_title_spec_id() -> None:
    errors = validate_pr(
        BranchInfo("chore/update-deps", "chore", None, "update-deps"),
        parse_title("chore: update dependencies [001]"),
        None,
        {},
        ["chore: update dependencies"],
        ["pyproject.toml"],
    )
    assert any("title has a spec ID" in error for error in errors)
