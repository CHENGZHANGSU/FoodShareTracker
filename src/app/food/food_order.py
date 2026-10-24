"""
The food order class stores all the food that the clients ordered.

@author Su Chengzhang
"""
from typing import Any
import math

from app.food.food_item import FoodItem

class FoodOrder(FoodItem):
    def __init__(
        self,
        id: int,
        name: str,
        category: str,
        order_amount: int | float,
        stock: int | float = 0.0,
        unit: str = "",
        food_tag: list[Any] | None = None,
        expiry_date: str | None = None,
    ) -> None:
        super().__init__(
            id,
            name,
            category,
            stock,
            unit,
            food_tag,
            expiryDate=expiry_date,
        )
        self._order_amount = 0
        self.set_order_amount(order_amount)
        self._order_status = "Pending"

    """
    Accessor
    """
    def get_order_amount(self) -> int | float:
        amount: int | float = self._order_amount
        return amount

    """
    Mutator
    """
    def set_order_amount(self, new_amount: int | float) -> None:
        if isinstance(new_amount, bool) or not isinstance(new_amount, (int, float)):
            raise TypeError("Order amount must be a number.")
        if isinstance(new_amount, float) and not math.isfinite(new_amount):
            raise ValueError("Order amount must be finite.")
        if new_amount < 0:
            raise ValueError("Order amount cannot be negative.")
        self._order_amount = new_amount
        
