"""
The donor class stores all the information of a donor.
It is a sub-class inherit from User abstract super class.

@author Su Chengzhang
"""
import datetime
from datetime import date

from app.users.user import User, UserAccess
from app.exceptions.NotFoundException import DonationNotFound

class Donor(User):
    def __init__(
        self,
        registered_account: str,
        password: str,
        name: str,
        contact: str,
        donation_rec: list | None = None,
    ) -> None:
        super().__init__(
            registered_account,
            password,
            name,
            contact,
            UserAccess.DONOR,
        )
        self._donation_rec = list(donation_rec or [])

    def get_donation_rec(self) -> list:
        return self._donation_rec

    def set_donation_rec(self, new_records: list) -> None:
        self._donation_rec = list(new_records)

    def add_donation_record(self, donation_id: int, new_records: list) -> None:
        for record in self._donation_rec:
            if int(record['id']) == donation_id:
                raise ValueError("Donation id already exists.")
        if len(new_records) <= 0:
            raise DonationNotFound("The incoming donation is empty.")
        self._donation_rec.append({
            "id": donation_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "donation": new_records,
        })

    def add_donation(self, food_name: str, quantity: int, expiry_date: str,
                     drop_off_date: str, drop_off_time: str) -> bool:
        """Validate a donation and add it using the main-branch record format."""
        slots = ("09:00", "10:00", "11:00", "14:00", "15:00", "16:00")
        if not isinstance(food_name, str) or not food_name.strip():
            return False
        if type(quantity) is not int or quantity <= 0 or drop_off_time not in slots:
            return False
        try:
            expiry = date.fromisoformat(expiry_date)
            drop_off = date.fromisoformat(drop_off_date)
        except (ValueError, TypeError):
            return False
        if expiry < date.today() or drop_off < date.today() or drop_off > expiry:
            return False
        donation_ids = [int(r["id"]) for r in self._donation_rec if "id" in r]
        next_id = max(donation_ids, default=0) + 1
        item = {"food_name": food_name.strip(), "quantity": quantity,
                "expiry_date": expiry_date, "drop_off_date": drop_off_date,
                "drop_off_time": drop_off_time, "status": "Pending"}
        self.add_donation_record(next_id, [item])
        return True

    def update_drop_off(self, donation_id: int, new_date: str, new_time: str) -> bool:
        for record in self._donation_rec:
            if int(record.get("id", -1)) == donation_id:
                items = record.get("donation", [])
                if not items or items[0].get("status") != "Pending":
                    return False
                item = items[0]
                slots = ("09:00", "10:00", "11:00", "14:00", "15:00", "16:00")
                try:
                    proposed = date.fromisoformat(new_date)
                    expiry = date.fromisoformat(item["expiry_date"])
                except (ValueError, TypeError, KeyError):
                    return False
                if proposed < date.today() or proposed > expiry or new_time not in slots:
                    return False
                item["drop_off_date"] = new_date
                item["drop_off_time"] = new_time
                return True
        return False

    def cancel_donation(self, donation_id: int) -> bool:
        for record in self._donation_rec:
            if int(record.get("id", -1)) == donation_id:
                items = record.get("donation", [])
                if not items or items[0].get("status") != "Pending":
                    return False
                items[0]["status"] = "Cancelled"
                return True
        return False

    def return_user(self) -> "Donor":
        return self
