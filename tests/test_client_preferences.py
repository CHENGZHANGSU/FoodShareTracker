import json

from app.auth.account_manager import AccountManager
from app.gui.staff.client_preferences import search_clients


def test_search_clients_matches_name_account_id_and_phone(tmp_path) -> None:
    # ARRANGE: Create client and staff accounts with searchable identifiers.
    accounts_path = tmp_path / "accounts.json"
    accounts_path.write_text(
        json.dumps({"accounts": {}}),
        encoding="utf-8",
    )
    account_manager = AccountManager(str(accounts_path))
    account_manager.create_account(
        "Alex Client",
        "555-0101",
        "password",
        "Client",
        food_constraints=["vegan", "nut"],
    )
    account_manager.create_account(
        "Morgan Client",
        "555-0202",
        "password",
        "Client",
        food_constraints=["halal"],
    )
    account_manager.create_account(
        "Alex Staff",
        "555-0101",
        "password",
        "Food Bank Staff",
    )

    # ACT: Search the client list by name, account ID, phone, and blank input.
    name_results = search_clients("alex", account_manager)
    account_results = search_clients("01-0002", account_manager)
    phone_results = search_clients("555-0202", account_manager)
    blank_results = search_clients("   ", account_manager)

    # ASSERT: Results match clients only and blank searches return no results.
    assert [client["_name"] for client in name_results] == ["Alex Client"]
    assert [client["_account_number"] for client in account_results] == ["01-0002"]
    assert [client["_name"] for client in phone_results] == ["Morgan Client"]
    assert blank_results == []


def test_client_search_results_do_not_include_passwords(tmp_path) -> None:
    # ARRANGE: Create a client account with private credentials and preferences.
    accounts_path = tmp_path / "accounts.json"
    accounts_path.write_text(
        json.dumps({"accounts": {}}),
        encoding="utf-8",
    )
    account_manager = AccountManager(str(accounts_path))
    account_manager.create_account(
        "Alex Client",
        "555-0101",
        "password",
        "Client",
        food_constraints=["vegan"],
    )

    # ACT: Retrieve the client through the preference search.
    client = search_clients("Alex", account_manager)[0]

    # ASSERT: The result includes preferences but never exposes the password.
    assert "_account_password" not in client
    assert client["_food_constraints"] == ["vegan"]
