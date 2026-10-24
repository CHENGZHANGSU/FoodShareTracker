# gui/staff/pending_orders.py

import json
import streamlit as st
import pandas as pd

from pathlib import Path
from datetime import datetime

from app.gui.staff.order_status import (
    load_order_statuses,
    normalize_order_status,
)
from app.gui.shared.toolbar import require_role
from app.users.user import UserAccess
from util.admin_utils import log_sensitive_access, opaque_audit_id


def get_orders_directory() -> Path:
    """Find the project's assets/orders directory."""
    project_root = Path(__file__).resolve().parents[4]
    return project_root / "assets" / "orders"


def load_orders(
    client_name_filter: str | None = None,
) -> list[dict]:
    """Load order records and their saved preparation statuses."""
    orders_directory = get_orders_directory()
    orders = []
    errors = []
    statuses = load_order_statuses()

    if not orders_directory.exists():
        return orders, [
            f"Orders directory not found: {orders_directory}"
        ]

    for file_path in sorted(orders_directory.glob("*_orders.json")):
        try:
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                errors.append(
                    f"{file_path.name}: expected a JSON object."
                )
                continue

            try:
                file_time = datetime.strptime(
                    file_path.name,
                    "%Y-%m-%d_%H-%M-%S_orders.json",
                ).strftime("%d %b %Y, %H:%M")
            except ValueError:
                file_time = file_path.stem

            for client_name, items in data.items():
                if (
                    client_name_filter is not None
                    and client_name != client_name_filter
                ):
                    continue
                if not isinstance(items, list):
                    errors.append(
                        f"{file_path.name}: items for {client_name} "
                        "must be a list."
                    )
                    continue

                for item_index, item in enumerate(items, start=1):
                    if not isinstance(item, dict):
                        continue

                    order_id = item.get("_id", item_index)
                    quantity = item.get("_order_amount", 0)

                    try:
                        quantity = float(quantity)
                    except (TypeError, ValueError):
                        quantity = 0

                    order_key = (
                        f"{file_path.name}|{client_name}|{item_index}"
                    )
                    recorded_status = item.get("_order_status")
                    if (
                        isinstance(recorded_status, str)
                        and recorded_status in {
                            "Pending",
                            "Preparing",
                            "Ready for Collection",
                            "Completed",
                        }
                    ):
                        status = recorded_status
                    else:
                        status = normalize_order_status(
                            statuses.get(order_key, recorded_status),
                        )

                    orders.append({
                        "order_key": order_key,
                        "order_id": order_id,
                        "client": str(client_name),
                        "food_name": str(
                            item.get("_name", "Unknown food")
                        ),
                        "category": str(
                            item.get("_category", "Uncategorised")
                        ),
                        "quantity": quantity,
                        "unit": str(item.get("_unit", "")),
                        "date": file_time,
                        "file_name": file_path.name,
                        "status": status,
                    })

        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{file_path.name}: {exc}")

    return orders, errors


