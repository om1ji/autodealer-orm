"""High-level service functions for AutoDealer domain operations.

These functions wrap multi-step ORM inserts into single atomic calls,
hiding the directory_registry / trigger bookkeeping from the caller.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import text

from autodealer.connection import session_scope
from datetime import datetime


# metatable_id=1 → ORGANIZATION
_METATABLE_ORGANIZATION = 1
# Системный пользователь по умолчанию
_SYSTEM_USER_ID = 1

_METATABLE_DOCUMENT_OUT = 12

_SERVICE_ORDER_PREFIX = "АВТ"

_DOCUMENT_STATE = {"Оформлен": 4, "Черновик": 2, "Удалён": -1}


# ---------------------------------------------------------------------------
# Организации
# ---------------------------------------------------------------------------


class OrganizationInfo:
    """Агрегат организации: основные поля + кошельки.

    Атрибуты:
        organization_id: PK организации.
        fullname: Полное название.
        shortname: Краткое название.
        inn: ИНН.
        kpp: КПП.
        ogrn: ОГРН.
        address: Адрес.
        face: 0=ЮЛ, 1=ИП/физлицо.
        hidden: 0=активна.
        wallets: Список кошельков ``[{"wallet_id": 3, "name": "Наличные"}]``.
    """

    def __init__(self, row: dict, wallets: list[dict]) -> None:
        self.organization_id: int = row["organization_id"]
        self.fullname: Optional[str] = row.get("fullname")
        self.shortname: Optional[str] = row.get("shortname")
        self.inn: Optional[str] = row.get("inn")
        self.kpp: Optional[str] = row.get("kpp")
        self.ogrn: Optional[str] = row.get("ogrn")
        self.address: Optional[str] = row.get("address")
        self.face: int = row.get("face", 0)
        self.hidden: int = row.get("hidden", 0)
        self.wallets: list[dict] = wallets

    def wallet_id_by_name(self, name: str) -> Optional[int]:
        """Найти wallet_id по части названия (без учёта регистра)."""
        name_lower = name.lower()
        for w in self.wallets:
            if name_lower in w["name"].lower():
                return w["wallet_id"]
        return None

    def __repr__(self) -> str:
        return (
            f"OrganizationInfo(id={self.organization_id},"
            f" name={self.shortname!r}, inn={self.inn!r},"
            f" wallets={len(self.wallets)})"
        )


def get_organization(organization_id: int) -> Optional["OrganizationInfo"]:
    """Загрузить организацию с кошельками по ID.

    Returns:
        :class:`OrganizationInfo` или ``None`` если не найдена.

    Example::

        org = get_organization(1)
        print(org)
        # OrganizationInfo(id=1, name='Наша фирма', inn=None, wallets=2)

        wallet_id = org.wallet_id_by_name("наличн")  # → 1
    """
    with session_scope() as session:
        row = (
            session.execute(
                text(
                    "SELECT organization_id, fullname, shortname, inn, kpp,"
                    "       ogrn, address, face, hidden"
                    " FROM organization WHERE organization_id = :oid"
                ),
                {"oid": organization_id},
            )
            .mappings()
            .first()
        )

        if row is None:
            return None

        wallets = (
            session.execute(
                text(
                    "SELECT wallet_id, name"
                    " FROM wallet WHERE organization_id = :oid"
                    " ORDER BY wallet_id"
                ),
                {"oid": organization_id},
            )
            .mappings()
            .all()
        )

        return OrganizationInfo(dict(row), [dict(w) for w in wallets])


def list_organizations() -> list["OrganizationInfo"]:
    """Вернуть список всех активных организаций с кошельками.

    Example::

        orgs = list_organizations()
        for org in orgs:
            print(org)
    """
    with session_scope() as session:
        rows = (
            session.execute(
                text(
                    "SELECT organization_id, fullname, shortname, inn, kpp,"
                    "       ogrn, address, face, hidden"
                    " FROM organization WHERE hidden = 0"
                    " ORDER BY organization_id"
                )
            )
            .mappings()
            .all()
        )

        result = []
        for row in rows:
            wallets = (
                session.execute(
                    text(
                        "SELECT wallet_id, name FROM wallet"
                        " WHERE organization_id = :oid ORDER BY wallet_id"
                    ),
                    {"oid": row["organization_id"]},
                )
                .mappings()
                .all()
            )
            result.append(OrganizationInfo(dict(row), [dict(w) for w in wallets]))

        return result


def create_organization(
    fullname: str,
    *,
    shortname: Optional[str] = None,
    inn: Optional[str] = None,
    kpp: Optional[str] = None,
    ogrn: Optional[str] = None,
    address: Optional[str] = None,
    face: int = 0,
    wallet_names: Optional[list[str]] = None,
    created_by_user_id: int = _SYSTEM_USER_ID,
) -> "OrganizationInfo":
    """Создать организацию в Firebird.

    Атомарно создаёт ``DirectoryRegistry`` → ``Organization`` → ``Wallet`` (если переданы).

    Args:
        fullname: Полное название (обязательно).
        shortname: Краткое название (по умолчанию — первые 30 символов fullname).
        inn: ИНН.
        kpp: КПП.
        ogrn: ОГРН.
        address: Адрес.
        face: 0=ЮЛ, 1=ИП.
        wallet_names: Список названий касс/счетов для создания.
            Например ``["Наличные", "Банковская карта", "СБП"]``.
        created_by_user_id: Пользователь-создатель.

    Returns:
        :class:`OrganizationInfo` созданной организации.

    Example::

        from autodealer.services import create_organization

        org = create_organization(
            "ООО СК-Авто Казань",
            shortname="СК-Авто",
            inn="1655012345",
            address="г. Казань, ул. Скрябина 8к1",
            wallet_names=["Наличные", "Банковская карта", "СБП"],
        )
        print(org.organization_id)
        print(org.wallets)
        # [{"wallet_id": 7, "name": "Наличные"}, ...]
    """
    from datetime import datetime as _dt

    sname = (shortname or fullname)[:30]

    with session_scope() as session:
        # 1. DirectoryRegistry
        dr = DirectoryRegistry(
            metatable_id=_METATABLE_ORGANIZATION,
            create_user_id=created_by_user_id,
            change_user_id=created_by_user_id,
        )
        session.add(dr)
        session.flush()
        dr_id = dr.directory_registry_id

        # 2. Organization
        session.execute(
            text(
                "INSERT INTO organization"
                " (directory_registry_id, fullname, shortname, inn, kpp, ogrn,"
                "  address, face, hidden, date_closing_period,"
                "  nds, can_sale, can_buy, print_check,"
                "  show_document_in_closing_period)"
                " VALUES"
                " (:dr_id, :fullname, :shortname, :inn, :kpp, :ogrn,"
                "  :address, :face, 0, :date_closing,"
                "  0, 1, 1, 1, 1)"
            ),
            {
                "dr_id": dr_id,
                "fullname": fullname,
                "shortname": sname,
                "inn": inn,
                "kpp": kpp,
                "ogrn": ogrn,
                "address": address,
                "face": face,
                "date_closing": _dt(2000, 1, 1),
            },
        )

        org_id = session.execute(
            text(
                "SELECT organization_id FROM organization"
                " WHERE directory_registry_id = :dr_id"
            ),
            {"dr_id": dr_id},
        ).scalar()

        # 3. Wallets (опционально)
        wallets_created = []
        for wname in wallet_names or []:
            session.execute(
                text(
                    "INSERT INTO wallet (name, organization_id) VALUES (:name, :org_id)"
                ),
                {"name": wname, "org_id": org_id},
            )
            wid = session.execute(
                text(
                    "SELECT MAX(wallet_id) FROM wallet WHERE organization_id = :org_id"
                ),
                {"org_id": org_id},
            ).scalar()
            wallets_created.append({"wallet_id": wid, "name": wname})

    return OrganizationInfo(
        {
            "organization_id": org_id,
            "fullname": fullname,
            "shortname": sname,
            "inn": inn,
            "kpp": kpp,
            "ogrn": ogrn,
            "address": address,
            "face": face,
            "hidden": 0,
        },
        wallets_created,
    )


# ---------------------------------------------------------------------------
# Комплексные работы (service_complex_work)
# ---------------------------------------------------------------------------


def iter_complex_works_by_tree(
    tree_id: int,
) -> "Generator[ServiceComplexWork, None, None]":
    """Генератор всех :class:`~autodealer.domain.service_complex_work.ServiceComplexWork`
    принадлежащих дереву ``tree_id``.

    Обходит ``service_complex_work_item`` → ``service_complex_work`` без загрузки
    всех записей в память сразу.

    Args:
        tree_id: ``service_complex_work_tree_id``.

    Yields:
        Экземпляры :class:`~autodealer.domain.service_complex_work.ServiceComplexWork`
        упорядоченные по ``(service_complex_work_item_id, position_number)``.

    Example::

        from autodealer.services import iter_complex_works_by_tree

        for work in iter_complex_works_by_tree(11):
            print(work.name, work.price)
    """

    from autodealer.domain.service_complex_work import ServiceComplexWork
    from autodealer.domain.service_complex_work_item import ServiceComplexWorkItem

    item_ids = [
        item.service_complex_work_item_id
        for item in ServiceComplexWorkItem.objects.filter(
            service_complex_work_tree_id=tree_id
        ).all()
    ]

    if not item_ids:
        return

    works = (
        ServiceComplexWork.objects.filter(service_complex_work_item_id__in=item_ids)
        .order_by("service_complex_work_item_id", "position_number")
        .all()
    )

    yield from works


# ---------------------------------------------------------------------------
# Каталог услуг (service_common_work)
# ---------------------------------------------------------------------------


def find_service_by_barcode(bar_code: str) -> Optional[int]:
    """Найти услугу в каталоге по bar_code. Возвращает service_common_work_id или None."""
    if not bar_code:
        return None
    with session_scope() as session:
        return session.execute(
            text(
                "SELECT service_common_work_id FROM service_common_work WHERE bar_code = :bc"
            ),
            {"bc": bar_code},
        ).scalar()


def get_or_create_service(
    name: str,
    price: Optional[float] = None,
    time_value: Optional[float] = None,
    bar_code: Optional[str] = None,
    tree_id: Optional[int] = None,
) -> int:
    """Найти услугу в каталоге по bar_code или создать новую.

    Args:
        name: Название услуги (обязательно).
        price: Цена по умолчанию.
        time_value: Длительность в минутах.
        bar_code: Уникальный ключ для идемпотентности (например ``rw:821460``).
        tree_id: FK → ``service_common_work_tree`` (папка в каталоге).

    Returns:
        ``service_common_work_id`` найденной или созданной записи.
    """
    with session_scope() as session:
        if bar_code:
            existing = session.execute(
                text(
                    "SELECT service_common_work_id FROM service_common_work"
                    " WHERE bar_code = :bc"
                ),
                {"bc": bar_code},
            ).scalar()
            if existing is not None:
                return existing

        session.execute(
            text(
                "INSERT INTO service_common_work"
                " (name, price, time_value, bar_code, service_common_work_tree_id)"
                " VALUES (:name, :price, :time_value, :bc, :tree_id)"
            ),
            {
                "name": name[:255],
                "price": price,
                "time_value": time_value,
                "bc": bar_code,
                "tree_id": tree_id,
            },
        )
        lookup = (
            "SELECT service_common_work_id FROM service_common_work WHERE bar_code = :bc"
            if bar_code
            else "SELECT MAX(service_common_work_id) FROM service_common_work WHERE name = :name"
        )
        params = {"bc": bar_code} if bar_code else {"name": name[:255]}
        return session.execute(text(lookup), params).scalar()


# ---------------------------------------------------------------------------
# Заказ-наряд с услугами
# ---------------------------------------------------------------------------

_DOCUMENT_TYPE_SERVICE_ORDER = 11  # «Заказ-наряд»


class ServiceOrderItem:
    """Одна строка услуги в заказ-наряде."""

    def __init__(
        self,
        name: str,
        price: float,
        time_value: float = 0.0,
        quantity: int = 1,
        external_id: Optional[str] = None,
    ) -> None:
        self.name = name
        self.price = price
        self.time_value = time_value
        self.quantity = quantity
        self.external_id = external_id


class ServiceOrder:
    """Агрегат заказ-наряда: document_out + document_out_header + service_work строки.

    Используется для чтения существующих документов.
    Для создания — используй :func:`create_service_order`.

    Атрибуты:
        document_out_id: PK документа.
        client_id: FK клиента.
        summa: Итоговая сумма.
        date_accept: Дата/время приёма.
        date_payment: Дата оплаты.
        document_number: Номер документа из document_out_header.
        date_create: Дата создания из document_out_header.
        client_car: Привязанное авто (из document_service_detail).
        items: Список строк услуг (:class:`ServiceOrderItem`).
    """

    def __init__(self, row: dict, items: list[ServiceOrderItem]) -> None:
        self.document_out_id: int = row["document_out_id"]
        self.client_id: Optional[int] = row.get("client_id")
        self.summa: float = row.get("summa") or 0.0
        self.date_accept = row.get("date_accept")
        self.date_payment = row.get("date_payment")
        self.document_number: Optional[int] = row.get("document_number")
        self.date_create = row.get("date_create")
        self.client_car: Optional[int] = row.get("client_car")
        self.items: list[ServiceOrderItem] = items

    def __repr__(self) -> str:
        return (
            f"ServiceOrder(id={self.document_out_id}, client={self.client_id},"
            f" summa={self.summa}, items={len(self.items)})"
        )


def get_service_order(document_out_id: int) -> Optional["ServiceOrder"]:
    """Загрузить заказ-наряд со всеми строками услуг по document_out_id.

    Returns:
        :class:`ServiceOrder` или ``None`` если документ не найден.

    Example::

        order = get_service_order(42)
        if order:
            for item in order.items:
                print(item.name, item.price)
    """
    with session_scope() as session:
        doc = (
            session.execute(
                text(
                    "SELECT do2.document_out_id, do2.client_id, do2.summa,"
                    "       do2.date_accept, do2.date_payment,"
                    "       doh.number AS document_number, doh.date_create,"
                    "       dsd.client_car"
                    " FROM document_out do2"
                    " LEFT JOIN document_out_header doh"
                    "        ON doh.document_out_id = do2.document_out_id"
                    " LEFT JOIN document_service_detail dsd"
                    "        ON dsd.document_out_header_id = doh.document_out_header_id"
                    " WHERE do2.document_out_id = :doc_id"
                ),
                {"doc_id": document_out_id},
            )
            .mappings()
            .first()
        )

        if doc is None:
            return None

        works = (
            session.execute(
                text(
                    "SELECT name, price, time_value, quantity, external_id"
                    " FROM service_work"
                    " WHERE document_out_id = :doc_id"
                    " ORDER BY position_number"
                ),
                {"doc_id": document_out_id},
            )
            .mappings()
            .all()
        )

        items = [
            ServiceOrderItem(
                name=w["name"] or "",
                price=float(w["price"] or 0),
                time_value=float(w["time_value"] or 0),
                quantity=w["quantity"] or 1,
                external_id=w["external_id"],
            )
            for w in works
        ]

        return ServiceOrder(dict(doc), items)


def create_service_order(
    *,
    client_id: int,
    items: list[ServiceOrderItem],
    document_out_tree_id: int,
    organization_id: int,
    client_car: Optional[int] = None,
    date_start: datetime,
    date_finish: datetime,
    created_by_user_id: int = _SYSTEM_USER_ID,
    notes: str | None = None,
    service_order_suffix: str | None = None,
) -> int:
    """Создать заказ-наряд с услугами для клиента.

    Создаёт цепочку:
    1. ``document_out``           — документ (Заказ-наряд, client_id, summa).
    2. ``document_out_header``    — заголовок (номер, дата, user_id).
    3. ``document_service_detail``— привязка авто (client_car), если передан.
    4. ``service_work`` × N      — строки услуг.

    Args:
        client_id: PK клиента в Firebird.
        items: Список услуг (:class:`ServiceOrderItem`).
        client_car: PK из ``model_link`` — привязка конкретного авто к документу.
        date_accept: Дата/время приёма авто (``datetime``). По умолчанию — сейчас.
        created_by_user_id: user_id исполнителя (записывается в ``document_out_header``).

    Returns:
        ``document_out_id`` созданного заказ-наряда.

    Example::

        from autodealer.services import create_service_order, ServiceOrderItem
        doc_id = create_service_order(
            client_id=42,
            client_car=7,
            items=[
                ServiceOrderItem("Экспресс мойка", price=600, time_value=20),
                ServiceOrderItem("Чернение резины", price=150, time_value=10),
            ],
        )
    """
    from datetime import datetime as _dt
    from autodealer.domain.document_out import DocumentOut
    from autodealer.domain.document_out_header import DocumentOutHeader
    from autodealer.domain.document_registry import DocumentRegistry
    from autodealer.domain.document_service_detail import DocumentServiceDetail
    from autodealer.domain.service_work import ServiceWork

    if not items:
        raise ValueError("items не может быть пустым")

    finish_dt = date_finish or _dt.now()
    summa = sum(i.price * i.quantity for i in items)

    with session_scope() as session:
        # 1. document_out
        doc_out = DocumentOut(
            document_type_id=_DOCUMENT_TYPE_SERVICE_ORDER,
            client_id=client_id,
            summa=summa,
            date_accept=finish_dt,
            organization_id=organization_id,
        )
        session.add(doc_out)
        session.flush()

        # 2. document_registry
        doc_reg = DocumentRegistry(
            metatable_id=_METATABLE_DOCUMENT_OUT,
            create_user_id=created_by_user_id,
            change_user_id=created_by_user_id,
            create_date=date_start,
            change_date=date_start,
            document_type_id_cache=_DOCUMENT_TYPE_SERVICE_ORDER,
        )
        session.add(doc_reg)
        session.flush()

        # 3. document_out_header
        next_number = session.execute(
            text(
                "SELECT MAX(number) + 1 FROM document_out_header WHERE document_type_id = :t"
            ),
            {"t": _DOCUMENT_TYPE_SERVICE_ORDER},
        ).scalar()

        doc_header = DocumentOutHeader(
            document_out_id=doc_out.document_out_id,
            document_type_id=_DOCUMENT_TYPE_SERVICE_ORDER,
            document_out_tree_id=document_out_tree_id,
            document_registry_id=doc_reg.document_registry_id,
            user_id=created_by_user_id,
            date_create=finish_dt,
            notes=notes,
            number=next_number,
            suffix=service_order_suffix,
            prefix=_SERVICE_ORDER_PREFIX,
            state=_DOCUMENT_STATE["Черновик"],
        )
        session.add(doc_header)
        session.flush()

        # 4. document_service_detail (привязка авто, опционально)
        if client_car is not None:
            session.add(
                DocumentServiceDetail(
                    document_out_header_id=doc_header.document_out_header_id,
                    model_link_id=client_car,
                )
            )

        # 5. service_work — строки услуг
        for pos, item in enumerate(items, 1):
            session.add(
                ServiceWork(
                    document_out_id=doc_out.document_out_id,
                    name=item.name,
                    price=item.price,
                    time_value=item.time_value,
                    quantity=item.quantity,
                    position_number=pos,
                    external_id=item.external_id or None,
                )
            )

        document_out_id = doc_out.document_out_id

    return document_out_id


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

    .. deprecated::
        Используй :func:`autodealer.actions.payment.create_payment`.
    """
    from autodealer.actions.payment import create_payment as _create_payment

    return _create_payment(
        document_out_id=document_out_id,
        summa=summa,
        wallet_id=wallet_id,
        payment_type_id=payment_type_id,
        payment_date=payment_date,
        notes=notes,
    )


