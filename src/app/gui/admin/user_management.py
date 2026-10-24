"""Admin account lookup and access controls."""

import logging
import re
import secrets
from typing import Any

import pandas as pd
import streamlit as st

from app.auth.account_manager import AccountManager, MIN_PASSWORD_LENGTH
from app.gui.admin.audit_log import (
    log_action,
    save_admin_changes,
    show_admin_change_message,
)
from app.gui.shared.toolbar import require_role, show_toolbar
from app.users.user import UserAccess
from util.admin_utils import log_sensitive_access

log: logging.Logger = logging.getLogger(__name__)
ROLES: tuple[str, ...] = ("Client", "Donor", "Food Bank Staff", "Admin")


def _account_manager(account_manager: AccountManager | None = None) -> AccountManager:
    if account_manager is not None:
        return account_manager
    return st.session_state.account_manager


def list_users(
    role: str | None = None,
    account_manager: AccountManager | None = None,
) -> list[dict[str, Any]]:
    visible_fields = {
        "_account_number",
        "_name",
        "_phone_number",
        "_allow_access",
        "_login_attempts",
        "_role",
    }
    return [
        {
            key: value
            for key, value in account.items()
            if key in visible_fields
        }
        for account in _account_manager(account_manager).list_accounts(role)
    ]


def search_staff_by_name(
    name: str,
    account_manager: AccountManager | None = None,
) -> list[dict[str, Any]]:
    query = name.strip().casefold()
    return [
        account
        for account in list_users("Food Bank Staff", account_manager)
        if query in str(account.get("_name", "")).casefold()
    ]


def _set_access(
    user_id: str,
    enabled: bool,
    account_manager: AccountManager | None = None,
    role: str | None = None,
    actor_id: str = "system",
    actor_role: str = "system",
) -> bool:
    changed = _account_manager(account_manager).set_account_access(
        user_id,
        enabled,
        role,
        actor_id=actor_id,
        actor_role=actor_role,
    )
    if changed:
        actor_role = actor_role or "system"
        log_action(
            actor_id,
            "account_access_enabled" if enabled else "account_access_disabled",
            user_id,
            actor_role=actor_role,
            record_type="account",
            record_id=user_id,
        )
        log.info(
            "Admin changed account access: account=%s enabled=%s role=%s",
            user_id,
            enabled,
            role or "any",
        )
    return changed


def restrict_staff_access(
    user_id: str,
    account_manager: AccountManager | None = None,
    *,
    actor_id: str = "system",
    actor_role: str = "system",
) -> bool:
    return _set_access(
        user_id,
        False,
        account_manager,
        "Food Bank Staff",
        actor_id,
        actor_role,
    )


def block_user(
    user_id: str,
    account_manager: AccountManager | None = None,
    *,
    actor_id: str = "system",
    actor_role: str = "system",
) -> bool:
    return _set_access(
        user_id,
        False,
        account_manager,
        actor_id=actor_id,
        actor_role=actor_role,
    )


def deactivate_account(
    user_id: str,
    account_manager: AccountManager | None = None,
    *,
    actor_id: str = "system",
    actor_role: str = "system",
) -> bool:
    return block_user(
        user_id,
        account_manager,
        actor_id=actor_id,
        actor_role=actor_role,
    )


def reactivate_account(
    user_id: str,
    account_manager: AccountManager | None = None,
    *,
    actor_id: str = "system",
    actor_role: str = "system",
) -> bool:
    return _set_access(
        user_id,
        True,
        account_manager,
        actor_id=actor_id,
        actor_role=actor_role,
    )


def unlock_account(
    user_id: str,
    account_manager: AccountManager | None = None,
    *,
    actor_id: str = "system",
    actor_role: str = "system",
) -> bool:
    manager = _account_manager(account_manager)
    account = next(
        (
            entry
            for entry in manager.list_accounts()
            if entry.get("_account_number") == user_id
        ),
        None,
    )
    if account is None or account.get("_login_attempts", 5) > 0:
        return False
    return _set_access(
        user_id,
        True,
        manager,
        str(account["_role"]),
        actor_id,
        actor_role,
    )