def show_pending_orders() -> None:
    """Display pending requests and saved preparation status."""
    require_role(UserAccess.STAFF)

    st.markdown(
        """
        <style>
        .stApp {
            background-color: #F8F7F2;
        }

        .orders-hero {
            background: linear-gradient(120deg, #E5EDE3, #F3E8E5);
            padding: 28px 30px;
            border-radius: 18px;
            margin-bottom: 22px;
            border: 1px solid #E0E6DC;
        }

        .orders-hero h1 {
            color: #34483A;
            font-size: 30px;
            margin: 0;
        }

        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E8E6DE;
            padding: 15px;
            border-radius: 13px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="orders-hero">
            <h1>Pending Orders</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    orders, errors = load_orders()

    # Orders not yet handed over to the client.
    pending_orders = [
        order for order in orders
        if order["status"] in ("Pending", "Preparing")
    ]

    # Prepared and waiting for collection.
    ready_orders = [
        order for order in orders
        if order["status"] == "Ready for Collection"
    ]

    # Successfully handed over and stock deducted.
    completed_orders = [
        order for order in orders
        if order["status"] == "Completed"
    ]
    col1, col2, col3 = st.columns(3)

    col1.metric("Pending Requests", len(pending_orders))
    col2.metric("Ready for Collection", len(ready_orders))
    col3.metric("Completed", len(completed_orders))
    st.divider()

    search_col, client_col = st.columns([2, 1])

    with search_col:
        search_text = st.text_input(
            "Search",
            placeholder="Search client, food name or food ID...",
        )

    with client_col:
        client_names = sorted({
            order["client"] for order in pending_orders
        })

        selected_client = st.selectbox(
            "Client",
            ["All Clients"] + client_names,
        )

    filtered_orders = pending_orders.copy()

    if selected_client != "All Clients":
        filtered_orders = [
            order for order in filtered_orders
            if order["client"] == selected_client
        ]

    if search_text.strip():
        query = search_text.strip().lower()

        filtered_orders = [
            order for order in filtered_orders
            if query in str(order["order_id"]).lower()
            or query in order["client"].lower()
            or query in order["food_name"].lower()
            or query in order["file_name"].lower()
        ]

    actor = st.session_state.get("account", {})
    actor_id = str(actor.get("_account_number", "unknown"))
    actor_role = str(st.session_state.get("user_role", UserAccess.STAFF))
    for order in orders:
        log_sensitive_access(
            "view",
            actor_id,
            actor_role,
            "client_order",
            opaque_audit_id(str(order["order_key"])),
        )

    st.subheader("Pending Requests")

    if filtered_orders:
        display_rows = [
            {
                "Food ID": order["order_id"],
                "Client": order["client"],
                "Food Item": order["food_name"],
                "Category": order["category"],
                "Requested Quantity": order["quantity"],
                "Unit": order["unit"],
                "Status": order["status"],
                "Order File Date": order["date"],
            }
            for order in filtered_orders
        ]

        st.dataframe(
            pd.DataFrame(display_rows),
            width='stretch',
            hide_index=True,
        )

        st.divider()
        st.subheader("View Request Details")

        request_labels = {
            (
                f"{order['client']} — {order['food_name']} "
                f"(Food ID {order['order_id']}, "
                f"{order['date']}, #{index})"
            ): order["order_key"]
            for index, order in enumerate(filtered_orders, start=1)
        }

        selected_label = st.selectbox(
            "Select a request",
            list(request_labels.keys()),
        )

        selected_key = request_labels[selected_label]

        selected_order = next(
            order for order in filtered_orders
            if order["order_key"] == selected_key
        )

        with st.container(border=True):
            st.write("**Client:**", selected_order["client"])
            st.write("**Food:**", selected_order["food_name"])
            st.write("**Category:**", selected_order["category"])
            st.write(
                "**Requested:**",
                f"{selected_order['quantity']:g} "
                f"{selected_order['unit']}",
            )
            st.write("**Status:**", selected_order["status"])
            st.write("**Record date:**", selected_order["date"])

            if st.button(
                "Use This Request in Order Details",
                width='stretch',
            ):
                st.session_state["selected_staff_order"] = selected_order
                st.success(
                    "Request selected. Open Order Details from the sidebar."
                )

    else:
        st.info("There are no matching pending requests.")

    
    with st.expander(f"Ready for Collection ({len(ready_orders)})"):
        if ready_orders:
            for index, order in enumerate(ready_orders):
                st.write(
                    f"**{order['client']} — {order['food_name']}** "
                    f"({order['quantity']:g} {order['unit']})"
                )
                st.caption(
                    f"Food ID: {order['order_id']} | "
                    f"Order date: {order['date']}"
                )

                if st.button(
                    "Open Order Details to Complete Handover",
                    key=f"ready_order_{index}_{order['order_key']}",
                    width='stretch',
                ):
                    st.session_state["selected_staff_order"] = order
                    st.session_state["open_handover_order"] = True
                    st.success(
                        "Order selected. Open Order Details from the sidebar."
                    )

                st.divider()
        else:
            st.info("No orders are ready for collection yet.")

    if errors:
        with st.expander("File loading warnings"):
            for error in errors:
                st.warning(error)


if __name__ == "__main__":
    show_pending_orders()
