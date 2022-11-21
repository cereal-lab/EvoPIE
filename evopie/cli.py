from datetime import datetime, timedelta
from functools import reduce
from io import StringIO
from itertools import combinations_with_replacement, product
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

from evopie import APP, deca, models
from evopie.config import EVO_PROCESS_STATUS_ACTIVE, EVO_PROCESS_STATUS_STOPPED, QUIZ_ATTEMPT_STEP1, QUIZ_STEP1, QUIZ_STEP2, ROLE_STUDENT
from evopie.utils import groupby, unpack_key
from evopie.evo import get_evo, sql_evo_serializer, Serializable

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
student_cli = AppGroup('student') #responsible for student simulation
deca_cli = AppGroup('deca')

@quiz_cli.command("init")
@click.option('-i', '--instructor', default='i@usf.edu')
@click.option('-nq', '--num-questions', required = True, type = int)
@click.option('-nd', '--num-distractors', required = True, type = int)
@click.option('-qd', '--question-distractors')
def start_quiz_init(instructor, num_questions, num_distractors, question_distractors):
    ''' Creates instructor, quiz, students for further testing 
        Note: flask app should be running
    '''
    instructor = {"email":instructor, "firstname":"I", "lastname": "I", "password":"pwd"}
    def build_quiz(i, questions):
        return { "title": f"Quiz {i}", "description": "Test quiz", "questions_ids": questions}
    def build_question(i):
        return { "title": f"Question {i}", "stem": f"Question {i} Stem?", "answer": f"a{i}"}
    def build_distractor(i, question):
        return { "answer": f"d{i}/q{question}", "justification": f"d{i}/q{question} just"}
    if question_distractors:
        question_distractors = json.loads(question_distractors)
    else:
        question_distractors = {}
    with APP.test_client(use_cookies=True) as c: #instructor session
        throw_on_http_fail(c.post("/signup", json={**instructor, "retype":instructor["password"]}), status=300)
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

@deca_cli.command("init")
@click.option('-q', '--quiz', type = int, required = True)
@click.option('-o', '--output') #folder were we should put generated spaces
@click.option('--fmt', default='space-{}.json') #folder were we should put generated spaces
@click.option('-a', "--axis", multiple=True, type = int, required=True) #generate knowledge from deca axes
@click.option('--spanned', type=int, default=0)
@click.option('--best-students-percent', type=float, default=0)
@click.option('--spanned-geometric-p', type=float, default=0.75)
@click.option('--noninfo', type=float, default=0)
@click.option('-n', type=int, default=1) #number of spaces to create
@click.option("--random-seed", type=int) #seed
@click.option("--timeout", default=1000000, type=int)
def create_deca_space(quiz, output, fmt, axis, spanned, best_students_percent, n, random_seed, spanned_geometric_p, noninfo, timeout):

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
        question_ids = set(q.id for q in quiz_questions)    
        quiz_question_distractors = models.DB.session.query(models.quiz_questions_hub).where(models.quiz_questions_hub.c.quiz_question_id.in_(question_ids)).all()
        #NOTE: for additional validation we also could check that distractors exist in Distractor tables
        question_distractors = [ (q.quiz_question_id, q.distractor_id) for q in quiz_question_distractors ]
        #NOTE: quiz also should be used to connect instructor to generated students and namespace them from other students

    for i in range(n):
        space = deca.gen_deca_space(emails, tuple(axis), spanned, best_students_percent, spanned_geometric_p, timeout=timeout, rnd = rnd)
        space = deca.gen_test_distractor_mapping(space, question_distractors, noninformative_percent=noninfo, rnd = rnd)
        space['meta'] = {'id': i, 'rnd': random_seed}
        # knowledge = deca.gen_test_distractor_mapping_knowledge(space)
        print(f"---\n{space}\n")
        if output:
            file_name = os.path.join(output, fmt.format(i))
            with open(file_name, 'w') as f: 
                f.write(deca.save_space_to_json(space))

