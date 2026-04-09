# autodealer

Python ORM-обёртка над базой данных системы АвтоДилер (Firebird).

## Установка

```bash
pip install -r requirements.txt
```

На macOS также нужен клиент Firebird:
```bash
brew install firebird
```

---

## Настройка подключения

### Через `.env`

```env
DB_HOST=192.168.88.64
DB_PORT=3050
DB_DATABASE=C:\Program Files (x86)\AutoDealer\AutoDealer\Database\StOm1.fdb
DB_USER=SYSDBA
DB_PASSWORD=masterkey
DB_CHARSET=UTF8
```

### Или явно в коде

```python
from autodealer.connection import configure_database

configure_database(
    host="192.168.88.64",
    port=3050,
    database=r"C:\Program Files (x86)\AutoDealer\AutoDealer\Database\StOm1.fdb",
    user="SYSDBA",
    password="masterkey",
    charset="UTF8",
)
```

> `configure_database` нужно вызвать **до** импорта моделей, если `.env` не используется.

---

## Модели

Каждая таблица БД представлена отдельным классом в `autodealer/domain/`.
Имена полей совпадают с именами колонок в БД (строчные).

```python
from autodealer.domain.bank import Bank
from autodealer.domain.users import Users
# или всё сразу:
from autodealer.domain import Bank, Users
```

Посмотреть список колонок модели:

```python
print(Bank.__table__.columns.keys())
# ['bank_id', 'name', 'bik', 'korr_account', 'address', 'notes', 'hidden']
```

---

## QuerySet API

Каждая модель имеет менеджер `objects` с Django-подобным интерфейсом.

### Чтение

```python
# Все записи
banks = Bank.objects.all()

# Количество
Bank.objects.count()

# Первый / последний
Bank.objects.first()
Bank.objects.last()

# Проверка существования
Bank.objects.exists()
```

### Фильтрация

```python
# Точное совпадение
Bank.objects.filter(hidden=0)
Bank.objects.exclude(hidden=1)

# Цепочки
Bank.objects.filter(hidden=0).order_by('name').limit(10)
```

#### Поддерживаемые лукапы

| Лукап | SQL |
|---|---|
| `field=value` / `field__exact=value` | `= value` |
| `field__contains="текст"` | `LIKE %текст%` |
| `field__icontains="текст"` | `ILIKE %текст%` |
| `field__startswith="А"` | `LIKE А%` |
| `field__endswith="ов"` | `LIKE %ов` |
| `field__gt=5` | `> 5` |
| `field__gte=5` | `>= 5` |
| `field__lt=5` | `< 5` |
| `field__lte=5` | `<= 5` |
| `field__in=[1, 2, 3]` | `IN (1, 2, 3)` |
| `field__isnull=True` | `IS NULL` |

### Сортировка и пагинация

```python
# ASC / DESC (префикс -)
Bank.objects.order_by('name')
Bank.objects.order_by('-name')

# Пагинация
Bank.objects.limit(20).offset(40)
```

### get() — одна запись

```python
from autodealer.queryset import DoesNotExist, MultipleObjectsReturned

try:
    bank = Bank.objects.get(bank_id=1)
except DoesNotExist:
    print("Не найдено")
except MultipleObjectsReturned:
    print("Найдено несколько записей")
```

### values() — список словарей

```python
# Все поля
Bank.objects.all().values()

# Только нужные поля
Bank.objects.filter(hidden=0).values('bank_id', 'name')
# [{'bank_id': 1, 'name': 'Сбербанк'}, ...]
```

### Запись

```python
# Создание
bank = Bank.objects.create(name="Тинькофф", bik="044525974", hidden=0)
print(bank.bank_id)  # ID присвоен после сохранения

# Bulk update
Bank.objects.filter(hidden=1).update(hidden=0)

# Bulk delete
Bank.objects.filter(hidden=1).delete()
```

### Итерация

```python
for bank in Bank.objects.filter(hidden=0):
    print(bank.name)
```

---

## Low-level: session_scope

Для сложных запросов, транзакций или операций с несколькими моделями:

```python
from sqlalchemy import select
from autodealer.connection import session_scope
from autodealer.domain.bank import Bank

with session_scope() as session:
    result = session.execute(
        select(Bank).where(Bank.hidden == 0).order_by(Bank.name)
    ).scalars().all()
```

---

## High-level API (`autodealer.services`)

Модуль `autodealer/services.py` содержит готовые функции для типичных бизнес-операций.
Они скрывают внутренние цепочки таблиц (`directory_registry`, триггеры, FK) и обходят
известный баг `sqlalchemy-firebird` с VARCHAR-фильтрами через raw SQL.

