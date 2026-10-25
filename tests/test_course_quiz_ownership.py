import uuid

import pytest

from evopie import APP
from datalayer import ROLE_ADMIN, ROLE_INSTRUCTOR, models


@pytest.fixture
def course_quiz_ownership_context():
    suffix = uuid.uuid4().hex
    with APP.app_context():
        models.DB.create_all()
        users = {
            "instructor_a": models.User(
                email="record-owner-a-{}@example.edu".format(suffix),
                first_name="Instructor",
                last_name="A",
                password="test-password",
                role=ROLE_INSTRUCTOR,
            ),
            "instructor_b": models.User(
                email="record-owner-b-{}@example.edu".format(suffix),
                first_name="Instructor",
                last_name="B",
                password="test-password",
                role=ROLE_INSTRUCTOR,
            ),
            "admin": models.User(
                email="record-owner-admin-{}@example.edu".format(suffix),
                first_name="Record",
                last_name="Admin",
                password="test-password",
                role=ROLE_ADMIN,
            ),
        }
        models.DB.session.add_all(users.values())
        models.DB.session.flush()

        courses = {
            name: models.Course(
                name="COURSE-{}-{}".format(name.upper(), suffix),
                title="Course {} {}".format(name, suffix),
                description="Test course {}".format(name),
                instructor_id=users[user_name].id,
            )
            for name, user_name in (
                ("a", "instructor_a"),
                ("b", "instructor_b"),
                ("admin", "admin"),
            )
        }
        quizzes = {
            name: models.Quiz(
                title="Quiz {} {}".format(name, suffix),
                description="Test quiz {}".format(name),
                author_id=users[user_name].id,
                status="HIDDEN",
            )
            for name, user_name in (
                ("a", "instructor_a"),
                ("b", "instructor_b"),
                ("admin", "admin"),
            )
        }
        quizzes["a"].courses.append(courses["a"])
        quizzes["b"].courses.append(courses["b"])
        quizzes["admin"].courses.append(courses["admin"])
        models.DB.session.add_all(list(courses.values()) + list(quizzes.values()))
        models.DB.session.commit()

        ids = {
            "users": {name: user.id for name, user in users.items()},
            "courses": {name: course.id for name, course in courses.items()},
            "quizzes": {name: quiz.id for name, quiz in quizzes.items()},
            "course_titles": {name: course.title for name, course in courses.items()},
            "course_names": {name: course.name for name, course in courses.items()},
            "quiz_titles": {name: quiz.title for name, quiz in quizzes.items()},
        }

    def make_client(name):
        client = APP.test_client()
        with client.session_transaction() as session:
            session["_user_id"] = str(ids["users"][name])
            session["_fresh"] = True
        return client

    yield make_client, ids

    with APP.app_context():
        user_ids = list(ids["users"].values())
        quizzes = models.Quiz.query.filter(
            models.Quiz.author_id.in_(user_ids)
        ).all()
        for quiz in quizzes:
            quiz.courses.clear()
            quiz.quiz_questions.clear()
        for quiz in quizzes:
            models.DB.session.delete(quiz)
        courses = models.Course.query.filter(
            models.Course.instructor_id.in_(user_ids)
        ).all()
        for course in courses:
            course.students.clear()
            models.DB.session.delete(course)
        models.DB.session.flush()
        models.User.query.filter(models.User.id.in_(user_ids)).delete(
            synchronize_session=False
        )
        models.DB.session.commit()


