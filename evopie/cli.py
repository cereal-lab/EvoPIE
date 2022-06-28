from functools import reduce
from io import StringIO
import json
from random import choice, random, shuffle
import click
from flask import g
from pandas import DataFrame
import pandas
from werkzeug.test import TestResponse
import sys
import numpy as np

from evopie import APP, models
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

@student_cli.command("init")
@click.option('-ns', '--num-students', type = int)
@click.option('--exclude-id', type = int, multiple=True)
@click.option('-ef', '--email-format', default="s{}@usf.edu")
@click.option('-i', '--input')
@click.option('-o', '--output') #csv file to output with student email and id 
@click.option('-kr', '--knowledge-replace', is_flag=True)
@click.option('-k', '--knows', multiple=True) #should be json representation
def start_quiz_init(num_students, exclude_id, input, output, email_format, knows, knowledge_replace):
    if input is None and num_students is None: 
        sys.stderr.write("Either --input or --num-students should be provided")
        sys.exit(1)
    def build_student(i):
        return {"email": email_format.format(i), "firstname":"S", "lastname": "S", "password":"pwd"}        

    input_students = None     
    knows_map_input = {}
    if input is not None:
        columns = {"firstname": "", "lastname": "", "password": "pwd"}
        input_students = pandas.read_csv(input)
        for column in columns:
            if column not in input_students:
                input_students[column] = columns[column]
        input_students.dropna(subset=["email"])
        input_students[["firstname", "lastname", "password"]].fillna(columns)  
        for sid in input_students.index:
            s = input_students.loc[sid]
            for c in input_students.columns:
                if c.startswith("d_") and s[c]:
                    qid, did, step = (int(id) for id in c.split("_")[1:])
                    knows_map_input.setdefault(s["email"], {}).setdefault(qid, {}).setdefault(did, [np.nan, np.nan])[step - 1] = s[c]
    knows = [json.loads(k) for k in knows]  #NOTE: expected format {'sid':<opt, by default all>, 'qid':<opt, by default all>, 'did':<opt, by default all>, choice:num or [step1_c, step2_c] }
    knows_unpacked = unpack_key('did', unpack_key('qid', unpack_key('sid', knows)))
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

    knows_map = {**knows_map_input, **knows_map_args}        
    students = DataFrame(columns=["email", "id", "created"])    

    distractor_column_order = list(sorted(set([ (i+1, qid, did) for skn in knows_map.values() for qid, qkn in skn.items() for did, dkn in qkn.items() for i, chance in enumerate(dkn) if chance > 0])))
    distractor_columns = [f'd_{q}_{d}_{step}' for step, q, d in distractor_column_order]

    with APP.test_client(use_cookies=True) as c:
        def create_student(student):
            resp = throw_on_http_fail(c.post("/signup", json={**student, "retype": student["password"]}), status=300)
            was_created = "id" in resp
            #NOTE: we ignore the fact that student is already present in the system - status_code for existing user is 200 with "redirect" in resp
            resp = throw_on_http_fail(c.post("/login", json={**student}))
            student_id = resp["id"]
            student_knowledge = {**knows_map_input.get(student_id, {}), **knows_map_input.get(student["email"], {}), **knows_map_args.get("*", {}), **knows_map_args.get(student_id, {}), **knows_map_args.get(student["email"], {})}
            distractors = {(i+1, qid, did):chance for qid, qks in student_knowledge.items() for did, dks in qks.items() for i, chance in enumerate(dks) if chance > 0}
            students.loc[student_id, [ "email", "id", "created", *distractor_columns ]] = [student["email"], student_id, was_created, *[distractors[kid] if kid in distractors else np.nan for kid in distractor_column_order]]

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
@click.option('-o', '--output')
@click.option('-l', '--likes', multiple=True)
@click.option('--justify-response', is_flag=True)
@click.option('-ef', '--email-format', default="s{}@usf.edu")
def simulate_quiz(quiz, instructor, password, no_algo, algo, algo_params, rnd, n_times, output, step, knowledge_selection, likes, justify_response, email_format):    
    import evopie.config
    if no_algo:
        evopie.config.distractor_selection_process = None
        evopie.config.distractor_selecton_settings = {}
    else:
        if algo is not None:         
            evopie.config.distractor_selection_process = algo 
        if algo_params is not None: 
            evopie.config.distractor_selecton_settings = json.loads(algo_params)

    def simulate_step(step):
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
            shuffle(students)
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
                    resp = throw_on_http_fail(c.get(f"/student/{quiz}", headers={"Accept": "application/json"}))

                attempt = models.QuizAttempt.query.where(models.QuizAttempt.quiz_id == quiz, models.QuizAttempt.student_id == sid).first()

                student_knowledge = knowledge.get(sid, {})
                if knowledge_selection == KNOWLEDGE_SELECTION_CHANCE:
                    responses = {qid:choice(known_distractors)
                                            for qid, distractors in attempt.alternatives_map.items() 
                                            for qskn in [student_knowledge.get(qid, {-1:1}) ]
                                            for ds_distr in [[(alt, qskn[d]) for alt, d in enumerate(distractors) if d in qskn]] 
                                            for ds in [ds_distr if any(ds_distr) else [(alt, 1) for alt, d in enumerate(distractors) if d == -1]]
                                            for known_distractors in [[alt for alt, w in ds if random() < w ]]}
                elif knowledge_selection == KNOWLEDGE_SELECTION_WEIGHT:
                    responses = {qid:ds[selected_d_index][0]
                                            for qid, distractors in attempt.alternatives_map.items() 
                                            for qskn in [student_knowledge.get(qid, {-1:1}) ]
                                            for ds_distr in [[(alt, qskn[d]) for alt, d in enumerate(distractors) if d in qskn]] 
                                            for ds in [ds_distr if any(ds_distr) else [(alt,1) for alt, d in enumerate(distractors) if d == -1]]
                                            for weights in [[w for _, w in ds]]
                                            for sums in [np.cumsum(weights)]
                                            for level in [(random() * sums[-1]) if len(sums) > 0 else None]
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
            existing_evo = models.EvoProcess.query.where(models.EvoProcess.quiz_id == quiz, models.EvoProcess.status == EVO_PROCESS_STATUS_ACTIVE).all()
            for evo in existing_evo:
                evo.status = EVO_PROCESS_STATUS_STOPPED    
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
                    sys.stdout.write(f"[{run_idx + 1}/{n_times}] Quiz {quiz} finished\n")            
                else:
                    evo.stop()
                    evo.join()
                    sql_evo_serializer.wait_dump(timeout=5)  #wait for db data dump
                    evo.archive["p"] = 0
                    evo.archive["p"] = evo.archive["p"].astype(int)            
                    for ind in evo.population:
                        evo.archive.loc[ind, "p"] = 1        
                    if output is not None: 
                        evo.archive.to_csv(output.format(run_idx))    
                    sys.stdout.write(f"[{run_idx + 1}/{n_times}] Step1 quiz {quiz} finished\n{evo.archive}\n")
        if QUIZ_STEP2 in step: 
            with APP.app_context(), APP.test_client(use_cookies=True) as c: #instructor session
                throw_on_http_fail(c.post("/login",json={"email": instructor, "password": password}))
                throw_on_http_fail(c.post(f"/quizzes/{quiz}/status", json={ "status" : "STEP2" }))

            simulate_step(2)            

            sys.stdout.write(f"[{run_idx + 1}/{n_times}] Step2 Quiz {quiz} finished\n")

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
        resp = c.get(f"/grades/{quiz}?q=csv")
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
                sys.stdout.write(f"FAILED, diff:\n{diff}\n")   




APP.cli.add_command(quiz_cli)
APP.cli.add_command(student_cli)