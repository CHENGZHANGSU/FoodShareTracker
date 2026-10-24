# gui/client/client_dashboard.py
import json
import streamlit as st
import pandas as pd

from app.core.food_tracker_client import FoodShareTracker

from app.users.client import Client
from app.users.user import UserAccess
from app.users.constraint import *

from app.food.inventory import Inventory
from app.food.food_item import FoodItem

from app.exceptions.NotFoundException import FoodNotFound

from app.gui.main import get_shared_inventory
from app.gui.shared.toolbar import require_role, show_toolbar
from app.gui.style import show_dashboard_header

# food = FoodItem(1, "Beef", "Meat", 10, "kg", [LifeStyle.VEGAN])
# food2 = FoodItem(2, "Shrimp", "Meat", 10, "kg")


    # st.session_state.inventory = Inventory()
    # st.session_state.inventory.add_food_to_inventory(food)
    # st.session_state.inventory.add_food_to_inventory(food2)
    # st.session_state.inventory.save_data()

def show_client_home_page() -> None:
    require_role(UserAccess.CLIENT)
    show_toolbar()
    show_dashboard_header("FoodShare Client Dashboard", "Client")
    st.session_state.inventory = get_shared_inventory()

    food_name = st.selectbox("Find food", [f.get_food_name() for f in st.session_state.inventory.get_inventory()], 
                            index=None, placeholder="Enter the food name you are looking for: ")
    if food_name:
        try:
            found = st.session_state.tracker.find_food_by_name(str(food_name))
            if found:
                in_date = found.get_food_in_date().split("T", maxsplit=1)[0]
                frame = pd.DataFrame([{
                    "ID": found.get_food_id(),
                    "Name": found.get_food_name(),
                    "Stock": found.get_food_stocks(),
                    "Category": found.get_food_category(),
                    "Unit": found.get_food_unit(),
                    "InDate": in_date,
                    "Expiry Date": found.get_food_expiry_date() or "Not set",
                }])
                st.dataframe(frame, width="stretch", hide_index=True)
                tags = [
                    str(tag)
                    for tag in found.get_food_tags()
                    if tag is not None
                ]
                st.write(f"**Tags:** {', '.join(tags) if tags else '-'}")
                st.success(f"Food {food_name} founded.")
        except FoodNotFound as e:
            st.warning(str(e))


    st.subheader("Food List")
    inventory_table()

def inventory_table() -> None:
    frame = pd.DataFrame(st.session_state.inventory.list_food())
    frame.columns = ["ID", "Name", "Stock", "Category", "Unit", "InDate", "Tags", "Expiry Date"]
    st.dataframe(frame, width="stretch", hide_index=True)


if __name__ == "__main__":
    show_client_home_page()