def test_instructor_cannot_manage_another_instructors_course_or_quiz(
    course_quiz_ownership_context,
):
    make_client, ids = course_quiz_ownership_context
    instructor = make_client("instructor_a")
    foreign_course_id = ids["courses"]["b"]
    foreign_quiz_id = ids["quizzes"]["b"]

    assert instructor.get("/courses-browser").status_code == 200
    course_page = instructor.get("/courses-browser")
    assert ids["course_names"]["a"].encode() in course_page.data
    assert ids["course_names"]["b"].encode() not in course_page.data
    quiz_page = instructor.get("/quizzes-browser")
    assert ids["quiz_titles"]["a"].encode() in quiz_page.data
    assert ids["quiz_titles"]["b"].encode() not in quiz_page.data
    assert instructor.get("/course-editor/{}".format(foreign_course_id)).status_code == 404
    assert instructor.get("/courses/{}/student-list".format(foreign_course_id)).status_code == 404
    assert instructor.put(
        "/courses/{}".format(foreign_course_id),
        json={"name": "Changed", "title": "Changed", "description": "Changed"},
    ).status_code == 404

    quiz_list = instructor.get("/quizzes")
    assert quiz_list.status_code == 200
    assert [quiz["id"] for quiz in quiz_list.get_json()] == [ids["quizzes"]["a"]]
    assert instructor.get("/quizzes/{}".format(foreign_quiz_id)).status_code == 404
    assert instructor.put(
        "/quizzes/{}".format(foreign_quiz_id),
        json={"title": "Changed", "description": "Changed"},
    ).status_code == 404
    assert instructor.delete("/quizzes/{}".format(foreign_quiz_id)).status_code == 404
    assert instructor.get("/quizzes/{}/status".format(foreign_quiz_id)).status_code == 404
    assert instructor.post(
        "/quizzes/{}/status".format(foreign_quiz_id), json={"status": "STEP1"}
    ).status_code == 404
    assert instructor.post(
        "/quizzes/{}/deadline_driven".format(foreign_quiz_id),
        json={"deadline_driven": "True"},
    ).status_code == 404
    assert instructor.post("/quiz/{}/settings".format(foreign_quiz_id), json={}).status_code == 404
    assert instructor.get("/quizzes/{}/responses".format(foreign_quiz_id)).status_code == 404
    assert instructor.get("/quiz-editor/{}".format(foreign_quiz_id)).status_code == 404
    assert instructor.get("/quiz-copy/{}".format(foreign_quiz_id)).status_code == 404
    assert instructor.get("/quiz-configuration/{}".format(foreign_quiz_id)).status_code == 404
    assert instructor.post(
        "/quiz-configuration/{}".format(foreign_quiz_id), json={}
    ).status_code == 404
    assert instructor.get(
        "/quiz-question-selector-1/{}".format(foreign_quiz_id)
    ).status_code == 404
    assert instructor.get(
        "/quiz/{}/{}/grades".format(foreign_quiz_id, foreign_course_id)
    ).status_code == 404
    assert instructor.get(
        "/quiz/{}/{}/justification/histogram".format(foreign_quiz_id, foreign_course_id)
    ).status_code == 404
    assert instructor.get(
        "/quiz/{}/{}/{}/step3_grade".format(
            foreign_quiz_id, foreign_course_id, ids["users"]["instructor_a"]
        )
    ).status_code == 404

    assert instructor.post(
        "/course-editor/{}".format(ids["courses"]["a"]),
        json={"selected_quizzes": [foreign_quiz_id]},
    ).status_code == 404
    assert instructor.post(
        "/quizzes/{}/course".format(ids["quizzes"]["a"]),
        json={"course_id": foreign_course_id},
    ).status_code == 404

    with APP.app_context():
        foreign_course = models.Course.query.get(foreign_course_id)
        foreign_quiz = models.Quiz.query.get(foreign_quiz_id)
        own_course = models.Course.query.get(ids["courses"]["a"])
        own_quiz = models.Quiz.query.get(ids["quizzes"]["a"])
        assert foreign_course.title == ids["course_titles"]["b"]
        assert foreign_quiz.title == ids["quiz_titles"]["b"]
        assert own_quiz.courses == [own_course]
        assert foreign_quiz.courses == [foreign_course]


