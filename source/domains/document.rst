Домен: Документы / Заказ-наряды
================================

Создание и чтение заказ-нарядов (``document_out``) и связанных цепочек записей.

.. contents:: Содержание
   :local:
   :depth: 2

---

Схема связей
------------

.. code-block:: text

   document_out  (document_type_id=11, client_id, summa=0, flag=2, date_accept)
       │
       ├── service_work × N           ← строки услуг (см. два режима ниже)
       │
       ├── document_cargo             ← плательщик документа (payer_id = client_id)
       │
       └── document_registry          ← метазапись (аудит: кто создал, когда)
               │
               └── document_out_header  (номер, дата, prefix="АВТ", state=2)
                       │
                       └── document_service_detail  ← привязка авто (обязательно)

---

ORM-модели
----------

DocumentOut
~~~~~~~~~~~

Таблица ``document_out`` — основная запись документа.

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Поле
     - Тип
     - Описание
   * - ``document_out_id``
     - ``int`` PK
     - Первичный ключ; возвращается из ``create_service_order``
   * - ``document_type_id``
     - ``int`` FK
     - Тип документа (11=Заказ-наряд)
   * - ``client_id``
     - ``int`` FK
     - Клиент
   * - ``organization_id``
     - ``int`` FK
     - Организация-исполнитель
   * - ``summa``
     - ``Decimal``
     - Сумма **товаров**, не общая. ``NOT NULL``, для заказ-наряда услуг
       (автомойка) = 0. UI считает итог как
       ``summa + document_service_detail.summa_work``.
   * - ``flag``
     - ``int``
     - Константа ``2`` у всех ручных заказ-нарядов АвтоМойки.
   * - ``summa_bonus``
     - ``Decimal``
     - Бонусы к начислению (дефолт 0).
   * - ``date_accept``
     - ``datetime``
     - Дата/время приёма / окончания работ
   * - ``date_payment``
     - ``datetime``
     - Дата оплаты (обновляется при ``create_payment``)

DocumentRegistry
~~~~~~~~~~~~~~~~

Таблица ``document_registry`` — метазапись для каждого документа (аудит + связь с платежами).

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Поле
     - Тип
     - Описание
   * - ``document_registry_id``
     - ``int`` PK
     - Первичный ключ
   * - ``metatable_id``
     - ``int``
     - Тип сущности (12=document_out)
   * - ``create_user_id``
     - ``int`` FK
     - Кто создал
   * - ``create_date``
     - ``datetime``
     - Когда создал
   * - ``change_user_id``
     - ``int`` FK
     - Кто изменил последним
   * - ``change_date``
     - ``datetime``
     - Когда изменил
   * - ``document_type_id_cache``
     - ``int`` FK
     - Кэш типа документа

DocumentOutHeader
~~~~~~~~~~~~~~~~~

Таблица ``document_out_header`` — заголовок документа (номер, дата, исполнитель).

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Поле
     - Тип
     - Описание
   * - ``document_out_header_id``
     - ``int`` PK
     - Первичный ключ
   * - ``document_out_id``
     - ``int`` FK
     - Ссылка на ``document_out``
   * - ``document_registry_id``
     - ``int`` FK
     - Ссылка на ``document_registry``
   * - ``document_out_tree_id``
     - ``int`` FK
     - Папка документов
   * - ``user_id``
     - ``int`` FK
     - Исполнитель
   * - ``prefix``
     - ``str(5)``
     - Префикс номера (``"АВТ"``)
   * - ``number``
     - ``int``
     - Порядковый номер
   * - ``suffix``
     - ``str(5)``
     - Суффикс номера (напр. ``"К"``)
   * - ``fullnumber``
     - ``str(21)``
     - Вычисляемое поле: ``prefix + number + suffix`` (COMPUTED BY в Firebird)
   * - ``date_create``
     - ``datetime``
     - Дата создания документа
   * - ``state``
     - ``int``
     - Статус: 2=Черновик, 4=Оформлен, -1=Удалён
   * - ``notes``
     - ``text``
     - Примечание

DocumentServiceDetail
~~~~~~~~~~~~~~~~~~~~~

