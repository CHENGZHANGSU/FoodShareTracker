from app.users.user import User, UserAccess


class Admin(User):
    def __init__(
        self,
        registered_account: str,
        password: str,
        name: str,
        contact: str,
    ) -> None:
        super().__init__(
            registered_account,
            password,
            name,
            contact,
            UserAccess.ADMIN,
        )

    def return_user(self) -> "Admin":
        return self
