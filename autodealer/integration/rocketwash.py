"""Integration layer: RocketWash → AutoDealer ORM.

Maps RocketWash entities to AutoDealer domain objects.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from autodealer.domain.service_complex_work_tree import ServiceComplexWorkTree

# ---------------------------------------------------------------------------
# RocketWash SQLite DB path (relative to this file → project root)
# ---------------------------------------------------------------------------

_ROCKETWASH_DB = (
    Path(__file__).parent.parent.parent.parent / "RocketWash-parser" / "rocketwash.db"
)

# ---------------------------------------------------------------------------
# Mapping: RocketWash service_id → AutoDealer service_complex_work name
# Only services that exist in BOTH systems (inner join).
# RocketWash service_id → canonical name used in service_complex_work.name
# ---------------------------------------------------------------------------

_SERVICE_ID_TO_CW_NAME: dict[int, str] = {
    821455: "Экспресс мойка",  # 02. Экспресс мойка (бесконтакт, без протирки)
    821457: "Экспресс мойка",  # 04. Экспресс мойка (контакт, без протирки)
    821459: "Стандарт",  # 06. Стандарт
    821460: "Комплекс",  # 07. Комплекс (Первая Фаза)
    821461: "Премиум Комплекс",  # 08. Комплекс премиум
    821462: "Вторая Фаза",  # 09. Вторая Фаза
    821463: "Кварцевое покрытие",  # 10. Кварцевое покрытие
    821464: "Восковое покрытие",  # 11. Покрытие кузова воском
    821465: "Чернение резины",  # 12. Чернение резины
    821466: "Силикон на уплотнители арок и дверей",  # 13. Силикон
    821467: "Мойка колеса (1шт.)",  # 14. Мойка колеса 1шт.
    821469: "Продувка воздухом ручек и зеркал",  # 16. Продувка воздухом
    821472: "Комплексная уборка салона",  # 19. Комплексная уборка салона
    821473: "Уборка багажника",  # 20. Уборка багажника
    821474: "Влажная уборка салона",  # 21. Влажная уборка салона
    821475: "Очистка стекл",  # 22. Чистка стёкл
    821476: "Пылесос салона",  # 23. Пылесос салона
    821477: "Полировка пластика",  # 24. Полировка пластика
    821478: "Кондиционер Кожи Салона",  # 25. Кондиционер кожи салона
    821479: "Чистка ковриков (1 шт.)",  # 26. Чистка ковриков
    821520: "Покрытие Антидождь",  # 32. Покрытие антидождь
}

# Services present in RocketWash but NOT mapped (no equivalent in AutoDealer CW.fdb):
# 821454 — Тех.мойка (Вода)               — нет аналога
# 821456 — Экспресс мойка (с протиркой)   — нет отдельной позиции
# 821458 — Экспресс мойка контакт+протирка — нет отдельной позиции
# 821468 — Очистка дисков от нагара       — нет аналога
# 821470 — Очистка от битума              — нет аналога
# 821471 — Очистка от насекомых           — нет аналога
# 821480 — Мойка ДВС                      — нет аналога
# 821481 — Мойка Мотоциклов              — нет аналога
# 821482 — Ковры (домашние)              — нет аналога
# 821492 — Незамерзайка (товар)          — нет аналога
# 821521 — Удаление водного камня        — нет аналога

# ---------------------------------------------------------------------------
# Mapping: RocketWash category name → service_complex_work_tree_id (AutoDealer)
# ---------------------------------------------------------------------------

_COMPLEX_WORK_TREE_ID_MAPPING: dict[str, int] = {
    "Кат.01": 11,
    "Кат.02": 15,
    "Кат.03": 16,
    "Кат.04": 17,
}

# Mapping: RocketWash car_type_id → category name
_CAR_TYPE_ID_TO_CATEGORY: dict[int, str] = {
    36: "Кат.01",
    37: "Кат.02",
    38: "Кат.03",
    35: "Кат.04",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class RocketWashService:
    """A RocketWash service with price for a specific car category."""

    service_id: int
    name: str
    category: str  # e.g. "01. МОЙКА и КОМПЛЕКСЫ"
    car_type_id: int
    car_category: str  # e.g. "Кат.01"
    price: Optional[float]
    duration: Optional[float]


@dataclass
class MappedServiceItem:
    """A RocketWash service resolved to its AutoDealer name and price."""

    rw_service_id: int
    rw_name: str  # original RocketWash name
    cw_name: str  # name in service_complex_work
    price: float  # actual price from the reservation
    duration: float  # duration in minutes
    count: int  # quantity (usually 1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_complex_work_tree_id(rocketwash_category: str) -> int:
    """Return the AutoDealer ``service_complex_work_tree_id`` for a RocketWash category name.

    Args:
        rocketwash_category: Category name as it appears in RocketWash (e.g. ``"Кат.01"``).

    Returns:
        The corresponding ``service_complex_work_tree_id`` in AutoDealer.

    Raises:
        KeyError: If the category name is not present in the mapping.

    Example:
        >>> get_complex_work_tree_id("Кат.01")
        11
    """
    if rocketwash_category not in _COMPLEX_WORK_TREE_ID_MAPPING:
        known = ", ".join(sorted(_COMPLEX_WORK_TREE_ID_MAPPING))
        raise KeyError(
            f"Unknown RocketWash category: {rocketwash_category!r}. "
            f"Known categories: {known}"
        )
    return _COMPLEX_WORK_TREE_ID_MAPPING[rocketwash_category]


def get_complex_work_tree(rocketwash_category: str) -> ServiceComplexWorkTree:
    """Return the AutoDealer ``ServiceComplexWorkTree`` ORM object for a RocketWash category.

    Args:
        rocketwash_category: Category name as it appears in RocketWash.

    Returns:
        The corresponding :class:`~autodealer.domain.service_complex_work_tree.ServiceComplexWorkTree` instance.

    Raises:
        KeyError: If the category name is not in the mapping.
        DoesNotExist: If the mapped ``service_complex_work_tree_id`` does not exist in the DB.
    """
    tree_id = get_complex_work_tree_id(rocketwash_category)
    return ServiceComplexWorkTree.objects.get(service_complex_work_tree_id=tree_id)


def resolve_complex_work_tree_id(rocketwash_category: str) -> int | None:
    """Like :func:`get_complex_work_tree_id` but returns ``None`` for unknown categories.

    Useful when processing bulk data where unknown categories should be skipped
    rather than raise an exception.
    """
    return _COMPLEX_WORK_TREE_ID_MAPPING.get(rocketwash_category)


def get_services_for_car_category(
    car_category: str,
    *,
    db_path: Path = _ROCKETWASH_DB,
    exclude_no_price: bool = True,
) -> list[RocketWashService]:
    """Load all RocketWash services with prices for a specific car category.

    Args:
        car_category: Category name, e.g. ``"Кат.01"``.
        db_path: Path to ``rocketwash.db``. Defaults to ``../RocketWash-parser/rocketwash.db``.
        exclude_no_price: If ``True`` (default), skip services without a price.

    Returns:
        List of :class:`RocketWashService` sorted by service id.

    Raises:
        KeyError: If ``car_category`` is not in the known mapping.
        FileNotFoundError: If ``rocketwash.db`` is not found.

    Example:
        >>> services = get_services_for_car_category("Кат.01")
        >>> for s in services:
        ...     print(s.name, s.price)
    """
    car_type_id = _get_car_type_id(car_category)

    if not db_path.exists():
        raise FileNotFoundError(f"rocketwash.db не найден: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT s.id, s.name, s.category, sp.car_type_id, sp.price, sp.duration
            FROM services s
            JOIN service_prices sp ON sp.service_id = s.id
            WHERE sp.car_type_id = ?
            ORDER BY s.id
            """,
            (car_type_id,),
        ).fetchall()
    finally:
        conn.close()

    result = []
    for service_id, name, category, ct_id, price, duration in rows:
        if exclude_no_price and price is None:
            continue
        result.append(
            RocketWashService(
                service_id=service_id,
                name=name,
                category=category,
                car_type_id=ct_id,
                car_category=car_category,
                price=price,
                duration=duration,
            )
        )
    return result


