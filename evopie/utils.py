# pylint: disable=no-member
# pylint: disable=E1101

# The following are flask custom commands; 

from datetime import datetime
from typing import Optional
from pytz import timezone
from evopie.config import QUIZ_HIDDEN, QUIZ_SOLUTIONS, QUIZ_STEP1, QUIZ_STEP2
from . import models, APP # get also DB from there
from quiz_model import get_quiz_builder

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
    models.DB.session.commit()
    if old_status != new_status:
        if new_status == QUIZ_STEP1:
            get_quiz_builder().create_quiz_model(quiz)
        else:
            get_quiz_builder().finalize_quiz_model(quiz)

        
    
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

