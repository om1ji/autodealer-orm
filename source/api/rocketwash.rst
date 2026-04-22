Интеграция с RocketWash
=======================

Модуль ``autodealer.integration.rocketwash`` обеспечивает маппинг между сущностями
RocketWash и справочниками AutoDealer, а также высокоуровневые функции создания
заказ-нарядов напрямую из данных RocketWash.

.. contents:: Содержание
   :local:
   :depth: 2

---

Маппинги
--------

Категории автомобилей
~~~~~~~~~~~~~~~~~~~~~

RocketWash использует числовой ``car_type_id``, AutoDealer — строковые категории.

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - RocketWash ``car_type_id``
     - Категория
     - Пример авто
   * - 36
     - Кат.01
     - Седан / хетчбэк
   * - 37
     - Кат.02
     - Внедорожник / кроссовер
   * - 38
     - Кат.03
     - Микроавтобус
   * - 35
     - Кат.04
     - Крупный внедорожник / минивэн

Категории → дерево комплексных работ AutoDealer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Каждой категории соответствует ``service_complex_work_tree_id`` в Firebird:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Категория
     - ``service_complex_work_tree_id``
   * - Кат.01
     - 11
   * - Кат.02
     - 15
   * - Кат.03
     - 16
   * - Кат.04
     - 17

Услуги RocketWash → ``service_complex_work.name``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Маппинг конкретных ``service_id`` RocketWash к названиям в справочнике AutoDealer.
Услуги без аналога в AutoDealer (``Мойка ДВС``, ``Очистка дисков`` и др.) молча
пропускаются при создании заказ-наряда.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - RocketWash ``service_id``
     - ``service_complex_work.name`` в AutoDealer
   * - 821455 / 821457
     - Экспресс мойка
   * - 821459
     - Стандарт
   * - 821460
     - Комплекс
   * - 821461
     - Премиум Комплекс
   * - 821462
     - Вторая Фаза
   * - 821463
     - Кварцевое покрытие
   * - 821464
     - Восковое покрытие
   * - 821465
     - Чернение резины
   * - 821466
     - Силикон на уплотнители арок и дверей
   * - 821467
     - Мойка колеса (1шт.)
   * - 821469
     - Продувка воздухом ручек и зеркал
   * - 821472
     - Комплексная уборка салона
   * - 821473
     - Уборка багажника
   * - 821474
     - Влажная уборка салона
     - 821475
     - Очистка стекл
   * - 821476
     - Пылесос салона
   * - 821477
     - Полировка пластика
   * - 821478
     - Кондиционер Кожи Салона
   * - 821479
     - Чистка ковриков (1 шт.)
   * - 821520
     - Покрытие Антидождь

---

Вспомогательные функции (``autodealer.integration.rocketwash``)
----------------------------------------------------------------

.. function:: autodealer.integration.rocketwash.resolve_complex_work(rw_service_id, car_type_id=None, car_type=None)

   Полный резолв услуги RocketWash в запись ``service_complex_work``
   АвтоДилера. Ключевая функция для создания заказ-нарядов в
   «справочном» режиме (с ``rt_work_id`` и каноническим именем работы).

   Алгоритм:

   1. ``rw_service_id`` → канонический ``name`` через внутренний маппинг
      (только для услуг, присутствующих в обеих системах).
   2. ``car_type_id`` / ``car_type`` → категория через
      :func:`resolve_car_category`.
   3. Категория → ``service_complex_work_tree_id``.
   4. В дереве ищется запись с совпадающим ``name``.

   :param int rw_service_id: ``services.id`` из RocketWash.
   :param int car_type_id: ``reservations.car_type_id`` — и актуальный
       (35/36/37/38), и устаревшие значения (3/27/28/29).
   :param str car_type: Строка ``reservations.car_type`` — fallback,
       когда ``car_type_id`` не в маппинге.
   :returns: Кортеж ``(service_complex_work_id, name, price)`` или ``None``.

   .. code-block:: python

      from autodealer.integration.rocketwash import resolve_complex_work

      resolve_complex_work(821459, car_type_id=37)         # → (94, "Стандарт", 1200.0)
      resolve_complex_work(821459, car_type_id=27)         # → тот же результат (устаревший id)
      resolve_complex_work(821459, car_type="Кат. 2")      # → то же (по строке)
      resolve_complex_work(999999, car_type_id=37)         # → None (нет в маппинге)

