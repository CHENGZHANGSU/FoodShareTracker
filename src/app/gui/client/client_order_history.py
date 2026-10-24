"""
This .py file contain the view for client's order history. 
"""
import json
from pathlib import Path

import streamlit as st
import pandas as pd
from typing import Any

from app.gui.shared.toolbar import require_role
from app.gui.staff.order_status import (
    load_order_statuses,
    normalize_order_status,
)
from app.users.user import UserAccess
from util.admin_utils import log_sensitive_access, opaque_audit_id

def show_client_order_history() -> None:
    require_role(UserAccess.CLIENT)
    account_id = str(
        st.session_state.account.get("_account_number", "unknown")
    )
    log_sensitive_access(
        "view",
        account_id,
        str(st.session_state.get("user_role", "unknown")),
        "client_order_history",
        account_id,
    )
    st.header("Order History")
    show_history_table()
    

def show_history_table() -> None:
    """
    This method used to retrieve the client order history and display.
    """
    history_records = st.session_state.account.get("_food_orders_rec", [])
    account_id = str(
        st.session_state.account.get("_account_number", "unknown")
    )
    if history_records:
        for history in history_records:
            log_sensitive_access(
                "view",
                account_id,
                str(st.session_state.get("user_role", "unknown")),
                "client_order_history_record",
                opaque_audit_id(
                    f"{account_id}|history|{history.get('id', 'unknown')}"
                ),
            )
            with st.container(border=True):
                details, action = st.columns([4, 1.2], vertical_alignment="center")
                with details:
                    display = history.copy()
                    display['orders'] = [len(history['orders'])]
                    time = history['timestamp'].split("T")
                    display['timestamp'] = [time[0]]
                    frame = pd.DataFrame(display)
                    frame.columns = ["Order ID", "Time", "Orders"]
                    st.dataframe(frame, width="stretch", hide_index=True)
                with action:
                    if st. button("View Order",
                                key=f"view_client_order{history['id']}_history",
                                disabled=len(history['orders']) <= 0,
                                width="stretch"):
                        client_name = st.session_state.current_user.get_user_name()
                        orders = []
                        for item in history["orders"]:
                            order_key = item.get("_order_key")
                            if not order_key:
                                order_key = _find_order_key(
                                    item,
                                    client_name,
                                    history.get("timestamp", ""),
                                )
                            orders.append({
                                **item,
                                "_order_key": order_key,
                            })
                        _display_specific_order(orders)
    else:
        st.info("No orders added yet.")


def _find_order_key(
    client_order: dict[str, Any],
    client_name: str,
    timestamp: str,
) -> str | None:
    order_date = timestamp.split("T", maxsplit=1)[0]
    if not order_date:
        return None

    project_root = Path(__file__).resolve().parents[4]
    orders_directory = project_root / "assets" / "orders"
    for orders_file in sorted(orders_directory.glob(f"{order_date}*_orders.json")):
        try:
            with orders_file.open("r", encoding="utf-8") as file:
                orders_by_client = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            st.warning(f"Could not search order file {orders_file.name}: {exc}")
            continue
        if not isinstance(orders_by_client, dict):
            continue

        client_orders = orders_by_client.get(client_name, [])
        if not isinstance(client_orders, list):
            continue

        for item_index, item in enumerate(client_orders, start=1):
            if not isinstance(item, dict):
                continue
            if (
                item.get("_id") == client_order.get("_id")
                and item.get("_name") == client_order.get("_name")
                and item.get("_order_amount")
                == client_order.get("_order_amount")
            ):
                return f"{orders_file.name}|{client_name}|{item_index}"

    return None


@st.dialog("Order History", width="medium", position="center")
def _display_specific_order(order: list[dict[str, Any]]) -> None:
    """
    This method display the specific order choose by the client. 
    """
    display_order = []
    account_id = str(
        st.session_state.account.get("_account_number", "unknown")
    )
    actor_role = str(st.session_state.get("user_role", "unknown"))
    statuses = load_order_statuses()
    for item in order:
        order_key = item.get("_order_key")
        log_sensitive_access(
            "view",
            account_id,
            actor_role,
            "client_order",
            opaque_audit_id(
                str(order_key or f"{account_id}|{item.get('_id', 'unknown')}")
            ),
        )
        fallback_status = normalize_order_status(
            item.get("_order_status"),
        )
        status = normalize_order_status(
            statuses.get(order_key, fallback_status)
            if isinstance(order_key, str)
            else fallback_status,
            fallback_status,
        )
        in_date = item.get("_inDate", "")
        display_order.append({
            "ID": item.get("_id"),
            "Name": item.get("_name"),
            "Category": item.get("_category"),
            "Unit": item.get("_unit"),
            "InDate": in_date.split("T")[0] if in_date else "",
            "Tags": item.get("_tags", []),
            "Order Amount": item.get("_order_amount"),
            "Expiry Date": item.get("_expiryDate") or "Not set",
            "Order Status": status,
        })

    frame = pd.DataFrame(display_order)
    st.dataframe(frame, width="stretch", hide_index=True)

if __name__ == '__main__':
    show_client_order_history()