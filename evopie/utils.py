# pylint: disable=no-member
# pylint: disable=E1101

# The following are flask custom commands; 
import flask_login
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


from flask import flash, redirect, url_for, request, abort
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
