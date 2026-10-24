import json
import pytest

from app.gui.donor import donor_dashboard


@pytest.fixture
def notification_file(tmp_path, monkeypatch):
    file_path = tmp_path / "donor_notifications.json"
    monkeypatch.setattr(
        donor_dashboard,
        "NOTIFICATION_FILE",
        str(file_path),
    )
    return file_path


def test_missing_notifications(notification_file):
    assert donor_dashboard.load_notifications() == []


def test_add_notification(notification_file):
    donor_dashboard.add_notification("02-0001", "Donation accepted")

    notifications = donor_dashboard.load_notifications()

    assert len(notifications) == 1
    assert notifications[0]["donor_id"] == "02-0001"
    assert notifications[0]["message"] == "Donation accepted"
    assert notifications[0]["read"] is False


def test_multiple_notifications(notification_file):
    donor_dashboard.add_notification("02-0001", "Donation accepted")
    donor_dashboard.add_notification("02-0002", "Donation rejected")

    notifications = donor_dashboard.load_notifications()

    assert len(notifications) == 2
    assert notifications[0]["donor_id"] == "02-0001"
    assert notifications[1]["donor_id"] == "02-0002"


def test_save_and_load_notifications(notification_file):
    data = [
        {
            "donor_id": "02-0001",
            "message": "Test message",
            "read": True,
        }
    ]

    donor_dashboard.save_notifications(data)

    assert donor_dashboard.load_notifications() == data


def test_invalid_notification_file(notification_file):
    notification_file.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError):
        donor_dashboard.load_notifications()