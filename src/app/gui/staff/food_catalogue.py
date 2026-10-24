# gui/staff/food_catalogue.py
import logging
import streamlit as st
import pandas as pd

from app.food.food_item import FoodItem
from app.food.inventory import Inventory
from app.gui.style import apply_app_style
from app.users.user import UserAccess

logger = logging.getLogger(__name__)


def get_inventory_manager() -> Inventory:
    """Reuse the inventory manager shared by this Streamlit session."""
    if "inventory_manager" not in st.session_state:
        from pathlib import Path

        project_root = Path(__file__).resolve().parents[4]
        inventory_path = project_root / "assets" / "inventory.json"

        st.session_state["inventory_manager"] = Inventory(
            str(inventory_path)
        )

    return st.session_state["inventory_manager"]


def show_food_catalogue() -> None:
    """Staff page for creating and correcting food catalogue entries."""
    apply_app_style()

    st.markdown(
        """
        <style>
        .stApp {
            background-color: #F8F7F2;
        }
        .catalogue-hero {
            background: linear-gradient(120deg, #E5EDE3, #F3E8E5);
            padding: 26px 30px;
            border-radius: 16px;
            margin-bottom: 22px;
            border: 1px solid #E0E6DC;
        }
        .catalogue-hero h1 {
            color: #34483A;
            font-size: 30px;
            margin: 0 0 8px 0;
        }
        .catalogue-hero p {
            color: #68776A;
            font-size: 14px;
            margin: 0;
        }
        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E8E6DE;
            padding: 14px;
            border-radius: 12px;
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
        <div class="catalogue-hero">
            <h1>Food Catalogue Management</h1>
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

    col1, col2 = st.columns(2)
    col1.metric("Food Types", len(foods))
    col2.metric(
        "Total Stock",
        sum(
            food.get_food_stocks()
            for food in foods
            if isinstance(food.get_food_stocks(), (int, float))
        ),
    )

    tab_add, tab_edit, tab_view = st.tabs(
        ["Add Food Type", "Edit Food Details", "View Catalogue"]
    )

    with tab_add:
        st.subheader("Register a New Food Type")
        st.caption(
            "New food types start with zero stock. "
            "Use Receive Stock to record actual donations."
        )

        with st.form("add_food_catalogue_form", clear_on_submit=False):
            name = st.text_input("Food Name", placeholder="e.g. Apple")

            category = st.selectbox(
                "Category",
                [
                    "Fruit",
                    "Vegetables",
                    "Meat",
                    "Seafood",
                    "Dairy",
                    "Grains",
                    "Canned Food",
                    "Other",
                ],
            )

            unit = st.selectbox(
                "Unit",
                ["kg", "g", "pieces", "litres", "packs", "boxes"],
            )

            tags_text = st.text_input(
                "Tags (optional)",
                placeholder="e.g. Vegan, Fresh",
            )

            expiry_date = st.text_input(
                "Expiry Date (YYYY-MM-DD, optional)",
                placeholder="e.g. 2026-10-30",
            )

            add_submitted = st.form_submit_button(
                "Register Food Type",
                width='stretch',
            )

        if add_submitted:
            clean_name = name.strip()

            if not clean_name:
                st.error("Food name cannot be empty.")
            elif any(
                food.get_food_name().strip().casefold()
                == clean_name.casefold()
                for food in inventory.get_inventory()
            ):
                st.error(
                    "A food type with this name already exists. "
                    "Use Edit Food Details to correct an existing entry."
                )
            else:
                try:
                    tags = [
                        tag.strip()
                        for tag in tags_text.split(",")
                        if tag.strip()
                    ]

                    # The next ID is allocated from existing inventory IDs.
                    existing_ids = [
                        food.get_food_id()
                        for food in inventory.get_inventory()
                        if isinstance(food.get_food_id(), int)
                        and not isinstance(food.get_food_id(), bool)
                    ]
                    new_food_id = max(existing_ids, default=0) + 1

                    new_food = FoodItem(
                        new_food_id,
                        clean_name,
                        category,
                        0.0,
                        unit,
                        tags if tags else [None],
                        expiryDate=expiry_date.strip() or None,
                    )

                    added = inventory.add_food_to_inventory(new_food)

                    if added:
                        logger.info(
                            "Food catalogue item created: food_id=%s, "
                            "name=%s, category=%s",
                            new_food_id,
                            clean_name,
                            category,
                        )
                        st.success(
                            f"{clean_name} registered successfully "
                            "with zero stock."
                        )
                        st.rerun()
                    else:
                        st.error(
                            "The food type could not be added. "
                            "Check whether its name already exists."
                        )

                except (TypeError, ValueError, KeyError) as exc:
                    logger.exception("Failed to register food type")
                    st.error(f"Could not register food type: {exc}")


    with tab_edit:
        st.subheader("Correct Existing Food Details")

        foods = inventory.get_inventory()

        if not foods:
            st.info("There are no food types to edit yet.")
        else:
            food_options = {
                f"{food.get_food_name()} (ID {food.get_food_id()})":
                food.get_food_id()
                for food in foods
            }

            selected_label = st.selectbox(
                "Select Food Type",
                list(food_options.keys()),
                key="catalogue_edit_selection",
            )
            selected_id = food_options[selected_label]
            selected_food = inventory.find_food_by_id(selected_id)

            if selected_food is not None:
                with st.form("edit_food_catalogue_form"):
                    edited_name = st.text_input(
                        "Food Name",
                        value=selected_food.get_food_name(),
                    )

                    categories = [
                        "Fruit",
                        "Vegetables",
                        "Meat",
                        "Seafood",
                        "Dairy",
                        "Grains",
                        "Canned Food",
                        "Other",
                    ]
                    current_category = selected_food.get_food_category()
                    category_index = (
                        categories.index(current_category)
                        if current_category in categories
                        else categories.index("Other")
                    )

                    edited_category = st.selectbox(
                        "Category",
                        categories,
                        index=category_index,
                    )

                    units = [
                        "kg", "g", "pieces", "litres", "packs", "boxes"
                    ]
                    current_unit = selected_food.get_food_unit()
                    unit_index = (
                        units.index(current_unit)
                        if current_unit in units
                        else 0
                    )

                    edited_unit = st.selectbox(
                        "Unit",
                        units,
                        index=unit_index,
                    )

                    current_tags = selected_food.get_food_tags() or []
                    current_tags_text = ", ".join(
                        str(tag)
                        for tag in current_tags
                        if tag is not None
                    )

                    edited_tags_text = st.text_input(
                        "Tags (comma-separated)",
                        value=current_tags_text,
                    )

                    edited_expiry_date = st.text_input(
                        "Expiry Date (YYYY-MM-DD, optional)",
                        value=selected_food.get_food_expiry_date() or "",
                    )

                    edit_submitted = st.form_submit_button(
                        "Save Food Details",
                        width='stretch',
                    )

                if edit_submitted:
                    clean_name = edited_name.strip()

                    duplicate = any(
                        food.get_food_id() != selected_id
                        and food.get_food_name().strip().casefold()
                        == clean_name.casefold()
                        for food in inventory.get_inventory()
                    )

                    if not clean_name:
                        st.error("Food name cannot be empty.")
                    elif duplicate:
                        st.error(
                            "Another food type already uses this name."
                        )
                    else:
                        try:
                            edited_tags = [
                                tag.strip()
                                for tag in edited_tags_text.split(",")
                                if tag.strip()
                            ]

                            inventory.update_food_from_inventory(
                                selected_id,
                                name=clean_name,
                                category=edited_category,
                                unit=edited_unit,
                                tags=edited_tags if edited_tags else [None],
                                expiry_date=edited_expiry_date.strip() or None,
                            )

                            logger.info(
                                "Food catalogue item updated: food_id=%s",
                                selected_id,
                            )
                            st.success("Food details updated successfully.")
                            st.rerun()

                        except (TypeError, ValueError, KeyError) as exc:
                            logger.exception("Failed to update food details")
                            st.error(f"Could not update food details: {exc}")


    with tab_view:
        st.subheader("Current Food Catalogue")

        foods = inventory.get_inventory()

        if not foods:
            st.info("No food types have been registered yet.")
        else:
            rows = [
                {
                    "Food ID": food.get_food_id(),
                    "Food Name": food.get_food_name(),
                    "Category": food.get_food_category(),
                    "Stock": food.get_food_stocks(),
                    "Unit": food.get_food_unit(),
                    "Expiry Date": food.get_food_expiry_date() or "Not set",
                    "Tags": ", ".join(
                        str(tag)
                        for tag in (food.get_food_tags() or [])
                        if tag is not None
                    ) or "None",
                }
                for food in foods
            ]

            st.dataframe(
                pd.DataFrame(rows),
                width='stretch',
                hide_index=True,
            )


if __name__ == "__main__":
    show_food_catalogue()
