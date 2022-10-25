# pylint: disable=no-member
# pylint: disable=E1101

# The following are flask custom commands; 

from datetime import datetime
from evopie.config import EVO_PROCESS_STATUS_ACTIVE, EVO_PROCESS_STATUS_STOPPED, QUIZ_ATTEMPT_SOLUTIONS, QUIZ_ATTEMPT_STEP1, QUIZ_ATTEMPT_STEP2, QUIZ_HIDDEN, QUIZ_SOLUTIONS, QUIZ_STEP1, QUIZ_STEP2, ROLE_STUDENT
from . import models, APP # get also DB from there
from sqlalchemy.orm.exc import StaleDataError

# helper method to use instead of directly calling bleach.clean
import bleach
from bleach_allowlist import generally_xss_safe, print_attrs, standard_styles

def sanitize(html):
    result = bleach.clean(html, tags=generally_xss_safe, attributes=print_attrs, styles=standard_styles)
    return result


# All TODO #3 issue from models.py are factored in the function below
# unescaping so that the stem and answer are rendered in jinja2 template with | safe
from jinja2 import Markup
def unescape(str):
    return Markup(str).unescape()

def changeQuizStatus(qid):
    currentDateTime = datetime.now()
    quiz = models.Quiz.query.get_or_404(qid)
    if currentDateTime <= quiz.deadline0:
        quiz.status = "HIDDEN"
    elif currentDateTime > quiz.deadline0 and currentDateTime <= quiz.deadline1:
        quiz.status = "STEP1"
    elif currentDateTime > quiz.deadline1 and currentDateTime <= quiz.deadline3:
        quiz.status = "STEP2"
    elif currentDateTime > quiz.deadline3 and currentDateTime <= quiz.deadline4:
        quiz.status = "SOLUTIONS"
    elif currentDateTime > quiz.deadline4:
        quiz.status = "HIDDEN"
    models.DB.session.commit()
    
@APP.template_filter('unescapeDoubleQuotes')
def unescape_double_quotes(s): 
    return s.replace('\\"','\"')

# Invoke with flask DB-reboot
# Tear down the data base and rebuild an empty one.
@APP.cli.command("DB-reboot")
def DB_reboot():
    models.DB.drop_all()
    models.DB.create_all()



# Invoke with flask DB-multi-instr
# First run flask DB-reboot
# adds sample data to be used for testing multi-instr support

@APP.cli.command("DB-multi-instr")
def DB_multi_instr():
    from subprocess import check_output
    import os
    script_path = os.path.abspath('./testing/MultiInstr')
    stdout = check_output([os.path.join(script_path, 'setup.sh')], 
                          cwd=script_path).decode('utf-8')
    print(stdout)
    # i1, i2, *students = models.User.query.all()
    i2 = models.User.query.filter_by(email='instructor2@usf.edu').first()
    i2.set_role(models.ROLE_INSTRUCTOR)
    # print(f'Adding students to instructor 1: {i1}')
    # for student in students[::2]:
    #     print(f'\tAdding {student}')
    #     i1.students.append(student)

    # print(f'Adding students to instructor 2: {i2}')
    # for student in students[1::2]:
    #     print(f'\tAdding {student}')
    #     i2.students.append(student)

    # print(f'\tAdding {students[-1]}')
    # i2.students.append(students[-1])
    
    models.DB.session.commit()



    