def create_service_order_from_rocketwash_category(
    *,
    client_id: int,
    rocketwash_category: str,
    client_car: Optional[int] = None,
    date_accept: Optional[object] = None,
    created_by_user_id: int = _SYSTEM_USER_ID,
) -> int:
    """Создать заказ-наряд со всеми работами из категории RocketWash.

    По маппингу ``rocketwash_category`` → ``service_complex_work_tree_id``
    подбираются все :class:`~autodealer.domain.service_complex_work.ServiceComplexWork`
    из соответствующего дерева и вставляются в заказ-наряд как строки услуг.

    Args:
        client_id: PK клиента в Firebird.
        rocketwash_category: Категория из RocketWash (напр. ``"Кат.01"``).
        client_car: PK из ``model_link`` — привязка конкретного авто.
        date_accept: Дата/время приёма. По умолчанию — текущее время.
        created_by_user_id: user_id исполнителя.

    Returns:
        ``document_out_id`` созданного заказ-наряда.

    Raises:
        KeyError: Если категория RocketWash не найдена в маппинге.
        ValueError: Если в категории нет ни одной работы.

    Example::

        from autodealer.services import create_service_order_from_rocketwash_category
        doc_id = create_service_order_from_rocketwash_category(
            client_id=100,
            rocketwash_category="Кат.01",
            client_car=3,
        )
    """
    from autodealer.integration.rocketwash import get_complex_work_tree_id
    from autodealer.domain.service_complex_work import ServiceComplexWork
    from autodealer.domain.service_complex_work_item import ServiceComplexWorkItem

    tree_id = get_complex_work_tree_id(rocketwash_category)

    # Все items дерева → все работы
    item_ids = [
        item.service_complex_work_item_id
        for item in ServiceComplexWorkItem.objects.filter(
            service_complex_work_tree_id=tree_id
        ).all()
    ]
    if not item_ids:
        raise ValueError(
            f"Нет групп работ для категории {rocketwash_category!r} (tree_id={tree_id})"
        )

    works = (
        ServiceComplexWork.objects.filter(service_complex_work_item_id__in=item_ids)
        .order_by("position_number")
        .all()
    )

    if not works:
        raise ValueError(
            f"Нет работ для категории {rocketwash_category!r} (tree_id={tree_id})"
        )

    items = [
        ServiceOrderItem(
            name=w.name,
            price=float(w.price or 0),
            time_value=float(w.time_value or 0),
            quantity=w.quantity or 1,
            external_id=str(w.service_complex_work_id),
        )
        for w in works
    ]

    return create_service_order(
        client_id=client_id,
        items=items,
        client_car=client_car,
        date_accept=date_accept,
        created_by_user_id=created_by_user_id,
    )


