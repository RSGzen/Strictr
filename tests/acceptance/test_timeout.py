from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any

import pytest

pytestmark = pytest.mark.spec("003")


def json_envelope(completed: Any) -> dict[str, Any]:
    assert completed.stdout.endswith("\n"), completed.stderr
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    return document


def tier_by_id(document: dict[str, Any], tier_id: str) -> dict[str, Any]:
    return next(tier for tier in document["tiers"] if tier["id"] == tier_id)


def process_is_running(pid: int) -> bool:
    if sys.platform == "win32":
        completed = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        return str(pid) in completed.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def wait_until_gone(pid: int, limit: float = 5.0) -> bool:
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        if not process_is_running(pid):
            return True
        time.sleep(0.05)
    return False


@pytest.mark.ac("AC-7")
def test_tier0_budget_exceeded_is_an_error(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("clean")

    completed = run_cli(root, "check", "--json", "--timeout", "0.000001")

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    tier0 = tier_by_id(document, "tier0")
    assert tier0["status"] == "error"
    assert tier0["skipped_reason"] == "tool timeout"
    for tier in document["tiers"][1:]:
        assert tier["status"] == "skipped"
        assert tier["skipped_reason"] == "earlier_tier_failed"


@pytest.mark.ac("AC-13")
def test_hung_pytest_is_terminated_with_its_process_tree(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("timeout")

    started = time.monotonic()
    completed = run_cli(root, "check", "--json", "--type-checker", "none", "--timeout", "5")
    elapsed = time.monotonic() - started

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    pytest_tier = tier_by_id(document, "tier2-pytest")
    assert pytest_tier["status"] == "error"
    assert pytest_tier["skipped_reason"] == "tool timeout"
    assert elapsed < 45, f"timeout took {elapsed:.1f}s"

    pid_file = root / "tests" / "child.pid"
    assert pid_file.is_file(), completed.stderr
    child_pid = int(pid_file.read_text(encoding="utf-8"))
    assert wait_until_gone(child_pid), f"pytest child process {child_pid} survived the timeout"
