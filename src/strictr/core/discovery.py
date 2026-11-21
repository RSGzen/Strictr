"""Project root resolution, target confinement, and Python file discovery."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from .errors import DiscoveryError
from .models import DiscoveryResult
from .paths import relative_posix

_MARKERS = ("pyproject.toml", ".git")
_PYTHON_SUFFIXES = frozenset({".py", ".pyi"})
_WALK_IGNORES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
        "build",
        "dist",
        "node_modules",
        ".eggs",
    }
)
_GIT_FALLBACK_WARNING = "git file discovery failed; fell back to filesystem walk"

type CandidateDisposition = Literal["include", "skip", "ignore"]


def discover(targets: Sequence[str] = ()) -> DiscoveryResult:
    """Resolve the project root and discover Python files under *targets*.

    Targets are CLI strings relative to the current directory. An empty
    sequence means the current directory and is recorded as ``(".",)``.
    Raises `DiscoveryError` for a missing target, an escaping target, more than
    one project root, or when no ``.py`` or ``.pyi`` file is found.
    """
    cwd = Path.cwd().resolve()
    normalized = _normalize_targets(tuple(targets) or (".",), cwd)
    root = _select_root(cwd, normalized)

    for raw, _, resolved in normalized:
        if not _is_within(resolved, root):
            raise DiscoveryError(f"target outside project root: {raw}")

    recorded_targets = tuple(
        sorted({relative_posix(display, root) for _, display, _ in normalized})
    )
    files: set[Path] = set()
    directories: list[Path] = []
    files_skipped = 0

    for _, display, resolved in normalized:
        if resolved.is_dir():
            directories.append(display)
        elif resolved.is_file():
            if _is_python(display):
                files.add(display)
        elif _is_python(display):
            files_skipped += 1

    warnings: list[str] = []
    if directories:
        directory_targets = tuple(
            sorted({relative_posix(directory, root) for directory in directories})
        )
        if _uses_git(root):
            git_files = _git_files(root, directory_targets)
            if git_files is None:
                warnings.append(_GIT_FALLBACK_WARNING)
                git_files = _walk_files(directories, root)
        else:
            git_files = _walk_files(directories, root)
        found, skipped = git_files
        files.update(found)
        files_skipped += skipped

    ordered = tuple(sorted(files, key=lambda path: relative_posix(path, root)))
    if not ordered:
        raise DiscoveryError("no Python files found")

    return DiscoveryResult(
        root=root,
        targets=recorded_targets,
        files=ordered,
        files_skipped=files_skipped,
        warnings=tuple(warnings),
    )


def _normalize_targets(targets: Sequence[str], cwd: Path) -> list[tuple[str, Path, Path]]:
    normalized: list[tuple[str, Path, Path]] = []
    for raw in targets:
        display = Path(raw)
        if not display.is_absolute():
            display = cwd / display
        try:
            resolved = display.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise DiscoveryError(f"target does not exist: {raw}") from error
        normalized.append((raw, display, resolved))
    return normalized


def _select_root(cwd: Path, targets: Sequence[tuple[str, Path, Path]]) -> Path:
    root = _nearest_marker_root(cwd)
    if root is not None:
        return root

    marker_roots: set[Path] = set()
    for _, _, resolved in targets:
        marker_root = _nearest_marker_root(_root_start(resolved))
        if marker_root is not None:
            marker_roots.add(marker_root)
    if len(marker_roots) > 1:
        roots = ", ".join(sorted(str(path) for path in marker_roots))
        raise DiscoveryError(f"targets span multiple project roots: {roots}")
    if marker_roots:
        return marker_roots.pop()

    starts = [_root_start(resolved) for _, _, resolved in targets]
    try:
        common = Path(os.path.commonpath([str(path) for path in starts]))
    except ValueError as error:
        raise DiscoveryError("targets do not share a common project root") from error
    return common.resolve()


def _root_start(path: Path) -> Path:
    return path if path.is_dir() else path.parent


def _nearest_marker_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if any((candidate / marker).exists() for marker in _MARKERS):
            return candidate
    return None


def _uses_git(root: Path) -> bool:
    if (root / ".git").exists():
        return True
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
        )
    except OSError:
        return False
    return completed.returncode == 0 and completed.stdout.strip() == b"true"


def _git_files(root: Path, directory_targets: Sequence[str]) -> tuple[set[Path], int] | None:
    command = [
        "git",
        "-C",
        str(root),
        "ls-files",
        "-co",
        "--exclude-standard",
        "-z",
        "--",
        *directory_targets,
    ]
    try:
        completed = subprocess.run(command, check=False, capture_output=True)
    except OSError:
        return None
    if completed.returncode != 0:
        return None

    files: set[Path] = set()
    skipped = 0
    for entry in completed.stdout.split(b"\0"):
        if not entry:
            continue
        path = root / Path(os.fsdecode(entry))
        if not _is_python(path):
            continue
        disposition = _candidate_disposition(path, root)
        if disposition == "include":
            files.add(path)
        elif disposition == "skip":
            skipped += 1
    return files, skipped


def _walk_files(directories: Sequence[Path], root: Path) -> tuple[set[Path], int]:
    files: set[Path] = set()
    skipped = 0
    for directory in directories:
        for dirpath, dirnames, filenames in os.walk(directory, topdown=True, followlinks=False):
            dirnames[:] = sorted(name for name in dirnames if not _is_ignored_dir(name))
            for name in sorted(filenames):
                path = Path(dirpath) / name
                if not _is_python(path):
                    continue
                disposition = _candidate_disposition(path, root)
                if disposition == "include":
                    files.add(path)
                elif disposition == "skip":
                    skipped += 1
    return files, skipped


def _candidate_disposition(path: Path, root: Path) -> CandidateDisposition:
    resolved = path.resolve()
    if not _is_within(resolved, root):
        raise DiscoveryError(
            f"symlinked file resolves outside project root: {relative_posix(path, root)}"
        )
    if not path.exists():
        return "ignore"
    if path.is_file():
        return "include"
    return "skip"


def _is_ignored_dir(name: str) -> bool:
    return name in _WALK_IGNORES or name.endswith(".egg-info")


def _is_python(path: Path) -> bool:
    return path.suffix in _PYTHON_SUFFIXES


def _is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents
