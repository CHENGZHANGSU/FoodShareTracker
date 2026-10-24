import json
import os
import pandas as pd
import streamlit as st
from datetime import date, datetime

from app.auth.account_manager import AccountManager
from app.gui.shared.toolbar import show_toolbar, require_role
from app.gui.style import show_dashboard_header
from app.users.user import UserAccess


NOTIFICATION_FILE = "assets/donor_notifications.json"
SLOTS = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]


def load_notifications():
    if not os.path.exists(NOTIFICATION_FILE):
        return []

    try:
        with open(NOTIFICATION_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Donor notification file contains invalid JSON: {NOTIFICATION_FILE}"
        ) from exc

    if not isinstance(data, list) or any(
        not isinstance(notification, dict) for notification in data
    ):
        raise ValueError(
            f"Donor notification file must contain a list of objects: "
            f"{NOTIFICATION_FILE}"
        )
    return data


def save_notifications(notifications):
    os.makedirs("assets", exist_ok=True)

    with open(NOTIFICATION_FILE, "w", encoding="utf-8") as file:
        json.dump(notifications, file, indent=4)


def add_notification(donor_id, message):
    notifications = load_notifications()

    notifications.append({
        "donor_id": str(donor_id),
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "read": False
    })

    save_notifications(notifications)


