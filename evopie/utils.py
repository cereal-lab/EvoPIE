# pylint: disable=no-member
# pylint: disable=E1101

# The following are flask custom commands; 
import flask_login

from evopie.config import ROLE_STUDENT
from . import models, APP # get also DB from there
import click
from sqlalchemy.orm.exc import StaleDataError



# helper method to use instead of directly calling bleach.clean
import json
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
    
# Defining a custom jinja2 filter to get rid of \"
# in JSON for student.html
import jinja2

@APP.template_filter('unescapeDoubleQuotes')
def unescape_double_quotes(s): 
    return s.replace('\\"','\"')
    
    
    
# Invoke with flask DB-init
# Initialize the DB but without first dropping it.
# NOTE Not used in a while, consider removing.
@APP.cli.command("DB-init")
def DB_init():
    models.DB.create_all()

# Invoke with flask DB-reboot
# Tear down the data base and rebuild an empty one.
@APP.cli.command("DB-reboot")
def DB_reboot():
    models.DB.drop_all()
    models.DB.create_all()



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


from flask import flash, jsonify, redirect, url_for, request, abort
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

def role_required(role, redirect_route='login', redirect_message="You are not authorized to access specified page"):
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
                        flash(redirect_message)                    
                    return redirect(url_for(redirect_route, next=request.url))
                elif request.accept_mimetypes.accept_json or request.is_json:
                    return jsonify({"message": redirect_message}), 403
                else: 
                    return abort(403)
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
        while True: #exit this loop if no StaleDataError: https://docs.sqlalchemy.org/en/14/orm/versioning.html   
            try:
                res = f(*args, **kwargs)            
                break
            except StaleDataError: 
                models.DB.session.rollback()
        return res 
    return decorated_function

from werkzeug.test import TestResponse
import sys
def throw_on_http_fail(resp: TestResponse):
    if resp.status_code >= 400:            
        APP.logger.error(f"[{resp.request.path}] failed for input {resp.request.json}:\n {resp.get_data(as_text=True)}")
        sys.exit(1)
    return resp.json

from flask.cli import AppGroup

quiz_cli = AppGroup('quiz')
student_cli = AppGroup('student') #responsible for student simulation

@quiz_cli.command("init")
@click.option('-nq', '--num-questions', required = True, type = int)
@click.option('-nd', '--num-distractors', required = True, type = int)
def start_quiz_init(num_questions, num_distractors):
    ''' Creates instructor, quiz, students for further testing 
        Note: flask app should be running
    '''
    instructor = {"email":"i@usf.edu", "firstname":"I", "lastname": "I", "password":"pwd"}
    def build_quiz(i, questions):
        return { "title": f"Quiz {i}", "description": "Test quiz", "questions_ids": questions}
    def build_question(i):
        return { "title": f"Question {i}", "stem": f"Question {i} Stem?", "answer": f"a{i}"}
    def build_distractor(i, question):
        return { "answer": f"d{i}/q{question}", "justification": f"d{i}/q{question} just"}
    with APP.test_client(use_cookies=True) as c: #instructor session
        throw_on_http_fail(c.post("/signup", json={**instructor, "retype":instructor["password"]}))
        throw_on_http_fail(c.post("/login",json=instructor))
        from sqlalchemy import func
        qids = []
        for _ in range(num_questions):
            q = build_question("X")
            dids = []
            resp = throw_on_http_fail(c.post("/questions", json=q))
            qid = resp["id"]
            qids.append(qid)
            q = build_question(qid)
            throw_on_http_fail(c.put(f"/questions/{qid}", json=q))
            for _ in range(num_distractors):
                d = build_distractor("X", qid)
                resp = throw_on_http_fail(c.post(f"/questions/{qid}/distractors", json=d))
                did = resp["id"]
                dids.append(did)
                d = build_distractor(did, qid)
                throw_on_http_fail(c.put(f"/distractors/{did}", json=d))
            throw_on_http_fail(c.post("/quizquestions", json={ "qid": str(qid), "distractors_ids": dids}))
        quiz = build_quiz("X", qids)
        resp = throw_on_http_fail(c.post("/quizzes", json=quiz))
        quiz_id = resp["id"]
        quiz = build_quiz(quiz_id, qids)
        throw_on_http_fail(c.put(f"/quizzes/{quiz_id}", json=quiz))
        APP.logger.info(f"Quiz with id {quiz_id} was created successfully!")

@student_cli.command("knows")
@click.option('-s', '--student', type = int)
@click.option('-d', '--distractor', type = int)
@click.option('-c', '--chance', required = True, type = float)
def add_student_knowledge(student, distractor, chance):
    student_ids = [ student ]
    if student is None: 
        # assuming all students 
        student_ids_plain = models.User.query.filter_by(role = ROLE_STUDENT).with_entities(models.User.id)
        student_ids = [s.id for s in student_ids_plain]
    distractor_ids = [ distractor ]
    if distractor is None: 
        distractor_ids_plain = models.Distractor.query.with_entities(models.Distractor.id)
        distractor_ids = [d.id for d in distractor_ids_plain]
     #TODO: consider to do bulk ops: https://docs.sqlalchemy.org/en/14/orm/persistence_techniques.html#bulk-operations
    for sid in student_ids:
        for did in distractor_ids:
            models.DB.session.add(models.StudentKnowledge(student_id = sid, distractor_id = did, chance_to_select = chance))            
    models.DB.commit()

APP.cli.add_command(quiz_cli)
APP.cli.add_command(student_cli)