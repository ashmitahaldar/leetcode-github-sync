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


class ApiResponseError(RemoteApiError):
    """Raised when a remote API returns a non-success HTTP response."""

    def __init__(self, message: str, status: int, detail: str = ""):
        super().__init__(message)
        self.status = status
        self.detail = detail
