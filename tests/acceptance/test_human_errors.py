from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.spec("004")

CLEAN = "def add(a: int, b: int) -> int:\n    return a + b\n"
RUFF_PIN = '[tool.ruff.lint]\nselect = ["E", "F"]\n'


@pytest.mark.ac("AC-4")
def test_human_collection_error_shows_evidence(make_project: Any, run_cli: Any) -> None:
    root = make_project(
        {
            "pyproject.toml": RUFF_PIN,
            "tests/test_missing_import.py": (
                'from definitely_missing_module import thing\n\n__all__ = ["thing"]\n'
            ),
        }
    )

    completed = run_cli(root, "check", "--type-checker", "none")

    assert completed.returncode == 2, completed.stderr
    assert "tier2-pytest" in completed.stdout
    assert "definitely_missing_module" in completed.stdout


@pytest.mark.ac("AC-4")
def test_human_tool_error_shows_meta_error(make_project: Any, run_cli: Any, tmp_path: Path) -> None:
    fake_dir = tmp_path / "fake"
    fake_dir.mkdir()
    (fake_dir / "pyright.py").write_text("import sys\n\nsys.exit(3)\n", encoding="utf-8")
    root = make_project(
        {
            "app.py": CLEAN,
            "pyproject.toml": f"{RUFF_PIN}\n[tool.pyright]\n",
        }
    )

    completed = run_cli(
        root,
        "check",
        env={**os.environ, "PYTHONPATH": str(fake_dir)},
    )

    assert completed.returncode == 2, completed.stderr
    assert "  tier1-types  error" in completed.stdout
    assert "  tier1-types: pyright is configured but not available" in completed.stdout
