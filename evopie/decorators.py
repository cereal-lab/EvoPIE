from datetime import datetime
from pytz import timezone
from evopie.config import QUIZ_ATTEMPT_SOLUTIONS, QUIZ_ATTEMPT_STEP1, QUIZ_ATTEMPT_STEP2, QUIZ_HIDDEN, QUIZ_SOLUTIONS, QUIZ_STEP1, QUIZ_STEP2, ROLE_STUDENT
from flask import flash, g, jsonify, redirect, url_for, request, abort
from flask_login import current_user
from functools import wraps
from evopie.utils import param_to_dict
from . import models
from sqlalchemy.orm.exc import StaleDataError
from evopie.quiz_model import get_quiz_builder

def change_quiz_status(quiz: models.Quiz) -> None:
    tzinfo = timezone('US/Eastern')
    currentDateTime = datetime.now(tzinfo)
    currentDateTime = currentDateTime.replace(tzinfo=None)
    old_status = quiz.status
    if currentDateTime <= quiz.deadline0 and quiz.status != QUIZ_HIDDEN:
        quiz.status = QUIZ_HIDDEN
    elif currentDateTime > quiz.deadline0 and currentDateTime <= quiz.deadline1 and quiz.status != QUIZ_STEP1:
        quiz.status = QUIZ_STEP1
    elif currentDateTime > quiz.deadline1 and currentDateTime <= quiz.deadline3 and quiz.status != QUIZ_STEP2:
        quiz.status = QUIZ_STEP2
    elif currentDateTime > quiz.deadline3 and currentDateTime <= quiz.deadline4 and quiz.status != QUIZ_SOLUTIONS:
        quiz.status = QUIZ_SOLUTIONS
    elif currentDateTime > quiz.deadline4 and quiz.status != QUIZ_HIDDEN:
        quiz.status = QUIZ_HIDDEN
    new_status = quiz.status    
    if old_status != new_status:
        models.DB.session.commit()
        if new_status == QUIZ_STEP1:
            get_quiz_builder().load_quiz_model(quiz, create_if_not_exist=True)


def role_required(role, redirect_to_referrer = False, redirect_route='login', redirect_message="You are not authorized to access specified page", category="message"):
    '''
    Sepcifies what role is needed: student or instructor
    Parameters
    -----
        role: one of ROLE_ contants from config module
    '''
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                if request.accept_mimetypes.accept_html: 
                    if redirect_message is not None: 
                        flash(redirect_message, category)                    
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
                elif request.accept_mimetypes.accept_json or request.is_json:
                    return jsonify({"message": redirect_message}), 403
                else: 
                    return abort(403)
            return f(*args, **kwargs)            
        return decorated_function
    return decorator

