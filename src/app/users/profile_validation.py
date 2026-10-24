MAX_ADDRESS_LENGTH = 200


def validate_client_address(address: object) -> str:
    if not isinstance(address, str):
        raise ValueError("Enter a valid address.")

    normalized_address = address.strip()
    if not normalized_address:
        raise ValueError("Address is required.")
    if len(normalized_address) > MAX_ADDRESS_LENGTH:
        raise ValueError(
            f"Address must be {MAX_ADDRESS_LENGTH} characters or fewer."
        )
    if any(
        ord(character) < 32 or ord(character) == 127
        for character in normalized_address
    ):
        raise ValueError("Address cannot contain control characters.")

    return normalized_address
