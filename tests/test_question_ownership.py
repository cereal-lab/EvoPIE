import uuid

import pytest

from evopie import APP
from datalayer import ROLE_ADMIN, ROLE_INSTRUCTOR, models


@pytest.fixture
def question_ownership_context():
    suffix = uuid.uuid4().hex
    with APP.app_context():
        models.DB.create_all()
        users = {
            "instructor_a": models.User(
                email="question-owner-a-{}@example.edu".format(suffix),
                first_name="Instructor",
                last_name="A",
                role=ROLE_INSTRUCTOR,
            ),
            "instructor_b": models.User(
                email="question-owner-b-{}@example.edu".format(suffix),
                first_name="Instructor",
                last_name="B",
                role=ROLE_INSTRUCTOR,
            ),
            "admin": models.User(
                email="question-owner-admin-{}@example.edu".format(suffix),
                first_name="Question",
                last_name="Admin",
                role=ROLE_ADMIN,
            ),
        }
        models.DB.session.add_all(users.values())
        models.DB.session.flush()

        questions = {
            name: models.Question(
                title="Question {} {}".format(name, suffix),
                stem="Question stem {}".format(name),
                answer="Correct answer {}".format(name),
                author_id=users[user_name].id,
            )
            for name, user_name in (("a", "instructor_a"), ("b", "instructor_b"))
        }
        distractors = {
            name: models.Distractor(
                answer="Wrong answer {}".format(name),
                justification="Why answer {} is wrong".format(name),
                author_id=questions[name].author_id,
            )
            for name in ("a", "b")
        }
        for name, question in questions.items():
            question.distractors.append(distractors[name])
        student_distractor = models.InvalidatedDistractor(
            answer="Student suggestion",
            justification="Student reason",
            author_id=users["instructor_b"].id,
        )
        questions["b"].invalidated_distractors.append(student_distractor)

        quizzes = {
            "instructor_a": models.Quiz(
                title="Quiz A {}".format(suffix),
                description="Quiz A",
                author_id=users["instructor_a"].id,
            ),
            "instructor_b": models.Quiz(
                title="Quiz B {}".format(suffix),
                description="Quiz B",
                author_id=users["instructor_b"].id,
            ),
            "admin": models.Quiz(
                title="Admin quiz {}".format(suffix),
                description="Admin quiz",
                author_id=users["admin"].id,
            ),
        }
        quiz_question_b = models.QuizQuestion(question=questions["b"])
        quiz_question_b.distractors.append(distractors["b"])
        quizzes["instructor_b"].quiz_questions.append(quiz_question_b)
        models.DB.session.add_all(
            list(questions.values())
            + list(quizzes.values())
            + [quiz_question_b, student_distractor]
        )
        models.DB.session.commit()

        ids = {
            "users": {name: user.id for name, user in users.items()},
            "questions": {name: question.id for name, question in questions.items()},
            "distractors": {name: distractor.id for name, distractor in distractors.items()},
            "quizzes": {name: quiz.id for name, quiz in quizzes.items()},
            "quiz_questions": {"b": quiz_question_b.id},
            "student_distractor": student_distractor.id,
        }

    def make_client(name):
        client = APP.test_client()
        with client.session_transaction() as session:
            session["_user_id"] = str(ids["users"][name])
            session["_fresh"] = True
        return client

    yield make_client, ids

    with APP.app_context():
        question_ids = list(ids["questions"].values())
        quiz_ids = list(ids["quizzes"].values())
        for quiz in models.Quiz.query.filter(models.Quiz.id.in_(quiz_ids)).all():
            quiz.quiz_questions.clear()
        for quiz_question in models.QuizQuestion.query.filter(
            models.QuizQuestion.question_id.in_(question_ids)
        ).all():
            quiz_question.distractors.clear()
            models.DB.session.delete(quiz_question)
        models.DB.session.flush()
        models.Distractor.query.filter(
            models.Distractor.question_id.in_(question_ids)
        ).delete(synchronize_session=False)
        models.InvalidatedDistractor.query.filter(
            models.InvalidatedDistractor.question_id.in_(question_ids)
        ).delete(synchronize_session=False)
        models.Question.query.filter(models.Question.id.in_(question_ids)).delete(
            synchronize_session=False
        )
        models.Quiz.query.filter(models.Quiz.id.in_(quiz_ids)).delete(
            synchronize_session=False
        )
        models.User.query.filter(
            models.User.id.in_(ids["users"].values())
        ).delete(synchronize_session=False)
        models.DB.session.commit()


