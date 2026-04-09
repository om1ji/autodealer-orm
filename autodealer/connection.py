"""Подключение к базе данных Firebird и управление сессиями SQLAlchemy.

Типичный сценарий использования::

    from autodealer.connection import configure_database, session_scope

    configure_database(
        host="192.168.88.64",
        port=3050,
        database=r"C:\\path\\to\\AutoDealer.fdb",
        user="SYSDBA",
        password="masterkey",
    )

    with session_scope() as session:
        # работа с сессией
        ...
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator, Iterator, Sequence
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker


def _patch_firebird_render_bind_cast() -> None:
    """Патч бага sqlalchemy-firebird: visit_VARCHAR получает неверные аргументы.

    ``FBCompiler.render_bind_cast`` пытается рендерить явный CAST для каждого
    bind-параметра строкового типа, но при этом передаёт аргументы в
    ``_render_string_type`` в неправильном порядке (сигнатура метода изменилась
    в sqlalchemy-firebird 2.1, но вызывающий код не обновился).

    Решение: отключить рендеринг CAST — Firebird выполняет неявное
    приведение типов самостоятельно, явный CAST не нужен.
    """
    try:
        from sqlalchemy_firebird.base import FBCompiler

        def render_bind_cast(self, type_, dbapi_type, cast_from):  # noqa: ARG001
            return cast_from

        FBCompiler.render_bind_cast = render_bind_cast  # type: ignore[method-assign]
    except (ImportError, AttributeError):
        pass


_patch_firebird_render_bind_cast()

DIRECT_URL_ENV_KEYS: Sequence[str] = (
    "DATABASE_URL",
    "SQLALCHEMY_DATABASE_URL",
    "DB_URL",
)

_config_override: DatabaseConfig | None = None
engine: Engine | None = None
_session_user_id: int | None = None


def set_session_user(user_id: int) -> None:
    """Установить ID пользователя для Firebird-триггеров.

    Триггеры AutoDealer (например, ``ORGANIZATION_AU``) определяют автора
    изменения через таблицу ``USER_CONNECTION``:

    .. code-block:: sql

        SELECT USER_ID FROM USER_CONNECTION
        WHERE USER_CONNECTION_ID = CURRENT_CONNECTION
        INTO :CONNECTED_USER_ID;

    После вызова этой функции каждый ``session_scope()`` будет автоматически
    регистрировать текущее соединение в ``USER_CONNECTION`` перед выполнением
    запросов.

    Args:
        user_id: ID пользователя из таблицы ``users``.

    Example::

        configure_database(host=..., user="SYSDBA", password="masterkey")
        set_session_user(1)   # user_id=1 (SYSDBA) в StOm1.fdb
    """
    global _session_user_id
    _session_user_id = user_id


@dataclass(frozen=True)
class DatabaseConfig:
    """Параметры подключения к базе данных Firebird.

    Используется внутри :func:`configure_database` и :func:`get_connection_url`.
    Можно создать вручную или через :meth:`from_env`.

    Args:
        database: Путь к файлу ``.fdb`` на сервере (Windows-путь).
        user: Имя пользователя Firebird.
        password: Пароль.
        host: Хост сервера. По умолчанию из ``DB_HOST`` или ``"localhost"``.
        port: Порт. По умолчанию из ``DB_PORT`` или ``3050``.
        charset: Кодировка. По умолчанию из ``DB_CHARSET`` или ``"UTF8"``.
        dsn: Полный DSN (альтернатива отдельным параметрам).
    """

    database: str | None
    user: str
    password: str
    host: str | None = os.getenv("DB_HOST")
    port: int | None = int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None
    charset: str = os.getenv("DB_CHARSET", "UTF8")
    dsn: str | None = os.getenv("DB_DSN")

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Создать конфигурацию из переменных окружения.

        Читает ``DB_DATABASE`` (или ``DB_PATH`` / ``DB_NAME``), ``DB_USER``,
        ``DB_PASSWORD``, ``DB_HOST``, ``DB_PORT``, ``DB_CHARSET``, ``DB_DSN``.

        Raises:
            RuntimeError: Если не заданы обязательные переменные.
        """
        database = (
            os.getenv("DB_DATABASE") or os.getenv("DB_PATH") or os.getenv("DB_NAME")
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
    """Вернуть SQLAlchemy URL для подключения к Firebird.

    Приоритет: явный вызов :func:`configure_database` → переменные окружения
    ``DATABASE_URL`` / ``DB_URL`` → ``DatabaseConfig.from_env()``.
    """
    if _config_override:
        return _config_override.to_url()
    url = _direct_database_url()
    if url:
        return url
    return DatabaseConfig.from_env().to_url()


def create_db_engine(url: str | URL | None = None) -> Engine:
    """Создать новый SQLAlchemy :class:`~sqlalchemy.engine.Engine` для Firebird.

    Args:
        url: Готовый URL. Если не передан — используется :func:`get_connection_url`.

    Returns:
        Новый экземпляр Engine (не кешируется).
    """
    return create_engine(
        url or get_connection_url(),
        echo=False,
        future=True,
    )


SessionLocal = scoped_session(sessionmaker(autoflush=False, autocommit=False))


def _set_engine(new_engine: Engine) -> Engine:
    global engine
    engine = new_engine
    SessionLocal.remove()
    SessionLocal.configure(bind=new_engine)
    return new_engine


def get_engine(url: str | URL | None = None) -> Engine:
    """Лениво создать или вернуть кешированный engine.

    Args:
        url: Если передан — пересоздаёт engine с новым URL.

    Returns:
        Текущий активный :class:`~sqlalchemy.engine.Engine`.
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
    """Настроить подключение, передав параметры напрямую (без ``.env``).

    Принимает те же поля, что и :class:`DatabaseConfig`:
    ``database``, ``user``, ``password``, ``host``, ``port``, ``charset``, ``dsn``.

    Args:
        **kwargs: Параметры подключения.

    Returns:
        Пересозданный :class:`~sqlalchemy.engine.Engine`.

    Example::

        configure_database(
            host="192.168.88.64",
            port=3050,
            database=r"C:\\path\\to\\AutoDealer.fdb",
            user="SYSDBA",
            password="masterkey",
            charset="UTF8",
        )
    """

    global _config_override
    _config_override = DatabaseConfig(**kwargs)
    return configure_engine(_config_override.to_url())


class Base(DeclarativeBase):
    """Declarative base class for ORM models."""

    pass


# Attach Manager after both Base and QuerySet are fully defined to avoid circular imports
from autodealer.queryset import Manager  # noqa: E402

Base.objects = Manager()  # type: ignore[attr-defined]


@contextmanager
def session_scope() -> Iterator[Session]:
    """Контекстный менеджер для транзакционной работы с сессией.

    Автоматически вызывает ``commit`` при успехе и ``rollback`` при исключении.

    Yields:
        Активная :class:`~sqlalchemy.orm.Session`.

    Example::

        with session_scope() as session:
            result = session.execute(select(Bank)).scalars().all()
    """

    get_engine()
    session: Session = SessionLocal()
    try:
        if _session_user_id is not None:
            # AutoDealer triggers resolve the current user via USER_CONNECTION:
            #   SELECT USER_ID FROM USER_CONNECTION
            #   WHERE USER_CONNECTION_ID = CURRENT_CONNECTION
            # Register this connection so triggers can find the user.
            session.execute(
                text(
                    "UPDATE OR INSERT INTO user_connection"
                    " (user_connection_id, user_id)"
                    f" VALUES (CURRENT_CONNECTION, {_session_user_id})"
                    " MATCHING (user_connection_id)"
                )
            )
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    """Генератор сессии для интеграции с FastAPI и подобными фреймворками.

    Yields:
        :class:`~sqlalchemy.orm.Session`

    Example::

        # FastAPI
        def get_banks(session: Session = Depends(get_session)):
            return session.execute(select(Bank)).scalars().all()
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
    "set_session_user",
)
