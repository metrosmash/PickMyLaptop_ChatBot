"""Database configuration resolution.

The whole point of this module: the project used to hardcode ``db4free.net`` inside
``Backend.py``. When that host went away, the app went with it.

This module makes the database a *configuration* problem instead of a *code* problem:

Resolution order (first non-empty value wins):
    1. ``DATABASE_URL``   -> e.g. ``mysql://user:password@host:25911/dbname``
                             (this is the canonical, provider-agnostic knob -- every
                             managed MySQL provider hands you this exact shape of string)
    2. Individual env vars -> ``DB_host``, ``DB_port``, ``DB_name``, ``DB_username``,
                             ``DB_password``, ``DB_ssl_ca``, ``DB_ssl_verify_cert``,
                             ``DB_timeout``, ``DB_table``
    3. ``.env`` file       -> loaded via ``python-dotenv``
    4. Streamlit secrets   -> ``st.secrets``
    5. Code defaults       -> ``localhost:3306 / metro_laptop / root``

Because both env vars and Streamlit secrets use the same key casing, switching
providers is a one-line change and never requires touching app code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import unquote, urlparse

try:  # python-dotenv is optional at import time; degrade gracefully without it.
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    _DOTENV_LOADED = True
except Exception:  # pragma: no cover - only when python-dotenv is not installed
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:  # type: ignore
        return False
    _DOTENV_LOADED = False

from .exceptions import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# The Aiven Project CA certificate that ships with this repo.
DEFAULT_CA_PATH = PROJECT_ROOT / "database" / "certs" / "ca.pem"


def _resolve_ssl_ca(path: Optional[str]) -> Optional[str]:
    """Resolve a CA cert path relative to the project root (e.g. database/certs/ca.pem)."""
    if not path:
        return None
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return str(candidate)


@dataclass(frozen=True)
class Settings:
    """Immutable database connection settings."""

    host: str = "localhost"
    port: int = 3306
    database: str = "metro_laptop"
    user: str = "root"
    password: str = ""
    ssl_ca: Optional[str] = None
    ssl_verify_cert: bool = True
    timeout: int = 30
    table: str = "laptop_dataset"

    @classmethod
    def from_url(cls, url: str) -> "Settings":
        """Build settings from a MySQL-style URL, e.g. mysql://user:pw@host:25911/dbname."""
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()
        if scheme not in {"mysql", "mysql2", "mariadb"}:
            raise ConfigurationError(
                f"Unsupported DATABASE_URL scheme: {scheme!r}. "
                "This connector speaks MySQL-family URLs, e.g. mysql://user:password@host:3306/dbname"
            )
        return cls(
            host=parsed.hostname or "localhost",
            port=parsed.port or 3306,
            user=unquote(parsed.username or "root"),
            password=unquote(parsed.password or ""),
            database=(parsed.path or "").lstrip("/") or "metro_laptop",
            ssl_ca=os.environ.get("DB_ssl_ca") or None,
            ssl_verify_cert=_as_bool(os.environ.get("DB_ssl_verify_cert"), True),
            timeout=int(os.environ.get("DB_timeout") or 30),
            table=os.environ.get("DB_table") or "laptop_dataset",
        )


_DEFAULTS: Dict[str, Optional[str]] = {
    "DB_host": "localhost",
    "DB_port": "3306",
    "DB_name": "metro_laptop",
    "DB_username": "root",
    "DB_password": "",
    "DB_ssl_ca": None,
    "DB_ssl_verify_cert": "True",
    "DB_timeout": "30",
    "DB_table": "laptop_dataset",
}


def _first(*values: Optional[str]) -> Optional[str]:
    """Return the first value that is not None and not an empty string."""
    for value in values:
        if value is None:
            continue
        value = str(value).strip()
        if value != "":
            return value
    return None


_secrets_cache: Optional[Dict[str, Any]] = None


