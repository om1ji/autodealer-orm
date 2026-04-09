"""High-level actions: client and vehicle management."""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import text

from autodealer.connection import session_scope
from autodealer.domain.client import Client
from autodealer.domain.directory_registry import DirectoryRegistry
from autodealer.domain.model_detail import ModelDetail
from autodealer.domain.model_link import ModelLink

_METATABLE_CLIENT = 3
_METATABLE_MODEL_DETAIL = 4
_SYSTEM_USER_ID = 1
_CLIENT_TREE_PHYSICAL = 1


# ---------------------------------------------------------------------------
# Клиенты
# ---------------------------------------------------------------------------


def create_client(
    fullname: str,
    *,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    birth: Optional[date] = None,
    sex: Optional[int] = None,
    discount: float = 0.0,
    discount_work: float = 0.0,
    client_tree_id: int = _CLIENT_TREE_PHYSICAL,
    created_by_user_id: int = _SYSTEM_USER_ID,
) -> int:
    """Создать клиента в Firebird.

    Атомарно создаёт цепочку:
    ``DirectoryRegistry (metatable=3)`` → ``Client`` → ``Contact`` (если есть phone/email).

    Args:
        fullname: Полное имя клиента (обязательно).
        phone: Мобильный телефон.
        email: Email.
        birth: Дата рождения.
        sex: 1=муж, 2=жен, None=не указан.
        discount: Скидка на товары %.
        discount_work: Скидка на работы %.
        client_tree_id: Папка клиентов (1=Физлица, 2=Юрлица, 3=VIP).
        created_by_user_id: Пользователь-создатель.

    Returns:
        ``client_id`` созданного клиента.

    Example::

        from datetime import date
        from autodealer.actions.client import create_client

        client_id = create_client(
            "Иванов Иван Иванович",
            phone="79991234567",
            email="ivan@example.com",
            birth=date(1990, 5, 15),
            sex=1,
            discount=5.0,
        )
    """
    shortname = fullname[:30]

    with session_scope() as session:
        # 1. DirectoryRegistry
        dr = DirectoryRegistry(
            metatable_id=_METATABLE_CLIENT,
            create_user_id=created_by_user_id,
            change_user_id=created_by_user_id,
        )
        session.add(dr)
        session.flush()
        dr_id = dr.directory_registry_id

        # 2. Client
        session.execute(
            text(
                "INSERT INTO client"
                " (directory_registry_id, client_tree_id, fullname, shortname,"
                "  face, hidden, discount, discount_work, sex, birth)"
                " VALUES"
                " (:dr_id, :tree_id, :fullname, :shortname,"
                "  0, 0, :discount, :discount_work, :sex, :birth)"
            ),
            {
                "dr_id": dr_id,
                "tree_id": client_tree_id,
                "fullname": fullname,
                "shortname": shortname,
                "discount": discount,
                "discount_work": discount_work,
                "sex": sex,
                "birth": birth,
            },
        )
        client_id = session.execute(
            text("SELECT client_id FROM client WHERE directory_registry_id = :dr_id"),
            {"dr_id": dr_id},
        ).scalar()

        # 3. Contact (если есть phone или email)
        if phone or email:
            session.execute(
                text(
                    "INSERT INTO contact"
                    " (directory_registry_link_id, mobile, email,"
                    "  default_contact, hidden, face)"
                    " VALUES (:dr_id, :mobile, :email, 1, 0, 0)"
                ),
                {"dr_id": dr_id, "mobile": phone, "email": email},
            )

    return client_id


# ---------------------------------------------------------------------------
# Автомобили
# ---------------------------------------------------------------------------


def get_or_create_mark(name: str) -> int:
    """Найти марку по имени или создать новую. Возвращает mark_id."""
    with session_scope() as session:
        existing = session.execute(
            text("SELECT mark_id FROM mark WHERE name = :name"), {"name": name}
        ).scalar()
        if existing is not None:
            return existing
        session.execute(
            text("INSERT INTO mark (name, hidden) VALUES (:name, 0)"), {"name": name}
        )
        return session.execute(
            text("SELECT mark_id FROM mark WHERE name = :name"), {"name": name}
        ).scalar()


