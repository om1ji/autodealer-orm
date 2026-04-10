# autodealer

Python ORM-обёртка над базой данных системы **АвтоДилер** (Firebird).

Предоставляет:
- Автоматически сгенерированные SQLAlchemy 2.0 модели для всех таблиц БД
- Django-подобный `QuerySet` API (`Model.objects.filter(...).all()`)
- Высокоуровневые функции для клиентов, автомобилей, заказ-нарядов и платежей

---

## Установка

```bash
pip install -r requirements.txt
```

На macOS также нужен клиент Firebird:
```bash
brew install firebird
```

С uv:
```bash
uv sync
```

---

## Настройка подключения

Через `.env` в корне проекта:

```env
DB_HOST=192.168.88.64
DB_PORT=3050
DB_DATABASE=C:\Program Files (x86)\AutoDealer\AutoDealer\Database\CW.fdb
DB_USER=SYSDBA
DB_PASSWORD=masterkey
DB_CHARSET=UTF8
```

Или явно в коде (вызов **до** использования моделей):

```python
from autodealer import configure_database

configure_database(
    host="192.168.88.64",
    port=3050,
    database=r"C:\path\to\AutoDealer.fdb",
    user="SYSDBA",
    password="masterkey",
    charset="UTF8",
)
```

---

## QuerySet API

```python
from autodealer.domain.bank import Bank

Bank.objects.all()
Bank.objects.filter(hidden=0).order_by('-name').limit(10)
Bank.objects.filter(name__icontains='сбер').first()
Bank.objects.get(bank_id=1)
Bank.objects.create(name='Тинькофф', bik='044525974')
Bank.objects.filter(hidden=1).update(hidden=0)
Bank.objects.filter(hidden=1).delete()
Bank.objects.filter(hidden=0).values('bank_id', 'name')
```

Поддерживаемые лукапы: `exact`, `contains`, `icontains`, `startswith`, `endswith`,
`gt`, `gte`, `lt`, `lte`, `in`, `isnull`.

---

## Высокоуровневые функции

### Клиенты (`autodealer.actions.client`)

```python
from autodealer.actions.client import (
    create_client,
    add_vehicle_to_client,
    get_client_vehicles,
    find_vehicle_by_regno,
)
from datetime import date

# Создать клиента
client_id = create_client(
    "Иванов Иван Иванович",
    phone="79991234567",
    birth=date(1990, 5, 15),
    discount_work=5.0,
)

# Добавить авто (идемпотентно по regno)
add_vehicle_to_client(
    client_id=client_id,
    make="Toyota",
    model_name="Camry",
    regno="А001ВС77",
    year=2020,
)

# Получить список авто
cars = get_client_vehicles(client_id)   # list[ModelLink]
car_link_id = cars[0].model_link_id     # передаётся в create_service_order
```

### Заказ-наряд (`autodealer.services`)

```python
from datetime import datetime, timedelta
from autodealer.services import create_service_order, get_service_order, ServiceOrderItem
from autodealer.actions.client import get_client_vehicles

now = datetime.now()
cars = get_client_vehicles(client_id=920)

doc_id = create_service_order(
    client_id=920,
    organization_id=1,
    document_out_tree_id=3,             # папка «АвтоМойка»
    date_start=now,
    date_finish=now + timedelta(hours=1),
    client_car=cars[0].model_link_id,   # привязка авто (опционально)
    notes="Комплексная мойка",
    service_order_suffix="К",
    items=[
        ServiceOrderItem("Комплекс",    price=2300.0, time_value=90, external_id="821460"),
        ServiceOrderItem("Вторая Фаза", price=800.0,  time_value=20, external_id="821462"),
    ],
)
print(doc_id)  # → document_out_id

# Прочитать обратно
order = get_service_order(doc_id)
print(order.summa, order.date_accept)
```

Цепочка записей в БД:
```
document_out → document_registry → document_out_header
    → document_service_detail (если передан client_car)
    → service_work × N
```

### Оплата (`autodealer.actions.payment`)

```python
from autodealer.actions.payment import (
    get_wallets, get_payment_types,
    create_payment, create_payment_split, get_payments,
    PaymentSplitItem,
)

# Справочники
wallets = get_wallets(organization_id=1)   # list[WalletInfo]
types   = get_payment_types()              # list[PaymentTypeInfo]

# Один платёж
payment_id = create_payment(
    document_out_id=doc_id,
    summa=3100.0,
    wallet_id=1,        # 1=Наличный расчет
    payment_type_id=1,  # 1=Наличный, 2=Безналичный, 7=Банковская карта
)

# Разбивка: наличные + карта
ids = create_payment_split(
    document_out_id=doc_id,
    parts=[
        PaymentSplitItem(wallet_id=1, payment_type_id=1, summa=1000.0),
        PaymentSplitItem(wallet_id=4, payment_type_id=7, summa=2100.0),
    ],
)

# Просмотр платежей
for p in get_payments(doc_id):
    print(p.payment_id, p.summa, p.payment_type_name)
```

Цепочка записей в БД:
```
payment → payment_out + payment_document
    → money_document_detail + money_document_payment
    → UPDATE document_out.date_payment
```

### Организации (`autodealer.services`)

```python
from autodealer.services import get_organization, list_organizations, create_organization

org = get_organization(1)
print(org.shortname, org.wallets)
wallet_id = org.wallet_id_by_name("наличн")

org = create_organization(
    "ООО СК-Авто",
    inn="1655012345",
    wallet_names=["Наличные", "Банковская карта"],
)
```

---

## Структура пакета

```
autodealer/
  connection.py       # configure_database(), session_scope(), Base
  queryset.py         # QuerySet, Manager — ORM API
  services.py         # create_service_order, get_service_order, create_organization, ...
  actions/
    client.py         # create_client, add_vehicle_to_client, get_client_vehicles, ...
    payment.py        # create_payment, create_payment_split, get_payments, get_wallets, ...
  domain/             # 286 автосгенерированных ORM-моделей (по одному файлу на таблицу)
  integration/
    rocketwash.py     # маппинг RocketWash → AutoDealer
  tools/
    generate_models.py  # регенерация domain/ из живой БД
```

---

## Генерация моделей

При изменении схемы БД:

```bash
python autodealer/tools/generate_models.py
```

Перезаписывает все файлы в `autodealer/domain/`.

---

## Документация

```bash
source venv/bin/activate
sphinx-build source docs
```

Открыть `docs/index.html`.

---

## Разработка и тесты

```bash
uv sync
uv run pytest
```

---

## Требования

- Python 3.11–3.13
- Firebird 3.x / 4.x (сервер)
- На macOS: `brew install firebird` (клиентская библиотека)
