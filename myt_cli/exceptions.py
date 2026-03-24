class MytCliError(Exception):
    """Base error for the CLI."""


class ConfigError(MytCliError):
    """Raised when configuration is invalid."""


class ApiRequestError(MytCliError):
    """Raised when the remote API returns a failure."""


class AuthError(ApiRequestError):
    """Raised when authentication fails."""


class NotFoundError(MytCliError):
    """Raised when a resource cannot be found."""


class MultipleMatchesError(MytCliError):
    """Raised when a name matches more than one resource."""


class ConflictError(MytCliError):
    """Raised when an operation would conflict with existing state."""


class TaskTimeoutError(MytCliError):
    """Raised when a task does not finish in time."""


class TaskFailedError(MytCliError):
    """Raised when an async task reports failure."""
