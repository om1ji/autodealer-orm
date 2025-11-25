"""SQLAlchemy ORM mapping for the existing BANK table."""

from __future__ import annotations

from sqlalchemy import Table

from autodealer import Base, get_engine


class Bank(Base):
    """
    ORM model bound to the legacy ``BANK`` Firebird table.

    Columns are reflected automatically, so once metadata is loaded you can
    use ``Bank`` instances just like a regular declarative model.
    """

    __tablename__ = "BANK"
    __table__ = Table(__tablename__, Base.metadata, autoload_with=get_engine())
