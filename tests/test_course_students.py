import io
import uuid

import pytest

from evopie import APP
from datalayer import ROLE_INSTRUCTOR, ROLE_STUDENT, models


@pytest.fixture
def course_student_context():
    suffix = uuid.uuid4().hex
    instructor_email = "instructor-{}@example.edu".format(suffix)
    student_email = "student-{}@example.edu".format(suffix)

    with APP.app_context():
        models.DB.create_all()
        instructor = models.User(
            email=instructor_email,
            first_name="Course",
            last_name="Owner",
            password="test-password",
            role=ROLE_INSTRUCTOR,
        )
        models.DB.session.add(instructor)
        models.DB.session.flush()
        course = models.Course(
            name="TEST 101",
            title="Test Course",
            description="Test course for roster management",
            instructor_id=instructor.id,
        )
        models.DB.session.add(course)
        models.DB.session.commit()
        course_id = course.id
        instructor_id = instructor.id

    client = APP.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(instructor_id)
        session["_fresh"] = True

    yield client, course_id, student_email

    with APP.app_context():
        course = models.Course.query.get(course_id)
        if course is not None:
            course.students.clear()
            models.DB.session.delete(course)
        student = models.User.query.filter_by(email=student_email).first()
        if student is not None:
            models.DB.session.delete(student)
        instructor = models.User.query.filter_by(email=instructor_email).first()
        if instructor is not None:
            models.DB.session.delete(instructor)
        models.DB.session.commit()


def test_add_student_by_email(course_student_context):
    client, course_id, student_email = course_student_context

    response = client.post(
        "/courses/{}/student-list".format(course_id),
        data={"action": "add_student", "email": student_email},
    )

    assert response.status_code == 302
    with APP.app_context():
        course = models.Course.query.get(course_id)
        student = models.User.query.filter_by(email=student_email).one()
        assert student.role == ROLE_STUDENT
        assert student in course.students
        assert student.password is None


def test_adding_an_already_enrolled_student_does_not_duplicate(course_student_context):
    client, course_id, student_email = course_student_context

    with APP.app_context():
        course = models.Course.query.get(course_id)
        student = models.User(
            email=student_email,
            first_name="Test",
            last_name="Student",
            role=ROLE_STUDENT,
        )
        course.students.append(student)
        models.DB.session.commit()

    response = client.post(
        "/courses/{}/student-list".format(course_id),
        data={"action": "add_student", "email": student_email},
    )

    assert response.status_code == 302
    with APP.app_context():
        course = models.Course.query.get(course_id)
        assert len([student for student in course.students if student.email == student_email]) == 1


def test_csv_reupload_deduplicates_student_emails(course_student_context):
    client, course_id, student_email = course_student_context

    response = client.post(
        "/courses/{}/student-list".format(course_id),
        data={
            "action": "replace_csv",
            "csvfile": (io.BytesIO((student_email + "\n" + student_email).encode("utf-8")), "students.csv"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    with APP.app_context():
        course = models.Course.query.get(course_id)
        assert len([student for student in course.students if student.email == student_email]) == 1


def test_remove_student_from_course(course_student_context):
    client, course_id, student_email = course_student_context

    with APP.app_context():
        course = models.Course.query.get(course_id)
        student = models.User(
            email=student_email,
            first_name="Test",
            last_name="Student",
            role=ROLE_STUDENT,
        )
        course.students.append(student)
        models.DB.session.commit()
        student_id = student.id

    response = client.post(
        "/courses/{}/student-list".format(course_id),
        data={"action": "remove_student", "student_id": str(student_id)},
    )

    assert response.status_code == 302
    with APP.app_context():
        course = models.Course.query.get(course_id)
        assert all(student.id != student_id for student in course.students)
        assert models.User.query.get(student_id) is not None
