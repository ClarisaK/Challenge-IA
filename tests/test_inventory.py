import pytest
from src.inventory import Inventory


def test_load_inventory_success():
    inventory = Inventory()
    units = inventory.get_all()
    assert len(units) == 5

    expected_ids = {"MIC-01", "MIC-02", "OSC-01", "MUL-01", "FUE-01"}
    actual_ids = {unit["id"] for unit in units}
    assert actual_ids == expected_ids


def test_inventory_units_content():
    inventory = Inventory()
    assert inventory.get_unit("MIC-01") == {"id": "MIC-01", "name": "Microscopio digital"}
    assert inventory.get_unit("MIC-02") == {"id": "MIC-02", "name": "Microscopio digital"}
    assert inventory.get_unit("OSC-01") == {"id": "OSC-01", "name": "Osciloscopio"}
    assert inventory.get_unit("MUL-01") == {"id": "MUL-01", "name": "Multímetro"}
    assert inventory.get_unit("FUE-01") == {"id": "FUE-01", "name": "Fuente de alimentación"}


def test_unit_exists():
    inventory = Inventory()
    for unit_id in ["MIC-01", "MIC-02", "OSC-01", "MUL-01", "FUE-01"]:
        assert inventory.exists(unit_id) is True


def test_unit_not_exists():
    inventory = Inventory()
    assert inventory.exists("INVENTADO-99") is False
    assert inventory.exists("") is False
    assert inventory.exists("OSC-02") is False
    assert inventory.get_unit("INVENTADO-99") is None
