"""Write tests for model_detail (vehicle card) and model_link."""

from __future__ import annotations

from datetime import date

import pytest

from autodealer.domain.directory_registry import DirectoryRegistry
from autodealer.domain.model_detail import ModelDetail
from autodealer.domain.model_link import ModelLink
from autodealer.queryset import DoesNotExist

TEST_DIR_ID    = 99903
TEST_DETAIL_ID = 99901
TEST_LINK_ID   = 99901
SYSTEM_USER    = 1

# Используем model_id=7 (Audi A3) — существует в StOm1.fdb
MODEL_ID = 7


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup():
    ModelLink.objects.filter(model_link_id=TEST_LINK_ID).delete()
    ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).delete()
    DirectoryRegistry.objects.filter(directory_registry_id=TEST_DIR_ID).delete()
    yield
    ModelLink.objects.filter(model_link_id=TEST_LINK_ID).delete()
    ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).delete()
    DirectoryRegistry.objects.filter(directory_registry_id=TEST_DIR_ID).delete()


def _make_dir() -> DirectoryRegistry:
    return DirectoryRegistry.objects.create(
        directory_registry_id=TEST_DIR_ID,
        metatable_id=4,  # MODEL_DETAIL
        create_user_id=SYSTEM_USER,
        change_user_id=SYSTEM_USER,
    )


def _make_detail(**kw) -> ModelDetail:
    defaults = dict(
        model_detail_id=TEST_DETAIL_ID,
        directory_registry_id=TEST_DIR_ID,
        model_id=MODEL_ID,
        regno="Т001ЕС99",
        vin="TESTZZ8P9BA000001",
    )
    defaults.update(kw)
    return ModelDetail.objects.create(**defaults)


def _make_link(**kw) -> ModelLink:
    defaults = dict(
        model_link_id=TEST_LINK_ID,
        model_detail_id=TEST_DETAIL_ID,
        hidden=0,
        default_car=1,
    )
    defaults.update(kw)
    return ModelLink.objects.create(**defaults)


# ---------------------------------------------------------------------------
# model_detail — create
# ---------------------------------------------------------------------------

class TestModelDetailCreate:
    def test_create_returns_instance(self):
        _make_dir()
        d = _make_detail()
        assert isinstance(d, ModelDetail)

    def test_create_persists(self):
        _make_dir()
        _make_detail()
        d = ModelDetail.objects.get(model_detail_id=TEST_DETAIL_ID)
        assert d.model_id == MODEL_ID
        assert d.regno == "Т001ЕС99"
        assert d.vin == "TESTZZ8P9BA000001"

    def test_create_increases_count(self):
        _make_dir()
        before = ModelDetail.objects.count()
        _make_detail()
        assert ModelDetail.objects.count() == before + 1

    def test_create_with_color(self):
        _make_dir()
        _make_detail(color_id=1)  # Белый — seeded
        d = ModelDetail.objects.get(model_detail_id=TEST_DETAIL_ID)
        assert d.color_id == 1

    def test_create_with_year(self):
        _make_dir()
        _make_detail(year_of_production=date(2021, 5, 20))
        d = ModelDetail.objects.get(model_detail_id=TEST_DETAIL_ID)
        assert d.year_of_production == date(2021, 5, 20)

    def test_create_with_gearbox_and_engine(self):
        _make_dir()
        _make_detail(car_engine_type_id=1, car_gearbox_type_id=2)
        d = ModelDetail.objects.get(model_detail_id=TEST_DETAIL_ID)
        assert d.car_engine_type_id == 1
        assert d.car_gearbox_type_id == 2

    def test_create_with_body_type(self):
        _make_dir()
        _make_detail(car_body_type_id=1)  # Седан
        d = ModelDetail.objects.get(model_detail_id=TEST_DETAIL_ID)
        assert d.car_body_type_id == 1


# ---------------------------------------------------------------------------
# model_detail — update
# ---------------------------------------------------------------------------

