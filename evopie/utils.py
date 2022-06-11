# pylint: disable=no-member
# pylint: disable=E1101

# The following are flask custom commands; 

from evopie.config import EVO_PROCESS_STATUS_ACTIVE, EVO_PROCESS_STATUS_STOPPED, QUIZ_ATTEMPT_SOLUTIONS, QUIZ_ATTEMPT_STEP1, QUIZ_ATTEMPT_STEP2, QUIZ_SOLUTIONS, QUIZ_STEP1, QUIZ_STEP2, ROLE_STUDENT
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
    
# Defining a custom jinja2 filter to get rid of \"
# in JSON for student.html
import jinja2

@APP.template_filter('unescapeDoubleQuotes')
def unescape_double_quotes(s): 
    return s.replace('\\"','\"')

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
