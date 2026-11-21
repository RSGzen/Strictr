"""Project root resolution, target confinement, and Python file discovery."""

from __future__ import annotations

from collections.abc import Sequence

from .models import DiscoveryResult


def discover(targets: Sequence[str] = ()) -> DiscoveryResult:
    """Resolve the project root and discover Python files under *targets*.

    Targets are CLI strings relative to the current directory. An empty
    sequence means the current directory and is recorded as ``(".",)``.
    Raises `DiscoveryError` for a missing target, an escaping target, more than
    one project root, or when no ``.py`` or ``.pyi`` file is found.
    """
    raise NotImplementedError