> **Важно:** все функции из `services` используют raw `text()` SQL для строковых параметров —
> это обходной путь для бага `sqlalchemy-firebird visit_VARCHAR` (версии 2.1 + SQLAlchemy 2.0.48).

---

### Организации

#### `list_organizations` — список всех организаций

```python
from autodealer.services import list_organizations

orgs = list_organizations()
for org in orgs:
    print(org)
# OrganizationInfo(id=2, name='СК-Авто', inn='1655012345', wallets=3)
```

#### `get_organization` — получить по ID

```python
from autodealer.services import get_organization

org = get_organization(2)
org.organization_id  # 2
org.fullname         # 'ООО СК-Авто Казань'
org.inn              # '1655012345'
org.wallets          # [{"wallet_id": 7, "name": "Наличные"}, ...]

# Найти wallet_id по части названия
wallet_id = org.wallet_id_by_name("налич")   # → 7
wallet_id = org.wallet_id_by_name("карта")   # → 8
wallet_id = org.wallet_id_by_name("сбп")     # → 9
```

#### `create_organization` — создать организацию с кошельками

```python
from autodealer.services import create_organization

org = create_organization(
    "ООО СК-Авто Казань",
    shortname="СК-Авто",
    inn="1655012345",
    kpp="165501001",
    ogrn="1021600000000",
    address="г. Казань, ул. Скрябина 8к1",
    face=0,                                      # 0=ЮЛ, 1=ИП
    wallet_names=["Наличные", "Банковская карта", "СБП"],
)
print(org.organization_id)  # → новый ID
print(org.wallets)
# [{"wallet_id": 7, "name": "Наличные"}, ...]
```

---

### Клиенты

Клиент в AutoDealer — цепочка: `DirectoryRegistry (metatable=3)` → `Client` → `Contact`.

Дерево папок (`client_tree_id`): 1=Физические лица, 2=Юридические лица, 3=VIP-клиенты.

#### `find_client_by_phone` — поиск по телефону

```python
from autodealer.services import find_client_by_phone

client_id = find_client_by_phone("79991697059")  # → int | None
```

#### `create_client` — создать клиента

Атомарно создаёт `DirectoryRegistry` → `Client` → `Contact`.

```python
from datetime import date
from autodealer.services import create_client

client_id = create_client(
    "Иванов Иван Иванович",
    phone="79991234567",        # опционально
    email="ivan@example.com",   # опционально
    birth=date(1990, 5, 15),    # опционально
    sex=1,                      # 1=муж, 2=жен, None=не указан
    discount=5.0,               # скидка на товары %
    discount_work=0.0,          # скидка на работы %
    client_tree_id=1,           # 1=Физлица (по умолчанию)
)
```

---

### Автомобили

Авто в AutoDealer: `mark` → `model` → `DirectoryRegistry (metatable=4)` → `model_detail` → `model_link` (привязка к клиенту).

#### Lookup-функции

```python
from autodealer.services import (
    get_or_create_mark,
    get_or_create_model,
    get_or_create_color,
    find_vehicle_by_regno,
    find_vehicle_by_vin,
)

mark_id  = get_or_create_mark("Toyota")           # → int
model_id = get_or_create_model(mark_id, "Camry")  # → int
color_id = get_or_create_color("Белый")           # → int | None

# Поиск по госномеру или VIN
model_detail_id = find_vehicle_by_regno("А001ВС77")   # → int | None
model_detail_id = find_vehicle_by_vin("WAUZZZ8P9BA")  # → int | None
```

#### `add_vehicle_to_client` — добавить авто по имени марки/модели

Высокоуровневая функция: принимает строки марки и модели, сама делает lookup/create
для `mark`, `model`, `color`, затем создаёт `model_detail` + `model_link`.
Идемпотентна по госномеру — если авто с таким `regno` уже есть, возвращает его `model_detail_id`.

```python
from autodealer.services import add_vehicle_to_client

md_id = add_vehicle_to_client(
    client_id=42,
    make="Toyota",
    model_name="Camry",
    regno="А001ВС77",   # опционально
    vin="WAUZZZ8P9BA",  # опционально
    year=2020,          # опционально
    color="Белый",      # опционально
    default_car=True,
)
# → model_detail_id (int)
```

#### `create_vehicle_for_client` — низкоуровневое создание (нужны готовые ID)

```python
from datetime import date
from autodealer.services import create_vehicle_for_client

link = create_vehicle_for_client(
    client_id=42,
    model_id=model_id,               # из get_or_create_model()
    regno="А001ВС77",
    vin="WAUZZZ8P9BA",
    year_of_production=date(2020, 1, 1),
    color_id=color_id,               # из get_or_create_color()
    default_car=True,
)
print(link.model_link_id)
```

