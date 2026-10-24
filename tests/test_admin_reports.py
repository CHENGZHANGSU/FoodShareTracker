import csv
import io
import json
from datetime import date

import pytest

from app.food.inventory import Inventory
from app.gui.admin.report_export import (
    export_report,
    generate_report,
    import_records,
    merge_inventory_import,
)


def make_inventory(tmp_path):
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps({
            "inventory": [
                {
                    "_id": 1,
                    "_name": "Rice",
                    "_category": "Grains",
                    "_stock": 10,
                    "_unit": "kg",
                    "_tags": ["halal"],
                    "_inDate": "2026-10-01",
                    "_expiryDate": "2027-01-01",
                }
            ],
            "next_food_id": 2,
            "minimum_stock": {"1": 5},
        }),
        encoding="utf-8",
    )
    return Inventory(str(inventory_path)), inventory_path


def test_inventory_import_validates_and_merges_by_food_id(tmp_path) -> None:
    inventory, inventory_path = make_inventory(tmp_path)
    imported = import_records(
        json.dumps({
            "inventory": [
                {
                    "_id": 1,
                    "_name": "Rice",
                    "_category": "Grains",
                    "_stock": 15,
                    "_unit": "kg",
                    "_tags": ["halal", "vegan"],
                    "_expiryDate": "2027-02-01",
                },
                {
                    "_id": 2,
                    "_name": "Beans",
                    "_category": "Pulses",
                    "_stock": 4,
                    "_unit": "kg",
                    "_tags": [],
                },
            ],
            "minimum_stock": {"2": 3},
        }),
    )

    assert merge_inventory_import(imported, inventory) == (1, 1)
    updated_rice = inventory.find_food_by_id(1)
    new_beans = inventory.find_food_by_id(2)
    assert updated_rice is not None and updated_rice.get_food_stocks() == 15
    assert new_beans is not None and new_beans.get_food_name() == "Beans"
    assert inventory.get_minimum_stock(1) == 5
    assert inventory.get_minimum_stock(2) == 3
    assert json.loads(inventory_path.read_text(encoding="utf-8"))["next_food_id"] == 3


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"inventory": [{"_id": 1, "_name": "Rice"}]},
        {
            "inventory": [
                {"_id": 1, "_name": "Rice", "_category": "Grains"},
                {"_id": 1, "_name": "Beans", "_category": "Pulses"},
            ]
        },
        {
            "inventory": [
                {
                    "_id": 1,
                    "_name": "Rice",
                    "_category": "Grains",
                    "_stock": -1,
                }
            ]
        },
    ],
)
def test_inventory_import_rejects_invalid_records(payload) -> None:
    with pytest.raises((TypeError, ValueError)):
        import_records(json.dumps(payload))


def test_merge_rejects_duplicate_names_without_changing_inventory(tmp_path) -> None:
    inventory, inventory_path = make_inventory(tmp_path)
    before = inventory_path.read_text(encoding="utf-8")
    imported = import_records(
        json.dumps({
            "inventory": [
                {
                    "_id": 2,
                    "_name": "rice",
                    "_category": "Grains",
                    "_stock": 3,
                }
            ]
        }),
    )

    with pytest.raises(ValueError, match="conflicts"):
        merge_inventory_import(imported, inventory)
    assert inventory_path.read_text(encoding="utf-8") == before


def test_csv_export_quotes_values_and_includes_thresholds() -> None:
    output = export_report(
        {
            "inventory": [
                {
                    "_id": 1,
                    "_name": "Beans, red",
                    "_category": "Pulses",
                    "_stock": 3,
                    "_tags": ["halal", "vegan"],
                }
            ],
            "minimum_stock": {"1": 2},
        },
        "csv",
    )
    rows = list(csv.DictReader(io.StringIO(output)))

    assert rows[0]["_name"] == "Beans, red"
    assert rows[0]["_tags"] == '["halal", "vegan"]'
    assert rows[0]["minimum_stock"] == "2"


def test_order_report_aggregates_without_client_names(tmp_path) -> None:
    assets = tmp_path / "assets"
    orders = assets / "orders"
    orders.mkdir(parents=True)
    (orders / "2026-10-20_orders.json").write_text(
        json.dumps({
            "Private Client": [
                {
                    "_name": "Rice",
                    "_category": "Grains",
                    "_order_amount": 2,
                    "_unit": "kg",
                }
            ],
            "Another Client": [
                {
                    "_name": "Rice",
                    "_category": "Grains",
                    "_order_amount": 3,
                    "_unit": "kg",
                }
            ],
        }),
        encoding="utf-8",
    )
    (assets / "inventory.json").write_text(
        json.dumps({"inventory": [], "next_food_id": 1, "minimum_stock": {}}),
        encoding="utf-8",
    )
    (assets / "account.json").write_text('{"accounts": {}}', encoding="utf-8")

    report = generate_report(
        "order_demand",
        (date(2026, 10, 20), date(2026, 10, 20)),
        project_root=tmp_path,
    )

    assert report["records"] == [
        {
            "date": "2026-10-20",
            "food_name": "Rice",
            "category": "Grains",
            "quantity": 5,
            "unit": "kg",
        }
    ]
    assert "Private Client" not in json.dumps(report)
