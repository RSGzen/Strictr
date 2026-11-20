"""Repository traceability policy checks.

Core functions are pure so they can be unit-tested without git or GitHub. The
CLI entry point collects git data and environment values, then calls
``validate_pr``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

SPEC_REQUIRED_TYPES = frozenset({"feat", "fix", "refactor", "test", "perf"})
TRUNK_BRANCHES = frozenset({"main", "master"})
BOT_PREFIXES = ("dependabot/", "renovate/")
NON_CODE_PREFIXES = ("specs/", "docs/", ".github/", ".githooks/", "internal-docs/")
NON_CODE_FILES = frozenset(
    {
        "AGENTS.md",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        ".gitattributes",
        ".gitignore",
    }
)
VALID_STATUSES = frozenset({"draft", "approved", "in-progress", "done", "superseded"})
CODE_STATUSES = frozenset({"approved", "in-progress"})
SKIP_SUBJECT_PREFIXES = ("Merge ", "fixup! ", "squash! ", "WIP", "wip")

BRANCH_RE = re.compile(
    r"^(?P<type>feat|fix|refactor|test|perf|docs|ci|chore)/"
    r"(?:(?P<id>\d{3})-)?(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$"
)
TITLE_RE = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\((?P<scope>[a-z0-9-]+)\))?(?P<breaking>!)?: (?P<summary>.+)$"
)
TITLE_ID_RE = re.compile(r"^(?P<summary>.+?) \[(?P<id>\d{3})\]$")
SUBJECT_RE = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\((?P<scope>[a-z0-9-]+)\))?(?P<breaking>!)?: (?P<summary>.+)$"
)
AC_RE = re.compile(r"\bAC-\d+\b")
SPEC_TRAILER_RE = re.compile(r"^Spec:\s*(?P<id>\d{3})\s*$", re.MULTILINE)


class TraceabilityError(ValueError):
    """Raised when policy inputs cannot be parsed."""


@dataclass(frozen=True)
class BranchInfo:
    raw: str
    type: str
    spec_id: str | None
    slug: str
    exempt: bool = False


@dataclass(frozen=True)
class TitleInfo:
    raw: str
    type: str
    scope: str | None
    summary: str
    spec_id: str | None


@dataclass(frozen=True)
class SpecInfo:
    spec_id: str
    path: Path
    status: str
    ac_ids: frozenset[str]


def parse_branch(name: str) -> BranchInfo:
    """Parse and validate a branch name."""
    if name in TRUNK_BRANCHES:
        return BranchInfo(name, "trunk", None, name, exempt=True)
    if name.startswith(BOT_PREFIXES):
        return BranchInfo(name, "bot", None, name, exempt=True)

    match = BRANCH_RE.fullmatch(name)
    if match is None:
        raise TraceabilityError(
            f"branch '{name}' must match <type>/<NNN>-<slug> "
            "(lowercase, hyphens only, no consecutive hyphens)"
        )

    branch_type = match.group("type")
    slug = match.group("slug")
    if branch_type is None or slug is None:
        raise TraceabilityError(f"branch '{name}' is malformed")

    spec_id = match.group("id")
    if branch_type in SPEC_REQUIRED_TYPES and spec_id is None:
        raise TraceabilityError(
            f"branch '{name}' requires a three-digit spec ID, "
            f"for example '{branch_type}/001-example'"
        )

    return BranchInfo(name, branch_type, spec_id, slug)


def parse_title(title: str) -> TitleInfo:
    """Parse and validate a Conventional Commits PR title."""
    raw = title.strip()
    match = TITLE_RE.fullmatch(raw)
    if match is None:
        raise TraceabilityError(
            "PR title must follow Conventional Commits, for example 'feat(scope): summary [001]'"
        )

    title_type = match.group("type")
    summary = match.group("summary")
    if title_type is None or summary is None:
        raise TraceabilityError("PR title is malformed")

    spec_id: str | None = None
    id_match = TITLE_ID_RE.fullmatch(summary)
    if id_match is not None:
        summary = id_match.group("summary") or ""
        spec_id = id_match.group("id")

    return TitleInfo(raw, title_type, match.group("scope"), summary.strip(), spec_id)


def parse_front_matter(text: str) -> dict[str, str]:
    """Parse a flat YAML front matter block without a YAML dependency."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return result
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            continue
        result[key.strip()] = value.strip().strip("\"'")
    return result


def extract_ac_ids(text: str) -> frozenset[str]:
    """Extract AC IDs from the 'Acceptance criteria' section only."""
    in_section = False
    ids: set[str] = set()
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = line.strip().lower() == "## acceptance criteria"
            continue
        if in_section:
            ids.update(AC_RE.findall(line))
    return frozenset(ids)


def load_spec(spec_id: str, root: Path) -> SpecInfo | None:
    """Find and parse a spec by ID in active or archive."""
    matches = sorted(root.glob(f"specs/active/{spec_id}-*/spec.md"))
    matches.extend(sorted(root.glob(f"specs/archive/{spec_id}-*/spec.md")))
    if not matches:
        return None
    if len(matches) > 1:
        raise TraceabilityError(f"multiple specs found for {spec_id}: {matches}")

    path = matches[0]
    text = path.read_text(encoding="utf-8-sig")
    status = parse_front_matter(text).get("status")
    if not status:
        raise TraceabilityError(f"{path} is missing a 'status' field")
    if status not in VALID_STATUSES:
        raise TraceabilityError(f"{path} has invalid status '{status}'")

    ac_ids = extract_ac_ids(text)
    if not ac_ids:
        raise TraceabilityError(f"{path} has no acceptance criteria")

    return SpecInfo(spec_id, path, status, ac_ids)


