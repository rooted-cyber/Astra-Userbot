class MediaException(Exception):
    """Base exception for all media-related failures."""

    def __init__(self, message: str, icon: str = "❌"):
        self.message = message
        self.icon = icon
        super().__init__(self.message)


class ContentPrivateException(MediaException):
    """Raised when the content is private."""

    def __init__(self, message: str = "This content is private."):
        super().__init__(message, icon="🚫")


class ContentUnavailableException(MediaException):
    """Raised when the content is unavailable or deleted."""

    def __init__(self, message: str = "This content is no longer available."):
        super().__init__(message, icon="⚠️")


class ContentAgeRestrictedException(MediaException):
    """Raised when the content is age-restricted."""

    def __init__(self, message: str = "This content is age-restricted."):
        super().__init__(message, icon="🔞")


class RateLimitException(MediaException):
    """Raised when the service is rate-limited (429)."""

    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__(message, icon="⏳")


class ServiceUnavailableException(MediaException):
    """Raised when the external service is down."""

    def __init__(self, message: str = "Media service is currently unreachable."):
        super().__init__(message, icon="🌐")


class InvalidURLException(MediaException):
    """Raised when the provided URL is malformed or unsupported."""

    def __init__(self, message: str = "Invalid or unsupported URL."):
        super().__init__(message, icon="🔗")