def get_or_create_model(mark_id: int, model_name: str) -> int:
    """Найти модель по марке и имени или создать новую. Возвращает model_id."""
    with session_scope() as session:
        existing = session.execute(
            text(
                "SELECT model_id FROM model WHERE mark_id = :mark_id AND name = :name"
            ),
            {"mark_id": mark_id, "name": model_name},
        ).scalar()
        if existing is not None:
            return existing
        session.execute(
            text(
                "INSERT INTO model (mark_id, name, hidden) VALUES (:mark_id, :name, 0)"
            ),
            {"mark_id": mark_id, "name": model_name},
        )
        return session.execute(
            text(
                "SELECT model_id FROM model WHERE mark_id = :mark_id AND name = :name"
            ),
            {"mark_id": mark_id, "name": model_name},
        ).scalar()


def get_or_create_color(name: str) -> Optional[int]:
    """Найти цвет по имени или создать новый. Возвращает color_id или None если name пустой."""
    if not name:
        return None
    with session_scope() as session:
        existing = session.execute(
            text("SELECT color_id FROM color WHERE name = :name"), {"name": name}
        ).scalar()
        if existing is not None:
            return existing
        session.execute(
            text("INSERT INTO color (name, hidden) VALUES (:name, 0)"), {"name": name}
        )
        return session.execute(
            text("SELECT color_id FROM color WHERE name = :name"), {"name": name}
        ).scalar()


def find_vehicle_by_regno(regno: str) -> Optional[int]:
    """Найти автомобиль по госномеру. Возвращает model_detail_id или None."""
    if not regno:
        return None
    with session_scope() as session:
        return session.execute(
            text("SELECT model_detail_id FROM model_detail WHERE regno = :regno"),
            {"regno": regno},
        ).scalar()


def find_vehicle_by_vin(vin: str) -> Optional[int]:
    """Найти автомобиль по VIN. Возвращает model_detail_id или None."""
    if not vin:
        return None
    with session_scope() as session:
        return session.execute(
            text("SELECT model_detail_id FROM model_detail WHERE vin = :vin"),
            {"vin": vin},
        ).scalar()


def create_vehicle_for_client(
    *,
    client_id: int,
    model_id: int,
    vin: Optional[str] = None,
    regno: Optional[str] = None,
    year_of_production: Optional[date] = None,
    color_id: Optional[int] = None,
    car_engine_type_id: Optional[int] = None,
    car_gearbox_type_id: Optional[int] = None,
    car_body_type_id: Optional[int] = None,
    car_fuel_type_id: Optional[int] = None,
    engine_number: Optional[str] = None,
    chassis: Optional[str] = None,
    body: Optional[str] = None,
    notes: Optional[str] = None,
    default_car: bool = False,
    created_by_user_id: int = _SYSTEM_USER_ID,
) -> ModelLink:
    """Create a vehicle and attach it to a client.

    Performs three inserts in a single transaction:
    1. ``directory_registry`` — audit record for the new model_detail.
    2. ``model_detail``       — the specific vehicle (VIN, regno, specs).
    3. ``model_link``         — the link between the vehicle and the client.

    Args:
        client_id: PK of the client who owns the vehicle.
        model_id: PK of the make/model (e.g. Toyota Camry → ``model.model_id``).
        vin: Vehicle identification number.
        regno: State registration plate (госномер).
        year_of_production: Year/date of manufacture.
        color_id: FK to ``color`` table.
        car_engine_type_id: FK to ``car_engine_type``.
        car_gearbox_type_id: FK to ``car_gearbox_type``.
        car_body_type_id: FK to ``car_body_type``.
        car_fuel_type_id: FK to ``car_fuel_type``.
        engine_number: Engine serial number.
        chassis: Chassis number.
        body: Body number.
        notes: Free-text notes.
        default_car: If ``True``, marks this as the client's primary vehicle.
        created_by_user_id: User performing the operation.

    Returns:
        The newly created :class:`~autodealer.domain.model_link.ModelLink` instance.

    Raises:
        ValueError: If the client with ``client_id`` does not exist.
    """
    with session_scope() as session:
        client = session.get(Client, client_id)
        if client is None:
            raise ValueError(f"Client with id={client_id} does not exist.")
        client_directory_registry_id = client.directory_registry_id
        session.expunge(client)

    dir_reg = DirectoryRegistry.objects.create(
        metatable_id=_METATABLE_MODEL_DETAIL,
        create_user_id=created_by_user_id,
        change_user_id=created_by_user_id,
    )

    detail_fields: dict = dict(
        model_id=model_id,
        directory_registry_id=dir_reg.directory_registry_id,
    )
    optional = dict(
        vin=vin,
        regno=regno,
        year_of_production=year_of_production,
        color_id=color_id,
        car_engine_type_id=car_engine_type_id,
        car_gearbox_type_id=car_gearbox_type_id,
        car_body_type_id=car_body_type_id,
        car_fuel_type_id=car_fuel_type_id,
        engine_number=engine_number,
        chassis=chassis,
        body=body,
        notes=notes,
    )
    detail_fields.update({k: v for k, v in optional.items() if v is not None})
    model_detail = ModelDetail.objects.create(**detail_fields)

    model_link = ModelLink.objects.create(
        model_detail_id=model_detail.model_detail_id,
        directory_registry_link_id=client_directory_registry_id,
        default_car=1 if default_car else 0,
    )

    return model_link


