# core/errors.py
"""
Custom error types for the Log-Os interpreter.
"""

class LogosError(Exception):
    """Base class for all Log-Os errors."""
    pass

class LogosSyntaxError(LogosError):
    """Raised for parsing errors."""
    pass

class LogosEvaluationError(LogosError):
    """Raised for errors during code evaluation."""
    pass

class LogosAssertionError(LogosError):
    """Raised for failed assertions."""
    pass