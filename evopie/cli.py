from functools import reduce
from io import StringIO
from itertools import product
import json
import os
import click
from flask import g
from pandas import DataFrame, Series
import pandas
from werkzeug.test import TestResponse
import sys
import numpy as np
import matplotlib.pyplot as plt
import traceback

from evopie import APP, deca, models
from evopie.config import QUIZ_ATTEMPT_STEP1, QUIZ_STEP1, QUIZ_STEP2, ROLE_STUDENT
from evopie.utils import groupby, unpack_key
from evopie.quiz_model import get_quiz_builder, set_quiz_model

def throw_on_http_fail(resp: TestResponse, status: int = 400):
    if resp.status_code >= status:            
        sys.stderr.write(f"[{resp.request.path}] failed:\n {resp.get_data(as_text=True)}")
        sys.exit(1)
    return resp.json

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

from flask.cli import AppGroup

quiz_cli = AppGroup('quiz')
course_cli = AppGroup('course')
student_cli = AppGroup('student') #responsible for student simulation
deca_cli = AppGroup('deca')

@course_cli.command("init")
@click.option('-i', '--instructor', default='i@usf.edu')
@click.option('-n', '--name', default="")
@click.option('-t', '--title', default="")
@click.option('-d', '--description', default="")
def start_course_init(instructor, name, title, description):
    instructor = {"email":instructor, "firstname":"I", "lastname": "I", "password":"pwd"}
    course = {"name":name, "title":title, "description":description, "instructor_id": 1}
    with APP.test_client(use_cookies=True) as c:
        throw_on_http_fail(c.post("/signup", json={**instructor, "retype":instructor["password"]}), status=300)
        throw_on_http_fail(c.post("/login",json=instructor))
        throw_on_http_fail(c.post('/courses', json=course))

@quiz_cli.command("copy")
@click.option('-q', '--quiz-id')
@click.option('-cid', '--course-id', type=int, default=1)
def start_quiz_copy(quiz_id, course_id):
    instructor = {"email":"i@usf.edu", "firstname":"I", "lastname": "I", "password":"pwd"}
    with APP.test_client(use_cookies=True) as c: #instructor session
        throw_on_http_fail(c.post("/login",json=instructor))
        c.get(f"/quiz-copy/{quiz_id}", headers={"Accept": "application/json"})
        new_quiz_id = str(int(quiz_id) + 1)
        throw_on_http_fail(c.post(f"/course-editor/{course_id}", json={"selected_quizzes": [new_quiz_id]}))

@quiz_cli.command("settings")
@click.option('-q', '--quiz-id')
@click.option('-s', '--settings')
def edit_quiz_settings(quiz_id, settings):
    settings = json.loads(settings)
    with APP.test_client(use_cookies=True) as c: #instructor session
        throw_on_http_fail(c.post(f"/quizzes/{quiz_id}/status", json={ "status" : "HIDDEN" }))
        settings_for_quiz = { 
            "first_quartile_grade": settings.get("fq", 1),
            "second_quartile_grade": settings.get("sq", 3),
            "third_quartile_grade": settings.get("tq", 5),
            "fourth_quartile_grade": settings.get("frq", 10),
            "initial_score": settings.get("is", 40),
            "revised_score": settings.get("rs", 30),
            "justification_grade": settings.get("jg", 20),
            "participation_grade": settings.get("pg", 10),
            "designing_grade": settings.get("dg", 0),
        }
        throw_on_http_fail(c.post(f"/quiz/{quiz_id}/settings", json=settings_for_quiz))


@quiz_cli.command("init")
@click.option('-i', '--instructor', default='i@usf.edu')
@click.option('-cid', '--course-id', type=int, default=1)
@click.option('-nq', '--num-questions', required = True, type = int)
@click.option('-nd', '--num-distractors', required = True, type = int)
@click.option('-qd', '--question-distractors')
@click.option('-s', '--settings')
def start_quiz_init(instructor, course_id, num_questions, num_distractors, question_distractors, settings):
    ''' Creates instructor, quiz, students for further testing 
        Note: flask app should be running
    '''
    instructor = {"email":instructor, "firstname":"I", "lastname": "I", "password":"pwd"}
    def build_quiz(i, questions):
        return { "title": f"Quiz {i}", "description": "Test quiz", "questions_ids": questions, "step3_enabled": True}
    def build_question(i):
        return { "title": f"Question {i}", "stem": f"Question {i} Stem?", "answer": f"a{i}"}
    def build_distractor(i, question):
        return { "answer": f"d{i}/q{question}", "justification": f"d{i}/q{question} just"}
    if settings:
        settings = json.loads(settings)
    else:
        settings = {}
    if question_distractors:
        question_distractors = json.loads(question_distractors)
    else:
        question_distractors = {}
    with APP.test_client(use_cookies=True) as c: #instructor session
        throw_on_http_fail(c.post("/login",json=instructor))
        distractor_map = DataFrame(columns=["question", "distractor"])
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
                distractor_map.loc[len(distractor_map)] = (qid, did)
            throw_on_http_fail(c.post("/quizquestions", json={ "qid": str(qid), "distractors_ids": question_distractors.get(str(qid), dids)}))
        quiz = build_quiz("X", qids)
        resp = throw_on_http_fail(c.post("/quizzes", json=quiz))
        quiz_id = resp["id"]
        quiz = build_quiz(quiz_id, qids)
        throw_on_http_fail(c.put(f"/quizzes/{quiz_id}", json=quiz))
        sys.stdout.write(f"Quiz with id {quiz_id} was created successfully:\n{distractor_map}\n")
        # add quiz to course
        throw_on_http_fail(c.post(f"/course-editor/{course_id}", json={"selected_quizzes": [quiz_id]}))
        settings_for_quiz = { 
            "first_quartile_grade": settings.get("fq", 1),
            "second_quartile_grade": settings.get("sq", 3),
            "third_quartile_grade": settings.get("tq", 5),
            "fourth_quartile_grade": settings.get("frq", 10),
            "initial_score": settings.get("is", 40),
            "revised_score": settings.get("rs", 30),
            "justification_grade": settings.get("jg", 20),
            "participation_grade": settings.get("pg", 10),
            "designing_grade": settings.get("dg", 0),
        }
        throw_on_http_fail(c.post(f"/quiz/{quiz_id}/settings", json=settings_for_quiz))

@deca_cli.command("init")
@click.option('-q', '--quiz', type = int, required = True)
@click.option('-o', '--output') #folder were we should put generated spaces
@click.option('--fmt', default='space-{}.json') #folder were we should put generated spaces
@click.option('-a', "--axis", multiple=True, type = int, required=True) #generate knowledge from deca axes
@click.option('-ss', '--spanned-strategy', type=str, default=None)
@click.option('--spanned', type=int, default=0)
@click.option('--best-students-percent', type=float, default=0)
@click.option('--spanned-geometric-p', type=float, default=0.75)
@click.option('--noninfo', type=float, default=0)
@click.option('-n', type=int, default=1) #number of spaces to create
@click.option("--random-seed", type=int) #seed
@click.option("--timeout", default=1000000, type=int)
def create_deca_space(quiz, output, fmt, axis, spanned_strategy, spanned, best_students_percent, n, random_seed, spanned_geometric_p, noninfo, timeout):

    rnd = np.random.RandomState(random_seed) #here random_seed is None if not specified therefore we reassign it on next line
    random_seed = int(rnd.get_state()[1][0])
    sys.stdout.write(f"Generate DECA with random seed SEED: {random_seed}\n")
    
    # students = np.unique((input_students["email"].to_list() if input_students else []) + ([email_format.format(i + 1) for i in range(num_students)] if num_students else [])).tolist()
    with APP.app_context():
        students = models.User.query.where(models.User.role == ROLE_STUDENT).with_entities(models.User.email)
        emails = [s.email for s in students]

    with APP.app_context():
        quiz = models.Quiz.query.get(quiz)
        quiz_questions = quiz.quiz_questions
        question_ids = set(q.question_id for q in quiz_questions)    
        quiz_question_distractors = models.DB.session.query(models.quiz_questions_hub).where(models.quiz_questions_hub.c.quiz_question_id.in_(question_ids)).all()
        #NOTE: for additional validation we also could check that distractors exist in Distractor tables
        question_distractors = [ (q.quiz_question_id, q.distractor_id) for q in quiz_question_distractors ]
        #NOTE: quiz also should be used to connect instructor to generated students and namespace them from other students

    for i in range(n):
        spanned_strategy = spanned_strategy if spanned_strategy is not None else deca.SPANNED_STRATEGY_RANDOM if spanned > 0 else deca.SPANNED_STRATEGY_NONE
        space = deca.gen_deca_space(emails, tuple(axis), spanned_strategy, 
                    num_spanned = spanned, best_candidates_percent=best_students_percent, 
                    p = spanned_geometric_p, timeout=timeout, rnd = rnd)
        space = deca.gen_test_distractor_mapping(space, question_distractors, noninformative_percent=noninfo, rnd = rnd)
        space['meta'] = {'id': i, 'rnd': random_seed}
        # knowledge = deca.gen_test_distractor_mapping_knowledge(space)
        print(f"---\n{space}\n")
        if output:
            file_name = os.path.join(output, fmt.format(i))
            with open(file_name, 'w') as f: 
                f.write(deca.save_space_to_json(space))

@student_cli.command("init")
@click.option('-cid', '--course-id', type=int, default=1)
@click.option('-ns', '--num-students', type = int)
@click.option('--exclude-id', type = int, multiple=True)
@click.option('-ef', '--email-format', default="s{}@usf.edu")
@click.option('-i', '--input')
@click.option('-o', '--output') #csv file to output with student email, id
def init_students(course_id, num_students, exclude_id, input, output, email_format):
    if input is None and num_students is None: 
        sys.stderr.write("Either  ")
        sys.exit(1)
    def build_student(i):
        return {"email": email_format.format(i), "firstname":"S", "lastname": "S", "password":"pwd"}        

    input_students = None     
    if input is not None:
        columns = {"firstname": "", "lastname": "", "password": "pwd"}
        input_students = pandas.read_csv(input)
        for column in columns:
            if column not in input_students:
                input_students[column] = columns[column]
        input_students.dropna(subset=["email"])
        input_students[["firstname", "lastname", "password"]].fillna(columns)  
                
    students = DataFrame(columns=["email", "id", "created"])    

    with APP.test_client(use_cookies=True) as c:
        def create_student(student):
            resp = throw_on_http_fail(c.post("/signup", json={**student, "retype": student["password"]}), status=300)
            was_created = "id" in resp
            #NOTE: we ignore the fact that student is already present in the system - status_code for existing user is 200 with "redirect" in resp
            resp = throw_on_http_fail(c.post("/login", json={**student}))
            student_id = resp["id"]
            students.loc[student_id, [ "email", "id", "created" ]] = [ student["email"], student_id, was_created ]

        if input_students is not None: 
            for _, student in input_students.iterrows():
                create_student(student)
        if num_students is not None:
            for i in range(num_students):
                if (i+1) in exclude_id:
                    continue
                student = build_student(i + 1)
                create_student(student)
    student_ids = set(students["id"])
    for student_id in student_ids:
        student = models.User.query.get_or_404(student_id)
        course = models.Course.query.get_or_404(course_id)
        student.courses.append(course)
        models.DB.session.commit()
    models.StudentKnowledge.query.where(models.StudentKnowledge.student_id.in_(student_ids)).delete()
    models.DB.session.commit()
    if output is not None:
        students.to_csv(output, index=False)    
        sys.stdout.write(f"Students were saved to {output}:\n {students}\n")
    else: 
        sys.stdout.write(f"Students were created:\n {students}\n")

@student_cli.command("addToCourse")
@click.option('-cid', '--course-id', type=int, default=1)
def add_to_course(course_id):
    course = models.Course.query.get_or_404(course_id)
    students = models.User.query.filter(models.User.id > 1).all()
    for student in students:
        student.courses.append(course)
        models.DB.session.commit()

@student_cli.command("knows")
# @click.option('-q', '--quiz', type = int, required = True)
@click.option('-ef', '--email-format', default="s{}@usf.edu")
@click.option('-i', '--input')
@click.option('-o', '--output') #csv file to output with student email, id, knowledge
@click.option('-kr', '--knowledge-replace', is_flag=True)
@click.option('-k', '--knows', multiple=True) #should be json representation
@click.option("--deca-input") #json file where we take deca parameters from, ignored if deca-axis is provided
# @click.option("--deca-output") #json file where we output generated deca parameters
# @click.option("--deca-spanned")
def init_knowledge(input, output, email_format, knows, knowledge_replace, deca_input):
    # def build_student(i):
    #     return {"email": email_format.format(i), "firstname":"S", "lastname": "S", "password":"pwd"}        

    # with APP.app_context():
    #     quiz = models.Quiz.query.get(quiz)
    #     quiz_questions = quiz.quiz_questions
    #     question_ids = set(q.id for q in quiz_questions)    
    #     quiz_question_distractors = models.DB.session.query(models.quiz_questions_hub).where(models.quiz_questions_hub.c.quiz_question_id.in_(question_ids)).all()
    #     #NOTE: for additional validation we also could check that distractors exist in Distractor tables
    #     question_distractors = {qid:[q.distractor_id for q in qds] for qid, qds in groupby(quiz_question_distractors, key = lambda x: x.quiz_question_id)}
    #     #NOTE: quiz also should be used to connect instructor to generated students and namespace them from other students
    print(f"Student knows {input}, {output}, {email_format}, {knows}, {knowledge_replace}, {deca_input}")
    try:
        knows_map_input = {}
        if input is not None:
            input_students = pandas.read_csv(input)
            input_students.dropna(subset=["email"])
            for sid in input_students.index:
                s = input_students.loc[sid]
                for c in input_students.columns:
                    if c.startswith("d_") and s[c]:
                        qid, did, step = (int(id) for id in c.split("_")[1:])
                        knows_map_input.setdefault(s["email"], {}).setdefault(qid, {}).setdefault(did, [np.nan, np.nan])[step - 1] = s[c]
        
        #NOTE: if step is provided - the knowledge will not be passed to next steps 
        #NOTE: otherwise if metrics is a list - elements are treated as chances for each step sequentially
        #NOTE: otherwise metrics defines value for all steps
        def dks_reducton(acc, k):
            ''' adds chances from simple knows record '''
            # try:
            if "step" in k:
                local_step = k["step"] - 1
                metrics = k["metrics"]
                acc[local_step] = metrics[local_step] if type(metrics) == list else metrics
            elif type(k["metrics"]) == list:
                for i in range(min(len(acc), len(k["metrics"]))):
                    acc[i] = k["metrics"][i]
            else: 
                for i in range(len(acc)):
                    if acc[i] < 0:
                        acc[i] = k["metrics"]
            # except Exception as e: 
            #     print(e)
            return acc 

        knows_map_deca = {} 
        if deca_input:
            with open(deca_input, 'r') as deca_input_json_file:
                deca_input_json_str = "\n".join(deca_input_json_file.readlines())
                space = deca.load_space_from_json(deca_input_json_str)
                knows_map_deca_plain = deca.gen_test_distractor_mapping_knowledge(space)
                knows_unpacked = unpack_key('did', unpack_key('qid', unpack_key('sid', knows_map_deca_plain)))
                knows_map_deca = {sid: {qid: {did: reduce(dks_reducton, dks, [-1,-1])
                                    for did, dks in groupby(qks, key = lambda x: x.get("did", "*")) } 
                                    for qid, qks in groupby(sks, key = lambda x: x.get("qid", "*")) } 
                                    for sid, sks in groupby(knows_unpacked, key = lambda x: x.get("sid", "*"))} 
            

        knows = [json.loads(k) for k in knows]  #NOTE: expected format {'sid':<opt, by default all>, 'qid':<opt, by default all>, 'did':<opt, by default all>, choice:num or [step1_c, step2_c] }
        knows_unpacked = unpack_key('did', unpack_key('qid', unpack_key('sid', knows)))

        knows_map_args = {email_format.format(sid): {qid: {did: reduce(dks_reducton, dks, [-1,-1])
                            for did, dks in groupby(qks, key = lambda x: x.get("did", "*")) } 
                            for qid, qks in groupby(sks, key = lambda x: x.get("qid", "*")) } 
                            for sid, sks in groupby(knows_unpacked, key = lambda x: x.get("sid", "*"))}    
            
        distractor_map = None
        with_wild_did = [(qid, qks) for sks in knows_map_args.values() for qid, qks in sks.items() if qid != "*" and "*" in qks]
        if len(with_wild_did) > 0: #remove wild dids 
            if not distractor_map:
                distractor_ids = models.Distractor.query.with_entities(models.Distractor.id, models.Distractor.question_id)
                distractor_map = {qid:set(d.id for d in qds) for qid, qds in groupby(distractor_ids, key = lambda x: x.question_id) }
            for (qid, qks) in with_wild_did:
                for did in distractor_map.get(qid, []):
                    qks.setdefault(did, list(qks["*"]))
                del qks["*"]    
        
        with_wild_qid = [(sid, sks) for sid, sks in knows_map_args.items() if "*" in sks]    
        if len(with_wild_qid) > 0: #remove wildcard for qid        
            if not distractor_map:
                distractor_ids = models.Distractor.query.with_entities(models.Distractor.id, models.Distractor.question_id)
                distractor_map = {qid:set(d.id for d in qds) for qid, qds in groupby(distractor_ids, key = lambda x: x.question_id) }                
            new_knows = {}
            for sid, sks in with_wild_qid:            
                new_sks = new_knows.setdefault(sid, {})
                qks = sks["*"]
                for qid, dids in distractor_map.items():
                    if "*" in qks: #for all distractors
                        for did in dids:
                            new_sks.setdefault(qid, {}).setdefault(did, qks["*"])
                    for did, dks in qks.items():
                        if did in dids:
                            new_sks.setdefault(qid, {}).setdefault(did, dks)
            for sid, sks in new_knows.items():
                for qid, qks in sks.items():
                    for did, dks in qks.items():
                        knows_map_args.setdefault(sid, {}).setdefault(qid, {}).setdefault(did, dks)
            for _, sks in with_wild_qid: 
                del sks["*"]

        knows_map = {**knows_map_input, **knows_map_deca, **knows_map_args}        
        students = DataFrame(columns=["email", "id"])    

        distractor_column_order = list(sorted(set([ (i+1, qid, did) for skn in knows_map.values() for qid, qkn in skn.items() for did, dkn in qkn.items() for i, metrics in enumerate(dkn)])))
        distractor_columns = [f'd_{q}_{d}_{step}' for step, q, d in distractor_column_order]

        with APP.test_client(use_cookies=True) as c:
            all_students = models.User.query.where(models.User.role == ROLE_STUDENT).with_entities(models.User.email, models.User.id)
            email_to_id = {}
            id_to_email = {}
            for s in all_students:
                email_to_id[s.email] = s.id 
                id_to_email[s.id] = s.email
            def init_knowledge_from_map(knowledge_map):
                def add_to_students(email, student_id, student_knowledge):
                    distractors = {(i+1, qid, did):metrics for qid, qks in student_knowledge.items() for did, dks in qks.items() for i, metrics in enumerate(dks)}
                    students.loc[student_id, [ "email", "id", *distractor_columns ]] = [email, student_id, *[distractors[kid] if kid in distractors else np.nan for kid in distractor_column_order]]                
                if "*" in knowledge_map:
                    for student_id, email in id_to_email.items():
                        add_to_students(email, student_id, knowledge_map["*"])
                for student_id, student_knowledge in knowledge_map.items():
                    if student_id in id_to_email:
                        email = id_to_email[student_id]
                        add_to_students(email, student_id, student_knowledge)
                for student_email, student_knowledge in knowledge_map.items():
                    if student_email in email_to_id:
                        student_id = email_to_id[student_email]
                        add_to_students(student_email, student_id, student_knowledge)
            init_knowledge_from_map(knows_map_input)
            init_knowledge_from_map(knows_map_deca)
            init_knowledge_from_map(knows_map_args)

        student_ids = set(students["id"])
        present_knowledge_query = models.StudentKnowledge.query.where(models.StudentKnowledge.student_id.in_(student_ids))
        if knowledge_replace: 
            present_knowledge_query.delete()
            present_knowledge = {}
        else:
            present_plain = present_knowledge_query.all()
            present_knowledge = {kid:ks[0] for kid, ks in groupby(present_plain, key=lambda k: (k.student_id, k.question_id, k.distractor_id, k.step_id))}
        for _, student in students.iterrows(): 
            for c in student[student.notnull()].index:
                if c.startswith("d_"):    
                    question_id, distractor_id, step_id = [int(x) for x in c.split('_')[1:]]
                    knowledge_id = student.id, question_id, distractor_id, step_id
                    if knowledge_id in present_knowledge:
                        present_knowledge[knowledge_id].metrics = student[c]
                    else:
                        k = models.StudentKnowledge(student_id=student.id, question_id = question_id, distractor_id=distractor_id, step_id = step_id, metrics = student[c])
                        models.DB.session.add(k) 
        for (sid, qid, did, step), v in present_knowledge.items():
            if sid in students.index: 
                column = f'd_{qid}_{did}_{step}'
                if np.isnan(students.loc[sid, column]):
                    students.loc[sid, column] = v.metrics
        models.DB.session.commit()
        if output is not None:
            students.to_csv(output, index=False)    
            sys.stdout.write(f"Students were saved to {output}:\n {students}\n")
        else: 
            sys.stdout.write(f"Students were created:\n {students}\n")
    except Exception as e:
        print(e)
        raise

@student_cli.command("export")        
@click.option('-o', '--output')
def export_student_knowledge(output): 
    students = models.User.query.where(models.User.role == ROLE_STUDENT).all()
    knowledge = models.StudentKnowledge.query.all()
    ids = list(sorted(set([ (k.step_id, k.question_id, k.distractor_id) for k in knowledge ])))
    knowledge_map = {sid:{f'd_{k.question_id}_{k.distractor_id}_{k.step_id}':k.metrics for k in ks} for sid, ks in groupby(knowledge, key=lambda k: k.student_id) }
    distractor_columns = [ f'd_{qid}_{did}_{step}' for step, qid, did in ids ]
    df = DataFrame(columns=['email', 'id', *distractor_columns])
    for s in students:
        df.loc[s.id, ['email', 'id']] = [s.email, s.id]
        skn = knowledge_map.get(s.id, {})
        for (step, qid, did) in ids:
            column_name = f'd_{qid}_{did}_{step}'
            if column_name in skn:
                df.loc[s.id, column_name] = skn[column_name]
    if output is not None: 
        df.to_csv(output, index=False)
    sys.stdout.write(f"Exported knowledge:\n{df}\n")

KNOWLEDGE_SELECTION_CHANCE = "KNOWLEDGE_SELECTION_CHANCE"
KNOWLEDGE_SELECTION_WEIGHT = "KNOWLEDGE_SELECTION_WEIGHT"
KNOWLEDGE_SELECTION_STRENGTH = "KNOWLEDGE_SELECTION_STRENGTH"

