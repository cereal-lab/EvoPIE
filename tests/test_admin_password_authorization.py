import uuid

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from evopie import APP
from datalayer import ROLE_ADMIN, ROLE_INSTRUCTOR, ROLE_STUDENT, models


CURRENT_PASSWORD = "a-long-existing-password"
NEW_PASSWORD = "a-long-new-password-for-user"


@pytest.fixture
def password_change_users():
    suffix = uuid.uuid4().hex
    roles = {
        "admin": ROLE_ADMIN,
        "instructor": ROLE_INSTRUCTOR,
        "student": ROLE_STUDENT,
        "target": ROLE_STUDENT,
    }
    with APP.app_context():
        models.DB.create_all()
        users = {
            name: models.User(
                email="password-change-{}-{}@example.edu".format(suffix, name),
                first_name=name.title(),
                last_name="PasswordTest",
                password=generate_password_hash(CURRENT_PASSWORD),
                role=role,
            )
            for name, role in roles.items()
        }
        models.DB.session.add_all(users.values())
        models.DB.session.commit()
        user_ids = {name: user.id for name, user in users.items()}

    def make_client(name=None):
        client = APP.test_client()
        if name is not None:
            with client.session_transaction() as session:
                session["_user_id"] = str(user_ids[name])
                session["_fresh"] = True
        return client

    yield make_client, user_ids

    with APP.app_context():
        models.User.query.filter(models.User.id.in_(user_ids.values())).delete(
            synchronize_session=False
        )
        models.DB.session.commit()


def get_target_password_hash(user_id):
    with APP.app_context():
        user = models.User.query.get(user_id)
        return user.password


def test_anonymous_user_cannot_change_a_password(password_change_users):
    make_client, user_ids = password_change_users
    original_hash = get_target_password_hash(user_ids["target"])

    response = make_client().post(
        "/users/{}/password".format(user_ids["target"]),
        json={"password": NEW_PASSWORD},
    )

    assert response.status_code in (302, 401)
    assert get_target_password_hash(user_ids["target"]) == original_hash


@pytest.mark.parametrize("role", ["instructor", "student"])
def test_non_admin_cannot_change_another_users_password(password_change_users, role):
    make_client, user_ids = password_change_users
    original_hash = get_target_password_hash(user_ids["target"])

    response = make_client(role).post(
        "/users/{}/password".format(user_ids["target"]),
        json={"password": NEW_PASSWORD},
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == (
        "You are not allowed to change user passwords."
    )
    assert get_target_password_hash(user_ids["target"]) == original_hash


def test_non_admin_form_request_gets_forbidden(password_change_users):
    make_client, user_ids = password_change_users
    original_hash = get_target_password_hash(user_ids["target"])

    response = make_client("instructor").post(
        "/users/{}/password".format(user_ids["target"]),
        data={"password": NEW_PASSWORD},
    )

    assert response.status_code == 403
    assert get_target_password_hash(user_ids["target"]) == original_hash


def test_admin_can_change_a_password(password_change_users):
    make_client, user_ids = password_change_users

    response = make_client("admin").post(
        "/users/{}/password".format(user_ids["target"]),
        json={"password": NEW_PASSWORD},
    )

    assert response.status_code == 302
    updated_hash = get_target_password_hash(user_ids["target"])
    assert check_password_hash(updated_hash, NEW_PASSWORD)
    assert not check_password_hash(updated_hash, CURRENT_PASSWORD)


def test_admin_password_change_still_enforces_password_policy(password_change_users):
    make_client, user_ids = password_change_users
    original_hash = get_target_password_hash(user_ids["target"])

    response = make_client("admin").post(
        "/users/{}/password".format(user_ids["target"]),
        json={"password": "short"},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == (
        "Password must be at least 15 characters long."
    )
    assert get_target_password_hash(user_ids["target"]) == original_hash
