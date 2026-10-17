import uuid

import pytest

from evopie import APP
from datalayer import ROLE_INSTRUCTOR, models


@pytest.fixture
def question_form_client():
    email = "question-author-{}@example.edu".format(uuid.uuid4().hex)
    with APP.app_context():
        models.DB.create_all()
        instructor = models.User(email=email, role=ROLE_INSTRUCTOR)
        models.DB.session.add(instructor)
        models.DB.session.commit()
        instructor_id = instructor.id

    client = APP.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(instructor_id)
        session["_fresh"] = True

    yield client, instructor_id

    with APP.app_context():
        models.Question.query.filter_by(author_id=instructor_id).delete()
        instructor = models.User.query.get(instructor_id)
        if instructor is not None:
            models.DB.session.delete(instructor)
        models.DB.session.commit()


@pytest.mark.parametrize(
    "stem, answer, missing_field",
    [
        ("<p><br></p>", "<p>42</p>", "question"),
        ("<p>What is the answer?</p>", "<p>&nbsp;</p>", "answer"),
    ],
)
def test_html_form_explains_empty_question_or_answer(
    question_form_client, stem, answer, missing_field
):
    client, instructor_id = question_form_client

    response = client.post(
        "/questions",
        data={"title": "Test question", "stem": stem, "answer": answer},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        "Please complete the required fields: {}.".format(missing_field).encode()
        in response.data
    )
    with APP.app_context():
        assert models.Question.query.filter_by(author_id=instructor_id).count() == 0


def test_json_request_gets_a_field_specific_validation_error(question_form_client):
    client, instructor_id = question_form_client

    response = client.post(
        "/questions",
        json={"title": "Test question", "stem": "<p><br></p>", "answer": "<p>42</p>"},
    )

    assert response.status_code == 400
    assert response.json["message"] == "Please complete the required fields: question."
    with APP.app_context():
        assert models.Question.query.filter_by(author_id=instructor_id).count() == 0


def test_empty_json_payload_returns_required_fields_error(question_form_client):
    client, instructor_id = question_form_client

    response = client.post("/questions", json={})

    assert response.status_code == 400
    assert response.json["message"] == (
        "Please complete the required fields: title, question, answer."
    )
    with APP.app_context():
        assert models.Question.query.filter_by(author_id=instructor_id).count() == 0


def test_whitespace_only_title_is_rejected(question_form_client):
    client, instructor_id = question_form_client

    response = client.post(
        "/questions",
        data={"title": "   ", "stem": "<p>Question</p>", "answer": "<p>Answer</p>"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please complete the required fields: title." in response.data
    with APP.app_context():
        assert models.Question.query.filter_by(author_id=instructor_id).count() == 0


def test_valid_question_form_still_creates_a_question(question_form_client):
    client, instructor_id = question_form_client

    response = client.post(
        "/questions",
        data={
            "title": "Test question",
            "stem": (
                '<p>What is the answer?</p><img src=x onerror="alert(1)">'
                '<a href="javascript:alert(1)">unsafe link</a>'
                '<script>alert(1)</script>'
            ),
            "answer": "<p>42</p>",
        },
        headers={"Referer": "/questions-browser"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    with APP.app_context():
        question = models.Question.query.filter_by(author_id=instructor_id).one()
        assert question.title == "Test question"
        assert "onerror" not in question.stem.lower()
        assert "javascript:" not in question.stem.lower()
        assert "<script" not in question.stem.lower()
