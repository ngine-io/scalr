"""Exception hierarchy of scalr.

Everything raised on purpose by scalr derives from :class:`ScalrError` so that
callers can catch a single base class instead of a bare ``Exception``.
"""


class ScalrError(Exception):
    """Base class for every error raised by scalr."""


class ConfigError(ScalrError):
    """Raised when the scaling configuration is invalid or cannot be read."""


class AdapterNotFoundError(ScalrError, NotImplementedError):
    """Raised when a configured cloud kind or policy source has no adapter.

    Also derives from :class:`NotImplementedError` to stay backwards
    compatible with callers that caught it before a dedicated class existed.
    """


class MetricError(ScalrError):
    """Raised when a policy adapter cannot gather its current metric."""


class CloudError(ScalrError):
    """Raised when a cloud adapter cannot fulfil a scaling request."""
