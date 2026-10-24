import json
from datetime import datetime
from pathlib import Path


def get_notification_file():
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "assets" / "orders" / "client_notifications.json"


def load_notifications():
    file_path = get_notification_file()

    if not file_path.exists():
        return []

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Notification file contains invalid JSON: {file_path}"
        ) from exc

    if not isinstance(data, list) or any(
        not isinstance(notification, dict) for notification in data
    ):
        raise ValueError(
            f"Notification file must contain a list of objects: {file_path}"
        )

    return data


def save_notifications(notifications):
    file_path = get_notification_file()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(notifications, file, indent=4, ensure_ascii=False)


def create_message(order_key, language="English"):
    if language == "Malay":
        return f"Pesanan {order_key} anda sedia untuk diambil."

    return f"Your FoodShare order {order_key} is ready for collection."


def notify_client(client_name, order_key, language="English"):
    notifications = load_notifications()

    # Prevent duplicate notifications for the same order.
    for notification in notifications:
        if notification.get("order_key") == order_key:
            return False

    message = create_message(order_key, language)

    # SMS is not connected, so use an in-app notification.
    notifications.append({
        "client": client_name,
        "order_key": order_key,
        "message": message,
        "language": language,
        "channel": "In-App",
        "sms_status": "Not configured",
        "timestamp": datetime.now().isoformat(),
        "read": False
    })

    save_notifications(notifications)
    return True


def mark_as_read(order_key, client_name):
    notifications = load_notifications()

    for notification in notifications:
        if (
            notification.get("order_key") == order_key
            and notification.get("client") == client_name
        ):
            notification["read"] = True
            save_notifications(notifications)
            return True

    return False