@quiz_cli.command("run")
@click.option('-q', '--quiz', type=int, required=True)
@click.option('-cid', '--course_id', type=int, default=1)
@click.option('-s', '--step', default = [QUIZ_STEP1], multiple=True)
@click.option('-n', '--n-times', type=int, default=1)
@click.option('-kns', '--knowledge-selection', default = KNOWLEDGE_SELECTION_STRENGTH)
@click.option('-i', '--instructor', default='i@usf.edu')
@click.option('-p', '--password', default='pwd') 
@click.option('--no-algo', is_flag=True) #randomize student order
@click.option('--algo') #evo algo to use
@click.option('--algo-params') #json settings of algo
@click.option('--rnd', is_flag=True) #randomize student order
@click.option('--archive-output')
@click.option('--evo-output')
@click.option('-l', '--likes', multiple=True)
@click.option('--justify-response', is_flag=True)
@click.option('-ef', '--email-format', default="s{}@usf.edu")
@click.option('--random-seed', type=int)
def simulate_quiz(quiz, course_id, instructor, password, no_algo, algo, algo_params, rnd, n_times, archive_output, evo_output, step, knowledge_selection, likes, justify_response, email_format, random_seed):        
    rnd_state = np.random.RandomState(random_seed)
    if no_algo:
        set_quiz_model(None)
    elif algo is not None:         
        set_quiz_model(algo, settings = json.loads(algo_params) if algo_params is not None else {})

    def simulate_step(step):
        with APP.app_context():
            k_plain = models.StudentKnowledge.query.where(models.StudentKnowledge.step_id == step).all() #TODO: students should be per instructor eventually 
            knowledge = {student_id: { str(qid): {x.distractor_id: x.metrics for x in qks} for qid, qks in groupby(ks, key=lambda x: x.question_id)} for student_id, ks in groupby(k_plain, key=lambda k: k.student_id) }
            students_plain = models.User.query.filter_by(role=ROLE_STUDENT).all()
            students = list(students_plain) #[s.id for s in students_plain]
            student_ids = set([s.id for s in students])
            if step == 1:
                models.QuizAttempt.query.where(models.QuizAttempt.student_id.in_(student_ids), models.QuizAttempt.quiz_id == quiz, models.QuizAttempt.course_id==course_id).delete()
                models.DB.session.commit()
            elif step == 2:
                models.Likes4Justifications.query.where(models.Likes4Justifications.student_id.in_(student_ids)).delete()
                models.DB.session.commit()
            if rnd:
                rnd_state.shuffle(students)
            ids_emails = [(student.id, student.email) for student in students]
        # if step == 1:
        #     #additional justifications
        #     justifications_json = [json.loads(j) for j in justifications]
        #     justifications_unpacked = unpack_key('did', unpack_key('qid', unpack_key('sid', justifications_json)))
        #     justifications_map = {sid:{str(qid):[j["did"] for j in qjs] for qid, qjs in groupby(sjs, key = lambda x: x["qid"])}
        #                             for sid, sjs in groupby(justifications_unpacked, key = lambda x: x["sid"]) }
        if step == 2: #student should like something
            #NOTE: no support for wildcard * for likes 
            likes_json = [json.loads(k) for k in likes]
            likes_unpacked = unpack_key("jid", unpack_key("sid", likes_json))
            likes_map = {email_format.format(sid):{str(l["jid"]):True for l in slikes} for sid, slikes in groupby(likes_unpacked, key = lambda x: x["sid"])}        
        for (sid, email) in ids_emails:
            with APP.test_client(use_cookies=True) as c:
                with APP.app_context():
                    resp = throw_on_http_fail(c.post("/login", json={"email": email, "password": "pwd"}))
                    if "id" not in resp:
                        continue #ignore non-default students
                    resp = throw_on_http_fail(c.get(f"/student/{quiz}/{course_id}/start", headers={"Accept": "application/json"}))
                    resp = throw_on_http_fail(c.get(f"/student/{quiz}/{course_id}", headers={"Accept": "application/json"}))

                with APP.app_context():
                    attempt = models.QuizAttempt.query.where(models.QuizAttempt.quiz_id == quiz, models.QuizAttempt.student_id == sid, models.QuizAttempt.course_id == course_id).first()

                student_knowledge = knowledge.get(sid, {})
                if knowledge_selection == KNOWLEDGE_SELECTION_CHANCE:
                    responses = {qid:rnd_state.choice(known_distractors)
                                            for qid, distractors in attempt.alternatives_map.items() 
                                            for qskn in [student_knowledge.get(qid, {-1:{"chance":1}}) ]
                                            for ds_distr in [[(alt, qskn[d]["chance"]) for alt, d in enumerate(distractors) if d in qskn]] 
                                            for ds in [ds_distr if any(ds_distr) else [(alt, 1) for alt, d in enumerate(distractors) if d == -1]]
                                            for known_distractors in [[alt for alt, w in ds if rnd_state.rand() < w ]]}
                elif knowledge_selection == KNOWLEDGE_SELECTION_WEIGHT:
                    responses = {qid:ds[selected_d_index][0]
                                            for qid, distractors in attempt.alternatives_map.items() 
                                            for qskn in [student_knowledge.get(qid, {-1:{"weight":1}}) ]
                                            for ds_distr in [[(alt, qskn[d]["weight"]) for alt, d in enumerate(distractors) if d in qskn]] 
                                            for ds in [ds_distr if any(ds_distr) else [(alt,1) for alt, d in enumerate(distractors) if d == -1]]
                                            for weights in [[w for _, w in ds]]
                                            for sums in [np.cumsum(weights)]
                                            for level in [(rnd_state.rand() * sums[-1]) if len(sums) > 0 else None]
                                            for selected_d_index in [next((i for i, s in enumerate(sums) if s > level), None)]}
                elif knowledge_selection == KNOWLEDGE_SELECTION_STRENGTH:
                    responses = {qid:sorted(ds, key=lambda x: x[1])[-1][0]
                                            for qid, distractors in attempt.alternatives_map.items() 
                                            for distractor_strength in [student_knowledge.get(qid, {}) ]
                                            for ds_distr in [[(alt, distractor_strength[d]["order"] + 0.001 * d) for alt, d in enumerate(distractors) if d in distractor_strength]] 
                                            for ds in [ds_distr if any(ds_distr) else [(alt,1) for alt, d in enumerate(distractors) if d == -1]]}
                else: 
                    responses = {}

                json_resp = {"question": responses}
                if step == 1:
                    # student_justifications_map = justifications_map.get(sid, {})             
                    json_resp["justification"] = {qid:{str(altid):f"s{sid}_q{qid}_o{altid}_d{did}" 
                                                for altid, did in enumerate(alternatives) if altid != responses.get(qid, None) or justify_response }
                                                for qid, alternatives in attempt.alternatives_map.items()}
                elif step == 2 and email in likes_map:
                    with APP.app_context():
                        g.ignore_selected_justifications = True
                        resp = throw_on_http_fail(c.put(f"/quizzes/{quiz}/{course_id}/justifications/like", json=likes_map[email]))
                with APP.app_context():
                    g.allow_justification_for_selected = True #do not delete justifications for selection
                    resp = throw_on_http_fail(c.post(f"/student/{quiz}/{course_id}", json=json_resp))
        
    for run_idx in range(n_times):
        #close prev evo process
        if QUIZ_STEP1 in step:
            with APP.app_context():
                models.EvoProcess.query.delete()            
                models.DB.session.commit()    
            with APP.app_context(), APP.test_client(use_cookies=True) as c: #instructor session
                throw_on_http_fail(c.post("/login",json={"email": instructor, "password": password}))
                throw_on_http_fail(c.post(f"/quizzes/{quiz}/status", json={ "status" : "HIDDEN" })) #stop in memory evo process
                throw_on_http_fail(c.post(f"/quizzes/{quiz}/status", json={ "status" : "STEP1" }))
                # evo process started 

            simulate_step(1)

            with APP.app_context():
                quiz_model = get_quiz_builder().load_quiz_model(quiz)
                if quiz_model is None:
                    sys.stdout.write(f"[{run_idx + 1}/{n_times}] Step1 quiz {quiz} finished\n")            
                else:
                    settings = quiz_model.get_model_state()
                    best_distractors = quiz_model.get_best_quiz()

                    if archive_output is not None: 
                        quiz_model.to_csv(archive_output.format(run_idx))
                    
                    search_space_size = quiz_model.get_search_space_size()
                    explored_search_space_size = quiz_model.get_explored_search_space_size()
                    sys.stdout.write(f"EVO algo: {quiz_model.__class__}\nEVO settings: {settings}\n")
                    if evo_output: 
                        with open(evo_output, 'w') as evo_output_json_file:
                            evo_output_json_file.write(json.dumps({"settings": settings, "distractors": best_distractors, 
                                                        "algo": quiz_model.__class__.__name__, 
                                                        "explored_search_space_size": explored_search_space_size,
                                                        "search_space_size": search_space_size}, indent=4))
                    sys.stdout.write(f"[{run_idx + 1}/{n_times}] Step1 quiz {quiz} finished\n{quiz_model.to_dataframe()}\n")
        if QUIZ_STEP2 in step: 
            with APP.app_context(), APP.test_client(use_cookies=True) as c: #instructor session
                throw_on_http_fail(c.post("/login",json={"email": instructor, "password": password}))
                throw_on_http_fail(c.post(f"/quizzes/{quiz}/status", json={ "status" : "STEP2" }))

            simulate_step(2)            

            sys.stdout.write(f"[{run_idx + 1}/{n_times}] Step2 Quiz {quiz} finished\n")

@deca_cli.command("result")
@click.option('--algo-input', required=True)
@click.option('--deca-space', required=True)
@click.option('-p', '--params', multiple=True) #params to take from algo-input json and put into final dataFrame
@click.option('-io', '--input_output')
def calc_deca_metrics(algo_input, deca_space, params, input_output):
    with open(algo_input, 'r') as f:
        algo_results = json.loads("\n".join(f.readlines()))
    with open(deca_space, 'r') as f:
        space = deca.load_space_from_json("\n".join(f.readlines()))
    population_distractors = algo_results["distractors"]
    algo_name = algo_input.split("/")[-1].split(".")[0]
    deca_name = deca_space.split("/")[-1].split(".")[0]
    metrics_map = {"algo":algo_name,"deca": deca_name, "seed": algo_results.get("settings", {}).get("seed", 0),
                    **deca.dimension_coverage(space, population_distractors),
                    **deca.avg_rank_of_repr(space, population_distractors),
                    **deca.redundancy(space, population_distractors),
                    **deca.duplication(space, population_distractors),
                    **deca.noninformative(space, population_distractors)}
    try:
        metrics = pandas.read_csv(input_output)
        # exisingMetric = metrics[(metrics["algo"] == algo_input) & (metrics["deca"] == deca_space)]
        # if len(exisingMetric) == 0:
        metrics.loc[len(metrics.index), list(metrics_map.keys())] = list(metrics_map.values())
        # else:         
        #     exisingMetric[list(metrics_map.keys())] = list(metrics_map.values())
    except FileNotFoundError:
        metrics = DataFrame([metrics_map])
    metrics.to_csv(input_output, index=False)   
    submetrics = metrics[["dim_coverage", "arr", "arra", "population_redundancy", "population_duplication", "noninfo"]]
    sys.stdout.write(f"Metrics:\n{submetrics}\n")

