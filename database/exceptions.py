"""Error types raised by the database layer.

The agent / UI layer should catch these and turn them into friendly messages or
``{"error": ...}`` tool results -- never let raw driver exceptions escape to the LLM.
"""


class DatabaseError(Exception):
    """Base error for anything database related."""


class ConfigurationError(DatabaseError):
    """Raised when the database configuration is missing or malformed."""


class DatabaseConnectionError(DatabaseError):
    """Raised when the database could not be reached / authenticated."""
