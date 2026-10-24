"""
This class stores all the foods items with essential time records.

@author Su Chengzhang
@author Low JoeYan
"""
import json, logging
from datetime import date
import math
from pathlib import Path
from typing import Any
from app.food.food_item import FoodItem

log: logging.Logger = logging.getLogger(__name__)

class Inventory:
    def __init__(self, inventory_path: str = "assets/inventory.json") -> None:
        self._inventory: list[Any] = []
        self._inventory_path: str = inventory_path
        self._id: dict[str, int] = {"next_food_id": 1}
        self._minimum_stock: dict[str, int | float] = {}
        self.load_data()
        self.to_object()

    """
    Accessor
    """
    def get_inventory(self) -> list[FoodItem]:
        inventory: list[FoodItem] = self._inventory.copy()
        return inventory

    def get_minimum_stock(self, food_id: int | str) -> int | float | None:
        return self._minimum_stock.get(str(food_id))

    def find_food_by_id(self, food_id: int | str) -> FoodItem | None:
            for food in self._inventory:
                if food.get_food_id() == food_id:
                    return food
            return None

    """
    Mutator
    """
    def set_inventory(self, inventory: list[FoodItem]) -> None:
        if not isinstance(inventory, list):
            raise TypeError("Inventory must be a list.")

        self._inventory = inventory
        self.save_data()
            
    def add_food_to_inventory(self, new_food: FoodItem) -> bool:
        """Add a new food item to inventory."""
        if not isinstance(new_food, FoodItem):
            raise TypeError("New food must be a FoodItem.")

        for food in self._inventory:
            if food.get_food_name().strip().casefold() == (new_food.get_food_name().strip().casefold()):
                return False

        self._inventory.append(new_food)

        food_id: int = new_food.get_food_id()
        if isinstance(food_id, int) and food_id >= self._id["next_food_id"]:
            self._id["next_food_id"] = food_id + 1

        self.save_data()
        return True
            
    def update_food_from_inventory(
        self,
        food_id: int | str,
        **fields: Any,
    ) -> FoodItem:
        """Update an existing food item's fields by ID."""
        allowed_fields: set[str] = {
            "name", "category", "stock", "unit", "tags", "expiry_date"
        }

        invalid_fields: set[str] = set(fields) - allowed_fields
        if invalid_fields:
            raise ValueError(
                f"Unsupported fields: {', '.join(sorted(invalid_fields))}"
            )

        food: FoodItem | None = next(
            (item for item in self._inventory
            if item.get_food_id() == food_id),
            None
        )

        if food is None:
            raise ValueError(f"Food ID {food_id} not found.")

        if "name" in fields:
            if not isinstance(fields["name"], str) or not fields["name"].strip():
                raise ValueError("Food name cannot be empty.")

        if "category" in fields:
            if not isinstance(fields["category"], str) or not fields["category"].strip():
                raise ValueError("Category cannot be empty.")

        if "stock" in fields:
            food.validate_stock(fields["stock"])

        if "unit" in fields:
            if not isinstance(fields["unit"], str) or not fields["unit"].strip():
                raise ValueError("Unit cannot be empty.")

        if "tags" in fields:
            if not isinstance(fields["tags"], list):
                raise TypeError("Tags must be a list.")

        if "expiry_date" in fields:
            expiry_date = fields["expiry_date"]
            if expiry_date is not None and not isinstance(expiry_date, str):
                raise TypeError("Expiry date must be a YYYY-MM-DD string.")
            if expiry_date is not None:
                try:
                    date.fromisoformat(expiry_date)
                except ValueError as exc:
                    raise ValueError(
                        "Expiry date must be in YYYY-MM-DD format."
                    ) from exc

        if "name" in fields:
            food.set_food_name(fields["name"].strip())

        if "category" in fields:
            food.set_food_category(fields["category"])

        if "stock" in fields:
            food.set_food_stock(fields["stock"])

        if "unit" in fields:
            food.set_food_unit(fields["unit"].strip())

        if "tags" in fields:
            food.set_food_tag(fields["tags"])

        if "expiry_date" in fields:
            food.set_food_expiry_date(fields["expiry_date"])

        self.save_data()
        return food

    def to_object(self) -> None:
        for i, food in enumerate(self._inventory):
            if isinstance(food, dict):
                self._inventory[i] = FoodItem(
                    food["_id"],
                    food["_name"],
                    food["_category"],
                    food.get("_stock", 0),
                    food.get("_unit", ""),
                    food.get("_tags", []),
                    food.get("_inDate"),
                    food.get("_expiryDate"),
                )

        if (
            isinstance(self._id.get("next_food_id"), bool)
            or not isinstance(self._id.get("next_food_id"), int)
            or self._id["next_food_id"] < 1
        ):
            self._id["next_food_id"] = 1

    def load_data(self) -> None:
        try:
            with open(self._inventory_path, "r", encoding="utf-8") as f:
                data: Any = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("Inventory file must contain a JSON object.")
            inventory = data.get("inventory", [])
            minimum_stock = data.get("minimum_stock", {})
            if not isinstance(inventory, list):
                raise ValueError("Inventory data must be a list.")
            if not isinstance(minimum_stock, dict):
                raise ValueError("Minimum stock data must be an object.")
            required_fields = {"_id", "_name", "_category"}
            for index, food in enumerate(inventory):
                if not isinstance(food, dict) or not required_fields.issubset(food):
                    raise ValueError(
                        f"Inventory item at index {index} is missing required data."
                    )
                if not isinstance(food["_name"], str) or not isinstance(
                    food["_category"], str
                ):
                    raise ValueError(
                        f"Inventory item at index {index} has invalid text fields."
                    )
            for food_id, threshold in minimum_stock.items():
                if (
                    isinstance(threshold, bool)
                    or not isinstance(threshold, (int, float))
                    or (
                        isinstance(threshold, float)
                        and not math.isfinite(threshold)
                    )
                    or threshold < 0
                ):
                    raise ValueError(
                        f"Minimum stock threshold for food {food_id} is invalid."
                    )

            self._inventory = inventory
            self._id["next_food_id"] = data.get("next_food_id", 1)
            self._minimum_stock = minimum_stock

        except FileNotFoundError:
            log.warning("Inventory file not found. Starting with a clean state.")

        except json.JSONDecodeError as exc:
            log.exception("Inventory JSON is invalid: %s", self._inventory_path)
            raise ValueError(
                f"Inventory file contains invalid JSON: {self._inventory_path}"
            ) from exc

    def save_data(self) -> None:
        inventory_to_save: dict[str, Any] = {
            "inventory": [vars(food) for food in self._inventory],
            "next_food_id": self._id["next_food_id"],
            "minimum_stock": self._minimum_stock,
        }

        path = Path(self._inventory_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(inventory_to_save, f, indent=4)


    def list_food(self) -> list[dict[str, Any]]:
        res: list[dict[str, Any]] = [vars(food) for food in self._inventory]
        for value in res:
            value['_inDate'] = value['_inDate'].split("T")[0] if value['_inDate'] else ""
            value['_tags'] = [str(tag) for tag in (value.get('_tags') or [])]
            value['_expiryDate'] = value['_expiryDate'].split("T")[0] if value['_expiryDate'] else ""
        return res

    def record_incoming_stock(
        self,
        food_id: int | str,
        quantity: int | float,
    ) -> None:
        """Add incoming stock to the inventory total."""
        if isinstance(quantity, bool) or not isinstance(quantity, (int, float)):
            raise TypeError("Quantity must be a number.")
        if isinstance(quantity, float) and not math.isfinite(quantity):
            raise ValueError("Quantity must be finite.")

        if quantity <= 0:
            raise ValueError("Incoming quantity must be positive.")

        food: FoodItem | None = self.find_food_by_id(food_id)
        if food is None:
            raise ValueError("Food item not found.")

        self.adjust_stock(
            food_id,
            food.get_food_stocks() + quantity,
            "Incoming stock",
        )

        log.info(
            "Incoming stock saved: food_id=%s, quantity=%s",
            food_id,
            quantity,
        )



    def adjust_stock(
        self,
        food_id: int | str,
        new_quantity: int | float,
        reason: str,
    ) -> bool:
        """Set an item's total stock quantity."""
        if isinstance(new_quantity, bool) or not isinstance(new_quantity, (int, float)):
            raise TypeError("Quantity must be a number.")
        if isinstance(new_quantity, float) and not math.isfinite(new_quantity):
            raise ValueError("Quantity must be finite.")
        if new_quantity < 0:
            raise ValueError("Quantity must be non-negative.")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Adjustment reason is required.")

        food: FoodItem | None = self.find_food_by_id(food_id)
        if food is None:
            raise ValueError("Food item not found.")

        old_quantity: int | float = food.get_food_stocks()

        food.set_food_stock(new_quantity)

        try:
            self.save_data()
        except Exception:
            food.set_food_stock(old_quantity)
            raise

        log.info(
            "Inventory adjustment saved: food_id=%s, old_quantity=%s, "
            "new_quantity=%s, reason=%s",
            food_id, old_quantity, new_quantity, reason.strip(),
        )
        return True



    def set_minimum_stock(self, food_id: int | str, threshold: int | float) -> None:
        """Configure the low-stock threshold for a food item."""
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
            raise TypeError("Threshold must be a number.")
        if isinstance(threshold, float) and not math.isfinite(threshold):
            raise ValueError("Threshold must be finite.")

        if threshold < 0:
            raise ValueError("Threshold must be non-negative.")

        if self.find_food_by_id(food_id) is None:
            raise ValueError("Food item not found.")

        self._minimum_stock[str(food_id)] = threshold
        self.save_data()


    def get_low_stock_foods(self) -> list[FoodItem]:
        """Return food items whose stock is below their minimum threshold."""
        low_stock_foods: list[FoodItem] = []

        for food in self._inventory:
            food_id: str = str(food.get_food_id())

            if food_id in self._minimum_stock:
                if food.get_food_stocks() < self._minimum_stock[food_id]:
                    low_stock_foods.append(food)

        return low_stock_foods

    def get_expired_foods(self, today: date | None = None) -> list[FoodItem]:
        """Return food items whose expiry date is before the given date."""
        current_date = today if today is not None else date.today()
        expired_foods: list[FoodItem] = []
        for food in self._inventory:
            expiry_date = food.get_food_expiry_date()
            if expiry_date is not None and date.fromisoformat(expiry_date) < current_date:
                expired_foods.append(food)
        return expired_foods

    def allocate_stock(
        self,
        food_id: int | str,
        quantity: int | float,
    ) -> bool:
        """Deduct an order quantity from the inventory total."""

        if isinstance(quantity, bool) or not isinstance(quantity, (int, float)):
            raise TypeError("Quantity must be a number.")
        if isinstance(quantity, float) and not math.isfinite(quantity):
            raise ValueError("Quantity must be finite.")

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        food: FoodItem | None = self.find_food_by_id(food_id)

        if food is None:
            raise ValueError("Food item not found.")

        original_stock: int | float = food.get_food_stocks()
        if original_stock < quantity:
            raise ValueError("Not enough stock available.")

        food.set_food_stock(original_stock - quantity)
        try:
            self.save_data()
        except Exception:
            food.set_food_stock(original_stock)
            raise

        return True