@deca_cli.command("space-result")
@click.option('-r', '--result-folder')
@click.option('-s', '--sort-column', default='algo')
@click.option('-f', '--filter-column', default=None)
@click.option('--stats-column', default=None)
@click.option('--scale', default=1, type=float)
@click.option('--no-group', is_flag=True)
def calc_space_result(result_folder, sort_column, filter_column, stats_column, no_group, scale):
    metrics = ['dim_coverage', 'arr', 'arra', 'population_redundancy', 'population_duplication', 'noninfo']
    res = DataFrame(columns=['space', 'algo', *[c for m in metrics for c in [m, m + '_std']]])
    dframes = {}
    for file_name in os.listdir(result_folder): 
        key = file_name if no_group else "-".join(file_name.split(".")[0].split("-")[:-1])        
        space_result = os.path.join(result_folder, file_name)
        algo_stats = pandas.read_csv(space_result)
        dframes.setdefault(key, []).append(algo_stats)
        # idx = len(res.index)        
        # res.loc[idx, 'algo'] = algo_stats.loc[0, 'algo'].split("/")[-1].split(".")[0]
        # res.loc[idx, metrics] = algo_stats[metrics].mean()
        # res.loc[idx, [m + '_std' for m in metrics]] = algo_stats[metrics].std().tolist()    
    if stats_column is not None: 
        #NOTE: need to install scipy, scikit-posthocs
        import scipy.stats as stats
        import scikit_posthocs as sp
        stats_samples = {}

    for key, lst in dframes.items():
        algo_stats = pandas.concat(lst)
        idx = len(res.index)   
        algo, space = key.split("-on-")   
        # if "_sp" in algo or "_dp" in algo: 
        # if "_sp" in algo: 
            # continue
        _, space_axes, space_spanned, *space_other = space.split("-")
        _, spanned_str = space_spanned.split('_')
        axes_str = space_axes.split('_')
        space_id = (int(spanned_str), len(axes_str), int(axes_str[0]), "" if len(space_other) == 0 else '-'.join(space_other))
        res.loc[idx, 'space'] = space_id
        res.loc[idx, 'algo'] = algo        
        algo_mean = algo_stats[metrics].mean()
        if stats_column is not None: 
            stats_samples.setdefault(space_id, {})[algo] = (algo_stats[stats_column].tolist()[-30:], algo_mean[stats_column])
        res.loc[idx, metrics] = algo_mean
        res.loc[idx, [m + '_std' for m in metrics]] = algo_stats[metrics].std().tolist()
    res[[m + '_std' for m in metrics]] = res[[m + '_std' for m in metrics]].astype(float)
    res[metrics] = res[metrics].astype(float)    
    res.rename(columns={'dim_coverage':'D', 'arr':'ARR', 'arra': 'ARRA', 'population_redundancy':'R', 'population_duplication':'Dup', 'noninfo':'nI',
                            'dim_coverage_std':'D_std', 'arr_std':'ARR_std', 'arra_std': 'ARRA_std', 'population_redundancy_std':'R_std', 'population_duplication_std':'Dup_std', 'noninfo_std':'nI_std'}, inplace=True)
    res.sort_values(by = ['space', sort_column, f"{sort_column}_std"], inplace=True, ascending=[True, False, True])
    res = res.round(3)
    if filter_column:
        ms = filter_column.split(',')
        res = res[['space', "algo", *[c for m in ms for c in [m, m + '_std']]]]
    if stats_column is not None:
        for space, algos in sorted(stats_samples.items(), key = lambda x: x[0]):  
            plain_algo_res = [(a, v, m) for (a, (v, m)) in algos.items()]
            sorted_algo_res = sorted(plain_algo_res, key=lambda x: -x[2])
            algo_names, algo_values, algo_means = zip(*sorted_algo_res)
            data = np.array([algo_res for algo_res in algo_values]).T
            friedman_res = stats.friedmanchisquare(*data.T)
            nemenyi_res = sp.posthoc_nemenyi_friedman(data) 
            p=0.10
            algo_m = {algo: algo_means[i] for i, algo in enumerate(algo_names)}
            print(f"\n----------------------------------")
            print(f"Stat result for space {space}")
            print(f"Algo: {algo_m}")
            print(f"Friedman: {friedman_res}")
            # print(f"Nemenyi:\n{nemenyi_res}")
            #we now assign score for each algo based on nemenyi p-value result 
            domination = {algo_name: {algo_names[j]: p_val for j, p_val in enumerate(nemenyi_res[i]) if p_val <= p and j > i}
                            for i, algo_name in enumerate(algo_names) }
            for algo_name, dominated in domination.items():
                if len(dominated) > 0: 
                    print(f"\t{algo_name} (mean {algo_m[algo_name]}) dominates {dominated}")

            space_res = res[res['space'] == space].drop(columns = 'space')
            print("\\# & ", end="")
            for col_id in space_res.columns:
                if not col_id.endswith("_std"):
                    print(f"{col_id} & ", end="")
            print(">_{0.1}\\\\\\hline")
            algo_index = {data['algo']: (i + 1) for i, (_, data) in enumerate(space_res.iterrows())}
            for i, (_, data) in enumerate(space_res.iterrows()):                
                print("{0: <3} & ".format(i+1), end="")
                for col_id, col_val in data.iteritems():
                    if col_id.endswith("_std"):
                        print(" $\pm$ {:.1f}\t& ".format(col_val * scale), end="")
                    else:
                        if type(col_val) == float: 
                            print("{:.1f}".format(col_val * scale), end = "")
                        else:
                            col_val = col_val.replace('_', '\_').replace('|', '+')
                            # col_val = col_val + '(2)' if col_val.startswith('phc') else col_val
                            print("{0: <40}& ".format(col_val), end="")
                dominated = sorted([algo_index[algo_name] for algo_name in domination[data['algo']].keys()])
                dominated_fmtd = [] 
                for idx in dominated: 
                    if len(dominated_fmtd) == 0:
                        dominated_fmtd.append([idx, idx])
                    elif dominated_fmtd[-1][-1] == idx - 1:
                        dominated_fmtd[-1][-1] = idx
                    else:
                        dominated_fmtd.append([idx, idx])
                print(",".join([f'{s}-{e}' if s != e else str(s) for s, e in dominated_fmtd]), end="")
                print("\\\\")
                # cur_group.append(algo_name)
                # for j in range(i + 1, len(nemenyi_res[i])):
                #     if nemenyi_res[i, j] > p: 
                #         cur_group.append()

    res.to_csv(os.path.join(result_folder, '../space-result.csv'), index=False)
    # print(res.to_string(index=False))

    # return { 'm_std': moments,
    #         'friedman': stats.friedmanchisquare(*fsa),
    #         'nemenyi': sp.posthoc_nemenyi_friedman(fsa.T) 
    #         # 'ttest': stats.ttest_ind(fs[0], fs[1], equal_var=False, alternative='two-sided'), 'utest': stats.mannwhitneyu(fs[0], fs[1],alternative='two-sided')
    #         }


@deca_cli.command("space-ranks")
@click.option('-r', '--result-folder')
def calc_space_ranks(result_folder):
    metrics = ['arra']
    res = DataFrame(columns=['space', 'algo', *[c for m in metrics for c in [m, m + '_std']]])
    res_by_seeds = {}
    for file_name in os.listdir(result_folder): 
        space_result = os.path.join(result_folder, file_name)
        algo_stats = pandas.read_csv(space_result)
        is_first = len(res_by_seeds) == 0
        algo, space = file_name.split("-on-")  
        if "_sp" in algo or "_dp" in algo: 
            continue
        _, space_axes, space_spanned, *space_other = space.split("-")
        _, spanned_str = space_spanned.split('_')
        axes_str = space_axes.split('_')
        space_id = (int(spanned_str), len(axes_str), int(axes_str[0]), "" if len(space_other) == 0 else '-'.join(space_other))

        for _, x in algo_stats[['seed', 'arra']].iterrows():
            seed = int(x['seed'])
            # assert is_first or seed in res_by_seeds, 'Rand seed is different'
            res_by_seeds.setdefault(space_id, {}).setdefault(seed, []).append((algo, x['arra']))

    from scipy.stats import rankdata
    space_res = []
    for space_id, seeds in res_by_seeds.items():
        assert len(seeds) == 30
        algo_res = {}
        for seed, algos in seeds.items():
            ranked = rankdata([-arra for _, arra in algos])
            min_rank = min(ranked)
            for a, r in zip([algo for algo, _ in algos], ranked):
                algo_res.setdefault(a, []).append((r, 1 if r == min_rank else 0))      
        res = []
        for a, ranks in algo_res.items():
            assert len(ranks) == 30 
            res.append((a, np.mean([r for r, _ in ranks]), np.std([r for r, _ in ranks]), sum(r for _, r in ranks)))
        res.sort(key = lambda x:-x[3])
        space_res.append((space_id, res))
    space_res.sort(key=lambda x:x[0])
    order_by_cnt = {}
    for _, res in space_res:
        for a, _, _, cnt in res:
            order_by_cnt[a] = order_by_cnt.get(a, 0) + cnt
    print("algo", end="")
    for space_id, res in space_res:
        res.sort(key = lambda x:-order_by_cnt[x[0]])
        space_idx = int(space_id[-1].split('.')[0]) + 1
        print(" & {0}".format(space_idx), end="")
    print("& $\sum$\\\\\\hline")
    for algo_id, (algo, _, _, _) in enumerate(space_res[0][1]):
        col_val = algo.replace('_', '\_').replace('|', '+')
        print("{0: <20}".format(col_val), end="")
        for space_id, res in space_res:
            # print(" & {0:.1f} $\pm$ {1:.1f}".format(res[algo_id][1], res[algo_id][2]), end="")
            print(" & {0}".format(res[algo_id][3]), end="")
        print(" & {0}".format(order_by_cnt[algo]), end="")
        print("\\\\")
        # print("{:.1f}".format(col_val * scale), end = "")s
    print("\\hline")
    

