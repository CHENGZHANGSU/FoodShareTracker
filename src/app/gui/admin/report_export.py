"""Admin reports, CSV/JSON export, inventory import, and backup actions."""

import csv
import io
import json
import math
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from app.food.food_item import FoodItem
from app.food.inventory import Inventory


def _project_root(project_root: Path | None = None) -> Path:
    return project_root or Path(__file__).resolve().parents[4]


def _validate_date_range(date_range: tuple[date, date]) -> tuple[date, date]:
    if (
        not isinstance(date_range, tuple)
        or len(date_range) != 2
        or not all(type(value) is date for value in date_range)
    ):
        raise ValueError("Select a valid start and end date.")
    date_from, date_to = date_range
    if date_from > date_to:
        raise ValueError("The start date must be on or before the end date.")
    return date_from, date_to


def _inventory_export(inventory: Inventory) -> dict[str, Any]:
    foods = inventory.get_inventory()
    return {
        "inventory": [vars(food).copy() for food in foods],
        "next_food_id": inventory._id["next_food_id"],
        "minimum_stock": {
            str(food.get_food_id()): inventory.get_minimum_stock(food.get_food_id())
            for food in foods
            if inventory.get_minimum_stock(food.get_food_id()) is not None
        },
    }


def _order_report(
    orders_directory: Path,
    date_from: date,
    date_to: date,
) -> list[dict[str, Any]]:
    totals: dict[tuple[str, str, str, str], float] = {}
    if not orders_directory.exists():
        return []
    for orders_file in sorted(orders_directory.glob("*_orders.json")):
        try:
            order_date = date.fromisoformat(orders_file.name[:10])
        except ValueError:
            continue
        if not date_from <= order_date <= date_to:
            continue
        try:
            with orders_file.open("r", encoding="utf-8") as file:
                clients = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Could not read {orders_file.name}: {exc}") from exc
        if not isinstance(clients, dict):
            raise ValueError(f"{orders_file.name} must contain an object.")
        for client_orders in clients.values():
            if not isinstance(client_orders, list):
                raise ValueError(f"Order records in {orders_file.name} must be lists.")
            for order in client_orders:
                if not isinstance(order, dict):
                    raise ValueError(f"Order rows in {orders_file.name} must be objects.")
                raw_quantity = order.get("_order_amount", 0)
                if isinstance(raw_quantity, bool):
                    raise ValueError(f"Invalid order quantity in {orders_file.name}.")
                try:
                    quantity = float(raw_quantity)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Invalid order quantity in {orders_file.name}."
                    ) from exc
                if not math.isfinite(quantity) or quantity < 0:
                    raise ValueError(
                        f"Invalid order quantity in {orders_file.name}."
                    )
                key = (
                    order_date.isoformat(),
                    str(order.get("_name", "Unknown food")),
                    str(order.get("_category", "Uncategorised")),
                    str(order.get("_unit", "")),
                )
                totals[key] = totals.get(key, 0) + quantity
    return [
        {
            "date": order_date,
            "food_name": food_name,
            "category": category,
            "quantity": quantity,
            "unit": unit,
        }
        for (order_date, food_name, category, unit), quantity
        in sorted(totals.items())
    ]


def _donation_report(
    account_path: Path,
    date_from: date,
    date_to: date,
) -> list[dict[str, Any]]:
    try:
        with account_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read account records: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("accounts"), dict):
        raise ValueError("Account data must contain an accounts object.")

    totals: dict[tuple[str, str, str], float] = {}
    donors = data["accounts"].get("Donor", [])
    if not isinstance(donors, list):
        raise ValueError("Donor account records must be a list.")
    for donor in donors:
        if not isinstance(donor, dict):
            raise ValueError("Donor account records must be objects.")
        donation_records = donor.get("_donation_rec", [])
        if not isinstance(donation_records, list):
            raise ValueError("Donation records must be a list.")
        for donation_record in donation_records:
            if not isinstance(donation_record, dict):
                raise ValueError("Donation records must be objects.")
            try:
                donated_at = datetime.fromisoformat(
                    str(donation_record.get("timestamp", ""))
                ).date()
            except ValueError as exc:
                raise ValueError("Invalid donation timestamp in account data.") from exc
            if not date_from <= donated_at <= date_to:
                continue
            donation_items = donation_record.get("donation", [])
            if not isinstance(donation_items, list):
                raise ValueError("Donation items must be a list.")
            for item in donation_items:
                if not isinstance(item, dict):
                    raise ValueError("Donation items must be objects.")
                raw_quantity = item.get("quantity", 0)
                if isinstance(raw_quantity, bool):
                    raise ValueError("Invalid donation quantity in account data.")
                try:
                    quantity = float(raw_quantity)
                except (TypeError, ValueError) as exc:
                    raise ValueError("Invalid donation quantity in account data.") from exc
                if not math.isfinite(quantity) or quantity < 0:
                    raise ValueError("Invalid donation quantity in account data.")
                key = (
                    donated_at.isoformat(),
                    str(item.get("food_name", "Unknown food")),
                    str(item.get("status", "Unknown")),
                )
                totals[key] = totals.get(key, 0) + quantity
    return [
        {
            "date": donated_at,
            "food_name": food_name,
            "status": status,
            "quantity": quantity,
        }
        for (donated_at, food_name, status), quantity in sorted(totals.items())
    ]


