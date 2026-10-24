import json
from datetime import date

import pytest

from app.auth.account_manager import AccountManager
from app.food.food_item import FoodItem
from app.food.inventory import Inventory
from app.gui.admin.stock_monitor import (
    adjust_stock,
    check_low_stock,
    set_threshold,
)
from app.gui.admin import audit_log
from app.gui.admin.user_management import (
    block_user,
    list_users,
    reactivate_account,
    restrict_staff_access,
    search_staff_by_name,
)


def make_account_manager(tmp_path) -> AccountManager:
    accounts_path = tmp_path / "accounts.json"
    accounts_path.write_text(json.dumps({"accounts": {}}), encoding="utf-8")
    return AccountManager(str(accounts_path))


def isolate_audit_log(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        audit_log,
        "_audit_file",
        lambda: tmp_path / "admin_audit_log.json",
    )


def test_account_access_can_be_disabled_and_reenabled(tmp_path, monkeypatch) -> None:
    isolate_audit_log(monkeypatch, tmp_path)
    manager = make_account_manager(tmp_path)
    account_number = manager.create_account(
        "Staff Member", "555-1234567890", "password", "Food Bank Staff"
    )

    assert restrict_staff_access(account_number, manager)
    disabled_account = manager.find_account(account_number, "Food Bank Staff")
    assert disabled_account is not None
    assert disabled_account["_allow_access"] is False

    disabled_account["_login_attempts"] = 0
    manager.save_data()
    assert reactivate_account(account_number, manager)
    reenabled_account = manager.find_account(account_number, "Food Bank Staff")
    assert reenabled_account is not None
    assert reenabled_account["_allow_access"] is True
    assert reenabled_account["_login_attempts"] == 5


def test_user_search_and_listing_omit_passwords(tmp_path, monkeypatch) -> None:
    isolate_audit_log(monkeypatch, tmp_path)
    manager = make_account_manager(tmp_path)
    account_number = manager.create_account(
        "Morgan Staff", "555-1234567890", "secret", "Food Bank Staff"
    )

    assert [
        user["_account_number"]
        for user in search_staff_by_name("morgan", manager)
    ] == [account_number]
    users = list_users("Food Bank Staff", manager)
    assert users[0]["_role"] == "Food Bank Staff"
    assert "_account_password" not in users[0]
    assert block_user(account_number, manager)


def test_stock_threshold_and_adjustment_use_inventory_totals(tmp_path) -> None:
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "inventory": [],
                "next_food_id": 1,
                "minimum_stock": {},
            }
        ),
        encoding="utf-8",
    )
    inventory = Inventory(str(inventory_path))
    food = FoodItem(1, "Rice", "Grains", 0, "kg", [])
    assert inventory.add_food_to_inventory(food)

    inventory.record_incoming_stock(1, 5)
    set_threshold(1, 6, inventory)
    assert check_low_stock("Rice", 6, inventory)

    assert adjust_stock(1, -2, "Stock correction", inventory)
    assert food.get_food_stocks() == 3
    assert "stock_records" not in json.loads(
        inventory_path.read_text(encoding="utf-8")
    )


def test_stock_adjustment_increase_requires_no_batch_details(tmp_path) -> None:
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "inventory": [{"_id": 1, "_name": "Rice", "_category": "Grains", "_stock": 2}],
                "next_food_id": 2,
            }
        ),
        encoding="utf-8",
    )
    inventory = Inventory(str(inventory_path))

    assert adjust_stock(1, 1, "Stock correction", inventory)
    food = inventory.find_food_by_id(1)
    assert food is not None
    assert food.get_food_stocks() == 3


def test_handover_allocates_from_inventory_total_without_batch_records(tmp_path) -> None:
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "inventory": [
                    {
                        "_id": 1,
                        "_name": "Rice",
                        "_category": "Grains",
                        "_stock": 5,
                        "_unit": "kg",
                    }
                ],
                "next_food_id": 2,
            }
        ),
        encoding="utf-8",
    )
    inventory = Inventory(str(inventory_path))

    food = inventory.find_food_by_id(1)
    assert food is not None
    assert food.get_food_stocks() == 5
    assert inventory.allocate_stock(1, 2)
    assert food.get_food_stocks() == 3
    assert inventory.allocate_stock(1, 3)
    assert food.get_food_stocks() == 0


def test_handover_rejects_quantity_above_inventory_total(tmp_path) -> None:
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "inventory": [
                    {
                        "_id": 1,
                        "_name": "Rice",
                        "_category": "Grains",
                        "_stock": 2,
                        "_unit": "kg",
                    }
                ],
                "next_food_id": 2,
            }
        ),
        encoding="utf-8",
    )
    inventory = Inventory(str(inventory_path))

    with pytest.raises(ValueError, match="Not enough stock available"):
        inventory.allocate_stock(1, 3)

    food = inventory.find_food_by_id(1)
    assert food is not None
    assert food.get_food_stocks() == 2


def test_expiry_date_is_persisted_and_expired_food_is_reported(tmp_path) -> None:
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "inventory": [
                    {
                        "_id": 1,
                        "_name": "Expired Rice",
                        "_category": "Grains",
                        "_stock": 2,
                        "_expiryDate": "2026-10-22",
                    },
                    {
                        "_id": 2,
                        "_name": "Fresh Rice",
                        "_category": "Grains",
                        "_stock": 3,
                        "_expiryDate": "2026-10-24",
                    },
                ],
                "next_food_id": 3,
            }
        ),
        encoding="utf-8",
    )
    inventory = Inventory(str(inventory_path))

    assert [
        food.get_food_name()
        for food in inventory.get_expired_foods(today=date(2026, 10, 23))
    ] == ["Expired Rice"]

    food = inventory.find_food_by_id(2)
    assert food is not None
    inventory.update_food_from_inventory(2, expiry_date="2026-10-20")
    assert food.get_food_expiry_date() == "2026-10-20"
    saved_data = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert saved_data["inventory"][1]["_expiryDate"] == "2026-10-20"

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        inventory.update_food_from_inventory(2, expiry_date="not-a-date")