@deca_cli.command("space-distr")
@click.option('-s', '--space-folder')
@click.option('-f', '--file-name')
@click.option('--from-point', type=int)
@click.option('--to-point', type=int)
def calc_space_ranks(space_folder, file_name, from_point, to_point):
    if file_name is not None and from_point is not None and to_point is not None: 
        space_file = os.path.join(os.path.abspath(space_folder), file_name)
        with open(space_file, 'r') as f:
            space = json.loads("\n".join(f.readlines()))
        for points in space['axes'].values():
            a, b = points[str(from_point)]['dids'], points[str(to_point)]['dids']
            points[str(to_point)]['dids'] = a  
            points[str(from_point)]['dids'] = b
        with open(space_file, 'w') as f:
            f.write(json.dumps(space))
    else:
        res = []
        for file_name in os.listdir(space_folder): 
            space_file = os.path.join(space_folder, file_name)
            with open(space_file, 'r') as f:
                space = json.loads("\n".join(f.readlines()))
            distr_cnt = [len(point['dids']) for axis_id, axis in space['axes'].items() for point_id, point in axis.items()]        
            total_distrs = sum(distr_cnt) + len(space['zero']['dids'])
            dstr = [len(axis[str(space['dims'][int(axis_id)] -  1)]['dids']) 
                                for axis_id, axis in space['axes'].items()]
            distrs_at_ends = sum(dstr) / total_distrs * 100
            distr_cnt = set([tuple([len(point['dids']) for point_id, point in axis.items()]) for axis_id, axis in space['axes'].items()])
            res.append((file_name, distrs_at_ends, np.mean(dstr), np.std(dstr), distr_cnt))
        res.sort(key = lambda x:x[0])
        for r in res:
            print(r)


    
        # idx = len(res.index)        
        # res.loc[idx, 'algo'] = algo_stats.loc[0, 'algo'].split("/")[-1].split(".")[0]
        # res.loc[idx, metrics] = algo_stats[metrics].mean()
        # res.loc[idx, [m + '_std' for m in metrics]] = algo_stats[metrics].std().tolist()    
    # if stats_column is not None: 
    #     #NOTE: need to install scipy, scikit-posthocs
    #     import scipy.stats as stats
    #     import scikit_posthocs as sp
    #     stats_samples = {}

    # for key, lst in dframes.items():
    #     algo_stats = pandas.concat(lst)
    #     idx = len(res.index)   
    #     algo, space = key.split("-on-")   
    #     if "_sp" in algo or "_dp" in algo: 
    #         continue
    #     _, space_axes, space_spanned, *space_other = space.split("-")
    #     _, spanned_str = space_spanned.split('_')
    #     axes_str = space_axes.split('_')
    #     space_id = (int(spanned_str), len(axes_str), int(axes_str[0]), "" if len(space_other) == 0 else '-'.join(space_other))
    #     res.loc[idx, 'space'] = space_id
    #     res.loc[idx, 'algo'] = algo        
    #     algo_mean = algo_stats[metrics].mean()
    #     # if stats_column is not None: 
    #     #     stats_samples.setdefault(space_id, {})[algo] = (algo_stats[stats_column].tolist()[-30:], algo_mean[stats_column])
    #     res.loc[idx, metrics] = algo_mean
    #     res.loc[idx, [m + '_std' for m in metrics]] = algo_stats[metrics].std().tolist()
    # res[[m + '_std' for m in metrics]] = res[[m + '_std' for m in metrics]].astype(float)
    # res[metrics] = res[metrics].astype(float)    
    # res.rename(columns={'dim_coverage':'D', 'arr':'ARR', 'arra': 'ARRA', 'population_redundancy':'R', 'population_duplication':'Dup', 'noninfo':'nI',
    #                         'dim_coverage_std':'D_std', 'arr_std':'ARR_std', 'arra_std': 'ARRA_std', 'population_redundancy_std':'R_std', 'population_duplication_std':'Dup_std', 'noninfo_std':'nI_std'}, inplace=True)
    # res.sort_values(by = ['space', sort_column, f"{sort_column}_std"], inplace=True, ascending=[True, False, True])
    # res = res.round(3)
    # if filter_column:
    #     ms = filter_column.split(',')
    #     res = res[['space', "algo", *[c for m in ms for c in [m, m + '_std']]]]
    # if stats_column is not None:
    #     for space, algos in sorted(stats_samples.items(), key = lambda x: x[0]):  
    #         plain_algo_res = [(a, v, m) for (a, (v, m)) in algos.items()]
    #         sorted_algo_res = sorted(plain_algo_res, key=lambda x: -x[2])
    #         algo_names, algo_values, algo_means = zip(*sorted_algo_res)
    #         data = np.array([algo_res for algo_res in algo_values]).T
    #         friedman_res = stats.friedmanchisquare(*data.T)
    #         nemenyi_res = sp.posthoc_nemenyi_friedman(data) 
    #         p=0.10
    #         algo_m = {algo: algo_means[i] for i, algo in enumerate(algo_names)}
    #         print(f"\n----------------------------------")
    #         print(f"Stat result for space {space}")
    #         print(f"Algo: {algo_m}")
    #         print(f"Friedman: {friedman_res}")
    #         # print(f"Nemenyi:\n{nemenyi_res}")
    #         #we now assign score for each algo based on nemenyi p-value result 
    #         domination = {algo_name: {algo_names[j]: p_val for j, p_val in enumerate(nemenyi_res[i]) if p_val <= p and j > i}
    #                         for i, algo_name in enumerate(algo_names) }
    #         for algo_name, dominated in domination.items():
    #             if len(dominated) > 0: 
    #                 print(f"\t{algo_name} (mean {algo_m[algo_name]}) dominates {dominated}")

    #         space_res = res[res['space'] == space].drop(columns = 'space')
    #         print("\\# & ", end="")
    #         for col_id in space_res.columns:
    #             if not col_id.endswith("_std"):
    #                 print(f"{col_id} & ", end="")
    #         print(">_{0.1}\\\\\\hline")
    #         algo_index = {data['algo']: (i + 1) for i, (_, data) in enumerate(space_res.iterrows())}
    #         for i, (_, data) in enumerate(space_res.iterrows()):                
    #             print("{0: <3} & ".format(i+1), end="")
    #             for col_id, col_val in data.iteritems():
    #                 if col_id.endswith("_std"):
    #                     print(" $\pm$ {:.1f}\t& ".format(col_val * scale), end="")
    #                 else:
    #                     if type(col_val) == float: 
    #                         print("{:.1f}".format(col_val * scale), end = "")
    #                     else:
    #                         col_val = col_val.replace('_', '\_').replace('|', '+')
    #                         # col_val = col_val + '(2)' if col_val.startswith('phc') else col_val
    #                         print("{0: <40}& ".format(col_val), end="")
    #             dominated = sorted([algo_index[algo_name] for algo_name in domination[data['algo']].keys()])
    #             dominated_fmtd = [] 
    #             for idx in dominated: 
    #                 if len(dominated_fmtd) == 0:
    #                     dominated_fmtd.append([idx, idx])
    #                 elif dominated_fmtd[-1][-1] == idx - 1:
    #                     dominated_fmtd[-1][-1] = idx
    #                 else:
    #                     dominated_fmtd.append([idx, idx])
    #             print(",".join([f'{s}-{e}' if s != e else str(s) for s, e in dominated_fmtd]), end="")
    #             print("\\\\")

@quiz_cli.command("export")
@click.option('-q', '--quiz', type=int, required=True)
@click.option('-o', '--output')
def export_quiz_evo(quiz, output):
    quiz_model = get_quiz_builder().load_quiz_model(quiz)
    if quiz_model is None:
        sys.stdout.write(f"Quiz {quiz} does not have evo process\n")
        return 
    if output is not None: 
        quiz_model.to_csv(output)
    sys.stdout.write(f"Genotypes for quiz {quiz}:\n{quiz_model.to_dataframe()}\n")   

@quiz_cli.command("result")
@click.option('-q', '--quiz', type=int, required=True)
@click.option('-o', '--output')
@click.option('-i', '--instructor', default='i@usf.edu')
@click.option('-p', '--password', default='pwd') 
@click.option('--expected') #csv file to compare with
@click.option('--diff-o') #where to save diff
def get_quiz_result(quiz, output, instructor, password, expected, diff_o):
    with APP.test_client(use_cookies=True) as c: #instructor session
        throw_on_http_fail(c.post("/login",json={"email": instructor, "password": password}))
        resp = c.get(f"/quiz/{quiz}/{1}/grades?q=csv")
        if resp.status_code >= 400:  
            sys.stderr.write(f"[{resp.request.path}] failed:\n {resp.get_data(as_text=True)}")
            sys.exit(1)
        csv_text = resp.get_data(as_text=True)
        result_frame = pandas.read_csv(StringIO(csv_text), header=0)
        if output is not None: 
            result_frame.to_csv(output)
        sys.stdout.write(f"Results for quiz {quiz}:\n{result_frame}\n")   
        if expected is not None: 
            expected_frame = pandas.read_csv(expected)
            # ne = result_frame != expected_frame
            joined = pandas.merge(expected_frame, result_frame, how='inner', left_on = 'Email', right_on = 'Email', suffixes=(' EXPECTED', ' ACTUAL'))
            diff = DataFrame()
            for c in ['Initial Score', 'Max Initial Score', 'Revised Score', 'Max Revised Score', 'Justification Score', 'Max Justification Score', 'Participation Score', 'Min Participation', 'Max Participation', 'Likes Given','Likes Received', 'Initial Score %', 'Revised Score %', 'Justifications %', 'Participation %','Final Percentage']:
                expected_column = c + " EXPECTED"
                actual_column = c + " ACTUAL"
                for sid, columns in joined.loc[joined[expected_column] != joined[actual_column], [ expected_column, actual_column ]].iterrows():
                    diff.loc[expected_frame.loc[sid, "Email"], c] = f"{columns[actual_column]} | {columns[expected_column]}"
            if diff.empty:
                sys.stdout.write(f"SUCCESS: actual matches expected csv\n")
            else: 
                if diff_o:
                    diff.to_csv(diff_o)
                sys.stderr.write(f"FAILED, diff:\n{diff}\n")   
                sys.exit(1)


