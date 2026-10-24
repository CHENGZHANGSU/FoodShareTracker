# gui/home.py
import streamlit as st
from app.auth.account_manager import AccountManager
from app.gui.header import show_header
from app.gui.style import markdown_header, markdown_image, markdown_section, markdown_bar

def prompt_account() -> None:
    header, image = st.columns([1, 1], vertical_alignment="center")
    with header:
        st.title("Login / Register")
        selected_role = st.selectbox(
            "Login / Register as", ["Client", "Donor", "Food Bank Staff", "Admin"]
        )
        login, register = st.columns([1, 1], gap="small")
        markdown_header()
        with login:
            if st.button("Register", key="register"):
                st.session_state["selected_role"] = selected_role
                st.switch_page("register.py")
        with register:
            if st.button("Login", key="login"):
                st.session_state["selected_role"] = selected_role
                st.switch_page("login.py")
    with image:
        markdown_image()
    st.divider()

def show_home_page(account_manager: AccountManager) -> None:
    show_header("home")
    section = st.session_state.get("home_section", "home")
    if section not in {"home", "about", "resources"}:
        section = "home"

    if section == "home":
        if not st.session_state.authenticated:
            prompt_account()
        markdown_section()
        st.write(
            "FoodShare Tracker helps local food banks and community organisations "
            "share available food with people who need it."
        )
    elif section == "about":
        picture, about = st.columns([1, 1], vertical_alignment="center")
        with picture:
            markdown_image()
        with about:
            st.subheader("About FoodShare Tracker")
            st.write(
                "FoodShare Tracker connects local food banks, charities, and support "
                "organisations with the people they serve. It supports safe, respectful "
                "food sharing while treating every client with dignity and protecting "
                "their privacy."
            )
            st.write(
                "By keeping food and order information organised, the service helps "
                "communities reduce food waste and direct available supplies where "
                "they are needed."
            )
    else:
        st.subheader("Resources")
        st.write("Choose the guide that matches how you use FoodShare Tracker.")
        client_col, donor_col = st.columns(2)
        with client_col:
            with st.container(border=True):
                st.markdown("#### Clients")
                st.write(
                    "Find food that fits your preferences, place orders, and follow collection updates. "
                    "Review order history and update your profile."
                )
        with donor_col:
            with st.container(border=True):
                st.markdown("#### Donors")
                st.write(
                    "Register donations and manage pending drop-offs. Track donation "
                    "status and download receipts for accepted donations."
                )
        staff_col, admin_col = st.columns(2)
        with staff_col:
            with st.container(border=True):
                st.markdown("#### Food bank staff")
                st.write(
                    "Review requests, prepare hampers, and confirm handovers. Maintain "
                    "the food catalogue and stock."
                )
        with admin_col:
            with st.container(border=True):
                st.markdown("#### Admin staff")
                st.write(
                    "Manage accounts, monitor stock alerts, and review audit logs. "
                    "Export reports, import inventory, and create backups."
                )

    st.divider()
    markdown_bar()
    
if __name__ == "__main__":
    if "account_manager" not in st.session_state:
        st.session_state.account_manager = AccountManager()
    show_home_page(st.session_state.account_manager)