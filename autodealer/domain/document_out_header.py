"""SQLAlchemy 2.0 ORM model for the document_out_header table. AUTO-GENERATED — do not edit manually."""

from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import FetchedValue

from autodealer.connection import Base


class DocumentOutHeader(Base):
    __tablename__ = "document_out_header"

    document_out_header_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_out_tree_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("document_out_tree.document_out_tree_id"), nullable=True
    )
    document_registry_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("document_registry.document_registry_id"), nullable=True
    )
    document_out_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("document_out.document_out_id"), nullable=True
    )
    document_type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("document_type.document_type_id"), nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    prefix: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    suffix: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    date_create: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mark: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    state: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fullnumber: Mapped[Optional[str]] = mapped_column(
        String(21), FetchedValue(), nullable=True
    )
    manager_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("manager.manager_id"), nullable=True
    )
    barcode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contract_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("contract.contract_id"), nullable=True
    )
    abcp_order: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_marking_stage: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    document_marking_reason: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )
