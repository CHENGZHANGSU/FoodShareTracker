"""Administrator overview with live account and inventory summaries."""

from typing import Any

import streamlit as st

from app.auth.account_manager import AccountManager
from app.food.inventory import Inventory
from app.gui.admin.audit_log import show_admin_change_message
from app.gui.admin.stock_monitor import (
    get_expiry_alerts,
    get_inventory_manager,
    get_low_stock_alerts,
)
from app.gui.shared.toolbar import show_toolbar, require_role
from app.gui.style import show_dashboard_header
from app.users.user import UserAccess


def get_activity_summary(
    account_manager: AccountManager | None = None,
) -> dict[str, int]:
    manager = account_manager or st.session_state.account_manager
    accounts: list[dict[str, Any]] = manager.list_accounts()
    return {
        "Total accounts": len(accounts),
        "Enabled accounts": sum(
            bool(account.get("_allow_access", True)) for account in accounts
        ),
        "Disabled accounts": sum(
            not bool(account.get("_allow_access", True)) for account in accounts
        ),
    }


def get_account_counts(
    account_manager: AccountManager | None = None,
) -> dict[str, int]:
    manager = account_manager or st.session_state.account_manager
    return manager.get_account_counts()


def get_stock_alerts(inventory: Inventory | None = None) -> list[str]:
    manager = inventory or get_inventory_manager()
    low_stock_alerts = [
        f"{food.get_food_name()} is below its minimum "
        f"({food.get_food_stocks()} {food.get_food_unit()} remaining)"
        for food in get_low_stock_alerts(manager)
    ]
    expiry_alerts = [
        f"{food.get_food_name()} is expired "
        f"(expiry date: {food.get_food_expiry_date()})"
        for food in get_expiry_alerts(manager)
    ]
    return [*low_stock_alerts, *expiry_alerts]


def get_shortage_categories(inventory: Inventory | None = None) -> list[str]:
    manager = inventory or get_inventory_manager()
    return sorted(
        {
            food.get_food_category()
            for food in get_low_stock_alerts(manager)
        }
    )


def get_dashboard_summary(
    inventory: Inventory | None = None,
) -> dict[str, int | float]:
    manager = inventory or get_inventory_manager()
    foods = manager.get_inventory()
    return {
        "food_items": len(foods),
        "total_stock": sum(food.get_food_stocks() for food in foods),
        "low_stock": len(get_low_stock_alerts(manager)),
        "expired": len(get_expiry_alerts(manager)),
    }


def show_activity_summary() -> None:
    summary = get_activity_summary()
    st.subheader("Account Access")
    columns = st.columns(len(summary))
    for column, (label, value) in zip(columns, summary.items()):
        column.metric(label, value)

    st.subheader("Accounts by Role")
    counts = get_account_counts()
    roles = (
        ("Client", "Clients"),
        ("Donor", "Donors"),
        ("Food Bank Staff", "Food Bank Staff"),
        ("Admin", "Administrators"),
    )
    role_columns = st.columns(len(roles))
    for column, (role, label) in zip(role_columns, roles):
        column.metric(label, counts.get(role, 0))


def show_stock_alerts() -> None:
    alerts = get_stock_alerts()
    st.subheader("Stock Alerts")
    if alerts:
        for alert in alerts:
            if "expired" in alert:
                st.error(alert)
            else:
                st.warning(alert)
    else:
        st.success("No low-stock or expired-food alerts.")


def show_shortage_categories() -> None:
    categories = get_shortage_categories()
    st.subheader("Categories needing attention")
    if categories:
        for category in categories:
            st.info(category)
    else:
        st.write("No categories are currently below their stock thresholds.")


def refresh_dashboard() -> None:
    st.rerun()


def show_admin_dashboard() -> None:
    require_role(UserAccess.ADMIN)
    show_toolbar()
    show_admin_change_message()
    show_dashboard_header("FoodShare Administrator Dashboard", "Administrator")

    show_activity_summary()
    inventory_summary = get_dashboard_summary()
    st.subheader("Inventory Summary")
    summary_columns = st.columns(4)
    summary_columns[0].metric("Food items", inventory_summary["food_items"])
    summary_columns[1].metric("Total stock", f"{inventory_summary['total_stock']:g}")
    summary_columns[2].metric("Low stock", inventory_summary["low_stock"])
    summary_columns[3].metric("Expired", inventory_summary["expired"])

    st.divider()
    left, right = st.columns(2)
    with left:
        show_stock_alerts()
    with right:
        show_shortage_categories()

    st.divider()
    user_col, stock_col, audit_col, reports_col = st.columns(4)
    with user_col:
        if st.button("Manage user access", width="stretch"):
            st.switch_page("admin/user_management.py")
    with stock_col:
        if st.button("Manage stock", width="stretch"):
            st.switch_page("admin/stock_monitor.py")
    with audit_col:
        if st.button("Audit log", width="stretch"):
            st.switch_page("admin/audit_log.py")
    with reports_col:
        if st.button("Reports & data", width="stretch"):
            st.switch_page("admin/report_export.py")


if __name__ == "__main__":
    show_admin_dashboard()
