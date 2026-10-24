import json
from datetime import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.core.food_tracker_client import FoodShareTracker
from app.exceptions.NotFoundException import FoodNotFound, OrderNotFound
from app.users.client import Client
from app.users.constraint import Allergy
from app.users.user import UserAccess
from app.gui.client import client_order


@pytest.fixture
def client_account_data():
    return {
        "_account_number": "0001-0001",
        "_account_password": "888888",
        "_name": "Adam",
        "_phone_number": "114514",
        "_food_constraints": [],
        "_food_orders_rec": [],
    }


@pytest.fixture
def fresh_client(client_account_data):
    account = client_account_data
    client = Client(
        account["_account_number"],
        account["_account_password"],
        account["_name"],
        account["_phone_number"],
        account["_food_constraints"],
    )
    if len(account["_food_orders_rec"]) > 0:
        client.set_food_rec(account["_food_orders_rec"])
    return client


@pytest.fixture
def tracker(tmp_path, fresh_client):
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "inventory": [
                    {
                        "_id": 1,
                        "_name": "Apple",
                        "_category": "Fruit",
                        "_stock": 5,
                        "_unit": "piece",
                        "_tags": [],
                        "_inDate": "2026-01-01",
                        "_expiryDate": "2026-12-31",
                    },
                    {
                        "_id": 2,
                        "_name": "Pear",
                        "_category": "Fruit",
                        "_stock": 2,
                        "_unit": "piece",
                        "_tags": [],
                        "_inDate": "2026-01-02",
                    },
                    {
                        "_id": 3,
                        "_name": "Bread",
                        "_category": "Grain",
                        "_stock": 4,
                        "_unit": "loaf",
                        "_tags": [Allergy.GLUTEN],
                        "_inDate": "2026-01-03",
                    },
                    {
                        "_id": 4,
                        "_name": "Rice",
                        "_category": "Grain",
                        "_stock": 6,
                        "_unit": "bag",
                        "_tags": [],
                        "_inDate": "2026-01-04",
                    },
                ],
                "next_food_id": 5,
            }
        ),
        encoding="utf-8",
    )
    return FoodShareTracker(fresh_client, str(inventory_path))


@pytest.mark.parametrize(
    ("account_number", "password", "name", "contact", "constraints"),
    [
        ("0001-0001", "888888", "Adam", "114514", []),
        ("0001-0002", "123456", "Mina", "0400000000", [Allergy.GLUTEN]),
    ],
)
def test_client_create_success(account_number, password, name, contact, constraints):
    # ARRANGE: Prepare account data in the shape supplied by the main page.
    account = {
        "_account_number": account_number,
        "_account_password": password,
        "_name": name,
        "_phone_number": contact,
        "_food_constraints": constraints,
        "_food_orders_rec": [],
    }

    # ACT: Construct a Client from the signed-in account data.
    client = Client(
        account["_account_number"],
        account["_account_password"],
        account["_name"],
        account["_phone_number"],
        account["_food_constraints"],
    )

    # ASSERT: Confirm the client contains the account's profile and role data.
    assert client.get_account_number() == account_number
    assert client.get_account_password() == password
    assert client.get_user_name() == name
    assert client.get_user_contact() == contact
    assert client.get_client_food_constraints() == constraints
    assert client.get_user_access() == UserAccess.CLIENT


def test_client_return_user_returns_same_instance(fresh_client):
    # ARRANGE: Use the fresh client fixture.
    # ACT: Request the user object represented by the client.
    # ASSERT: Confirm the client returns itself.
    assert fresh_client.return_user() is fresh_client


def test_client_constraints_default_to_empty_list():
    # ARRANGE: Create a client without specifying food constraints.
    client = Client("0001-0001", "888888", "Adam", "114514")

    # ACT: Read the client's constraints.
    # ASSERT: Confirm the default is an empty list.
    assert client.get_client_food_constraints() == []


@pytest.mark.parametrize("amount", [float("nan"), float("inf")])
def test_order_rejects_non_finite_quantity(tracker, amount):
    with pytest.raises(ValueError, match="positive number"):
        tracker.add_food_order("Apple", amount)


