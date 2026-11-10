"""
Gnani Voice AI Service Exceptions.
"""

class GnaniError(Exception):
    """Base exception for all Gnani service errors."""
    pass

class GnaniConfigurationMissingError(GnaniError):
    """Raised when GNANI_API_KEY or necessary endpoints are not configured."""
    pass

class GnaniAuthError(GnaniError):
    """Raised when Gnani returns 401 Unauthorized."""
    pass

class GnaniRateLimitError(GnaniError):
    """Raised when Gnani returns 429 Rate Limit."""
    pass

class GnaniTimeoutError(GnaniError):
    """Raised when request to Gnani service exceeds timeout limit."""
    pass

class GnaniVoiceNotFoundError(GnaniError):
    """Raised when an requested voice ID is not supported by Gnani."""
    pass

