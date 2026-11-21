from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "projects"


@pytest.fixture
def copy_fixture(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory that copies a fixture project into *tmp_path*."""

    def copy(name: str, destination: str | None = None) -> Path:
        target = tmp_path / (destination or name)
        shutil.copytree(FIXTURES / name, target)
        return target

    return copy


@pytest.fixture
def make_project(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory that writes a minimal project into *tmp_path*."""

    def build(files: dict[str, str], *, git_marker: bool = False) -> Path:
        root = tmp_path.resolve()
        (root / "pyproject.toml").write_text("", encoding="utf-8")
        if git_marker:
            (root / ".git").mkdir()
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return root

    return build


@pytest.fixture
def run_cli() -> Callable[..., subprocess.CompletedProcess[str]]:
    """Return a runner for `python -m strictr` from a project root."""

    def run(
        root: Path, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            (sys.executable, "-m", "strictr", *args),
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    return run


@pytest.fixture
def run_console() -> Callable[..., subprocess.CompletedProcess[str]]:
    """Return a runner for the installed `strictr` console script."""

    def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            (_console_script(), *args),
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    return run


def _console_script() -> str:
    executable = shutil.which("strictr")
    if executable is not None:
        return executable
    sibling = Path(sys.executable).with_name(
        "strictr.exe" if sys.platform == "win32" else "strictr"
    )
    assert sibling.exists(), "strictr console script is not installed; run `uv sync`"
    return str(sibling)
