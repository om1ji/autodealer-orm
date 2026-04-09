Высокоуровневые действия (``autodealer.actions``)
==================================================

Пакет ``autodealer.actions`` содержит высокоуровневые функции для работы
с клиентами, автомобилями и платежами.
В отличие от ORM-моделей, каждая функция выполняет атомарную бизнес-операцию
и скрывает детали ``directory_registry`` / транзакций от вызывающего кода.

.. contents:: Содержание
   :local:
   :depth: 2

---

Клиенты и автомобили (``actions.client``)
------------------------------------------

Создание клиента
~~~~~~~~~~~~~~~~

.. function:: autodealer.actions.client.create_client(fullname, *, phone=None, email=None, birth=None, sex=None, discount=0.0, discount_work=0.0, client_tree_id=1, created_by_user_id=1)

   Создать клиента в Firebird.

   Атомарно создаёт цепочку:
   ``DirectoryRegistry (metatable=3)`` → ``Client`` → ``Contact`` (если есть phone/email).

   :param str fullname: Полное имя (обязательно).
   :param str phone: Мобильный телефон.
   :param str email: Email.
   :param date birth: Дата рождения.
   :param int sex: 1=муж, 2=жен, ``None``=не указан.
   :param float discount: Скидка на товары %.
   :param float discount_work: Скидка на работы %.
   :param int client_tree_id: Папка клиентов (1=Физлица, 2=Юрлица, 3=VIP).
   :param int created_by_user_id: Пользователь-создатель.
   :returns: ``client_id`` созданного клиента.
   :rtype: int

   .. code-block:: python

      from datetime import date
      from autodealer.actions.client import create_client

      client_id = create_client(
          "Иванов Иван Иванович",
          phone="79991234567",
          email="ivan@example.com",
          birth=date(1990, 5, 15),
          sex=1,
          discount=5.0,
      )

Автомобили клиента
~~~~~~~~~~~~~~~~~~

.. function:: autodealer.actions.client.add_vehicle_to_client(client_id, make, model_name, *, regno=None, vin=None, year=None, color=None, default_car=False, created_by_user_id=1)

   Добавить автомобиль клиенту по имени марки и модели.

   Автоматически находит или создаёт записи в ``mark``, ``model``, ``color``,
   затем создаёт ``model_detail`` и ``model_link``.

   Идемпотентность: если машина с таким ``regno`` уже существует — возвращает
   существующий ``model_detail_id`` без дубликата.

   :param int client_id: PK клиента.
   :param str make: Марка («Toyota», «BMW»).
   :param str model_name: Модель («Camry», «X5»).
   :param str regno: Госномер.
   :param str vin: VIN-номер.
   :param int year: Год выпуска.
   :param str color: Цвет строкой («Белый», «Чёрный»).
   :param bool default_car: Пометить как основное авто.
   :returns: ``model_detail_id`` созданного или существующего автомобиля.
   :rtype: int

   .. code-block:: python

      from autodealer.actions.client import add_vehicle_to_client

      md_id = add_vehicle_to_client(
          client_id=42,
          make="Toyota",
          model_name="Camry",
          regno="А001ВС77",
          year=2020,
          color="Белый",
          default_car=True,
      )

.. function:: autodealer.actions.client.get_client_vehicles(client_id)

   Вернуть все автомобили клиента в виде объектов :class:`~autodealer.domain.model_link.ModelLink`.

   :param int client_id: PK клиента.
   :returns: Список :class:`~autodealer.domain.model_link.ModelLink`.
       Пустой список если у клиента нет машин.

   .. code-block:: python

      from autodealer.actions.client import get_client_vehicles

      cars = get_client_vehicles(42)
      for car in cars:
          print(car.model_link_id, car.model_detail_id, car.default_car)

.. function:: autodealer.actions.client.create_vehicle_for_client(*, client_id, model_id, vin=None, regno=None, year_of_production=None, color_id=None, ...)

   Создать автомобиль и привязать к клиенту напрямую через ``model_id``.

   :returns: Экземпляр :class:`~autodealer.domain.model_link.ModelLink`.

Вспомогательные функции
~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: autodealer.actions.client.get_or_create_mark(name)

   Найти марку по имени или создать новую. Возвращает ``mark_id``.

.. function:: autodealer.actions.client.get_or_create_model(mark_id, model_name)

   Найти модель по марке и имени или создать новую. Возвращает ``model_id``.

.. function:: autodealer.actions.client.get_or_create_color(name)

   Найти цвет или создать новый. Возвращает ``color_id`` или ``None`` если ``name`` пустой.

.. function:: autodealer.actions.client.find_vehicle_by_regno(regno)

   Найти автомобиль по госномеру. Возвращает ``model_detail_id`` или ``None``.

.. function:: autodealer.actions.client.find_vehicle_by_vin(vin)

   Найти автомобиль по VIN. Возвращает ``model_detail_id`` или ``None``.

---

Платежи (``actions.payment``)
------------------------------

Связь таблиц
~~~~~~~~~~~~

