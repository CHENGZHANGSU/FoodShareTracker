import json

import pytest

from app.auth.account_manager import AccountManager


def make_manager(tmp_path):
    path = tmp_path / "accounts.json"
    path.write_text('{"accounts": {}}', encoding="utf-8")
    return AccountManager(str(path))


def test_role_change_restores_role_specific_data_without_exposing_it(tmp_path) -> None:
    manager = make_manager(tmp_path)
    client_id = manager.create_account(
        "Client User",
        "555-1234567890",
        "secret",
        "Client",
        food_constraints=["vegan"],
        address="Client address",
    )

    assert manager.update_account_role(client_id, "Food Bank Staff")
    staff = manager.find_account(client_id, "Food Bank Staff")
    assert staff is not None
    assert "_address" not in staff
    assert "_food_constraints" not in staff
    assert "_address" not in manager.list_accounts("Food Bank Staff")[0]

    assert manager.update_account_role(client_id, "Client")
    client = manager.find_account(client_id, "Client")
    assert client is not None
    assert client["_address"] == "Client address"
    assert client["_food_constraints"] == ["vegan"]


def test_last_enabled_admin_cannot_be_demoted(tmp_path) -> None:
    manager = make_manager(tmp_path)
    admin_id = manager.create_account(
        "Admin User", "555-1234567890", "secret", "Admin"
    )

    with pytest.raises(ValueError, match="last enabled administrator"):
        manager.update_account_role(admin_id, "Food Bank Staff")
    assert manager.find_account(admin_id, "Admin") is not None


def test_account_ids_remain_unique_after_role_changes(tmp_path) -> None:
    manager = make_manager(tmp_path)
    client_id = manager.create_account(
        "Client User", "555-1234567890", "secret", "Client"
    )
    assert manager.update_account_role(client_id, "Donor")

    new_client_id = manager.create_account(
        "Another Client", "555-1234567891", "secret", "Client"
    )
    assert new_client_id != client_id

