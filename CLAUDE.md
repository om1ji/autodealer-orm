# autodealer — контекст проекта

## Что это

Python ORM-обёртка над базой данных системы **АвтоДилер** (Firebird).
Пакет: `autodealer/`. Версия: 0.1.0.

## База данных

- **Сервер**: 192.168.88.64:3050 (Windows, Firebird)
- **Тестовая**: `C:\Program Files (x86)\AutoDealer\AutoDealer\Database\StOm1.fdb`
- **User**: SYSDBA / masterkey
- **Charset**: UTF8

## Структура пакета

```
autodealer/
  __init__.py         # реэкспорт из connection.py
  connection.py       # DatabaseConfig, get_engine(), session_scope(), Base, configure_database()
  queryset.py         # QuerySet, Manager — Django-like ORM API (Model.objects.filter(...))
  services.py         # create_service_order, get_service_order, delete_service_order,
                      # restore_service_order, get/create organization, ...
  actions/
    __init__.py
    client.py         # create_client, add_vehicle_to_client, get_client_vehicles,
                      # create_vehicle_for_client, get_or_create_mark/model/color, ...
    payment.py        # create_payment, create_payment_split, get_payments,
                      # delete_payment, get_wallets, get_payment_types,
                      # BOT_NOTE_MARKER, WalletInfo, PaymentTypeInfo, ...
    employee.py       # add_executor (привязка сотрудника к строке работы
                      # через brigade_structure)
  domain/
    __init__.py       # авто-импорт всех 288 моделей
    bank.py           # пример: class Bank(Base)
    ...               # по одному файлу на каждую таблицу StOm1.fdb
  integration/
    __init__.py
    rocketwash.py     # маппинги RW→AD: service_id → complex_work name,
                      # car_type_id/строка → категория/tree_id,
                      # resolve_complex_work — полный резолв услуги в справочник
  tools/
    __init__.py
    generate_models.py   # интроспектирует БД и перегенерирует domain/
    seed_test_db.py      # заполняет StOm1.fdb тестовыми данными (идемпотентно)
```

## Ключевые решения

- **Модели статичные** — генерируются один раз скриптом, не используют reflection при импорте
- **Стиль моделей** — SQLAlchemy 2.0, `Mapped[T]` / `mapped_column()` (Django-like явные поля)
- **QuerySet** — `Model.objects` — дескриптор `Manager` на `Base`, возвращает `QuerySet(Model)`
- **Типы Firebird** — sqlalchemy-firebird возвращает типы с префиксом `FB` (FBINTEGER, FBVARCHAR и т.д.) — в генераторе срезается через `.removeprefix("FB")`
- **Circular import** — `queryset.py` импортирует `session_scope`/`get_engine` лениво внутри методов; `Manager` навешивается на `Base` после определения обоих классов
- **GC warning** от драйвера Firebird при выходе — фиксится через `get_engine().dispose()` в `finally`
- **Блокировка в UI** — если документ открыт в окне АвтоДилера, `UPDATE/DELETE` упадёт с deadlock «update conflicts with concurrent update». Закройте документ — и транзакция пройдёт. Для тестов лучше работать с документами, которых нет в UI.

## Семантика полей (подводные камни)

Обнаруженные при сверке с ручными заказ-нарядами АвтоМойки:

- **`document_out.summa`** — сумма **ТОВАРОВ**, не общая. `NOT NULL`. Для заказ-наряда автомойки (только услуги) = 0. UI складывает `document_out.summa + document_service_detail.summa_work` — если не 0 в обоих, получается удвоение.
- **`service_work` — два режима**:
  - *Справочный*: `price=<цена>, time_value=NULL, work_source=3, rt_work_id=<service_complex_work_id>, name='Стандарт'/'Комплекс'/…`. Так создают UI и наш парсер через `ServiceOrderItem.complex_work_id`.
  - *Ручной*: `price=NULL, time_value=<цена>, work_source=NULL`. UI показывает сумму через `time_value * price_norm` при `price_norm=1`. Без `price_norm=1` — показывает 0.
- **`brigade_structure`** — реальная таблица связки «работа ↔ исполнитель». `executor` — это VIEW поверх неё, `INSERT` идёт только в `brigade_structure`.
- **Бух-проводки `payment_document` / `money_document_detail` / `money_document_payment`** — у ручных заказов АвтоМойки их **нет** (0/272 в проде). Они создаются в другом месте (закрытие смены, 1С). `create_payment` их НЕ создаёт — иначе двойной учёт.
- **`payment_action`** — обязательный журнал аудита платежей (`action_type`: 0=создан, 1=изменён, -1=удалён). `create_payment` пишет `action_type=0`.
- **`document_cargo`** — запись плательщика документа (`payer_id = client_id`). Создаётся у всех ручных заказов (285/285). Без неё UI может вести себя неожиданно при печати реквизитов.
- **Константы-дефолты** у ручных заказов АвтоМойки, которые теперь выставляются автоматически: `document_out.flag=2`, `document_service_detail.price_norm_id=5` (норма с множителем 1), `doc_date_end_section_link=1`, `guarante=<текст>`, `discount_work=0`, `summa_bonus=0`.
- **RW `car_type_id`** может содержать и устаревшие id (3/27/28/29) помимо актуальных (35/36/37/38). `autodealer.integration.rocketwash.resolve_car_category` понимает оба варианта + fallback по нормализованной строке `car_type`.

## Запуск

```bash
uv run python main.py
```

## Как перегенерировать модели

```bash
uv run python autodealer/tools/generate_models.py
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

### Заказ-наряд (`services.py`)

`client_car` — **обязательный** параметр: заказ-наряд нельзя создать без привязки авто клиента (на уровне функции стоит `ValueError` если передано `None`).

```python
from autodealer.services import (
    create_service_order, delete_service_order, restore_service_order,
    ServiceOrderItem,
)
from autodealer.integration.rocketwash import resolve_complex_work

