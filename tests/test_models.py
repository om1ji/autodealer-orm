"""Tests for ORM model structure and static properties (no DB required)."""

import pytest

from autodealer.domain.bank import Bank
from autodealer.domain.users import Users
from autodealer.connection import Base


class TestBankModel:
    def test_tablename(self):
        assert Bank.__tablename__ == "bank"

    def test_inherits_base(self):
        assert issubclass(Bank, Base)

    def test_has_objects_manager(self):
        from autodealer.queryset import QuerySet
        assert isinstance(Bank.objects, QuerySet)

    def test_expected_columns(self):
        cols = set(Bank.__table__.columns.keys())
        assert {"bank_id", "name", "bik", "korr_account", "address", "notes", "hidden"} <= cols

    def test_primary_key_column(self):
        pk_cols = [c.name for c in Bank.__table__.primary_key.columns]
        assert "bank_id" in pk_cols

    def test_columns_are_explicit(self):
        """Все колонки объявлены явно — нет __table__ = Table(..., autoload_with=...)."""
        # В reflection-моделях колонки не имеют типа (NullType).
        # В сгенерированных — каждая колонка имеет явный тип.
        from sqlalchemy.types import NullType
        for col in Bank.__table__.columns:
            assert not isinstance(col.type, NullType), (
                f"Колонка {col.name} имеет NullType — возможно используется reflection"
            )


class TestUsersModel:
    def test_tablename(self):
        assert Users.__tablename__ == "users"

    def test_inherits_base(self):
        assert issubclass(Users, Base)

    def test_expected_columns(self):
        cols = set(Users.__table__.columns.keys())
        assert {"user_id", "employee_id", "hidden"} <= cols

    def test_primary_key_column(self):
        pk_cols = [c.name for c in Users.__table__.primary_key.columns]
        assert "user_id" in pk_cols


class TestDomainPackage:
    def test_all_models_importable(self):
        """Все модели в domain/__init__.py должны импортироваться без ошибок."""
        import autodealer.domain as domain
        assert hasattr(domain, "Bank")
        assert hasattr(domain, "Users")

    def test_models_count(self):
        """В пакете должно быть значительное количество моделей."""
        import autodealer.domain as domain
        model_classes = [
            v for v in vars(domain).values()
            if isinstance(v, type) and issubclass(v, Base) and v is not Base
        ]
        assert len(model_classes) > 100