def show_donor_dashboard(section="Dashboard") -> None:
    require_role(UserAccess.DONOR)
    show_toolbar()

    account = st.session_state.account
    donor = st.session_state.current_user
    donor_id = account["_account_number"]

    manager = AccountManager()
    saved_account = manager.find_account(donor_id, "Donor")

    if saved_account is None:
        st.error("Donor account could not be found.")
        st.stop()

    def save_records():
        records = donor.get_donation_rec()
        saved_account["_donation_rec"] = records
        manager.save_data()
        account["_donation_rec"] = records

    # Donor pages share the same account and persistence logic.
    if section == "Dashboard":
        show_dashboard_header("FoodShare Donor Dashboard", "Donor")
    else:
        st.title(section)

    donations = donor.get_donation_rec()
    if section == "Dashboard":
        st.metric("Recorded Donations", len(donations))
        st.info("Use the sidebar to register donations, view history, manage donations, or check notifications.")

    if section == "Donation History":
        st.subheader("Donation History")

        if not donations:
            st.info("No donation records are available for your account.")

        rows = [
            {
                "Donation ID": record.get("id", "-"),
                "Date": record.get("timestamp", "").split("T")[0],
                "Items": len(record.get("donation", []))
            }
            for record in donations
        ]

        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

        for record in donations:
            with st.expander(f"Donation {record.get('id', '-')}"):
                st.dataframe(
                    record.get("donation", []),
                    column_config={
                        "food_name": st.column_config.TextColumn("Food Name"),
                        "quantity": st.column_config.NumberColumn("Quantity"),
                        "expiry_date": st.column_config.TextColumn("Expiry Date"),
                        "drop_off_date": st.column_config.TextColumn("Drop-off Date"),
                        "drop_off_time": st.column_config.TextColumn("Drop-off Time"),
                        "status": st.column_config.TextColumn("Status"),
                    },
                )

    if section == "Register Donation":
        # Register donation
        st.subheader("Register Donation")

        if st.session_state.pop("donation_success", False):
            st.success("Donation registered successfully!")

        with st.form("donation_form"):
            food_name = st.text_input("Food Name")
            category = st.selectbox(
                "Category",
                ["Fruit", "Vegetables", "Meat", "Seafood", "Dairy",
                 "Grains", "Canned Food", "Other"]
            )
            unit = st.selectbox(
                "Unit", ["kg", "g", "pieces", "litres", "packs", "boxes"]
            )
            dietary_tags = st.multiselect(
                "Food Tags / Dietary Information (optional)",
                ["Halal", "Kosher", "Vegetarian", "Vegan", "Nut-Free",
                 "Lactose-Free", "Gluten-Free", "Suitable for Diabetes",
                 "Low Cholesterol", "Spicy"]
            )
            quantity = st.number_input(
                "Quantity",
                min_value=1,
                step=1
            )

            expiry_date = st.date_input(
                "Expiry Date",
                min_value=date.today()
            )

            drop_off_date = st.date_input(
                "Drop-off Date",
                min_value=date.today()
            )

            drop_off_time = st.selectbox(
                "Drop-off Time",
                SLOTS
            )

            submitted = st.form_submit_button("Submit Donation")

        if submitted:
            if drop_off_date > expiry_date:
                st.error(
                    "Drop-off date cannot be after the expiry date."
                )

            elif not food_name.strip():
                st.error("Please enter a food name.")

            else:
                # Find the next ID across all donor accounts.
                all_ids = []

                for donor_account in manager._accounts.get("Donor", []):
                    for record in donor_account.get("_donation_rec", []):
                        if "id" in record:
                            all_ids.append(int(record["id"]))

                donation_id = max(all_ids, default=0) + 1

                item = {
                    "food_name": food_name.strip(),
                    "category": category,
                    "unit": unit,
                    "food_tag": dietary_tags,
                    "quantity": int(quantity),
                    "expiry_date": str(expiry_date),
                    "drop_off_date": str(drop_off_date),
                    "drop_off_time": drop_off_time,
                    "status": "Pending"
                }

                try:
                    donor.add_donation_record(donation_id, [item])
                    save_records()

                    add_notification(
                        donor_id,
                        f"Donation {donation_id} has been registered."
                    )

                    st.session_state["donation_success"] = True
                    st.rerun()

                except ValueError as error:
                    st.error(str(error))

    if section == "Manage Donations":
        # Manage donations
        st.subheader("Manage Donations")

        for record in donor.get_donation_rec():
            items = record.get("donation", [])

            if not items:
                continue

            item = items[0]
            donation_id = int(record["id"])

            st.write(
                f"Donation {donation_id}: "
                f"{item.get('food_name', 'Food')} - "
                f"{item.get('status', 'Unknown')}"
            )

            if item.get("status") == "Pending":
                expiry = date.fromisoformat(item["expiry_date"])

                if expiry < date.today():
                    st.warning(
                        "This donation has expired and cannot be rescheduled."
                    )
                else:
                    saved_date = date.fromisoformat(
                        item.get("drop_off_date", str(date.today()))
                    )

                    if saved_date < date.today():
                        saved_date = date.today()

                    with st.form(f"manage_{donation_id}"):
                        new_date = st.date_input(
                            "Change Drop-off Date",
                            value=saved_date,
                            min_value=date.today(),
                            max_value=expiry,
                            key=f"date_{donation_id}"
                        )

                        current_time = item.get("drop_off_time", "09:00")

                        time_index = (
                            SLOTS.index(current_time)
                            if current_time in SLOTS
                            else 0
                        )

                        new_time = st.selectbox(
                            "Change Drop-off Time",
                            SLOTS,
                            index=time_index,
                            key=f"time_{donation_id}"
                        )

                        update = st.form_submit_button("Update Donation")
                        cancel = st.form_submit_button("Cancel Donation")

                    if update:
                        if donor.update_drop_off(
                            donation_id,
                            str(new_date),
                            new_time
                        ):
                            save_records()

                            add_notification(
                                donor_id,
                                f"Drop-off for donation {donation_id} "
                                "has been updated."
                            )

                            st.success("Drop-off updated!")
                            st.rerun()
                        else:
                            st.error("Invalid drop-off date or time.")

                    if cancel:
                        if donor.cancel_donation(donation_id):
                            save_records()

                            add_notification(
                                donor_id,
                                f"Donation {donation_id} has been cancelled."
                            )

                            st.success("Donation cancelled!")
                            st.rerun()

            # Receipt is available only after acceptance.
            if item.get("status") == "Accepted":
                receipt = (
                    "Donation Receipt\n"
                    f"Donation ID: {donation_id}\n"
                    f"Food: {item.get('food_name', '')}\n"
                    f"Quantity: {item.get('quantity', '')}\n"
                    f"Drop-off Date: {item.get('drop_off_date', '')}\n"
                    "Status: Accepted\n"
                )

                st.download_button(
                    "Download Receipt",
                    receipt,
                    file_name=f"donation_{donation_id}_receipt.txt",
                    key=f"receipt_{donation_id}"
                )

            st.divider()

    if section == "Notifications":
        # Persistent donor notifications
        st.subheader("Notifications")

        notifications = load_notifications()
        my_notifications = []

        for index, notification in enumerate(notifications):
            if str(notification.get("donor_id")) == str(donor_id):
                my_notifications.append((index, notification))

        if not my_notifications:
            st.info("No notifications yet.")

        for index, notification in reversed(my_notifications):
            message = notification.get("message", "")

            if notification.get("read", False):
                st.write("Read: " + message)

            else:
                st.info("New: " + message)

                if st.button(
                    "Mark as Read",
                    key=f"read_notification_{index}"
                ):
                    notifications[index]["read"] = True
                    save_notifications(notifications)
                    st.rerun()


if __name__ == "__main__":
    show_donor_dashboard()