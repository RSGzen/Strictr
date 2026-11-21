from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from strictr.core.discovery import discover
from strictr.core.errors import DiscoveryError

pytestmark = pytest.mark.spec("003")


def write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def make_project(root: Path) -> Path:
    write(root / "pyproject.toml")
    return root


def git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
    )


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = make_project(tmp_path.resolve())
    monkeypatch.chdir(root)
    return root


@pytest.mark.ac("AC-5")
def test_no_targets_defaults_to_current_directory(project: Path) -> None:
    source = write(project / "app.py")

    result = discover()

    assert result.root == project
    assert result.targets == (".",)
    assert result.files == (source,)
    assert result.files_skipped == 0
    assert result.warnings == ()


@pytest.mark.ac("AC-5")
def test_nearest_marker_wins_when_walking_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    write(root / "outer.py")
    inner = root / "inner"
    make_project(inner)
    source = write(inner / "app.py")
    monkeypatch.chdir(inner)

    result = discover((".",))

    assert result.root == inner
    assert result.targets == (".",)
    assert result.files == (source,)


@pytest.mark.ac("AC-5")
def test_current_directory_root_wins_for_nested_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    (root / ".git").mkdir()
    inner = root / "inner"
    make_project(inner)
    source = write(inner / "app.py")
    monkeypatch.chdir(root)

    result = discover(("inner",))

    assert result.root == root
    assert result.targets == ("inner",)
    assert result.files == (source,)


@pytest.mark.ac("AC-5")
def test_target_marker_selects_root_when_cwd_has_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    nested = root / "project"
    make_project(nested)
    source = write(nested / "app.py")
    monkeypatch.chdir(root)

    result = discover(("project",))

    assert result.root == nested
    assert result.targets == (".",)
    assert result.files == (source,)


@pytest.mark.ac("AC-5")
def test_file_target_marker_starts_at_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    nested = root / "project"
    make_project(nested)
    source = write(nested / "app.py")
    monkeypatch.chdir(root)

    result = discover(("project/app.py",))

    assert result.root == nested
    assert result.targets == ("app.py",)
    assert result.files == (source,)


@pytest.mark.ac("AC-5")
def test_common_ancestor_selected_when_no_marker_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    first = write(root / "a" / "one.py")
    second = write(root / "b" / "two.py")
    monkeypatch.chdir(root)

    result = discover(("b", "a"))

    assert result.root == root
    assert result.targets == ("a", "b")
    assert result.files == (first, second)


@pytest.mark.ac("AC-5")
def test_multiple_target_roots_is_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path.resolve()
    make_project(root / "one")
    write(root / "one" / "a.py")
    make_project(root / "two")
    write(root / "two" / "b.py")
    monkeypatch.chdir(root)

    with pytest.raises(DiscoveryError, match="multiple project roots"):
        discover(("one", "two"))


@pytest.mark.ac("AC-5")
def test_targets_are_normalized_sorted_and_deduplicated(project: Path) -> None:
    source = write(project / "src" / "a.py")
    first = write(project / "b.py")
    second = write(project / "c.py")

    result = discover((".", "./src", str(project / "src"), "b.py"))

    assert result.targets == (".", "b.py", "src")
    assert result.files == (first, second, source)


@pytest.mark.ac("AC-5")
def test_missing_target_is_error(project: Path) -> None:
    with pytest.raises(DiscoveryError, match="does not exist"):
        discover(("missing.py",))


@pytest.mark.ac("AC-5")
def test_target_outside_project_root_is_error(project: Path) -> None:
    write(project.parent / "outside" / "escape.py")

    with pytest.raises(DiscoveryError, match="outside project root"):
        discover(("../outside",))


@pytest.mark.ac("AC-5")
def test_symlinked_file_outside_root_is_error(project: Path) -> None:
    outside = write(project.parent / "outside.py")
    link = project / "link.py"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is not available")

    with pytest.raises(DiscoveryError, match="outside project root"):
        discover()


@pytest.mark.ac("AC-5")
def test_path_with_spaces_and_unicode(project: Path) -> None:
    directory = project / "path with space-ü"
    source = write(directory / "módulo.py")

    result = discover(("path with space-ü",))

    assert result.root == project
    assert result.targets == ("path with space-ü",)
    assert result.files == (source,)


@pytest.mark.ac("AC-5")
def test_walk_prunes_ignored_directories(project: Path) -> None:
    source = write(project / "src" / "kept.py")
    write(project / ".venv" / "ignored.py")
    write(project / "build" / "ignored.py")
    write(project / "node_modules" / "ignored.py")
    write(project / "__pycache__" / "ignored.py")

    result = discover()

    assert result.files == (source,)
    assert result.files_skipped == 0


@pytest.mark.ac("AC-5")
def test_git_discovery_respects_gitignore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path.resolve()
    git(root, "init", "--quiet")
    write(root / ".gitignore", "ignored.py\n")
    source = write(root / "kept.py")
    write(root / "ignored.py")
    monkeypatch.chdir(root)

    result = discover()

    assert result.files == (source,)
    assert result.files_skipped == 0
    assert result.warnings == ()


@pytest.mark.ac("AC-5")
def test_explicit_file_target_bypasses_gitignore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    git(root, "init", "--quiet")
    write(root / ".gitignore", "ignored.py\n")
    source = write(root / "ignored.py")
    monkeypatch.chdir(root)

    result = discover(("ignored.py",))

    assert result.targets == ("ignored.py",)
    assert result.files == (source,)


@pytest.mark.ac("AC-5")
def test_deleted_tracked_file_is_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path.resolve()
    git(root, "init", "--quiet")
    source = write(root / "kept.py")
    tracked = write(root / "tracked.py")
    git(root, "add", "kept.py", "tracked.py")
    tracked.unlink()
    monkeypatch.chdir(root)

    result = discover()

    assert result.files == (source,)
    assert result.files_skipped == 0


@pytest.mark.ac("AC-5")
def test_git_failure_falls_back_to_walk_with_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    (root / ".git").mkdir()
    source = write(root / "app.py")
    monkeypatch.chdir(root)

    result = discover()

    assert result.files == (source,)
    assert len(result.warnings) == 1
    assert "git" in result.warnings[0].lower()


@pytest.mark.ac("AC-5")
@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="requires POSIX FIFOs")
def test_non_regular_python_candidate_is_skipped(project: Path) -> None:
    source = write(project / "app.py")
    os.mkfifo(project / "pipe.py")

    result = discover()

    assert result.files == (source,)
    assert result.files_skipped == 1


@pytest.mark.ac("AC-6")
def test_empty_project_is_error(project: Path) -> None:
    with pytest.raises(DiscoveryError, match="no Python files found"):
        discover()


@pytest.mark.ac("AC-6")
def test_only_non_python_files_is_error(project: Path) -> None:
    write(project / "README.md", "# empty\n")

    with pytest.raises(DiscoveryError, match="no Python files found"):
        discover()


@pytest.mark.ac("AC-6")
def test_gitignored_only_python_files_is_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    git(root, "init", "--quiet")
    write(root / ".gitignore", "*.py\n")
    write(root / "ignored.py")
    monkeypatch.chdir(root)

    with pytest.raises(DiscoveryError, match="no Python files found"):
        discover()
