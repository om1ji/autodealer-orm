"""Write tests for shop_nomenclature_tree and shop_nomenclature."""

from __future__ import annotations

from decimal import Decimal

import pytest

from autodealer.domain.directory_registry import DirectoryRegistry
from autodealer.domain.shop_nomenclature import ShopNomenclature
from autodealer.domain.shop_nomenclature_tree import ShopNomenclatureTree
from autodealer.queryset import DoesNotExist

TEST_TREE_ID  = 99901
TEST_DIR_ID   = 99904
TEST_NOM_ID   = 99901
SYSTEM_USER   = 1

# Обязательные FK, уже есть в БД
GOODS_TYPE_ID   = 1   # Запасные части
UNIT_ID         = 1   # шт
TAX_SCHEMES_ID  = 1   # Общее налогообложение


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup():
    ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).delete()
    DirectoryRegistry.objects.filter(directory_registry_id=TEST_DIR_ID).delete()
    ShopNomenclatureTree.objects.filter(shop_nomenclature_tree_id=TEST_TREE_ID).delete()
    yield
    ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).delete()
    DirectoryRegistry.objects.filter(directory_registry_id=TEST_DIR_ID).delete()
    ShopNomenclatureTree.objects.filter(shop_nomenclature_tree_id=TEST_TREE_ID).delete()


def _make_tree(**kw) -> ShopNomenclatureTree:
    defaults = dict(shop_nomenclature_tree_id=TEST_TREE_ID, name="Тест-категория", parent_id=None)
    defaults.update(kw)
    return ShopNomenclatureTree.objects.create(**defaults)


def _make_dir() -> DirectoryRegistry:
    return DirectoryRegistry.objects.create(
        directory_registry_id=TEST_DIR_ID,
        metatable_id=13,  # SHOP_NOMENCLATURE
        create_user_id=SYSTEM_USER,
        change_user_id=SYSTEM_USER,
    )


def _make_nom(**kw) -> ShopNomenclature:
    defaults = dict(
        shop_nomenclature_id=TEST_NOM_ID,
        directory_registry_id=TEST_DIR_ID,
        fullname="Тест-запчасть",
        shortname="Тест",
        goods_type_id=GOODS_TYPE_ID,
        unit_id=UNIT_ID,
        tax_schemes_id=TAX_SCHEMES_ID,
        tax_schemes_material_id=TAX_SCHEMES_ID,
        default_cost=Decimal("500.00"),
        default_margin=Decimal("25.00"),
        default_count=Decimal("1"),
    )
    defaults.update(kw)
    return ShopNomenclature.objects.create(**defaults)


# ---------------------------------------------------------------------------
# shop_nomenclature_tree
# ---------------------------------------------------------------------------

class TestShopNomenclatureTree:
    def test_create_returns_instance(self):
        t = _make_tree()
        assert isinstance(t, ShopNomenclatureTree)

    def test_create_persists(self):
        _make_tree()
        t = ShopNomenclatureTree.objects.get(shop_nomenclature_tree_id=TEST_TREE_ID)
        assert t.name == "Тест-категория"

    def test_create_with_parent(self):
        _make_tree(parent_id=1)   # seeded parent
        t = ShopNomenclatureTree.objects.get(shop_nomenclature_tree_id=TEST_TREE_ID)
        assert t.parent_id == 1

    def test_update_name(self):
        _make_tree()
        ShopNomenclatureTree.objects.filter(shop_nomenclature_tree_id=TEST_TREE_ID).update(name="Переименовано")
        t = ShopNomenclatureTree.objects.get(shop_nomenclature_tree_id=TEST_TREE_ID)
        assert t.name == "Переименовано"

    def test_delete(self):
        _make_tree()
        ShopNomenclatureTree.objects.filter(shop_nomenclature_tree_id=TEST_TREE_ID).delete()
        with pytest.raises(DoesNotExist):
            ShopNomenclatureTree.objects.get(shop_nomenclature_tree_id=TEST_TREE_ID)

    def test_seeded_trees_exist(self):
        assert ShopNomenclatureTree.objects.count() >= 5

    def test_seeded_tree_hierarchy(self):
        child = ShopNomenclatureTree.objects.get(shop_nomenclature_tree_id=3)  # Масла → parent=2
        assert child.parent_id == 2


# ---------------------------------------------------------------------------
# shop_nomenclature — create
# ---------------------------------------------------------------------------