Таблица ``document_service_detail`` — деталь услуги: привязка авто + сумма работ.
Создаётся всегда; ``client_car`` у :func:`create_service_order` —
**обязательный** параметр.

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Поле
     - Тип
     - Описание
   * - ``document_service_detail_id``
     - ``int`` PK
     - Первичный ключ
   * - ``document_out_header_id``
     - ``int`` FK
     - Заголовок документа
   * - ``model_link_id``
     - ``int`` FK
     - Привязка авто клиента (``model_link.model_link_id``)
   * - ``summa_work``
     - ``Decimal``
     - Сумма услуг. UI прибавляет к ``document_out.summa`` для итога.
   * - ``price_norm_id``
     - ``int`` FK
     - Норма цены, у всех ручных = ``5`` (``price_norm.price = 1``).
   * - ``discount_work``
     - ``float``
     - Скидка на работы (дефолт 0).
   * - ``summa_bonus``
     - ``Decimal``
     - Бонусы за работу (дефолт 0).
   * - ``doc_date_end_section_link``
     - ``int``
     - Константа ``1`` у всех ручных заказов АвтоМойки.
   * - ``guarante``
     - ``text``
     - Текст гарантии (стандартный шаблон).

DocumentCargo
~~~~~~~~~~~~~

Таблица ``document_cargo`` — реквизиты плательщика документа (не про груз,
несмотря на имя). У всех ручных заказ-нарядов АвтоМойки заполнена;
``create_service_order`` создаёт её автоматически.

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Поле
     - Тип
     - Описание
   * - ``document_cargo_id``
     - ``int`` PK
     - Первичный ключ
   * - ``document_out_id``
     - ``int`` FK
     - Документ
   * - ``payer_id``
     - ``int`` FK
     - Плательщик (``client.client_id``; у заказов АвтоМойки равен
       ``document_out.client_id``)
   * - ``update_sender`` / ``update_receiver`` / ``update_payer``
     - ``int``
     - Флаги актуализации реквизитов (константно = ``1``)
   * - ``use_main_payment``
     - ``int``
     - Использовать основной способ оплаты (константно = ``0``)

ServiceWork
~~~~~~~~~~~

Таблица ``service_work`` — строки услуг в заказ-наряде. Существует **два
режима записи**: справочный (привязка к ``service_complex_work``) и
ручной. Выбор определяется наличием ``complex_work_id`` в
:class:`ServiceOrderItem`.

.. list-table::
   :header-rows: 1
   :widths: 25 18 57

   * - Поле
     - Тип
     - Описание
   * - ``service_work_id``
     - ``int`` PK
     - Первичный ключ
   * - ``document_out_id``
     - ``int`` FK
     - Заказ-наряд
   * - ``name``
     - ``str(255)``
     - Справочный режим: каноническое имя (``"Стандарт"``, ``"Комплекс"``).
       Ручной режим: произвольное имя (напр. длинное из RW).
   * - ``price``
     - ``Decimal``
     - **Справочный режим**: цена за единицу.
       **Ручной режим**: ``NULL`` — цена уходит в ``time_value``.
   * - ``time_value``
     - ``Decimal``
     - **Справочный режим**: ``NULL``.
       **Ручной режим**: цена за единицу (UI считает
       ``time_value × price_norm`` как итог; при ``price_norm=NULL``
       показывает 0, поэтому в любом режиме ставим ``price_norm=1``).
   * - ``price_norm``
     - ``Decimal``
     - Множитель для UI-расчёта итога. Всегда ``1``.
   * - ``rt_work_id``
     - ``int``
     - FK в справочник работ. При ``work_source=3`` —
       ``service_complex_work.service_complex_work_id``, при
       ``work_source=2`` — ``service_common_work.service_common_work_id``,
       при ``NULL`` — ручной ввод.
   * - ``work_source``
     - ``int``
     - Тип справочника: ``3`` — комплексные работы, ``2`` — общий каталог,
       ``NULL`` — ручной ввод.
   * - ``quantity``
     - ``int``
     - Количество (по умолчанию 1)
   * - ``position_number``
     - ``int``
     - Порядок строки
   * - ``external_id``
     - ``str(512)``
     - Внешний ID (напр. из RocketWash — ``services.id``)

DocumentOutTree
~~~~~~~~~~~~~~~

Таблица ``document_out_tree`` — иерархия папок для документов реализации.

.. code-block:: python

   from autodealer.domain.document_out_tree import DocumentOutTree

   folders = DocumentOutTree.objects.filter(hidden=0).all()
   # document_out_tree_id=3 → «АвтоМойка»

---

Высокоуровневые функции (``services``)
---------------------------------------

create_service_order
~~~~~~~~~~~~~~~~~~~~

