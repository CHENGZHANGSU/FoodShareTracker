# gui/client/client_order.py
import streamlit as st
import pandas as pd 
from app.gui.style import makrdown_options, markdown_home
from app.gui.shared.toolbar import require_role
from app.users.user import UserAccess

from app.gui.main import get_shared_inventory

def show_start_order_page() -> None:
    require_role(UserAccess.CLIENT)
    st.session_state.inventory = get_shared_inventory()

    ordering, home, helps = st.columns(
        [4, 1, 1],
        vertical_alignment="center",
    )

    with ordering:
        st.header("Ordering")
    with home:
        markdown_home()
        if st.button("Home", key="client_order_home", width="stretch"):
            st.switch_page("client/client_dashboard.py")
    with helps:
        makrdown_options()
        if st.button("Helps", key="client_order_helps", width="stretch"):
            st.switch_page("helps.py")

    foods = st.session_state.inventory.get_inventory()
    categories = sorted({food.get_food_category() for food in foods})
    if not categories:
        st.info("There are no food items available to order.")
        return

    selected_category = st.session_state.setdefault(
        "client_selected_food_category",
        categories[0],
    )
    if selected_category not in categories:
        selected_category = categories[0]
        st.session_state["client_selected_food_category"] = selected_category

    # order_quantities = st.session_state.setdefault("client_order_quantities", {})
    if "order_quantity" not in st.session_state:
        st.session_state.order_quantity = {}

    category_column, food_column = st.columns([1, 3], gap="large")

    with category_column:
        st.subheader("Categories")
        for index, category in enumerate(categories):
            label = f"* {category}" if category == selected_category else category
            if st.button(label, key=f"client_food_category_{index}", width="stretch"):
                selected_category = category
                st.session_state["client_selected_food_category"] = category

    with food_column:
        st.subheader(selected_category)
        category_foods = [
            food for food in foods if food.get_food_category() == selected_category
        ]
        for food in category_foods:
            food_name = food.get_food_name()
            available_stock = max(0, int(food.get_food_stocks()))
            ordered_quantity = st.session_state.order_quantity.get(food_name, 0)
            add_disabled = (
                available_stock == 0 or ordered_quantity >= available_stock
            )
            with st.container(border=True):
                details, action = st.columns([4, 1], vertical_alignment="center")
                with details:
                    in_date_parts = food.get_food_in_date().split("T", maxsplit=1)
                    in_date = in_date_parts[0] or "Unknown"
                    in_time = in_date_parts[1] if len(in_date_parts) > 1 else ""
                    st.markdown(f"**{food_name}**")
                    st.caption(
                        f"Stock: {food.get_food_stocks()} {food.get_food_unit()}  |  "
                        f"In date: {in_date}"
                        + (f"  {in_time}" if in_time else "")
                    )
                    tags = food.get_food_tags()
                    st.caption(f"Tags: {', '.join(str(tag) for tag in tags) if tags else '-'}")
                with action:
                    st.caption(f"In order: {ordered_quantity}")
                    if st.button(
                        "Add",
                        key=f"client_add_food_{food.get_food_id()}",
                        disabled=add_disabled,
                        width="stretch",
                    ):
                        st.session_state.order_quantity[food_name] = ordered_quantity + 1
                        st.session_state.tracker.add_food_order(food.get_food_name(), 1)
                        st.rerun()
                if add_disabled:
                    if available_stock == 0:
                        st.warning("This food is out of stock.")
                    else:
                        st.warning("You have added all available stock.")

        st.subheader("Your Order")
        if len(st.session_state.tracker.list_orders()) > 0:
            for order in st.session_state.tracker.list_orders():
                st.write(f"{order.get_food_name()} - {order.get_order_amount()}")
        else:
            st.caption("No items added yet.")

        if st.button("Ordered Food"):
            st.switch_page("client/display_order.py")


    

if __name__ == "__main__":
    show_start_order_page()