from flask import abort

from datalayer import models


def course_query_for_user(user):
    query = models.Course.query
    if not user.is_admin():
        query = query.filter(models.Course.instructor_id == user.id)
    return query


def get_course_for_user_or_404(course_id, user):
    course = models.Course.query.get_or_404(course_id)
    if not user.is_admin() and course.instructor_id != user.id:
        abort(404)
    return course


def quiz_query_for_user(user):
    query = models.Quiz.query
    if not user.is_admin():
        query = query.filter(models.Quiz.author_id == user.id)
    return query


def get_quiz_for_user_or_404(quiz_id, user):
    quiz = models.Quiz.query.get_or_404(quiz_id)
    if not user.is_admin() and quiz.author_id != user.id:
        abort(404)
    return quiz
