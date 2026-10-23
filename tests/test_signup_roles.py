import uuid

from evopie import APP
from datalayer import ROLE_STUDENT, models


def test_self_service_signup_is_student():
    email = "first-signup-{}@example.edu".format(uuid.uuid4().hex)
    client = APP.test_client()

    response = client.post(
        "/signup",
        json={
            "email": email,
            "firstname": "New",
            "lastname": "User",
            "password": "a-long-signup-passphrase",
            "retype": "a-long-signup-passphrase",
        },
    )

    assert response.status_code == 201
    with APP.app_context():
        user = models.User.query.filter_by(email=email).one()
        assert user.role == ROLE_STUDENT
        models.DB.session.delete(user)
        models.DB.session.commit()
