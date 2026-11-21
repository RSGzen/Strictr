from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

from strictr.core.errors import ToolNotFoundError, ToolTimeoutError
from strictr.tools.runner import SubprocessRunner

pytestmark = pytest.mark.spec("003")

MISSING_TOOL = "strictr-no-such-tool-3f9a"


@pytest.fixture
def runner() -> SubprocessRunner:
    return SubprocessRunner()


def python(code: str, *args: str) -> list[str]:
    return [sys.executable, "-c", code, *args]


@pytest.mark.ac("AC-13")
def test_run_captures_output_and_returncode(runner: SubprocessRunner, tmp_path: Path) -> None:
    command = python("import sys; sys.stdout.write('out'); sys.stderr.write('err'); sys.exit(3)")

    result = runner.run(command, cwd=tmp_path, timeout=30)

    assert result.command == tuple(command)
    assert result.returncode == 3
    assert result.stdout == "out"
    assert result.stderr == "err"
    assert isinstance(result.duration_ms, int)


@pytest.mark.ac("AC-13")
def test_run_uses_requested_working_directory(runner: SubprocessRunner, tmp_path: Path) -> None:
    result = runner.run(python("import os; print(os.getcwd())"), cwd=tmp_path, timeout=30)

    assert Path(result.stdout.strip()).resolve() == tmp_path.resolve()


@pytest.mark.ac("AC-13")
def test_run_passes_arguments_without_a_shell(runner: SubprocessRunner, tmp_path: Path) -> None:
    argument = "a b && echo injected"

    result = runner.run(
        python("import sys; print(sys.argv[1])", argument), cwd=tmp_path, timeout=30
    )

    assert result.stdout.strip() == argument


@pytest.mark.ac("AC-13")
def test_run_replaces_invalid_utf8(runner: SubprocessRunner, tmp_path: Path) -> None:
    result = runner.run(
        python("import sys; sys.stdout.buffer.write(b'caf\\xff')"),
        cwd=tmp_path,
        timeout=30,
    )

    assert result.stdout == "caf\ufffd"


@pytest.mark.ac("AC-13")
def test_missing_executable_raises_tool_not_found(runner: SubprocessRunner, tmp_path: Path) -> None:
    with pytest.raises(ToolNotFoundError):
        runner.run([MISSING_TOOL], cwd=tmp_path, timeout=5)


@pytest.mark.ac("AC-13")
def test_timeout_raises_without_waiting_for_the_tool(
    runner: SubprocessRunner, tmp_path: Path
) -> None:
    started = time.perf_counter()

    with pytest.raises(ToolTimeoutError):
        runner.run(
            python("import threading; threading.Event().wait(10)"),
            cwd=tmp_path,
            timeout=0.5,
        )

    assert time.perf_counter() - started < 5


@pytest.mark.ac("AC-13")
def test_which_returns_none_for_missing_executable(runner: SubprocessRunner) -> None:
    assert runner.which(MISSING_TOOL) is None


@pytest.mark.ac("AC-13")
def test_which_finds_executable_on_path(
    runner: SubprocessRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name = "strictr-fake-tool"
    executable = tmp_path / (f"{name}.exe" if os.name == "nt" else name)
    executable.write_text("", encoding="utf-8")
    if os.name == "nt":
        monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    else:
        executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    found = runner.which(name)

    assert found is not None
    assert Path(found) == executable