def add_vehicle_to_client(
    client_id: int,
    make: str,
    model_name: str,
    *,
    regno: Optional[str] = None,
    vin: Optional[str] = None,
    year: Optional[int] = None,
    color: Optional[str] = None,
    default_car: bool = False,
    created_by_user_id: int = _SYSTEM_USER_ID,
) -> int:
    """Добавить автомобиль клиенту по имени марки и модели.

    Автоматически находит или создаёт ``mark``, ``model``, ``color``,
    затем создаёт ``model_detail`` + ``model_link``.

    Идемпотентность: если машина с таким ``regno`` уже существует в БД —
    возвращает существующий ``model_detail_id`` без создания дубликата.

    Args:
        client_id: PK клиента в Firebird.
        make: Марка («Toyota», «BMW»).
        model_name: Модель («Camry», «X5»).
        regno: Госномер.
        vin: VIN-номер.
        year: Год выпуска (например 2020).
        color: Цвет строкой («Белый», «Чёрный»).
        default_car: Пометить как основное авто клиента.
        created_by_user_id: Пользователь-создатель.

    Returns:
        ``model_detail_id`` созданного или уже существующего автомобиля.

    Example::

        from autodealer.actions.client import add_vehicle_to_client

        md_id = add_vehicle_to_client(
            client_id=42,
            make="Toyota",
            model_name="Camry",
            regno="А001ВС77",
            year=2020,
            color="Белый",
            default_car=True,
        )
    """
    if regno:
        existing = find_vehicle_by_regno(regno)
        if existing is not None:
            return existing

    mark_id = get_or_create_mark(make)
    model_id = get_or_create_model(mark_id, model_name)
    color_id = get_or_create_color(color) if color else None
    year_date = date(year, 1, 1) if year else None

    link = create_vehicle_for_client(
        client_id=client_id,
        model_id=model_id,
        regno=regno,
        vin=vin,
        year_of_production=year_date,
        color_id=color_id,
        default_car=default_car,
        created_by_user_id=created_by_user_id,
    )
    return link.model_detail_id


def get_client_vehicles(client_id: int) -> list[ModelLink]:
    """Вернуть все автомобили клиента в виде объектов :class:`ModelLink`.

    Каждый :class:`ModelLink` содержит ``model_detail_id``, ``default_car``
    и ``directory_registry_link_id`` (FK → клиент).

    Args:
        client_id: PK клиента в Firebird.

    Returns:
        Список :class:`ModelLink`. Пустой список если у клиента нет машин.

    Example::

        from autodealer.actions.client import get_client_vehicles

        links = get_client_vehicles(42)
        for link in links:
            print(link.model_link_id, link.model_detail_id, link.default_car)
    """
    with session_scope() as session:
        client = session.get(Client, client_id)
        if client is None:
            return []
        links = (
            session.query(ModelLink)
            .filter(
                ModelLink.directory_registry_link_id == client.directory_registry_id
            )
            .all()
        )
        session.expunge_all()
        return links
