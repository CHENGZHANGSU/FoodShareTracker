import json
from datetime import date
from pathlib import Path

import pytest

from app.food.food_item import FoodItem
from app.food.inventory import Inventory


@pytest.fixture
def inventory_path(tmp_path) -> Path:
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "inventory": [
                    {
                        "_id": 1,
                        "_name": "Expired Rice",
                        "_category": "Grains",
                        "_stock": 5,
                        "_unit": "kg",
                        "_tags": [],
                        "_inDate": "2026-10-01",
                        "_expiryDate": "2026-10-22",
                    },
                    {
                        "_id": 2,
                        "_name": "Fresh Rice",
                        "_category": "Grains",
                        "_stock": 3,
                        "_unit": "kg",
                        "_tags": [],
                        "_inDate": "2026-10-01",
                        "_expiryDate": "2026-10-24",
                    },
                ],
                "next_food_id": 3,
                "minimum_stock": {"1": 6, "2": 2},
            }
        ),
        encoding="utf-8",
    )
    return inventory_path


@pytest.fixture
def inventory(inventory_path: Path) -> Inventory:
    return Inventory(str(inventory_path))


def test_inventory_loads_food_items_and_expiry_dates(inventory: Inventory):
    # ARRANGE: Load food entries with one past and one future expiry date.
    # ACT: Read the food items and expired-food report.
    foods = inventory.get_inventory()
    expired_foods = inventory.get_expired_foods(today=date(2026, 10, 23))

    # ASSERT: Confirm food data is loaded and only expired stock is reported.
    assert [food.get_food_name() for food in foods] == [
        "Expired Rice",
        "Fresh Rice",
    ]
    assert [food.get_food_expiry_date() for food in foods] == [
        "2026-10-22",
        "2026-10-24",
    ]
    assert [food.get_food_name() for food in expired_foods] == ["Expired Rice"]


def test_inventory_adds_food_and_rejects_duplicate_name(inventory: Inventory):
    # ARRANGE: Create a food item whose name is not in the inventory.
    new_food = FoodItem(3, "Beans", "Legumes", 4, "kg", ["vegan"])

    # ACT: Add it, then try to add another item with the same name.
    added = inventory.add_food_to_inventory(new_food)
    duplicate_added = inventory.add_food_to_inventory(
        FoodItem(4, " beans ", "Legumes", 1, "kg", [])
    )

    # ASSERT: Confirm unique names are enforced and IDs advance.
    assert added is True
    assert duplicate_added is False
    assert inventory.find_food_by_id(3) is new_food


def test_inventory_updates_and_persists_food_fields(
    inventory: Inventory,
    inventory_path: Path,
):
    # ARRANGE: Select the existing fresh food.
    food = inventory.find_food_by_id(2)
    assert food is not None

    # ACT: Update its name, quantity, and expiry date.
    inventory.update_food_from_inventory(
        2,
        name="Brown Rice",
        stock=7,
        expiry_date="2026-11-01",
    )
    saved_data = json.loads(
        inventory_path.read_text(encoding="utf-8")
    )

    # ASSERT: Confirm object state and persisted JSON match.
    assert food.get_food_name() == "Brown Rice"
    assert food.get_food_stocks() == 7
    assert food.get_food_expiry_date() == "2026-11-01"
    assert saved_data["inventory"][1]["_name"] == "Brown Rice"
    assert saved_data["inventory"][1]["_stock"] == 7
    assert saved_data["inventory"][1]["_expiryDate"] == "2026-11-01"


def test_inventory_rejects_invalid_stock_and_expiry_values(inventory: Inventory):
    # ARRANGE: Select the existing food item.
    food = inventory.find_food_by_id(1)
    assert food is not None
    original_stock = food.get_food_stocks()
    original_expiry = food.get_food_expiry_date()

    # ACT / ASSERT: Invalid values raise errors without mutating the item.
    with pytest.raises(ValueError, match="cannot be negative"):
        inventory.update_food_from_inventory(1, stock=-1)
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        inventory.update_food_from_inventory(1, expiry_date="not-a-date")

    assert food.get_food_stocks() == original_stock
    assert food.get_food_expiry_date() == original_expiry


