import os
import sqlite3
import subprocess
import sys

from werkzeug.security import check_password_hash


INITIAL_ADMIN_PASSWORD = "a-long-initial-admin-password"


def run_db_init(database_path, admin_email="", admin_password=""):
    env = os.environ.copy()
    env.update(
        {
            "FLASK_APP": "evopie/__init__.py",
            "EVOPIE_SECRET_KEY": "test-only-session-key",
            "EVOPIE_DATABASE_URI": "sqlite:///{}".format(database_path),
            "EVOPIE_ADMIN_EMAIL": admin_email,
            "EVOPIE_ADMIN_PASSWORD": admin_password,
        }
    )
    return subprocess.run(
        [sys.executable, "-m", "flask", "DB-init"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )


def test_empty_database_needs_admin_environment_values(tmp_path):
    database_path = str(tmp_path / "empty.sqlite")

    result = run_db_init(database_path)

    assert result.returncode != 0
    assert "EVOPIE_ADMIN_EMAIL and EVOPIE_ADMIN_PASSWORD" in result.stderr


def test_db_init_rejects_a_weak_initial_admin_password(tmp_path):
    database_path = str(tmp_path / "weak-admin-password.sqlite")

    result = run_db_init(database_path, "admin@example.edu", "weak")

    assert result.returncode != 0
    assert "at least 15 characters" in result.stderr


def test_db_init_creates_admin_once_and_does_not_reset_password(tmp_path):
    database_path = str(tmp_path / "initial-admin.sqlite")
    email = "admin@example.edu"

    result = run_db_init(database_path, email, INITIAL_ADMIN_PASSWORD)

    assert result.returncode == 0, result.stderr
    with sqlite3.connect(database_path) as connection:
        admin = connection.execute(
            "SELECT email, first_name, last_name, password, role FROM user"
        ).fetchone()

    assert admin[0:3] == (email, "EvoPIE", "Admin")
    assert admin[4] == "ADMIN"
    assert check_password_hash(admin[3], INITIAL_ADMIN_PASSWORD)

    repeated_init = run_db_init(database_path, email, "a-different-admin-password")
    assert repeated_init.returncode == 0, repeated_init.stderr

    with sqlite3.connect(database_path) as connection:
        users = connection.execute("SELECT email, password FROM user").fetchall()

    assert len(users) == 1
    assert users[0][0] == email
    assert check_password_hash(users[0][1], INITIAL_ADMIN_PASSWORD)
