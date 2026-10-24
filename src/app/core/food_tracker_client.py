"""
This class holds the main logic between users and the inventory, as well as the in and out data flows.

@author Su Chengzhang
"""
import json, logging, datetime
import math
from pathlib import Path
from typing import Any
import streamlit as st

from app.food.food_item import FoodItem
from app.food.food_order import FoodOrder
from util.admin_utils import log_sensitive_access, opaque_audit_id

from app.users.user import User
from app.users.client import Client
from app.users.constraint import is_hard

from app.auth.account_manager import AccountManager

from app.exceptions.NotFoundException import FoodNotFound, OrderNotFound

# logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s',
#     )

log: logging.Logger = logging.getLogger(__name__)

class FoodShareTracker:
    def __init__(
        self,
        user: Client,
        inventory_path: str = "assets/inventory.json",
        account_manager: AccountManager | None = None,
    ) -> None:
        self._inventory_path: str = inventory_path
        self._inventory: list[Any] = []
        self._user: Client = user
        self._account_manager: AccountManager | None = account_manager
        self._orders: list[FoodOrder] = []
        self._origin_orders: list[FoodOrder] = []
        self._id: dict[str, int] = {"next_order_id": 1}
        self.load_data()
        self.to_object()

    def load_data(self) -> None:
        """
        Load data from JSON file and populates the object lists.
        """
        try:
            with open(self._inventory_path, 'r') as f:
                data: dict[str, Any] = json.load(f)
                if not isinstance(data, dict) or not isinstance(
                    data.get("inventory", []), list
                ):
                    raise ValueError("Inventory file must contain an inventory list.")
                self._inventory = data.get("inventory", [])
        except FileNotFoundError:
            log.warning("Inventory file not found: %s", self._inventory_path)
        except json.JSONDecodeError as exc:
            log.exception("Inventory JSON is invalid: %s", self._inventory_path)
            raise ValueError(
                f"Inventory file contains invalid JSON: {self._inventory_path}"
            ) from exc

    def to_object(self) -> None:
        self._inventory = [
            food if isinstance(food, FoodItem) else FoodItem(
                food["_id"],
                food["_name"],
                food["_category"],
                food.get("_stock", 0),
                food.get("_unit", ""),
                food.get("_tags", []),
                food.get("_inDate"),
                food.get("_expiryDate"),
            )
            for food in self._inventory
        ]
        previous_ids: list[int] = [
            record.get("id", 0)
            for record in self._user.get_food_order_rec()
            if isinstance(record, dict) and isinstance(record.get("id"), int)
        ]
        self._id["next_order_id"] = max(previous_ids, default=0) + 1


    def save_data(self) -> None:
        order_to_save: dict[str, Any] = {
            f"{self._user.get_user_name()}": [vars(self._user)],
            "next_order_id": self._id['next_order_id']
        }
        if self._account_manager is not None:
            account: dict[str, Any] | None = self._account_manager.find_account(
                self._user.get_account_number(),
                "Client",
            )
            self._account_manager.update_account_info(
                account,
                actor_id=self._user.get_account_number(),
                actor_role="Client",
                _food_orders_rec=self._user.get_food_order_rec(),
            )

        client_path: Path = Path("assets/user/client") / f"client{self._user.get_user_name()}.json"
        client_path.parent.mkdir(parents=True, exist_ok=True)
        with client_path.open("w", encoding="utf-8") as f:
            json.dump(order_to_save, f, indent=4)