def verify_instructor_relationship(quiz_attempt_param = "q", redirect_to_referrer = False, redirect_route='index'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if type(kwargs.get(quiz_attempt_param)) is models.Quiz:
                q = kwargs[quiz_attempt_param]
            elif kwargs.get(quiz_attempt_param, None) is None:
                q = models.Quiz.query.get_or_404(kwargs['qid'])
            else:
                q, attempt = kwargs[quiz_attempt_param]

            student = models.User.query.filter_by(id=current_user.id).first()
            courses = student.courses
            for course in courses:
                if q in course.quizzes:
                    return f(*args, **kwargs)

            flash("You are not allowed to take this quiz", "error")
            return redirect(url_for('pages.index'))
                    
        return decorated_function
    return decorator

def verify_deadline(quiz_attempt_param = "q", redirect_to_referrer = False, redirect_route='index'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tzinfo = timezone('US/Eastern')
            date = datetime.now(tzinfo)
            date = date.replace(tzinfo=None)
            if type(kwargs.get(quiz_attempt_param)) is models.Quiz:
                q = kwargs[quiz_attempt_param]
                attempt = models.QuizAttempt.query.filter_by(student_id=current_user.id, quiz_id=q.id).first()
            elif kwargs.get(quiz_attempt_param, None) is None:
                q = models.Quiz.query.get_or_404(kwargs['qid'])
                attempt = models.QuizAttempt.query.filter_by(student_id=current_user.id, quiz_id=q.id).first()
            else:
                q, attempt = kwargs[quiz_attempt_param]

            status, revised_responses_cnt = (attempt.status, len(attempt.revised_responses)) if attempt else (QUIZ_ATTEMPT_STEP1, 0)
            def err_redir():
                return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))

            if q.deadline_driven == "True":
                change_quiz_status(q)
            else:
                if (status == QUIZ_ATTEMPT_STEP1 and q.status == QUIZ_STEP1
                 or status == QUIZ_ATTEMPT_STEP2 and q.status == QUIZ_STEP2
                 or status == QUIZ_ATTEMPT_SOLUTIONS and q.status == QUIZ_SOLUTIONS):
                    return f(*args, **kwargs)

            #Block about statuses
            #check correspondence of quiz and attemot statuses
            if q.status == QUIZ_HIDDEN: #quiz is hidden from students
                flash("Quiz not accessible at this time", "error")
                return err_redir()

            if (status == QUIZ_ATTEMPT_STEP1) and (q.status != QUIZ_STEP1):
                flash("Step 1 of this quiz is not available", "error")
                return err_redir()

            if status == QUIZ_ATTEMPT_STEP2 and q.status == QUIZ_STEP1:
                flash("You already submitted your answers for step 1 of this quiz. Wait for the instructor to open step 2 for everyone.", "error")
                return err_redir()

            if status == QUIZ_ATTEMPT_STEP1 and q.status == QUIZ_STEP2:
                flash("You did not submit your answers for step 1 of this quiz. Because of that, you may not participate in step 2.", "error")
                return err_redir()

            if status == QUIZ_ATTEMPT_SOLUTIONS and q.status == QUIZ_STEP2 and revised_responses_cnt > 0:
                flash("You already submitted your answers for both step 1 and step 2. You are done with this quiz.", "error")
                return err_redir()

            # First sanity check: is the quiz active? 
            if date >= q.deadline4:
                flash("Quiz is closed.", "error")
                # Should we hide the quiz from the student?
                return err_redir()
            if date < q.deadline0:
                flash("The quiz is not available yet.", "error")
                return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))

            if status == QUIZ_ATTEMPT_STEP1:
                if q.status != QUIZ_STEP1:
                    flash("You did not submit your answers for step 1 of this quiz. Because of that, you may not participate in step 2.", "error")
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
                elif not (date > q.deadline0 and date <= q.deadline1):
                    flash("You missed the deadline for completing Step1.", "error")
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
            elif status == QUIZ_ATTEMPT_STEP2:
                if attempt is None:
                    flash("You did not submit your answers for step 1 of this quiz. Because of that, you may not participate in step 2.", "error")
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
                elif q.status != QUIZ_STEP2:
                    flash("You already submitted your answers for step 1 of this quiz. Wait for the instructor to open step 2 for everyone.", "error")
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
                elif date <= q.deadline1:
                    flash("You cannot participate in step 2 of this quiz before the deadline for step 1.", "error")
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
                elif not (date > q.deadline1 and date <= q.deadline2):
                    flash("You missed the deadline for completing Step2.", "error")
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
            elif status == QUIZ_ATTEMPT_SOLUTIONS:
                if date < q.deadline3:
                    flash("Solutions have not been released yet.", "error")
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
                elif q.status == QUIZ_STEP2 and attempt.revised_responses != "{}":
                    flash("You already submitted your answers for both step 1 and step 2. You are done with this quiz.", "error")
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
                elif not (date >= q.deadline3 and date < q.deadline4):
                    flash("You missed the deadline for checking the solutions.", "error")
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
                elif request.method == "POST":
                    flash("You cannot submit your answers after the deadline.", "error")
                    return redirect(request.referrer if redirect_to_referrer else url_for(redirect_route, next=request.url))
            
            return f(*args, **kwargs)            
        return decorated_function
    return decorator

