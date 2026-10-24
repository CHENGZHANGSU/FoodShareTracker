import json

import pytest

from app.auth.account_manager import AccountManager, hash_password, verify_password


def make_account_manager(tmp_path, data: dict | None = None) -> AccountManager:
    accounts_path = tmp_path / "accounts.json"
    accounts_path.write_text(
        json.dumps(data or {"accounts": {}}),
        encoding="utf-8",
    )
    return AccountManager(str(accounts_path))


def test_password_hashes_are_salted_and_verifiable() -> None:
    first_hash = hash_password("correct horse battery staple")
    second_hash = hash_password("correct horse battery staple")

    assert first_hash != second_hash
    assert verify_password("correct horse battery staple", first_hash)
    assert not verify_password("wrong password", first_hash)


def test_new_accounts_authenticate_using_hashed_passwords(tmp_path) -> None:
    manager = make_account_manager(tmp_path)
    account_number = manager.create_account(
        "Client User", "555-1234567890", "secret", "Client"
    )
    account = manager.find_account(account_number, "Client")

    assert account is not None
    assert account["_account_password"] != "secret"
    assert verify_password("secret", account["_account_password"])
    assert manager.auth(account_number, "secret", "Client")[0] == "success"
    assert manager.auth(account_number, "incorrect", "Client")[0] == "failed"


def test_legacy_passwords_are_migrated_and_can_still_authenticate(tmp_path) -> None:
    account = {
        "_account_number": "01-0001",
        "_account_password": "legacy-secret",
        "_name": "Legacy User",
        "_allow_access": True,
        "_login_attempts": 5,
    }
    manager = make_account_manager(tmp_path, {"accounts": {"Client": [account]}})

    migrated_password = manager.find_account("01-0001", "Client")["_account_password"]
    assert migrated_password != "legacy-secret"
    assert verify_password("legacy-secret", migrated_password)
    assert manager.auth("01-0001", "legacy-secret", "Client")[0] == "success"


def test_password_changes_and_account_updates_hash_passwords(tmp_path) -> None:
    manager = make_account_manager(tmp_path)
    account_number = manager.create_account(
        "Client User", "555-1234567890", "old-secret", "Client"
    )
    account = manager.find_account(account_number, "Client")
    assert account is not None

    manager.change_account_password(account, "new-secret")
    assert verify_password("new-secret", account["_account_password"])
    assert manager.auth(account_number, "new-secret", "Client")[0] == "success"

    manager.update_account_info(account, _account_password="updated-secret")
    assert verify_password("updated-secret", account["_account_password"])


def test_missing_account_file_starts_empty_and_saves_to_new_parent(
    tmp_path,
) -> None:
    accounts_path = tmp_path / "new" / "accounts.json"
    manager = AccountManager(str(accounts_path))

    assert manager.get_account_counts() == {}
    manager.create_account("New Client", "555-1234567890", "secret", "Client")
    assert accounts_path.is_file()


def test_corrupt_account_json_raises_clear_error(tmp_path) -> None:
    accounts_path = tmp_path / "accounts.json"
    accounts_path.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSON"):
        AccountManager(str(accounts_path))


def test_invalid_account_role_records_are_rejected(tmp_path) -> None:
    accounts_path = tmp_path / "accounts.json"
    accounts_path.write_text(
        json.dumps({"accounts": {"Client": [None]}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be objects"):
        AccountManager(str(accounts_path))
