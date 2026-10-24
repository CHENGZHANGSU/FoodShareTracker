# auth/account_manager.py
import hashlib
import hmac
import json
import logging
import secrets
from pathlib import Path
from typing import Any

from util.admin_utils import log_sensitive_access

log = logging.getLogger(__name__)

_PASSWORD_SCHEME = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 600_000
MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    """Hash a password with a unique salt using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PASSWORD_ITERATIONS,
    )
    return (
        f"{_PASSWORD_SCHEME}${_PASSWORD_ITERATIONS}"
        f"${salt.hex()}${password_hash.hex()}"
    )


def verify_password(password: str, stored_password: str) -> bool:
    """Verify a password against a PBKDF2 hash or a legacy plaintext value."""
    if not isinstance(stored_password, str):
        return False

    if not stored_password.startswith(f"{_PASSWORD_SCHEME}$"):
        return hmac.compare_digest(
            password.encode("utf-8"),
            stored_password.encode("utf-8"),
        )

    try:
        scheme, iterations_text, salt_text, expected_hash_text = stored_password.split("$")
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_text)
        expected_hash = bytes.fromhex(expected_hash_text)
    except ValueError:
        return False

    if (
        scheme != _PASSWORD_SCHEME
        or not 1 <= iterations <= 10_000_000
        or len(salt) != 16
        or len(expected_hash) != hashlib.sha256().digest_size
    ):
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_hash, expected_hash)


def _is_password_hash(stored_password: str) -> bool:
    return stored_password.startswith(f"{_PASSWORD_SCHEME}$")


class AccountManager:
    # manage user accounts stored in a JSON file
    def __init__(self, accounts_path: str = "assets/account.json") -> None:
        self._accounts_path: str = accounts_path
        data: dict = self.load_data()
        self._accounts: dict = data.setdefault("accounts", {})
        self._max_login_attempts = 5
        if self._migrate_legacy_passwords():
            self.save_data()

    def _migrate_legacy_passwords(self) -> bool:
        changed = False
        for role_accounts in self._accounts.values():
            for account in role_accounts:
                stored_password = account.get("_account_password", "")
                if (
                    isinstance(stored_password, str)
                    and not _is_password_hash(stored_password)
                ):
                    account["_account_password"] = hash_password(stored_password)
                    changed = True
        return changed

    # load data from JSON file
    def load_data(self) -> dict:
        try:
            with open(self._accounts_path, "r", encoding="utf-8") as f:
                data: Any = json.load(f)
        except FileNotFoundError:
            log.warning(
                "Account file not found at %s. Starting with no accounts.",
                self._accounts_path,
            )
            return {"accounts": {}}
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Account file contains invalid JSON: {self._accounts_path}"
            ) from exc

        if not isinstance(data, dict) or not isinstance(data.get("accounts", {}), dict):
            raise ValueError("Account file must contain an accounts object.")
        for role, accounts in data.get("accounts", {}).items():
            if not isinstance(role, str) or not isinstance(accounts, list):
                raise ValueError("Each account role must contain a list of accounts.")
            if any(not isinstance(account, dict) for account in accounts):
                raise ValueError(f"Accounts for role {role!r} must be objects.")
        return data

    # save data to JSON file
    def save_data(self) -> None:
        accounts_to_save: dict = {"accounts": self._accounts}
        Path(self._accounts_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self._accounts_path, "w", encoding="utf-8") as f:
            json.dump(accounts_to_save, f, indent=4)

    # create account with role-specific properties
    def create_account(
        self,
        name: str,
        phone_number: str,
        password: str,
        selected_role: str,
        **args: Any,
    ) -> str:
        role_ids = {"Client": 1, "Donor": 2, "Food Bank Staff": 3, "Admin": 4}
        if selected_role not in role_ids:
            raise ValueError("Unsupported account role.")
        role_id = role_ids[selected_role]
        role_accounts: list[dict] = self._accounts.setdefault(selected_role, [])
        role_prefix = f"{role_id:02d}-"
        existing_ids = []
        for accounts in self._accounts.values():
            for account in accounts:
                number = account.get("_account_number")
                if (
                    isinstance(number, str)
                    and number.startswith(role_prefix)
                    and number[len(role_prefix):].isdigit()
                ):
                    existing_ids.append(int(number[len(role_prefix):]))
        account_number = f"{role_prefix}{max(existing_ids, default=0) + 1:04d}"
        # shared account properties
        new_account: dict = {
            "_account_number": account_number, # Account number
            "_account_password": hash_password(password),
            "_name": name, # Name
            "_phone_number": phone_number, # Phone number
            "_allow_access": True, # Login access
            "_login_attempts": self._max_login_attempts, # Login attempts, default = 5
        }
        # configure account for different roles
        match selected_role:
            case "Client":
                new_account["_food_constraints"] = args.get("food_constraints", [])
                new_account["_food_orders_rec"] = []
                new_account["_address"] = args.get("address", "")
            case "Donor":
                new_account["_donation_rec"] = []
            case "Admin":
                new_account["_admin_privileges"] = True
        role_accounts.append(new_account)
        self.save_data()
        if selected_role == "Client":
            log_sensitive_access(
                "create",
                "self-registration",
                "Client",
                "client_profile",
                account_number,
            )
        return account_number

    # delete account
    def delete_account(self, name: str, selected_role: str | None = None) -> bool:
        """Disable a matching account without deleting its records."""
        roles: list[str] = [selected_role] if selected_role else list(self._accounts)
        for role in roles:
            for account in self._accounts.get(role, []):
                if account.get("_name") == name:
                    account["_allow_access"] = False
                    self.save_data()
                    if role == "Client":
                        log_sensitive_access(
                            "update",
                            "system",
                            "system",
                            "client_account",
                            str(account.get("_account_number", "unknown")),
                        )
                    return True
        return False

    # search account
    def find_account(self, account_number: str, selected_role: str) -> dict[str, Any] | None:
        return next(
            (
                account
                for account in self._accounts.get(selected_role, [])
                if account.get("_account_number") == account_number
            ),
            None,
        )

    # get account counts by role
    def get_account_counts(self) -> dict[str, int]:
        return {role: len(accounts) for role, accounts in self._accounts.items()}

    def list_accounts(self, selected_role: str | None = None) -> list[dict[str, Any]]:
        """Return account records without exposing mutable storage references."""
        roles = [selected_role] if selected_role else list(self._accounts)
        return [
            {
                **{
                    key: value
                    for key, value in account.items()
                    if key not in {"_account_password", "_previous_role_data"}
                },
                "_role": role,
            }
            for role in roles
            for account in self._accounts.get(role, [])
        ]

    def set_account_access(
        self,
        account_number: str,
        enabled: bool,
        selected_role: str | None = None,
        *,
        actor_id: str = "system",
        actor_role: str = "system",
    ) -> bool:
        """Enable or disable an account by its account number."""
        if not isinstance(enabled, bool):
            raise TypeError("Account access state must be boolean.")
        roles = [selected_role] if selected_role else list(self._accounts)
        for role in roles:
            account = self.find_account(account_number, role)
            if account is not None:
                if role == "Admin" and not enabled:
                    if account_number == actor_id:
                        raise ValueError("You cannot disable your own administrator account.")
                    enabled_admins = [
                        admin
                        for admin in self._accounts.get("Admin", [])
                        if admin.get("_allow_access", True)
                    ]
                    if account.get("_allow_access", True) and len(enabled_admins) <= 1:
                        raise ValueError(
                            "The last enabled administrator cannot be deactivated."
                        )
                account["_allow_access"] = enabled
                if enabled:
                    account["_login_attempts"] = self._max_login_attempts
                self.save_data()
                if role == "Client":
                    log_sensitive_access(
                        "update",
                        actor_id,
                        actor_role,
                        "client_account",
                        account_number,
                    )
                return True
        return False

    def update_account_role(
        self,
        account_number: str,
        new_role: str,
        *,
        actor_id: str = "system",
        actor_role: str = "system",
    ) -> bool:
        role_fields = {
            "Client": ("_address", "_food_constraints", "_food_orders_rec"),
            "Donor": ("_donation_rec",),
            "Admin": ("_admin_privileges",),
        }
        if new_role not in {"Client", "Donor", "Food Bank Staff", "Admin"}:
            raise ValueError("Unsupported account role.")

        old_role = next(
            (
                role
                for role, accounts in self._accounts.items()
                if any(
                    account.get("_account_number") == account_number
                    for account in accounts
                )
            ),
            None,
        )
        if old_role is None or old_role == new_role:
            return False
        if account_number == actor_id:
            raise ValueError("You cannot change your own account role.")

        account = self.find_account(account_number, old_role)
        if account is None:
            return False
        if old_role == "Admin" and account.get("_allow_access", True):
            enabled_admins = [
                admin
                for admin in self._accounts.get("Admin", [])
                if admin.get("_allow_access", True)
            ]
            if len(enabled_admins) <= 1:
                raise ValueError("The last enabled administrator cannot be demoted.")

        role_data = account.setdefault("_previous_role_data", {})
        if not isinstance(role_data, dict):
            raise ValueError("Account role history is invalid.")
        current_fields = role_fields.get(old_role, ())
        role_data[old_role] = {
            field: account.pop(field)
            for field in current_fields
            if field in account
        }

        next_role_data = role_data.pop(new_role, {})
        if not isinstance(next_role_data, dict):
            raise ValueError("Saved account role data is invalid.")
        defaults = {
            "Client": {
                "_address": "",
                "_food_constraints": [],
                "_food_orders_rec": [],
            },
            "Donor": {"_donation_rec": []},
            "Admin": {"_admin_privileges": True},
        }
        for field, default in defaults.get(new_role, {}).items():
            account[field] = next_role_data.get(field, default)

        self._accounts[old_role].remove(account)
        self._accounts.setdefault(new_role, []).append(account)
        self.save_data()
        log_sensitive_access(
            "update",
            actor_id,
            actor_role,
            "account_role",
            account_number,
        )
        return True

    # reset login permissions after successful login
    def reset_login_permissions(self, account: dict[str, Any]) -> None:
        account["_allow_access"] = True
        account["_login_attempts"] = self._max_login_attempts
        self.save_data()
        if self._is_client_account(account):
            log_sensitive_access(
                "update",
                "authentication",
                "system",
                "client_account",
                str(account.get("_account_number", "unknown")),
            )

    # user authentication
    def auth(
        self,
        account_number: str,
        account_password: str,
        selected_role: str,
    ) -> tuple[str, str, dict[str, Any] | int]:
        account: dict[str, Any] | None = self.find_account(account_number, selected_role)
        if not account:
            return "not_found", "Account number not found", {}

        if selected_role == "Client":
            log_sensitive_access(
                "view",
                "authentication",
                "system",
                "client_credentials",
                account_number,
            )

        if not account.get("_allow_access"):
            return "locked", "Account is locked.", {}
        stored_password: str = account.get("_account_password", "")

        if verify_password(account_password, stored_password):
            if not _is_password_hash(stored_password):
                account["_account_password"] = hash_password(account_password)
                self.save_data()
                if selected_role == "Client":
                    log_sensitive_access(
                        "update",
                        "authentication",
                        "system",
                        "client_credentials",
                        account_number,
                    )
            if selected_role == "Client":
                log_sensitive_access(
                    "view",
                    account_number,
                    "Client",
                    "client_profile",
                    account_number,
                )
            if account.get("_login_attempts", self._max_login_attempts) < self._max_login_attempts:
                self.reset_login_permissions(account)
            return "success", "Login successful", account

        attempts: int = max(0, account.get("_login_attempts", 0) - 1)
        account["_login_attempts"] = attempts
        self.save_data()
        if selected_role == "Client":
            log_sensitive_access(
                "update",
                "authentication",
                "system",
                "client_account",
                account_number,
            )

        if attempts == 0:
            self.lock_account(account)
            return "locked", f"Account locked after {self._max_login_attempts} login attempts.", account
        return "failed", "Wrong password", attempts # wrong password

    # lock account after consecutive failed login attempts
    def lock_account(self, account: dict[str, Any]) -> None:
        account["_allow_access"] = False
        self.save_data()
        if self._is_client_account(account):
            log_sensitive_access(
                "update",
                "authentication",
                "system",
                "client_account",
                str(account.get("_account_number", "unknown")),
            )

    # change account password
    def change_account_password(
        self,
        account: dict[str, Any],
        new_password: str,
        *,
        actor_id: str = "system",
        actor_role: str = "system",
    ) -> None:
        if not isinstance(new_password, str) or len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        account["_account_password"] = hash_password(new_password)
        self.save_data()
        if self._is_client_account(account):
            log_sensitive_access(
                "update",
                actor_id,
                actor_role,
                "client_credentials",
                str(account.get("_account_number", "unknown")),
            )

    # update account information
    def update_account_info(
        self,
        account: dict[str, Any],
        *,
        actor_id: str = "system",
        actor_role: str = "system",
        **fields: Any,
    ) -> None:
        if account is None:
            raise ValueError("Account was not found.")
        client_only_fields = {
            "_address",
            "_food_constraints",
            "_food_orders_rec",
        }
        if client_only_fields.intersection(fields) and not self._is_client_account(
            account
        ):
            raise ValueError("Client-only fields can only be updated for client accounts.")
        if "_account_password" in fields:
            fields["_account_password"] = hash_password(fields["_account_password"])
        account.update(fields)
        self.save_data()
        sensitive_fields = {
            "_account_password",
            "_name",
            "_phone_number",
            "_address",
            "_food_constraints",
            "_food_orders_rec",
        }
        if self._is_client_account(account) and sensitive_fields.intersection(fields):
            log_sensitive_access(
                "update",
                actor_id,
                actor_role,
                "client_profile",
                str(account.get("_account_number", "unknown")),
            )

    # update client-specific information
    def update_client_info(
        self,
        account: dict[str, Any],
        entry: str,
        new_entry: Any,
        *,
        actor_id: str = "system",
        actor_role: str = "system",
    ) -> None:
        if account is None:
            raise ValueError("Account was not found.")
        if entry not in {"_food_constraints", "_food_orders_rec", "_address"}:
            raise ValueError(f"Unsupported client field: {entry}")
        if not self._is_client_account(account):
            raise ValueError("Client-only fields can only be updated for client accounts.")
        account[entry] = new_entry
        self.save_data()
        if self._is_client_account(account):
            log_sensitive_access(
                "update",
                actor_id,
                actor_role,
                "client_profile",
                str(account.get("_account_number", "unknown")),
            )

    def _is_client_account(self, account: dict[str, Any]) -> bool:
        return any(
            account is client_account
            for client_account in self._accounts.get("Client", [])
        )
