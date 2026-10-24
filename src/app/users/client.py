"""
This class stores all the entities and behaviors of a clients (people need help from Food Share Tracker).
It is a sub-class inherit from User abstract super class.

@author Su Chengzhang
"""
import datetime

from app.users.user import User, UserAccess
from app.users.constraint import Allergy, FlavourPre, HealthDiet, LifeStyle, Religious

from app.exceptions.NotFoundException import OrderNotFound

class Client(User):
    def __init__(
        self,registered_account: str,
        password: str,
        name: str,
        contact: str,
        constraints: list | None = None,
        address: str | None = None,
        food_orders_rec: list | None = None,
    ) -> None:
        super().__init__(
            registered_account,
            password,
            name,
            contact,
            UserAccess.CLIENT,
        )
        self._food_constraints = list(constraints or [])
        self._food_orders_rec = list(food_orders_rec or [])
        self._address = address

    def get_client_food_constraints(self) -> list:
        return self._food_constraints

    def get_food_order_rec(self) -> list:
        return self._food_orders_rec

    def get_client_address(self) -> str | None:
        return self._address

    def set_client_food_constraints(self, constraints: list) -> None:
        if len(constraints) != 0:
            self._food_constraints = list(constraints)

    def add_food_constraints(
        self,
        new_food_constraint: Allergy | HealthDiet | Religious | LifeStyle | FlavourPre,
    ) -> None:
        if new_food_constraint not in self._food_constraints:
            self._food_constraints.append(new_food_constraint)

    def set_food_rec(self, rec: list) -> None:
        self._food_orders_rec = list(rec)

    def add_food_orders_rec(self, order_id: int, food_order_record: list) -> None:
        if len(food_order_record) <= 0:
            raise OrderNotFound("Cannot record an empty order.")
        self._food_orders_rec.append({
            "id": order_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "orders": food_order_record,
        })

    def return_user(self) -> User:
        return self
