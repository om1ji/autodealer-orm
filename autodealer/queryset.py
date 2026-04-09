"""Django-подобный QuerySet и Manager для моделей SQLAlchemy 2.0.

Каждая модель наследует от :class:`~autodealer.connection.Base`, к которому
автоматически привязан :class:`Manager`. Доступ через атрибут ``objects``::

    from autodealer.domain.bank import Bank

    Bank.objects.filter(hidden=0).order_by('name').all()
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar, overload

from sqlalchemy import (
    delete,
    func,
    select,
    type_coerce,
    update,
)
from sqlalchemy.types import NullType
from sqlalchemy.orm import sessionmaker


def _session_scope():
    from autodealer.connection import session_scope

    return session_scope()


def _get_engine():
    from autodealer.connection import get_engine

    return get_engine()


T = TypeVar("T")


class DoesNotExist(Exception):
    """Объект не найден. Выбрасывается из :meth:`QuerySet.get`."""


class MultipleObjectsReturned(Exception):
    """Найдено более одного объекта. Выбрасывается из :meth:`QuerySet.get`."""


class QuerySet(Generic[T]):
    """Цепочечный построитель запросов, аналогичный Django QuerySet.

    Не выполняет SQL до вызова терминального метода
    (:meth:`all`, :meth:`first`, :meth:`last`, :meth:`count`, :meth:`get`,
    :meth:`exists`, :meth:`values`).

    Не создавать напрямую — использовать ``Model.objects``.

    Example::

        # Все активные банки, отсортированные по имени
        banks = Bank.objects.filter(hidden=0).order_by('name').all()

        # Один объект или исключение
        bank = Bank.objects.get(bank_id=1)

        # Проверка существования
        if Bank.objects.filter(name__icontains='сбер').exists():
            ...
    """

    def __init__(self, model: type[T]) -> None:
        self._model = model
        self._wheres: list = []
        self._order_cols: list = []
        self._limit_val: int | None = None
        self._offset_val: int | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clone(self) -> "QuerySet[T]":
        qs: QuerySet[T] = QuerySet(self._model)
        qs._wheres = self._wheres.copy()
        qs._order_cols = self._order_cols.copy()
        qs._limit_val = self._limit_val
        qs._offset_val = self._offset_val
        return qs

    def _resolve_field(self, key: str):
        """Support double-underscore lookups: name__contains, age__gte, etc."""
        # literal() is required for LIKE patterns to avoid a sqlalchemy-firebird
        # bug where the Firebird type compiler receives the column length as `name`
        # instead of the type name, causing TypeError during SQL compilation.
        lookups = {
            "exact": lambda col, v: col == v,
            # type_coerce(..., NullType()) prevents sqlalchemy-firebird from
            # calling visit_VARCHAR on the bind parameter, which has a bug
            # where _render_string_type receives swapped positional arguments.
            "iexact": lambda col, v: col.ilike(type_coerce(v, NullType())),
            "contains": lambda col, v: col.like(type_coerce(f"%{v}%", NullType())),
            "icontains": lambda col, v: col.ilike(type_coerce(f"%{v}%", NullType())),
            "startswith": lambda col, v: col.like(type_coerce(f"{v}%", NullType())),
            "endswith": lambda col, v: col.like(type_coerce(f"%{v}", NullType())),
            "gt": lambda col, v: col > v,
            "gte": lambda col, v: col >= v,
            "lt": lambda col, v: col < v,
            "lte": lambda col, v: col <= v,
            "in": lambda col, v: col.in_(v),
            "isnull": lambda col, v: col.is_(None) if v else col.isnot(None),
        }
        parts = key.rsplit("__", 1)
        if len(parts) == 2 and parts[1] in lookups:
            field_name, lookup = parts
            col = getattr(self._model, field_name)
            return lookups[lookup], col
        col = getattr(self._model, key)
        return lookups["exact"], col

    @staticmethod
    def _coerce_strings(kwargs: dict) -> dict:
        """Wrap str values with type_coerce(..., NullType()) to avoid the
        sqlalchemy-firebird bug where _render_string_type receives swapped
        arguments during INSERT/UPDATE compilation."""
        return {
            k: type_coerce(v, NullType()) if isinstance(v, str) else v
            for k, v in kwargs.items()
        }

    def _build_stmt(self):
        stmt = select(self._model)
        for w in self._wheres:
            stmt = stmt.where(w)
        if self._order_cols:
            stmt = stmt.order_by(*self._order_cols)
        if self._limit_val is not None:
            stmt = stmt.limit(self._limit_val)
        if self._offset_val is not None:
            stmt = stmt.offset(self._offset_val)
        return stmt

    # ------------------------------------------------------------------
    # Filtering / ordering
    # ------------------------------------------------------------------

    def filter(self, **kwargs: Any) -> "QuerySet[T]":
        """Добавить условия фильтрации (WHERE).

        Поддерживаются лукапы через ``__``:
        ``exact``, ``iexact``, ``contains``, ``icontains``,
        ``startswith``, ``endswith``, ``gt``, ``gte``, ``lt``, ``lte``,
        ``in``, ``isnull``.

        Args:
            **kwargs: Условия вида ``field=value`` или ``field__lookup=value``.

        Returns:
            Новый :class:`QuerySet` с добавленными условиями.

        Example::

            Bank.objects.filter(hidden=0, name__icontains='сбер')
        """
        qs = self._clone()
        for key, value in kwargs.items():
            op, col = self._resolve_field(key)
            qs._wheres.append(op(col, value))
        return qs

    def exclude(self, **kwargs: Any) -> "QuerySet[T]":
        """Исключить записи, соответствующие условиям (WHERE NOT).

        Args:
            **kwargs: Условия вида ``field=value`` или ``field__lookup=value``.

        Returns:
            Новый :class:`QuerySet`.
        """
        qs = self._clone()
        for key, value in kwargs.items():
            op, col = self._resolve_field(key)
            qs._wheres.append(~op(col, value))
        return qs

    def order_by(self, *fields: str) -> "QuerySet[T]":
        """Задать сортировку.

        Префикс ``-`` означает сортировку по убыванию.

        Args:
            *fields: Имена полей. ``'-name'`` — DESC, ``'name'`` — ASC.

        Returns:
            Новый :class:`QuerySet`.

        Example::

            Bank.objects.order_by('-bank_id', 'name')
        """
        qs = self._clone()
        for field in fields:
            if field.startswith("-"):
                col = getattr(self._model, field[1:])
                qs._order_cols.append(col.desc())
            else:
                col = getattr(self._model, field)
                qs._order_cols.append(col.asc())
        return qs

    def limit(self, n: int) -> "QuerySet[T]":
        """Ограничить количество результатов (LIMIT).

        Args:
            n: Максимальное число записей.

        Returns:
            Новый :class:`QuerySet`.
        """
        qs = self._clone()
        qs._limit_val = n
        return qs

    def offset(self, n: int) -> "QuerySet[T]":
        """Пропустить первые *n* записей (OFFSET).

        Args:
            n: Число пропускаемых записей.

        Returns:
            Новый :class:`QuerySet`.
        """
        qs = self._clone()
        qs._offset_val = n
        return qs

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def all(self) -> list[T]:
        """Выполнить запрос и вернуть все результаты.

        Returns:
            Список экземпляров модели (detached от сессии).
        """
        with _session_scope() as session:
            result = session.execute(self._build_stmt()).scalars().all()
            session.expunge_all()
            return result

    def first(self) -> T | None:
        """Вернуть первую запись или ``None``.

        Returns:
            Экземпляр модели или ``None``.
        """
        with _session_scope() as session:
            stmt = self._build_stmt().limit(1)
            obj = session.execute(stmt).scalars().first()
            if obj is not None:
                session.expunge(obj)
            return obj

    def last(self) -> T | None:
        """Вернуть последнюю запись или ``None``.

        Returns:
            Экземпляр модели или ``None``.
        """
        results = self.all()
        return results[-1] if results else None

    def get(self, **kwargs: Any) -> T:
        """Вернуть ровно одну запись.

        Args:
            **kwargs: Дополнительные условия (как в :meth:`filter`).

        Returns:
            Экземпляр модели.

        Raises:
            DoesNotExist: Запись не найдена.
            MultipleObjectsReturned: Найдено более одной записи.

        Example::

            bank = Bank.objects.get(bank_id=1)
        """
        qs = self.filter(**kwargs) if kwargs else self
        with _session_scope() as session:
            results = session.execute(qs._build_stmt()).scalars().all()
            if len(results) == 0:
                raise DoesNotExist(
                    f"{self._model.__name__} matching query does not exist."
                )
            if len(results) > 1:
                raise MultipleObjectsReturned(
                    f"get() returned more than one {self._model.__name__}."
                )
            session.expunge(results[0])
            return results[0]

    def count(self) -> int:
        """Вернуть количество записей (SELECT COUNT(*)).

        Returns:
            Целое число.
        """
        stmt = select(func.count()).select_from(self._model)
        for w in self._wheres:
            stmt = stmt.where(w)
        with _session_scope() as session:
            return session.execute(stmt).scalar() or 0

    def exists(self) -> bool:
        """Проверить, есть ли хотя бы одна запись.

        Returns:
            ``True`` если записи существуют.
        """
        return self.count() > 0

    def values(self, *fields: str) -> list[dict]:
        """Вернуть список словарей вместо экземпляров модели.

        Args:
            *fields: Имена полей. Если не переданы — все колонки.

        Returns:
            Список ``dict``.

        Example::

            Bank.objects.filter(hidden=0).values('bank_id', 'name')
            # [{'bank_id': 1, 'name': 'Сбербанк'}, ...]
        """
        cols = fields or [c.key for c in self._model.__table__.columns]
        with _session_scope() as session:
            objs = session.execute(self._build_stmt()).scalars().all()
            return [{f: getattr(obj, f) for f in cols} for obj in objs]

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create(self, **kwargs: Any) -> T:
        """Создать и сохранить новую запись.

        Args:
            **kwargs: Значения полей новой записи.

        Returns:
            Сохранённый экземпляр модели (атрибуты доступны после коммита).

        Example::

            bank = Bank.objects.create(name='Тинькофф', bik='044525974')
        """
        from sqlalchemy import insert as _insert

        Session = sessionmaker(bind=_get_engine(), expire_on_commit=False)
        session = Session()
        try:
            stmt = _insert(self._model).values(**self._coerce_strings(kwargs))
            result = session.execute(stmt)
            session.commit()
            # Build detached instance; populate trigger-generated PK from RETURNING
            obj = self._model(**kwargs)
            pk_cols = list(self._model.__mapper__.primary_key)
            for col, val in zip(pk_cols, result.inserted_primary_key or []):
                if getattr(obj, col.key, None) is None and val is not None:
                    setattr(obj, col.key, val)
            return obj
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update(self, **kwargs: Any) -> int:
        """Массово обновить записи, соответствующие фильтрам.

        Args:
            **kwargs: Поля и новые значения.

        Returns:
            Количество изменённых строк.

        Example::

            Bank.objects.filter(hidden=1).update(hidden=0)
        """
        stmt = update(self._model)
        for w in self._wheres:
            stmt = stmt.where(w)
        stmt = stmt.values(**self._coerce_strings(kwargs))
        with _session_scope() as session:
            result = session.execute(stmt)
            return result.rowcount

    def delete(self) -> int:
        """Массово удалить записи, соответствующие фильтрам.

        Returns:
            Количество удалённых строк.

        Example::

            Bank.objects.filter(hidden=1).delete()
        """
        stmt = delete(self._model)
        for w in self._wheres:
            stmt = stmt.where(w)
        with _session_scope() as session:
            result = session.execute(stmt)
            return result.rowcount

    # ------------------------------------------------------------------
    # Python protocol
    # ------------------------------------------------------------------

    def __iter__(self):
        return iter(self.all())

    def __len__(self) -> int:
        return self.count()

    def __repr__(self) -> str:
        return f"<QuerySet model={self._model.__name__}>"


class Manager:
    """Descriptor that provides Django-like `Model.objects` access.

    Attach to a class with::

        class MyModel(Base):
            objects = Manager()
    """

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    @overload
    def __get__(self, obj: None, objtype: type[T]) -> QuerySet[T]: ...

    @overload
    def __get__(self, obj: object, objtype: type[T] | None) -> QuerySet[T]: ...

    def __get__(self, obj: object, objtype: type | None = None) -> QuerySet:
        if obj is not None:
            raise AttributeError("Manager is not accessible via model instances.")
        return QuerySet(objtype)
