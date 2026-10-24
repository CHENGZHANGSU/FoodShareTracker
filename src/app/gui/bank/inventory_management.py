# gui/bank/inventory_management.py
import streamlit as st
import pandas as pd
from pathlib import Path

from app.food.inventory import Inventory
from app.gui.style import apply_app_style
from app.users.user import UserAccess


def get_inventory_manager() -> Inventory:
    """Return the inventory manager shared by pages in this session."""
    if "inventory_manager" not in st.session_state:
        project_root = Path(__file__).resolve().parents[4]
        inventory_path = project_root / "assets" / "inventory.json"

        st.session_state.inventory_manager = Inventory(
            str(inventory_path)
        )

    return st.session_state.inventory_manager


def show_inventory_management_page() -> None:
    """Display inventory management tools for authorised staff."""
    apply_app_style()
    st.title("Food Bank Stock Management")

    if not st.session_state.get("authenticated", False):
        st.error("Please log in to access stock management.")
        st.stop()

    if st.session_state.get("user_role") != UserAccess.STAFF:
        st.error("Access denied. This page is for Food Bank Staff.")
        st.stop()

    inventory = get_inventory_manager()

    inventory_tab, threshold_tab, alerts_tab = st.tabs(
        ["Inventory", "Set Minimum Stock Threshold", "Alerts"]
    )
   
    with inventory_tab:
        st.subheader("Current Inventory")

        foods = inventory.get_inventory()

        available_foods = [
            food for food in foods
            if food.get_food_stocks() > 0
        ]

        if available_foods:
            rows = [
                {
                    "ID": food.get_food_id(),
                    "Food Name": food.get_food_name(),
                    "Category": food.get_food_category(),
                    "Quantity": food.get_food_stocks(),
                    "Unit": food.get_food_unit(),
                    "Tags": ", ".join(
                        str(tag)
                        for tag in (food.get_food_tags() or [])
                        if tag is not None
                    ) or "None",
                }
                for food in available_foods
            ]

            st.dataframe(
                pd.DataFrame(rows),
                width='stretch',
                hide_index=True,
            )
        else:
            st.info("No food items currently have stock.")
    
    with threshold_tab:
        st.subheader("Set Minimum Stock Threshold")

        foods = inventory.get_inventory()

        if foods:
            food_options = {
                f"{food.get_food_name()} (ID {food.get_food_id()})":
                    food.get_food_id()
                for food in foods
            }

            selected_food = st.selectbox(
                "Food Item",
                list(food_options.keys()),
                key="threshold_food",
            )

            food_id = food_options[selected_food]

            threshold = st.number_input(
                "Minimum Stock Quantity",
                min_value=0.0,
                value=1.0,
                step=1.0,
                key="threshold_quantity",
            )

            if st.button("Save Threshold"):
                try:
                    inventory.set_minimum_stock(food_id, threshold)

                    st.success(
                        f"Minimum stock threshold saved for {selected_food}."
                    )
                    st.rerun()

                except (TypeError, ValueError) as exc:
                    st.error(str(exc))
        else:
            st.info("No food items available.")

    
    with alerts_tab:
        st.subheader("Low-stock Alerts")
        low_stock = inventory.get_low_stock_foods()

        if low_stock:
            for food in low_stock:
                st.warning(
                    f"{food.get_food_name()}: "
                    f"{food.get_food_stocks()} "
                    f"{food.get_food_unit()} remaining."
                )
        else:
            st.success("No low-stock alerts.")

        st.info(
            "Expiry dates are not tracked. Verify food safety before "
            "distribution."
        )


if __name__ == "__main__":
    show_inventory_management_page()