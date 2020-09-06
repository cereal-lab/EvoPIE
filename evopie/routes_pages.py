# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response
from flask import Blueprint
from flask_login import login_required, current_user

import json

from . import models



pages = Blueprint('pages', __name__)



@pages.route('/')
def index():
    '''
    Index page for the whole thing; used to test out a rudimentary user interface
    '''
    all_quizzes =  [q.dump_as_dict() for q in models.Question.query.all()]
    return render_template('index.html', quizzes=all_quizzes)



@pages.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.first_name)
    # based on the current_user.is_student & current_user.is_instructor we could
    # redirect to different dashboards



@pages.route('/student/<int:qid>', methods=['GET'])
@login_required
def get_student(qid):
    if not current_user.is_student():
        response = ('You are not allowed to take this quiz', 403, {"Content-Type": "application/json"})
        return make_response(response)

    q = models.Quiz.query.get_or_404(qid)
    u = models.User.query.get_or_404(current_user.id)
    
    # determine which step of the peer instruction the student is in
    # TODO we need to reject step2 until it has been enabled by instructor
    # do so in the /quizzes/x/take route below as well
    # e.g., store step # in attribute of Quiz
    a = models.QuizAttempt.query.filter_by(student_id=current_user.id).filter_by(quiz_id=qid).all()
    quiz_questions = [question.dump_as_dict() for question in q.quiz_questions]
    
    # Redirect to different pages depending on step; e.g., student1.html vs. student2.html
    if a: # step = 2
        return render_template('student2.html', quiz=q, questions=quiz_questions, student=u, attempt=a[0])
    else: # step = 1
        return render_template('student1.html', quiz=q, questions=quiz_questions, student=u)


