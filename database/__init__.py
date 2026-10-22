"""Public API for the provider-agnostic database package.

Usage:
    from database import get_db_connection, get_settings, health_check, run_query
"""
from .exceptions import DatabaseConnectionError, DatabaseError, ConfigurationError
from .config import Settings, connect_kwargs, get_settings
from .db import get_db_connection, health_check, release_connection, reset_pool, run_query
from .schema import ALLOWED_COLUMNS, ALLOWED_NUMERIC_COLUMNS, ALLOWED_TEXT_COLUMNS, DDL, TABLE, TABLE_QUOTED
from .repository import (
    attribute_range_search,
    search_by_attribute,
    search_by_range,
    search_specific_laptop,
)

__all__ = [
    "Settings",
    "DatabaseError",
    "DatabaseConnectionError",
    "ConfigurationError",
    "get_settings",
    "connect_kwargs",
    "get_db_connection",
    "health_check",
    "run_query",
    "release_connection",
    "reset_pool",
    "TABLE",
    "TABLE_QUOTED",
    "ALLOWED_COLUMNS",
    "ALLOWED_TEXT_COLUMNS",
    "ALLOWED_NUMERIC_COLUMNS",
    "DDL",
    "search_by_attribute",
    "search_specific_laptop",
    "search_by_range",
    "attribute_range_search",
]