#-----------------------------CRUD-----------------------------#

    def list_orders_in_dict(self) -> list[dict[str, Any]]:
        orders: list[dict[str, Any]] = [vars(i) for i in self._orders]
        for order in orders:
            order.pop("_id", None)
            order.pop("_inDate", None)
        return orders

    def list_orders(self) -> list[FoodOrder]:
        original_orders: list[FoodOrder] = self._origin_orders
        return self._origin_orders

    def find_food_by_name(self, food_name:str) -> FoodItem:
        """
        Retrieve the specific food details through searching the food name.
        """
        for food in self._inventory:
            if food.get_food_name() == food_name:
                return food
        raise FoodNotFound(f"Food {food_name} not found.")

    def find_food_by_category(self, food_category:str) -> list[FoodItem]:
        """
        Retrieve the specific food details through category.
        """
        foods: list[FoodItem] = []
        for food in self._inventory:
            if food.get_food_category() == food_category:
                foods.append(food)
        if len(foods) > 0:
            return foods
        raise FoodNotFound(f"Food {food_category} not found.")

    def start_new_order(self) -> None:
        """
        For client to start a brand new order from the current one.
        """
        self._orders, self._origin_orders = [], []

    def add_food_order(self, food_name: str, amount: int | float = 1) -> bool:
        """
        Add a food into existing order
        """
        if (
            isinstance(amount, bool)
            or not isinstance(amount, (int, float))
            or (isinstance(amount, float) and not math.isfinite(amount))
            or amount <= 0
        ):
            raise ValueError("Order amount must be a positive number.")

        for order1, order2 in zip(self._orders, self._origin_orders):
            if order1.get_food_name() == food_name and order2.get_food_name() == food_name:
                new_amount = order1.get_order_amount() + amount
                if new_amount > order1.get_food_stocks():
                    st.warning("Insufficient food")
                    return False
                order1.set_order_amount(new_amount)
                order2.set_order_amount(new_amount)
                return True

        food: FoodItem = self.find_food_by_name(food_name)
        if food.get_food_stocks() >= amount:
            food_order1: FoodOrder = FoodOrder(food.get_food_id(), food.get_food_name(), food.get_food_category(),
                                   amount, food.get_food_stocks(), food.get_food_unit(), food.get_food_tags(),
                                   food.get_food_expiry_date())
            food_order2: FoodOrder = FoodOrder(food.get_food_id(), food.get_food_name(), food.get_food_category(),
                                   amount, food.get_food_stocks(), food.get_food_unit(), food.get_food_tags(),
                                   food.get_food_expiry_date())
            self._orders.append(food_order1)
            self._origin_orders.append(food_order2)
            return True
        else:
            st.warning("Insufficient food") # may need to set restrictions when the menu given to the client
            return False


    def update_food_order(self, food_name:str, new_quantity:float) -> bool:
        """
        Update a specific food order with given quantity
        """
        if (
            isinstance(new_quantity, bool)
            or not isinstance(new_quantity, (int, float))
            or (isinstance(new_quantity, float) and not math.isfinite(new_quantity))
            or new_quantity <= 0
        ):
            raise ValueError("Order quantity must be a positive number.")

        for order1, order2 in zip(self._orders, self._origin_orders):
            if order1.get_food_name() == food_name and order2.get_food_name() == food_name:
                if float(order1.get_food_stocks()) >= new_quantity and float(order2.get_food_stocks()) >= new_quantity:
                    order1.set_order_amount(new_quantity)
                    order2.set_order_amount(new_quantity)
                    return True
                else:
                    st.info(f"Only few {food_name} left")
                    return False
        raise OrderNotFound

    def remove_food_from_order(self, order_food_name: str) -> None:
        """
        Remove a food from existing orders.
        """
        for order1, order2 in zip(self._orders, self._origin_orders):
            if order1.get_food_name() == order_food_name and order2.get_food_name() == order_food_name:
                self._orders.remove(order1)
                self._origin_orders.remove(order2)
                st.info(f"Ordered {order_food_name} remove. ")
                return
        raise OrderNotFound(f"Ordered food {order_food_name} not found")

    def food_constraint_violation(self) -> None:
        """
        Check no food in existing order violate the client's food constraints. 
        """
        hard_constraints: list[object] = [
            constraint
            for constraint in self._user.get_client_food_constraints()
            if is_hard(constraint)
        ]
        violating_orders: list[tuple[FoodOrder, list[object]]] = []
        remaining_orders: list[FoodOrder] = []
        reserved_quantities: dict[int | str, int | float] = {}
        for food_order in self._orders:
            violations: list[object] = [
                constraint
                for constraint in hard_constraints
                if constraint in food_order.get_food_tags()
            ]
            if violations:
                violating_orders.append((food_order, violations))
            else:
                remaining_orders.append(food_order)
                food_id: int = food_order.get_food_id()
                reserved_quantities[food_id] = (
                    reserved_quantities.get(food_id, 0)
                    + food_order.get_order_amount()
                )

        substitutions: list[FoodOrder] = []
        for food_order, violations in violating_orders:
            new_order: FoodOrder | None = self._food_substitution(
                food_order.get_food_category(),
                hard_constraints,
                food_order.get_order_amount(),
                reserved_quantities,
            )
            if new_order is not None:
                substitutions.append(new_order)
                food_id: int = new_order.get_food_id()
                reserved_quantities[food_id] = (
                    reserved_quantities.get(food_id, 0)
                    + new_order.get_order_amount()
                )
                st.info(
                    f"Food violating {', '.join(map(str, violations))} was "
                    f"replaced by {new_order.get_food_name()}."
                )
                log.info(
                    "Food %s substituted by %s with the same quantity.",
                    food_order.get_food_name(),
                    new_order.get_food_name(),
                )
            else:
                log.warning(
                    "No valid substitute found for %s",
                    food_order.get_food_name(),
                )
                st.warning(
                    f"Food violating {', '.join(map(str, violations))} was "
                    "removed; no suitable replacement is available."
                )
        self._orders = remaining_orders + substitutions
                        
    def _food_substitution(
        self,
        food_category: str,
        constraints: list,
        amount: int | float = 1,
        reserved_quantities: dict[int | str, int | float] | None = None,
    ) -> FoodOrder | None:
        """
        Possible provide a substitution for food violate the constraint under same category. 

        :param food_category: The food category that need to be substituted.
        :param constraints: The client's hard dietary restrictions.
        :param amount: The amount of food ordered that need to be substituted.

        :return Whether the substitution is found as a boolean value.
        """
        reserved_quantities = reserved_quantities or {}
        for food in self._inventory:
            if food.get_food_category() == food_category:
                if (
                    not any(constraint in food.get_food_tags() for constraint in constraints)
                    and food.get_food_stocks() - reserved_quantities.get(
                        food.get_food_id(),
                        0,
                    ) >= amount
                ):
                    return FoodOrder(
                        food.get_food_id(),
                        food.get_food_name(),
                        food.get_food_category(),
                        amount,
                        food.get_food_stocks(),
                        food.get_food_unit(),
                        food.get_food_tags(),
                        food.get_food_expiry_date(),
                    )
        return None

    def finish_food_order(self) -> tuple[list[FoodOrder], list[FoodOrder]]:
        """
        Response to the requested order list from the frontend if FoodOrder exist.
        The client can choose to accept to reject the substitution.

        :return A tuple consist of one list of substituted orders and one original orders.
        :raise OrderNotFound: If there's nothing in the current order. 
        """
        # for food_order in self._orders:
        #     # self._real_time_synchronization(food_order.get_food_name(), food_order.get_order_amount())       # real time reduction
        self.food_constraint_violation()
        if len(self._orders) > 0:
            return (self._orders, self._origin_orders)
        else:
            raise OrderNotFound

    def reject_changes(self) -> None:
        self._orders = []
        for food in self._origin_orders:
            new_order: FoodOrder = FoodOrder(food.get_food_id(), food.get_food_name(), food.get_food_category(),
                                   food.get_order_amount(), food.get_food_stocks(), food.get_food_unit(), food.get_food_tags(),
                                   food.get_food_expiry_date())
            self._orders.append(new_order)

    def accept_orders(self, accepted_orders: list[FoodOrder]) -> None:
        if not accepted_orders:
            raise OrderNotFound("Cannot accept an empty order.")

        order_date: str = datetime.datetime.now().strftime("%Y-%m-%d")
        orders_path: Path = Path("assets/orders")
        orders_path.mkdir(parents=True, exist_ok=True)
        daily_path: Path = orders_path / f"{order_date}_orders.json"
        if daily_path.exists():
            with daily_path.open("r", encoding="utf-8") as f:
                daily_orders: dict[str, Any] = json.load(f)
            if not isinstance(daily_orders, dict):
                raise ValueError(f"Order data in {daily_path} must be an object.")
        else:
            daily_orders: dict[str, Any] = {}

        client_orders: list[dict[str, Any]] = daily_orders.setdefault(self._user.get_user_name(), [])
        if not isinstance(client_orders, list):
            raise ValueError("Client order data must be a list.")

        accepted: list[dict[str, Any]] = []
        for order in accepted_orders:
            order_record = vars(order).copy()
            order_key = (
                f"{daily_path.name}|{self._user.get_user_name()}|"
                f"{len(client_orders) + len(accepted) + 1}"
            )
            order_record["_order_key"] = order_key
            order_record["_order_status"] = "Pending"
            accepted.append(order_record)

        client_orders.extend(accepted)
        temporary_path: Path = daily_path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as f:
            json.dump(daily_orders, f, indent=4)
        temporary_path.replace(daily_path)

        self._user.add_food_orders_rec(self._id["next_order_id"], accepted)
        account_number = self._user.get_account_number()
        for order in accepted:
            log_sensitive_access(
                "create",
                account_number,
                "Client",
                "client_order",
                opaque_audit_id(str(order["_order_key"])),
            )
        self._id["next_order_id"] += 1


    def check_order_history(self) -> list[dict[str, Any]]:
        history_rec: list[dict[str, Any]] = self._user.get_food_order_rec()
        return history_rec      # return in a form of [{'id': 1, 'timestamp': ____, 'orders': [{FoodOrder}, {FoodOrder}]}]
        
        
