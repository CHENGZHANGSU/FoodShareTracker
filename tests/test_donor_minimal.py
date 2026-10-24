from datetime import date, timedelta
from app.users.donor import Donor


def test_donor_registration_and_update():
    donor = Donor("02-0001", "hash", "Test", "0123")
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert donor.add_donation("Rice", 2, tomorrow, today, "09:00")
    assert donor.get_donation_rec()[0]["donation"][0]["food_name"] == "Rice"
    assert donor.update_drop_off(1, tomorrow, "10:00")
    assert donor.cancel_donation(1)
    assert not donor.update_drop_off(1, tomorrow, "11:00")


def test_invalid_donation():
    donor = Donor("02-0002", "hash", "Test", "0123")
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    assert not donor.add_donation("", 2, today, today, "09:00")
    assert not donor.add_donation("Rice", 0, today, today, "09:00")
    assert not donor.add_donation("Rice", 2, yesterday, today, "09:00")
    assert not donor.add_donation("Rice", 2, today, today, "08:00")

def test_drop_off_after_expiry():
    donor = Donor("02-0003", "hash", "Test", "0123")
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    later = (date.today() + timedelta(days=2)).isoformat()

    assert not donor.add_donation("Rice", 2, tomorrow, later, "09:00")
    assert donor.get_donation_rec() == []


def test_update_changes_saved_data():
    donor = Donor("02-0004", "hash", "Test", "0123")
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    assert donor.add_donation("Rice", 2, tomorrow, today, "09:00")
    assert donor.update_drop_off(1, tomorrow, "10:00")

    item = donor.get_donation_rec()[0]["donation"][0]
    assert item["drop_off_date"] == tomorrow
    assert item["drop_off_time"] == "10:00"


def test_cancel_changes_saved_status():
    donor = Donor("02-0005", "hash", "Test", "0123")
    today = date.today().isoformat()

    assert donor.add_donation("Rice", 2, today, today, "09:00")
    assert donor.cancel_donation(1)

    item = donor.get_donation_rec()[0]["donation"][0]
    assert item["status"] == "Cancelled"
    assert not donor.cancel_donation(1)


def test_accepted_donation_cannot_be_changed():
    donor = Donor("02-0006", "hash", "Test", "0123")
    today = date.today().isoformat()

    assert donor.add_donation("Rice", 2, today, today, "09:00")

    item = donor.get_donation_rec()[0]["donation"][0]
    item["status"] = "Accepted"

    assert not donor.update_drop_off(1, today, "10:00")
    assert not donor.cancel_donation(1)