def create_user_account(
    role: str,
    data: dict[str, Any],
    account_manager: AccountManager | None = None,
) -> str:
    if role not in {"Food Bank Staff", "Admin"}:
        raise ValueError("Admins can create staff or administrator accounts only.")
    if not isinstance(data, dict):
        raise ValueError("Account details must be provided.")
    name = data.get("name")
    phone_number = data.get("phone_number")
    password = data.get("password")
    if (
        not isinstance(name, str)
        or len(name.strip()) < 2
        or len(name.strip()) > 100
        or any(ord(character) < 32 for character in name)
    ):
        raise ValueError("Enter a valid name between 2 and 100 characters.")
    normalized_phone = phone_number.strip() if isinstance(phone_number, str) else ""
    if (
        not re.fullmatch(r"\+?\d(?:[\d ()-]*\d)?", normalized_phone)
        or not 10 <= sum(character.isdigit() for character in normalized_phone) <= 15
    ):
        raise ValueError("Enter a phone number with 10 to 15 digits.")
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Initial password must be at least {MIN_PASSWORD_LENGTH} characters."
        )
    account_number = _account_manager(account_manager).create_account(
        name.strip(),
        phone_number.strip(),
        password,
        role,
    )
    log_action(
        str(st.session_state.get("account", {}).get("_account_number", "system")),
        "account_created",
        account_number,
        actor_role=str(st.session_state.get("user_role", UserAccess.ADMIN)),
        record_type="account",
        record_id=account_number,
    )
    return account_number


def update_user_role(
    user_id: str,
    new_role: str,
    account_manager: AccountManager | None = None,
    *,
    actor_id: str = "system",
    actor_role: str = "system",
) -> bool:
    manager = _account_manager(account_manager)
    if user_id == actor_id:
        raise ValueError("You cannot change your own account role.")
    changed = manager.update_account_role(
        user_id,
        new_role,
        actor_id=actor_id,
        actor_role=actor_role,
    )
    if changed:
        log_action(
            actor_id,
            "account_role_changed",
            f"{user_id}:{new_role}",
            actor_role=actor_role,
            record_type="account",
            record_id=user_id,
        )
    return changed


def reset_user_password(
    user_id: str,
    account_manager: AccountManager | None = None,
    *,
    actor_id: str = "system",
    actor_role: str = "system",
) -> str:
    manager = _account_manager(account_manager)
    account = next(
        (
            entry
            for role in ROLES
            if (entry := manager.find_account(user_id, role)) is not None
        ),
        None,
    )
    if account is None:
        raise ValueError("Account was not found.")
    temporary_password = secrets.token_urlsafe(18)
    manager.change_account_password(
        account,
        temporary_password,
        actor_id=actor_id,
        actor_role=actor_role,
    )
    log_action(
        actor_id,
        "account_password_reset",
        user_id,
        actor_role=actor_role,
        record_type="account",
        record_id=user_id,
    )
    return temporary_password


def assign_role(
    user_id: str,
    role: str,
    account_manager: AccountManager | None = None,
) -> bool:
    return update_user_role(user_id, role, account_manager)


def update_permissions(user_id: str, permissions: list[str]) -> None:
    raise ValueError(
        "Custom permissions are not supported; access is controlled by account role."
    )


