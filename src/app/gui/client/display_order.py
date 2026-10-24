# gui/client/display_order.py
import streamlit as st
import pandas as pd

from app.exceptions.NotFoundException import OrderNotFound

from app.gui.style import makrdown_options
from app.gui.shared.toolbar import require_role
from app.users.user import UserAccess

def show_client_order_page() -> None:
    require_role(UserAccess.CLIENT)
    st.session_state.setdefault("show_substitution", False)

    ordering, back = st.columns(
        [4, 1.5],
        vertical_alignment="center",
    )

    with ordering:
        st.header("Your Order")
    with back:
        makrdown_options()
        if st.button("Back Ordering", key = "back_ordering", width="stretch"):
            st.session_state.tracker.reject_changes()
            st.switch_page("client/client_order.py")

    if len(st.session_state.tracker.list_orders()) > 0:
        for order in st.session_state.tracker.list_orders():
            ordered_food_name = order.get_food_name()
            with st.container(border=True):
                details, action = st.columns([4, 1], vertical_alignment="center")
                with details:
                    st.markdown(f"**{ordered_food_name}**")
                    if order.get_food_unit() != "":
                        st.caption(
                            f"Ordered Amount: {order.get_order_amount()} {order.get_food_unit()}"
                        )
                    else:
                        st.caption(
                            f"Ordered Amount: {order.get_order_amount()}"
                        )
                    tags = order.get_food_tags()
                    st.caption(f"Tags: {', '.join(str(tag) for tag in tags) if tags else '-'}")
                with action:
                    if st.button(
                        "Remove",
                        key=f"client_remove_food_{order.get_food_id()}",
                        width="stretch",
                    ):
                        st.session_state.order_quantity.pop(ordered_food_name, None)
                        st.session_state.tracker.remove_food_from_order(order.get_food_name())
                        st.rerun()
                    if st.button(
                        "Reduce",
                        key=f"client_reduce_food_{order.get_food_id()}",
                        width="stretch",
                    ):
                        current_amount = order.get_order_amount()
                        if current_amount <= 1:
                            st.session_state.order_quantity.pop(ordered_food_name, None)
                            st.session_state.tracker.remove_food_from_order(ordered_food_name)
                        else:
                            st.session_state.order_quantity[ordered_food_name] = current_amount - 1
                            st.session_state.tracker.update_food_order(
                                ordered_food_name,
                                current_amount - 1,
                            )
                        st.rerun()

        if st.button("Check Order"):
            try:
                changed, original = st.session_state.tracker.finish_food_order()
                st.session_state.order = changed
                st.session_state.original_order = original
                st.session_state.show_substitution = True
            except OrderNotFound as e:
                st.warning(str(e))

        if st.session_state.show_substitution:
            show_food_substitution()
        
    else:
        st.info("No items added yet in the cart.")



def show_food_substitution() -> None:
    for aorder in st.session_state.order:
        ordered_food_name = aorder.get_food_name()
        with st.container(border=True):
            details, action = st.columns([4, 1], vertical_alignment="center")
            with details:
                st.markdown(f"**{ordered_food_name}**")
                if aorder.get_food_unit() != "":
                    st.caption(
                        f"Ordered Amount: {aorder.get_order_amount()} {aorder.get_food_unit()}"
                    )
                else:
                    st.caption(
                        f"Ordered Amount: {aorder.get_order_amount()}"
                    )
                tags = aorder.get_food_tags()
                st.caption(f"Tags: {', '.join(str(tag) for tag in tags) if tags else '-'}")

    if len(st.session_state.order) > 0:
        accept, reject = st.columns([2, 1.4], vertical_alignment="bottom")

        with accept:
            if st.button("Submit Changed Order"):
                try:
                    st.session_state.tracker.accept_orders(st.session_state.tracker.finish_food_order()[0])
                    st.session_state.tracker.save_data()
                    st.balloons()
                    st.success("Order submitted")
                    st.session_state.tracker.start_new_order()
                    st.session_state.order_quantity = {}
                    st.session_state.show_substitution = False
                except (OrderNotFound, OSError, ValueError) as e:
                    st.warning(str(e))

        with reject:
            if st.button("Submit Original Order"):
                try:
                    st.session_state.tracker.accept_orders(st.session_state.tracker.finish_food_order()[1])
                    st.session_state.tracker.save_data()
                    st.balloons()
                    st.success("Order submitted")
                    st.session_state.tracker.start_new_order()
                    st.session_state.order_quantity = {}
                    st.session_state.show_substitution = False
                except (OrderNotFound, OSError, ValueError) as e:
                    st.warning(str(e))



if __name__ == "__main__":
    show_client_order_page()