def _secrets() -> Dict[str, Any]:
    """Read Streamlit secrets lazily (cached); empty dict when unavailable."""
    global _secrets_cache
    if _secrets_cache is None:
        try:
            import streamlit as st

            raw = dict(st.secrets)
            # Build a case-insensitive view so `DB_host` / `db_host` both resolve.
            lowered = {str(k).lower(): v for k, v in raw.items()}
            _secrets_cache = {**raw, **lowered}
        except Exception:
            _secrets_cache = {}
    return _secrets_cache


def _env(*names: str) -> Optional[str]:
    """Look up an env var by any casing variant (Linux env vars are case-sensitive)."""
    lowered_env = {k.lower(): v for k, v in os.environ.items()}
    for name in names:
        if name in os.environ:
            return os.environ[name]
        if name.lower() in lowered_env:
            return lowered_env[name.lower()]
    return None


def _setting(name: str, default: Optional[str] = None) -> Optional[str]:
    """Resolve a single DB setting: env var -> Streamlit secret -> code default."""
    secrets = _secrets()
    for candidate in (name, name.lower(), name.upper()):
        value = secrets.get(candidate)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return _first(_env(name, name.upper(), name.lower()), default)


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def get_settings() -> Settings:
    """Resolve the current database settings from the environment."""
    url = _first(_env("DATABASE_URL"))
    if url:
        return _with_default_ca(Settings.from_url(url))

    return _with_default_ca(Settings(
        host=_setting("DB_host", _DEFAULTS["DB_host"]) or "localhost",
        port=int(_first(_env("DB_port", "DB_PORT"), _setting("DB_port", _DEFAULTS["DB_port"]), _DEFAULTS["DB_port"]) or 3306),
        database=_setting("DB_name", _DEFAULTS["DB_name"]) or "metro_laptop",
        user=_setting("DB_username", _DEFAULTS["DB_username"]) or "root",
        password=_setting("DB_password", _DEFAULTS["DB_password"]) or "",
        ssl_ca=_setting("DB_ssl_ca", _DEFAULTS["DB_ssl_ca"]),
        ssl_verify_cert=_as_bool(_setting("DB_ssl_verify_cert", _DEFAULTS["DB_ssl_verify_cert"]), True),
        timeout=int(_first(_env("DB_timeout", "DB_TIMEOUT"), _setting("DB_timeout", _DEFAULTS["DB_timeout"]), _DEFAULTS["DB_timeout"]) or 30),
        table=_setting("DB_table", _DEFAULTS["DB_table"]) or "laptop_dataset",
    ))


def _with_default_ca(settings: Settings) -> Settings:
    """Use the bundled Aiven Project CA automatically when talking to Aiven.

    Aiven services *always* require TLS, so if the user set only DATABASE_URL (and
    the host is an Aiven host) we can save them a confusing SSL error by picking up
    the CA certificate that already lives in this repo.
    """
    if settings.ssl_ca:
        return settings
    if DEFAULT_CA_PATH.exists() and "aivencloud.com" in (settings.host or "").lower():
        return replace(settings, ssl_ca=str(DEFAULT_CA_PATH))
    return settings


def connect_kwargs(settings: Optional[Settings] = None) -> dict:
    """Assemble the mysql.connector kwargs for whatever provider is configured."""
    cfg = settings or get_settings()
    kwargs: dict = {
        "host": cfg.host,
        "port": cfg.port,
        "user": cfg.user,
        "password": cfg.password,
        "database": cfg.database,
        "connection_timeout": cfg.timeout,
    }
    # Aiven-style providers REQUIRE TLS and give you a CA certificate to verify with.
    # Failing fast here is much friendlier than a cryptic driver error at query time.
    if cfg.ssl_ca:
        ca_path = _resolve_ssl_ca(cfg.ssl_ca)
        if not Path(ca_path).exists():
            raise ConfigurationError(
                f"DB_ssl_ca points to a missing file: {ca_path}. "
                "Download the CA certificate from your provider and save it there."
            )
        kwargs["ssl_ca"] = ca_path
        kwargs["ssl_verify_cert"] = cfg.ssl_verify_cert
    return kwargs
