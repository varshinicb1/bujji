class BUJJIError(Exception):
    """Base exception for all BUJJI errors."""


class ConfigurationError(BUJJIError):
    """Raised when configuration is invalid or missing."""


class ProviderError(BUJJIError):
    """Raised when an LLM provider fails."""


class ToolError(BUJJIError):
    """Raised when a tool execution fails."""


class MemoryError(BUJJIError):
    """Raised when memory operations fail."""


class PlanningError(BUJJIError):
    """Raised when task planning fails."""


class RoutingError(BUJJIError):
    """Raised when routing decisions fail."""
