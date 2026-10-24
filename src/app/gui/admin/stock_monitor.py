"""Admin inventory monitoring and stock controls."""

import logging
import math
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from app.food.food_item import FoodItem
from app.food.inventory import Inventory
from app.gui.admin.audit_log import (
    log_action,
    save_admin_changes,
    show_admin_change_message,
)
from app.gui.shared.toolbar import require_role, show_toolbar
from app.users.user import UserAccess

log: logging.Logger = logging.getLogger(__name__)


def get_inventory_manager() -> Inventory:
    if "inventory_manager" not in st.session_state:
        project_root = Path(__file__).resolve().parents[4]
        inventory_path = project_root / "assets" / "inventory.json"
        st.session_state.inventory_manager = Inventory(str(inventory_path))
    return st.session_state.inventory_manager


def _inventory_manager(inventory: Inventory | None = None) -> Inventory:
    return inventory if inventory is not None else get_inventory_manager()


def get_stock_levels(
    inventory: Inventory | None = None,
) -> dict[str, int | float]:
    return {
        food.get_food_name(): food.get_food_stocks()
        for food in _inventory_manager(inventory).get_inventory()
    }


def check_low_stock(
    item: str,
    threshold: int | float = 10,
    inventory: Inventory | None = None,
) -> bool:
    validate_threshold(threshold)
    return get_stock_levels(inventory).get(item, 0) < threshold


def set_threshold(
    item_id: int | str,
    threshold: int | float,
    inventory: Inventory | None = None,
) -> None:
    validate_threshold(threshold)
    _inventory_manager(inventory).set_minimum_stock(item_id, threshold)


def get_low_stock_alerts(
    inventory: Inventory | None = None,
) -> list[FoodItem]:
    return _inventory_manager(inventory).get_low_stock_foods()


def get_expiry_alerts(
    inventory: Inventory | None = None,
    today=None,
) -> list[FoodItem]:
    return _inventory_manager(inventory).get_expired_foods(today)


def validate_threshold(value: int | float) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or (isinstance(value, float) and not math.isfinite(value))
        or value < 0
    ):
        raise ValueError("Threshold must be a non-negative number.")


def generate_low_stock_alert(
    item_id: str,
    current_stock: int | float,
    threshold: int | float,
) -> str:
    return (
        f"Alert: {item_id} stock is low. Current stock: "
        f"{current_stock}, Threshold: {threshold}."
    )


def adjust_stock(
    item_id: int | str,
    delta: int | float,
    reason: str,
    inventory: Inventory | None = None,
) -> bool:
    manager = _inventory_manager(inventory)
    food: FoodItem | None = manager.find_food_by_id(item_id)
    if food is None:
        raise ValueError(f"Food ID {item_id} not found.")
    if isinstance(delta, bool) or not isinstance(delta, (int, float)) or delta == 0:
        raise ValueError("Stock adjustment must be a non-zero number.")
    return manager.adjust_stock(
        food_id=item_id,
        new_quantity=food.get_food_stocks() + delta,
        reason=reason,
    )


def manage_food_category(
    action: str,
    category: str | None = None,
    inventory: Inventory | None = None,
) -> list[str]:
    manager = _inventory_manager(inventory)
    categories = sorted({food.get_food_category() for food in manager.get_inventory()})
    if action == "list":
        return categories
    raise ValueError("Food categories are maintained when editing inventory items.")


def update_item_info(
    item_id: int | str,
    fields: dict[str, Any],
    inventory: Inventory | None = None,
) -> FoodItem:
    return _inventory_manager(inventory).update_food_from_inventory(
        item_id,
        **fields,
    )


def monitor_stock(
    inventory: Inventory | None = None,
) -> dict[str, Any]:
    manager = _inventory_manager(inventory)
    foods = manager.get_inventory()
    low_stock = get_low_stock_alerts(manager)
    expired_foods = get_expiry_alerts(manager)
    return {
        "foods": foods,
        "low_stock": low_stock,
        "expired_foods": expired_foods,
    }


