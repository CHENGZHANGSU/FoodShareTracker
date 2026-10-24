import pandas as pd
import streamlit as st

from app.gui.shared.toolbar import require_role
from app.gui.staff.pending_orders import load_orders
from app.users.user import UserAccess
from util.admin_utils import (
    log_sensitive_access,
    opaque_audit_id,
)
from app.core.notification import load_notifications, mark_as_read


def show_ready_for_collection() -> None:
    require_role(UserAccess.CLIENT)

    st.header("Ready for Collection")
    st.info("Please collect these orders from your food bank.")

    current_user = st.session_state.current_user
    client_name = current_user.get_user_name()
    account_id = str(
        st.session_state.account.get("_account_number", "unknown")
    )
    log_sensitive_access(
        "view",
        account_id,
        str(st.session_state.get("user_role", "unknown")),
        "client_ready_orders",
        account_id,
    )
    orders, errors = load_orders(client_name_filter=client_name)
    for order in orders:
        log_sensitive_access(
            "view",
            account_id,
            str(st.session_state.get("user_role", "unknown")),
            "client_order",
            opaque_audit_id(str(order["order_key"])),
        )
    ready_orders = [
        order
        for order in orders
        if order["client"] == client_name
        and order["status"] == "Ready for Collection"
    ]

    if ready_orders:
        display_rows = [
            {
                "Food Item": order["food_name"],
                "Category": order["category"],
                "Quantity": order["quantity"],
                "Unit": order["unit"],
                "Order Date": order["date"],
            }
            for order in ready_orders
        ]
        st.dataframe(
            pd.DataFrame(display_rows),
            width='stretch',
            hide_index=True,
        )
    else:
        st.info("You do not have any orders ready for collection.")

    
    if errors:
        with st.expander("Order loading warnings"):
            for error in errors:
                st.warning(error)

    st.subheader("Notifications")

    notifications = load_notifications()

    my_notifications = [
        notification
        for notification in notifications
        if notification.get("client") == client_name
    ]

    if not my_notifications:
        st.info("No notifications yet.")

    for notification in reversed(my_notifications):
        message = notification.get("message", "")
        order_key = notification.get("order_key", "")

        if notification.get("read", False):
            st.write("Read: " + message)
        else:
            st.info("New: " + message)

            if st.button("Mark as Read", key=f"client_read_{order_key}"):
                mark_as_read(order_key, client_name)
                st.rerun()



if __name__ == "__main__":
    show_ready_for_collection()