def _resolve_mapped_services(
    rw_service_ids: list[int],
    car_category: str,
    *,
    db_path: Path = _ROCKETWASH_DB,
) -> list[RocketWashService]:
    """Return only the RocketWash services that have a mapping in AutoDealer.

    Filters ``rw_service_ids`` to those present in ``_SERVICE_ID_TO_CW_NAME``
    and fetches their price for ``car_category`` from ``rocketwash.db``.

    Args:
        rw_service_ids: List of RocketWash service ids (e.g. from a reservation).
        car_category: Car category, e.g. ``"Кат.01"``.
        db_path: Path to ``rocketwash.db``.

    Returns:
        List of :class:`RocketWashService` for services that exist in both systems,
        with price set for the given car category.

    Example:
        >>> services = resolve_mapped_services([821459, 821462, 821480], "Кат.02")
        >>> # 821480 (Мойка ДВС) is skipped — no AutoDealer equivalent
        >>> for s in services:
        ...     print(s.name, s.price)
    """
    car_type_id = _get_car_type_id(car_category)
    mapped_ids = [sid for sid in rw_service_ids if sid in _SERVICE_ID_TO_CW_NAME]

    if not mapped_ids:
        return []

    placeholders = ",".join("?" * len(mapped_ids))
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            f"""
            SELECT s.id, s.name, s.category, sp.car_type_id, sp.price, sp.duration
            FROM services s
            JOIN service_prices sp ON sp.service_id = s.id
            WHERE sp.car_type_id = ? AND s.id IN ({placeholders})
            ORDER BY s.id
            """,
            (car_type_id, *mapped_ids),
        ).fetchall()
    finally:
        conn.close()

    return [
        RocketWashService(
            service_id=service_id,
            name=name,
            category=category,
            car_type_id=ct_id,
            car_category=car_category,
            price=price,
            duration=duration,
        )
        for service_id, name, category, ct_id, price, duration in rows
        if price is not None
    ]


