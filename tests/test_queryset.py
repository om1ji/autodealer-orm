"""Tests for the QuerySet API (SELECT-only, production database).

Uses the Bank table as the primary fixture — it has known stable data.
"""

import pytest

from autodealer.domain.bank import Bank
from autodealer.domain.users import Users
from autodealer.queryset import DoesNotExist, MultipleObjectsReturned


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def first_bank_id() -> int:
    """Return the PK of the first bank for deterministic lookups."""
    bank = Bank.objects.order_by("bank_id").first()
    assert bank is not None, "Bank table must not be empty"
    return bank.bank_id


# ---------------------------------------------------------------------------
# all / count / exists
# ---------------------------------------------------------------------------

class TestBasicRetrieval:
    def test_all_returns_list(self):
        result = Bank.objects.all()
        assert isinstance(result, list)

    def test_all_contains_bank_instances(self):
        result = Bank.objects.all()
        assert len(result) > 0
        assert all(isinstance(b, Bank) for b in result)

    def test_count_returns_positive_int(self):
        count = Bank.objects.count()
        assert isinstance(count, int)
        assert count > 0

    def test_count_matches_all_length(self):
        assert Bank.objects.count() == len(Bank.objects.all())

    def test_exists_true_for_populated_table(self):
        assert Bank.objects.exists() is True

    def test_exists_false_for_impossible_filter(self):
        assert Bank.objects.filter(bank_id=-9999).exists() is False


# ---------------------------------------------------------------------------
# first / last
# ---------------------------------------------------------------------------

class TestFirstLast:
    def test_first_returns_bank(self):
        assert isinstance(Bank.objects.first(), Bank)

    def test_last_returns_bank(self):
        assert isinstance(Bank.objects.last(), Bank)

    def test_first_on_empty_filter_returns_none(self):
        result = Bank.objects.filter(bank_id=-9999).first()
        assert result is None

    def test_first_respects_order(self):
        asc = Bank.objects.order_by("bank_id").first()
        desc = Bank.objects.order_by("-bank_id").first()
        assert asc.bank_id <= desc.bank_id


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

class TestGet:
    def test_get_by_pk_returns_correct_object(self):
        pk = first_bank_id()
        bank = Bank.objects.get(bank_id=pk)
        assert isinstance(bank, Bank)
        assert bank.bank_id == pk

    def test_get_raises_does_not_exist(self):
        with pytest.raises(DoesNotExist):
            Bank.objects.get(bank_id=-9999)

    def test_get_raises_multiple_objects_returned(self):
        # Если в таблице > 1 строки и фильтр не уникальный — ожидаем исключение
        count = Bank.objects.count()
        if count < 2:
            pytest.skip("Нужно минимум 2 банка для проверки MultipleObjectsReturned")
        with pytest.raises(MultipleObjectsReturned):
            Bank.objects.get(hidden=0)


# ---------------------------------------------------------------------------
# filter / exclude
# ---------------------------------------------------------------------------

class TestFilter:
    def test_filter_by_exact_field(self):
        result = Bank.objects.filter(hidden=0).all()
        assert all(b.hidden == 0 for b in result)

    def test_filter_reduces_result_set(self):
        total = Bank.objects.count()
        filtered = Bank.objects.filter(hidden=0).count()
        assert filtered <= total

    def test_exclude_by_field(self):
        result = Bank.objects.exclude(hidden=1).all()
        assert all(b.hidden != 1 for b in result)

    def test_filter_and_exclude_complement(self):
        total = Bank.objects.count()
        hidden = Bank.objects.filter(hidden=1).count()
        not_hidden = Bank.objects.exclude(hidden=1).count()
        assert hidden + not_hidden == total


# ---------------------------------------------------------------------------
# Lookups (__contains, __gt, __in, __isnull, etc.)
# ---------------------------------------------------------------------------

