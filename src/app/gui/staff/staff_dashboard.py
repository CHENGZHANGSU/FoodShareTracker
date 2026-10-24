# gui/staff/staff_dashboard.py

import streamlit as st
import pandas as pd
from pathlib import Path

from app.food.inventory import Inventory
from app.gui.shared.toolbar import show_toolbar
from app.gui.style import (
    apply_app_style,
    apply_staff_dashboard_style,
    show_dashboard_header,
)
from app.users.user import UserAccess


def get_inventory_manager() -> Inventory:
    """Reuse the inventory manager stored in this Streamlit session."""
    if "inventory_manager" not in st.session_state:
        project_root = Path(__file__).resolve().parents[4]
        inventory_path = project_root / "assets" / "inventory.json"

        st.session_state.inventory_manager = Inventory(
            str(inventory_path)
        )

    return st.session_state.inventory_manager


def show_staff_dashboard() -> None:
    """Display the Food Bank Staff dashboard."""
    apply_app_style()
    apply_staff_dashboard_style()
    show_toolbar()

    show_dashboard_header("FoodShare Staff Dashboard", "Staff")

    # Access control
    if not st.session_state.get("authenticated", False):
        st.error("Please log in to access the Staff Dashboard.")
        st.stop()

    if st.session_state.get("user_role") != UserAccess.STAFF:
        st.error("Access denied. This page is for Food Bank Staff.")
        st.stop()

    inventory = get_inventory_manager()

    foods = inventory.get_inventory()
    low_stock = inventory.get_low_stock_foods()
    expired_foods = inventory.get_expired_foods()

    total_quantity = sum(
        food.get_food_stocks()
        for food in foods
        if isinstance(food.get_food_stocks(), (int, float))
    )

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Food Items", len(foods))
    col2.metric("Total Stock", f"{total_quantity:g}")
    col3.metric("Low Stock", len(low_stock))
    col4.metric("Out-of-date Food", len(expired_foods))

    st.write("")

    left, right = st.columns([1.7, 1])

    # Current inventory
    with left:
        st.subheader("Current Inventory")
        st.markdown(
            '<p class="section-caption">'
            'The food items currently recorded.'
            '</p>',
            unsafe_allow_html=True,
        )

        available_foods = [
            food for food in foods
            if food.get_food_stocks() > 0
        ]

        if available_foods:
            rows = [
                {
                    "Food": food.get_food_name(),
                    "Category": food.get_food_category(),
                    "Quantity": food.get_food_stocks(),
                    "Unit": food.get_food_unit(),
                }
                for food in available_foods
            ]

            st.dataframe(
                pd.DataFrame(rows),
                width='stretch',
                hide_index=True,
            )
        else:
            st.info("No food items found in inventory.")

    # Dynamic inventory alerts
    with right:
        st.subheader("Inventory Alerts")
        st.markdown(
            '<p class="section-caption">'
            'Items that may need your attention.'
            '</p>',
            unsafe_allow_html=True,
        )

        if low_stock:
            critical_items = [
                food for food in low_stock
                if food.get_food_stocks() == 0
            ]

            if critical_items:
                for food in critical_items:
                    st.markdown(
                        f"""
                        <div class="alert-critical">
                            <strong>Out of stock</strong><br>
                            {food.get_food_name()} has no remaining stock.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            warning_items = [
                food for food in low_stock
                if food.get_food_stocks() != 0
            ]

            if warning_items:
                for food in warning_items:
                    st.markdown(
                        f"""
                        <div class="alert-warning">
                            <strong>Low stock</strong><br>
                            {food.get_food_name()}: 
                            {food.get_food_stocks()} 
                            {food.get_food_unit()} remaining.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown(
                """
                <div class="alert-normal">
                    <strong>Stock levels look good</strong><br>
                    No items are below their minimum thresholds.
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.subheader("Out-of-date Food")
        if expired_foods:
            for food in expired_foods:
                st.error(
                    f"{food.get_food_name()} is out of date "
                    f"(expiry date: {food.get_food_expiry_date()}). "
                    f"Recorded stock: {food.get_food_stocks()} "
                    f"{food.get_food_unit()}."
                )
        else:
            st.success("No out-of-date food items.")

        st.divider()
        st.caption("Check expiry dates before preparing or handing over food.")


if __name__ == "__main__":
    st.session_state["authenticated"] = True
    st.session_state["user_role"] = UserAccess.STAFF
    show_staff_dashboard()
