Заказ-наряды (``autodealer.services``)
======================================

Высокоуровневые функции для работы с заказ-нарядами.
Каждая функция выполняет несколько INSERT-ов в одной транзакции — при ошибке полный rollback.

.. contents:: Содержание
   :local:
   :depth: 2

---

Создание заказ-наряда
----------------------

.. function:: autodealer.services.create_service_order(*, client_id, items, document_out_tree_id, organization_id, client_car=None, date_start, date_finish, created_by_user_id=1, notes=None, service_order_suffix=None)

   Создать заказ-наряд с услугами для клиента.

   Цепочка записей в БД::

       document_out
           ↓
       document_registry
           ↓
       document_out_header  (prefix="АВТ", state=2 «Черновик»)
           ↓
       document_service_detail  — только если передан client_car
           ↓
       service_work × N    — по одной записи на каждый ServiceOrderItem

   :param int client_id: PK клиента (``client.client_id``).
   :param list items: Список :class:`ServiceOrderItem`. Не может быть пустым.
   :param int document_out_tree_id: FK папки документов (``document_out_tree``).
   :param int organization_id: FK организации-исполнителя.
   :param int client_car: ``model_link.model_link_id`` — привязка авто (опционально).
   :param datetime date_start: Дата/время начала (``document_registry``).
   :param datetime date_finish: Дата/время окончания (``document_out.date_accept``,
       ``document_out_header.date_create``).
   :param int created_by_user_id: ``users.user_id`` исполнителя. По умолчанию ``1``.
   :param str notes: Примечание к заказ-наряду.
   :param str service_order_suffix: Суффикс номера (напр. ``"К"``). Префикс всегда ``"АВТ"``.
   :returns: ``document_out_id`` созданного заказ-наряда.
   :rtype: int
   :raises ValueError: Если ``items`` пустой.
   :raises sqlalchemy.exc.DatabaseError: При FK-нарушении.

   .. code-block:: python

      from datetime import datetime, timedelta
      from autodealer.services import create_service_order, ServiceOrderItem

      now = datetime.now()
      doc_id = create_service_order(
          client_id=920,
          organization_id=1,
          document_out_tree_id=3,
          date_start=now,
          date_finish=now + timedelta(hours=1),
          client_car=959,
          notes="Комплексная мойка",
          service_order_suffix="К",
          items=[
              ServiceOrderItem("Комплекс",    price=2300.0, time_value=90, external_id="821460"),
              ServiceOrderItem("Вторая Фаза", price=800.0,  time_value=20, external_id="821462"),
          ],
      )
      print(doc_id)  # → document_out_id

.. class:: autodealer.services.ServiceOrderItem

   Строка услуги в заказ-наряде.

   .. attribute:: name: str

      Название работы (макс. 255 символов).

   .. attribute:: price: float

      Цена за единицу.

   .. attribute:: time_value: float

      Длительность в минутах.

   .. attribute:: quantity: int

      Количество. По умолчанию ``1``.

   .. attribute:: external_id: str | None

      Внешний ID (напр. ``"821460"`` из RocketWash).

---

Чтение заказ-наряда
--------------------

.. function:: autodealer.services.get_service_order(document_out_id)

   Загрузить заказ-наряд со всеми строками услуг.

   :param int document_out_id: PK документа.
   :returns: :class:`ServiceOrder` или ``None`` если не найден.

   .. code-block:: python

      from autodealer.services import get_service_order

      order = get_service_order(42)
      print(order.summa, order.date_accept)
      for item in order.items:
          print(item.name, item.price)

.. class:: autodealer.services.ServiceOrder

   Агрегат заказ-наряда.

   .. attribute:: document_out_id: int
   .. attribute:: client_id: int | None
   .. attribute:: summa: float
   .. attribute:: date_accept: datetime | None
   .. attribute:: date_payment: datetime | None
   .. attribute:: document_number: int | None
   .. attribute:: date_create: datetime | None
   .. attribute:: client_car: int | None

      ``model_link_id`` привязанного авто.

   .. attribute:: items: list[ServiceOrderItem]

---

Создание из RocketWash
-----------------------

См. страницу :doc:`rocketwash`.

---

Константы
---------

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Константа
     - Значение
     - Описание
   * - ``_DOCUMENT_TYPE_SERVICE_ORDER``
     - ``11``
     - Тип документа «Заказ-наряд»
   * - ``_SERVICE_ORDER_PREFIX``
     - ``"АВТ"``
     - Префикс номера документа
   * - ``_DOCUMENT_STATE["Черновик"]``
     - ``2``
     - Статус при создании
   * - ``_METATABLE_DOCUMENT_OUT``
     - ``12``
     - ``document_registry.metatable_id``
