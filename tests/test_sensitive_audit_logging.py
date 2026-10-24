import logging

from app.auth.account_manager import AccountManager
from app.gui.staff import pending_orders
from util.admin_utils import init_logger, log_sensitive_access


def test_sensitive_access_log_contains_audit_metadata_only(caplog) -> None:
    # ARRANGE: Capture audit events and define identifying record metadata.
    private_value = "sensitive-client-phone"

    # ACT: Log a sensitive-record access without passing client field values.
    with caplog.at_level(logging.INFO, logger="foodshare.audit"):
        log_sensitive_access(
            "view",
            "03-0001",
            "staff",
            "client_preferences",
            "01-0001",
        )

    # ASSERT: The record identifies the access but contains no client values.
    assert len(caplog.records) == 1
    assert "action=view" in caplog.text
    assert "actor_id=03-0001" in caplog.text
    assert "actor_role=staff" in caplog.text
    assert "record_type=client_preferences" in caplog.text
    assert "record_id=01-0001" in caplog.text
    assert private_value not in caplog.text


def test_client_account_creation_and_update_are_audited(
    tmp_path,
    caplog,
) -> None:
    # ARRANGE: Create an isolated account store and capture audit messages.
    accounts_path = tmp_path / "accounts.json"
    accounts_path.write_text('{"accounts": {}}', encoding="utf-8")
    manager = AccountManager(str(accounts_path))

    # ACT: Create a client and update a sensitive field.
    with caplog.at_level(logging.INFO, logger="foodshare.audit"):
        client_id = manager.create_account(
            "Private Client Name",
            "555-0101",
            "private-password",
            "Client",
            food_constraints=["private-preference"],
            address="private-address",
        )
        account = manager.find_account(client_id, "Client")
        assert account is not None
        manager.update_account_info(
            account,
            actor_id=client_id,
            actor_role="client",
            _phone_number="555-0199",
        )

    # ASSERT: Mutations are recorded without embedding sensitive values.
    assert "action=create" in caplog.text
    assert "action=update" in caplog.text
    assert f"record_id={client_id}" in caplog.text
    for private_value in (
        "Private Client Name",
        "555-0101",
        "private-password",
        "private-preference",
        "private-address",
        "555-0199",
    ):
        assert private_value not in caplog.text


def test_init_logger_persists_audit_events(tmp_path) -> None:
    # ARRANGE: Configure the application logger to write to a temporary file.
    log_path = tmp_path / "application.log"
    init_logger(str(log_path))
    root_logger = logging.getLogger()
    file_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.FileHandler)
        and handler.baseFilename == str(log_path.resolve())
    ]

    # ACT: Emit an audit event through the configured logger.
    try:
        log_sensitive_access(
            "export",
            "system",
            "system",
            "client_order_backup",
            "order_backup_2026-10-23.json",
        )
        for handler in file_handlers:
            handler.flush()
        content = log_path.read_text(encoding="utf-8")
    finally:
        for handler in file_handlers:
            root_logger.removeHandler(handler)
            handler.close()

    # ASSERT: The configured log file contains the action and record metadata.
    assert "sensitive_data_access action=export" in content
    assert "record_type=client_order_backup" in content


def test_client_order_lookup_only_returns_that_clients_orders(
    tmp_path,
    monkeypatch,
) -> None:
    # ARRANGE: Store two clients' orders in the shared daily order file.
    order_file = tmp_path / "2026-10-23_12-00-00_orders.json"
    order_file.write_text(
        (
            '{"Alex Client": [{"_id": 1, "_name": "Apples", '
            '"_order_amount": 2, "_unit": "kg"}], '
            '"Morgan Client": [{"_id": 2, "_name": "Bread", '
            '"_order_amount": 1, "_unit": "loaf"}]}'
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        pending_orders,
        "get_orders_directory",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        pending_orders,
        "load_order_statuses",
        lambda: {},
    )

    # ACT: Load orders under a client's own name filter.
    orders, errors = pending_orders.load_orders("Alex Client")

    # ASSERT: Only that client's order is returned without loader warnings.
    assert errors == []
    assert [order["client"] for order in orders] == ["Alex Client"]
    assert [order["food_name"] for order in orders] == ["Apples"]
