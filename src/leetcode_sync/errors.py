class SyncError(Exception):
    """Base exception for user-facing sync failures."""


class ConfigError(SyncError):
    """Raised when configuration is missing or invalid."""


class AuthError(SyncError):
    """Raised when authentication fails."""


class RateLimitError(SyncError):
    """Raised when a remote API reports rate limiting."""


class RemoteApiError(SyncError):
    """Raised when a remote API returns an unexpected response."""
