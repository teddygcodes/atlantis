"""
Atlantis Exception Hierarchy
=============================
Specific exception types to replace bare Exception handling.
"""


class AtlantisException(Exception):
    """Base exception for all Atlantis errors."""
    pass


class LLMTimeoutException(AtlantisException):
    """Raised when LLM API call times out after retries."""
    pass


class LLMRateLimitException(AtlantisException):
    """Raised when LLM API rate limit is exceeded after retries."""
    pass


class ConstitutionalViolationException(AtlantisException):
    """Raised when State/City/Town constitution violates parent constitution."""
    pass


class StateFormationException(AtlantisException):
    """Raised when State formation fails after max attempts."""
    pass


class InvalidVoteException(AtlantisException):
    """Raised when vote parsing fails or vote is invalid."""
    pass


class BlueprintValidationException(AtlantisException):
    """Raised when government blueprint validation fails."""
    pass
