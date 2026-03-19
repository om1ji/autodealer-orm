"""Write tests for client_tree and client."""

from __future__ import annotations

import pytest

from autodealer.domain.client import Client
from autodealer.domain.client_tree import ClientTree
from autodealer.domain.directory_registry import DirectoryRegistry
from autodealer.queryset import DoesNotExist

TEST_TREE_ID = 99901
TEST_DIR_ID  = 99902
TEST_CLI_ID  = 99901
SYSTEM_USER  = 1


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup():
    Client.objects.filter(client_id=TEST_CLI_ID).delete()
    DirectoryRegistry.objects.filter(directory_registry_id=TEST_DIR_ID).delete()
    ClientTree.objects.filter(client_tree_id=TEST_TREE_ID).delete()
    yield
    Client.objects.filter(client_id=TEST_CLI_ID).delete()
    DirectoryRegistry.objects.filter(directory_registry_id=TEST_DIR_ID).delete()
    ClientTree.objects.filter(client_tree_id=TEST_TREE_ID).delete()


def _make_tree(**kw) -> ClientTree:
    defaults = dict(client_tree_id=TEST_TREE_ID, name="Тест-группа", parent_id=None)
    defaults.update(kw)
    return ClientTree.objects.create(**defaults)


def _make_dir() -> DirectoryRegistry:
    return DirectoryRegistry.objects.create(
        directory_registry_id=TEST_DIR_ID,
        metatable_id=3,  # CLIENT
        create_user_id=SYSTEM_USER,
        change_user_id=SYSTEM_USER,
    )


def _make_client(**kw) -> Client:
    defaults = dict(
        client_id=TEST_CLI_ID,
        directory_registry_id=TEST_DIR_ID,
        fullname="Тестов Тест Тестович",
        shortname="Тестов Т.Т.",
        face=0,
        hidden=0,
        discount=0.0,
        discount_work=0.0,
    )
    defaults.update(kw)
    return Client.objects.create(**defaults)


# ---------------------------------------------------------------------------
# client_tree
# ---------------------------------------------------------------------------

class TestClientTree:
    def test_create_returns_instance(self):
        t = _make_tree()
        assert isinstance(t, ClientTree)

    def test_create_persists(self):
        _make_tree()
        t = ClientTree.objects.get(client_tree_id=TEST_TREE_ID)
        assert t.name == "Тест-группа"

    def test_create_with_parent(self):
        # client_tree_id=1 уже есть (seeded)
        _make_tree(parent_id=1)
        t = ClientTree.objects.get(client_tree_id=TEST_TREE_ID)
        assert t.parent_id == 1

    def test_update_name(self):
        _make_tree()
        ClientTree.objects.filter(client_tree_id=TEST_TREE_ID).update(name="Переименовано")
        t = ClientTree.objects.get(client_tree_id=TEST_TREE_ID)
        assert t.name == "Переименовано"

    def test_delete(self):
        _make_tree()
        ClientTree.objects.filter(client_tree_id=TEST_TREE_ID).delete()
        with pytest.raises(DoesNotExist):
            ClientTree.objects.get(client_tree_id=TEST_TREE_ID)


# ---------------------------------------------------------------------------
# client — create
# ---------------------------------------------------------------------------

