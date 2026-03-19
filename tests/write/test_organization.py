"""Write tests for organization (and its directory_registry dependency)."""

from __future__ import annotations

from datetime import datetime

import pytest

from autodealer.domain.directory_registry import DirectoryRegistry
from autodealer.domain.organization import Organization
from autodealer.queryset import DoesNotExist

# Sentinel PKs — не пересекаются с реальными данными
TEST_DIR_ID = 99901
TEST_ORG_ID = 99901
# Системный пользователь, который уже есть в StOm1.fdb
SYSTEM_USER_ID = 1


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup():
    """Удаляем тестовые строки до и после каждого теста."""
    Organization.objects.filter(organization_id=TEST_ORG_ID).delete()
    DirectoryRegistry.objects.filter(directory_registry_id=TEST_DIR_ID).delete()
    yield
    Organization.objects.filter(organization_id=TEST_ORG_ID).delete()
    DirectoryRegistry.objects.filter(directory_registry_id=TEST_DIR_ID).delete()


def _make_dir_registry() -> DirectoryRegistry:
    return DirectoryRegistry.objects.create(
        directory_registry_id=TEST_DIR_ID,
        metatable_id=1,  # ORGANIZATION
        create_user_id=SYSTEM_USER_ID,
        change_user_id=SYSTEM_USER_ID,
    )


def _make_organization(**kwargs) -> Organization:
    defaults = dict(
        organization_id=TEST_ORG_ID,
        directory_registry_id=TEST_DIR_ID,
        fullname='ООО "Тест"',
        shortname="Тест",
        inn="7701234567",
        face=0,
        hidden=0,
        nds=0,
        can_sale=1,
        can_buy=1,
        date_closing_period=datetime(2020, 1, 1),
    )
    defaults.update(kwargs)
    return Organization.objects.create(**defaults)


# ---------------------------------------------------------------------------
# directory_registry
# ---------------------------------------------------------------------------

class TestDirectoryRegistry:
    def test_create_returns_instance(self):
        dr = _make_dir_registry()
        assert isinstance(dr, DirectoryRegistry)

    def test_create_persists(self):
        _make_dir_registry()
        dr = DirectoryRegistry.objects.get(directory_registry_id=TEST_DIR_ID)
        assert dr.metatable_id == 1
        assert dr.create_user_id == SYSTEM_USER_ID

    def test_create_increases_count(self):
        before = DirectoryRegistry.objects.count()
        _make_dir_registry()
        assert DirectoryRegistry.objects.count() == before + 1

    def test_delete_removes_record(self):
        _make_dir_registry()
        DirectoryRegistry.objects.filter(directory_registry_id=TEST_DIR_ID).delete()
        with pytest.raises(DoesNotExist):
            DirectoryRegistry.objects.get(directory_registry_id=TEST_DIR_ID)


# ---------------------------------------------------------------------------
# organization — create
# ---------------------------------------------------------------------------

class TestOrganizationCreate:
    def test_create_returns_instance(self):
        _make_dir_registry()
        org = _make_organization()
        assert isinstance(org, Organization)

    def test_create_persists(self):
        _make_dir_registry()
        _make_organization()
        org = Organization.objects.get(organization_id=TEST_ORG_ID)
        assert org.shortname == "Тест"
        assert org.inn == "7701234567"

    def test_create_increases_count(self):
        _make_dir_registry()
        before = Organization.objects.count()
        _make_organization()
        assert Organization.objects.count() == before + 1

    def test_default_hidden_is_zero(self):
        _make_dir_registry()
        _make_organization()
        org = Organization.objects.get(organization_id=TEST_ORG_ID)
        assert org.hidden == 0

    def test_optional_fields(self):
        _make_dir_registry()
        _make_organization(kpp="770101001", ogrn="1027700000000", address="г. Москва, ул. Тестовая, 1")
        org = Organization.objects.get(organization_id=TEST_ORG_ID)
        assert org.kpp == "770101001"
        assert org.ogrn == "1027700000000"
        assert org.address == "г. Москва, ул. Тестовая, 1"

    def test_individual_face(self):
        """face=1 — физическое лицо (ИП)."""
        _make_dir_registry()
        _make_organization(face=1, fullname="ИП Тестов Тест Тестович", inn="771234567890")
        org = Organization.objects.get(organization_id=TEST_ORG_ID)
        assert org.face == 1

    def test_can_sale_can_buy_flags(self):
        _make_dir_registry()
        _make_organization(can_sale=1, can_buy=0)
        org = Organization.objects.get(organization_id=TEST_ORG_ID)
        assert org.can_sale == 1
        assert org.can_buy == 0