@deca_cli.command("init-many")
@click.option('-nq', '--num-questions', required = True, type = int)
@click.option('-nd', '--num-distractors', required = True, type = int)
@click.option('-ns', '--num-students', required = True, type = int)
@click.option('-an', '--axes-number', multiple=True, required=True, type = int)
@click.option('-as', '--axes-size', multiple=True, required=True, type = int)
@click.option('--num-spaces', default=1, type = int)
@click.option('--spanned-strategy', type = str, default=None)
@click.option('--num-spanned', multiple=True, type = int)
@click.option('--best-students-percent', multiple=True, type = float)
@click.option('--noninfo', multiple=True, type = float)
@click.option("-of", "--output-folder", default="deca-spaces")
@click.option("--random-seed", type=int)
@click.option("--timeout", default = 1000000, type = int)
def init_experiment(num_questions, num_distractors, num_students, axes_number, axes_size, num_spaces, spanned_strategy, num_spanned, best_students_percent, noninfo, output_folder, timeout, random_seed): 
    if len(num_spanned) == 0: 
        num_spanned.append(0)
    if len(best_students_percent) == 0:
        best_students_percent.append(0)
    if len(noninfo) == 0:
        noninfo.append(0)
    runner = APP.test_cli_runner()
    res = runner.invoke(args=["DB-reboot"])
    assert res.exit_code == 0
    res = runner.invoke(args=["course", "init" ])    
    assert res.exit_code == 0
    res = runner.invoke(args=["quiz", "init", "-nq", num_questions, "-nd", num_distractors ])
    assert res.exit_code == 0
    print(res.stdout)
    res = runner.invoke(args=["student", "init", "-ns", num_students ])
    assert res.exit_code == 0
    print(res.stdout)
    os.makedirs(output_folder, exist_ok=True)
    # dims = [dim for num_axes in axes_number for dim in combinations_with_replacement(axes_size, num_axes) ]
    dims = [ [ sz for _ in range(num_axes) ] for sz in axes_size for num_axes in axes_number ]
    rnd = np.random.RandomState(random_seed)
    for dim, spanned, bsp, ni in product(dims, num_spanned, best_students_percent, noninfo): 
        a_param = [p for a in dim for p in ["-a", a]]
        axes_str = "_".join([str(a) for a in dim ])
        spanned_str = "s_" + str(spanned)
        res = runner.invoke(args=["deca", "init", "-q", 1, "-o", output_folder, *a_param, 
                                    *[el for el in (["--spanned-strategy", spanned_strategy] if spanned_strategy is not None else [])],
                                    "--spanned", spanned, "--spanned-geometric-p", 0.8, 
                                    "--best-students-percent", bsp, "--noninfo", ni, "-n", num_spaces, 
                                    '--fmt', 'space-' + axes_str + '-' + spanned_str + '-{}.json',
                                    "--timeout", timeout, "--random-seed", rnd.randint(1000) ])
        assert res.exit_code == 0
        print(f"Generated {num_spaces} spaces for dims {dim} and spanned {spanned}, best students {bsp}, noninfo {ni}")

@quiz_cli.command("deca-experiment")
@click.option("--deca-input", required = True)
@click.option("--algo-folder", default="algo")
@click.option("--results-folder", default="results")
@click.option("--algo", multiple=True, required = True)
@click.option("--random-seed", type=int)
@click.option("--num-runs", type=int, default = 1)
def run_experiment(deca_input, algo, algo_folder, random_seed, results_folder, num_runs):    
    runner = APP.test_cli_runner()
    print(f"Experiment {deca_input}, {algo}, {algo_folder}, {random_seed}, {results_folder}, {num_runs}")
    res = runner.invoke(args=["student", "knows", "-kr", "--deca-input", deca_input ])
    if res.exit_code != 0:
        print(res.stdout)
    print("Before assert student")
    assert res.exit_code == 0
    print("After assert")
    os.makedirs(algo_folder, exist_ok=True)
    os.makedirs(results_folder, exist_ok=True)
    rnd = np.random.RandomState(random_seed)
    deca_space_id = os.path.splitext(os.path.basename(deca_input))[0]
    for a in algo: 
        algo_with_params = json.loads(a)
        algo_display_name = algo_with_params["id"]
        algo_name = algo_with_params["algo"]
        del algo_with_params["algo"]
        del algo_with_params["id"]
        for i in range(num_runs):
            #NOTE: if it is important to preserve each run algo results - change names of files bellow to include i inside it 
            #currently only last run is preserved and archive is ignored        
            algo_with_params["seed"] = rnd.randint(1000) #init seed of pphc
            algo_file_name = os.path.join(algo_folder, algo_display_name)
            run_random_seed = rnd.randint(1000) #init seed of quiz run
            print(f"Start run {i} of {algo_file_name} on {deca_space_id}")
            res = runner.invoke(args=["quiz", "run", "-q", 1, "-s", "STEP1", "--algo", algo_name, "--algo-params", json.dumps(algo_with_params),
                                        "--evo-output", f"{algo_file_name}.json", "--random-seed", run_random_seed ])
            # if res.exit_code != 0:
            print(res.stdout)                
            assert res.exit_code == 0, f" {traceback.format_exception(None, res.exc_info[1], res.exc_info[2])}"
            print(f"Analysing run {i} of {algo_file_name} on {deca_space_id}")
            res = runner.invoke(args=["deca", "result", "--algo-input", f"{algo_file_name}.json", "--deca-space", deca_input, 
                                        "-p", "explored_search_space_size", "-p", "search_space_size", "-io", os.path.join(results_folder, f"{algo_display_name}-on-{deca_space_id}.csv")])
            if res.exit_code != 0:
                print(res.stdout)            
            assert res.exit_code == 0
            print(f"Finished run {i} of {algo_file_name} on {deca_space_id}")

@quiz_cli.command("deca-experiments")
@click.option("--deca-spaces", default="deca-spaces")
@click.option("--algo-folder", default="algo")
@click.option("--results-folder", default="results")
@click.option("--algo", multiple=True, required = True)
@click.option("--random-seed", type=int)
@click.option("--num-runs", type=int, default = 1)
def run_experiment(deca_spaces, algo, algo_folder, random_seed, results_folder, num_runs):  
    runner = APP.test_cli_runner() 
    for file_name in os.listdir(deca_spaces):        
        deca_input = os.path.join(deca_spaces, file_name)
        print(f"--- Space {deca_input} ---")
        res = runner.invoke(args=["quiz", "deca-experiment", "--deca-input", deca_input, "--algo-folder", algo_folder,
                                    "--results-folder", results_folder, *[p for a in algo for p in ["--algo", a]], 
                                    "--random-seed", random_seed, "--num-runs", num_runs ])
        # if res.exit_code != 0:
        #     print(res.exc_info)
        print(res.stdout)
        assert res.exit_code == 0

