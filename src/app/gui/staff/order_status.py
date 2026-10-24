# gui/staff/order_status.py
import json
from pathlib import Path
from app.core.notification import notify_client

from util.admin_utils import log_sensitive_access, opaque_audit_id


VALID_STATUSES = {
    "Pending",
    "Preparing",
    "Ready for Collection",
    "Completed",
}


def normalize_order_status(status: object, fallback: str = "Pending") -> str:
    if isinstance(status, str) and status in VALID_STATUSES:
        return str(status)
    if isinstance(status, bool):
        return "Completed" if status else "Pending"
    return fallback


def get_status_file() -> Path:
    project_root = Path(__file__).resolve().parents[4]
    return project_root / "assets" / "orders" / "order_status.json"


def load_order_statuses() -> dict[str, str]:
    status_file = get_status_file()

    if not status_file.exists():
        return {}

    try:
        with status_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Order status file contains invalid JSON: {status_file}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Order status file must contain an object: {status_file}"
        )

    return data


def save_order_status(
    order_key: str,
    status: str,
    *,
    actor_id: str = "system",
    actor_role: str = "system",
) -> None:
    if status not in VALID_STATUSES:
        raise ValueError("Invalid order status.")

    try:
        file_name, client_name, item_index_text = order_key.split("|", 2)
    except (AttributeError, ValueError) as exc:
        raise ValueError("Invalid order record key.") from exc
    if Path(file_name).name != file_name:
        raise ValueError("Invalid order record key.")

    try:
        item_index = int(item_index_text)
    except ValueError as exc:
        raise ValueError("Invalid order record key.") from exc
    if item_index < 1 or not client_name:
        raise ValueError("Invalid order record key.")

    orders_file = get_status_file().parent / file_name
    with orders_file.open("r", encoding="utf-8") as file:
        orders = json.load(file)
    if not isinstance(orders, dict):
        raise ValueError("Order data must be a JSON object.")

    client_orders = orders.get(client_name)
    if not isinstance(client_orders, list) or item_index > len(client_orders):
        raise ValueError("Order record was not found. Refresh and try again.")

    order = client_orders[item_index - 1]
    if not isinstance(order, dict):
        raise ValueError("Order record is invalid.")

    status_file = get_status_file()
    statuses = load_order_statuses()
    statuses[order_key] = status

    order["_order_key"] = order_key
    order["_order_status"] = status
    orders_temporary_file = orders_file.with_suffix(".tmp")
    with orders_temporary_file.open("w", encoding="utf-8") as file:
        json.dump(orders, file, indent=4, ensure_ascii=False)
    orders_temporary_file.replace(orders_file)

    status_file.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = status_file.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(statuses, file, indent=4, ensure_ascii=False)

    temporary_file.replace(status_file)
    log_sensitive_access(
        "update",
        actor_id,
        actor_role,
        "client_order",
        opaque_audit_id(order_key),
    )

    if status == "Ready for Collection":
        notify_client(client_name, order_key)
