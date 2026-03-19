"""Write operation tests (create / update / delete) against StOm1.fdb.

Each test is fully isolated: it creates the records it needs, then removes
them in a teardown fixture so the DB is left clean.
"""

from __future__ import annotations

import pytest

from autodealer.domain.bank import Bank
from autodealer.queryset import DoesNotExist

# Sentinel PK — unlikely to collide with real data in the test DB.
TEST_BANK_ID = 99900


# ---------------------------------------------------------------------------
# Shared fixture: ensure the sentinel row is absent before and after each test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup():
    """Remove sentinel rows before and after every test."""
    Bank.objects.filter(bank_id=TEST_BANK_ID).delete()
    yield
    Bank.objects.filter(bank_id=TEST_BANK_ID).delete()


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------

class TestCreate:
    def test_create_returns_instance(self):
        bank = Bank.objects.create(bank_id=TEST_BANK_ID, name="Тест-Банк")
        assert isinstance(bank, Bank)

    def test_create_persists_to_db(self):
        Bank.objects.create(bank_id=TEST_BANK_ID, name="Тест-Банк", bik="044525001")
        fetched = Bank.objects.get(bank_id=TEST_BANK_ID)
        assert fetched.name == "Тест-Банк"
        assert fetched.bik == "044525001"

    def test_create_sets_optional_fields(self):
        Bank.objects.create(
            bank_id=TEST_BANK_ID,
            name="Тест-Банк",
            address="ул. Тестовая, 1",
            notes="автотест",
        )
        bank = Bank.objects.get(bank_id=TEST_BANK_ID)
        assert bank.address == "ул. Тестовая, 1"
        assert bank.notes == "автотест"

    def test_create_default_hidden_is_zero(self):
        Bank.objects.create(bank_id=TEST_BANK_ID, name="Тест-Банк")
        bank = Bank.objects.get(bank_id=TEST_BANK_ID)
        assert bank.hidden == 0

    def test_create_increases_count(self):
        before = Bank.objects.count()
        Bank.objects.create(bank_id=TEST_BANK_ID, name="Тест-Банк")
        assert Bank.objects.count() == before + 1


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------

class TestUpdate:
    def test_update_returns_rowcount(self):
        Bank.objects.create(bank_id=TEST_BANK_ID, name="До")
        rows = Bank.objects.filter(bank_id=TEST_BANK_ID).update(name="После")
        assert rows == 1

    def test_update_persists_change(self):
        Bank.objects.create(bank_id=TEST_BANK_ID, name="До")
        Bank.objects.filter(bank_id=TEST_BANK_ID).update(name="После", bik="000000000")
        bank = Bank.objects.get(bank_id=TEST_BANK_ID)
        assert bank.name == "После"
        assert bank.bik == "000000000"

    def test_update_hidden_flag(self):
        Bank.objects.create(bank_id=TEST_BANK_ID, name="Тест-Банк", hidden=0)
        Bank.objects.filter(bank_id=TEST_BANK_ID).update(hidden=1)
        bank = Bank.objects.get(bank_id=TEST_BANK_ID)
        assert bank.hidden == 1

    def test_update_no_match_returns_zero(self):
        rows = Bank.objects.filter(bank_id=-9999).update(name="X")
        assert rows == 0

    def test_update_does_not_touch_other_rows(self):
        Bank.objects.create(bank_id=TEST_BANK_ID, name="Тест-Банк")
        count_before = Bank.objects.count()
        Bank.objects.filter(bank_id=TEST_BANK_ID).update(name="Изменён")
        assert Bank.objects.count() == count_before


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_returns_rowcount(self):
        Bank.objects.create(bank_id=TEST_BANK_ID, name="Удалить")
        rows = Bank.objects.filter(bank_id=TEST_BANK_ID).delete()
        assert rows == 1

    def test_delete_removes_from_db(self):
        Bank.objects.create(bank_id=TEST_BANK_ID, name="Удалить")
        Bank.objects.filter(bank_id=TEST_BANK_ID).delete()
        with pytest.raises(DoesNotExist):
            Bank.objects.get(bank_id=TEST_BANK_ID)

    def test_delete_no_match_returns_zero(self):
        rows = Bank.objects.filter(bank_id=-9999).delete()
        assert rows == 0

    def test_delete_decreases_count(self):
        Bank.objects.create(bank_id=TEST_BANK_ID, name="Удалить")
        before = Bank.objects.count()
        Bank.objects.filter(bank_id=TEST_BANK_ID).delete()
        assert Bank.objects.count() == before - 1


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_create_update_delete(self):
        """Full lifecycle: create → update → verify → delete."""
        Bank.objects.create(bank_id=TEST_BANK_ID, name="v1", bik="111")
        Bank.objects.filter(bank_id=TEST_BANK_ID).update(name="v2", bik="222")

        bank = Bank.objects.get(bank_id=TEST_BANK_ID)
        assert bank.name == "v2"
        assert bank.bik == "222"

        Bank.objects.filter(bank_id=TEST_BANK_ID).delete()
        assert Bank.objects.filter(bank_id=TEST_BANK_ID).exists() is False
