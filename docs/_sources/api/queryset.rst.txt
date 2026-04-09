QuerySet API
============

.. autoclass:: autodealer.queryset.DoesNotExist
   :show-inheritance:

.. autoclass:: autodealer.queryset.MultipleObjectsReturned
   :show-inheritance:

.. autoclass:: autodealer.queryset.QuerySet
   :members:
   :member-order: bysource

.. autoclass:: autodealer.queryset.Manager
   :members:

Таблица лукапов
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Лукап
     - SQL
   * - ``field=value`` / ``field__exact=value``
     - ``field = value``
   * - ``field__iexact=value``
     - ``field ILIKE value``
   * - ``field__contains="текст"``
     - ``field LIKE '%текст%'``
   * - ``field__icontains="текст"``
     - ``field ILIKE '%текст%'``
   * - ``field__startswith="А"``
     - ``field LIKE 'А%'``
   * - ``field__endswith="ов"``
     - ``field LIKE '%ов'``
   * - ``field__gt=5``
     - ``field > 5``
   * - ``field__gte=5``
     - ``field >= 5``
   * - ``field__lt=5``
     - ``field < 5``
   * - ``field__lte=5``
     - ``field <= 5``
   * - ``field__in=[1,2,3]``
     - ``field IN (1, 2, 3)``
   * - ``field__isnull=True``
     - ``field IS NULL``
   * - ``field__isnull=False``
     - ``field IS NOT NULL``