def test_client_order_page_accepts_date_only_inventory_dates(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "inventory.json").write_text(
        json.dumps(
            {
                "inventory": [
                    {
                        "_id": 1,
                        "_name": "Rice",
                        "_category": "Grains",
                        "_stock": 2,
                        "_unit": "kg",
                        "_tags": [],
                        "_inDate": "2026-10-01",
                    }
                ],
                "next_food_id": 2,
            }
        ),
        encoding="utf-8",
    )
    client = Client("01-0001", "hash", "Test Client", "555-1234567890")
    tracker = FoodShareTracker(client, "assets/inventory.json")

    app = AppTest.from_file(
        str(Path(client_order.__file__)),
        default_timeout=20,
    )
    app.session_state["authenticated"] = True
    app.session_state["user_role"] = UserAccess.CLIENT
    app.session_state["tracker"] = tracker

    app.run()

    assert not app.exception


@pytest.mark.parametrize(
    ("initial", "added", "expected"),
    [
        ([], Allergy.GLUTEN, [Allergy.GLUTEN]),
        ([Allergy.GLUTEN], Allergy.GLUTEN, [Allergy.GLUTEN]),
        ([Allergy.GLUTEN], Allergy.LACTOSE, [Allergy.GLUTEN, Allergy.LACTOSE]),
    ],
)
def test_client_add_food_constraint(initial, added, expected):
    # ARRANGE: Create a client with the parameterized initial constraints.
    client = Client("0001-0001", "888888", "Adam", "114514", initial.copy())

    # ACT: Add the parameterized constraint.
    client.add_food_constraints(added)

    # ASSERT: Confirm the constraints match the expected result.
    assert client.get_client_food_constraints() == expected


@pytest.mark.parametrize(
    ("replacement", "expected"),
    [
        ([Allergy.LACTOSE], [Allergy.LACTOSE]),
        ([], [Allergy.GLUTEN]),
    ],
)
def test_client_set_food_constraints(replacement, expected):
    # ARRANGE: Create a client with an existing constraint.
    client = Client("0001-0001", "888888", "Adam", "114514", [Allergy.GLUTEN])

    # ACT: Replace the constraints with the parameterized list.
    client.set_client_food_constraints(replacement)

    # ASSERT: Confirm the resulting constraints.
    assert client.get_client_food_constraints() == expected


def test_client_add_food_order_record_success(fresh_client):
    # ARRANGE: Use a fresh client and prepare a non-empty order.
    orders = [{"name": "Apple", "amount": 2}]

    # ACT: Add the order record.
    fresh_client.add_food_orders_rec(1, orders)

    # ASSERT: Confirm the record contents and that its timestamp is valid.
    record = fresh_client.get_food_order_rec()[0]
    assert record["id"] == 1
    assert record["orders"] == orders
    datetime.fromisoformat(record["timestamp"])


def test_client_add_empty_food_order_record_fails(fresh_client):
    # ARRANGE: Use a fresh client and an empty order list.
    empty_orders = []

    # ACT: Try to add an empty order record.
    # ASSERT: Confirm the client rejects the empty record.
    with pytest.raises(OrderNotFound):
        fresh_client.add_food_orders_rec(1, empty_orders)


def test_client_loads_order_history_from_account_data(client_account_data):
    # ARRANGE: Prepare order history persisted with the signed-in client account.
    saved_history = [{"id": 3, "timestamp": "2026-10-22T12:00:00", "orders": []}]
    client_account_data["_food_orders_rec"] = saved_history
    client = Client(
        client_account_data["_account_number"],
        client_account_data["_account_password"],
        client_account_data["_name"],
        client_account_data["_phone_number"],
        client_account_data["_food_constraints"],
    )

    # ACT: Load the account's saved order history as the main page does.
    if len(client_account_data["_food_orders_rec"]) > 0:
        client.set_food_rec(client_account_data["_food_orders_rec"])

    # ASSERT: Confirm the client exposes the saved history.
    assert client.get_food_order_rec() == saved_history


@pytest.mark.parametrize(
    ("food_name", "expected_name"),
    [("Apple", "Apple"), ("Pear", "Pear")],
)
def test_tracker_find_food_by_name_success(tracker, food_name, expected_name):
    # ARRANGE: Use the tracker fixture and a name present in its inventory.
    # ACT: Find the food by name.
    food = tracker.find_food_by_name(food_name)

    # ASSERT: Confirm the matching food is returned.
    assert food.get_food_name() == expected_name