def load_ac_report(path: Path) -> dict[str, dict[str, list[str]]]:
    """Load the spec-scoped pytest AC collection report."""
    if not path.is_file():
        return {}
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise TraceabilityError(f"invalid AC report: {path}") from exc

    if not isinstance(raw, dict):
        raise TraceabilityError(f"AC report must be an object: {path}")

    report: dict[str, dict[str, list[str]]] = {}
    for spec_id, acs in raw.items():
        if not isinstance(spec_id, str) or not isinstance(acs, dict):
            raise TraceabilityError(f"AC report has an invalid spec entry: {spec_id!r}")
        spec_report: dict[str, list[str]] = {}
        for ac_id, tests in acs.items():
            if not isinstance(ac_id, str) or not isinstance(tests, list):
                raise TraceabilityError(f"AC report has an invalid AC entry: {ac_id!r}")
            spec_report[ac_id] = [str(item) for item in tests]
        report[spec_id] = spec_report
    return report


def code_change(changed_files: Sequence[str]) -> bool:
    """Return True when the change includes anything other than docs/specs."""
    for path in changed_files:
        normalised = path.replace("\\", "/").removeprefix("./")
        if normalised in NON_CODE_FILES:
            continue
        if normalised.startswith(NON_CODE_PREFIXES):
            continue
        return True
    return False


def validate_commits(messages: Sequence[str], spec_id: str) -> list[str]:
    """Validate commit subjects and spec trailers."""
    errors: list[str] = []
    checked = 0
    for raw in messages:
        message = raw.strip()
        if not message:
            continue
        subject = message.splitlines()[0].strip()
        if subject.startswith(SKIP_SUBJECT_PREFIXES):
            continue

        checked += 1
        if SUBJECT_RE.fullmatch(subject) is None:
            errors.append(f"commit subject is not Conventional Commits: {subject!r}")

        trailer_ids = SPEC_TRAILER_RE.findall(message)
        if spec_id not in trailer_ids:
            errors.append(f"commit is missing 'Spec: {spec_id}': {subject!r}")

    if checked == 0:
        errors.append("no non-fixup commits found to validate")
    return errors


def validate_ac_coverage(spec: SpecInfo, report: dict[str, dict[str, list[str]]]) -> list[str]:
    """Check that every AC has a tagged test and no tags are orphaned."""
    spec_report = report.get(spec.spec_id, {})
    errors: list[str] = []
    for ac_id in sorted(spec.ac_ids):
        if not spec_report.get(ac_id):
            errors.append(f"{ac_id} has no tagged test in build/ac-tests.json")
    for ac_id in sorted(spec_report):
        if ac_id not in spec.ac_ids:
            errors.append(f"test tag {ac_id} does not exist in the spec")
    return errors


def validate_pr(
    branch: BranchInfo,
    title: TitleInfo,
    spec: SpecInfo | None,
    ac_report: dict[str, dict[str, list[str]]],
    commit_messages: Sequence[str],
    changed_files: Sequence[str],
) -> list[str]:
    """Validate a pull request against the traceability policy."""
    if branch.exempt:
        return []

    errors: list[str] = []
    if title.type != branch.type:
        errors.append(f"PR title type '{title.type}' does not match branch type '{branch.type}'")

    if branch.spec_id is None:
        if title.spec_id is not None:
            errors.append("PR title has a spec ID but the branch does not")
        return errors

    if title.spec_id != branch.spec_id:
        errors.append(
            f"PR title spec ID '{title.spec_id}' does not match branch spec ID '{branch.spec_id}'"
        )

    if spec is None:
        errors.append(f"no spec found for {branch.spec_id}")
        return errors

    if code_change(changed_files):
        if spec.status not in CODE_STATUSES:
            errors.append(
                f"spec status '{spec.status}' is not allowed for a code change; "
                "expected 'approved' or 'in-progress'"
            )
    elif spec.status not in {"draft", "approved", "in-progress", "done"}:
        errors.append(f"spec status '{spec.status}' is not allowed for a docs change")

    errors.extend(validate_commits(commit_messages, branch.spec_id))
    errors.extend(validate_ac_coverage(spec, ac_report))
    return errors


def collect_commits(root: Path, base_ref: str) -> list[str]:
    """Read commit messages for the current branch."""
    result = subprocess.run(
        ["git", "log", f"origin/{base_ref}..HEAD", "--format=%B%x00"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [part.strip() for part in result.stdout.split("\x00") if part.strip()]


def collect_changed_files(root: Path, base_ref: str) -> list[str]:
    """Read files changed relative to the merge base."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    """CLI entry point used by CI."""
    head_ref = os.environ.get("HEAD_REF", "").strip()
    pr_title = os.environ.get("PR_TITLE", "").strip()
    base_ref = os.environ.get("BASE_REF", "main").strip() or "main"

    if not head_ref or not pr_title:
        print("traceability: HEAD_REF and PR_TITLE are required", file=sys.stderr)
        return 1

    root = Path.cwd()
    try:
        branch = parse_branch(head_ref)
        if branch.exempt:
            print(f"traceability: exempt branch {head_ref}")
            return 0

        title = parse_title(pr_title)
        spec = load_spec(branch.spec_id, root) if branch.spec_id is not None else None
        report = load_ac_report(root / "build" / "ac-tests.json")
        commits = collect_commits(root, base_ref)
        changed = collect_changed_files(root, base_ref)
        errors = validate_pr(branch, title, spec, report, commits, changed)
    except (TraceabilityError, subprocess.CalledProcessError, OSError) as exc:
        print(f"traceability: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"traceability: {error}", file=sys.stderr)
        return 1

    print("traceability: ok")
    return 0
