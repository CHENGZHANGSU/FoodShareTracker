# gui/header.py
import streamlit as st
from app.gui.style import (
    apply_app_style,
    markdown_logo,
    markdown_nav,
    markdown_button,
)

def show_header(current_page: str) -> None:
    apply_app_style()
    # Header
    logo_left, nav_col, button_col = st.columns([1, 5, 1], vertical_alignment="center")
    with logo_left:
        markdown_logo()
    with nav_col:
        markdown_nav(st.session_state.get("home_section", "home"))
        with st.container(horizontal=True, horizontal_alignment="center"):
            for section in ["Home", "About", "Resources"]:
                if st.button(section, key=f"nav_{section}_{current_page}"):
                    st.session_state["home_section"] = section.lower()
                    if current_page == "home":
                        st.rerun()
                    st.switch_page("home.py")
    with button_col:
        markdown_button()
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Helps", key="helps_page"):
                st.switch_page("helps.py")
    st.divider()