class TestLookups:
    def test_contains(self):
        result = Bank.objects.filter(name__contains="банк").all()
        assert all("банк" in (b.name or "").lower() for b in result)

    def test_icontains(self):
        result = Bank.objects.filter(name__icontains="БАНК").all()
        assert len(result) > 0

    def test_startswith(self):
        result = Bank.objects.filter(name__startswith="А").all()
        assert all((b.name or "").startswith("А") for b in result)

    def test_endswith(self):
        result = Bank.objects.filter(bik__endswith="03").all()
        assert all((b.bik or "").endswith("03") for b in result)

    def test_gt(self):
        pk = first_bank_id()
        result = Bank.objects.filter(bank_id__gt=pk).all()
        assert all(b.bank_id > pk for b in result)

    def test_gte(self):
        pk = first_bank_id()
        result = Bank.objects.filter(bank_id__gte=pk).all()
        assert all(b.bank_id >= pk for b in result)

    def test_lt(self):
        last = Bank.objects.order_by("-bank_id").first()
        result = Bank.objects.filter(bank_id__lt=last.bank_id).all()
        assert all(b.bank_id < last.bank_id for b in result)

    def test_lte(self):
        last = Bank.objects.order_by("-bank_id").first()
        result = Bank.objects.filter(bank_id__lte=last.bank_id).all()
        assert last.bank_id in [b.bank_id for b in result]

    def test_in(self):
        banks = Bank.objects.order_by("bank_id").limit(3).all()
        ids = [b.bank_id for b in banks]
        result = Bank.objects.filter(bank_id__in=ids).all()
        assert {b.bank_id for b in result} == set(ids)

    def test_isnull_true(self):
        result = Bank.objects.filter(notes__isnull=True).all()
        assert all(b.notes is None for b in result)

    def test_isnull_false(self):
        result = Bank.objects.filter(notes__isnull=False).all()
        assert all(b.notes is not None for b in result)


# ---------------------------------------------------------------------------
# order_by / limit / offset
# ---------------------------------------------------------------------------

class TestOrderingPagination:
    def test_order_by_asc(self):
        result = Bank.objects.order_by("bank_id").all()
        ids = [b.bank_id for b in result]
        assert ids == sorted(ids)

    def test_order_by_desc(self):
        result = Bank.objects.order_by("-bank_id").all()
        ids = [b.bank_id for b in result]
        assert ids == sorted(ids, reverse=True)

    def test_limit(self):
        result = Bank.objects.limit(3).all()
        assert len(result) <= 3

    def test_limit_zero(self):
        result = Bank.objects.limit(0).all()
        assert result == []

    def test_offset(self):
        all_banks = Bank.objects.order_by("bank_id").all()
        offset_banks = Bank.objects.order_by("bank_id").offset(1).all()
        if len(all_banks) > 1:
            assert offset_banks[0].bank_id == all_banks[1].bank_id

    def test_limit_and_offset(self):
        page1 = Bank.objects.order_by("bank_id").limit(2).all()
        page2 = Bank.objects.order_by("bank_id").limit(2).offset(2).all()
        ids1 = {b.bank_id for b in page1}
        ids2 = {b.bank_id for b in page2}
        assert ids1.isdisjoint(ids2)

    def test_chaining(self):
        result = (
            Bank.objects
            .filter(hidden=0)
            .order_by("-bank_id")
            .limit(5)
            .offset(1)
            .all()
        )
        assert isinstance(result, list)
        assert len(result) <= 5


# ---------------------------------------------------------------------------
# values
# ---------------------------------------------------------------------------

class TestValues:
    def test_values_returns_list_of_dicts(self):
        result = Bank.objects.limit(3).values()
        assert isinstance(result, list)
        assert all(isinstance(row, dict) for row in result)

    def test_values_with_specific_fields(self):
        result = Bank.objects.limit(3).values("bank_id", "name")
        assert all(set(row.keys()) == {"bank_id", "name"} for row in result)

    def test_values_data_matches_objects(self):
        obj = Bank.objects.order_by("bank_id").first()
        row = Bank.objects.filter(bank_id=obj.bank_id).values("bank_id", "name")[0]
        assert row["bank_id"] == obj.bank_id
        assert row["name"] == obj.name


# ---------------------------------------------------------------------------
# Python protocols
# ---------------------------------------------------------------------------

class TestProtocols:
    def test_iterable(self):
        banks = list(Bank.objects.limit(3))
        assert isinstance(banks, list)
        assert all(isinstance(b, Bank) for b in banks)

    def test_len(self):
        qs = Bank.objects.filter(hidden=0)
        assert len(qs) == qs.count()

    def test_repr(self):
        assert "Bank" in repr(Bank.objects)


# ---------------------------------------------------------------------------
# Multiple models
# ---------------------------------------------------------------------------

class TestMultipleModels:
    def test_users_count(self):
        count = Users.objects.count()
        assert isinstance(count, int)
        assert count >= 0

    def test_users_filter_by_hidden(self):
        result = Users.objects.filter(hidden=0).all()
        assert all(u.hidden == 0 for u in result)