# ---------------------------------------------------------------------------
# organization — update
# ---------------------------------------------------------------------------

class TestOrganizationUpdate:
    def test_update_shortname(self):
        _make_dir_registry()
        _make_organization()
        Organization.objects.filter(organization_id=TEST_ORG_ID).update(shortname="Новое имя")
        org = Organization.objects.get(organization_id=TEST_ORG_ID)
        assert org.shortname == "Новое имя"

    def test_update_returns_rowcount(self):
        _make_dir_registry()
        _make_organization()
        rows = Organization.objects.filter(organization_id=TEST_ORG_ID).update(hidden=1)
        assert rows == 1

    def test_update_hidden_flag(self):
        _make_dir_registry()
        _make_organization(hidden=0)
        Organization.objects.filter(organization_id=TEST_ORG_ID).update(hidden=1)
        org = Organization.objects.get(organization_id=TEST_ORG_ID)
        assert org.hidden == 1

    def test_update_nds_flag(self):
        _make_dir_registry()
        _make_organization(nds=0)
        Organization.objects.filter(organization_id=TEST_ORG_ID).update(nds=1)
        org = Organization.objects.get(organization_id=TEST_ORG_ID)
        assert org.nds == 1

    def test_update_no_match_returns_zero(self):
        rows = Organization.objects.filter(organization_id=-9999).update(shortname="X")
        assert rows == 0


# ---------------------------------------------------------------------------
# organization — delete
# ---------------------------------------------------------------------------

class TestOrganizationDelete:
    def test_delete_returns_rowcount(self):
        _make_dir_registry()
        _make_organization()
        rows = Organization.objects.filter(organization_id=TEST_ORG_ID).delete()
        assert rows == 1

    def test_delete_removes_record(self):
        _make_dir_registry()
        _make_organization()
        Organization.objects.filter(organization_id=TEST_ORG_ID).delete()
        with pytest.raises(DoesNotExist):
            Organization.objects.get(organization_id=TEST_ORG_ID)

    def test_delete_decreases_count(self):
        _make_dir_registry()
        _make_organization()
        before = Organization.objects.count()
        Organization.objects.filter(organization_id=TEST_ORG_ID).delete()
        assert Organization.objects.count() == before - 1


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

class TestOrganizationRoundTrip:
    def test_full_lifecycle(self):
        """create → update → get → delete."""
        _make_dir_registry()
        _make_organization(shortname="v1", inn="1111111111")

        Organization.objects.filter(organization_id=TEST_ORG_ID).update(
            shortname="v2", inn="2222222222"
        )
        org = Organization.objects.get(organization_id=TEST_ORG_ID)
        assert org.shortname == "v2"
        assert org.inn == "2222222222"

        Organization.objects.filter(organization_id=TEST_ORG_ID).delete()
        assert Organization.objects.filter(organization_id=TEST_ORG_ID).exists() is False

    def test_seeded_organizations_exist(self):
        """Проверяем, что данные из seed_test_db попали в БД."""
        assert Organization.objects.filter(organization_id=100).exists()
        assert Organization.objects.filter(organization_id=101).exists()

    def test_seeded_org_fields(self):
        org = Organization.objects.get(organization_id=100)
        assert org.inn == "7701234567"
        assert org.can_sale == 1