---

### Каталог услуг (`service_common_work`)

Справочник работ — дерево папок + записи услуг с ценами.
`bar_code = "rw:{id}"` используется как идемпотентный ключ для синхронизации из RocketWash.

```python
from autodealer.services import find_service_by_barcode, get_or_create_service

# Найти по barcode
sid = find_service_by_barcode("rw:821460")  # → int | None

# Создать или найти (идемпотентно)
sid = get_or_create_service(
    name="Экспресс мойка",
    price=700.0,
    time_value=20.0,        # минуты
    bar_code="rw:821455",
    tree_id=5,              # папка в дереве (опционально)
)
```

> `service_common_work` (каталог) и `service_work` (строки документа) не связаны FK.
> При создании заказ-наряда имя и цена **копируются** из каталога в строку документа.

---

### Заказ-наряд (`document_type_id = 11`)

Структура документа:

```
document_out              — тип, клиент, сумма, дата приёма
    ↓
document_out_header       — номер документа, дата создания, исполнитель
    ↓
document_service_detail   — привязка авто (model_link_id), пробег
    ↓
service_work × N          — строки услуг (название, цена, время, кол-во)
```

#### `ServiceOrderItem` — строка услуги

```python
from autodealer.services import ServiceOrderItem

item = ServiceOrderItem(
    name="Комплекс (1-я фаза)",
    price=1800.0,
    time_value=90.0,        # минуты
    quantity=1,
    external_id="rw:821460",  # внешний ID для идемпотентности
)
```

#### `create_service_order` — создать заказ-наряд

```python
from autodealer.services import create_service_order, ServiceOrderItem

doc_id = create_service_order(
    client_id=42,
    model_link_id=7,        # привязка авто (опционально)
    items=[
        ServiceOrderItem("Экспресс мойка", price=600, time_value=20),
        ServiceOrderItem("Чернение резины", price=150, time_value=10),
    ],
    date_accept=datetime(2026, 3, 31, 10, 0),  # опционально, default = now()
    created_by_user_id=1,   # исполнитель
)
print(doc_id)  # document_out_id
```

#### `ServiceOrder` — агрегат для чтения

```python
from autodealer.services import get_service_order

order = get_service_order(doc_id)
# ServiceOrder(id=2, client=42, summa=750, items=2)

order.document_out_id   # int
order.client_id         # int
order.summa             # float
order.date_accept       # datetime
order.date_payment      # datetime | None
order.document_number   # int | None  (номер из document_out_header)
order.date_create       # datetime | None
order.model_link_id     # int | None  (привязанное авто)
order.items             # list[ServiceOrderItem]

for item in order.items:
    print(f"{item.name}: {item.price} руб, {item.time_value} мин")
```

---

### Планы (GraphQL / упрощение API)

Для будущего GraphQL API все публичные функции `services.py` возвращают простые объекты
(не SQLAlchemy-сущности), что упрощает сериализацию:

| Функция | Возвращает |
|---|---|
| `list_organizations` | `list[OrganizationInfo]` |
| `get_organization` | `OrganizationInfo \| None` |
| `create_organization` | `OrganizationInfo` |
| `find_client_by_phone` | `int \| None` (client_id) |
| `create_client` | `int` (client_id) |
| `add_vehicle_to_client` | `int` (model_detail_id) |
| `get_or_create_mark` | `int` (mark_id) |
| `get_or_create_model` | `int` (model_id) |
| `get_or_create_color` | `int \| None` |
| `find_vehicle_by_regno` | `int \| None` (model_detail_id) |
| `find_vehicle_by_vin` | `int \| None` |
| `create_vehicle_for_client` | `ModelLink` |
| `find_service_by_barcode` | `int \| None` |
| `get_or_create_service` | `int` (service_common_work_id) |
| `create_service_order` | `int` (document_out_id) |
| `get_service_order` | `ServiceOrder \| None` |

---

## Документация

Документация собирается через [Sphinx](https://www.sphinx-doc.org/) в папку `docs/`.

```bash
source venv/bin/activate
venv/bin/sphinx-build source docs
```

После сборки открыть `docs/index.html` в браузере.

Исходники документации — в `source/` (`.rst`-файлы и `conf.py`).

---

## Генерация моделей

Модели генерируются автоматически из схемы живой БД:

```bash
python autodealer/tools/generate_models.py
```

Скрипт подключается к БД, интроспектирует все таблицы и создаёт (перезаписывает) файлы в `autodealer/domain/`. Запускать при изменении схемы БД.