def retry_concurrent_update(f):
    '''
    For optimistic concurrency retries endpoint when concurrent updates happen.
    This could be not always optimal strategy. Consider also showing to client updates versions of data from db before retry
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "inside_retry_concurrent" in g:
            return f(*args, **kwargs)        
        g.inside_retry_concurrent = True            
        while True: #exit this loop if no StaleDataError: https://docs.sqlalchemy.org/en/14/orm/versioning.html   
            try:
                res = f(*args, **kwargs)            
                break
            except StaleDataError: 
                models.DB.session.rollback()
        return res 
    return decorated_function

def validate_quiz_attempt_step(quiz_attempt_param, required_step = None):
    '''
    Check that view_args quiz and attempt has consistent state. 
    Otherwise return either redirect to pages index with flash or json which forces redirect.
    '''
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "quiz_attempt_validated" in g:
                return f(*args, **kwargs)        
            g.quiz_attempt_validated = True            
            quiz, attempt = request.view_args[quiz_attempt_param]
            shortcut = False 
            if required_step is not None and attempt.status != required_step: 
                flash("Cannot perform action. Quiz attempt is not on required quiz step")
                shortcut = True 
            elif attempt.status == QUIZ_ATTEMPT_STEP1 and quiz.status != QUIZ_STEP1:
                flash("Quiz step1 is not available anymore") #saves msg to cookie
                shortcut = True 
            elif attempt.status == QUIZ_ATTEMPT_STEP2 and quiz.status != QUIZ_STEP2:
                flash("Quiz step2 is not available anymore") #saves msg to cookie
                shortcut = True 
            elif attempt.status == QUIZ_ATTEMPT_SOLUTIONS and quiz.status != QUIZ_SOLUTIONS:
                flash("Quiz solutions are not available yet") #saves msg to cookie
                shortcut = True 
            if shortcut:
                if request.accept_mimetypes.accept_html:
                    return redirect(url_for("pages.index"))
                else: 
                    return jsonify({"redirect": url_for("pages.index")})
            return f(*args, **kwargs)            
        return decorated_function
    return decorator

def unmime(delim = '_', type_converters = {}):
    '''
    Normalizes request.form and request.json and provides it as body parameter of endpoint 
    Normalization of json is trivial. For form parameter names are normalized with param_to_dict
    '''
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):    
            if "unmimed" in g:
                return f(*args, **kwargs)        
            g.unmimed = True
            if request.is_json:
                body = request.json
                #NOTE: next code was existed  only due to json type conversions in Extensive tests - better to fix tests
                # body = dict(request.json)
                # def convert_values(cur, conv):
                #     for k, v in conv.items():
                #         if k == "*":
                #             for ck, cv in cur.items():
                #                 if callable(v):
                #                     cur[ck] = v(cv)
                #                 else:
                #                     convert_values(cv, v)       
                #         elif k in cur:
                #             if callable(v):
                #                 cur[k] = v(cur[k])
                #             else:
                #                 convert_values(cur[k], v)                               
                # convert_values(body, type_converters)                 
            else: 
                body = {}
                for name, value in request.form.items():
                    param_to_dict(name, value, d = body, delim = delim, type_converters = type_converters)            
            orig_res = res = f(*args, **kwargs, body=body)
            if type(res) == tuple:
                res, status = res[0:2]
            else:
                status = 200
            if type(res) == dict:
                #converting dict back to html for form
                if request.is_json: #NOTE: works only for requests with body - more careful login for GET is necessary - or use accept headers
                    return orig_res
                else:
                    if res["message"]: 
                        flash_area = "error" if status >= 400 else "message"
                        flash(res["message"], flash_area)
                    if res["redirect"]:
                        return redirect(res["redirect"])
                    else:
                        return redirect(url_for("pages.index"))
            return orig_res
        return decorated_function
    return decorator