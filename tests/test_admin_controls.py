import json

import pytest

from app.auth.account_manager import AccountManager, verify_password
from app.gui.admin import audit_log
from app.gui.register import check_input
from app.gui.admin.user_management import (
    create_user_account,
    reset_user_password,
    unlock_account,
    update_user_role,
)


def test_registration_requires_at_least_eight_password_characters() -> None:
    valid, feedback = check_input(
        "Staff User",
        "1234567890",
        "1234567",
        "1234567",
    )

    assert not valid
    assert any("at least 8 characters" in message for _, message in feedback)
    assert check_input(
        "Staff User",
        "1234567890",
        "12345678",
        "12345678",
    ) == (True, [])


def make_manager(tmp_path):
    path = tmp_path / "accounts.json"
    path.write_text('{"accounts": {}}', encoding="utf-8")
    return AccountManager(str(path))


def isolate_audit(monkeypatch, tmp_path):
    monkeypatch.setattr(
        audit_log,
        "_audit_file",
        lambda: tmp_path / "admin_audit_log.json",
    )


def test_admin_create_user_validates_and_creates_staff_account(
    tmp_path,
    monkeypatch,
) -> None:
    isolate_audit(monkeypatch, tmp_path)
    manager = make_manager(tmp_path)

    account_id = create_user_account(
        "Food Bank Staff",
        {
            "name": "Staff User",
            "phone_number": "+60-1234567890",
            "password": "a-strong-password",
        },
        manager,
    )

    account = manager.find_account(account_id, "Food Bank Staff")
    assert account is not None
    assert verify_password("a-strong-password", account["_account_password"])
    assert "_address" not in account


def test_admin_create_user_rejects_client_and_short_password(tmp_path) -> None:
    manager = make_manager(tmp_path)

    with pytest.raises(ValueError, match="staff or administrator"):
        create_user_account(
            "Client",
            {
                "name": "Client User",
                "phone_number": "555-1234567890",
                "password": "a-strong-password",
            },
            manager,
        )
    with pytest.raises(ValueError, match="8 characters"):
        create_user_account(
            "Food Bank Staff",
            {
                "name": "Staff",
                "phone_number": "555-1234567890",
                "password": "short",
            },
            manager,
        )


def test_admin_create_user_accepts_eight_character_password(
    tmp_path,
    monkeypatch,
) -> None:
    isolate_audit(monkeypatch, tmp_path)
    manager = make_manager(tmp_path)

    account_id = create_user_account(
        "Food Bank Staff",
        {
            "name": "Staff User",
            "phone_number": "555-1234567890",
            "password": "12345678",
        },
        manager,
    )

    account = manager.find_account(account_id, "Food Bank Staff")
    assert account is not None
    assert verify_password("12345678", account["_account_password"])


def test_admin_unlock_and_reset_password(tmp_path, monkeypatch) -> None:
    isolate_audit(monkeypatch, tmp_path)
    manager = make_manager(tmp_path)
    account_id = manager.create_account(
        "Staff User", "555-1234567890", "old-password", "Food Bank Staff"
    )
    account = manager.find_account(account_id, "Food Bank Staff")
    assert account is not None
    account["_allow_access"] = False
    account["_login_attempts"] = 0
    manager.save_data()

    assert unlock_account(account_id, manager)
    unlocked = manager.find_account(account_id, "Food Bank Staff")
    assert unlocked is not None
    assert unlocked["_allow_access"] is True
    assert unlocked["_login_attempts"] == 5

    temporary_password = reset_user_password(account_id, manager)
    assert len(temporary_password) >= 12
    assert verify_password(temporary_password, unlocked["_account_password"])


def test_account_password_update_rejects_password_shorter_than_eight(
    tmp_path,
) -> None:
    manager = make_manager(tmp_path)
    account_id = manager.create_account(
        "Staff User", "555-1234567890", "old-password", "Food Bank Staff"
    )
    account = manager.find_account(account_id, "Food Bank Staff")
    assert account is not None

    with pytest.raises(ValueError, match="at least 8 characters"):
        manager.change_account_password(account, "short")


def test_admin_role_update_refuses_self_change_and_logs_success(
    tmp_path,
    monkeypatch,
) -> None:
    isolate_audit(monkeypatch, tmp_path)
    manager = make_manager(tmp_path)
    admin_id = manager.create_account(
        "Admin User", "555-1234567890", "secret", "Admin"
    )
    staff_id = manager.create_account(
        "Staff User", "555-1234567891", "secret", "Food Bank Staff"
    )

    with pytest.raises(ValueError, match="own account"):
        update_user_role(
            admin_id,
            "Food Bank Staff",
            manager,
            actor_id=admin_id,
            actor_role="Admin",
        )
    assert update_user_role(
        staff_id,
        "Admin",
        manager,
        actor_id=admin_id,
        actor_role="Admin",
    )
    saved_audit = json.loads(
        (tmp_path / "admin_audit_log.json").read_text(encoding="utf-8")
    )
    assert saved_audit[-1]["action"] == "account_role_changed"
