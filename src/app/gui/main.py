# gui/main.py
import streamlit as st

from app.auth.account_manager import AccountManager
from app.users.user import UserAccess
from app.users.client import Client
from app.users.donor import Donor
from app.users.staff import Staff
from app.users.admin import Admin
from app.users.constraint import HARD_CONSTRAINTS

from app.core.food_tracker_client import FoodShareTracker

from app.food.inventory import Inventory
from app.gui.style import apply_app_style
from util.admin_utils import init_logger, backup_data

# Get the shared inventory instance
def get_shared_inventory() -> Inventory:
    return Inventory()

# Main function to run the Streamlit app
def main() -> None:
    apply_app_style()

    if "account_manager" not in st.session_state:
        st.session_state.account_manager = AccountManager()

    if "init_logger" not in st.session_state:
        st.session_state.init_logger = init_logger()

    if "backup_data" not in st.session_state:
        st.session_state.backup_data = backup_data()
    if not st.session_state.backup_data:
        st.warning("Automatic data backup failed. Check the application log.")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user_role" not in st.session_state:
        st.session_state.user_role = UserAccess.CLIENT

    home = st.Page("home.py", title="Home", default=not st.session_state.authenticated)
    helps = st.Page("helps.py", title="Helps")
    login = st.Page("login.py", title="Login")
    register = st.Page("register.py", title="Register")

    if st.session_state.authenticated:
        # base page
        pages = [home, st.Page("shared/profile.py", title="Profile")]
        # add pages according to roles
        match st.session_state.user_role:
            case UserAccess.CLIENT:
                account = st.session_state.account
                constraints = {
                    item.value: item
                    for constraint_group in HARD_CONSTRAINTS
                    for item in constraint_group
                }
                client = Client(
                    account["_account_number"],
                    account["_account_password"],
                    account["_name"],
                    account["_phone_number"],
                    [
                        constraints.get(value, value)
                        for value in account.get("_food_constraints", [])
                    ],
                    account.get("_address"),
                    account.get("_food_orders_rec", []),
                )
                st.session_state.current_user = client
                if "tracker" not in st.session_state:
                    st.session_state.tracker = FoodShareTracker(
                        client,
                        account_manager=st.session_state.account_manager,
                    )

                client_pages = [
                    st.Page("client/client_dashboard.py", title="Dashboard", default=True),
                    st.Page("client/client_order.py", title="Start Ordering"),
                    st.Page("client/display_order.py", title="Current Order"),
                    st.Page(
                        "client/ready_for_collection.py",
                        title="Ready for Collection",
                    ),
                    st.Page("client/client_order_history.py", title="History")
                ]
                pages.extend(client_pages)

            case UserAccess.DONOR:
                account = st.session_state.account
                st.session_state.current_user = Donor(
                    account["_account_number"],
                    account["_account_password"],
                    account["_name"],
                    account["_phone_number"],
                    account.get("_donation_rec", []),
                )
                donor_pages = [
                    st.Page("donor/donor_dashboard.py", title="Dashboard", default=True),
                    st.Page("donor/register_donation.py", title="Register Donation"),
                    st.Page("donor/donation_history.py", title="Donation History"),
                    st.Page("donor/manage_donations.py", title="Manage Donations"),
                    st.Page("donor/donor_notifications.py", title="Notifications"),
                ]
                pages.extend(donor_pages)
                
            
            case UserAccess.STAFF:
                account = st.session_state.account
                st.session_state.current_user = Staff(
                    account["_account_number"],
                    account["_account_password"],
                    account["_name"],
                    account["_phone_number"],
                )
                staff_pages = [
                    st.Page("staff/staff_dashboard.py", title="Dashboard", default=True),
                    st.Page("staff/pending_orders.py", title="Pending Orders"),
                    st.Page("staff/client_preferences.py", title="Client Preferences"),
                    st.Page("staff/order_details.py", title="Order Details"),
                    st.Page("bank/inventory_management.py", title="Inventory Management"),
                    st.Page("staff/receive_stock.py", title="Receive Stock"),
                    st.Page("staff/food_catalogue.py", title="Food Catalogue"),
                    st.Page("staff/adjust_stock.py", title="Adjust Stock"),
                    st.Page("staff/pending_donations.py", title="Pending Donations"),
                ]
                pages.extend(staff_pages)


            case UserAccess.ADMIN:
                account = st.session_state.account
                st.session_state.current_user = Admin(
                    account["_account_number"],
                    account["_account_password"],
                    account["_name"],
                    account["_phone_number"],
                )
                admin_pages = [
                    st.Page("admin/admin_dashboard.py", title="Dashboard", default=True),
                    st.Page("admin/user_management.py", title="User Management"),
                    st.Page("admin/stock_monitor.py", title="Stock Management"),
                    st.Page("admin/audit_log.py", title="Audit Log"),
                    st.Page("admin/report_export.py", title="Reports & Data"),
                ]
                pages.extend(admin_pages)
    else:
        pages = [home, login, register]

    # help page as last
    pages.append(helps)
    st.navigation(pages).run()

if __name__ == "__main__":
    main()