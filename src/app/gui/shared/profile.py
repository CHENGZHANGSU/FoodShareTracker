# gui/shared/profile.py
import streamlit as st
from typing import Any

from app.auth.account_manager import (
    MIN_PASSWORD_LENGTH,
    AccountManager,
    verify_password,
)
from app.users.user import UserAccess
from app.users.profile_validation import MAX_ADDRESS_LENGTH, validate_client_address
from app.users.constraint import *

from app.gui.shared.toolbar import require_authenticated, show_toolbar
from app.gui.style import markdown_button
from util.admin_utils import log_sensitive_access

# Display account information
def display_account(account: dict[str, Any]) -> None:
    account_number = account.get("_account_number") or "Not provided"
    with st.container(border=True):
        st.markdown("#### Account")
        st.caption(f"**Account number:**")
        st.write(account_number)
        st.caption("**Password:**")
        st.write("••••••••")

# Display personal information
def display_personal_info(account: dict[str, Any]) -> None:
    name = account.get("_name")
    contact = account.get("_phone_number")
    is_client = st.session_state.get("user_role") == UserAccess.CLIENT
    with st.container(border=True):
        st.markdown("#### Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Name")
            st.write(name)
        with col2:
            st.caption("Contact")
            st.write(contact)
        if is_client:
            st.caption("Address")
            st.write(account.get("_address", ""))
            st.caption("Food constraints")
            constraints = account.get("_food_constraints", [])
            st.write(", ".join(map(str, constraints)) if constraints else "None")

# Update password for the account
def update_password(
    account_manager: AccountManager,
    account: dict[str, Any],
) -> tuple[int, str] | None:
    with st.form("change_password_form", border=True):
        current_password = st.text_input("Current password", type="password")
        new_password = st.text_input(
            f"New password ({MIN_PASSWORD_LENGTH} characters minimum)",
            type="password",
        )
        confirm_password = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Update password")
    if not submitted:
        return None
    if not current_password or not new_password or not confirm_password:
        return 2, "Complete all fields."
    if len(new_password) < MIN_PASSWORD_LENGTH:
        return 1, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if new_password != confirm_password:
        return 1, "The new passwords do not match."
    if not verify_password(current_password, account.get("_account_password", "")):
        return 1, "Wrong current password."
    if new_password == current_password:
        return 1, "Choose a password different from your current one."
    actor_id = str(account.get("_account_number", "unknown"))
    actor_role = str(st.session_state.get("user_role", "unknown"))
    account_manager.change_account_password(
        account,
        new_password,
        actor_id=actor_id,
        actor_role=actor_role,
    )
    return 0, "Password updated."

