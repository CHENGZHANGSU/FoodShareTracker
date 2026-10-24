# gui/staff/adjust_stock.py
import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from app.food.inventory import Inventory
from app.gui.style import apply_app_style
from app.users.user import UserAccess

logger = logging.getLogger(__name__)


def get_inventory_manager() -> Inventory:
    """Get the inventory manager for this Streamlit session."""
    if "inventory_manager" not in st.session_state:
        project_root = Path(__file__).resolve().parents[4]
        inventory_path = project_root / "assets" / "inventory.json"
        st.session_state["inventory_manager"] = Inventory(
            str(inventory_path)
        )
    return st.session_state["inventory_manager"]


def show_adjust_stock() -> None:
    """Allow staff to adjust inventory totals."""
    apply_app_style()

    st.markdown(
        """
        <style>
        .stApp {
            background-color: #F8F7F2;
        }
        .adjust-hero {
            background: linear-gradient(120deg, #E5EDE3, #F3E8E5);
            padding: 28px 30px;
            border-radius: 18px;
            margin-bottom: 22px;
            border: 1px solid #E0E6DC;
        }
        .adjust-hero h1 {
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
        <div class="adjust-hero">
            <h1>Adjust Stock</h1>
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

    inventory = get_inventory_manager()
    foods = inventory.get_inventory()

    if not foods:
        st.info("No food items are available to adjust.")
        return

    total_quantity = sum(
        food.get_food_stocks()
        for food in foods
        if isinstance(food.get_food_stocks(), (int, float))
    )

    col1, col2 = st.columns(2)
    col1.metric("Food Items", len(foods))
    col2.metric("Total Stock", f"{total_quantity:g}")

    st.divider()
    st.subheader("Stock Adjustment Form")
    st.caption("Set the correct total quantity for the selected food item.")

    food_options = {
        f"{food.get_food_name()} (ID {food.get_food_id()})":
        food.get_food_id()
        for food in foods
    }

    with st.form("adjust_stock_page_form"):
        selected_food = st.selectbox(
            "Food Item",
            list(food_options.keys()),
        )
        food_id = food_options[selected_food]
        selected_item = inventory.find_food_by_id(food_id)
        current_quantity = (
            selected_item.get_food_stocks()
            if selected_item is not None
            else 0
        )

        st.number_input(
            "Current Quantity",
            min_value=0.0,
            value=float(current_quantity),
            disabled=True,
        )

        new_quantity = st.number_input(
            "New Total Quantity",
            min_value=0.0,
            value=float(current_quantity),
            step=1.0,
        )

        reason = st.selectbox(
            "Reason for Adjustment",
            [
                "Stocktake correction",
                "Damaged goods",
                "Spoiled food",
                "Data entry correction",
                "Other",
            ],
        )

        additional_notes = st.text_area(
            "Additional Notes",
            placeholder="Explain the adjustment...",
        )

        submitted = st.form_submit_button(
            "Save Adjustment",
            width='stretch',
        )

    if submitted:
        try:
            if selected_item is None:
                raise ValueError("Food item not found.")

            if new_quantity == current_quantity:
                raise ValueError(
                    "The new quantity is the same as the current quantity."
                )

            if reason == "Other" and not additional_notes.strip():
                raise ValueError(
                    "Please provide notes when the reason is Other."
                )

            full_reason = reason
            if additional_notes.strip():
                full_reason += ": " + additional_notes.strip()

            inventory.adjust_stock(
                food_id=food_id,
                new_quantity=new_quantity,
                reason=full_reason,
            )

            logger.info(
                "Staff adjusted stock: food_id=%s, old_quantity=%s, "
                "new_quantity=%s, reason=%s",
                food_id,
                current_quantity,
                new_quantity,
                full_reason,
            )

            st.success(
                f"{selected_item.get_food_name()} stock updated: "
                f"{current_quantity:g} → {new_quantity:g} "
                f"{selected_item.get_food_unit()}."
            )
            st.rerun()

        except (TypeError, ValueError, OSError) as exc:
            logger.warning("Stock adjustment failed: %s", exc)
            st.error(str(exc))

    st.divider()
    st.subheader("Current Stock Overview")

    current_foods = inventory.get_inventory()
    rows = [
        {
            "Food ID": food.get_food_id(),
            "Food Name": food.get_food_name(),
            "Category": food.get_food_category(),
            "Current Quantity": food.get_food_stocks(),
            "Unit": food.get_food_unit(),
        }
        for food in current_foods
    ]

    st.dataframe(
        pd.DataFrame(rows),
        width='stretch',
        hide_index=True,
    )


if __name__ == "__main__":
    st.session_state["authenticated"] = True
    st.session_state["user_role"] = UserAccess.STAFF
    show_adjust_stock()