@pytest.mark.parametrize("stock", [float("nan"), float("inf"), float("-inf")])
def test_inventory_rejects_non_finite_stock(inventory: Inventory, stock: float):
    food = inventory.find_food_by_id(1)
    assert food is not None
    original_stock = food.get_food_stocks()

    with pytest.raises(ValueError, match="finite"):
        inventory.update_food_from_inventory(1, stock=stock)

    assert food.get_food_stocks() == original_stock


def test_missing_inventory_file_can_be_saved_to_new_parent(tmp_path: Path):
    inventory_path = tmp_path / "new" / "inventory.json"
    inventory = Inventory(str(inventory_path))

    assert inventory.get_inventory() == []
    inventory.set_inventory([])
    assert inventory_path.is_file()


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("{", "invalid JSON"),
        ('{"inventory": [{"_id": 1}]}', "missing required data"),
        ('{"inventory": {}}', "must be a list"),
        (
            '{"inventory": [], "minimum_stock": {"1": "not-a-number"}}',
            "threshold.*invalid",
        ),
    ],
)
def test_invalid_inventory_data_is_reported(
    tmp_path: Path,
    contents: str,
    message: str,
):
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        Inventory(str(inventory_path))


def test_inventory_reports_low_stock_items(inventory: Inventory):
    # ARRANGE: Inventory has minimum quantities for both foods.
    # ACT: Request the low-stock items.
    low_stock_foods = inventory.get_low_stock_foods()

    # ASSERT: Only the item below its minimum is returned.
    assert [food.get_food_name() for food in low_stock_foods] == ["Expired Rice"]


def test_inventory_adjusts_stock_and_records_incoming_quantity(
    inventory: Inventory,
    inventory_path: Path,
):
    # ARRANGE: Select the existing item and its current quantity.
    food = inventory.find_food_by_id(2)
    assert food is not None

    # ACT: Add incoming stock and then correct the total quantity.
    inventory.record_incoming_stock(2, 4)
    assert food.get_food_stocks() == 7
    inventory.adjust_stock(2, 6, "Stocktake correction")

    # ASSERT: Confirm the latest total is saved without batch records.
    saved_data = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert food.get_food_stocks() == 6
    assert saved_data["inventory"][1]["_stock"] == 6
    assert "stock_records" not in saved_data


def test_inventory_deducts_order_stock_and_rejects_shortfall(
    inventory: Inventory,
):
    # ARRANGE: Select food with a known inventory quantity.
    food = inventory.find_food_by_id(2)
    assert food is not None
    original_stock = food.get_food_stocks()

    # ACT: Deduct an available order, then request more than remains.
    assert inventory.allocate_stock(2, 2) is True
    with pytest.raises(ValueError, match="Not enough stock available"):
        inventory.allocate_stock(2, 2)

    # ASSERT: Successful deduction persists; failed deduction leaves stock intact.
    assert food.get_food_stocks() == original_stock - 2


@pytest.mark.parametrize(
    ("quantity", "error", "message"),
    [
        (0, ValueError, "positive"),
        (-1, ValueError, "positive"),
        (True, TypeError, "number"),
        ("2", TypeError, "number"),
    ],
)
def test_inventory_rejects_invalid_allocation_quantity(
    inventory: Inventory,
    quantity,
    error,
    message,
):
    # ARRANGE: Use a valid food item and an invalid allocation quantity.
    food = inventory.find_food_by_id(2)
    assert food is not None
    original_stock = food.get_food_stocks()

    # ACT / ASSERT: Invalid allocation input raises and preserves stock.
    with pytest.raises(error, match=message):
        inventory.allocate_stock(2, quantity)
    assert food.get_food_stocks() == original_stock