@student_cli.command("init")
@click.option('-ns', '--num-students', type = int)
@click.option('--exclude-id', type = int, multiple=True)
@click.option('-ef', '--email-format', default="s{}@usf.edu")
@click.option('-i', '--input')
@click.option('-o', '--output') #csv file to output with student email, id
def init_students(num_students, exclude_id, input, output, email_format):
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
        instructor = models.User.query.get_or_404(1)
        student.instructors.append(instructor)
        models.DB.session.commit()
    models.StudentKnowledge.query.where(models.StudentKnowledge.student_id.in_(student_ids)).delete()
    models.DB.session.commit()
    if output is not None:
        students.to_csv(output, index=False)    
        sys.stdout.write(f"Students were saved to {output}:\n {students}\n")
    else: 
        sys.stdout.write(f"Students were created:\n {students}\n")

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
    #NOTE: otherwise if chance is a list - elements are treated as chances for each step sequentially
    #NOTE: otherwise chance defines value for all steps
    def dks_reducton(acc, k):
        ''' adds chances from simple knows record '''
        if "step" in k:
            local_step = k["step"] - 1
            acc[local_step] = k["chance"][local_step] if type(k["chance"]) == list else k["chance"]
        elif type(k["chance"]) == list:
            for i in range(min(len(acc), len(k["chance"]))):
                acc[i] = k["chance"][i]
        else: 
            for i in range(len(acc)):
                if acc[i] < 0:
                    acc[i] = k["chance"]
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

    distractor_column_order = list(sorted(set([ (i+1, qid, did) for skn in knows_map.values() for qid, qkn in skn.items() for did, dkn in qkn.items() for i, chance in enumerate(dkn) if chance > 0])))
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
                distractors = {(i+1, qid, did):chance for qid, qks in student_knowledge.items() for did, dks in qks.items() for i, chance in enumerate(dks) if chance > 0}
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
                    present_knowledge[knowledge_id].chance = student[c]
                else:
                    k = models.StudentKnowledge(student_id=student.id, question_id = question_id, distractor_id=distractor_id, step_id = step_id, chance = student[c])
                    models.DB.session.add(k) 
    for (sid, qid, did, step), v in present_knowledge.items():
        if sid in students.index: 
            column = f'd_{qid}_{did}_{step}'
            if np.isnan(students.loc[sid, column]):
                students.loc[sid, column] = v.chance
    models.DB.session.commit()
    if output is not None:
        students.to_csv(output, index=False)    
        sys.stdout.write(f"Students were saved to {output}:\n {students}\n")
    else: 
        sys.stdout.write(f"Students were created:\n {students}\n")

@student_cli.command("export")        
@click.option('-o', '--output')
def export_student_knowledge(output): 
    students = models.User.query.where(models.User.role == ROLE_STUDENT).all()
    knowledge = models.StudentKnowledge.query.all()
    ids = list(sorted(set([ (k.step_id, k.question_id, k.distractor_id) for k in knowledge ])))
    knowledge_map = {sid:{f'd_{k.question_id}_{k.distractor_id}_{k.step_id}':k.chance for k in ks} for sid, ks in groupby(knowledge, key=lambda k: k.student_id) }
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