.. function:: autodealer.integration.rocketwash.resolve_car_category(car_type_id=None, car_type=None)

   Определить категорию АвтоДилера по RW ``car_type_id`` и/или строке
   ``car_type``. Сначала ищет по id, потом fallback через нормализованную
   строку (``"Кат. 2"`` → ``"Кат.02"``).

   :returns: ``"Кат.01"`` / ``"Кат.02"`` / ``"Кат.03"`` / ``"Кат.04"``
       или ``None`` если не удалось определить.

   .. code-block:: python

      from autodealer.integration.rocketwash import resolve_car_category

      resolve_car_category(27)                 # → "Кат.02"
      resolve_car_category(99, "Кат. 2")       # → "Кат.02" (fallback)
      resolve_car_category(99, "мусор")        # → None

.. function:: autodealer.integration.rocketwash.get_car_category_by_type_id(car_type_id)

   Возвращает строку категории по ``car_type_id`` RocketWash.
   Старая версия — выбрасывает ``KeyError`` на неизвестные id. Для
   нового кода предпочтительнее :func:`resolve_car_category`.

   :raises KeyError: Если ``car_type_id`` неизвестен.

   .. code-block:: python

      from autodealer.integration.rocketwash import get_car_category_by_type_id

      get_car_category_by_type_id(36)   # → "Кат.01"
      get_car_category_by_type_id(35)   # → "Кат.04"

.. function:: autodealer.integration.rocketwash.get_complex_work_tree_id(rocketwash_category)

   Возвращает ``service_complex_work_tree_id`` AutoDealer для категории RocketWash.

   :raises KeyError: Если категория неизвестна.

   .. code-block:: python

      from autodealer.integration.rocketwash import get_complex_work_tree_id

      get_complex_work_tree_id("Кат.01")   # → 11
      get_complex_work_tree_id("Кат.04")   # → 17

.. function:: autodealer.integration.rocketwash.resolve_complex_work_tree_id(rocketwash_category)

   То же, что :func:`get_complex_work_tree_id`, но возвращает ``None`` для неизвестных
   категорий вместо исключения. Удобно при обработке данных в batch-режиме.

.. function:: autodealer.integration.rocketwash.map_reservation_services(services_detail)

   Маппит список услуг из JSON резервации RocketWash в ``MappedServiceItem``.
   Услуги без аналога в AutoDealer молча пропускаются.

   :param list[dict] services_detail: Распарсенный список из ``reservations.services_detail``.
       Каждый элемент должен содержать ключи ``"id"``, ``"name"``, ``"price"``,
       ``"duration"``, ``"count"``.
   :returns: Список :class:`MappedServiceItem`.

   .. code-block:: python

      import json
      from autodealer.integration.rocketwash import map_reservation_services

      raw = json.loads(reservation_row["services_detail"])
      items = map_reservation_services(raw)
      for item in items:
          print(item.cw_name, item.price)

.. function:: autodealer.integration.rocketwash.get_services_for_car_category(car_category, *, db_path=..., exclude_no_price=True)

   Загружает все услуги RocketWash с ценами для заданной категории авто из ``rocketwash.db``.

   :param str car_category: Категория, напр. ``"Кат.01"``.
   :param Path db_path: Путь к ``rocketwash.db``. По умолчанию — ``../RocketWash-parser/rocketwash.db``.
   :param bool exclude_no_price: Пропустить услуги без цены (по умолчанию ``True``).
   :returns: Список :class:`RocketWashService`.
   :raises FileNotFoundError: Если ``rocketwash.db`` не найден.

   .. code-block:: python

      from autodealer.integration.rocketwash import get_services_for_car_category

      services = get_services_for_car_category("Кат.02")
      for s in services:
          print(s.name, s.price)

---

Типы данных
-----------

.. class:: autodealer.integration.rocketwash.RocketWashService

   Услуга RocketWash с ценой для конкретной категории авто.

   .. attribute:: service_id: int
   .. attribute:: name: str
   .. attribute:: category: str

      Категория услуги (напр. ``"01. МОЙКА и КОМПЛЕКСЫ"``).

   .. attribute:: car_type_id: int
   .. attribute:: car_category: str

      Строковая категория авто (напр. ``"Кат.01"``).

   .. attribute:: price: float | None
   .. attribute:: duration: float | None

      Длительность в минутах.

.. class:: autodealer.integration.rocketwash.MappedServiceItem

   Услуга RocketWash, смаппированная на AutoDealer ``service_complex_work``.

   .. attribute:: rw_service_id: int
   .. attribute:: rw_name: str

      Оригинальное название в RocketWash.

   .. attribute:: cw_name: str

      Название в ``service_complex_work`` AutoDealer.

   .. attribute:: price: float
   .. attribute:: duration: float

      Длительность в минутах.

   .. attribute:: count: int
