"""
This class holds the main logic between users and the inventory, as well as the in and out data flows.

@author Su Chengzhang
"""
import json, logging
from pathlib import Path
import streamlit as st

from app.food.food_item import FoodItem
from app.food.food_order import FoodOrder
from app.food.inventory import Inventory

from app.users.user import User, UserAccess
from app.users.donor import Donor


from app.exceptions.NotFoundException import FoodNotFound, OrderNotFound


log = logging.getLogger(__name__)

class FoodShareTracker:
    def __init__(
        self,
        user: Donor,
        inventory_path: str = "assets/inventory.json",
    ) -> None:
        self._inventory_path = inventory_path
        self._inventory_data = []
        self._inventory = Inventory(inventory_path)
        self._user = user
        self._id = {}
        self.load_data()
        self.to_object()

    def load_data(self) -> None:
        """
        Load data from JSON file and populates the object lists.
        """
        try:
            with open(self._inventory_path, 'r') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Inventory file must contain a JSON object.")
                inventory = data.get("inventory", [])
                if not isinstance(inventory, list):
                    raise ValueError("Inventory data must be a list.")
                self._inventory_data = inventory
                # self._id['next_food_id'] = data.get("next_food_id", {})

            # with open(self._account_path, 'r') as x:
            #     data = json.load(x)
            #     self._account = data.get("accounts", [])
            #     self._id['next_user_id'] = data.get("next_user_id", {})

        except FileNotFoundError:
            print("Data file not found. Starting with a clean state.")

    def to_object(self) -> None:
        """
        Converts dictionaries back to their respective object types.
        """
        if len(self._inventory_data) != 0:
            for i in range(len(self._inventory_data)):
                food = self._inventory_data[i]
                new_food = FoodItem(food['_id'], food['_name'], food['_category'], 
                                    food['_stock'], food['_unit'], food['_tags'], food['_inDate'],
                                    food.get('_expiryDate'))
                self._inventory_data[i] = new_food


        if len(self._id) == 0:
            donation_ids = [
                record.get("id", 0)
                for record in self._user.get_donation_rec()
                if isinstance(record, dict) and isinstance(record.get("id"), int)
            ]
            self._id = {"next_donation_id": max(donation_ids, default=0) + 1}


    def save_data(self) -> None:
        """
        Converts object lists back to dictionaries and saves to JSON.
        """

        order_to_save = {
            f"{self._user.get_user_name()}": [vars(self._user)],
            "next_donation_id": self._id['next_donation_id']
        }
        donor_path = Path("assets/user/donor") / f"donor{self._user.get_user_id()}.json"
        donor_path.parent.mkdir(parents=True, exist_ok=True)
        with donor_path.open("w", encoding="utf-8") as f:
            json.dump(order_to_save, f, indent=4)


#-----------------------------CRUD-----------------------------#


        
        
