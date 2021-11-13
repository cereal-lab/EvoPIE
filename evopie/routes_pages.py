# pylint: disable=no-member
# pylint: disable=E1101 
# Dynamic classes like scoped_session are caught by pylint as not having any
# of the members they end up featuring at runtime. This is a way to tell pylint to let it be

from operator import not_
from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response
from flask import Blueprint
from flask_login import login_required, current_user
from flask import flash
from sqlalchemy import not_
from sqlalchemy.sql import collate

import json, random

from . import DB, models

import jinja2


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
    # TODO based on the current_user.is_student & current_user.is_instructor we could
    # redirect to different dashboards. This might come in handy for the data dashboard.



@pages.route('/contributor')
@login_required
def contributor():
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    all_questions = [q.dump_as_dict() for q in models.Question.query.all()]
    #return jsonify(all_questions) 
    return render_template('contributor.html', all_questions = all_questions)



@pages.route('/questions-browser')
@login_required
def questions_browser():
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    #all_questions = [q.dump_as_dict() for q in models.Question.query.all()]
    #return render_template('questions-browser.html', all_questions = all_questions)
    # version with pagination below
    page = request.args.get('page',1, type=int)
    QUESTIONS_PER_PAGE = 10 # FIXME make this a field in a global config object
    paginated = models.Question.query.paginate(page, QUESTIONS_PER_PAGE, False)
    all_questions = [q.dump_as_dict() for q in paginated.items]
    #return jsonify(all_questions)
    next_url = url_for('pages.questions_browser', page=paginated.next_num) if paginated.has_next else None
    prev_url = url_for('pages.questions_browser', page=paginated.prev_num) if paginated.has_prev else None
    return render_template('questions-browser.html', all_questions = all_questions, next_url=next_url, prev_url=prev_url)



@pages.route('/quizzes-browser')
@login_required
def quizzes_browser():
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    page = request.args.get('page',1, type=int)
    QUESTIONS_PER_PAGE = 2 # FIXME make this a field in a global config object
    paginated = models.Quiz.query.paginate(page, QUESTIONS_PER_PAGE, False)
    all_quizzes = [q.dump_as_dict() for q in paginated.items]
    #return jsonify(all_questions)
    next_url = url_for('pages.quizzes_browser', page=paginated.next_num) if paginated.has_next else None
    prev_url = url_for('pages.quizzes_browser', page=paginated.prev_num) if paginated.has_prev else None
    return render_template('quizzes-browser.html', all_quizzes = all_quizzes, next_url=next_url, prev_url=prev_url)



@pages.route('/question-editor/<int:question_id>')
@login_required
def question_editor(question_id):
    if not current_user.is_instructor():
        flash("Restricted to contributors.", "error")
        return redirect(url_for('pages.index'))
    q = models.Question.query.get_or_404(question_id)
    ds = [d.dump_as_dict() for d in q.distractors]
    q = q.dump_as_dict()
    return render_template('question-editor.html', all_distractors = ds, question = q)
    