def test_instructor_can_manage_own_course_and_quiz(course_quiz_ownership_context):
    make_client, ids = course_quiz_ownership_context
    instructor = make_client("instructor_a")
    course_id = ids["courses"]["a"]
    quiz_id = ids["quizzes"]["a"]

    assert instructor.get("/course-editor/{}".format(course_id)).status_code == 200
    assert instructor.get("/quiz-editor/{}".format(quiz_id)).status_code == 200
    assert instructor.get("/quiz-configuration/{}".format(quiz_id)).status_code == 200
    assert instructor.put(
        "/courses/{}".format(course_id),
        json={"name": "Updated course", "title": "Updated course", "description": "Updated"},
    ).status_code == 200
    assert instructor.get("/quizzes/{}".format(quiz_id)).status_code == 200
    assert instructor.put(
        "/quizzes/{}".format(quiz_id),
        json={"title": "Updated quiz", "description": "Updated"},
    ).status_code == 200
    assert instructor.get("/quizzes/{}/status".format(quiz_id)).status_code == 200
    assert instructor.post(
        "/quiz/{}/settings".format(quiz_id), json={"num_justifications_shown": 5}
    ).status_code == 200
    assert instructor.post(
        "/quizzes/{}/deadline_driven".format(quiz_id),
        json={"deadline_driven": "True"},
    ).status_code == 200
    assert instructor.post(
        "/course-editor/{}".format(course_id),
        json={"selected_quizzes": [quiz_id]},
    ).status_code == 200
    assert instructor.post(
        "/quizzes/{}/course".format(quiz_id), json={"course_id": course_id}
    ).status_code == 200

    copied_quiz = instructor.get("/quiz-copy/{}".format(quiz_id))
    assert copied_quiz.status_code == 302
    with APP.app_context():
        copied = models.Quiz.query.filter_by(
            author_id=ids["users"]["instructor_a"], title="Updated quiz"
        ).all()
        assert len(copied) == 2
        assert all(quiz.author_id == ids["users"]["instructor_a"] for quiz in copied)

    assert instructor.delete("/quizzes/{}".format(quiz_id)).status_code == 200


def test_admin_can_manage_courses_and_quizzes_from_all_instructors(
    course_quiz_ownership_context,
):
    make_client, ids = course_quiz_ownership_context
    admin = make_client("admin")
    course_id = ids["courses"]["b"]
    quiz_id = ids["quizzes"]["b"]

    courses_page = admin.get("/courses-browser")
    quizzes_page = admin.get("/quizzes-browser")
    assert courses_page.status_code == 200
    assert ids["course_names"]["a"].encode() in courses_page.data
    assert ids["course_names"]["b"].encode() in courses_page.data
    assert quizzes_page.status_code == 200
    assert ids["quiz_titles"]["a"].encode() in quizzes_page.data
    assert ids["quiz_titles"]["b"].encode() in quizzes_page.data
    quiz_list = admin.get("/quizzes")
    assert quiz_list.status_code == 200
    assert {quiz["id"] for quiz in quiz_list.get_json()} >= set(ids["quizzes"].values())
    assert admin.get("/course-editor/{}".format(course_id)).status_code == 200
    assert admin.get("/courses/{}/student-list".format(course_id)).status_code == 200
    assert admin.get("/quiz-editor/{}".format(quiz_id)).status_code == 200
    assert admin.get("/quiz-configuration/{}".format(quiz_id)).status_code == 200
    assert admin.put(
        "/courses/{}".format(course_id),
        json={"name": "Admin course update", "title": "Admin course update", "description": "Updated"},
    ).status_code == 200
    assert admin.put(
        "/quizzes/{}".format(quiz_id),
        json={"title": "Admin quiz update", "description": "Updated"},
    ).status_code == 200
    assert admin.post(
        "/quizzes/{}/course".format(quiz_id),
        json={"course_id": ids["courses"]["a"]},
    ).status_code == 200
    assert admin.get("/quizzes/{}/status".format(quiz_id)).status_code == 200
