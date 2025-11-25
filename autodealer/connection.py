"""SQLAlchemy bootstrap helpers for the Firebird database."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator, Iterator, Sequence
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

DIRECT_URL_ENV_KEYS: Sequence[str] = (
    "DATABASE_URL",
    "SQLALCHEMY_DATABASE_URL",
    "DB_URL",
)

_config_override: DatabaseConfig | None = None
engine: Engine | None = None


@dataclass(frozen=True)
class DatabaseConfig:
    """Store credentials for constructing a SQLAlchemy URL."""

    database: str | None
    user: str
    password: str
    host: str | None = os.getenv("DB_HOST")
    port: int | None = int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None
    charset: str = os.getenv("DB_CHARSET", "UTF8")
    dsn: str | None = os.getenv("DB_DSN")

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        database = (
            os.getenv("DB_DATABASE")
            or os.getenv("DB_PATH")
            or os.getenv("DB_NAME")
        )
        dsn = os.getenv("DB_DSN")
        if not database and not dsn:
            raise RuntimeError(
                "Database path is missing. Set DB_DATABASE/DB_PATH/DB_NAME "
                "or provide DB_DSN/DATABASE_URL/DB_URL for a full SQLAlchemy URL."
            )
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        if not user or not password:
            raise RuntimeError(
                "Database credentials missing. Set DB_USER and DB_PASSWORD."
            )
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        if not dsn:
            host = host or "localhost"
            port_value = int(port) if port else 3050
        else:
            port_value = int(port) if port else None
        return cls(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port_value,
            dsn=dsn,
        )

    def _database_argument(self) -> str:
        if self.dsn:
            return self.dsn
        if not self.database:
            raise RuntimeError("Database path missing.")
        return self.database

    def to_url(self) -> URL:
        query = {"charset": self.charset} if self.charset else None
        kwargs: dict[str, object] = {
            "username": self.user,
            "password": self.password,
            "database": self._database_argument(),
            "query": query,
        }
        if not self.dsn:
            if self.host:
                kwargs["host"] = self.host
            if self.port:
                kwargs["port"] = self.port
        return URL.create("firebird+firebird", **kwargs)


def _direct_database_url() -> str | None:
    for key in DIRECT_URL_ENV_KEYS:
        value = os.getenv(key)
        if value:
            return value
    return None


def get_connection_url() -> str | URL:
    """Return the SQLAlchemy URL for the Firebird database."""
    if _config_override:
        return _config_override.to_url()
    url = _direct_database_url()
    if url:
        return url
    return DatabaseConfig.from_env().to_url()


def create_db_engine(url: str | URL | None = None) -> Engine:
    """Create a SQLAlchemy engine configured for Firebird."""
    return create_engine(
        url or get_connection_url(),
        echo=False,
        future=True,
    )


SessionLocal = scoped_session(
    sessionmaker(autoflush=False, autocommit=False)
)


def _set_engine(new_engine: Engine) -> Engine:
    global engine
    engine = new_engine
    SessionLocal.remove()
    SessionLocal.configure(bind=new_engine)
    return new_engine


def get_engine(url: str | URL | None = None) -> Engine:
    """
    Lazily create or return the configured SQLAlchemy engine.
    """

    if url is not None:
        return _set_engine(create_db_engine(url))
    if engine is None:
        return _set_engine(create_db_engine())
    return engine


def configure_engine(url: str | URL | None = None) -> Engine:
    """
    Rebuild the SQLAlchemy engine/session factory with new connection details.
    """

    global engine
    if engine is not None:
        engine.dispose()
    return _set_engine(create_db_engine(url))


def configure_database(**kwargs: object) -> Engine:
    """
    Accept raw credentials instead of relying on environment variables.

    Example:
        configure_database(
            database="path/to/AutoDealer.fdb",
            user="SYSDBA",
            password="masterkey",
            host="192.168.88.64",
            port=3050,
            charset="WIN1251",
        )
    """

    global _config_override
    _config_override = DatabaseConfig(**kwargs)
    return configure_engine(_config_override.to_url())


class Base(DeclarativeBase):
    """Declarative base class for ORM models."""

    pass


@contextmanager
def session_scope() -> Iterator[Session]:
    """
    Provide a transactional scope around a series of operations.

    Example:
        with session_scope() as session:
            session.query(...)
    """

    get_engine()
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI-style dependency/helper that yields a session.

    Use this when integrating with frameworks that expect a generator.
    """

    get_engine()
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


__all__ = (
    "Base",
    "SessionLocal",
    "engine",
    "get_connection_url",
    "create_db_engine",
    "get_engine",
    "configure_database",
    "configure_engine",
    "session_scope",
    "get_session",
)
