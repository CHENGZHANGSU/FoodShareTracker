"""
The food item class stores all the entities and behaviors of the food items.

@author Su Chengzhang
@author Low Joeyan
"""
import datetime
import math
from abc import ABC
from typing import Any

from app.users.constraint import *

class FoodItem(ABC):
    def __init__(
        self,
        id: int,
        name: str,
        category: str,
        stock: int | float = 0.0,
        unit: str = "",
        food_tag: list[Any] | None = None,
        inDate: str | None = None,
        expiryDate: str | None = None,
    ) -> None:
        self._id: int = id
        self._name: str = name
        self.validate_stock(stock)
        self._stock: int | float = stock
        self._category: str = category
        self._unit: str = unit
        self._inDate: str = inDate if inDate is not None else datetime.datetime.now().isoformat()
        self._tags: list[Any] = food_tag if food_tag is not None else [None]
        self._expiryDate: str | None = None
        self.set_food_expiry_date(expiryDate)

    """
    Accessor
    """
    def get_food_id(self) -> int:
        food_id: int = self._id
        return food_id

    def get_food_name(self) -> str:
        food_name: str = self._name
        return food_name

    def get_food_stocks(self) -> int | float:
        stocks: int | float = self._stock
        return stocks

    def get_food_category(self) -> str:
        category: str = self._category
        return category

    def get_food_unit(self) -> str:
        unit: str = self._unit
        return unit

    def get_food_tags(self) -> list[Any]:
        food_tags: list[Any] = self._tags
        return food_tags

    def get_food_in_date(self) -> str:
        inDate: str = self._inDate
        return inDate

    def get_food_expiry_date(self) -> str | None:
        return self._expiryDate

    """
    Mutator
    """
    def set_food_name(self, new_name: str) -> None:
        self._name = new_name

    def set_food_tag(self, new_tags: list[Any]) -> None:
        self._tags = new_tags;

    def set_food_stock(self, new_stock: int | float) -> None:
        self.validate_stock(new_stock)
        self._stock = new_stock

    def validate_stock(self, stock: int | float) -> None:
        if isinstance(stock, bool):
            raise TypeError("Stock quantity must be a number.")

        if not isinstance(stock, (int, float)):
            raise TypeError("Stock quantity must be a number.")

        if isinstance(stock, float) and not math.isfinite(stock):
            raise ValueError("Stock quantity must be finite.")

        if stock < 0:
            raise ValueError("Stock quantity cannot be negative.")

    def set_food_category(self, new_category: str) -> None:
        self._category = new_category

    def set_food_unit(self, new_unit: str) -> None:
        self._unit = new_unit

    def set_food_expiry_date(self, expiry_date: str | None) -> None:
        if expiry_date is not None:
            if not isinstance(expiry_date, str):
                raise TypeError("Expiry date must be a YYYY-MM-DD string.")
            try:
                datetime.date.fromisoformat(expiry_date)
            except ValueError as exc:
                raise ValueError(
                    "Expiry date must be in YYYY-MM-DD format."
                ) from exc

        self._expiryDate = expiry_date

    def add_food_tag(self, new_tag: object) -> None:
        if new_tag not in self._tags:
            self._tags.append(new_tag)

    def __str__(self) -> str:
        return (
            f"Food Name: {self._name}, "
            f"category: {self._category}, "
            f"stock: {self._stock}, "
            f"unit: {self._unit}"
        )