@quiz_cli.command("run")
@click.option('-q', '--quiz', type=int, required=True)
@click.option('-s', '--step', default = [QUIZ_STEP1], multiple=True)
@click.option('-n', '--n-times', type=int, default=1)
@click.option('-kns', '--knowledge-selection', default = KNOWLEDGE_SELECTION_WEIGHT)
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
def simulate_quiz(quiz, instructor, password, no_algo, algo, algo_params, rnd, n_times, archive_output, evo_output, step, knowledge_selection, likes, justify_response, email_format, random_seed):    
    import evopie.config
    rnd_state = np.random.RandomState(random_seed)
    if no_algo:
        evopie.config.distractor_selection_process = None
        evopie.config.distractor_selecton_settings = {}
    else:
        if algo is not None:         
            evopie.config.distractor_selection_process = algo 
        if algo_params is not None: 
            evopie.config.distractor_selecton_settings = json.loads(algo_params)

    def simulate_step(step):
        with APP.app_context():
            k_plain = models.StudentKnowledge.query.where(models.StudentKnowledge.step_id == step).all() #TODO: students should be per instructor eventually 
            knowledge = {student_id: { str(qid): {x.distractor_id: x.chance for x in qks} for qid, qks in groupby(ks, key=lambda x: x.question_id)} for student_id, ks in groupby(k_plain, key=lambda k: k.student_id) }
            students_plain = models.User.query.filter_by(role=ROLE_STUDENT).all()
            students = list(students_plain) #[s.id for s in students_plain]
            student_ids = set([s.id for s in students])
            if step == 1:
                models.QuizAttempt.query.where(models.QuizAttempt.student_id.in_(student_ids), models.QuizAttempt.quiz_id == quiz).delete()
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
                    resp = throw_on_http_fail(c.get(f"/student/{quiz}/start", headers={"Accept": "application/json"}))
                    resp = throw_on_http_fail(c.get(f"/student/{quiz}", headers={"Accept": "application/json"}))

                with APP.app_context():
                    attempt = models.QuizAttempt.query.where(models.QuizAttempt.quiz_id == quiz, models.QuizAttempt.student_id == sid).first()

                student_knowledge = knowledge.get(sid, {})
                if knowledge_selection == KNOWLEDGE_SELECTION_CHANCE:
                    responses = {qid:rnd_state.choice(known_distractors)
                                            for qid, distractors in attempt.alternatives_map.items() 
                                            for qskn in [student_knowledge.get(qid, {-1:1}) ]
                                            for ds_distr in [[(alt, qskn[d]) for alt, d in enumerate(distractors) if d in qskn]] 
                                            for ds in [ds_distr if any(ds_distr) else [(alt, 1) for alt, d in enumerate(distractors) if d == -1]]
                                            for known_distractors in [[alt for alt, w in ds if rnd_state.rand() < w ]]}
                elif knowledge_selection == KNOWLEDGE_SELECTION_WEIGHT:
                    responses = {qid:ds[selected_d_index][0]
                                            for qid, distractors in attempt.alternatives_map.items() 
                                            for qskn in [student_knowledge.get(qid, {-1:1}) ]
                                            for ds_distr in [[(alt, qskn[d]) for alt, d in enumerate(distractors) if d in qskn]] 
                                            for ds in [ds_distr if any(ds_distr) else [(alt,1) for alt, d in enumerate(distractors) if d == -1]]
                                            for weights in [[w for _, w in ds]]
                                            for sums in [np.cumsum(weights)]
                                            for level in [(rnd_state.rand() * sums[-1]) if len(sums) > 0 else None]
                                            for selected_d_index in [next((i for i, s in enumerate(sums) if s > level), None)]}
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
                        resp = throw_on_http_fail(c.put(f"/quizzes/{quiz}/justifications/like", json=likes_map[email]))
                with APP.app_context():
                    g.allow_justification_for_selected = True #do not delete justifications for selection
                    resp = throw_on_http_fail(c.post(f"/student/{quiz}", json=json_resp))
        
    for run_idx in range(n_times):
        #close prev evo process
        if QUIZ_STEP1 in step:
            with APP.app_context():
                models.EvoProcessArchive.query.delete()
                models.EvoProcess.query.delete()            
                # existing_evo = models.EvoProcess.query.where(models.EvoProcess.quiz_id == quiz, models.EvoProcess.status == EVO_PROCESS_STATUS_ACTIVE).all()
                # for evo in existing_evo:
                #     evo.status = EVO_PROCESS_STATUS_STOPPED    
                models.DB.session.commit()    
            with APP.app_context(), APP.test_client(use_cookies=True) as c: #instructor session
                throw_on_http_fail(c.post("/login",json={"email": instructor, "password": password}))
                throw_on_http_fail(c.post(f"/quizzes/{quiz}/status", json={ "status" : "HIDDEN" })) #stop in memory evo process
                throw_on_http_fail(c.post(f"/quizzes/{quiz}/status", json={ "status" : "STEP1" }))
                # evo process started 

            simulate_step(1)

            with APP.app_context():     
                evo = get_evo(quiz)
                if evo is None:
                    sys.stdout.write(f"[{run_idx + 1}/{n_times}] Step1 quiz {quiz} finished\n")            
                else:
                    evo.stop()
                    evo.join()
                    sql_evo_serializer.wait_dump(timeout=5)  #wait for db data dump
                    evo.archive["p"] = 0
                    evo.archive["p"] = evo.archive["p"].astype(int)            
                    for ind in evo.population:
                        evo.archive.loc[ind, "p"] = 1        
                    if archive_output is not None: 
                        evo.archive.to_csv(archive_output.format(run_idx))  
                    evo_state = evo.get_state()
                    population = evo.get_population_genotypes()
                    population_distractors = evo.get_population_distractors()
                    search_space_size = evo.get_search_space_size()
                    explored_search_space_size = evo.get_explored_search_space_size()
                    sys.stdout.write(f"EVO algo: {evo.__class__}\nEVO settings: {evo_state}\nEVO population: {population}\n")
                    if evo_output: 
                        with open(evo_output, 'w') as evo_output_json_file:
                            evo_output_json_file.write(json.dumps({"algo": evo.__class__.__name__, "settings":evo_state, 
                                                        "population":population, "population_distractors": population_distractors, 
                                                        "explored_search_space_size": explored_search_space_size, 
                                                        "search_space_size": search_space_size}, indent=4))
                    sys.stdout.write(f"[{run_idx + 1}/{n_times}] Step1 quiz {quiz} finished\n{evo.archive}\n")
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
    population_distractors = algo_results["population_distractors"]
    metrics_map = {"algo":algo_input,"deca": deca_space, **{p:algo_results.get(p, np.nan) for p in params},
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
    submetrics = metrics[["dim_coverage", "arr", "population_redundancy", "population_duplication", "noninfo"]]
    sys.stdout.write(f"Metrics:\n{submetrics}\n")

@quiz_cli.command("export")
@click.option('-q', '--quiz', type=int, required=True)
@click.option('-o', '--output')
def export_quiz_evo(quiz, output):
    evo_process = sql_evo_serializer.from_store([quiz]).get(quiz, None)
    if evo_process is None:
        sys.stdout.write(f"Quiz {quiz} does not have evo process\n")
        return 
    evo = Serializable.load(evo_process, sql_evo_serializer)
    evo.archive["p"] = 0
    evo.archive["p"] = evo.archive["p"].astype(int)
    for ind in evo.population:
        evo.archive.loc[ind, "p"] = 1
    if output is not None: 
        evo.archive.to_csv(output)
    sys.stdout.write(f"Genotypes for quiz {quiz}:\n{evo.archive}\n")   

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
        resp = c.get(f"/quiz/{quiz}/grades?q=csv")
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
            for c in ['Initial Score','Revised Score','Grade for Justifications','Min Participation','Likes Given','Max Participation','Grade for Participation','Likes Received','Total Score','Max Possible Score','Final Percentage']:
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
@click.option('--num-spanned', multiple=True, type = int)
@click.option('--best-students-percent', multiple=True, type = float)
@click.option('--noninfo', multiple=True, type = float)
@click.option("-of", "--output-folder", default="deca-spaces")
@click.option("--random-seed", type=int)
@click.option("--timeout", default = 1000000, type = int)
def init_experiment(num_questions, num_distractors, num_students, axes_number, axes_size, num_spaces, num_spanned, best_students_percent, noninfo, output_folder, timeout, random_seed): 
    if len(num_spanned) == 0: 
        num_spanned.append(0)
    if len(best_students_percent) == 0:
        best_students_percent.append(0)
    if len(noninfo) == 0:
        noninfo.append(0)
    runner = APP.test_cli_runner()
    res = runner.invoke(args=["DB-reboot"])
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
        res = runner.invoke(args=["deca", "init", "-q", 1, "-o", output_folder, *a_param, "--spanned", spanned, "--spanned-geometric-p", 0.8, 
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
    res = runner.invoke(args=["student", "knows", "-kr", "--deca-input", deca_input ])
    assert res.exit_code == 0
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
            if res.exit_code != 0:
                print(res.stdout)
            assert res.exit_code == 0
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
        print(f"--- Working with space {deca_input} ---")
        res = runner.invoke(args=["quiz", "deca-experiment", "--deca-input", deca_input, "--algo-folder", algo_folder,
                                    "--results-folder", results_folder, *[p for a in algo for p in ["--algo", a]], 
                                    "--random-seed", random_seed, "--num-runs", num_runs ])
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
APP.cli.add_command(student_cli)
APP.cli.add_command(deca_cli)