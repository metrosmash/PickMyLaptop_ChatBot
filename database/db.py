"""Thin, pooled database access layer for the laptop dataset.

Design goals (this is what makes the project "provider agnostic" and not just
"hardcoded to another host"):

1. Settings come from :mod:`database.config` (env -> .env -> Streamlit secrets -> defaults).
2. Connections come from a ``mysql.connector`` connection POOL (5 slots), not one
   connection per browser session. Free-tier hosts cap concurrent connections --
   this is what actually stops you from getting locked out.
3. Every query goes through :func:`run_query`, which implements the agent-friendly
   placeholder-binding rules and returns either a list of row dicts or an
   ``{"error": ...}`` dict (so the LLM tool layer never sees raw driver exceptions).

The rest of the app (Backend.py) should never talk to ``mysql.connector`` directly.
"""
from __future__ import annotations

import threading
import logging 
from typing import Any, Optional

import mysql.connector
from mysql.connector import pooling

from .config import Settings, connect_kwargs, get_settings
from .exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)
logging.basicConfig(format = '%(levelname)s:%(message)s on %(asctime)s', datefmt = '%d/%m/%Y @ %I:%M:%S %p',filename = "database_db.log", level = logging.DEBUG)
logger.info("New session started")

_pool = None
_pool_lock = threading.Lock()


def get_pool(settings: Optional[Settings] = None) -> pooling.MySQLConnectionPool:
    """Lazily create (and then reuse) the module-level connection pool."""
    global _pool
    cfg = settings or get_settings()
    with _pool_lock:
        if _pool is None:
            kwargs = dict(connect_kwargs(cfg))
            _pool = pooling.MySQLConnectionPool(
                pool_size=5,               # free-tier friendly ceiling
                pool_name="pickmylaptop",
                pool_reset_session=True,   # clean up session state between pooled uses
                use_pure=True,             # pure-python implementation (more portable)
                **kwargs,
            )
    return _pool


def reset_pool() -> None:
    """Drop the pool entirely (used after a broken connection to force a fresh one)."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            try:
                _pool.close()
            except Exception:
                pass
            _pool = None


def get_db_connection(settings: Optional[Settings] = None):
    """Checkout a live connection from the pool; raise a friendly error if unavailable."""
    cfg = settings or get_settings()
    try:
        conn = get_pool(cfg).get_connection()
        if conn.is_connected():
            return conn
        try:
            conn.close()
        except Exception:
            pass
        raise DatabaseConnectionError("Could not establish a live database connection.")
    except mysql.connector.Error as error:
        logger.warning("MySQL connection failed", exc_info=error)
        raise DatabaseConnectionError(f"Could not connect to the database ") from error




def release_connection(conn: Any) -> None:
    """Return a connection to the pool (or close it if pool bookkeeping fails)."""
    try:
        get_pool().put_connection(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def health_check(settings: Optional[Settings] = None) -> dict:
    """Liveness probe: run a trivial query and return the server version."""
    conn = get_db_connection(settings)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchall()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
        return {"ok": True, "version": version}
    except mysql.connector.Error as error:
        logger.warning("Database health check failed with", exc_info = error)
        raise DatabaseConnectionError(f"Database health check failed ") from error 
    finally:
        release_connection(conn)


def _bind_params(query: str, state: Optional[dict], values: Any) -> tuple:
    """Turn the agent's loose ``values`` into a proper DB-API parameter tuple.

    The LLM tools produce different shapes (a single scalar, a list of LIKE terms,
    a (min, max) range...). ``state["query_type"]`` tells us which rule applies.
    Keeping this pure means it can be tested without a database connection.
    """
    query_type = (state or {}).get("query_type") or "use_value"

    if query_type == "use_value":
        # One value -> wrap it so `execute()` gets a 1-tuple.
        if isinstance(values, (tuple, list)):
            return tuple(values)
        return () if values is None else (values,)
    if query_type == "use_keyword":
        # Keyword searches repeat the term for every LIKE placeholder.
        if isinstance(values, (tuple, list)):
            return tuple(values)
        return tuple([values] * query.count("%s"))
    if query_type in {"use_range", "specific_range"}:
        # BETWEEN-style range searches (optionally combined with a LIKE above).
        return tuple(values) if values is not None else ()
    return ()


def _execute(conn, query: str, state: Optional[dict], values: Any) -> list:
    """Run one query on a live connection and return rows as dicts."""
    params = _bind_params(query, state, values)
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in rows]


def run_query(query: str, state: Optional[dict] = None, values: Any = None) -> Any:
    """
    Execute a parameterized SQL query.

    - query: SQL string with %s placeholders
    - state: agent state dict (optional) used to decide how values are bound
    - values: None, a single value, or a tuple/list of multiple values
    - returns: list of dict rows, or ``{"error": "..."}`` on failure (after one reconnect attempt)

    Never raises for connection/query failures: a chatbot tool must degrade into a
    readable tool result, not crash the graph.
    """
    try:
        conn = get_db_connection()
    except DatabaseConnectionError as error:
        return {"error": f"Database unavailable: {error}"}

    try:
        return _execute(conn, query, state, values)
    except mysql.connector.Error as error:
        broken = not conn.is_connected()
        release_connection(conn)
        if not broken:
            # Connection is healthy but the query itself failed -> surface the error.
            return {"error": f"MySQL error: {error}"}
        # Connection died mid-query -> drop it and retry once on a fresh one.
        try:
            conn = get_db_connection()
        except DatabaseConnectionError as reconnect_error:
            return {"error": f"Database unavailable: {reconnect_error}"}
        try:
            return _execute(conn, query, state, values)
        except mysql.connector.Error as retry_error:
            release_connection(conn)
            return {"error": f"MySQL error: {retry_error}"}