def generate_report(
    report_type: str,
    date_range: tuple[date, date],
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)
    if report_type == "inventory":
        inventory_path = root / "assets" / "inventory.json"
        if not inventory_path.is_file():
            raise FileNotFoundError(f"Inventory file not found: {inventory_path}")
        inventory = Inventory(str(inventory_path))
        return _inventory_export(inventory)

    date_from, date_to = _validate_date_range(date_range)
    if report_type == "order_demand":
        records = _order_report(
            root / "assets" / "orders",
            date_from,
            date_to,
        )
    elif report_type == "donations":
        records = _donation_report(
            root / "assets" / "account.json",
            date_from,
            date_to,
        )
    else:
        raise ValueError("Unsupported report type.")
    return {
        "report_type": report_type,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "records": records,
    }


def export_report(report: dict[str, Any], format: str) -> str:
    if not isinstance(report, dict):
        raise ValueError("Report must be an object.")
    normalized_format = format.lower()
    if normalized_format == "json":
        return json.dumps(report, indent=2, ensure_ascii=False)
    if normalized_format != "csv":
        raise ValueError("Unsupported export format.")

    records = report.get("inventory", report.get("records"))
    if not isinstance(records, list):
        raise ValueError("Report does not contain tabular records.")
    columns = list(dict.fromkeys(
        key for record in records if isinstance(record, dict) for key in record
    ))
    if not columns and "inventory" in report:
        columns = [
            "_id", "_name", "_category", "_stock", "_unit", "_tags",
            "_inDate", "_expiryDate",
        ]
    if not columns:
        columns = {
            "inventory": [
                "_id", "_name", "_category", "_stock", "_unit", "_tags",
                "_inDate", "_expiryDate",
            ],
            "order_demand": [
                "date", "food_name", "category", "quantity", "unit",
            ],
            "donations": ["date", "food_name", "status", "quantity"],
        }.get(str(report.get("report_type")), [])
    thresholds = report.get("minimum_stock", {})
    if "inventory" in report and "minimum_stock" not in columns:
        columns.append("minimum_stock")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Report rows must be objects.")
        row = {
            key: (
                json.dumps(value, ensure_ascii=False)
                if isinstance(value, (dict, list))
                else value
            )
            for key, value in record.items()
        }
        if "inventory" in report:
            row["minimum_stock"] = thresholds.get(str(record.get("_id")), "")
        writer.writerow(row)
    return output.getvalue()


def export_records(record_type: str, format: str) -> str:
    report = generate_report(
        record_type,
        (date.min, date.max),
    )
    return export_report(report, format)


def _read_upload(file: BinaryIO | TextIO | bytes | str) -> Any:
    try:
        if isinstance(file, bytes):
            content = file.decode("utf-8")
        elif isinstance(file, str):
            content = file
        else:
            raw = file.getvalue() if hasattr(file, "getvalue") else file.read()
            content = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError, OSError, TypeError) as exc:
        raise ValueError("Import file must contain valid UTF-8 JSON.") from exc