@pages.route('/student/<int:qid>', methods=['GET'])
@login_required
def get_student(qid):
    '''
    Links using this route are meant to be shared with students so that they may take the quiz
    and engage in the asynchronous peer instrution aspects. 
    '''
    if not current_user.is_student():
        # response = ({ "message" : "You are not allowed to take this quiz"}, 403, {"Content-Type": "application/json"})
        flash("You are not allowed to take this quiz", "error")
        return redirect(url_for('pages.index'))

    u = models.User.query.get_or_404(current_user.id)
    q = models.Quiz.query.get_or_404(qid)
    quiz_questions = [question.dump_as_dict() for question in q.quiz_questions]
    simplified_quiz_questions = [question.dump_as_simplified_dict() for question in q.quiz_questions]    
    # PBM - the alternatives for questions show unescaped when taking the quiz
    # SOL - need to unescape them before to pass them to the template
    for qq in quiz_questions:
        for altern in qq["alternatives"]:
            # experimenting, this works: tmp = jinja2.Markup(quiz_questions[0]["alternatives"][0][1]).unescape()
            altern[1] = jinja2.Markup(altern[1]).unescape()
            # nope... altern[1] = jinja2.Markup.escape(altern[1])


    # determine which step of the peer instruction the student is in
    a = models.QuizAttempt.query.filter_by(student_id=current_user.id).filter_by(quiz_id=qid).all()
    
    if q.status == "HIDDEN":
        #response     = ({ "message" : "Quiz not accessible at this time"}, 403, {"Content-Type": "application/json"})
        flash("Quiz not accessible at this time", "error")
        return redirect(url_for('pages.index'))
    if a and q.status == "STEP1":
        #response     = ({ "message" : "You already submitted your initial answers for this quiz, wait for the instructor to re-release it."}, 403, {"Content-Type": "application/json"})
        flash("You already submitted your answers for step 1 of this quiz.", "error")
        flash("Wait for the instructor to open step 2 for everyone.", "error")
        return redirect(url_for('pages.index'))
    if not a and q.status == "STEP2":
        #response     = ({ "message" : "You did not submit your initial answers for this quiz, you may not participate in the second step."}, 403, {"Content-Type": "application/json"})
        flash("You did not submit your answers for step 1 of this quiz.", "error")
        flash("Because of that, you may not participate in step 2.", "error")
        return redirect(url_for('pages.index'))
    if q.status == "STEP2" and a[0].revised_responses != "{}":
        #TODO the above is ugly, add a boolean method instead
        #response     = ({ "message" : "You already revised your initial answers, you are done with both steps of this quiz."}, 403, {"Content-Type": "application/json"})
        flash("You already submitted your answers for both step 1 and step 2.", "error")
        flash("You are done with this quiz.", "error")
        return redirect(url_for('pages.index'))
        
    # Redirect to different pages depending on step; e.g., student1.html vs. student2.html
    if a: # step == 2
        # retrieve the peers' justifications for each question
        quiz_justifications = {}
        for quiz_question in q.quiz_questions:
            question_justifications = {}
            for distractor in quiz_question.distractors:
                # get all justifications for that alternative / question pair
                # NOTE some empty justifications end up making it here, we need to remove them then make sure that we handle, in the template, the possibility of no justification available at all.\
                question_justifications[str(distractor.id)] = models.Justification.query\
                    .filter_by(quiz_question_id=quiz_question.id)\
                    .filter_by(distractor_id=distractor.id)\
                    .filter(not_(models.Justification.justification==""))\
                    .all()
            # also handle the solution -1
            # NOTE some empty justifications end up making it here, we need to remove them then make sure that we handle, in the template, the possibility of no justification available at all.\
            question_justifications["-1"] = models.Justification.query\
                .filter_by(quiz_question_id=quiz_question.id)\
                .filter_by(distractor_id="-1")\
                .filter(not_(models.Justification.justification==""))\
                .all()
            
            # NOTE use filter instead of filter_by for != comparisons
            # https://stackoverflow.com/questions/16093475/flask-sqlalchemy-querying-a-column-with-not-equals/16093713



            # record this array of objects as corresponding to this question
            quiz_justifications[str(quiz_question.id)] = question_justifications
            
        # This is where we apply the peer selection policy
        # We now revisit the data we collected and pick one justification in each array of Justification objects
        for key_question in quiz_justifications:
            for key_distractor in quiz_justifications[key_question]:
                #pick multiple of the justification objects at random
                
                #NOTE make sure we check that the len of the array is big enough first
                number_to_select = min(3 , len(quiz_justifications[key_question][key_distractor]))
                #TODO FFS remove the above ugly, hardcoded, magic, number

                #FIXME prevent selection of our own justifications!!!

                selected = []
                for n in range(number_to_select): 
                    
                    index = random.randint(0,len(quiz_justifications[key_question][key_distractor])-1)
                    neo = quiz_justifications[key_question][key_distractor].pop(index) #[index]
                    selected.append(neo)

                # now replace the object by a dictionary so that the javascript may handle it easily
                #quiz_justifications[key_question][key_distractor] = {
                #    "id" : neo.id,
                #    "justification": neo.justification
                #}
                #undo the above and keep a python object right there
                #quiz_justifications[key_question][key_distractor] = neo
                quiz_justifications[key_question][key_distractor] = selected

                initial_responses = [] 
                asdict = json.loads(a[0].initial_responses.replace("'",'"'))
                for k in asdict:
                    initial_responses.append(asdict[k])
                return render_template('student.html', quiz=q, simplified_questions=simplified_quiz_questions, questions=quiz_questions, student=u, attempt=a[0], initial_responses=initial_responses, justifications=quiz_justifications)
    else: # step == 1
        return render_template('student.html', quiz=q, simplified_questions=simplified_quiz_questions, questions=quiz_questions, student=u)




@pages.route('/grades/<int:qid>', methods=['GET'])
@login_required
def get_grades(qid):
    '''
    This page allows to get all stats on a given quiz.
    '''
    if not current_user.is_instructor():
        flash("Restricted to instructors.", "error")
        return redirect(url_for('pages.index'))
    q = models.Quiz.query.get_or_404(qid)
    # base syntax; returns a list of tupples (blah)
    # grades=DB.session.query(models.QuizAttempt, models.User)\
    #    .filter(models.QuizAttempt.quiz_id == qid)\
    #    .filter(models.QuizAttempt.student_id == models.User.id)\
    #    .all()
    grades=models.QuizAttempt.query.join(models.User)\
        .filter(models.QuizAttempt.quiz_id == qid)\
        .filter(models.QuizAttempt.student_id == models.User.id)\
        .order_by(collate(models.User.last_name, 'NOCASE'))\
        .all()
    return render_template('grades.html', quiz=q, all_grades=grades)