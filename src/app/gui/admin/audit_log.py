"""Persistent audit records for administrator account and stock actions."""

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from app.gui.shared.toolbar import require_role, show_toolbar
from app.users.user import UserAccess


def _audit_file() -> Path:
    project_root = Path(__file__).resolve().parents[4]
    return project_root / "assets" / "admin_audit_log.json"


def _load_audit_logs() -> list[dict[str, Any]]:
    path = _audit_file()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        logs: Any = json.load(file)
    if not isinstance(logs, list) or any(not isinstance(row, dict) for row in logs):
        raise ValueError("Admin audit log must contain a list of records.")
    return logs


def _application_audit_logs() -> list[dict[str, Any]]:
    project_root = Path(__file__).resolve().parents[4]
    candidates = {
        Path.cwd() / "FoodShareTracker.log",
        project_root / "FoodShareTracker.log",
    }
    audit_rows: list[dict[str, Any]] = []
    pattern = re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}"
        r"(?:[,.]\d+)?)\s+-\s+\w+\s+-\s+"
        r"sensitive_data_access (?P<fields>.*)$"
    )
    for path in candidates:
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                match = pattern.match(line.rstrip("\n"))
                if not match:
                    continue
                fields = dict(
                    field.split("=", maxsplit=1)
                    for field in match.group("fields").split()
                    if "=" in field
                )
                audit_rows.append({
                    "timestamp": match.group("timestamp").replace(",", "."),
                    "user": fields.get("actor_id", ""),
                    "actor_role": fields.get("actor_role", ""),
                    "action": fields.get("action", ""),
                    "record_type": fields.get("record_type", ""),
                    "record_id": fields.get("record_id", ""),
                    "source": "sensitive_access",
                })
    return audit_rows


def view_audit_logs(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    records = [*_load_audit_logs(), *_application_audit_logs()]
    return [
        record
        for record in records
        if all(
            value is None or str(record.get(key, "")) == str(value)
            for key, value in filters.items()
        )
    ]


def filter_audit_logs(
    user_id: str | None = None,
    action: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    record_type: str | None = None,
    record_id: str | None = None,
    records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    result = []
    for record in view_audit_logs() if records is None else records:
        timestamp = str(record.get("timestamp", ""))
        try:
            record_date = date.fromisoformat(timestamp[:10])
        except ValueError:
            continue
        if user_id and str(record.get("user", "")) != user_id:
            continue
        if action and str(record.get("action", "")) != action:
            continue
        if record_type and str(record.get("record_type", "")) != record_type:
            continue
        if record_id and str(record.get("record_id", "")) != record_id:
            continue
        if date_from and record_date < date_from:
            continue
        if date_to and record_date > date_to:
            continue
        result.append(record)
    return result


def flag_unusual_activity(
    records: list[dict[str, Any]],
    account_manager=None,
) -> list[dict[str, Any]]:
    if account_manager is None:
        from app.auth.account_manager import AccountManager

        account_manager = AccountManager()
    known_users = {
        str(account.get("_account_number"))
        for account in account_manager.list_accounts()
    }
    flagged = []
    for record in records:
        actor_id = str(record.get("user", ""))
        if (
            record.get("record_type") == "inventory_threshold"
            and (
                actor_id not in known_users
                or str(record.get("actor_role", "")).casefold() != "admin"
            )
        ):
            flagged.append({
                **record,
                "flag": "Threshold change by an unknown or non-admin account.",
            })
    return flagged


def log_action(
    user: str,
    action: str,
    target: str,
    *,
    actor_role: str = "Admin",
    record_type: str = "admin_action",
    record_id: str | None = None,
) -> None:
    from datetime import datetime

    path = _audit_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    records = _load_audit_logs()
    records.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user": user,
        "actor_role": actor_role,
        "action": action,
        "target": target,
        "record_type": record_type,
        "record_id": record_id or target,
    })
    temporary_path = path.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)
    temporary_path.replace(path)


def save_admin_changes(message: str) -> None:
    st.session_state["admin_change_message"] = message
    st.rerun()


def show_admin_change_message() -> None:
    if message := st.session_state.pop("admin_change_message", None):
        st.success(message)


def show_audit_log_page() -> None:
    require_role(UserAccess.ADMIN)
    show_toolbar()
    st.title("Audit Log")
    st.caption(
        "Review administrator changes and logged access to sensitive records."
    )
    try:
        all_records = view_audit_logs()
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        st.error(f"Unable to read audit records: {exc}")
        return
    with st.form("audit_log_filters"):
        user_id = st.text_input("User or account ID").strip() or None
        action_options = [
            "All actions",
            *sorted({str(record.get("action", "")) for record in all_records}),
        ]
        selected_action = st.selectbox("Action", action_options)
        record_type = st.text_input("Record type").strip() or None
        record_id = st.text_input("Record ID").strip() or None
        date_from_col, date_to_col = st.columns(2)
        with date_from_col:
            date_from = st.date_input("From date", value=date.today())
        with date_to_col:
            date_to = st.date_input("To date", value=date.today())
        submitted = st.form_submit_button("Apply filters")

    if submitted and date_from and date_to and date_from > date_to:
        st.error("The start date must be on or before the end date.")
        return
    if submitted:
        records = filter_audit_logs(
            user_id=user_id,
            action=selected_action if selected_action != "All actions" else None,
            date_from=date_from,
            date_to=date_to,
            record_type=record_type,
            record_id=record_id,
            records=all_records,
        )
    else:
        records = all_records
    if records:
        audit_frame = pd.DataFrame(records).sort_values(
            "timestamp",
            ascending=False,
        )
        audit_frame.index = pd.RangeIndex(
            start=1,
            stop=len(audit_frame) + 1,
            name="No.",
        )
        st.dataframe(
            audit_frame,
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
    else:
        st.info("No audit records match the selected filters.")
    flags = flag_unusual_activity(
        records,
        st.session_state.account_manager,
    )
    if flags:
        st.subheader("Unusual activity")
        flags_frame = pd.DataFrame(flags)
        flags_frame.index = pd.RangeIndex(
            start=1,
            stop=len(flags_frame) + 1,
            name="No.",
        )
        st.dataframe(
            flags_frame,
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

    st.subheader("Consent history")
    client_id = st.text_input("Client account number for consent history").strip()
    if client_id:
        try:
            consent_records = view_consent_log(client_id)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            st.error(f"Unable to read consent records: {exc}")
            return
        if consent_records:
            consent_frame = pd.DataFrame(consent_records)
            consent_frame.index = pd.RangeIndex(
                start=1,
                stop=len(consent_frame) + 1,
                name="No.",
            )
            st.dataframe(
                consent_frame,
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
        else:
            st.info(
                "No consent records found. Consent history is available only "
                "when consent events have been recorded."
            )


def view_consent_log(client_id: str) -> list[dict[str, Any]]:
    path = _audit_file().parent / "consent_log.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        records: Any = json.load(file)
    if not isinstance(records, list) or any(
        not isinstance(record, dict) for record in records
    ):
        raise ValueError("Consent log must contain a list of records.")
    return [
        record
        for record in records
        if str(record.get("client_id", "")) == client_id
    ]


if __name__ == "__main__":
    show_audit_log_page()