def _validate_inventory_import(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("inventory"), list):
        raise ValueError("Import JSON must contain an inventory list.")
    imported_foods = []
    seen_ids: set[int] = set()
    seen_names: set[str] = set()
    for index, item in enumerate(data["inventory"]):
        if not isinstance(item, dict):
            raise ValueError(f"Inventory item {index + 1} must be an object.")
        food_id = item.get("_id")
        name = item.get("_name")
        category = item.get("_category")
        if isinstance(food_id, bool) or not isinstance(food_id, int) or food_id < 1:
            raise ValueError(f"Inventory item {index + 1} has an invalid ID.")
        if food_id in seen_ids:
            raise ValueError(f"Duplicate food ID {food_id} in import.")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Inventory item {index + 1} has an invalid name.")
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"Inventory item {index + 1} has an invalid category.")
        normalized_name = name.strip().casefold()
        if normalized_name in seen_names:
            raise ValueError(f"Duplicate food name {name!r} in import.")
        seen_ids.add(food_id)
        seen_names.add(normalized_name)
        tags = item.get("_tags", [])
        if not isinstance(tags, list):
            raise ValueError(f"Tags for food ID {food_id} must be a list.")
        if any(tag is not None and not isinstance(tag, str) for tag in tags):
            raise ValueError(f"Tags for food ID {food_id} must be text values.")
        in_date = item.get("_inDate")
        if in_date is not None and not isinstance(in_date, str):
            raise ValueError(f"Received date for food ID {food_id} must be text.")
        unit = item.get("_unit", "")
        if not isinstance(unit, str):
            raise ValueError(f"Unit for food ID {food_id} must be text.")
        imported_foods.append(
            FoodItem(
                food_id,
                name.strip(),
                category.strip(),
                item.get("_stock", 0),
                unit,
                tags,
                in_date,
                item.get("_expiryDate"),
            )
        )

    minimum_stock = data.get("minimum_stock", {})
    if not isinstance(minimum_stock, dict):
        raise ValueError("Minimum stock thresholds must be an object.")
    thresholds: dict[str, int | float] = {}
    for food_id, threshold in minimum_stock.items():
        if str(food_id) not in {str(item_id) for item_id in seen_ids}:
            raise ValueError(f"Threshold references unknown food ID {food_id}.")
        if (
            isinstance(threshold, bool)
            or not isinstance(threshold, (int, float))
            or not math.isfinite(threshold)
            or threshold < 0
        ):
            raise ValueError(f"Threshold for food ID {food_id} is invalid.")
        thresholds[str(food_id)] = threshold
    return {
        "inventory": [vars(food).copy() for food in imported_foods],
        "minimum_stock": thresholds,
        "next_food_id": max(seen_ids, default=0) + 1,
    }


def import_records(
    file: BinaryIO | TextIO | bytes | str,
    format: str = "json",
) -> dict[str, Any]:
    if not isinstance(format, str):
        raise ValueError("Only JSON inventory imports are supported.")
    if format.lower() != "json":
        raise ValueError("Only JSON inventory imports are supported.")
    return _validate_inventory_import(_read_upload(file))


