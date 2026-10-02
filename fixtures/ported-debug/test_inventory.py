import pytest

from inventory import Inventory


def test_restock_then_reserve():
    inv = Inventory()
    inv.restock("WH-001", 10)
    assert inv.reserve("WH-001", 3) == 7


def test_reserve_unknown_sku_raises():
    inv = Inventory()
    with pytest.raises(KeyError):
        inv.reserve("WH-404", 1)


def test_reserve_more_than_available_raises():
    inv = Inventory()
    inv.restock("WH-001", 2)
    with pytest.raises(ValueError):
        inv.reserve("WH-001", 5)


def test_available_unknown_sku_is_zero():
    inv = Inventory()
    assert inv.available("WH-404") == 0


def test_restock_rejects_non_positive_quantity():
    inv = Inventory()
    with pytest.raises(ValueError):
        inv.restock("WH-001", 0)