@quiz_cli.command("post-process")        
@click.option("--result-folder", required=True)
@click.option("--figure-folder", required=True)
@click.option("-p", "--param", multiple=True, required=True)
@click.option("--file-name-pattern")
@click.option("--group-by-space", is_flag = True)
def post_process(result_folder, figure_folder, param, file_name_pattern, group_by_space):
    import re
    pattern = re.compile(file_name_pattern)
    frames_data = {}    
    def get_space_params(file_name):
        [axes, spanned, i] = file_name.split('-on-')[1].split('-')[1:4]
        dims = tuple([int(d) for d in axes.split('_')])
        sp = int(spanned.split('s_')[1])
        if group_by_space:
            return dims, sp, ''
        return dims, sp, int(i.split(".")[0])
    
    for file in os.listdir(result_folder):        
        if not pattern.match(file): 
            continue
        dims, sp, i = get_space_params(file)
        # file_id = f"{len(dims)} {sp} {i}"
        # file_id = f"{dims} {sp} {i}"
        file_frame = pandas.read_csv(os.path.join(result_folder, file))
        for c in file_frame.columns:
            if c in param:
                file_data = file_frame[c].to_list()
                print(f'Debug {(dims, sp, i)} and {file_data}')
                frames_data.setdefault(c, []).append(((dims, sp, i), file_data))
            # if c in param:
            #     f = frames.setdefault(c, DataFrame())
            #     f[(dims, sp, i)] = file_frame[c]
            #     f.astype('float')        
    frames = {}
    for param, values_group in frames_data.items():
        f = frames.setdefault(param, DataFrame()) 
        for space, g in groupby(values_group, key = lambda x: x[0]):            
            f[space] = Series([v2 for v in g for v2 in v[1]])
            f.astype('float')
        # print(f'Debug {param} and {f}')
    stats_frames = []
    for param, frame in frames.items():
        sorting_values = sorted(frame.columns, key = lambda c: (*c[0], c[1], c[2]))        
        frame = frame.reindex(sorting_values, axis=1)
        frame.rename(columns = lambda c: f"{c[0]} {c[1]} {c[2]}".strip(), inplace=True)
        mn = frame.mean()
        std = frame.std()
        clr = ((0.3 + mn * 0.7) if param in ['dim_coverage', 'arr'] else (1 - mn * 0.7)).round(2).astype(str)
        stats = DataFrame({param: "cellcolor[rgb]{" + clr + "," + clr + "," + clr + "}" + mn.round(2).astype(str) + " ± " + std.round(2).astype(str) })
        stats_frames.append(stats)
        # print(f"Frame\n{frame}\n-----------")        
        boxplot = frame.boxplot(figsize=(12, 7), column = list(frame.columns), fontsize='small')        
        boxplot.set_xticklabels(boxplot.get_xticklabels(), rotation=-60)
        fig = boxplot.get_figure()  
        fig.set_tight_layout(True)      
        fig.savefig(os.path.join(figure_folder, f"{param}.png"), format='png')
        plt.close(fig)
    stats = pandas.concat(stats_frames, axis=1)
    latex_table = stats.to_latex().replace("cellcolor[rgb]\\{", "\\cellcolor[rgb]{").replace("\\}", "}")
    print(f"Stats:\n{latex_table}\n--------")

@quiz_cli.command("plot-metric-vs-num-of-dims")
@click.option("-p", "--param", required=True, multiple=True)   
@click.option("-pt", "--param-title", multiple=True)  
@click.option("--data-folder", required=True)
@click.option("--path-suffix", required=True)
@click.option("--figure-folder", required=True)
@click.option("--file-name-pattern")
@click.option("--fixate-range", is_flag=True)
@click.option("--fig-name")
@click.option("--legend")
def post_process(data_folder, path_suffix, figure_folder, fig_name, param, legend, param_title, file_name_pattern, fixate_range):
    import re
    pattern = re.compile(file_name_pattern)
    frames_data = {}    
    def get_space_params(file_name):
        [axes, spanned] = file_name.split('-on-')[1].split('-')[1:3]
        dims = tuple([int(d) for d in axes.split('_')])
        # sp = int(spanned.split('s_')[1])
        return dims[0]
        
    param_titles = {}
    for p, pt in zip(param, param_title):
        param_titles[p] = pt

    for dim_data_dir in os.listdir(data_folder): 
        num_dims = int(dim_data_dir.split('-')[1])
        file_path = os.path.join(data_folder, dim_data_dir, path_suffix)
        for file in os.listdir(file_path):
            if (m := pattern.match(file)) is None: 
                continue
            # print(file)            
            dim_size = get_space_params(file)
            # file_id = f"{len(dims)} {sp} {i}"
            # file_id = f"{dims} {sp} {i}"
            file_frame = pandas.read_csv(os.path.join(file_path, file))
            for p in param:
                file_key = (p, str(dim_size), *m.groupdict().values())
                file_data = file_frame[p].to_list()
                frames_data.setdefault(file_key, {}).setdefault(num_dims, []).extend(file_data)
    frames = { file_key: DataFrame(data = df) for file_key, df in frames_data.items() }
    frames = {file_key: frame.reindex(sorted(frame.columns, key = lambda c: int(c)), axis=1) for file_key, frame in frames.items() }  
    sorted_file_keys = sorted(frames.keys())  
    frames_list = {}
    markers = ["o", "s", "x"]
    # legend = []
    groupedPlots = {}
    for file_key in sorted_file_keys:
        param = file_key[0]
        dim_size = file_key[1]
        frame = frames[file_key]
        mn = frame.mean()
        std = frame.std()
        clr = ((0.3 + mn * 0.7) if file_key[0] in ['dim_coverage', 'arr'] else (1 - mn * 0.7)).round(2).astype(str)
        group_keys = {p:pi for pi, p in enumerate(pattern.groupindex.keys())}
        algo = file_key[2 + group_keys["algo"]] if "algo" in group_keys else "algo"
        spanned = file_key[2 + group_keys["spanned"]] if "spanned" in group_keys else 0
        frames_list.setdefault(param, {}).setdefault(algo, []).append(DataFrame({(spanned, dim_size): "cellcolor[rgb]{" + clr + "," + clr + "," + clr + "}" + mn.round(2).astype(str) + " ± " + std.round(2).astype(str)}))
        #drawing plot
        # legend.append(f"Axis size {dim_size}")
        # plot = mn.plot(xlabel="Number of DECA axes", ylabel=param_title, marker = markers[file_key_id], fontsize = 16)  
        fn = fig_name or "<param>"
        l = legend or "Axis size <dimSize>"
        for p, pi in group_keys.items():
            fn = fn.replace(f"<{p}>", file_key[2 + pi])
            l = l.replace(f"<{p}>", file_key[2 + pi])
        fn = fn.replace("<param>", file_key[0])
        l = l.replace("<param>", file_key[0])
        fn = fn.replace("<dimSize>", file_key[1])
        l = l.replace("<dimSize>", file_key[1])
        
        groupedPlots.setdefault(fn, []).append((mn, l, param_titles.get(file_key[0], file_key[0])))
        # boxplot.set_xticklabels(boxplot.get_xticklabels(), rotation=-60)
    for file_name, mns in groupedPlots.items():
        legends = []
        for (mn, legend, pt) in mns:
            mk = markers.pop(0)
            legends.append(legend)
            plot = mn.plot(xlabel="Number of DECA axes", ylabel=pt, marker = mk, fontsize = 16)  
            markers.append(mk)
        if fixate_range:
            plot.set_ylim([0, 1.05])
        legend = plot.legend(legends, fontsize=16)
        plot.xaxis.label.set_fontsize(18)
        plot.yaxis.label.set_fontsize(18)
        fig = plot.get_figure()  
        fig.set_tight_layout(True)      
        fig.savefig(os.path.join(figure_folder, f"{file_name}.png"), format='png')
        plt.close(fig)    
    for param_id, param_frames in frames_list.items():
        print(f"Param {param_id}")
        for algo_id, algo_frames in param_frames.items():
            algo_frames.sort(key = lambda d: (int(d.columns[0][0]), int(d.columns[0][1])))
            stat_frame = pandas.concat(algo_frames, axis=1) 
            latex_table = stat_frame.to_latex().replace("cellcolor[rgb]\\{", "\\cellcolor[rgb]{").replace("\\}", "}")
            print(f"Frame for algo {algo_id}:\n{latex_table}\n")    
    # for param, values_group in frames_data.items():
    #     f = frames.setdefault(param, DataFrame()) 
    #     for space, g in groupby(values_group, key = lambda x: x[0]):            
    #         f[space] = Series([v2 for v in g for v2 in v[1]])
    #         f.astype('float')
    #     # print(f'Debug {param} and {f}')
    # stats_frames = []
    # for param, frame in frames.items():
    #     sorting_values = sorted(frame.columns, key = lambda c: (*c[0], c[1], c[2]))        
    #     frame = frame.reindex(sorting_values, axis=1)
    #     frame.rename(columns = lambda c: f"{c[0]} {c[1]} {c[2]}".strip(), inplace=True)
    #     mn = frame.mean()
    #     std = frame.std()
    #     clr = ((0.3 + mn * 0.7) if param in ['dim_coverage', 'arr'] else (1 - mn * 0.7)).round(2).astype(str)
    #     stats = DataFrame({param: "cellcolor[rgb]{" + clr + "," + clr + "," + clr + "}" + mn.round(2).astype(str) + " ± " + std.round(2).astype(str) })
    #     stats_frames.append(stats)
    #     # print(f"Frame\n{frame}\n-----------")        
    #     boxplot = frame.boxplot(figsize=(12, 7), column = list(frame.columns), fontsize='small')        
    #     boxplot.set_xticklabels(boxplot.get_xticklabels(), rotation=-60)
    #     fig = boxplot.get_figure()  
    #     fig.set_tight_layout(True)      
    #     fig.savefig(os.path.join(figure_folder, f"{param}.png"), format='png')
    #     plt.close(fig)
    # stats = pandas.concat(stats_frames, axis=1)
    # latex_table = stats.to_latex().replace("cellcolor[rgb]\\{", "\\cellcolor[rgb]{").replace("\\}", "}")
    # print(f"Stats:\n{latex_table}\n--------")    

APP.cli.add_command(quiz_cli)
APP.cli.add_command(course_cli)
APP.cli.add_command(student_cli)
APP.cli.add_command(deca_cli)