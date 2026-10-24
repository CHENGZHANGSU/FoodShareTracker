import json

import pytest

from app.gui.staff import order_status


def test_staff_status_update_is_saved_to_shared_order_and_status_file(
    tmp_path,
    monkeypatch,
) -> None:
    orders_file = tmp_path / "2026-10-23_orders.json"
    orders_file.write_text(
        json.dumps(
            {
                "Leo": [
                    {
                        "_id": 1,
                        "_name": "Beef",
                        "_order_amount": 2,
                        "_order_status": "Pending",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    status_file = tmp_path / "order_status.json"
    monkeypatch.setattr(order_status, "get_status_file", lambda: status_file)

    order_key = "2026-10-23_orders.json|Leo|1"
    order_status.save_order_status(order_key, "Preparing")

    saved_order = json.loads(orders_file.read_text(encoding="utf-8"))
    assert saved_order["Leo"][0]["_order_key"] == order_key
    assert saved_order["Leo"][0]["_order_status"] == "Preparing"
    assert order_status.load_order_statuses()[order_key] == "Preparing"


def test_legacy_boolean_status_normalizes_to_text() -> None:
    assert order_status.normalize_order_status(False) == "Pending"
    assert order_status.normalize_order_status(True) == "Completed"


def test_corrupt_order_status_file_is_not_treated_as_empty(
    tmp_path,
    monkeypatch,
) -> None:
    status_file = tmp_path / "order_status.json"
    status_file.write_text("{", encoding="utf-8")
    monkeypatch.setattr(order_status, "get_status_file", lambda: status_file)

    with pytest.raises(ValueError, match="invalid JSON"):
        order_status.load_order_statuses()


@pytest.mark.parametrize("order_key", ["", "missing-fields", None])
def test_malformed_order_keys_raise_clear_error(order_key) -> None:
    with pytest.raises(ValueError, match="Invalid order record key"):
        order_status.save_order_status(order_key, "Preparing")
