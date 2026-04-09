"""High-level actions: payment creation and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import text

from autodealer.connection import session_scope

_ACCOUNTING_ITEM_CLIENT_PAYMENT = 3  # «Поступление от клиента»


# ---------------------------------------------------------------------------
# Справочники
# ---------------------------------------------------------------------------


@dataclass
class WalletInfo:
    """Кошелёк (касса или счёт) организации."""

    wallet_id: int
    name: str
    organization_id: int


@dataclass
class PaymentTypeInfo:
    """Способ оплаты."""

    payment_type_id: int
    name: str


def get_wallets(organization_id: int) -> list[WalletInfo]:
    """Вернуть все кошельки организации.

    Args:
        organization_id: PK организации.

    Returns:
        Список :class:`WalletInfo`.

    Example::

        wallets = get_wallets(1)
        for w in wallets:
            print(w.wallet_id, w.name)
    """
    with session_scope() as session:
        rows = (
            session.execute(
                text(
                    "SELECT wallet_id, name, organization_id"
                    " FROM wallet WHERE organization_id = :oid"
                    " ORDER BY wallet_id"
                ),
                {"oid": organization_id},
            )
            .mappings()
            .all()
        )
    return [WalletInfo(**dict(r)) for r in rows]


def get_payment_types() -> list[PaymentTypeInfo]:
    """Вернуть все активные способы оплаты.

    Returns:
        Список :class:`PaymentTypeInfo`.

    Example::

        for pt in get_payment_types():
            print(pt.payment_type_id, pt.name)
    """
    with session_scope() as session:
        rows = (
            session.execute(
                text(
                    "SELECT payment_type_id, name FROM payment_type"
                    " WHERE hidden = 0 ORDER BY payment_type_id"
                )
            )
            .mappings()
            .all()
        )
    return [PaymentTypeInfo(**dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Чтение платежей
# ---------------------------------------------------------------------------


@dataclass
class PaymentRecord:
    """Платёж, привязанный к заказ-наряду."""

    payment_id: int
    summa: Decimal
    payment_date: datetime
    payment_type_id: int
    payment_type_name: Optional[str]
    wallet_id: Optional[int]
    wallet_name: Optional[str]
    notes: Optional[str]


def get_payments(document_out_id: int) -> list[PaymentRecord]:
    """Вернуть все платежи по заказ-наряду.

    Args:
        document_out_id: PK заказ-наряда.

    Returns:
        Список :class:`PaymentRecord`. Пустой если платежей нет.

    Example::

        for p in get_payments(42):
            print(p.payment_id, p.summa, p.payment_type_name)
    """
    with session_scope() as session:
        rows = (
            session.execute(
                text(
                    "SELECT p.payment_id, p.summa, p.payment_date,"
                    "       p.payment_type_id, pt.name AS payment_type_name,"
                    "       p.wallet_id, w.name AS wallet_name, p.notes"
                    " FROM payment_out po"
                    " JOIN payment p ON p.payment_id = po.payment_id"
                    " LEFT JOIN payment_type pt ON pt.payment_type_id = p.payment_type_id"
                    " LEFT JOIN wallet w ON w.wallet_id = p.wallet_id"
                    " WHERE po.document_out_id = :doc_id"
                    " ORDER BY p.payment_date"
                ),
                {"doc_id": document_out_id},
            )
            .mappings()
            .all()
        )
    return [PaymentRecord(**dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Создание платежей
# ---------------------------------------------------------------------------


def create_payment(
    *,
    document_out_id: int,
    summa: float,
    wallet_id: int,
    payment_type_id: int,
    payment_date: Optional[datetime] = None,
    notes: Optional[str] = None,
) -> int:
    """Создать документ оплаты для заказ-наряда.

    Атомарно создаёт цепочку:

    1. ``payment``                — запись платежа (сумма, способ, кошелёк).
    2. ``payment_out``            — привязка платежа к ``document_out``.
    3. ``payment_document``       — привязка платежа к ``document_registry``.
    4. ``money_document_detail``  — бухгалтерская проводка
       (``accounting_item_id=3`` «Поступление от клиента»).
    5. ``money_document_payment`` — связь проводки с платежом.
    6. Обновляет ``document_out.date_payment``.

    Args:
        document_out_id: PK заказ-наряда (из :func:`~autodealer.services.create_service_order`).
        summa: Сумма платежа.
        wallet_id: FK в ``wallet`` — касса/счёт списания.
        payment_type_id: FK в ``payment_type`` — способ оплаты
            (1=Наличный, 2=Безналичный, 7=Банковская карта).
        payment_date: Дата/время платежа. По умолчанию — текущее время.
        notes: Примечание к платежу.

    Returns:
        ``payment_id`` созданного платежа.

    Raises:
        ValueError: Если заказ-наряд с ``document_out_id`` не найден.

    Example::

        from autodealer.actions.payment import create_payment

        payment_id = create_payment(
            document_out_id=42,
            summa=2300.0,
            wallet_id=1,        # Наличный расчёт
            payment_type_id=1,  # Наличный
        )
    """
    from autodealer.domain.payment import Payment
    from autodealer.domain.payment_out import PaymentOut
    from autodealer.domain.payment_document import PaymentDocument
    from autodealer.domain.money_document_detail import MoneyDocumentDetail
    from autodealer.domain.money_document_payment import MoneyDocumentPayment

    pay_dt = payment_date or datetime.now()

    with session_scope() as session:
        doc_reg_id = session.execute(
            text(
                "SELECT document_registry_id FROM document_out_header"
                " WHERE document_out_id = :doc_id"
            ),
            {"doc_id": document_out_id},
        ).scalar()

        if doc_reg_id is None:
            raise ValueError(
                f"Заказ-наряд document_out_id={document_out_id} не найден"
                " или не имеет document_registry_id"
            )

        pay = Payment(
            payment_type_id=payment_type_id,
            wallet_id=wallet_id,
            summa=summa,
            payment_date=pay_dt,
            document_registry_id=doc_reg_id,
            notes=notes,
        )
        session.add(pay)
        session.flush()
        payment_id = pay.payment_id

        session.add(PaymentOut(document_out_id=document_out_id, payment_id=payment_id))
        session.add(
            PaymentDocument(document_registry_id=doc_reg_id, payment_id=payment_id)
        )

        mdd = MoneyDocumentDetail(
            document_out_id=document_out_id,
            wallet_id=wallet_id,
            payment_type_id=payment_type_id,
            accounting_item_id=_ACCOUNTING_ITEM_CLIENT_PAYMENT,
        )
        session.add(mdd)
        session.flush()

        session.add(
            MoneyDocumentPayment(
                money_document_detail_id=mdd.money_document_detail_id,
                payment_id=payment_id,
            )
        )

        session.execute(
            text(
                "UPDATE document_out SET date_payment = :dt"
                " WHERE document_out_id = :doc_id"
            ),
            {"dt": pay_dt, "doc_id": document_out_id},
        )

    return payment_id


@dataclass
class PaymentSplitItem:
    """Одна часть разбивки платежа (способ + кошелёк + сумма)."""

    wallet_id: int
    payment_type_id: int
    summa: float
    notes: Optional[str] = None


def create_payment_split(
    *,
    document_out_id: int,
    parts: list[PaymentSplitItem],
    payment_date: Optional[datetime] = None,
) -> list[int]:
    """Создать несколько платежей за один заказ-наряд (разбивка по способам оплаты).

    Каждая часть создаётся независимо через :func:`create_payment`.
    Если хотя бы одна часть упадёт — предыдущие уже будут зафиксированы
    (транзакции независимы). Передавай только корректные данные.

    Args:
        document_out_id: PK заказ-наряда.
        parts: Список :class:`PaymentSplitItem` — по одному на каждый способ оплаты.
        payment_date: Единая дата/время для всех частей. По умолчанию — текущее время.

    Returns:
        Список ``payment_id`` в том же порядке, что и ``parts``.

    Raises:
        ValueError: Если ``parts`` пустой или суммы <= 0.

    Example::

        from autodealer.actions.payment import create_payment_split, PaymentSplitItem

        ids = create_payment_split(
            document_out_id=42,
            parts=[
                PaymentSplitItem(wallet_id=1, payment_type_id=1, summa=1000.0),  # наличные
                PaymentSplitItem(wallet_id=4, payment_type_id=7, summa=1300.0),  # карта
            ],
        )
    """
    if not parts:
        raise ValueError("parts не может быть пустым")

    invalid = [p for p in parts if p.summa <= 0]
    if invalid:
        raise ValueError(f"Сумма платежа должна быть > 0: {invalid}")

    pay_dt = payment_date or datetime.now()

    return [
        create_payment(
            document_out_id=document_out_id,
            summa=part.summa,
            wallet_id=part.wallet_id,
            payment_type_id=part.payment_type_id,
            payment_date=pay_dt,
            notes=part.notes,
        )
        for part in parts
    ]
