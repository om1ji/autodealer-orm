# Контракт: `create_service_order`

**Расположение:** `autodealer/services.py`

---

## Сигнатура

```python
def create_service_order(
    *,
    client_id: int,
    items: list[ServiceOrderItem],
    document_out_tree_id: int,
    organization_id: int,
    client_car: int | None = None,
    date_start: datetime,
    date_finish: datetime,
    created_by_user_id: int = 1,
    notes: str | None = None,
    service_order_suffix: str | None = None,
) -> int:
```

Все аргументы — только keyword-only (после `*`).

---

## Аргументы

| Аргумент | Тип | Обязательный | Описание |
|---|---|---|---|
| `client_id` | `int` | да | PK клиента (`client.client_id`) |
| `items` | `list[ServiceOrderItem]` | да | Строки услуг. Не может быть пустым |
| `document_out_tree_id` | `int` | да | FK в `document_out_tree` — папка документа |
| `organization_id` | `int` | да | FK в `organization` — организация-исполнитель |
| `client_car` | `int \| None` | нет | `model_link.model_link_id` — привязка авто. Если передан, создаётся `document_service_detail` |
| `date_start` | `datetime` | да | Дата/время начала (записывается в `document_registry`) |
| `date_finish` | `datetime` | да | Дата/время окончания / приёма (`document_out.date_accept`, `document_out_header.date_create`) |
| `created_by_user_id` | `int` | нет | `users.user_id` исполнителя. По умолчанию `1` (системный) |
| `notes` | `str \| None` | нет | Примечание к заказ-наряду (`document_out_header.notes`) |
| `service_order_suffix` | `str \| None` | нет | Суффикс номера документа (напр. `"К"`). Префикс всегда `"АВТ"` |

---

## Возвращаемое значение

`int` — `document_out_id` созданного заказ-наряда.

---

## Исключения

| Исключение | Условие |
|---|---|
| `ValueError` | `items` пустой список |
| `sqlalchemy.exc.DatabaseError` | FK-нарушение (несуществующий `document_out_tree_id`, `organization_id`, `client_id` и т.д.) |

---

## Что создаётся в БД

```
document_out               — документ (тип=11, клиент, сумма, date_accept)
    ↓
document_registry          — метазапись для документа (metatable_id=12)
    ↓
document_out_header        — заголовок (номер, дата, исполнитель, prefix="АВТ", state=2)
    ↓
document_service_detail    — привязка авто (только если передан client_car)
    ↓
service_work × N           — строки услуг (name, price, time_value, quantity, external_id)
```

Всё в одной транзакции — при любой ошибке полный rollback.

---

## `ServiceOrderItem`

```python
@dataclass
class ServiceOrderItem:
    name: str           # Название работы (макс. 255 символов)
    price: float        # Цена за единицу
    time_value: float   # Длительность в минутах
    quantity: int = 1   # Количество
    external_id: str | None = None  # Внешний ID (напр. "821460" из RocketWash)
```

---

## Константы (зашиты в функцию)

| Константа | Значение | Описание |
|---|---|---|
| `document_type_id` | `11` | Тип документа «Заказ-наряд» |
| `prefix` | `"АВТ"` | Префикс номера |
| `state` | `2` | Статус «Черновик» |
| `metatable_id` | `12` | `document_registry.metatable_id` для документов |

---

## Пример

```python
from datetime import datetime, timedelta
from autodealer.services import create_service_order, ServiceOrderItem
from autodealer.actions.client import get_client_vehicles

now = datetime.now()

# Получить model_link_id машины клиента
cars = get_client_vehicles(client_id=855)
car_link_id = cars[0].model_link_id  # 959

doc_id = create_service_order(
    client_id=855,
    organization_id=1,
    document_out_tree_id=5,           # уточнить в document_out_tree
    date_start=now,
    date_finish=now + timedelta(hours=1),
    client_car=car_link_id,
    notes="Комплексная мойка",
    service_order_suffix="К",
    items=[
        ServiceOrderItem("Комплекс",       price=2300.0, time_value=90, external_id="821460"),
        ServiceOrderItem("Вторая Фаза",    price=800.0,  time_value=20, external_id="821462"),
        ServiceOrderItem("Кварцевое покрытие", price=1000.0, time_value=40, external_id="821463"),
    ],
)
print(doc_id)  # → document_out_id
```

---

## Связанные функции

| Функция | Модуль | Описание |
|---|---|---|
| `create_service_order_from_rocketwash_services` | `autodealer.services` | Создаёт заказ из `rw_service_ids` + `car_type_id` |
| `create_service_order_from_rocketwash_category` | `autodealer.services` | Создаёт заказ по категории RocketWash (все работы) |
| `get_client_vehicles` | `autodealer.actions.client` | Возвращает `list[ModelLink]` для клиента |
| `get_service_order` | `autodealer.services` | Читает созданный заказ-наряд по `document_out_id` |