def show_stock_monitor_page() -> None:
    require_role(UserAccess.ADMIN)
    show_toolbar()
    show_admin_change_message()
    inventory = get_inventory_manager()
    snapshot = monitor_stock(inventory)
    foods: list[FoodItem] = snapshot["foods"]

    st.title("Stock Management")
    st.caption(
        "Review inventory totals, configure alerts, and record adjustments. "
        "Expiry alerts flag items that have passed their recorded expiry date."
    )
    total_stock: int | float = sum(food.get_food_stocks() for food in foods)
    metric_columns = st.columns(4)
    metric_columns[0].metric("Food items", len(foods))
    metric_columns[1].metric("Total stock", f"{total_stock:g}")
    metric_columns[2].metric("Low stock", len(snapshot["low_stock"]))
    metric_columns[3].metric("Expired food", len(snapshot["expired_foods"]))

    if foods:
        rows = [
            {
                "ID": food.get_food_id(),
                "Food": food.get_food_name(),
                "Category": food.get_food_category(),
                "Stock": food.get_food_stocks(),
                "Unit": food.get_food_unit(),
                "Minimum": inventory.get_minimum_stock(food.get_food_id()),
            }
            for food in foods
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("No inventory items are configured.")

    low_stock: list[FoodItem] = snapshot["low_stock"]
    if low_stock:
        st.subheader("Below minimum stock")
        for food in low_stock:
            threshold = inventory.get_minimum_stock(food.get_food_id())
            st.warning(
                generate_low_stock_alert(
                    food.get_food_name(),
                    food.get_food_stocks(),
                    threshold if threshold is not None else 0,
                )
            )

    expired_foods: list[FoodItem] = snapshot["expired_foods"]
    st.subheader("Expiry alerts")
    if expired_foods:
        for food in expired_foods:
            st.error(
                f"{food.get_food_name()} expired on "
                f"{food.get_food_expiry_date()}."
            )
    else:
        st.success("No expired food items.")

    if not foods:
        return

    food_options: dict[str, int | str] = {
        f"{food.get_food_name()} (ID {food.get_food_id()})": food.get_food_id()
        for food in foods
    }
    st.divider()
    st.subheader("Stock controls")
    selected_label = st.selectbox("Food item", list(food_options))
    food_id = food_options[selected_label]
    selected_item = inventory.find_food_by_id(food_id)
    if selected_item is None:
        st.error("Selected food item was not found. Refresh and try again.")
        return

    threshold_col, threshold_action_col = st.columns([2, 1])
    with threshold_col:
        current_threshold = inventory.get_minimum_stock(food_id)
        threshold = st.number_input(
            "Minimum stock threshold",
            min_value=0.0,
            value=float(current_threshold if current_threshold is not None else 0),
            step=1.0,
            key=f"admin_threshold_{food_id}",
        )
    with threshold_action_col:
        with st.form("admin_threshold_update"):
            confirm_threshold = st.checkbox(
                f"Confirm setting the minimum stock threshold to {threshold:g}."
            )
            threshold_submitted = st.form_submit_button(
                "Save threshold",
                disabled=not confirm_threshold,
            )
        if threshold_submitted:
            try:
                set_threshold(food_id, threshold, inventory)
            except (TypeError, ValueError, OSError) as exc:
                st.error(str(exc))
            else:
                admin_account = st.session_state.account
                log_action(
                    str(admin_account.get("_account_number", "unknown")),
                    "stock_threshold_updated",
                    f"food_id={food_id}; threshold={threshold:g}",
                    actor_role=str(st.session_state.get("user_role", "Admin")),
                    record_type="inventory_threshold",
                    record_id=str(food_id),
                )
                save_admin_changes("Minimum stock threshold saved.")

    st.subheader("Update food details")
    with st.form("admin_update_food_details"):
        updated_name = st.text_input("Food name", value=selected_item.get_food_name())
        updated_category = st.text_input(
            "Category",
            value=selected_item.get_food_category(),
        )
        updated_unit = st.text_input("Unit", value=selected_item.get_food_unit())
        current_tags = [
            str(tag)
            for tag in selected_item.get_food_tags()
            if tag not in (None, "")
        ]
        updated_tags = st.text_input(
            "Tags (comma-separated)",
            value=", ".join(current_tags),
        )
        current_expiry = selected_item.get_food_expiry_date() or ""
        updated_expiry = st.text_input(
            "Expiry date (YYYY-MM-DD; optional)",
            value=current_expiry,
        )
        confirm_details = st.checkbox("Confirm updating these food details.")
        details_submitted = st.form_submit_button(
            "Update food details",
            disabled=not confirm_details,
        )
    if details_submitted:
        try:
            update_item_info(
                food_id,
                {
                    "name": updated_name,
                    "category": updated_category,
                    "unit": updated_unit,
                    "tags": [
                        tag.strip()
                        for tag in updated_tags.split(",")
                        if tag.strip()
                    ],
                    "expiry_date": updated_expiry.strip() or None,
                },
                inventory,
            )
        except (TypeError, ValueError, OSError) as exc:
            st.error(str(exc))
        else:
            admin_account = st.session_state.account
            log_action(
                str(admin_account.get("_account_number", "unknown")),
                "food_item_updated",
                f"food_id={food_id}",
                actor_role=str(st.session_state.get("user_role", "Admin")),
                record_type="inventory_item",
                record_id=str(food_id),
            )
            save_admin_changes("Food details updated.")

    with st.form("admin_stock_adjustment"):
        adjustment_direction = st.selectbox(
            "Adjustment",
            ("Increase stock", "Decrease stock"),
        )
        quantity = st.number_input(
            "Quantity",
            min_value=0.1,
            value=1.0,
            step=1.0,
        )
        reason = st.text_input("Reason")
        submitted = st.form_submit_button("Record adjustment")

    if submitted:
        delta = quantity if adjustment_direction == "Increase stock" else -quantity
        try:
            if not reason.strip():
                raise ValueError("Enter a reason for the stock adjustment.")
            adjust_stock(
                food_id,
                delta,
                reason.strip(),
                inventory,
            )
        except (TypeError, ValueError, OSError) as exc:
            st.error(str(exc))
        else:
            log.info(
                "Admin adjusted inventory: food_id=%s delta=%s reason=%s",
                food_id,
                delta,
                reason.strip(),
            )
            admin_account = st.session_state.account
            log_action(
                str(admin_account.get("_account_number", "unknown")),
                "stock_adjusted",
                f"food_id={food_id}; delta={delta:g}; reason={reason.strip()}",
                actor_role=str(st.session_state.get("user_role", "Admin")),
                record_type="inventory_stock",
                record_id=str(food_id),
            )
            save_admin_changes("Stock adjustment recorded.")


if __name__ == "__main__":
    show_stock_monitor_page()