class TestShopNomenclatureCreate:
    def test_create_returns_instance(self):
        _make_dir()
        n = _make_nom()
        assert isinstance(n, ShopNomenclature)

    def test_create_persists(self):
        _make_dir()
        _make_nom()
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.fullname == "Тест-запчасть"
        assert n.goods_type_id == GOODS_TYPE_ID
        assert n.unit_id == UNIT_ID

    def test_create_increases_count(self):
        _make_dir()
        before = ShopNomenclature.objects.count()
        _make_nom()
        assert ShopNomenclature.objects.count() == before + 1

    def test_create_with_article(self):
        _make_dir()
        _make_nom(number_manufacture="TEST-001", number_original="OEM-001")
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.number_manufacture == "TEST-001"
        assert n.number_original == "OEM-001"

    def test_create_with_producer_and_country(self):
        _make_dir()
        _make_nom(producer_id=1, country_id=1)
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.producer_id == 1
        assert n.country_id == 1

    def test_create_with_tree(self):
        _make_dir()
        _make_nom(shop_nomenclature_tree_id=1)
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.shop_nomenclature_tree_id == 1

    def test_create_with_cost_and_margin(self):
        _make_dir()
        _make_nom(default_cost=Decimal("1500.00"), default_margin=Decimal("30.00"))
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.default_cost == Decimal("1500.00")
        assert n.default_margin == Decimal("30.00")

    def test_create_with_stock_limits(self):
        _make_dir()
        _make_nom(stock_min=Decimal("5.00"), stock_max=Decimal("50.00"))
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.stock_min == Decimal("5.00")
        assert n.stock_max == Decimal("50.00")

    def test_create_with_barcode(self):
        _make_dir()
        _make_nom(bar_code="4607026900001")
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.bar_code == "4607026900001"


# ---------------------------------------------------------------------------
# shop_nomenclature — update
# ---------------------------------------------------------------------------

class TestShopNomenclatureUpdate:
    def test_update_fullname(self):
        _make_dir()
        _make_nom()
        ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).update(fullname="Обновлённая запчасть")
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.fullname == "Обновлённая запчасть"

    def test_update_returns_rowcount(self):
        _make_dir()
        _make_nom()
        rows = ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).update(default_cost=Decimal("999.00"))
        assert rows == 1

    def test_update_cost(self):
        _make_dir()
        _make_nom(default_cost=Decimal("500.00"))
        ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).update(default_cost=Decimal("750.00"))
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.default_cost == Decimal("750.00")

    def test_update_article(self):
        _make_dir()
        _make_nom()
        ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).update(number_manufacture="NEW-999")
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.number_manufacture == "NEW-999"

    def test_update_no_match(self):
        rows = ShopNomenclature.objects.filter(shop_nomenclature_id=-9999).update(fullname="X")
        assert rows == 0


# ---------------------------------------------------------------------------
# shop_nomenclature — delete
# ---------------------------------------------------------------------------

class TestShopNomenclatureDelete:
    def test_delete_returns_rowcount(self):
        _make_dir()
        _make_nom()
        rows = ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).delete()
        assert rows == 1

    def test_delete_removes(self):
        _make_dir()
        _make_nom()
        ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).delete()
        with pytest.raises(DoesNotExist):
            ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)

    def test_delete_decreases_count(self):
        _make_dir()
        _make_nom()
        before = ShopNomenclature.objects.count()
        ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).delete()
        assert ShopNomenclature.objects.count() == before - 1


# ---------------------------------------------------------------------------
# Round-trip + seeded data
# ---------------------------------------------------------------------------

class TestShopNomenclatureRoundTrip:
    def test_full_lifecycle(self):
        _make_dir()
        _make_nom(fullname="v1", default_cost=Decimal("100.00"))

        ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).update(
            fullname="v2", default_cost=Decimal("200.00")
        )
        n = ShopNomenclature.objects.get(shop_nomenclature_id=TEST_NOM_ID)
        assert n.fullname == "v2"
        assert n.default_cost == Decimal("200.00")

        ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).delete()
        assert ShopNomenclature.objects.filter(shop_nomenclature_id=TEST_NOM_ID).exists() is False

    def test_seeded_nomenclatures_exist(self):
        assert ShopNomenclature.objects.count() >= 5

    def test_seeded_oil_filter(self):
        n = ShopNomenclature.objects.get(shop_nomenclature_id=100)
        assert n.number_manufacture == "0986AF0"
        assert n.producer_id == 1  # Bosch
        assert n.default_cost == Decimal("850.0000")

    def test_seeded_oil(self):
        n = ShopNomenclature.objects.get(shop_nomenclature_id=102)
        assert n.unit_id == 2   # литры
        assert n.goods_type_id == 4  # Масла и жидкости

    def test_filter_by_goods_type(self):
        spare_parts = ShopNomenclature.objects.filter(goods_type_id=1).count()
        assert spare_parts >= 3

    def test_filter_by_producer(self):
        bosch = ShopNomenclature.objects.filter(producer_id=1).count()
        assert bosch >= 2

    def test_filter_by_tree(self):
        filters = ShopNomenclature.objects.filter(shop_nomenclature_tree_id=4).count()
        assert filters >= 2  # масляный + воздушный фильтр

    def test_search_by_article(self):
        n = ShopNomenclature.objects.filter(number_manufacture__icontains="0986AF0").first()
        assert n is not None
        assert n.shop_nomenclature_id == 100
