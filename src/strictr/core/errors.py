"""Exception hierarchy for expected Strictr failures."""

from __future__ import annotations


class StrictrError(Exception):
    """Base class for failures the CLI can report as a verification result."""


class DiscoveryError(StrictrError):
    """The project root or the target set cannot be resolved safely."""


class ConfigError(StrictrError):
    """The project configuration cannot be interpreted."""


class ToolError(StrictrError):
    """A tool could not produce usable output."""


class ToolNotFoundError(ToolError):
    """The requested executable is not available."""


class ToolTimeoutError(ToolError):
    """The tool exceeded its timeout and was terminated."""


class InvalidToolOutput(ToolError):
    """The tool returned output that does not match its expected format."""