def test_tracker_find_food_by_name_failure(tracker):
    # ARRANGE: Use a name that is not in the tracker's inventory.
    # ACT: Try to find the missing food.
    # ASSERT: Confirm the tracker raises FoodNotFound with the expected message.
    with pytest.raises(FoodNotFound, match="Food Missing not found"):
        tracker.find_food_by_name("Missing")


def test_tracker_find_food_by_category_success(tracker):
    # ARRANGE: Use the tracker fixture and an inventory category with matches.
    # ACT: Find foods in the Fruit category.
    foods = tracker.find_food_by_category("Fruit")

    # ASSERT: Confirm all matching foods are returned in inventory order.
    assert [food.get_food_name() for food in foods] == ["Apple", "Pear"]


def test_tracker_find_food_by_category_failure(tracker):
    # ARRANGE: Use a category that is not present in the inventory.
    # ACT: Try to find foods in the missing category.
    # ASSERT: Confirm the tracker raises FoodNotFound with the expected message.
    with pytest.raises(FoodNotFound, match="Food Vegetable not found"):
        tracker.find_food_by_category("Vegetable")


@pytest.mark.parametrize(
    ("food_name", "amount", "expected"),
    [("Apple", 1, True), ("Apple", 5, True), ("Apple", 6, False)],
)
def test_tracker_add_food_order(tracker, monkeypatch, food_name, amount, expected):
    # ARRANGE: Suppress the UI warning and use parameterized food and quantity.
    monkeypatch.setattr("app.core.food_tracker_client.st.warning", lambda *_: None)

    # ACT: Add the requested food and quantity to the order.
    # ASSERT: Confirm the result and whether an order was created.
    assert tracker.add_food_order(food_name, amount) is expected
    assert len(tracker.list_orders()) == (1 if expected else 0)


def test_tracker_add_food_order_unknown_food_fails(tracker):
    # ARRANGE: Use a food name absent from the inventory.
    # ACT: Try to add the unknown food.
    # ASSERT: Confirm the tracker raises FoodNotFound.
    with pytest.raises(FoodNotFound):
        tracker.add_food_order("Missing")


def test_tracker_add_existing_food_order_increases_quantity(tracker):
    # ARRANGE: Add one unit of Apple to create an existing order.
    tracker.add_food_order("Apple", 1)

    # ACT: Add two more units of the same food.
    result = tracker.add_food_order("Apple", 2)

    # ASSERT: Confirm the operation succeeds and combines the quantities.
    assert result is True
    assert tracker.list_orders_in_dict()[0]["_order_amount"] == 3


@pytest.mark.parametrize(
    ("quantity", "expected"),
    [(3, True), (6, False)],
)
def test_tracker_update_food_order_quantity(
    tracker, monkeypatch, quantity, expected
):
    # ARRANGE: Add an initial order and suppress any UI information message.
    tracker.add_food_order("Apple", 1)
    monkeypatch.setattr("app.core.food_tracker_client.st.info", lambda *_: None)

    # ACT: Update the order to the parameterized quantity.
    result = tracker.update_food_order("Apple", quantity)

    # ASSERT: Confirm whether the update succeeds and, if so, the new quantity.
    assert result is expected
    if expected:
        assert tracker.list_orders_in_dict()[0]["_order_amount"] == quantity


def test_tracker_update_missing_food_order_fails(tracker):
    # ARRANGE: Leave the current order empty.
    # ACT: Try to update an order that does not exist.
    # ASSERT: Confirm the tracker raises OrderNotFound.
    with pytest.raises(OrderNotFound):
        tracker.update_food_order("Apple", 1)


def test_tracker_remove_food_order_success(tracker, monkeypatch):
    # ARRANGE: Add Apple to the order and suppress the UI information message.
    tracker.add_food_order("Apple", 1)
    monkeypatch.setattr("app.core.food_tracker_client.st.info", lambda *_: None)

    # ACT: Remove Apple from the order.
    tracker.remove_food_from_order("Apple")

    # ASSERT: Confirm the current order is empty.
    assert tracker.list_orders() == []


def test_tracker_remove_missing_food_order_fails(tracker):
    # ARRANGE: Leave the current order empty.
    # ACT: Try to remove an order that does not exist.
    # ASSERT: Confirm the tracker raises OrderNotFound with the expected message.
    with pytest.raises(OrderNotFound, match="Ordered food Apple not found"):
        tracker.remove_food_from_order("Apple")


