# gui/shared/toolbar.py
import streamlit as st
from app.auth.account_manager import AccountManager
from app.users.user import UserAccess
from app.gui.style import (
    apply_app_style,
    markdown_home,
    markdown_logout,
    makrdown_options,
)

def require_authenticated() -> None:
    apply_app_style()
    if not st.session_state.get("authenticated", False):
        st.error("Please log in to access this page.")
        st.stop()
    role_names = {
        UserAccess.CLIENT: "Client",
        UserAccess.DONOR: "Donor",
        UserAccess.STAFF: "Food Bank Staff",
        UserAccess.ADMIN: "Admin",
    }
    role_name = role_names.get(st.session_state.get("user_role"))
    account = st.session_state.get("account")
    account_number = account.get("_account_number") if isinstance(account, dict) else None
    if role_name is None or not account_number:
        _invalidate_session()
        st.error("Your session is no longer valid. Please log in again.")
        st.stop()

    account_manager = AccountManager()
    current_account = account_manager.find_account(str(account_number), role_name)
    if current_account is None or not current_account.get("_allow_access", True):
        _invalidate_session()
        st.error("Your account access has changed. Please log in again.")
        st.stop()
    if current_account != account:
        st.session_state.account_manager = account_manager
        st.session_state.account = current_account
        for key in ("current_user", "tracker", "client"):
            st.session_state.pop(key, None)
        st.rerun()
    st.session_state.account_manager = account_manager
    st.session_state.account = current_account


def _invalidate_session() -> None:
    st.session_state.authenticated = False
    for key in (
        "account",
        "current_user",
        "tracker",
        "client",
        "order",
        "original_order",
        "selected_staff_order",
    ):
        st.session_state.pop(key, None)


def require_role(required_role: UserAccess) -> None:
    require_authenticated()
    if st.session_state.get("user_role") != required_role:
        st.error("Access denied. This page is not available for your role.")
        st.stop()


def show_toolbar() -> None:
    role_actions = {
        UserAccess.CLIENT: (
            ("Check Record", "client/client_order_history.py"),
            ("Start Order", "client/client_order.py"),
        ),
        UserAccess.DONOR: (
            ("Register Donation", "donor/register_donation.py"),
            ("Manage Donations", "donor/manage_donations.py"),
        ),
        UserAccess.STAFF: (
            ("Pending Orders", "staff/pending_orders.py"),
            ("Receive Stock", "staff/receive_stock.py"),
        ),
        UserAccess.ADMIN: (
            ("User Management", "admin/user_management.py"),
            ("Stock Monitor", "admin/stock_monitor.py"),
        ),
    }
    home, logout, options = st.columns([1, 1, 5], vertical_alignment="center")
    with home:
        # home
        markdown_home()
        if st.button("Home", key="home_page"):
            st.switch_page("home.py")

    with logout:
        # logout
        markdown_logout()
        if st.button("Logout", key="logout"):
            st.session_state.account = None
            st.session_state.authenticated = False
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
            st.rerun()

    with options:
        makrdown_options()
        with st.container(horizontal=True, horizontal_alignment="right"):
            actions = (
                *role_actions.get(st.session_state.user_role, ()),
                ("Profile", "shared/profile.py"),
                ("Helps", "helps.py"),
            )
            for label, page in actions:
                if st.button(label, key=f"option_{label}"):
                    st.switch_page(page)
    st.divider()