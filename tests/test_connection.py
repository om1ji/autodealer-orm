"""Tests for autodealer.connection — engine and session management."""

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from autodealer.connection import get_connection_url, get_engine, get_session, session_scope


class TestEngine:
    def test_returns_engine_instance(self, db_engine):
        assert isinstance(db_engine, Engine)

    def test_is_cached(self, db_engine):
        """Повторный вызов возвращает тот же объект."""
        assert get_engine() is db_engine

    def test_dialect_is_firebird(self, db_engine):
        assert "firebird" in db_engine.dialect.name.lower()

    def test_connection_url_contains_firebird(self):
        assert "firebird" in str(get_connection_url()).lower()


class TestSessionScope:
    def test_yields_session(self):
        with session_scope() as session:
            assert isinstance(session, Session)

    def test_can_execute_raw_query(self):
        """Простейший SELECT к системной таблице Firebird."""
        with session_scope() as session:
            result = session.execute(text("SELECT 1 FROM RDB$DATABASE")).scalar()
            assert result == 1

    def test_rollback_on_exception(self):
        """Исключение внутри блока пробрасывается, сессия закрывается."""
        with pytest.raises(ValueError, match="test"):
            with session_scope() as session:
                session.execute(text("SELECT 1 FROM RDB$DATABASE"))
                raise ValueError("test")


class TestGetSession:
    def test_yields_session(self):
        gen = get_session()
        session = next(gen)
        assert isinstance(session, Session)
        try:
            next(gen)
        except StopIteration:
            pass