class TestModelDetailUpdate:
    def test_update_regno(self):
        _make_dir()
        _make_detail()
        ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).update(regno="Х999УУ77")
        d = ModelDetail.objects.get(model_detail_id=TEST_DETAIL_ID)
        assert d.regno == "Х999УУ77"

    def test_update_returns_rowcount(self):
        _make_dir()
        _make_detail()
        rows = ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).update(notes="после ТО")
        assert rows == 1

    def test_update_color(self):
        _make_dir()
        _make_detail(color_id=1)
        ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).update(color_id=2)
        d = ModelDetail.objects.get(model_detail_id=TEST_DETAIL_ID)
        assert d.color_id == 2

    def test_update_no_match(self):
        rows = ModelDetail.objects.filter(model_detail_id=-9999).update(regno="X")
        assert rows == 0


# ---------------------------------------------------------------------------
# model_detail — delete
# ---------------------------------------------------------------------------

class TestModelDetailDelete:
    def test_delete_returns_rowcount(self):
        _make_dir()
        _make_detail()
        rows = ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).delete()
        assert rows == 1

    def test_delete_removes(self):
        _make_dir()
        _make_detail()
        ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).delete()
        with pytest.raises(DoesNotExist):
            ModelDetail.objects.get(model_detail_id=TEST_DETAIL_ID)

    def test_delete_decreases_count(self):
        _make_dir()
        _make_detail()
        before = ModelDetail.objects.count()
        ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).delete()
        assert ModelDetail.objects.count() == before - 1


# ---------------------------------------------------------------------------
# model_link — create / update / delete
# ---------------------------------------------------------------------------

class TestModelLink:
    def test_create_returns_instance(self):
        _make_dir()
        _make_detail()
        lnk = _make_link()
        assert isinstance(lnk, ModelLink)

    def test_create_persists(self):
        _make_dir()
        _make_detail()
        _make_link()
        lnk = ModelLink.objects.get(model_link_id=TEST_LINK_ID)
        assert lnk.model_detail_id == TEST_DETAIL_ID
        assert lnk.default_car == 1

    def test_update_default_car(self):
        _make_dir()
        _make_detail()
        _make_link(default_car=1)
        ModelLink.objects.filter(model_link_id=TEST_LINK_ID).update(default_car=0)
        lnk = ModelLink.objects.get(model_link_id=TEST_LINK_ID)
        assert lnk.default_car == 0

    def test_update_hidden(self):
        _make_dir()
        _make_detail()
        _make_link(hidden=0)
        ModelLink.objects.filter(model_link_id=TEST_LINK_ID).update(hidden=1)
        lnk = ModelLink.objects.get(model_link_id=TEST_LINK_ID)
        assert lnk.hidden == 1

    def test_delete_link(self):
        _make_dir()
        _make_detail()
        _make_link()
        ModelLink.objects.filter(model_link_id=TEST_LINK_ID).delete()
        with pytest.raises(DoesNotExist):
            ModelLink.objects.get(model_link_id=TEST_LINK_ID)


# ---------------------------------------------------------------------------
# Round-trip + seeded data
# ---------------------------------------------------------------------------

class TestVehicleRoundTrip:
    def test_full_lifecycle(self):
        _make_dir()
        _make_detail(regno="А001АА77")
        _make_link()

        ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).update(regno="В999ВВ99")
        d = ModelDetail.objects.get(model_detail_id=TEST_DETAIL_ID)
        assert d.regno == "В999ВВ99"

        ModelLink.objects.filter(model_link_id=TEST_LINK_ID).delete()
        ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).delete()
        assert ModelDetail.objects.filter(model_detail_id=TEST_DETAIL_ID).exists() is False

    def test_seeded_details_exist(self):
        assert ModelDetail.objects.count() >= 3

    def test_seeded_links_exist(self):
        assert ModelLink.objects.count() >= 3

    def test_seeded_detail_fields(self):
        d = ModelDetail.objects.get(model_detail_id=100)
        assert d.model_id == 7
        assert d.regno == "А123ВС77"
        assert d.car_gearbox_type_id == 2  # АКПП

    def test_seeded_link_default_car(self):
        lnk = ModelLink.objects.get(model_link_id=100)
        assert lnk.default_car == 1
        assert lnk.model_detail_id == 100

    def test_filter_by_model(self):
        assert ModelDetail.objects.filter(model_id=7).count() >= 1

    def test_filter_hidden_links(self):
        visible = ModelLink.objects.filter(hidden=0).count()
        assert visible >= 3
