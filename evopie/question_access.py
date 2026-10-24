from flask import abort

from datalayer import models


def question_query_for_user(user):
    query = models.Question.query
    if not user.is_admin():
        query = query.filter(models.Question.author_id == user.id)
    return query


def get_question_for_user_or_404(question_id, user):
    question = models.Question.query.get_or_404(question_id)
    if not user.is_admin() and question.author_id != user.id:
        abort(404)
    return question


def get_distractor_for_user_or_404(distractor_id, user):
    distractor = models.Distractor.query.get_or_404(distractor_id)
    get_question_for_user_or_404(distractor.question_id, user)
    return distractor
