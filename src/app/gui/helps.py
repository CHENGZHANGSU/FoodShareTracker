# gui/helps.py
import streamlit as st
from app.gui.style import apply_app_style, markdown_help_links
from app.users.user import UserAccess

def show_helps_page() -> None:
    apply_app_style()
    st.title("Help & getting started")
    st.write(
        "Use the top menu to open Home, About, or Resources. Choose Helps at any "
        "time to return to this guide."
    )
    dashboard_by_role = {
        UserAccess.CLIENT: (
            "Client dashboard",
            "client/client_dashboard.py",
            "Clients",
            """
            - Browse available food from your dashboard.
            - Choose **Start Ordering** to add items, then review your current order.
            - Open **History** to review previous orders.
            - Add your food constraints and address under **Profile**.
            """,
        ),
        UserAccess.DONOR: (
            "Donor dashboard",
            "donor/donor_dashboard.py",
            "Donors",
            """
            - Register a donation with its food name, quantity, expiry date, and drop-off date and time.
            - Review donation history and check each donation's status.
            - Update the drop-off date or time, or cancel a donation while it is pending.
            - Check notifications for registration, schedule changes, and cancellations; mark them as read.
            - Download a receipt once a donation has been accepted.
            """,
        ),
        UserAccess.STAFF: (
            "Staff dashboard",
            "staff/staff_dashboard.py",
            "Food bank staff",
            """
            - Review and process requests using **Pending Orders** and **Order Details**.
            - Record incoming supplies in **Receive Stock**.
            - Use **Inventory Management**, **Adjust Stock**, and **Food Catalogue** to maintain stock information.
            """,
        ),
        UserAccess.ADMIN: (
            "Admin dashboard",
            "admin/admin_dashboard.py",
            "Admin staff",
            """
            - Use **User Management** to create accounts, review users, change roles, reset passwords, and control access.
            - Use **Stock Management** to review stock, expiry alerts, thresholds, and adjustments.
            - Use **Audit Log** to filter account, inventory, and sensitive-record activity.
            - Use **Reports & Data** to export reports, merge inventory JSON, or create a backup.
            """,
        ),
    }
    authenticated = st.session_state.get("authenticated", False)
    role = st.session_state.get("user_role")
    role_help = dashboard_by_role.get(role) if authenticated else None
    if not authenticated:
        st.info("Sign in to view help for your role and open its dashboard.")
    elif role_help is None:
        st.warning("Your account role is not recognised. Please contact an administrator.")

    st.subheader("Return to page")
    if role_help is not None or not authenticated:
        markdown_help_links()
        dashboard_col, home_col = st.columns(
            [1, 1],
            vertical_alignment="center",
            gap="small",
        )
        with dashboard_col:
            if role_help is not None:
                if st.button(
                    f"Open {role_help[0]}",
                    key="help_dashboard_link",
                    width="stretch",
                ):
                    st.switch_page(role_help[1])
            else:
                if st.button("Login", key="help_dashboard_login", width="stretch"):
                    st.switch_page("login.py")
        with home_col:
            if st.button("Home", key="home_page", width="stretch"):
                st.session_state["home_section"] = "home"
                st.switch_page("home.py")

    st.subheader("For new users")
    st.markdown(
        """
        - Register with your name, phone number, and a password, then keep your account number.
        - Sign in with your account number, password, and the role you registered with.
        - Your account is temporarily locked after five incorrect password attempts.
        - Change your password or update your details from **Profile**.
        """
    )

    if role_help is not None:
        st.subheader(role_help[2])
        st.markdown(role_help[3])
    elif not authenticated:
        st.subheader("Role-specific help")
        st.write(
            "Client, donor, food bank staff, and admin guidance is shown after you sign in."
        )
if __name__ == "__main__":
    show_helps_page()