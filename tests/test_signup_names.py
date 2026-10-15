import pytest

from evopie import APP


@pytest.mark.parametrize(
    "first_name,last_name",
    [
        (None, "Student"),
        ("Student", None),
        ("   ", "Student"),
        ("Student", "  "),
        ("<b> </b>", "Student"),
        (123, "Student"),
    ],
)
def test_signup_api_requires_nonblank_names(first_name, last_name):
    response = APP.test_client().post(
        "/signup",
        json={
            "email": "student@example.edu",
            "firstname": first_name,
            "lastname": last_name,
            "password": "password",
            "retype": "password",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "First and last name are required."


def test_signup_form_shows_name_validation_error():
    response = APP.test_client().post(
        "/signup",
        data={
            "email": "student@example.edu",
            "firstname": " ",
            "lastname": "Student",
            "password": "password",
            "retype": "password",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"First and last name are required." in response.data