def create_service_order_from_rocketwash_services(
    *,
    client_id: int,
    rw_service_ids: list[int],
    car_type_id: int,
    client_car: Optional[int] = None,
    date_accept: Optional[object] = None,
    created_by_user_id: int = _SYSTEM_USER_ID,
) -> int:
    """Создать заказ-наряд из конкретных услуг RocketWash для заданной категории авто.

    По ``car_type_id`` определяет категорию авто (``"Кат.01"`` … ``"Кат.04"``),
    фильтрует ``rw_service_ids`` через маппинг и берёт цены из ``rocketwash.db``
    для этой категории.

    Args:
        client_id: PK клиента в Firebird.
        rw_service_ids: Список id услуг из RocketWash (``services.id``).
        car_type_id: RocketWash ``car_type_id`` (35=Кат.04, 36=Кат.01, 37=Кат.02, 38=Кат.03).
        client_car: PK из ``model_link`` — привязка конкретного авто.
        date_accept: Дата/время приёма. По умолчанию — текущее время.
        created_by_user_id: user_id исполнителя.

    Returns:
        ``document_out_id`` созданного заказ-наряда.

    Raises:
        KeyError: Если ``car_type_id`` неизвестен или услуга не найдена в маппинге.
        ValueError: Если ни одна из услуг не смаппирована.

    Example::

        from autodealer.services import create_service_order_from_rocketwash_services

        doc_id = create_service_order_from_rocketwash_services(
            client_id=100,
            rw_service_ids=[821460, 821462, 821476],
            car_type_id=36,   # Кат.01 — Седан
            client_car=3,
        )
    """
    from autodealer.integration.rocketwash import (
        _resolve_mapped_services,
        _get_cw_name,
        get_car_category_by_type_id,
    )

    car_category = get_car_category_by_type_id(car_type_id)
    mapped = _resolve_mapped_services(rw_service_ids, car_category)

    if not mapped:
        raise ValueError(
            f"Ни одна из услуг {rw_service_ids} не смаппирована "
            f"для категории {car_category!r}"
        )

    items = [
        ServiceOrderItem(
            name=_get_cw_name(svc.service_id) or svc.name[:255],
            price=svc.price or 0.0,
            time_value=svc.duration or 0.0,
            quantity=1,
            external_id=str(svc.service_id),
        )
        for svc in mapped
    ]

    return create_service_order(
        client_id=client_id,
        items=items,
        client_car=client_car,
        date_accept=date_accept,
        created_by_user_id=created_by_user_id,
    )
