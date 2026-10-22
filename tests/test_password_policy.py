import pytest

from evopie.passwords import password_validation_error


@pytest.mark.parametrize("password", [None, "", "short", "password123"])
def test_password_policy_rejects_missing_or_short_passwords(password):
    assert password_validation_error(password) is not None


@pytest.mark.parametrize(
    "password",
    ["a sufficiently long passphrase", "  a long passphrase with spaces  ", "long-unicode-passphrase-雪"],
)
def test_password_policy_accepts_long_passphrases(password):
    assert password_validation_error(password) is None


def test_signup_api_rejects_short_password():
    from evopie import APP

    response = APP.test_client().post(
        "/signup",
        json={
            "email": "password-policy@example.edu",
            "firstname": "Test",
            "lastname": "User",
            "password": "password123",
            "retype": "password123",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Password must be at least 15 characters long."


def test_admin_password_change_api_rejects_short_password():
    from evopie import APP

    response = APP.test_client().post(
        "/users/1/password",
        json={"password": "password123"},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Password must be at least 15 characters long."


def test_signup_form_shows_short_password_error():
    from evopie import APP

    response = APP.test_client().post(
        "/signup",
        data={
            "email": "password-policy@example.edu",
            "firstname": "Test",
            "lastname": "User",
            "password": "short",
            "retype": "short",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Password must be at least 15 characters long." in response.data