def test_question_lists_and_selector_are_scoped_to_instructor(
    question_ownership_context,
):
    make_client, ids = question_ownership_context
    instructor = make_client("instructor_a")
    admin = make_client("admin")

    instructor_questions = instructor.get("/questions")
    admin_questions = admin.get("/questions")
    instructor_browser = instructor.get("/questions-browser")
    selector = instructor.get(
        "/quiz-question-selector-1/{}?iid={}".format(
            ids["quizzes"]["instructor_a"], ids["users"]["instructor_b"]
        )
    )

    assert instructor_questions.status_code == 200
    assert {question["id"] for question in instructor_questions.json} == {
        ids["questions"]["a"]
    }
    assert admin_questions.status_code == 200
    assert set(ids["questions"].values()).issubset(
        {question["id"] for question in admin_questions.json}
    )
    assert instructor.get("/quizquestions").status_code == 200
    assert ids["quiz_questions"]["b"] not in {
        question["id"] for question in instructor.get("/quizquestions").json
    }
    assert instructor_browser.status_code == 200
    assert b"Question a" in instructor_browser.data
    assert b"Question b" not in instructor_browser.data
    assert selector.status_code == 200
    assert b"Question a" in selector.data
    assert b"Question b" not in selector.data


def test_instructor_cannot_access_another_instructors_question_or_distractor(
    question_ownership_context,
):
    make_client, ids = question_ownership_context
    instructor = make_client("instructor_a")
    question_id = ids["questions"]["b"]
    distractor_id = ids["distractors"]["b"]
    quiz_id = ids["quizzes"]["instructor_a"]

    assert instructor.get("/questions/{}".format(question_id)).status_code == 404
    quiz_question_id = ids["quiz_questions"]["b"]
    assert instructor.get("/quizquestions/{}".format(quiz_question_id)).status_code == 404
    assert instructor.delete("/quizquestions/{}".format(quiz_question_id)).status_code == 404
    assert instructor.put(
        "/quizquestions/{}".format(quiz_question_id),
        json={"qid": ids["questions"]["a"], "distractors_ids": [ids["distractors"]["a"]]},
    ).status_code == 404
    assert instructor.post(
        "/quizquestions",
        json={"qid": question_id, "distractors_ids": [distractor_id]},
    ).status_code == 404
    assert instructor.put(
        "/questions/{}".format(question_id),
        json={"title": "Changed", "stem": "Changed", "answer": "Changed"},
    ).status_code == 404
    assert instructor.delete("/questions/{}".format(question_id)).status_code == 404
    assert instructor.get(
        "/questions/{}/distractors".format(question_id)
    ).status_code == 404
    assert instructor.post(
        "/questions/{}/distractors".format(question_id),
        json={"answer": "New wrong answer", "justification": "Not correct"},
    ).status_code == 404
    student_distractor_id = ids["student_distractor"]
    assert instructor.put(
        "/student_distractors/{}/grade".format(student_distractor_id),
        json={"grade": 5},
    ).status_code == 404
    assert instructor.put(
        "/student_distractors/{}/add_to_pool".format(student_distractor_id),
        json={},
    ).status_code == 404
    assert instructor.put(
        "/student_distractors/{}/remove_from_pool".format(student_distractor_id),
        json={},
    ).status_code == 404
    assert instructor.put(
        "/student_distractors/{}/comment".format(student_distractor_id),
        json={"comment": "Not allowed"},
    ).status_code == 404
    assert instructor.get("/distractors/{}".format(distractor_id)).status_code == 404
    assert instructor.put(
        "/distractors/{}".format(distractor_id),
        json={"answer": "Changed", "justification": "Changed"},
    ).status_code == 404
    assert instructor.delete("/distractors/{}".format(distractor_id)).status_code == 404
    assert instructor.get("/question-editor/{}".format(question_id)).status_code == 404
    assert instructor.get(
        "/quiz-question-selector-2/{}/{}".format(quiz_id, question_id)
    ).status_code == 404
    assert instructor.post(
        "/quiz-question-selector-2/{}/{}".format(quiz_id, question_id),
        json={"selected_distractors": [distractor_id]},
    ).status_code == 404

    with APP.app_context():
        assert models.Question.query.get(question_id).title.startswith("Question b")
        assert models.Distractor.query.get(distractor_id).answer == "Wrong answer b"
        assert models.Quiz.query.get(quiz_id).quiz_questions == []


