import uuid

import pytest

from evopie import APP
from datalayer import ROLE_INSTRUCTOR, models


@pytest.fixture
def empty_distractor_context():
    suffix = uuid.uuid4().hex
    with APP.app_context():
        models.DB.create_all()
        instructor = models.User(
            email="empty-distractors-{}@example.edu".format(suffix),
            first_name="Quiz",
            last_name="Author",
            password="test-password",
            role=ROLE_INSTRUCTOR,
        )
        models.DB.session.add(instructor)
        models.DB.session.flush()
        question = models.Question(
            title="Question without distractors",
            stem="Question stem",
            answer="Correct answer",
            author_id=instructor.id,
        )
        quiz = models.Quiz(
            title="Quiz without distractors",
            description="Test quiz",
            author_id=instructor.id,
        )
        models.DB.session.add_all([question, quiz])
        models.DB.session.commit()
        instructor_id = instructor.id
        question_id = question.id
        quiz_id = quiz.id

    client = APP.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(instructor_id)
        session["_fresh"] = True

    yield client, instructor_id, question_id, quiz_id

    with APP.app_context():
        quiz = models.Quiz.query.get(quiz_id)
        question = models.Question.query.get(question_id)
        instructor = models.User.query.get(instructor_id)
        if quiz is not None:
            quiz.quiz_questions.clear()
            models.DB.session.delete(quiz)
        if question is not None:
            models.DB.session.delete(question)
        if instructor is not None:
            models.DB.session.delete(instructor)
        models.DB.session.commit()


@pytest.mark.parametrize("selected_distractors", [None, []])
def test_quiz_rejects_empty_distractor_selection(
    empty_distractor_context, selected_distractors
):
    client, _, question_id, quiz_id = empty_distractor_context

    response = client.post(
        "/quiz-question-selector-2/{}/{}".format(quiz_id, question_id),
        json={"selected_distractors": selected_distractors},
    )

    assert response.status_code == 400
    assert response.json["message"] == (
        "Select at least one distractor, or add a distractor to this question first."
    )
    with APP.app_context():
        assert models.Quiz.query.get(quiz_id).quiz_questions == []


def test_quiz_editor_does_not_create_an_empty_placeholder_question(
    empty_distractor_context,
):
    client, instructor_id, _, quiz_id = empty_distractor_context

    with APP.app_context():
        question_count = models.Question.query.filter_by(author_id=instructor_id).count()
        quiz_question_count = models.QuizQuestion.query.count()

    response = client.get("/quiz-question-editor/{}/-1".format(quiz_id))

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/questions-browser")
    with APP.app_context():
        assert models.Question.query.filter_by(author_id=instructor_id).count() == question_count
        assert models.QuizQuestion.query.count() == quiz_question_count


def test_selector_pages_direct_instructor_to_add_missing_distractor(
    empty_distractor_context,
):
    client, _, question_id, quiz_id = empty_distractor_context

    available_questions = client.get("/quiz-question-selector-1/{}".format(quiz_id))
    question_selection = client.get(
        "/quiz-question-selector-2/{}/{}".format(quiz_id, question_id)
    )

    assert available_questions.status_code == 200
    assert b"Add a distractor before selecting this question" in available_questions.data
    assert question_selection.status_code == 200
    assert b"This question needs at least one distractor" in question_selection.data
    assert "/question-editor/{}".format(question_id).encode() in question_selection.data
    assert b"Submit with all selected distractors" not in question_selection.data