class TestClientCreate:
    def test_create_returns_instance(self):
        _make_dir()
        c = _make_client()
        assert isinstance(c, Client)

    def test_create_persists(self):
        _make_dir()
        _make_client()
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.fullname == "Тестов Тест Тестович"
        assert c.shortname == "Тестов Т.Т."

    def test_create_increases_count(self):
        _make_dir()
        before = Client.objects.count()
        _make_client()
        assert Client.objects.count() == before + 1

    def test_default_hidden_is_zero(self):
        _make_dir()
        _make_client()
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.hidden == 0

    def test_individual_client(self):
        _make_dir()
        _make_client(face=0, fullname="Физлицо Иван", shortname="Физлицо")
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.face == 0

    def test_legal_client(self):
        _make_dir()
        _make_client(face=1, fullname='ООО "Тест"', inn="7701234567", kpp="770101001")
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.face == 1
        assert c.inn == "7701234567"

    def test_client_with_discount(self):
        _make_dir()
        _make_client(discount=10.0, discount_work=5.0)
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.discount == 10.0
        assert c.discount_work == 5.0

    def test_client_with_tree(self):
        _make_dir()
        _make_client(client_tree_id=1)  # seeded tree_id=1
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.client_tree_id == 1

    def test_client_with_source_info(self):
        _make_dir()
        _make_client(source_info_id=1)  # seeded
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.source_info_id == 1


# ---------------------------------------------------------------------------
# client — update
# ---------------------------------------------------------------------------

class TestClientUpdate:
    def test_update_fullname(self):
        _make_dir()
        _make_client()
        Client.objects.filter(client_id=TEST_CLI_ID).update(fullname="Обновлённое имя")
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.fullname == "Обновлённое имя"

    def test_update_returns_rowcount(self):
        _make_dir()
        _make_client()
        rows = Client.objects.filter(client_id=TEST_CLI_ID).update(hidden=1)
        assert rows == 1

    def test_update_hidden(self):
        _make_dir()
        _make_client(hidden=0)
        Client.objects.filter(client_id=TEST_CLI_ID).update(hidden=1)
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.hidden == 1

    def test_update_discount(self):
        _make_dir()
        _make_client(discount=0.0)
        Client.objects.filter(client_id=TEST_CLI_ID).update(discount=15.0)
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.discount == 15.0

    def test_update_no_match(self):
        rows = Client.objects.filter(client_id=-9999).update(fullname="X")
        assert rows == 0


# ---------------------------------------------------------------------------
# client — delete
# ---------------------------------------------------------------------------

class TestClientDelete:
    def test_delete_returns_rowcount(self):
        _make_dir()
        _make_client()
        rows = Client.objects.filter(client_id=TEST_CLI_ID).delete()
        assert rows == 1

    def test_delete_removes(self):
        _make_dir()
        _make_client()
        Client.objects.filter(client_id=TEST_CLI_ID).delete()
        with pytest.raises(DoesNotExist):
            Client.objects.get(client_id=TEST_CLI_ID)

    def test_delete_decreases_count(self):
        _make_dir()
        _make_client()
        before = Client.objects.count()
        Client.objects.filter(client_id=TEST_CLI_ID).delete()
        assert Client.objects.count() == before - 1


# ---------------------------------------------------------------------------
# Round-trip + seeded data
# ---------------------------------------------------------------------------

class TestClientRoundTrip:
    def test_full_lifecycle(self):
        _make_dir()
        _make_client(fullname="v1", discount=0.0)

        Client.objects.filter(client_id=TEST_CLI_ID).update(fullname="v2", discount=7.0)
        c = Client.objects.get(client_id=TEST_CLI_ID)
        assert c.fullname == "v2"
        assert c.discount == 7.0

        Client.objects.filter(client_id=TEST_CLI_ID).delete()
        assert Client.objects.filter(client_id=TEST_CLI_ID).exists() is False

    def test_seeded_clients_exist(self):
        assert Client.objects.count() >= 4

    def test_seeded_physical_client(self):
        c = Client.objects.get(client_id=100)
        assert c.face == 0
        assert c.fullname == "Иванов Иван Иванович"

    def test_seeded_legal_client(self):
        c = Client.objects.get(client_id=102)
        assert c.face == 1
        assert c.inn == "7712345678"

    def test_filter_hidden(self):
        active = Client.objects.filter(hidden=0).count()
        assert active >= 3

    def test_filter_by_face(self):
        individuals = Client.objects.filter(face=0, hidden=0).count()
        assert individuals >= 2
