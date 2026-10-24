# gui/login.py
import streamlit as st
from math import ceil
from time import time

from app.auth.account_manager import AccountManager
from app.gui.header import show_header
from app.users.user import UserAccess
from app.gui.style import markdown_button

# Set lockout for an account number with a specified duration
def set_lockout(account_number: str, lockout_time: int = 60) -> None:
    lockouts = st.session_state.setdefault("lockouts", {})
    lockouts[account_number] = time() + lockout_time

# Check if an account number is locked out and return the lockout status, remaining time, and whether it just expired
def check_lockout(account_number: str) -> tuple[bool, int, bool]:
    lockouts = st.session_state.setdefault("lockouts", {})
    expires_at = lockouts.get(account_number)

    if expires_at is None:
        return False, 0, False

    remaining = ceil(expires_at - time())
    if remaining > 0:
        return True, remaining, False

    lockouts.pop(account_number, None)
    return False, 0, True

# Display lockout status for an account number and return the lockout status and whether it just expired
def display_lockout_status(account_number: str) -> tuple[bool, bool]:
    locked, remaining, just_expired = check_lockout(account_number)
    if locked:
        st.error(f"Please try again after {remaining} seconds.")
    return locked, just_expired

# Handle the login process for an account number, password, and selected role
@st.fragment(run_every="1s")
def show_lockout_status(
    account_manager: AccountManager,
    account_number: str,
    selected_role: str,
) -> None:
    account_number = account_number.strip()
    if not account_number:
        return
    locked, just_expired = display_lockout_status(account_number)
    if just_expired:
        account = account_manager.find_account(account_number, selected_role)
        if account is not None:
            account_manager.reset_login_permissions(account)

        st.session_state["lockout_expired_account"] = account_number

    if (
        not locked
        and st.session_state.get("lockout_expired_account") == account_number
    ):
        st.success("You can try logging in again.")

def handle_login(
    account_manager: AccountManager,
    account_number: str,
    account_password: str,
    selected_role: str,
) -> None:
    if not account_number or not account_password:
        st.session_state["login_feedback"] = [("warning", "Complete all fields.")]
        return

    account_number = account_number.strip()
    if st.session_state.get("lockout_expired_account") == account_number:
        st.session_state.pop("lockout_expired_account", None)
    locked, _, _ = check_lockout(account_number)
    if locked:
        st.session_state["login_feedback"] = [
            ("error", "Please wait for the lockout period to end before trying again.")
        ]
        return

    access, message, account = account_manager.auth(account_number, account_password, selected_role)
    if access == "success":
        role_map = {
            "Client": UserAccess.CLIENT,
            "Donor": UserAccess.DONOR,
            "Food Bank Staff": UserAccess.STAFF,
            "Admin": UserAccess.ADMIN,
        }
        for key in (
            "current_user",
            "tracker",
            "client",
            "order_quantity",
            "order",
            "original_order",
            "show_substitution",
            "selected_staff_order",
        ):
            st.session_state.pop(key, None)
        st.session_state.account = account
        st.session_state.user_role = role_map[selected_role]
        st.session_state.authenticated = True

    elif access == "failed":
        st.session_state["login_feedback"] = [
            ("error", message),
            ("info", f"{account} attempts remaining."),
        ]

    elif access == "locked":
        set_lockout(account_number)
        st.session_state["login_feedback"] = [("error", message)]

    else:
        st.session_state["login_feedback"] = [("error", message)]


def submit_login(account_manager: AccountManager, selected_role: str) -> None:
    handle_login(
        account_manager,
        st.session_state.get("login_account_number", ""),
        st.session_state.get("login_account_password", ""),
        selected_role,
    )


# Show the login page with input fields for account number and password
def show_login_page(account_manager: AccountManager) -> None:
    show_header("login")
    selected_role = st.session_state.get("selected_role", "Client")
    st.header(f"Login as {selected_role}")

    account_number = st.text_input("Account Number", key="login_account_number")
    st.text_input("Password", type="password", key="login_account_password")

    show_lockout_status(account_manager, account_number, selected_role)
    for level, message in st.session_state.pop("login_feedback", []):
        getattr(st, level)(message)

    with st.container(horizontal=True):
        markdown_button()
        st.button(
            "Login",
            key="login_account",
            on_click=submit_login,
            args=(account_manager, selected_role),
        )

        if st.button("Register account", key="to_register"):
            st.switch_page("register.py")

if __name__ == "__main__":
    show_login_page(st.session_state.account_manager)
