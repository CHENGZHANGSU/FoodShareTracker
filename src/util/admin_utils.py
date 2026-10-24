# app/admin_utils.py
import logging
import shutil
import datetime
import hashlib
import os


def opaque_audit_id(record_id: str) -> str:
    """Return a stable, non-reversible identifier for sensitive record keys."""
    return hashlib.sha256(record_id.encode("utf-8")).hexdigest()


def log_sensitive_access(
    action: str,
    actor_id: str,
    actor_role: str,
    record_type: str,
    record_id: str,
) -> None:
    """Write client-data audit metadata through the configured application logger."""
    logging.getLogger("foodshare.audit").info(
        "sensitive_data_access action=%s actor_id=%s actor_role=%s "
        "record_type=%s record_id=%s",
        action,
        actor_id,
        actor_role,
        record_type,
        record_id,
    )


def init_logger(log_file="FoodShareTracker.log"):
    """Configures the root logger to write to a file."""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        filename=log_file,
        filemode="a",
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    resolved_log_file = os.path.abspath(log_file)
    if not any(
        isinstance(handler, logging.FileHandler)
        and handler.baseFilename == resolved_log_file
        for handler in root_logger.handlers
    ):
        file_handler = logging.FileHandler(
            resolved_log_file,
            mode="a",
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    print(f"Logging configured. Outputting to {log_file}")

def backup_data(data_path="assets/inventory.json", backup_dir="assets/backups"):
    """Creates a timestamped backup of the main data file."""
    try:
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"inventory_backup_{timestamp}.json"
        backup_filepath = os.path.join(backup_dir, backup_filename)
        shutil.copy(data_path, backup_filepath)
        logging.info(f"Data successfully backed up to {backup_filepath}")

        order_date = datetime.datetime.now().strftime("%Y-%m-%d")
        order_path = os.path.join("assets", "orders", f"{order_date}_orders.json")
        if os.path.exists(order_path):
            backup_order_filename = f"order_backup_{order_date}.json"
            backup_order_filepath = os.path.join(backup_dir, backup_order_filename)
            shutil.copy(order_path, backup_order_filepath)
            logging.info(f"Data successfully backed up to {backup_order_filepath}")
            log_sensitive_access(
                "export",
                "system",
                "system",
                "client_order_backup",
                os.path.basename(backup_order_filepath),
            )
        else:
            logging.info(
                "No order file for %s; skipping the optional order backup.",
                order_date,
            )

        return True
    except OSError:
        logging.exception("Failed to create data backup.")
        return False