.. function:: autodealer.services.create_service_order(*, client_id, items, document_out_tree_id, organization_id, client_car, date_start, date_finish, created_by_user_id=1, notes=None, service_order_suffix=None)

   Создать заказ-наряд. Все записи — в одной транзакции.

   :param int client_id: PK клиента.
   :param list[ServiceOrderItem] items: Строки услуг. Не может быть пустым.
   :param int document_out_tree_id: Папка документов.
   :param int organization_id: Организация-исполнитель.
   :param int client_car: ``model_link_id`` — **обязателен**. При ``None``
       функция выбрасывает ``ValueError``.
   :param datetime date_start: Дата начала.
   :param datetime date_finish: Дата окончания / приёма.
   :param int created_by_user_id: Исполнитель (по умолчанию 1).
   :param str notes: Примечание.
   :param str service_order_suffix: Суффикс номера (напр. ``"К"``).
   :returns: ``document_out_id``.
   :rtype: int
   :raises ValueError: Если ``items`` пустой или ``client_car`` не передан.

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

delete_service_order / restore_service_order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: autodealer.services.delete_service_order(document_out_id, *, hard=False)

   Удалить заказ-наряд.

   - **Soft** (``hard=False``, по умолчанию): ставит
     ``document_out_header.state = -1`` («Удалён»). Документ скрывается
     в UI АвтоДилера, но данные сохраняются.
   - **Hard** (``hard=True``): физически удаляет всю цепочку записей в
     одной транзакции —
     ``document_cargo`` → ``service_work`` → ``document_service_detail`` →
     ``document_out_header`` → ``document_registry`` → ``document_out``.
     Перед этим авто-удаляются «ботовые» платежи (с маркером
     :data:`~autodealer.actions.payment.BOT_NOTE_MARKER` в
     ``payment.notes``). Если на документе есть **ручные** платежи —
     функция выбрасывает ``ValueError``.

   :raises ValueError: Документ не найден; при ``hard=True`` — привязаны
       ручные платежи.

.. function:: autodealer.services.restore_service_order(document_out_id, *, state=2)

   Парная операция к soft-delete. Переводит ``document_out_header.state``
   из ``-1`` обратно в рабочее (по умолчанию ``2`` — «Черновик»).
   Отказывает, если текущий state ≠ ``-1``, чтобы не понизить/повысить
   state живого документа.

get_service_order
~~~~~~~~~~~~~~~~~

.. function:: autodealer.services.get_service_order(document_out_id)

   Прочитать заказ-наряд со строками услуг.

   :returns: :class:`~autodealer.services.ServiceOrder` или ``None``.

   .. code-block:: python

      order = get_service_order(42)
      print(order.summa, order.date_accept)
      for item in order.items:
          print(item.name, item.price)

.. class:: autodealer.services.ServiceOrderItem

   Одна строка услуги в заказ-наряде. Два режима записи в
   ``service_work`` (см. :ref:`ServiceWork <service_work>` выше):

   .. attribute:: name: str

      Имя работы. В справочном режиме — каноническое из
      ``service_complex_work.name`` (``"Стандарт"``, ``"Комплекс"``).

   .. attribute:: price: float

      Цена за единицу. Попадает в ``service_work.price`` (справочный режим)
      или ``service_work.time_value`` (ручной режим).

   .. attribute:: time_value: float

      Длительность (минуты). Справочная информация, **в БД не сохраняется** —
      в ``service_work`` нет отдельного поля под длительность.

   .. attribute:: quantity: int = 1
   .. attribute:: external_id: str | None

      Напр. ``"821459"`` — ``services.id`` из RocketWash.

   .. attribute:: complex_work_id: int | None = None

      PK в ``service_complex_work``. Если задан — включает
      «справочный» режим записи: ``rt_work_id = complex_work_id``,
      ``work_source = 3``. Ищется через
      :func:`autodealer.integration.rocketwash.resolve_complex_work`.

.. class:: autodealer.services.ServiceOrder

   .. attribute:: document_out_id: int
   .. attribute:: client_id: int | None
   .. attribute:: summa: float
   .. attribute:: date_accept: datetime | None
   .. attribute:: date_payment: datetime | None
   .. attribute:: document_number: int | None
   .. attribute:: client_car: int | None
   .. attribute:: items: list[ServiceOrderItem]

---

Константы
---------

.. list-table::
   :header-rows: 1
   :widths: 40 15 45

   * - Константа
     - Значение
     - Описание
   * - ``document_type_id``
     - ``11``
     - Заказ-наряд
   * - ``prefix``
     - ``"АВТ"``
     - Префикс номера
   * - ``state`` (Черновик)
     - ``2``
     - Статус при создании
   * - ``metatable_id``
     - ``12``
     - ``document_registry.metatable_id``
