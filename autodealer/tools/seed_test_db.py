"""Populate StOm1.fdb with realistic test data.

Run from the project root:
    python autodealer/tools/seed_test_db.py

Inserts are idempotent: existing rows (matched by PK) are skipped.
Only tables without FK dependencies are seeded here (80 tables).
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from autodealer.connection import configure_database, get_engine  # noqa: E402
from autodealer.domain.bank import Bank  # noqa: E402
from autodealer.domain.mark import Mark  # noqa: E402
from autodealer.domain.color import Color  # noqa: E402
from autodealer.domain.country import Country  # noqa: E402
from autodealer.domain.currency import Currency  # noqa: E402
from autodealer.domain.department import Department  # noqa: E402
from autodealer.domain.job import Job  # noqa: E402
from autodealer.domain.unit import Unit  # noqa: E402
from autodealer.domain.payment_type import PaymentType  # noqa: E402
from autodealer.domain.operation_type import OperationType  # noqa: E402
from autodealer.domain.operation_state import OperationState  # noqa: E402
from autodealer.domain.document_type import DocumentType  # noqa: E402
from autodealer.domain.goods_type import GoodsType  # noqa: E402
from autodealer.domain.producer import Producer  # noqa: E402
from autodealer.domain.stage import Stage  # noqa: E402
from autodealer.domain.repair_type import RepairType  # noqa: E402
from autodealer.domain.material import Material  # noqa: E402
from autodealer.domain.packing import Packing  # noqa: E402
from autodealer.domain.car_body_type import CarBodyType  # noqa: E402
from autodealer.domain.car_engine_type import CarEngineType  # noqa: E402
from autodealer.domain.car_fuel_type import CarFuelType  # noqa: E402
from autodealer.domain.car_gearbox_type import CarGearboxType  # noqa: E402
from autodealer.domain.car_brake_type import CarBrakeType  # noqa: E402
from autodealer.domain.source_info import SourceInfo  # noqa: E402
from autodealer.domain.price_norm import PriceNorm  # noqa: E402
from autodealer.domain.directory_registry import DirectoryRegistry  # noqa: E402
from autodealer.domain.organization import Organization  # noqa: E402
from autodealer.domain.client_tree import ClientTree  # noqa: E402
from autodealer.domain.client import Client  # noqa: E402
from autodealer.domain.model_detail import ModelDetail  # noqa: E402
from autodealer.domain.model_link import ModelLink  # noqa: E402
from autodealer.domain.shop_nomenclature_tree import ShopNomenclatureTree  # noqa: E402
from autodealer.domain.shop_nomenclature import ShopNomenclature  # noqa: E402
from autodealer.domain.service_complex_work import ServiceComplexWork  # noqa: E402
from autodealer.domain.service_complex_work_item import ServiceComplexWorkItem  # noqa: E402
from autodealer.domain.service_complex_work_tree import ServiceComplexWorkTree  # noqa: E402

configure_database(
    host="192.168.88.64",
    port=3050,
    database=r"C:\Program Files (x86)\AutoDealer\AutoDealer\Database\StOm1.fdb",
    user="SYSDBA",
    password="masterkey",
    charset="UTF8",
)

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

BANKS = [
    dict(
        bank_id=1,
        name="Сбербанк",
        bik="044525225",
        korr_account="30101810400000000225",
        address="г. Москва, ул. Вавилова, 19",
        hidden=0,
    ),
    dict(
        bank_id=2,
        name="ВТБ",
        bik="044525187",
        korr_account="30101810700000000187",
        address="г. Москва, Дегтярный пер., 11",
        hidden=0,
    ),
    dict(
        bank_id=3,
        name="Газпромбанк",
        bik="044525823",
        korr_account="30101810200000000823",
        address="г. Москва, ул. Намёткина, 16",
        hidden=0,
    ),
    dict(
        bank_id=4,
        name="Альфа-Банк",
        bik="044525593",
        korr_account="30101810200000000593",
        address="г. Москва, ул. Каланчёвская, 27",
        hidden=0,
    ),
    dict(
        bank_id=5,
        name="Россельхозбанк",
        bik="044525111",
        korr_account="30101810200000000111",
        address="г. Москва, Гагаринский пер., 3",
        hidden=0,
    ),
    dict(
        bank_id=6,
        name="Тинькофф Банк",
        bik="044525974",
        korr_account="30101810145250000974",
        address="г. Москва, 1-й Волоколамский пр., 10",
        hidden=0,
    ),
    dict(
        bank_id=7,
        name="Райффайзенбанк",
        bik="044525700",
        korr_account="30101810200000000700",
        address="г. Москва, ул. Троицкая, 17/1",
        hidden=0,
    ),
    dict(
        bank_id=8,
        name="Росбанк",
        bik="044525256",
        korr_account="30101810000000000256",
        address="г. Москва, ул. Маши Порываевой, 34",
        hidden=0,
    ),
    dict(
        bank_id=9,
        name="Промсвязьбанк",
        bik="044525555",
        korr_account="30101810600000000555",
        address="г. Москва, Смирновская ул., 10/22",
        hidden=0,
    ),
    dict(
        bank_id=10,
        name="МКБ",
        bik="044525659",
        korr_account="30101810600000000659",
        address="г. Москва, Луков пер., 2/1 с.1",
        hidden=0,
    ),
    dict(
        bank_id=11,
        name="Совкомбанк",
        bik="043469743",
        korr_account="30101810200000000743",
        address="г. Кострома, пр. Текстильщиков, 46",
        hidden=0,
    ),
    dict(
        bank_id=12,
        name="Банк «Открытие»",
        bik="044525297",
        korr_account="30101810300000000297",
        address="г. Москва, ул. Летниковская, 2/4",
        hidden=0,
    ),
    dict(
        bank_id=13,
        name="Уралсиб",
        bik="044525790",
        korr_account="30101810100000000790",
        address="г. Москва, ул. Ефремова, 8",
        hidden=0,
    ),
    dict(
        bank_id=14,
        name="Ситибанк",
        bik="044525202",
        korr_account="30101810300000000202",
        address="г. Москва, Гасетный пер., 17-19/1",
        hidden=0,
    ),
    dict(
        bank_id=15,
        name="Абсолют Банк",
        bik="044525976",
        korr_account="30101810500000000976",
        address="г. Москва, Цветной б-р, 18",
        hidden=1,
    ),
]

MARKS = [
    dict(mark_id=1, name="Toyota", hidden=0),
    dict(mark_id=2, name="Honda", hidden=0),
    dict(mark_id=3, name="BMW", hidden=0),
    dict(mark_id=4, name="Mercedes", hidden=0),
    dict(mark_id=5, name="Audi", hidden=0),
    dict(mark_id=6, name="Volkswagen", hidden=0),
    dict(mark_id=7, name="Ford", hidden=0),
    dict(mark_id=8, name="Hyundai", hidden=0),
    dict(mark_id=9, name="Kia", hidden=0),
    dict(mark_id=10, name="Lada", hidden=0),
    dict(mark_id=11, name="Renault", hidden=0),
    dict(mark_id=12, name="Skoda", hidden=0),
]

COLORS = [
    dict(color_id=1, name="Белый", color_value=0xFFFFFF, hidden=0),
    dict(color_id=2, name="Чёрный", color_value=0x000000, hidden=0),
    dict(color_id=3, name="Серебристый", color_value=0xC0C0C0, hidden=0),
    dict(color_id=4, name="Серый", color_value=0x808080, hidden=0),
    dict(color_id=5, name="Красный", color_value=0xFF0000, hidden=0),
    dict(color_id=6, name="Синий", color_value=0x0000FF, hidden=0),
    dict(color_id=7, name="Зелёный", color_value=0x008000, hidden=0),
    dict(color_id=8, name="Бежевый", color_value=0xF5F5DC, hidden=0),
    dict(color_id=9, name="Коричневый", color_value=0x8B4513, hidden=0),
    dict(color_id=10, name="Жёлтый", color_value=0xFFFF00, hidden=0),
]

COUNTRIES = [
    dict(country_id=1, name="Россия", country_code="RU", hidden=0),
    dict(country_id=2, name="Германия", country_code="DE", hidden=0),
    dict(country_id=3, name="Япония", country_code="JP", hidden=0),
    dict(country_id=4, name="США", country_code="US", hidden=0),
    dict(country_id=5, name="Китай", country_code="CN", hidden=0),
    dict(country_id=6, name="Южная Корея", country_code="KR", hidden=0),
    dict(country_id=7, name="Франция", country_code="FR", hidden=0),
    dict(country_id=8, name="Италия", country_code="IT", hidden=0),
]

CURRENCIES = [
    dict(
        currency_id=1, shortname="руб", fullname="Российский рубль", code=643, gender=1
    ),
    dict(currency_id=2, shortname="USD", fullname="Доллар США", code=840, gender=2),
    dict(currency_id=3, shortname="EUR", fullname="Евро", code=978, gender=2),
    dict(currency_id=4, shortname="CNY", fullname="Китайский юань", code=156, gender=2),
]

DEPARTMENTS = [
    dict(department_id=1, name="Отдел продаж", hidden=0),
    dict(department_id=2, name="Сервисный центр", hidden=0),
    dict(department_id=3, name="Склад запчастей", hidden=0),
    dict(department_id=4, name="Бухгалтерия", hidden=0),
    dict(department_id=5, name="Администрация", hidden=0),
    dict(department_id=6, name="Отдел кузовного ремонта", hidden=0),
]

JOBS = [
    dict(job_id=1, name="Директор", hidden=0),
    dict(job_id=2, name="Менеджер по продажам", hidden=0),
    dict(job_id=3, name="Мастер-приёмщик", hidden=0),
    dict(job_id=4, name="Автомеханик", hidden=0),
    dict(job_id=5, name="Кладовщик", hidden=0),
    dict(job_id=6, name="Бухгалтер", hidden=0),
    dict(job_id=7, name="Маляр", hidden=0),
    dict(job_id=8, name="Кузовщик", hidden=0),
]

UNITS = [
    dict(unit_id=1, shortname="шт", fullname="Штука", hidden=0, integer_value=1),
    dict(unit_id=2, shortname="л", fullname="Литр", hidden=0, integer_value=0),
    dict(unit_id=3, shortname="кг", fullname="Килограмм", hidden=0, integer_value=0),
    dict(unit_id=4, shortname="м", fullname="Метр", hidden=0, integer_value=0),
    dict(unit_id=5, shortname="компл", fullname="Комплект", hidden=0, integer_value=1),
    dict(unit_id=6, shortname="н/ч", fullname="Нормо-час", hidden=0, integer_value=0),
]

PAYMENT_TYPES = [
    dict(payment_type_id=1, name="Наличные", hidden=0),
    dict(payment_type_id=2, name="Безналичные", hidden=0),
    dict(payment_type_id=3, name="Карта", hidden=0),
    dict(payment_type_id=4, name="СБП", hidden=0),
    dict(payment_type_id=5, name="Кредит", hidden=0),
]

OPERATION_TYPES = [
    dict(operation_type_id=1, name="Техническое обслуживание", hidden=0),
    dict(operation_type_id=2, name="Ремонт", hidden=0),
    dict(operation_type_id=3, name="Диагностика", hidden=0),
    dict(operation_type_id=4, name="Кузовной ремонт", hidden=0),
    dict(operation_type_id=5, name="Шиномонтаж", hidden=0),
]

OPERATION_STATES = [
    dict(operation_state_id=1, name="Новый", hidden=0),
    dict(operation_state_id=2, name="В работе", hidden=0),
    dict(operation_state_id=3, name="Готов", hidden=0),
    dict(operation_state_id=4, name="Выдан", hidden=0),
    dict(operation_state_id=5, name="Отменён", hidden=0),
]

DOCUMENT_TYPES = [
    dict(
        document_type_id=1,
        name="Заказ-наряд",
        shortname="ЗН",
        flag=1,
        payment_direction=0,
    ),
    dict(document_type_id=2, name="Счёт", shortname="СЧ", flag=2, payment_direction=1),
    dict(
        document_type_id=3,
        name="Расходная накладная",
        shortname="РН",
        flag=3,
        payment_direction=0,
    ),
    dict(
        document_type_id=4,
        name="Приходная накладная",
        shortname="ПН",
        flag=4,
        payment_direction=1,
    ),
    dict(
        document_type_id=5,
        name="Акт выполненных работ",
        shortname="АВР",
        flag=5,
        payment_direction=0,
    ),
]

GOODS_TYPES = [
    dict(goods_type_id=1, name="Запасные части", hidden=0),
    dict(goods_type_id=2, name="Расходные материалы", hidden=0),
    dict(goods_type_id=3, name="Аксессуары", hidden=0),
    dict(goods_type_id=4, name="Масла и жидкости", hidden=0),
    dict(goods_type_id=5, name="Шины и диски", hidden=0),
]

PRODUCERS = [
    dict(producer_id=1, name="Bosch", hidden=0),
    dict(producer_id=2, name="Denso", hidden=0),
    dict(producer_id=3, name="NGK", hidden=0),
    dict(producer_id=4, name="Mobil", hidden=0),
    dict(producer_id=5, name="Castrol", hidden=0),
    dict(producer_id=6, name="Shell", hidden=0),
    dict(producer_id=7, name="Mann Filter", hidden=0),
    dict(producer_id=8, name="Febi", hidden=0),
    dict(producer_id=9, name="SKF", hidden=0),
    dict(producer_id=10, name="Gates", hidden=0),
]

STAGES = [
    dict(stage_id=1, name="Приёмка", required=1, hidden=0, position_no=1),
    dict(stage_id=2, name="Диагностика", required=0, hidden=0, position_no=2),
    dict(stage_id=3, name="Ремонт", required=1, hidden=0, position_no=3),
    dict(stage_id=4, name="Контроль качества", required=1, hidden=0, position_no=4),
    dict(stage_id=5, name="Выдача", required=1, hidden=0, position_no=5),
]

REPAIR_TYPES = [
    dict(repair_type_id=1, name="Гарантийный", hidden=0),
    dict(repair_type_id=2, name="Коммерческий", hidden=0),
    dict(repair_type_id=3, name="Страховой", hidden=0),
    dict(repair_type_id=4, name="Внутренний", hidden=0),
]

MATERIALS = [
    dict(material_id=1, name="Сталь", hidden=0),
    dict(material_id=2, name="Алюминий", hidden=0),
    dict(material_id=3, name="Пластик", hidden=0),
    dict(material_id=4, name="Резина", hidden=0),
    dict(material_id=5, name="Стекло", hidden=0),
]

PACKINGS = [
    dict(packing_id=1, name="Штука", hidden=0),
    dict(packing_id=2, name="Упаковка", hidden=0),
    dict(packing_id=3, name="Коробка", hidden=0),
    dict(packing_id=4, name="Канистра", hidden=0),
]

CAR_BODY_TYPES = [
    dict(car_body_type_id=1, name="Седан", hidden=0),
    dict(car_body_type_id=2, name="Хэтчбек", hidden=0),
    dict(car_body_type_id=3, name="Универсал", hidden=0),
    dict(car_body_type_id=4, name="Внедорожник", hidden=0),
    dict(car_body_type_id=5, name="Кроссовер", hidden=0),
    dict(car_body_type_id=6, name="Минивэн", hidden=0),
    dict(car_body_type_id=7, name="Купе", hidden=0),
    dict(car_body_type_id=8, name="Пикап", hidden=0),
]

CAR_ENGINE_TYPES = [
    dict(car_engine_type_id=1, name="Бензиновый", hidden=0),
    dict(car_engine_type_id=2, name="Дизельный", hidden=0),
    dict(car_engine_type_id=3, name="Гибридный", hidden=0),
    dict(car_engine_type_id=4, name="Электрический", hidden=0),
    dict(car_engine_type_id=5, name="Газовый", hidden=0),
]

CAR_FUEL_TYPES = [
    dict(car_fuel_type_id=1, name="АИ-92", hidden=0),
    dict(car_fuel_type_id=2, name="АИ-95", hidden=0),
    dict(car_fuel_type_id=3, name="АИ-98", hidden=0),
    dict(car_fuel_type_id=4, name="Дизель", hidden=0),
    dict(car_fuel_type_id=5, name="Газ", hidden=0),
    dict(car_fuel_type_id=6, name="Электро", hidden=0),
]

CAR_GEARBOX_TYPES = [
    dict(car_gearbox_type_id=1, name="МКПП", hidden=0),
    dict(car_gearbox_type_id=2, name="АКПП", hidden=0),
    dict(car_gearbox_type_id=3, name="Вариатор", hidden=0),
    dict(car_gearbox_type_id=4, name="Робот", hidden=0),
]

CAR_BRAKE_TYPES = [
    dict(car_brake_type_id=1, name="Дисковые", hidden=0),
    dict(car_brake_type_id=2, name="Барабанные", hidden=0),
    dict(car_brake_type_id=3, name="Смешанные", hidden=0),
]

SOURCE_INFOS = [
    dict(source_info_id=1, name="Сайт", hidden=0),
    dict(source_info_id=2, name="Рекомендация", hidden=0),
    dict(source_info_id=3, name="Реклама", hidden=0),
    dict(source_info_id=4, name="Повторный визит", hidden=0),
    dict(source_info_id=5, name="Социальные сети", hidden=0),
]

PRICE_NORMS = [
    dict(price_norm_id=1, name="Базовая", price=1.0, hidden=0),
    dict(price_norm_id=2, name="Оптовая", price=0.9, hidden=0),
    dict(price_norm_id=3, name="Дилерская", price=0.85, hidden=0),
    dict(price_norm_id=4, name="Розничная", price=1.1, hidden=0),
]

# ---------------------------------------------------------------------------
# service_complex_work — категории, группы, работы
# ID соответствуют маппингу в integration/rocketwash.py
# ---------------------------------------------------------------------------

SERVICE_COMPLEX_WORK_TREES = [
    dict(service_complex_work_tree_id=11, name="Кат.01", parent_id=None),
    dict(service_complex_work_tree_id=15, name="Кат.02", parent_id=None),
    dict(service_complex_work_tree_id=16, name="Кат.03", parent_id=None),
    dict(service_complex_work_tree_id=17, name="Кат.04", parent_id=None),
]

SERVICE_COMPLEX_WORK_ITEMS = [
    # Кат.01 → tree_id=11
    dict(
        service_complex_work_item_id=101,
        service_complex_work_tree_id=11,
        name="Мойка кузова",
    ),
    dict(
        service_complex_work_item_id=102,
        service_complex_work_tree_id=11,
        name="Уборка салона",
    ),
    # Кат.02 → tree_id=15
    dict(
        service_complex_work_item_id=103,
        service_complex_work_tree_id=15,
        name="Полировка",
    ),
    # Кат.03 → tree_id=16
    dict(
        service_complex_work_item_id=104,
        service_complex_work_tree_id=16,
        name="Химчистка",
    ),
    # Кат.04 → tree_id=17
    dict(
        service_complex_work_item_id=105,
        service_complex_work_tree_id=17,
        name="Детейлинг",
    ),
]

SERVICE_COMPLEX_WORKS = [
    # Мойка кузова (item=101)
    dict(
        service_complex_work_id=1001,
        service_complex_work_item_id=101,
        name="Экспресс мойка",
        price=600,
        time_value=20,
        quantity=1,
        discount_work=0,
    ),
    dict(
        service_complex_work_id=1002,
        service_complex_work_item_id=101,
        name="Комплексная мойка",
        price=1200,
        time_value=40,
        quantity=1,
        discount_work=0,
    ),
    dict(
        service_complex_work_id=1003,
        service_complex_work_item_id=101,
        name="Мойка двигателя",
        price=800,
        time_value=30,
        quantity=1,
        discount_work=0,
    ),
    # Уборка салона (item=102)
    dict(
        service_complex_work_id=1004,
        service_complex_work_item_id=102,
        name="Пылесос салона",
        price=400,
        time_value=15,
        quantity=1,
        discount_work=0,
    ),
    dict(
        service_complex_work_id=1005,
        service_complex_work_item_id=102,
        name="Протирка торпедо",
        price=300,
        time_value=10,
        quantity=1,
        discount_work=0,
    ),
    # Полировка (item=103)
    dict(
        service_complex_work_id=1006,
        service_complex_work_item_id=103,
        name="Полировка кузова",
        price=4500,
        time_value=120,
        quantity=1,
        discount_work=0,
    ),
    dict(
        service_complex_work_id=1007,
        service_complex_work_item_id=103,
        name="Нанесение воска",
        price=2000,
        time_value=60,
        quantity=1,
        discount_work=0,
    ),
    # Химчистка (item=104)
    dict(
        service_complex_work_id=1008,
        service_complex_work_item_id=104,
        name="Химчистка сидений",
        price=3500,
        time_value=90,
        quantity=1,
        discount_work=0,
    ),
    dict(
        service_complex_work_id=1009,
        service_complex_work_item_id=104,
        name="Химчистка потолка",
        price=2500,
        time_value=60,
        quantity=1,
        discount_work=0,
    ),
    # Детейлинг (item=105)
    dict(
        service_complex_work_id=1010,
        service_complex_work_item_id=105,
        name="Нанесение керамики",
        price=15000,
        time_value=240,
        quantity=1,
        discount_work=0,
    ),
    dict(
        service_complex_work_id=1011,
        service_complex_work_item_id=105,
        name="Антигравийная плёнка",
        price=8000,
        time_value=180,
        quantity=1,
        discount_work=0,
    ),
]

# directory_registry: metatable_id=1 означает ORGANIZATION (из таблицы metatable)
# create_user_id=1 — системный пользователь, уже существует в StOm1.fdb
DIRECTORY_REGISTRIES = [
    dict(directory_registry_id=100, metatable_id=1, create_user_id=1, change_user_id=1),
    dict(directory_registry_id=101, metatable_id=1, create_user_id=1, change_user_id=1),
]

CLIENT_TREES = [
    dict(client_tree_id=1, name="Физические лица", parent_id=None),
    dict(client_tree_id=2, name="Юридические лица", parent_id=None),
    dict(client_tree_id=3, name="VIP-клиенты", parent_id=1),
]

# directory_registry: metatable_id=3 → CLIENT (из таблицы metatable)
DIRECTORY_REGISTRIES_CLIENT = [
    dict(directory_registry_id=200, metatable_id=3, create_user_id=1, change_user_id=1),
    dict(directory_registry_id=201, metatable_id=3, create_user_id=1, change_user_id=1),
    dict(directory_registry_id=202, metatable_id=3, create_user_id=1, change_user_id=1),
    dict(directory_registry_id=203, metatable_id=3, create_user_id=1, change_user_id=1),
]

CLIENTS = [
    dict(
        client_id=100,
        directory_registry_id=200,
        client_tree_id=1,
        fullname="Иванов Иван Иванович",
        shortname="Иванов И.И.",
        face=0,
        hidden=0,
        discount=5.0,
        discount_work=0.0,
        source_info_id=1,
    ),
    dict(
        client_id=101,
        directory_registry_id=201,
        client_tree_id=1,
        fullname="Петрова Мария Сергеевна",
        shortname="Петрова М.С.",
        face=0,
        hidden=0,
        discount=0.0,
        discount_work=0.0,
        source_info_id=2,
    ),
    dict(
        client_id=102,
        directory_registry_id=202,
        client_tree_id=2,
        fullname='ООО "Ромашка"',
        shortname="Ромашка",
        inn="7712345678",
        kpp="771201001",
        face=1,
        hidden=0,
        discount=10.0,
        discount_work=5.0,
        source_info_id=3,
    ),
    dict(
        client_id=103,
        directory_registry_id=203,
        client_tree_id=1,
        fullname="Сидоров Алексей Петрович",
        shortname="Сидоров А.П.",
        face=0,
        hidden=1,
        discount=0.0,
        discount_work=0.0,
    ),
]

# directory_registry: metatable_id=4 → MODEL_DETAIL
DIRECTORY_REGISTRIES_MODEL = [
    dict(directory_registry_id=300, metatable_id=4, create_user_id=1, change_user_id=1),
    dict(directory_registry_id=301, metatable_id=4, create_user_id=1, change_user_id=1),
    dict(directory_registry_id=302, metatable_id=4, create_user_id=1, change_user_id=1),
]

# model_id: используем существующие модели из продакшн-данных в StOm1.fdb
# Toyota Camry ≈ model_id уточним по факту; используем первые доступные
# mark Toyota = mark_id из нашего seed; но model уже загружен из базы (948 записей)
# Возьмём model_id=7 (Audi A3), 8 (Audi A4), 100 (что-то из середины)
MODEL_DETAILS = [
    dict(
        model_detail_id=100,
        directory_registry_id=300,
        model_id=7,  # Audi A3
        color_id=1,  # Белый
        regno="А123ВС77",
        vin="WAUZZZ8P9BA123456",
        year_of_production="2020-06-15",
        car_engine_type_id=1,  # Бензиновый
        car_gearbox_type_id=2,  # АКПП
        car_body_type_id=1,  # Седан
    ),
    dict(
        model_detail_id=101,
        directory_registry_id=301,
        model_id=8,  # Audi A4
        color_id=2,  # Чёрный
        regno="В456ГД99",
        vin="WAUZZZ8P9BA654321",
        year_of_production="2019-03-01",
        car_engine_type_id=2,  # Дизельный
        car_gearbox_type_id=1,  # МКПП
        car_body_type_id=3,  # Универсал
    ),
    dict(
        model_detail_id=102,
        directory_registry_id=302,
        model_id=100,  # любая модель из БД
        color_id=3,  # Серебристый
        regno="С789ЕЖ150",
        year_of_production="2018-01-01",
    ),
]

SHOP_NOMENCLATURE_TREES = [
    dict(shop_nomenclature_tree_id=1, name="Запасные части", parent_id=None),
    dict(shop_nomenclature_tree_id=2, name="Расходные материалы", parent_id=None),
    dict(shop_nomenclature_tree_id=3, name="Масла и жидкости", parent_id=2),
    dict(shop_nomenclature_tree_id=4, name="Фильтры", parent_id=1),
    dict(shop_nomenclature_tree_id=5, name="Тормозная система", parent_id=1),
]

# directory_registry: metatable_id=13 → SHOP_NOMENCLATURE
DIRECTORY_REGISTRIES_NOMENCLATURE = [
    dict(
        directory_registry_id=400, metatable_id=13, create_user_id=1, change_user_id=1
    ),
    dict(
        directory_registry_id=401, metatable_id=13, create_user_id=1, change_user_id=1
    ),
    dict(
        directory_registry_id=402, metatable_id=13, create_user_id=1, change_user_id=1
    ),
    dict(
        directory_registry_id=403, metatable_id=13, create_user_id=1, change_user_id=1
    ),
    dict(
        directory_registry_id=404, metatable_id=13, create_user_id=1, change_user_id=1
    ),
]

# tax_schemes_id=1 (Общее налогообложение) — единственная запись в StOm1.fdb
SHOP_NOMENCLATURES = [
    dict(
        shop_nomenclature_id=100,
        directory_registry_id=400,
        shop_nomenclature_tree_id=4,  # Фильтры
        fullname="Фильтр масляный Bosch 0986AF0",
        shortname="Ф.масл.Bosch",
        number_manufacture="0986AF0",
        number_original="06A115561B",
        goods_type_id=1,  # Запасные части
        unit_id=1,  # шт
        tax_schemes_id=1,
        tax_schemes_material_id=1,
        producer_id=1,  # Bosch
        country_id=1,  # Россия
        packing_id=1,  # Штука
        default_cost=850.00,
        default_margin=30.00,
        default_count=1,
    ),
    dict(
        shop_nomenclature_id=101,
        directory_registry_id=401,
        shop_nomenclature_tree_id=4,  # Фильтры
        fullname="Фильтр воздушный Mann C30130",
        shortname="Ф.возд.Mann",
        number_manufacture="C30130",
        goods_type_id=1,
        unit_id=1,
        tax_schemes_id=1,
        tax_schemes_material_id=1,
        producer_id=7,  # Mann Filter
        default_cost=620.00,
        default_margin=25.00,
        default_count=1,
    ),
    dict(
        shop_nomenclature_id=102,
        directory_registry_id=402,
        shop_nomenclature_tree_id=3,  # Масла и жидкости
        fullname="Масло моторное Mobil 5W-30 4л",
        shortname="Mobil 5W-30 4л",
        number_manufacture="152559",
        goods_type_id=4,  # Масла и жидкости
        unit_id=2,  # л
        tax_schemes_id=1,
        tax_schemes_material_id=1,
        producer_id=4,  # Mobil
        default_cost=2800.00,
        default_margin=20.00,
        default_count=4,
    ),
    dict(
        shop_nomenclature_id=103,
        directory_registry_id=403,
        shop_nomenclature_tree_id=5,  # Тормозная система
        fullname="Колодки тормозные передние Bosch 0986424723",
        shortname="Кол.торм.перед.Bosch",
        number_manufacture="0986424723",
        goods_type_id=1,
        unit_id=5,  # компл
        tax_schemes_id=1,
        tax_schemes_material_id=1,
        producer_id=1,  # Bosch
        default_cost=3200.00,
        default_margin=28.00,
        default_count=1,
    ),
    dict(
        shop_nomenclature_id=104,
        directory_registry_id=404,
        shop_nomenclature_tree_id=2,  # Расходные материалы
        fullname="Антифриз Shell Helix 1л",
        shortname="Антифриз Shell 1л",
        goods_type_id=2,  # Расходные материалы
        unit_id=2,  # л
        tax_schemes_id=1,
        tax_schemes_material_id=1,
        producer_id=6,  # Shell
        default_cost=350.00,
        default_margin=35.00,
        default_count=1,
    ),
]

MODEL_LINKS = [
    dict(model_link_id=100, model_detail_id=100, hidden=0, default_car=1),
    dict(model_link_id=101, model_detail_id=101, hidden=0, default_car=1),
    dict(model_link_id=102, model_detail_id=102, hidden=0, default_car=0),
]

ORGANIZATIONS = [
    dict(
        organization_id=100,
        directory_registry_id=100,
        fullname='ООО "Тест Авто"',
        shortname="Тест Авто",
        inn="7701234567",
        kpp="770101001",
        ogrn="1027700000000",
        face=0,
        hidden=0,
        nds=1,
        can_sale=1,
        can_buy=1,
        date_closing_period="2020-01-01",
    ),
    dict(
        organization_id=101,
        directory_registry_id=101,
        fullname="ИП Иванов Иван Иванович",
        shortname="ИП Иванов",
        inn="771234567890",
        face=1,
        hidden=0,
        nds=0,
        can_sale=1,
        can_buy=0,
        date_closing_period="2020-01-01",
    ),
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def seed(model, pk_attr: str, rows: list[dict], label: str) -> None:
    existing = {getattr(obj, pk_attr) for obj in model.objects.all()}
    inserted = sum(
        1
        for row in rows
        if row[pk_attr] not in existing and model.objects.create(**row) is not None
    )
    skipped = len(rows) - inserted
    print(f"  {label:<35} вставлено {inserted:>3} / пропущено {skipped:>3}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

TABLES = [
    (Bank, "bank_id", BANKS, "bank"),
    (Mark, "mark_id", MARKS, "mark"),
    (Color, "color_id", COLORS, "color"),
    (Country, "country_id", COUNTRIES, "country"),
    (Currency, "currency_id", CURRENCIES, "currency"),
    (Department, "department_id", DEPARTMENTS, "department"),
    (Job, "job_id", JOBS, "job"),
    (Unit, "unit_id", UNITS, "unit"),
    (PaymentType, "payment_type_id", PAYMENT_TYPES, "payment_type"),
    (OperationType, "operation_type_id", OPERATION_TYPES, "operation_type"),
    (OperationState, "operation_state_id", OPERATION_STATES, "operation_state"),
    (DocumentType, "document_type_id", DOCUMENT_TYPES, "document_type"),
    (GoodsType, "goods_type_id", GOODS_TYPES, "goods_type"),
    (Producer, "producer_id", PRODUCERS, "producer"),
    (Stage, "stage_id", STAGES, "stage"),
    (RepairType, "repair_type_id", REPAIR_TYPES, "repair_type"),
    (Material, "material_id", MATERIALS, "material"),
    (Packing, "packing_id", PACKINGS, "packing"),
    (CarBodyType, "car_body_type_id", CAR_BODY_TYPES, "car_body_type"),
    (CarEngineType, "car_engine_type_id", CAR_ENGINE_TYPES, "car_engine_type"),
    (CarFuelType, "car_fuel_type_id", CAR_FUEL_TYPES, "car_fuel_type"),
    (CarGearboxType, "car_gearbox_type_id", CAR_GEARBOX_TYPES, "car_gearbox_type"),
    (CarBrakeType, "car_brake_type_id", CAR_BRAKE_TYPES, "car_brake_type"),
    (SourceInfo, "source_info_id", SOURCE_INFOS, "source_info"),
    (PriceNorm, "price_norm_id", PRICE_NORMS, "price_norm"),
    # Зависимые таблицы (порядок важен)
    (
        DirectoryRegistry,
        "directory_registry_id",
        DIRECTORY_REGISTRIES,
        "directory_registry (org)",
    ),
    (Organization, "organization_id", ORGANIZATIONS, "organization"),
    (ClientTree, "client_tree_id", CLIENT_TREES, "client_tree"),
    (
        DirectoryRegistry,
        "directory_registry_id",
        DIRECTORY_REGISTRIES_CLIENT,
        "directory_registry (client)",
    ),
    (Client, "client_id", CLIENTS, "client"),
    (
        DirectoryRegistry,
        "directory_registry_id",
        DIRECTORY_REGISTRIES_MODEL,
        "directory_registry (model)",
    ),
    (ModelDetail, "model_detail_id", MODEL_DETAILS, "model_detail"),
    (ModelLink, "model_link_id", MODEL_LINKS, "model_link"),
    (
        ShopNomenclatureTree,
        "shop_nomenclature_tree_id",
        SHOP_NOMENCLATURE_TREES,
        "shop_nomenclature_tree",
    ),
    (
        DirectoryRegistry,
        "directory_registry_id",
        DIRECTORY_REGISTRIES_NOMENCLATURE,
        "directory_registry (nomenclature)",
    ),
    (ShopNomenclature, "shop_nomenclature_id", SHOP_NOMENCLATURES, "shop_nomenclature"),
    (
        ServiceComplexWorkTree,
        "service_complex_work_tree_id",
        SERVICE_COMPLEX_WORK_TREES,
        "service_complex_work_tree",
    ),
    (
        ServiceComplexWorkItem,
        "service_complex_work_item_id",
        SERVICE_COMPLEX_WORK_ITEMS,
        "service_complex_work_item",
    ),
    (
        ServiceComplexWork,
        "service_complex_work_id",
        SERVICE_COMPLEX_WORKS,
        "service_complex_work",
    ),
]


def main() -> None:
    print("=== Заполнение StOm1.fdb тестовыми данными ===\n")
    for model, pk_attr, rows, label in TABLES:
        seed(model, pk_attr, rows, label)
    print("\nГотово.")


if __name__ == "__main__":
    try:
        main()
    finally:
        get_engine().dispose()
