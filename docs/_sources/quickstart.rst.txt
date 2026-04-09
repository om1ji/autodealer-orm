Быстрый старт
=============

Установка
---------

.. code-block:: bash

   pip install -r requirements.txt

На macOS также нужен клиент Firebird:

.. code-block:: bash

   brew install firebird

Настройка подключения
---------------------

Через ``.env`` в корне проекта:

.. code-block:: ini

   DB_HOST=192.168.88.64
   DB_PORT=3050
   DB_DATABASE=C:\Program Files (x86)\AutoDealer\AutoDealer\Database\StOm1.fdb
   DB_USER=SYSDBA
   DB_PASSWORD=masterkey
   DB_CHARSET=UTF8

Или явно в коде (вызов **до** импорта моделей):

.. code-block:: python

   from autodealer.connection import configure_database

   configure_database(
       host="192.168.88.64",
       port=3050,
       database=r"C:\path\to\AutoDealer.fdb",
       user="SYSDBA",
       password="masterkey",
       charset="UTF8",
   )

Использование моделей
---------------------

.. code-block:: python

   from autodealer.domain.bank import Bank
   from autodealer.domain.users import Users

   # Все записи
   banks = Bank.objects.all()

   # Фильтрация
   active = Bank.objects.filter(hidden=0).order_by('name').all()

   # Один объект
   bank = Bank.objects.get(bank_id=1)
   print(bank.name, bank.bik)

   # Проверка существования
   if Bank.objects.filter(name__icontains='сбер').exists():
       print("Сбербанк найден")

   # Список словарей
   rows = Bank.objects.filter(hidden=0).values('bank_id', 'name')

Запись данных
-------------

.. code-block:: python

   # Создание
   bank = Bank.objects.create(name="Тинькофф", bik="044525974", hidden=0)

   # Массовое обновление
   Bank.objects.filter(hidden=1).update(hidden=0)

   # Удаление
   Bank.objects.filter(hidden=1).delete()

Сложные запросы (low-level)
----------------------------

Для многотабличных запросов или сложных условий используйте ``session_scope``:

.. code-block:: python

   from sqlalchemy import select
   from autodealer.connection import session_scope
   from autodealer.domain.bank import Bank

   with session_scope() as session:
       result = session.execute(
           select(Bank)
           .where(Bank.hidden == 0)
           .order_by(Bank.name)
       ).scalars().all()

Генерация моделей
-----------------

При изменении схемы БД — перегенерировать модели:

.. code-block:: bash

   python autodealer/tools/generate_models.py

Скрипт перезаписывает все файлы в ``autodealer/domain/``.