def merge_inventory_import(
    imported_data: dict[str, Any],
    inventory: Inventory,
) -> tuple[int, int]:
    imported = _validate_inventory_import(imported_data)
    current_items = {
        food.get_food_id(): vars(food).copy()
        for food in inventory.get_inventory()
    }
    added = 0
    updated = 0
    for item in imported["inventory"]:
        food_id = item["_id"]
        if food_id in current_items:
            updated += 1
        else:
            added += 1
        current_items[food_id] = item

    names: dict[str, int] = {}
    for food_id, item in current_items.items():
        name_key = item["_name"].strip().casefold()
        if name_key in names and names[name_key] != food_id:
            raise ValueError(
                f"Food name {item['_name']!r} conflicts with another food ID."
            )
        names[name_key] = food_id

    thresholds = {
        str(food.get_food_id()): inventory.get_minimum_stock(food.get_food_id())
        for food in inventory.get_inventory()
        if inventory.get_minimum_stock(food.get_food_id()) is not None
    }
    thresholds.update(imported["minimum_stock"])
    merged = {
        "inventory": list(current_items.values()),
        "next_food_id": max(
            imported["next_food_id"],
            max(current_items, default=0) + 1,
        ),
        "minimum_stock": thresholds,
    }

    path = Path(inventory._inventory_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(merged, file, indent=4, ensure_ascii=False)
        os.replace(temporary_path, path)
    except (OSError, TypeError, ValueError):
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise

    inventory.load_data()
    inventory.to_object()
    return added, updated


def _log_export(report_type: str) -> None:
    import streamlit as st

    from app.gui.admin.audit_log import log_action

    account = st.session_state.get("account", {})
    log_action(
        str(account.get("_account_number", "unknown")),
        "export",
        report_type,
        actor_role="Admin",
        record_type="admin_report",
        record_id=report_type,
    )


def show_report_export_page() -> None:
    import pandas as pd
    import streamlit as st

    from app.gui.admin.audit_log import (
        log_action,
        save_admin_changes,
        show_admin_change_message,
    )
    from app.gui.admin.stock_monitor import get_inventory_manager
    from app.gui.shared.toolbar import require_role, show_toolbar
    from app.users.user import UserAccess
    from util.admin_utils import backup_data

    require_role(UserAccess.ADMIN)
    show_toolbar()
    show_admin_change_message()
    st.title("Reports & Data")
    st.caption("Export operational reports, merge inventory data, or create a backup.")

    report_type = st.selectbox(
        "Report",
        ("Inventory", "Order demand", "Donations"),
    )
    report_key = {
        "Inventory": "inventory",
        "Order demand": "order_demand",
        "Donations": "donations",
    }[report_type]
    if report_key == "inventory":
        date_range = (date.min, date.max)
        st.caption("Inventory export contains the current inventory and thresholds.")
    else:
        date_col, end_col = st.columns(2)
        with date_col:
            date_from = st.date_input("From date", value=date.today())
        with end_col:
            date_to = st.date_input("To date", value=date.today())
        date_range = (date_from, date_to)

    try:
        report = generate_report(report_key, date_range)
        json_data = export_report(report, "json")
        csv_data = export_report(report, "csv")
    except (OSError, TypeError, ValueError) as exc:
        st.error(str(exc))
        report = None
    if report is not None:
        report_frame = pd.DataFrame(
            report.get("inventory", report.get("records", []))
        )
        report_frame.index = pd.RangeIndex(
            start=1,
            stop=len(report_frame) + 1,
            name="No.",
        )
        st.dataframe(
            report_frame,
            width="stretch",
            column_config={
                "_index": st.column_config.NumberColumn(
                    "No.",
                    width="small",
                    format="%d",
                ),
            },
            hide_index=False,
        )
        filename_stub = f"{report_key}_{date.today().isoformat()}"
        download_col, csv_col = st.columns(2)
        with download_col:
            st.download_button(
                "Download JSON",
                json_data,
                file_name=f"{filename_stub}.json",
                mime="application/json",
                on_click=_log_export,
                args=(report_key,),
            )
        with csv_col:
            st.download_button(
                "Download CSV",
                csv_data,
                file_name=f"{filename_stub}.csv",
                mime="text/csv",
                on_click=_log_export,
                args=(report_key,),
            )

    st.divider()
    st.subheader("Import inventory")
    st.caption(
        "Upload a FoodShare inventory JSON file. Matching food IDs are updated; "
        "new IDs are added. Other records and existing thresholds are preserved."
    )
    uploaded_file = st.file_uploader(
        "Inventory JSON",
        type=["json"],
        key="admin_inventory_import",
    )
    imported_data = None
    if uploaded_file is not None:
        try:
            imported_data = import_records(uploaded_file, "json")
        except (TypeError, ValueError) as exc:
            st.error(str(exc))
        else:
            st.write(f"{len(imported_data['inventory'])} valid food items found.")
            import_frame = pd.DataFrame(imported_data["inventory"])
            import_frame.index = pd.RangeIndex(
                start=1,
                stop=len(import_frame) + 1,
                name="No.",
            )
            st.dataframe(
                import_frame,
                width="stretch",
                column_config={
                    "_index": st.column_config.NumberColumn(
                        "No.",
                        width="small",
                        format="%d",
                    ),
                },
                hide_index=False,
            )
    with st.form("admin_inventory_import_confirm"):
        confirm_import = st.checkbox(
            "I reviewed the preview and confirm merging these inventory records."
        )
        import_submitted = st.form_submit_button(
            "Merge inventory",
            disabled=imported_data is None or not confirm_import,
        )
    if import_submitted and imported_data is not None:
        inventory = get_inventory_manager()
        try:
            added, updated = merge_inventory_import(imported_data, inventory)
        except (OSError, TypeError, ValueError) as exc:
            st.error(str(exc))
        else:
            account = st.session_state.get("account", {})
            log_action(
                str(account.get("_account_number", "unknown")),
                "inventory_imported",
                f"added={added}; updated={updated}",
                actor_role="Admin",
                record_type="inventory",
                record_id="inventory.json",
            )
            save_admin_changes(
                f"Inventory merged: {added} added, {updated} updated."
            )

    st.divider()
    st.subheader("Data backup")
    with st.form("admin_backup_confirm"):
        confirm_backup = st.checkbox("Confirm creating an inventory backup.")
        backup_submitted = st.form_submit_button(
            "Create backup",
            disabled=not confirm_backup,
        )
    if backup_submitted:
        root = _project_root()
        backup_directory = root / "assets" / "backups"
        success = backup_data(
            str(root / "assets" / "inventory.json"),
            str(backup_directory),
        )
        if not success:
            st.error("Backup failed. Check the application log for details.")
        else:
            account = st.session_state.get("account", {})
            log_action(
                str(account.get("_account_number", "unknown")),
                "data_backup_created",
                str(backup_directory),
                actor_role="Admin",
                record_type="backup",
                record_id=backup_directory.name,
            )
            save_admin_changes("Inventory and available daily order data backed up.")


if __name__ == "__main__":
    show_report_export_page()