def test_instructor_can_manage_own_question_and_distractors(
    question_ownership_context,
):
    make_client, ids = question_ownership_context
    instructor = make_client("instructor_a")
    question_id = ids["questions"]["a"]

    assert instructor.get("/questions/{}".format(question_id)).status_code == 200
    update_response = instructor.put(
        "/questions/{}".format(question_id),
        json={"title": "Updated own question", "stem": "Updated stem", "answer": "Updated answer"},
    )
    assert update_response.status_code == 200

    create_response = instructor.post(
        "/questions/{}/distractors".format(question_id),
        json={"answer": "New own distractor", "justification": "It is incorrect"},
    )
    assert create_response.status_code == 201
    new_distractor_id = create_response.json["id"]
    assert instructor.get("/distractors/{}".format(new_distractor_id)).status_code == 200
    assert instructor.put(
        "/distractors/{}".format(new_distractor_id),
        json={"answer": "Updated distractor", "justification": "Updated reason"},
    ).status_code == 200
    assert instructor.delete("/distractors/{}".format(new_distractor_id)).status_code == 204
    assert instructor.delete("/questions/{}".format(question_id)).status_code == 200


def test_admin_can_select_and_manage_questions_from_other_instructors(
    question_ownership_context,
):
    make_client, ids = question_ownership_context
    admin = make_client("admin")
    question_id = ids["questions"]["b"]
    distractor_id = ids["distractors"]["b"]
    admin_quiz_id = ids["quizzes"]["admin"]

    assert admin.get("/questions/{}".format(question_id)).status_code == 200
    assert admin.get("/quizquestions/{}".format(ids["quiz_questions"]["b"])).status_code == 200
    assert ids["quiz_questions"]["b"] in {
        question["id"] for question in admin.get("/quizquestions").json
    }
    assert admin.get("/distractors/{}".format(distractor_id)).status_code == 200
    assert admin.get("/question-editor/{}".format(question_id)).status_code == 200

    selector = admin.get("/quiz-question-selector-1/{}".format(admin_quiz_id))
    assert selector.status_code == 200
    assert b"Question b" in selector.data
    assert admin.get(
        "/quiz-question-selector-2/{}/{}".format(admin_quiz_id, question_id)
    ).status_code == 200

    response = admin.post(
        "/quiz-question-selector-2/{}/{}".format(admin_quiz_id, question_id),
        json={"selected_distractors": [distractor_id]},
    )
    assert response.status_code == 200
    with APP.app_context():
        quiz = models.Quiz.query.get(admin_quiz_id)
        assert len(quiz.quiz_questions) == 1
        assert quiz.quiz_questions[0].question_id == question_id


def test_admin_can_update_and_delete_another_instructors_question_bank_records(
    question_ownership_context,
):
    make_client, ids = question_ownership_context
    admin = make_client("admin")
    question_id = ids["questions"]["b"]
    distractor_id = ids["distractors"]["b"]

    assert admin.put(
        "/questions/{}".format(question_id),
        json={"title": "Admin update", "stem": "Admin stem", "answer": "Admin answer"},
    ).status_code == 200
    with APP.app_context():
        models.InvalidatedDistractor.query.filter_by(
            question_id=question_id
        ).delete(synchronize_session=False)
        quiz_question = models.QuizQuestion.query.get(ids["quiz_questions"]["b"])
        for quiz in list(quiz_question.quizzes):
            quiz.quiz_questions.remove(quiz_question)
        quiz_question.distractors.clear()
        models.DB.session.delete(quiz_question)
        models.DB.session.commit()

    assert admin.put(
        "/distractors/{}".format(distractor_id),
        json={"answer": "Admin distractor update", "justification": "Admin reason"},
    ).status_code == 200
    assert admin.delete("/distractors/{}".format(distractor_id)).status_code == 204
    assert admin.delete("/questions/{}".format(question_id)).status_code == 200