# «Справочный» ServiceOrderItem — с привязкой к service_complex_work (единообразно с ручными):
resolved = resolve_complex_work(821459, car_type_id=37)  # "Стандарт" для Кат.02
cw_id, cw_name, _ = resolved or (None, None, None)

doc_id = create_service_order(
    client_id=920,
    organization_id=1,
    document_out_tree_id=3,              # папка «АвтоМойка»
    date_start=now,
    date_finish=now + timedelta(hours=1),
    client_car=959,                      # model_link_id — ОБЯЗАТЕЛЬНО
    notes="Комплексная мойка",
    service_order_suffix="К",
    items=[
        ServiceOrderItem(
            name=cw_name or "Мойка",
            price=600.0, time_value=20,
            external_id="821459",
            complex_work_id=cw_id,       # опционально — включает справочный режим
        ),
    ],
)

# soft-delete (state = -1, документ скрывается в UI)
delete_service_order(doc_id)
restore_service_order(doc_id)            # state ← 2 (Черновик)

# hard-delete (физический каскад по всем таблицам)
delete_service_order(doc_id, hard=True)  # ботовые платежи сносятся автоматически
```

Цепочка создаваемых записей:
`document_out` → `document_registry` → `document_out_header` → `document_service_detail` (всегда) → `service_work × N` → `document_cargo` (плательщик).

Ключевые поля:
- `document_out.summa` = 0 (сумма товаров; услуги уходят в `summa_work`)
- `document_out.date_accept` = `date_start`
- `document_out.flag` = 2, `summa_bonus` = 0 (константы)
- `document_out_header.date_create` = `date_start`, `state` = 2 («Черновик»), `prefix` = "АВТ"
- `document_service_detail.date_start` = `date_start`, `summa_work` = сумма всех позиций
- `document_service_detail.price_norm_id` = 5 (норма с множителем 1)
- `document_service_detail.guarante` — стандартный шаблон гарантии
- `document_cargo.payer_id` = `client_id`

`hard=True` при наличии **ручных** платежей (без маркера `BOT_NOTE_MARKER`) бросает `ValueError` — их нужно обработать вручную.

### Оплата заказ-наряда (`actions/payment.py`)

```python
from autodealer.actions.payment import (
    BOT_NOTE_MARKER,                             # "Добавлено ботом"
    get_wallets, get_payment_types, get_payments,
    create_payment, create_payment_split, PaymentSplitItem,
    delete_payment,
)

wallets = get_wallets(organization_id=1)        # list[WalletInfo]
types   = get_payment_types()                   # list[PaymentTypeInfo]

payment_id = create_payment(
    document_out_id=doc_id,
    summa=2300.0,
    wallet_id=1,        # 1=Наличный расчет, 3=Сбербанк, 4=ТБанк
    payment_type_id=1,  # 1=Наличный, 2=Безналичный, 7=Банковская карта, 14=Перевод на карту
)                       # в notes автоматически добавляется BOT_NOTE_MARKER

ids = create_payment_split(
    document_out_id=doc_id,
    parts=[
        PaymentSplitItem(wallet_id=1, payment_type_id=1, summa=1000.0),
        PaymentSplitItem(wallet_id=4, payment_type_id=7, summa=1300.0),
    ],
)

payments = get_payments(doc_id)                 # list[PaymentRecord]
delete_payment(payment_id)                      # каскадное удаление платежа
```

Цепочка записей (только то, что **реально** создаёт `create_payment`):
`payment` → `payment_out` → `payment_action` (action_type=0) → `UPDATE document_out.date_payment`.

`payment_document` / `money_document_detail` / `money_document_payment` намеренно **НЕ создаются** — у ручных заказов АвтоМойки их тоже нет (0/272). Эти проводки генерируются отдельно при закрытии смены / выгрузке в 1С. `_delete_payment_rows` оставляет `DELETE` на все таблицы — каскадное удаление остаётся совместимо со старыми записями.

### Исполнители (`actions/employee.py`)

```python
from autodealer.actions.employee import add_executor

# привязать сотрудника к строке работы
add_executor(service_work_id=1537, employee_id=8)
```

Пишет в `brigade_structure` (`executor` — это VIEW поверх неё, `INSERT` туда невозможен). Идемпотентна: если пара `(service_work_id, employee_id)` уже существует, возвращает её `brigade_structure_id` без нового INSERT.

### Клиенты и авто (`actions/client.py`)

```python
from autodealer.actions.client import create_client, add_vehicle_to_client, get_client_vehicles

client_id = create_client("Иванов Иван", phone="79991234567")
add_vehicle_to_client(client_id, make="Toyota", model_name="Camry", regno="А001ВС77")
cars = get_client_vehicles(client_id)  # list[ModelLink]
```

`add_vehicle_to_client` возвращает `model_detail_id`.
`get_client_vehicles` возвращает `list[ModelLink]` — у каждого есть `.model_link_id` (нужен для `client_car`).

### Организации (`services.py`)

```python
from autodealer.services import get_organization, list_organizations, create_organization

org = get_organization(1)           # OrganizationInfo | None
orgs = list_organizations()         # list[OrganizationInfo]

org = create_organization(
    "ООО СК-Авто",
    shortname="СК-Авто",
    inn="1655012345",
    wallet_names=["Наличные", "Банковская карта"],
)
```

## Зависимости

- SQLAlchemy ≥ 2.0
- sqlalchemy-firebird ≥ 2.1
- firebird-driver ≥ 2.0
- python-dotenv ≥ 1.0
- Sphinx ≥ 8.0 (документация)
