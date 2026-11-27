from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.spec("004")

BOTH_CONFIGURED_WARNING = (
    "Both mypy and pyright are configured; using mypy. Pass --type-checker pyright to override."
)
CLEAN_MODULE = "def add(a: int, b: int) -> int:\n    return a + b\n"
TYPE_ERROR_MODULE = 'VALUE: int = "text"\n'
RUFF_CONFIG = '[tool.ruff.lint]\nselect = ["E", "F"]\n'

# Test double only: it proves the subprocess/parser path, not real pyright parity.
FAKE_PYRIGHT = """\
import json
import sys

if "--version" in sys.argv:
    print("pyright 1.1.999")
    raise SystemExit(0)

print(
    json.dumps(
        {
            "generalDiagnostics": [
                {
                    "file": "app.py",
                    "range": {
                        "start": {"line": 0, "character": 4},
                        "end": {"line": 0, "character": 9},
                    },
                    "severity": "error",
                    "message": "str is not assignable to int",
                    "rule": "reportAssignmentType",
                }
            ],
            "summary": {"errorCount": 1},
        }
    )
)
raise SystemExit(1)
"""

UNAVAILABLE_PYRIGHT = """\
from pathlib import Path

Path(__file__).with_name("invoked").write_text("probe", encoding="utf-8")
raise SystemExit(1)
"""


def json_envelope(completed: Any) -> dict[str, Any]:
    assert completed.stdout.endswith("\n"), completed.stderr
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    return document


def tier_by_id(document: dict[str, Any], tier_id: str) -> dict[str, Any]:
    return next(tier for tier in document["tiers"] if tier["id"] == tier_id)


def fake_pyright(tmp_path: Path, source: str) -> tuple[Path, dict[str, str]]:
    """Write a fake `pyright` module and an environment where it wins on import."""
    fake_dir = tmp_path / "fake_pyright"
    fake_dir.mkdir()
    (fake_dir / "pyright.py").write_text(source, encoding="utf-8")
    environment = os.environ.copy()
    # PYTHONPATH precedes site-packages, so the fake shadows any installed pyright.
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(fake_dir), environment.get("PYTHONPATH", "")) if part
    )
    return fake_dir, environment


@pytest.mark.ac("AC-5")
def test_config_selects_mypy(make_project: Any, run_cli: Any) -> None:
    root = make_project(
        {
            "pyproject.toml": f"{RUFF_CONFIG}\n[tool.mypy]\n",
            "app.py": TYPE_ERROR_MODULE,
        }
    )

    completed = run_cli(root, "check", "--json")

    assert completed.returncode == 1, completed.stderr
    document = json_envelope(completed)
    assert document["status"] == "fail"
    types = tier_by_id(document, "tier1-types")
    assert types["status"] == "fail"
    assert types["tool"]["name"] == "mypy"
    assert types["meta"]["checker"] == "mypy"
    assert types["meta"]["selection"] == "config"
    assert types["diagnostics"]
    assert types["diagnostics"][0]["path"] == "app.py"


@pytest.mark.ac("AC-5")
def test_both_configured_selects_mypy_and_warns_once(make_project: Any, run_cli: Any) -> None:
    root = make_project(
        {
            "pyproject.toml": f"{RUFF_CONFIG}\n[tool.mypy]\n\n[tool.pyright]\n",
            "app.py": CLEAN_MODULE,
        }
    )

    completed = run_cli(root, "check", "--json")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    types = tier_by_id(document, "tier1-types")
    assert types["status"] == "pass"
    assert types["tool"]["name"] == "mypy"
    assert types["meta"]["selection"] == "config"
    assert document["warnings"].count(BOTH_CONFIGURED_WARNING) == 1
    assert completed.stderr.count(BOTH_CONFIGURED_WARNING) == 1


@pytest.mark.ac("AC-5")
def test_fake_pyright_runs_through_subprocess(
    make_project: Any, run_cli: Any, tmp_path: Path
) -> None:
    root = make_project(
        {
            "pyproject.toml": f"{RUFF_CONFIG}\n[tool.pyright]\n",
            "app.py": TYPE_ERROR_MODULE,
        }
    )
    _, environment = fake_pyright(tmp_path, FAKE_PYRIGHT)

    completed = run_cli(root, "check", "--json", "--type-checker", "pyright", env=environment)

    assert completed.returncode == 1, completed.stderr
    document = json_envelope(completed)
    assert document["status"] == "fail"
    types = tier_by_id(document, "tier1-types")
    assert types["status"] == "fail"
    assert types["meta"]["selection"] == "explicit"
    assert types["tool"]["name"] == "pyright"
    assert types["tool"]["version"] == "1.1.999"
    diagnostic = types["diagnostics"][0]
    assert diagnostic["source"] == "pyright"
    assert diagnostic["path"] == "app.py"
    assert diagnostic["code"] == "reportAssignmentType"
    assert diagnostic["line"] == 1
    assert diagnostic["column"] == 5
    assert diagnostic["end_line"] == 1
    assert diagnostic["end_column"] == 10
    assert diagnostic["severity"] == "error"


@pytest.mark.ac("AC-5")
def test_configured_checker_unavailable(make_project: Any, run_cli: Any, tmp_path: Path) -> None:
    root = make_project(
        {
            "pyproject.toml": f"{RUFF_CONFIG}\n[tool.pyright]\n",
            "app.py": "VALUE = 1\n",
        }
    )
    fake_dir, environment = fake_pyright(tmp_path, UNAVAILABLE_PYRIGHT)

    completed = run_cli(root, "check", "--json", env=environment)

    # A configured checker that cannot be probed is `error`, and the v1 contract
    # maps an overall `error` status to exit code 2.
    assert completed.returncode == 2, completed.stderr
    document = json_envelope(completed)
    assert document["status"] == "error"
    types = tier_by_id(document, "tier1-types")
    assert types["status"] == "error"
    assert types["skipped_reason"] == "pyright not found"
    assert types["meta"]["selection"] == "config"
    error = types["meta"]["error"]
    assert "configured" in error.lower()
    assert "not available" in error.lower()
    # The sentinel proves the fake on PYTHONPATH ran, not a real installed pyright.
    assert (fake_dir / "invoked").is_file()