.. code-block:: text

   document_out
       │
       └── payment_out.document_out_id ──► payment
                                               │
                                               ├── payment_document.payment_id
                                               │       └── document_registry
                                               │
                                               └── money_document_payment.payment_id
                                                       └── money_document_detail
                                                               (accounting_item_id=3
                                                                «Поступление от клиента»)

Справочники
~~~~~~~~~~~

.. function:: autodealer.actions.payment.get_wallets(organization_id)

   Вернуть кошельки (кассы/счета) организации.

   :param int organization_id: PK организации.
   :returns: Список :class:`WalletInfo`.

   .. code-block:: python

      from autodealer.actions.payment import get_wallets

      for w in get_wallets(1):
          print(w.wallet_id, w.name)

.. function:: autodealer.actions.payment.get_payment_types()

   Вернуть активные способы оплаты из ``payment_type``.

   :returns: Список :class:`PaymentTypeInfo`.

   .. code-block:: python

      from autodealer.actions.payment import get_payment_types

      for pt in get_payment_types():
          print(pt.payment_type_id, pt.name)

Чтение платежей
~~~~~~~~~~~~~~~

.. function:: autodealer.actions.payment.get_payments(document_out_id)

   Вернуть все платежи по заказ-наряду.

   :param int document_out_id: PK заказ-наряда.
   :returns: Список :class:`PaymentRecord`. Пустой если платежей нет.

   .. code-block:: python

      from autodealer.actions.payment import get_payments

      for p in get_payments(42):
          print(p.payment_id, p.summa, p.payment_type_name, p.wallet_name)

Создание платежа
~~~~~~~~~~~~~~~~

.. function:: autodealer.actions.payment.create_payment(*, document_out_id, summa, wallet_id, payment_type_id, payment_date=None, notes=None)

   Создать документ оплаты для заказ-наряда.

   Атомарно создаёт цепочку:

   1. ``payment`` — запись платежа.
   2. ``payment_out`` — привязка к ``document_out``.
   3. ``payment_document`` — привязка к ``document_registry``.
   4. ``money_document_detail`` — бухгалтерская проводка (``accounting_item_id=3``).
   5. ``money_document_payment`` — связь проводки с платежом.
   6. ``UPDATE document_out.date_payment``.

   :param int document_out_id: PK заказ-наряда.
   :param float summa: Сумма платежа.
   :param int wallet_id: FK в ``wallet`` — касса/счёт.
   :param int payment_type_id: FK в ``payment_type`` — способ оплаты.
   :param datetime payment_date: Дата платежа. По умолчанию — текущее время.
   :param str notes: Примечание.
   :returns: ``payment_id`` созданного платежа.
   :rtype: int
   :raises ValueError: Если заказ-наряд не найден.

   .. code-block:: python

      from autodealer.actions.payment import create_payment

      payment_id = create_payment(
          document_out_id=42,
          summa=2300.0,
          wallet_id=1,        # Наличный расчёт
          payment_type_id=1,  # Наличный
      )

Разбивка оплаты
~~~~~~~~~~~~~~~

.. function:: autodealer.actions.payment.create_payment_split(*, document_out_id, parts, payment_date=None)

   Создать несколько платежей за один заказ-наряд (разбивка по способам оплаты).
   Каждая часть создаётся через :func:`create_payment` независимо.

   :param int document_out_id: PK заказ-наряда.
   :param list parts: Список :class:`PaymentSplitItem`.
   :param datetime payment_date: Единая дата для всех частей.
   :returns: Список ``payment_id`` в том же порядке, что и ``parts``.
   :rtype: list[int]
   :raises ValueError: Если ``parts`` пустой или суммы <= 0.

   .. code-block:: python

      from autodealer.actions.payment import create_payment_split, PaymentSplitItem

      ids = create_payment_split(
          document_out_id=42,
          parts=[
              PaymentSplitItem(wallet_id=1, payment_type_id=1, summa=1000.0),  # наличные
              PaymentSplitItem(wallet_id=4, payment_type_id=7, summa=1300.0),  # карта
          ],
      )

Типы данных
~~~~~~~~~~~

.. class:: autodealer.actions.payment.WalletInfo

   .. attribute:: wallet_id: int
   .. attribute:: name: str
   .. attribute:: organization_id: int

.. class:: autodealer.actions.payment.PaymentTypeInfo

   .. attribute:: payment_type_id: int
   .. attribute:: name: str

.. class:: autodealer.actions.payment.PaymentRecord

   .. attribute:: payment_id: int
   .. attribute:: summa: Decimal
   .. attribute:: payment_date: datetime
   .. attribute:: payment_type_id: int
   .. attribute:: payment_type_name: str | None
   .. attribute:: wallet_id: int | None
   .. attribute:: wallet_name: str | None
   .. attribute:: notes: str | None

.. class:: autodealer.actions.payment.PaymentSplitItem

   .. attribute:: wallet_id: int
   .. attribute:: payment_type_id: int
   .. attribute:: summa: float
   .. attribute:: notes: str | None