def show_user_management_page() -> None:
    require_role(UserAccess.ADMIN)
    show_toolbar()
    account_manager: AccountManager = st.session_state.account_manager

    st.title("User Management")
    show_admin_change_message()
    st.caption(
        "Create staff accounts, find users, change roles, reset passwords, "
        "and manage login access."
    )

    with st.expander("Create staff or administrator account"):
        with st.form("admin_create_account"):
            new_role = st.selectbox(
                "New account role",
                ("Food Bank Staff", "Admin"),
                key="admin_new_role",
            )
            new_name = st.text_input("Name", key="admin_new_name")
            new_phone = st.text_input("Phone number", key="admin_new_phone")
            new_password = st.text_input(
                f"Initial password ({MIN_PASSWORD_LENGTH} characters minimum)",
                type="password",
                key="admin_new_password",
            )
            create_submitted = st.form_submit_button("Create account")
        if create_submitted:
            try:
                new_account_id = create_user_account(
                    new_role,
                    {
                        "name": new_name,
                        "phone_number": new_phone,
                        "password": new_password,
                    },
                    account_manager,
                )
            except (TypeError, ValueError, OSError) as exc:
                st.error(str(exc))
            else:
                save_admin_changes(f"{new_role} account created: {new_account_id}")

    selected_role = st.selectbox("Role", ("All roles", *ROLES))
    role = None if selected_role == "All roles" else selected_role
    search = st.text_input("Search by name or account number")

    accounts = list_users(role, account_manager)
    query = search.strip().casefold()
    if query:
        accounts = [
            account
            for account in accounts
            if any(
                query in str(account.get(field, "")).casefold()
                for field in ("_name", "_account_number")
            )
        ]

    if not accounts:
        st.info("No matching accounts.")
        return

    admin_account = st.session_state.account
    admin_id = str(admin_account.get("_account_number", "unknown"))
    admin_role = str(st.session_state.get("user_role", UserAccess.ADMIN))
    for client in accounts:
        if client.get("_role") == "Client":
            client_id = str(client.get("_account_number", "unknown"))
            log_sensitive_access(
                "view",
                admin_id,
                admin_role,
                "client_account",
                client_id,
            )

    rows = [
        {
            "Account Number": account.get("_account_number", ""),
            "Name": account.get("_name", ""),
            "Role": account.get("_role", ""),
            "Access": "Enabled" if account.get("_allow_access", True) else "Disabled",
            "Login attempts remaining": account.get("_login_attempts", 5),
        }
        for account in accounts
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    account_numbers = [str(account.get("_account_number", "")) for account in accounts]
    selected_account = st.selectbox("Account to update", account_numbers)
    account = next(
        account
        for account in accounts
        if account.get("_account_number") == selected_account
    )
    if str(account.get("_account_number")) == str(
        st.session_state.account.get("_account_number")
    ):
        st.info("Your own administrator account cannot be changed here.")
        return

    enabled = bool(account.get("_allow_access", True))
    action_label = "Deactivate account" if enabled else "Reactivate account"
    with st.form("admin_account_access"):
        confirm_access_change = st.checkbox(
            f"Confirm: {action_label.lower()} {selected_account}"
        )
        access_submitted = st.form_submit_button(
            action_label,
            disabled=not confirm_access_change,
        )
    if access_submitted:
        if account.get("_role") == "Admin" and enabled:
            active_admins = [
                admin for admin in list_users("Admin", account_manager)
                if admin.get("_allow_access", True)
            ]
            if len(active_admins) <= 1:
                st.error("The last enabled administrator cannot be deactivated.")
                return
        changed = _set_access(
            selected_account,
            not enabled,
            account_manager,
            account.get("_role"),
            admin_id,
            admin_role,
        )
        if changed:
            save_admin_changes(
                f"Login access {'enabled' if not enabled else 'disabled'} "
                f"for {selected_account}."
            )
        st.error("The account could not be updated; refresh and try again.")

    attempts = account.get("_login_attempts", 5)
    if not enabled and attempts == 0:
        with st.form("admin_unlock_account"):
            confirm_unlock = st.checkbox(
                f"Confirm unlocking {selected_account} after failed logins"
            )
            unlock_submitted = st.form_submit_button(
                "Unlock account",
                disabled=not confirm_unlock,
            )
        if unlock_submitted:
            if unlock_account(
                selected_account,
                account_manager,
                actor_id=admin_id,
                actor_role=admin_role,
            ):
                save_admin_changes(f"Account {selected_account} unlocked.")
            st.error("The account could not be unlocked; refresh and try again.")

    available_roles = [
        candidate for candidate in ROLES if candidate != account["_role"]
    ]
    with st.form("admin_change_role"):
        new_role = st.selectbox("New role", available_roles)
        confirm_role_change = st.checkbox(
            f"Confirm changing {selected_account} to {new_role}"
        )
        role_submitted = st.form_submit_button(
            "Change role",
            disabled=not confirm_role_change,
        )
    if role_submitted:
        try:
            changed = update_user_role(
                selected_account,
                new_role,
                account_manager,
                actor_id=admin_id,
                actor_role=admin_role,
            )
        except (TypeError, ValueError, OSError) as exc:
            st.error(str(exc))
        else:
            if changed:
                save_admin_changes(f"Account role changed to {new_role}.")
            st.error("The account role was not changed.")

    with st.form("admin_reset_password"):
        confirm_password_reset = st.checkbox(
            f"Confirm resetting the password for {selected_account}"
        )
        reset_submitted = st.form_submit_button(
            "Reset password",
            disabled=not confirm_password_reset,
        )
    if reset_submitted:
        try:
            temporary_password = reset_user_password(
                selected_account,
                account_manager,
                actor_id=admin_id,
                actor_role=admin_role,
            )
        except (TypeError, ValueError, OSError) as exc:
            st.error(str(exc))
        else:
            st.session_state["admin_temporary_password"] = (
                selected_account,
                temporary_password,
            )
            st.rerun()
    if reset_result := st.session_state.get("admin_temporary_password"):
        if reset_result[0] == selected_account:
            st.warning(
                "Share this temporary password securely; it will not be shown again."
            )
            st.code(reset_result[1])
            if st.button("Dismiss temporary password", key="dismiss_temp_password"):
                del st.session_state["admin_temporary_password"]
                st.rerun()


if __name__ == "__main__":
    show_user_management_page()
