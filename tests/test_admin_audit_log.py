import json
from datetime import date

from app.gui.admin import audit_log


def test_audit_log_filters_admin_actions_by_user_action_and_date(
    tmp_path,
    monkeypatch,
) -> None:
    audit_path = tmp_path / "audit.json"
    monkeypatch.setattr(audit_log, "_audit_file", lambda: audit_path)
    audit_log.log_action(
        "admin-1",
        "stock_adjusted",
        "food_id=1",
        record_type="inventory",
        record_id="1",
    )
    audit_log.log_action(
        "admin-2",
        "account_access_disabled",
        "client-1",
        record_type="account",
        record_id="client-1",
    )

    records = audit_log.filter_audit_logs(
        user_id="admin-1",
        action="stock_adjusted",
        date_from=date.today(),
        date_to=date.today(),
        record_type="inventory",
        record_id="1",
    )

    assert len(records) == 1
    assert records[0]["target"] == "food_id=1"
    assert records[0]["actor_role"] == "Admin"
    assert json.loads(audit_path.read_text(encoding="utf-8"))[0]["record_id"] == "1"
