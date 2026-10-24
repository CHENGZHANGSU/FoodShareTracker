import pytest

from app.users.profile_validation import (
    MAX_ADDRESS_LENGTH,
    validate_client_address,
)


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("  12 Main Street, Unit 4  ", "12 Main Street, Unit 4"),
        ("Apt #3, 10-12 King St.", "Apt #3, 10-12 King St."),
        ("東京都新宿区", "東京都新宿区"),
    ],
)
def test_validate_client_address_accepts_and_trims_addresses(
    address: str,
    expected: str,
) -> None:
    assert validate_client_address(address) == expected


@pytest.mark.parametrize(
    ("address", "message"),
    [
        ("", "required"),
        ("   ", "required"),
        ("A" * (MAX_ADDRESS_LENGTH + 1), "characters or fewer"),
        ("10 Main\nStreet", "control characters"),
        (None, "valid address"),
    ],
)
def test_validate_client_address_rejects_invalid_values(
    address: str | None,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_client_address(address)


def test_validate_client_address_accepts_maximum_length() -> None:
    address = "A" * MAX_ADDRESS_LENGTH
    assert validate_client_address(address) == address
