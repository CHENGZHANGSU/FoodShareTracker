import pytest

from app.core import notification


def test_missing_notification_file_starts_empty(
    tmp_path,
    monkeypatch,
) -> None:
    notification_path = tmp_path / "client_notifications.json"
    monkeypatch.setattr(
        notification,
        "get_notification_file",
        lambda: notification_path,
    )

    assert notification.load_notifications() == []


def test_corrupt_notification_file_is_not_treated_as_empty(
    tmp_path,
    monkeypatch,
) -> None:
    notification_path = tmp_path / "client_notifications.json"
    notification_path.write_text("{", encoding="utf-8")
    monkeypatch.setattr(
        notification,
        "get_notification_file",
        lambda: notification_path,
    )

    with pytest.raises(ValueError, match="invalid JSON"):
        notification.load_notifications()
