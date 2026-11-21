"""Subprocess execution for external verification tools."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from strictr.core.errors import ToolNotFoundError, ToolTimeoutError
from strictr.core.models import ToolResult

# Typeshed exposes CREATE_NEW_PROCESS_GROUP only on Windows; the Windows API
# value is stable and the flag lets taskkill reach the whole process tree.
_CREATE_NEW_PROCESS_GROUP = 0x00000200


class SubprocessRunner:
    """Run tools without a shell and capture their output under a hard timeout."""

    def run(self, command: Sequence[str], *, cwd: Path, timeout: float) -> ToolResult:
        """Run *command* in *cwd* and capture UTF-8 stdout and stderr.

        Raises `ToolNotFoundError` when the executable cannot be started and
        `ToolTimeoutError` after terminating the process tree when *timeout*
        expires.
        """
        started = time.perf_counter()
        try:
            process = subprocess.Popen(
                list(command),
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                errors="replace",
                creationflags=_CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                start_new_session=sys.platform != "win32",
            )
        except FileNotFoundError as error:
            raise ToolNotFoundError(f"tool not found: {command[0]}") from error

        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _terminate_tree(process)
            process.communicate()
            raise ToolTimeoutError(f"tool timed out after {timeout:g} seconds") from None

        return ToolResult(
            command=tuple(command),
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )

    def which(self, name: str) -> str | None:
        """Return the executable path for *name*, or `None` when absent."""
        return shutil.which(name)


def _terminate_tree(process: subprocess.Popen[str]) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(process.pid)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        process.kill()
