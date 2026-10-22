"""Password validation helpers."""

MIN_PASSWORD_LENGTH = 15


def password_validation_error(password):
    """Return a validation message when a password does not meet policy."""
    if not isinstance(password, str) or not password:
        return "Password is required."
    if len(password) < MIN_PASSWORD_LENGTH:
        return "Password must be at least 15 characters long."
    return None