def _get_cw_name(rw_service_id: int) -> Optional[str]:
    """Return the AutoDealer ``service_complex_work.name`` for a RocketWash service id.

    Returns ``None`` if the service has no mapping.

    Example:
        >>> get_cw_name(821459)
        'Стандарт'
        >>> get_cw_name(821480)  # Мойка ДВС — not mapped
        None
    """
    return _SERVICE_ID_TO_CW_NAME.get(rw_service_id)


def map_reservation_services(services_detail: list[dict]) -> list[MappedServiceItem]:
    """Map RocketWash reservation services to AutoDealer ``service_complex_work`` names.

    Accepts the parsed ``services_detail`` JSON from a reservation row and returns
    only the services that have a mapping in ``_SERVICE_ID_TO_CW_NAME``.
    Prices and durations are taken directly from the reservation (already correct
    for the specific car category — no extra DB lookup needed).

    Args:
        services_detail: Parsed list from ``reservations.services_detail`` JSON.
            Each item must have ``"id"``, ``"name"``, ``"price"``,
            ``"duration"``, and ``"count"`` keys.

    Returns:
        List of :class:`MappedServiceItem` for services found in both systems.
        Unmapped services are silently skipped.

    Example::

        import json
        from autodealer.integration.rocketwash import map_reservation_services

        raw = json.loads(reservation_row["services_detail"])
        items = map_reservation_services(raw)
        for item in items:
            print(item.cw_name, item.price)
    """
    result = []
    for svc in services_detail:
        rw_id = svc.get("id")
        cw_name = _get_cw_name(rw_id)
        if cw_name is None:
            continue
        result.append(
            MappedServiceItem(
                rw_service_id=rw_id,
                rw_name=svc.get("name", ""),
                cw_name=cw_name,
                price=svc.get("price") or 0.0,
                duration=svc.get("duration") or 0.0,
                count=svc.get("count") or 1,
            )
        )
    return result


def get_car_category_by_type_id(car_type_id: int) -> str:
    """Return the category name for a RocketWash ``car_type_id``.

    Raises:
        KeyError: If ``car_type_id`` is not in the mapping.
    """
    if car_type_id not in _CAR_TYPE_ID_TO_CATEGORY:
        raise KeyError(f"Unknown car_type_id: {car_type_id}")
    return _CAR_TYPE_ID_TO_CATEGORY[car_type_id]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_car_type_id(car_category: str) -> int:
    """Reverse lookup: category name → car_type_id."""
    reverse = {v: k for k, v in _CAR_TYPE_ID_TO_CATEGORY.items()}
    if car_category not in reverse:
        known = ", ".join(sorted(reverse))
        raise KeyError(f"Unknown car category: {car_category!r}. Known: {known}")
    return reverse[car_category]
