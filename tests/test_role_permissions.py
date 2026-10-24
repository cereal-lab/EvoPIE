import uuid

import pytest

from evopie import APP
from datalayer import ROLE_ADMIN, ROLE_INSTRUCTOR, ROLE_STUDENT, models


@pytest.fixture
def role_permission_users():
    suffix = uuid.uuid4().hex
    roles = {
        "admin": ROLE_ADMIN,
        "instructor": ROLE_INSTRUCTOR,
        "student": ROLE_STUDENT,
    }
    with APP.app_context():
        models.DB.create_all()
        users = {
            name: models.User(
                email="role-permissions-{}-{}@example.edu".format(suffix, name),
                first_name=name.title(),
                last_name="RoleTest",
                password="test-password",
                role=role,
            )
            for name, role in roles.items()
        }
        models.DB.session.add_all(users.values())
        models.DB.session.commit()
        user_ids = {name: user.id for name, user in users.items()}

    def make_client(name):
        client = APP.test_client()
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


def test_admin_role_includes_instructor_access(role_permission_users):
    make_client, _ = role_permission_users
    admin = models.User(id=24, role=ROLE_ADMIN)

    assert admin.is_admin()
    assert admin.is_instructor()
    assert admin.has_role(ROLE_INSTRUCTOR)
    assert not admin.has_role(ROLE_STUDENT)

    client = make_client("admin")
    assert client.get("/courses-browser").status_code == 200
    assert client.get("/users/").status_code == 200


def test_user_id_one_has_no_admin_access_without_admin_role():
    user = models.User(id=1, role=ROLE_INSTRUCTOR)

    assert user.is_instructor()
    assert not user.is_admin()

    assert user.set_role(ROLE_STUDENT)
    assert user.is_student()
    assert not user.is_admin()
    assert not user.is_instructor()


def test_instructor_cannot_access_admin_user_page(role_permission_users):
    make_client, _ = role_permission_users

    response = make_client("instructor").get("/users/")

    assert response.status_code == 302


def test_student_cannot_use_instructor_only_routes(role_permission_users):
    make_client, _ = role_permission_users

    response = make_client("student").get("/courses-browser")

    assert response.status_code == 403