def test_tracker_start_new_order_clears_current_orders(tracker):
    # ARRANGE: Add Apple to the current order.
    tracker.add_food_order("Apple", 1)

    # ACT: Start a new order.
    tracker.start_new_order()

    # ASSERT: Confirm both current and original order lists are cleared.
    assert tracker.list_orders() == []
    assert tracker.list_orders_in_dict() == []


def test_tracker_finish_order_success(tracker):
    # ARRANGE: Add Apple to the order with a known quantity.
    tracker.add_food_order("Apple", 2)

    # ACT: Finish the order.
    current_orders, original_orders = tracker.finish_food_order()

    # ASSERT: Confirm the finished and original orders contain the expected food.
    assert current_orders[0].get_food_name() == "Apple"
    assert original_orders[0].get_order_amount() == 2


def test_tracker_finish_empty_order_fails(tracker):
    # ARRANGE: Leave the current order empty.
    # ACT: Try to finish the empty order.
    # ASSERT: Confirm the tracker raises OrderNotFound.
    with pytest.raises(OrderNotFound):
        tracker.finish_food_order()


def test_tracker_reject_changes_restores_original_order(
    tracker, fresh_client, monkeypatch
):
    # ARRANGE: Set a hard constraint, suppress UI messages, and add violating food.
    fresh_client.add_food_constraints(Allergy.GLUTEN)
    monkeypatch.setattr("app.core.food_tracker_client.st.info", lambda *_: None)
    tracker.add_food_order("Bread", 2)
    tracker.finish_food_order()

    # ACT: Reject the proposed substitution.
    tracker.reject_changes()

    # ASSERT: Confirm the original food and quantity have been restored.
    assert tracker.list_orders_in_dict()[0]["_name"] == "Bread"
    assert tracker.list_orders_in_dict()[0]["_order_amount"] == 2


def test_tracker_substitutes_food_violating_hard_constraint(
    tracker, fresh_client, monkeypatch
):
    # ARRANGE: Set a hard constraint, add violating food, and suppress UI messages.
    fresh_client.add_food_constraints(Allergy.GLUTEN)
    tracker.add_food_order("Bread", 1)
    monkeypatch.setattr("app.core.food_tracker_client.st.info", lambda *_: None)

    # ACT: Finish the order to trigger constraint substitution.
    current_orders, original_orders = tracker.finish_food_order()

    # ASSERT: Confirm Rice replaces Bread while the original order is preserved.
    assert [order.get_food_name() for order in current_orders] == ["Rice"]
    assert [order.get_food_name() for order in original_orders] == ["Bread"]


def test_tracker_accept_orders_records_history(tracker, tmp_path, monkeypatch):
    # ARRANGE: Prepare an isolated output directory and a valid Apple order.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "assets" / "orders").mkdir(parents=True)
    tracker.add_food_order("Apple", 1)
    accepted_orders, _ = tracker.finish_food_order()

    # ACT: Accept the order so the tracker records and saves it.
    tracker.accept_orders(accepted_orders)

    # ASSERT: Confirm order history and the saved order file.
    history = tracker.check_order_history()
    assert len(history) == 1
    assert history[0]["id"] == 1
    assert history[0]["orders"][0]["_name"] == "Apple"
    assert history[0]["orders"][0]["_expiryDate"] == "2026-12-31"
    history_order = history[0]["orders"][0]
    assert history_order["_order_status"] == "Pending"
    assert history_order["_order_key"].endswith("|Adam|1")
    order_file = next((tmp_path / "assets" / "orders").glob("*_orders.json"))
    saved_order = json.loads(order_file.read_text(encoding="utf-8"))
    assert saved_order["Adam"][0]["_order_status"] == "Pending"
    assert saved_order["Adam"][0]["_order_key"] == history_order["_order_key"]
    assert saved_order["Adam"][0]["_expiryDate"] == "2026-12-31"


def test_tracker_accept_empty_orders_fails(tracker, tmp_path, monkeypatch):
    # ARRANGE: Prepare an isolated output directory and an empty order list.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "assets" / "orders").mkdir(parents=True)

    # ACT: Try to accept an empty order.
    # ASSERT: Confirm the tracker raises OrderNotFound and records no history.
    with pytest.raises(OrderNotFound):
        tracker.accept_orders([])

    assert tracker.check_order_history() == []
