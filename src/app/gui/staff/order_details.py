# gui/staff/order_details.py
import streamlit as st
from pathlib import Path

from app.food.inventory import Inventory
from app.gui.style import apply_app_style
from app.users.user import UserAccess
from app.gui.staff.order_status import (
    load_order_statuses,
    save_order_status,
)
from util.admin_utils import log_sensitive_access, opaque_audit_id


def get_inventory_manager() -> Inventory:
    """Reuse the inventory manager stored in this Streamlit session."""
    if "inventory_manager" not in st.session_state:
        project_root = Path(__file__).resolve().parents[4]
        inventory_path = project_root / "assets" / "inventory.json"
        st.session_state["inventory_manager"] = Inventory(
            str(inventory_path)
        )

    return st.session_state["inventory_manager"]


def show_order_details() -> None:
    apply_app_style()
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #F8F7F2;
        }
        .details-hero {
            background: linear-gradient(120deg, #E5EDE3, #F3E8E5);
            padding: 28px 30px;
            border-radius: 18px;
            margin-bottom: 22px;
            border: 1px solid #E0E6DC;
        }
        .details-hero h1 {
            color: #34483A;
            font-size: 29px;
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
        <div class="details-hero">
            <h1>Order Details & Hamper Preparation</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.get("authenticated", False):
        st.error("Please log in to access this page.")
        st.stop()

    if st.session_state.get("user_role") != UserAccess.STAFF:
        st.error("Access denied. This page is for Food Bank Staff.")
        st.stop()

    order = st.session_state.get("selected_staff_order")

    if not order:
        st.info(
            "No request selected. Open Pending Orders and select "
            "a request first."
        )
        return

    order_key = order.get("order_key")
    if not order_key:
        st.error("Order record key is missing. Please select the order again.")
        return

    actor = st.session_state.get("account", {})
    actor_id = str(actor.get("_account_number", "unknown"))
    actor_role = str(st.session_state.get("user_role", UserAccess.STAFF))
    log_sensitive_access(
        "view",
        actor_id,
        actor_role,
        "client_order",
        opaque_audit_id(str(order_key)),
    )

    statuses = load_order_statuses()
    persisted_status = statuses.get(order_key, "Pending")

    preparation_key = f"preparation_{order_key}"

    if preparation_key not in st.session_state:
        st.session_state[preparation_key] = {
            "status": persisted_status,
            "notes": "",
            "quantity_checked": False,
            "expiry_checked": False,
            "packed": False,
        }

    current = st.session_state[preparation_key]
    current["status"] = persisted_status

    inventory = get_inventory_manager()

    food_id = order.get("order_id")
    food = inventory.find_food_by_id(food_id)

    # JSON IDs may be strings while Inventory IDs are integers.
    if food is None:
        try:
            food = inventory.find_food_by_id(int(food_id))
        except (TypeError, ValueError):
            food = None

    st.subheader("Selected Request")

    col1, col2, col3 = st.columns(3)
    col1.metric("Food Item", order.get("food_name", "Unknown"))
    col2.metric(
        "Requested Quantity",
        f"{order.get('quantity', 0):g} {order.get('unit', '')}".strip(),
    )
    col3.metric("Client", order.get("client", "Unknown"))

    with st.container(border=True):
        st.write("**Food:**", order.get("food_name", "Unknown"))
        st.write("**Food ID:**", food_id)
        st.write("**Category:**", order.get("category", "Unknown"))
        st.write("**Client:**", order.get("client", "Unknown"))
        st.write("**Record date:**", order.get("date", "Unknown"))
        st.write("**Current status:**", persisted_status)

    if persisted_status == "Completed":
        st.success("This order has already been handed over. Stock was processed.")
        return

    st.divider()
    st.subheader("Hamper Preparation")

    status_options = ["Pending", "Preparing", "Ready for Collection"]
    if current["status"] not in status_options:
        current["status"] = "Pending"

    with st.form("hamper_preparation_form"):
        status = st.selectbox(
            "Preparation Status",
            status_options,
            index=status_options.index(current["status"]),
        )

        quantity_checked = st.checkbox(
            "Requested quantity checked",
            value=current["quantity_checked"],
        )
        expiry_checked = st.checkbox(
            "Food expiry information checked",
            value=current["expiry_checked"],
        )
        packed = st.checkbox(
            "Hamper packed and ready",
            value=current["packed"],
        )
        notes = st.text_area(
            "Preparation Notes",
            value=current["notes"],
            placeholder="Record packing notes or substitution details...",
        )

        submitted = st.form_submit_button(
            "Save Preparation Progress",
            width='stretch',
        )

        if submitted:
            if status == "Ready for Collection" and not (
                quantity_checked and expiry_checked and packed
            ):
                st.error(
                    "Confirm quantity, expiry information and packing "
                    "before marking the order ready."
                )
            else:
                try:
                    save_order_status(
                        order_key,
                        status,
                        actor_id=actor_id,
                        actor_role=actor_role,
                    )
                    st.session_state[preparation_key] = {
                        "status": status,
                        "notes": notes,
                        "quantity_checked": quantity_checked,
                        "expiry_checked": expiry_checked,
                        "packed": packed,
                    }
                    order["status"] = status
                    st.session_state["selected_staff_order"] = order
                    st.success(f"Preparation status saved: {status}")
                    st.rerun()
                except (OSError, ValueError) as exc:
                    st.error(f"Could not save status: {exc}")

    st.divider()
    st.subheader("Confirm Actual Food Handover")

    st.caption(
        "Only click this after the food has actually been handed to the client. "
        "Stock will be deducted from the inventory total. Verify the food is "
        "safe to distribute; expiry dates are not tracked."
    )

    if persisted_status != "Ready for Collection":
        st.info("Save the status as Ready for Collection and complete the checklist first.")
        return

    if not (
        current["quantity_checked"]
        and current["expiry_checked"]
        and current["packed"]
    ):
        st.warning("The preparation checklist is incomplete.")
        return

    if food is None:
        st.error(
            f"Food ID {food_id} was not found in inventory. "
            "No stock has been deducted."
        )
        return

    requested_quantity = order.get("quantity", 0)

    if st.button(
        "Confirm Food Handover",
        type="primary",
        width='stretch',
    ):
        try:
            if requested_quantity <= 0:
                raise ValueError("Order quantity must be greater than zero.")

            # Check status again to reduce accidental duplicate deductions.
            latest_status = load_order_statuses().get(order_key, "Pending")
            if latest_status == "Completed":
                st.warning("This order has already been completed.")
                st.rerun()

            inventory.allocate_stock(
                food.get_food_id(),
                requested_quantity,
            )

            # Save Completed only after stock deduction succeeds.
            save_order_status(
                order_key,
                "Completed",
                actor_id=actor_id,
                actor_role=actor_role,
            )

            current["status"] = "Completed"
            st.session_state[preparation_key] = current
            order["status"] = "Completed"
            st.session_state["selected_staff_order"] = order

            st.success(
                f"Handover confirmed. Deducted {requested_quantity:g} "
                f"{food.get_food_unit()} of {food.get_food_name()}."
            )
            st.rerun()

        except (TypeError, ValueError, OSError) as exc:
            st.error(
                f"Handover was not completed: {exc}. "
                "Check the inventory total and try again."
            )

    st.divider()
    st.subheader("Preparation Summary")

    st.write("**Status:**", current["status"])
    st.write(
        "**Quantity checked:**",
        "Yes" if current["quantity_checked"] else "Not yet",
    )
    st.write(
        "**Expiry information checked:**",
        "Yes" if current["expiry_checked"] else "Not yet",
    )
    st.write("**Hamper packed:**", "Yes" if current["packed"] else "Not yet")

    if current["notes"].strip():
        st.write("**Notes:**", current["notes"])


if __name__ == "__main__":
    st.session_state["authenticated"] = True
    st.session_state["user_role"] = UserAccess.STAFF
    show_order_details()
