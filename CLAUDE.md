# autodealer — контекст проекта

## Что это

Python ORM-обёртка над базой данных системы **АвтоДилер** (Firebird).
Пакет: `autodealer/`. Версия: 0.0.1.

## База данных

- **Сервер**: 192.168.88.64:3050 (Windows, Firebird)
- **Тестовая**: `C:\Program Files (x86)\AutoDealer\AutoDealer\Database\StOm1.fdb`
- **User**: SYSDBA / masterkey
- **Charset**: UTF8
- `.env` сейчас указывает на `StOm1.fdb`

## Структура пакета

```
autodealer/
  connection.py       # DatabaseConfig, get_engine(), session_scope(), Base, configure_database()
  queryset.py         # QuerySet, Manager — Django-like ORM API (Model.objects.filter(...))
  services.py         # create_service_order, get_service_order, create_payment (thin wrapper)
  __init__.py         # реэкспорт из connection.py
  actions/
    client.py         # create_client, add_vehicle_to_client, get_client_vehicles, ...
    payment.py        # create_payment, create_payment_split, get_payments, get_wallets, ...
  domain/
    __init__.py       # авто-импорт всех 286 моделей
    bank.py           # пример: class Bank(Base)
    users.py          # ...
    ...               # по одному файлу на каждую таблицу StOm1.fdb
  tools/
    __init__.py
    generate_models.py  # интроспектирует БД и перегенерирует domain/
```

## Ключевые решения

- **Модели статичные** — генерируются один раз скриптом, не используют reflection при импорте
- **Стиль моделей** — SQLAlchemy 2.0, `Mapped[T]` / `mapped_column()` (Django-like явные поля)
- **QuerySet** — `Model.objects` — дескриптор `Manager` на `Base`, возвращает `QuerySet(Model)`
- **Типы Firebird** — sqlalchemy-firebird возвращает типы с префиксом `FB` (FBINTEGER, FBVARCHAR и т.д.) — в генераторе срезается через `.removeprefix("FB")`
- **Circular import** — `queryset.py` импортирует `session_scope`/`get_engine` лениво внутри методов; `Manager` навешивается на `Base` после определения обоих классов
- **GC warning** от драйвера Firebird при выходе — фиксится через `get_engine().dispose()` в `finally`

## Как перегенерировать модели

```bash
python autodealer/tools/generate_models.py
```

Перезаписывает все файлы в `autodealer/domain/`.

## QuerySet API (кратко)

```python
Bank.objects.all()
Bank.objects.filter(hidden=0).order_by('-name').limit(10)
Bank.objects.filter(name__icontains='сбер').first()
Bank.objects.get(bank_id=1)
Bank.objects.create(name='...', bik='...')
Bank.objects.filter(hidden=1).update(hidden=0)
Bank.objects.filter(hidden=1).delete()
Bank.objects.values('bank_id', 'name')
```

## High-level функции (`services.py`, `actions/`)

### Заказ-наряд

```python
from autodealer.services import create_service_order, ServiceOrderItem

doc_id = create_service_order(
    client_id=920,
    organization_id=1,
    document_out_tree_id=3,       # папка «АвтоМойка»
    date_start=now,
    date_finish=now + timedelta(hours=1),
    client_car=959,               # model_link_id
    notes="Комплексная мойка",
    service_order_suffix="К",
    items=[ServiceOrderItem("Мойка", price=600.0, time_value=20)],
)
```

Цепочка в БД: `document_out` → `document_registry` → `document_out_header` → `document_service_detail` (если передан `client_car`) → `service_work × N`.

### Оплата заказ-наряда (`actions/payment.py`)

```python
from autodealer.actions.payment import (
    get_wallets, get_payment_types, get_payments,
    create_payment, create_payment_split, PaymentSplitItem,
)

# Справочники
wallets = get_wallets(organization_id=1)        # list[WalletInfo]
types   = get_payment_types()                   # list[PaymentTypeInfo]

# Один платёж
payment_id = create_payment(
    document_out_id=doc_id,
    summa=2300.0,
    wallet_id=1,        # 1=Наличный расчет, 3=Сбербанк, 4=ТБанк
    payment_type_id=1,  # 1=Наличный, 2=Безналичный, 7=Банковская карта
)

# Разбивка: часть наличными, часть картой
ids = create_payment_split(
    document_out_id=doc_id,
    parts=[
        PaymentSplitItem(wallet_id=1, payment_type_id=1, summa=1000.0),
        PaymentSplitItem(wallet_id=4, payment_type_id=7, summa=1300.0),
    ],
)

# Чтение платежей
payments = get_payments(doc_id)                 # list[PaymentRecord]
```

Цепочка: `payment` → `payment_out` + `payment_document` + `money_document_detail` (accounting_item_id=3 «Поступление от клиента») + `money_document_payment` + `UPDATE document_out.date_payment`.

### Клиенты и авто (`actions/client.py`)

```python
from autodealer.actions.client import create_client, add_vehicle_to_client, get_client_vehicles

client_id = create_client("Иванов Иван", phone="79991234567")
add_vehicle_to_client(client_id, make="Toyota", model_name="Camry", regno="А001ВС77")
cars = get_client_vehicles(client_id)  # list[ModelLink]
```

## Зависимости

- SQLAlchemy 2.0.44
- sqlalchemy-firebird 2.1
- firebird-driver 2.0.2
- python-dotenv 1.2.1
- Sphinx (документация)

## venv

```bash
source venv/bin/activate
```
