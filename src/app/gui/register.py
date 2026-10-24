# gui/register.py
import streamlit as st
from app.auth.account_manager import AccountManager, MIN_PASSWORD_LENGTH
from app.gui.header import show_header
from app.gui.style import markdown_button
from app.users.profile_validation import MAX_ADDRESS_LENGTH, validate_client_address

from app.users.constraint import *

# Check input fields for registration
def check_input(
    name: str,
    number: str,
    password: str,
    verify: str,
) -> tuple[bool, list[tuple[str, str]]]:
    name = name.strip()
    number = number.strip()
    feedback: list[tuple[str, str]] = []

    if not name or not number or not password or not verify:
        feedback.append(("warning", "Complete all fields."))
        return False, feedback

    if not name.replace(" ", "").isalpha() or len(name) < 2:
        feedback.append(("error", "Invalid name. Use letters and spaces only."))

    if not number.isdigit() or len(number) < 10:
        feedback.append(("error", "Invalid phone number. Enter at least 10 digits."))

    if password != verify:
        feedback.append(("error", "Passwords do not match."))
    if len(password) < MIN_PASSWORD_LENGTH:
        feedback.append(
            ("error", f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        )

    return not feedback, feedback

# Show the registration page with input fields for user information
def show_register_page(account_manager: AccountManager) -> None:
    show_header("register")
    selected_role = st.session_state.get("selected_role", "Client")

    st.header(f"Register as {selected_role}")
    name: str = st.text_input("Personal Information", placeholder="Name")

    country_col, contact_col = st.columns([1, 4])
    country_codes = ["+60", "+1", "+44", "+61", "+65"]
    with country_col:
        country_code = st.selectbox(
            "Country code",
            country_codes,
            index=country_codes.index("+60"),
            label_visibility="collapsed")

    with contact_col:
        number = st.text_input(
            "Contact number",
            placeholder="Phone Number",
            label_visibility="collapsed")

    password: str = st.text_input("Password", type="password")
    verify: str = st.text_input("Verify Password", type="password")

    additional_information: dict[str, list | str] = {}

    match selected_role:
        case "Client":
            food_constraints = st.multiselect(
                label="Select food constraints",
                options=[
                    constraint
                    for constraint_group in (*HARD_CONSTRAINTS, SOFT_CONSTRAINTS)
                    for constraint in constraint_group
                ],
                format_func=lambda constraint: constraint.value.replace("_", " ").title(),
            )
            address = st.text_input(
                "Address",
                placeholder="Please enter your address",
                max_chars=MAX_ADDRESS_LENGTH,
            )
            additional_information['food_constraints'] = food_constraints
            additional_information['address'] = address
    
    for level, message in st.session_state.pop("register_feedback", []):
        getattr(st, level)(message)

    with st.container(horizontal=True):
        markdown_button()
        if st.button("Register", key="register_account"):
            valid, feedback = check_input(name, number, password, verify)
            if valid and selected_role == "Client":
                try:
                    additional_information["address"] = validate_client_address(
                        additional_information.get("address", "")
                    )
                except ValueError as error:
                    valid = False
                    feedback.append(("error", str(error)))
            if valid:
                phone_number = country_code + '-' + str(number)
                account_number: str = account_manager.create_account(
                    name, phone_number, password, selected_role, **additional_information)
                feedback = [
                    ("info", f"Account Number: {account_number}"),
                    ("success", "Account registered."),
                ]
            st.session_state["register_feedback"] = feedback
            st.rerun()

        if st.button("Direct login", key="to_login"):
            st.switch_page("login.py")

if __name__ == "__main__":
    show_register_page(st.session_state.account_manager)