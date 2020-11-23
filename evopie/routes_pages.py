# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response
from flask import Blueprint
from flask_login import login_required, current_user

import json, random

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
    '''
    Links using this route are meant to be shared with students so that they may take the quiz
    and engage in the asynchronous peer instrution aspects. 
    '''
    if not current_user.is_student():
        response = ('You are not allowed to take this quiz', 403, {"Content-Type": "application/json"})
        return make_response(response)

    u = models.User.query.get_or_404(current_user.id)
    q = models.Quiz.query.get_or_404(qid)
    quiz_questions = [question.dump_as_dict() for question in q.quiz_questions]
    
    # determine which step of the peer instruction the student is in
    a = models.QuizAttempt.query.filter_by(student_id=current_user.id).filter_by(quiz_id=qid).all()
    
    if q.status == "HIDDEN":
        response     = ({ "message" : "Quiz not accessible at this time"}, 403, {"Content-Type": "application/json"})
        return make_response(response)
    if a and q.status == "STEP1":
        response     = ({ "message" : "You already submitted your initial answers for this quiz, wait for the instructor to re-release it."}, 403, {"Content-Type": "application/json"})
        return make_response(response)
    if not a and q.status == "STEP2":
        response     = ({ "message" : "You did not submit your initial answers for this quiz, you may not participate in the second step."}, 403, {"Content-Type": "application/json"})
        return make_response(response)
    if q.status == "STEP2" and a[0].revised_responses != "{}":
        #TODO the above is ugly, add a boolean method instead
        response     = ({ "message" : "You already revised your initial answers, you are done with both steps of this quiz."}, 403, {"Content-Type": "application/json"})
        return make_response(response)
        
    # Redirect to different pages depending on step; e.g., student1.html vs. student2.html
    if a: # step == 2
        # retrieve the peers' justifications for each question
        quiz_justifications = {}
        for quiz_question in q.quiz_questions:
            question_justifications = {}
            for distractor in quiz_question.distractors:
                # get all justifications for that alternative / question pair
                question_justifications[str(distractor.id)] = models.Justification.query\
                    .filter_by(quiz_question_id=quiz_question.id)\
                    .filter_by(distractor_id=distractor.id)\
                    .all()
            # also handle the solution -1
            question_justifications["-1"] = models.Justification.query\
                .filter_by(quiz_question_id=quiz_question.id)\
                .filter_by(distractor_id="-1")\
                .all()
            
            # record this array of objects as corresponding to this question
            quiz_justifications[str(quiz_question.id)] = question_justifications
            
        # This is where we apply the peer selection policy
        # We now revisit the data we collected and pick one justification in each array of Justification objects
        for key_question in quiz_justifications:
            for key_distractor in quiz_justifications[key_question]:
                #pick one of the justification objects at random
                index = random.randint(0,len(quiz_justifications[key_question][key_distractor])-1)
                neo = quiz_justifications[key_question][key_distractor][index]
                
                # now replace the object by a dictionary so that the javascript may handle it easily
                quiz_justifications[key_question][key_distractor] = {
                    "id" : neo.id,
                    "justification": neo.justification
                }

        return render_template('student2.html', quiz=q, questions=quiz_questions, student=u, attempt=a[0], justifications=quiz_justifications)
    else: # step == 1
        return render_template('student1.html', quiz=q, questions=quiz_questions, student=u)
    
    # FIXME we need to reject step2 until it has been enabled by instructor
    # do so in the /quizzes/x/take route below as well e.g., store step # in attribute of Quiz
    
