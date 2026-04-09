"""SQLAlchemy 2.0 ORM model for the service_complex_work_item table. AUTO-GENERATED — do not edit manually."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from autodealer.connection import Base


class ServiceComplexWorkItem(Base):
    "Many-to-many relationship between Tree and Complex_Work objects"
    
    __tablename__ = "service_complex_work_item"

    service_complex_work_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_complex_work_tree_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("service_complex_work_tree.service_complex_work_tree_id"), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rmi_car_select: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
