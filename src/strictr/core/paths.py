"""Root-relative POSIX path display helpers."""

from __future__ import annotations

import os
from pathlib import Path


def relative_posix(path: Path, root: Path) -> str:
    """Return *path* relative to *root* with `/` separators.

    The result is for display, so symlinks are never resolved. This is not a
    confinement check; discovery owns that decision.
    """
    return Path(os.path.relpath(path, root)).as_posix()