# Edit account information
def edit_account_info(
    account_manager: AccountManager,
    account: dict[str, Any],
) -> tuple[int, str] | None:
    with st.container(border=True):
        actor_id = str(account.get("_account_number", "unknown"))
        actor_role = str(st.session_state.get("user_role", "unknown"))
        is_client = st.session_state.get("user_role") == UserAccess.CLIENT
        details = ["Name", "Phone Number"]
        if is_client:
            details.extend(["Address", "Food Constraints"])
        info = st.selectbox("Edit Personal Information", details)
        user_name: str = ""
        country_code: str = ""
        phone_number: str = ""
        user_address: str = ""
        food_constraints = []
        match info:
            case "Name":
                user_name = st.text_input("New Name")
            case "Phone Number":
                country_col, contact_col = st.columns([1, 4])
                country_codes = ["+60", "+1", "+44", "+61", "+65"]
                with country_col:
                    country_code = st.selectbox(
                        "Country code",
                        country_codes,
                        index=country_codes.index("+60"),
                        label_visibility="collapsed")
                with contact_col:
                    phone_number = st.text_input(
                        "Contact number",
                        placeholder="Phone Number",
                        label_visibility="collapsed")
            case "Food Constraints":
                client_constraints = account.get("_food_constraints", []) or []
                original_constraints = st.session_state.setdefault(
                    "profile_original_food_constraints",
                    list(client_constraints),
                )
                available_constraints = [
                    constraint
                    for constraint_group in (*HARD_CONSTRAINTS, SOFT_CONSTRAINTS)
                    for constraint in constraint_group
                    if constraint not in client_constraints
                ]
                constraint_options = [*client_constraints, *available_constraints]
                constraints_key = "profile_food_constraints"
                st.session_state.setdefault(constraints_key, list(client_constraints))
                if st.button("Restore previous constraints", key="restore_food_constraints"):
                    st.session_state[constraints_key] = list(original_constraints)
                food_constraints = st.multiselect(
                    label="Select food constraints",
                    options=constraint_options,
                    format_func=lambda constraint: constraint.replace("_", " ").title(),
                    key=constraints_key,
                )
            case "Address":
                user_address = st.text_input(
                    "New Address",
                    max_chars=MAX_ADDRESS_LENGTH,
                )
        submitted = st.button(f"Update {info}")
        if submitted:
            match info:
                case "Name":
                    if len(user_name.strip()) < 2 or not user_name.replace(" ", "").isalpha():
                        return 1, "Invalid name. Use letters and spaces only."
                    account_manager.update_account_info(
                        account,
                        actor_id=actor_id,
                        actor_role=actor_role,
                        _name=user_name.strip(),
                    )
                    return 0, f"{info} updated."
                case "Phone Number":
                    if not phone_number.strip() or len(phone_number.strip()) < 10:
                        return 1, "Invalid phone number. Enter at least 10 digits."
                    user_contact = country_code + "-" + phone_number.strip()
                    account_manager.update_account_info(
                        account,
                        actor_id=actor_id,
                        actor_role=actor_role,
                        _phone_number=user_contact,
                    )
                    return 0, f"{info} updated."
                case "Food Constraints":
                    account_manager.update_client_info(
                        account,
                        "_food_constraints",
                        [
                            constraint.value
                            if hasattr(constraint, "value")
                            else str(constraint)
                            for constraint in food_constraints
                        ],
                        actor_id=actor_id,
                        actor_role=actor_role,
                    )
                    return 0, f"{info} updated."
                case "Address":
                    try:
                        user_address = validate_client_address(user_address)
                    except ValueError as error:
                        return 1, str(error)
                    account_manager.update_account_info(
                        account,
                        actor_id=actor_id,
                        actor_role=actor_role,
                        _address=user_address.strip(),
                    )
                    return 0, f"{info} updated."

# Show the profile page with account and personal information
def show_profile_page(account_manager: AccountManager) -> None:
    require_authenticated()
    show_toolbar()
    st.subheader("User Profile")
    account = st.session_state.get("account", {})
    if st.session_state.get("user_role") == UserAccess.CLIENT:
        account_id = str(account.get("_account_number", "unknown"))
        log_sensitive_access(
            "view",
            account_id,
            str(st.session_state.get("user_role", "unknown")),
            "client_profile",
            account_id,
        )
    nav_col, content_col = st.columns([1, 4], gap="large")

    section = st.selectbox(
        "Profile section",
        ["Account", "Personal Information"],
        label_visibility="collapsed",
        key="profile_section",
    )

    if "show_password_form" not in st.session_state:
        st.session_state.show_password_form = False
    if "show_edit_form" not in st.session_state:
        st.session_state.show_edit_form = False

    if section == "Account":
        st.session_state.show_edit_form = False
        display_account(account)
        if message := st.session_state.pop("password_success", None):
            st.success(message)
        with st.container(horizontal_alignment="center"):
            markdown_button()
            if st.button("Change password", key="change_password"):
                st.session_state.show_password_form = True
            if st.session_state.show_password_form:
                changed = update_password(account_manager, account)
                if changed:
                    err_code, info = changed
                    match err_code:
                        case 0:
                            st.session_state.password_success = info
                            st.session_state.show_password_form = False
                            st.rerun()
                        case 1:
                            st.error(info)
                        case 2:
                            st.warning(info)

    else:
        st.session_state.show_password_form = False
        display_personal_info(account)
        if message := st.session_state.pop("edit_success", None):
            st.success(message)
        with st.container(horizontal_alignment="center"):
            markdown_button()
            if st.button("Edit", key="edit_profile"):
                st.session_state.show_edit_form = True
                original_constraints = account.get("_food_constraints", []) or []
                st.session_state.profile_original_food_constraints = list(original_constraints)
                st.session_state.profile_food_constraints = list(original_constraints)
            if st.session_state.get("show_edit_form", False):
                changed = edit_account_info(account_manager, account)
                if changed:
                    err_code, info = changed
                    match err_code:
                        case 0:
                            st.session_state.edit_success = info
                            st.session_state.show_edit_form = False
                            st.rerun()
                        case 1:
                            st.error(info)

if __name__ == "__main__":
    show_profile_page(st.session_state.account_manager)