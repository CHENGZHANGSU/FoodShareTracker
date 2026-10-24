# gui/staff/receive_stock.py

import streamlit as st
from pathlib import Path

from app.food.inventory import Inventory
from app.gui.style import apply_app_style
from app.users.user import UserAccess
import logging

logger = logging.getLogger(__name__)
def get_inventory_manager() -> Inventory:
    """Reuse the inventory manager stored in this Streamlit session."""
    if "inventory_manager" not in st.session_state:
        project_root = Path(__file__).resolve().parents[4]
        inventory_path = project_root / "assets" / "inventory.json"

        st.session_state.inventory_manager = Inventory(
            str(inventory_path)
        )

    return st.session_state.inventory_manager


def show_receive_stock() -> None:
    """Display the receive-stock page for authorised staff."""
    apply_app_style()

    st.markdown(
        """
        <style>
        .stApp {
            background-color: #F8F7F2;
        }

        .receive-hero {
            background: linear-gradient(120deg, #E5EDE3, #F3E8E5);
            padding: 28px 30px;
            border-radius: 18px;
            margin-bottom: 22px;
            border: 1px solid #E0E6DC;
        }

        .receive-hero h1 {
            color: #34483A;
            font-size: 30px;
            margin: 0 0 8px 0;
        }

        .receive-hero p {
            color: #68776A;
            font-size: 14px;
            margin: 0;
        }

        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E8E6DE;
            padding: 15px;
            border-radius: 13px;
        }

        div.stButton > button,
        div.stFormSubmitButton > button {
            border-radius: 10px;
            border: 1px solid #C8D6C5;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="receive-hero">
            <h1>Receive Stock</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Authentication
    if not st.session_state.get("authenticated", False):
        st.error("Please log in to access this page.")
        st.stop()

    if st.session_state.get("user_role") != UserAccess.STAFF:
        st.error("Access denied. This page is for Food Bank Staff.")
        st.stop()

    inventory = get_inventory_manager()
    foods = inventory.get_inventory()

    total_items = len(foods)
    total_quantity = sum(
        food.get_food_stocks()
        for food in foods
        if isinstance(food.get_food_stocks(), (int, float))
    )

    metric1, metric2 = st.columns(2)
    metric1.metric("Food Items", total_items)
    metric2.metric("Total Stock", total_quantity)

    st.divider()

    st.subheader("Record Incoming Donation")
    st.caption(
        "Add received food directly to the inventory total. Expiry dates are "
        "not tracked; verify food safety before distribution."
    )

    if not foods:
        st.warning(
            "No food items are available. Add food items to inventory "
            "before recording incoming stock."
        )
        return

    food_options = {
        f"{food.get_food_name()} (ID {food.get_food_id()})":
        food.get_food_id()
        for food in foods
    }

    with st.form("receive_stock_form"):
        selected_food = st.selectbox(
            "Food Item",
            list(food_options.keys()),
        )

        quantity = st.number_input(
            "Quantity Received",
            min_value=1.0,
            value=1.0,
            step=1.0,
        )

        submitted = st.form_submit_button(
            "Record Incoming Stock",
            width='stretch',
        )

        if submitted:
            try:
                food_id = food_options[selected_food]
                food = inventory.find_food_by_id(food_id)

                if food is None:
                    raise ValueError("Food item not found.")

                inventory.record_incoming_stock(
                    food_id=food_id,
                    quantity=quantity,
                )

                logger.info(
                    "Staff recorded incoming stock: food_id=%s, quantity=%s",
                    food_id,
                    quantity,
                )

                st.success(
                    f"Successfully recorded {quantity:g} "
                    f"{food.get_food_unit()} of {food.get_food_name()}."
                )

                st.rerun()

            except (TypeError, ValueError) as exc:
                logger.warning("Failed to record incoming stock: %s", exc)
                st.error(str(exc))

    st.divider()

    st.subheader("Current Stock Overview")

    if foods:
        import pandas as pd

        rows = [
            {
                "Food ID": food.get_food_id(),
                "Food Name": food.get_food_name(),
                "Category": food.get_food_category(),
                "Current Quantity": food.get_food_stocks(),
                "Unit": food.get_food_unit(),
            }
            for food in foods
        ]

        st.dataframe(
            pd.DataFrame(rows),
            width='stretch',
            hide_index=True,
        )


if __name__ == "__main__":
    st.session_state["authenticated"] = True
    st.session_state["user_role"] = UserAccess.STAFF
    show_receive_stock()