# Invoke with flask DB-populate
# Empties the table and insert some testing data in the DB.
# Consider using scripts/TestDB_[setup|step1|step2].sh 
@APP.cli.command("DB-populate")
def DB_populate():
    '''
        Just populating the DB with some mock quizzes
    '''
    # For some reason Flask restarts the app when we launch it with
    # pipenv run python app.py
    # as a result, we populate twice and get too many quizzes / distractors
    # let's fix this by deleting all data from the tables first
    models.Question.query.delete()
    models.Distractor.query.delete()
    models.DB.session.commit() # don't forget to commit or the DB will be locked

    all_mcqs = [
            models.Question(title=u'Sir Lancelot and the bridge keeper, part 1',
                            stem=u'What... is your name?',
                            answer=u'Sir Lancelot of Camelot'),
            models.Question(title=u'Sir Lancelot and the bridge keeper, part 2',
                            stem=u'What... is your quest?',
                            answer=u'To seek the holy grail'),
            models.Question(title=u'Sir Lancelot and the bridge keeper, part 3',
                            stem=u'What... is your favorite colour?',
                            answer=u'Blue')
    ]

    models.DB.session.add_all(all_mcqs)
    models.DB.session.commit()
    # need to commit right now; if not, the qid below will not be added in the distractors table's rows

    qid=all_mcqs[0].id
    some_distractors = [
        models.Distractor(question_id=qid,answer=u'Sir Galahad of Camelot'),
        models.Distractor(question_id=qid,answer=u'Sir Arthur of Camelot'),
        models.Distractor(question_id=qid,answer=u'Sir Bevedere of Camelot'),
        models.Distractor(question_id=qid,answer=u'Sir Robin of Camelot'),
    ]

    qid=all_mcqs[1].id
    more_distractors = [
        models.Distractor(question_id=qid,answer=u'To bravely run away'),
        models.Distractor(question_id=qid,answer=u'To spank Zoot'),
        models.Distractor(question_id=qid,answer=u'To find a shrubbery')
    ]

    qid=all_mcqs[2].id
    yet_more_distractors = [
        models.Distractor(question_id=qid,answer=u'Green'),
        models.Distractor(question_id=qid,answer=u'Red'),
        models.Distractor(question_id=qid,answer=u'Yellow')
    ]

    models.DB.session.add_all(some_distractors + more_distractors + yet_more_distractors)
    models.DB.session.commit()


from flask import flash, g, jsonify, redirect, url_for, request, abort
from flask_login import current_user

from functools import wraps

def groupby(iterable, key=lambda x: x):
    '''from iterable creates list of pairs group_key:list of elements with the key'''
    res = {}
    for el in iterable:
        k = key(el)
        if k not in res:
            res[k] = []
        res[k].append(el)
    return res.items()

def unpack_key(key, knows):
    ''' Allows to flatten 'sid': [1,2,3] to several records with 'sid': 1, 'sid':2, 'sid': 3
        It does same for qid and did 
    '''
    return [k2 for k in knows 
                for ks in [[{**k, key: i} for i in k[key]] 
                            if type(k.get(key, "*")) == list else 
                            [{**k, key: i} for i in range(k[key]["range"][0], k[key]["range"][1] + 1)] #NOTE: json "range":[2,3] is mapped to call range(2,4)
                            if type(k.get(key, "*")) == dict and "range" in k[key] else
                            [{**k, key: i} for r in k[key]["ranges"] for rg in [r if type(r) == list else [r, r]] for i in range(rg[0], rg[1] + 1)]
                            if type(k.get(key, "*")) == dict and "ranges" in k[key] else
                            [k]] 
                for k2 in ks]    

def find_median(sorted_list):
    if len(sorted_list) == 0: return None, []
    indices = []

    list_size = len(sorted_list)
    median = 0

    if list_size % 2 == 0:
        indices.append(int(list_size / 2) - 1)  # -1 because index starts from 0
        indices.append(int(list_size / 2))

        median = (sorted_list[indices[0]] + sorted_list[indices[1]]) / 2
    else:
        indices.append(int(list_size / 2))

        median = sorted_list[indices[0]]

    return median, indices    

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

            instructors = [ instructor.id for instructor in models.User.query.filter_by(id=current_user.id).first().instructors ]
            all_quiz_ids = [ quiz.id for quiz in models.Quiz.query.filter(models.Quiz.author_id.in_(instructors)).all() ]
            if q.id not in all_quiz_ids:
                flash("You are not allowed to take this quiz", "error")
                return redirect(url_for('pages.index'))
            
            return f(*args, **kwargs)            
        return decorated_function
    return decorator

def verify_deadline(quiz_attempt_param = "q", redirect_to_referrer = False, redirect_route='index'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            date = datetime.now()
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
                changeQuizStatus(q.id)
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

def param_to_dict(n, v, d = {}, type_converters = {}, delim = '_'):
    '''
    Converts flat dict to tree using delim as edge in hierarchy
    Example: a.b.0.test --> {"a":{"b":{"0":{"test":...}}}} 
    '''
    cur = d     
    converter = type_converters
    path = n.split(delim)
    for path_elem in path[:-1]:
        converter = converter.get(path_elem, converter.get("*", {}))
        cur = cur.setdefault(path_elem, {})        
    converter = converter.get(path[-1], converter.get("*", {}))
    cur[path[-1]] = converter(v) if callable(converter) else v
    return d

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