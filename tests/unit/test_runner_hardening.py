from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

import strictr.tools.runner as runner_module
from strictr.core.errors import ToolTimeoutError
from strictr.tools.runner import SubprocessRunner

pytestmark = pytest.mark.spec("003")


def python(code: str) -> list[str]:
    return [sys.executable, "-c", code]


@pytest.mark.ac("AC-13")
def test_timeout_is_bounded_when_tree_termination_does_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner_module, "_terminate_tree", lambda process: None)
    started = time.perf_counter()

    with pytest.raises(ToolTimeoutError):
        SubprocessRunner().run(python("import time; time.sleep(3)"), cwd=tmp_path, timeout=0.1)

    assert time.perf_counter() - started < 2.5


@pytest.mark.ac("AC-13")
def test_timeout_is_a_tool_error_when_tree_termination_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(process: subprocess.Popen[str]) -> None:
        raise OSError("termination unavailable")

    monkeypatch.setattr(runner_module, "_terminate_tree", fail)
    started = time.perf_counter()

    with pytest.raises(ToolTimeoutError):
        SubprocessRunner().run(python("import time; time.sleep(3)"), cwd=tmp_path, timeout=0.1)

    assert time.perf_counter() - started < 2.5


class _InterruptedProcess:
    pid = 4242
    returncode: int | None = None
    stdout = None
    stderr = None

    def __init__(self) -> None:
        self.killed = False
        self.waited = False

    def communicate(self, timeout: float | None = None) -> tuple[str, str]:
        del timeout
        raise KeyboardInterrupt

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        del timeout
        self.waited = True
        return 0


@pytest.mark.ac("AC-13")
def test_keyboard_interrupt_terminates_the_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    process = _InterruptedProcess()
    terminated: list[Any] = []

    def record(target: Any) -> None:
        terminated.append(target)

    def fake_popen(*args: Any, **kwargs: Any) -> _InterruptedProcess:
        del args, kwargs
        return process

    monkeypatch.setattr(runner_module, "_terminate_tree", record)
    monkeypatch.setattr(runner_module.subprocess, "Popen", fake_popen)

    with pytest.raises(KeyboardInterrupt):
        SubprocessRunner().run(python("pass"), cwd=tmp_path, timeout=30)

    assert terminated == [process]
    assert process.killed
    assert process.waited
