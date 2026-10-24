"""
This class represent a user within the application, stores all entities and behaviors of a normal user.

@author Su Chengzhang
"""
from abc import ABC, abstractmethod
from enum import StrEnum, auto
from typing import Final

class UserAccess(StrEnum):
    CLIENT = auto()
    DONOR = auto()
    STAFF = auto()
    ADMIN = auto()  


class User(ABC):
    def __init__(
        self,
        registered_account: str,
        password: str,
        name: str,
        contact: str,
        user_access: UserAccess,
    ) -> None:
        self._account_number = registered_account
        self._account_password = password
        self._name = name
        self._contact = contact
        self._user_access: Final = user_access

    def get_account_number(self) -> str:
        return self._account_number

    def get_account_password(self) -> str:
        return self._account_password

    def get_user_name(self) -> str:
        return self._name

    def get_user_contact(self) -> str:
        return self._contact

    def get_user_access(self) -> UserAccess:
        return self._user_access


    def set_account_password(self, new_password: str) -> None:
        self._account_password = new_password

    def set_user_name(self, new_name: str) -> None:
        self._name = new_name

    def set_user_contact(self, new_contact: str) -> None:
        self._contact = new_contact

    @abstractmethod
    def return_user(self) -> "User":
        return self





