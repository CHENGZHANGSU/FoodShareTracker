class UserNotFound(Exception):
    def __str__(self) -> str:
        return "User Not Found."

class FoodNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class OrderNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class DonationNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
