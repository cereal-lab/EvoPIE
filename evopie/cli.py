import json
from random import choice, random, shuffle
import click
from pandas import DataFrame
import pandas
from werkzeug.test import TestResponse
import sys
import numpy as np

from evopie import APP, models
from evopie.config import EVO_PROCESS_STATUS_ACTIVE, EVO_PROCESS_STATUS_STOPPED, ROLE_STUDENT
from evopie.utils import groupby
from evopie.evo import get_evo, sql_evo_serializer, Serializable

def throw_on_http_fail(resp: TestResponse, status: int = 400):
    if resp.status_code >= status:            
        sys.stderr.write(f"[{resp.request.path}] failed for input {resp.request.json}:\n {resp.get_data(as_text=True)}")
        sys.exit(1)
    return resp.json

from flask.cli import AppGroup

quiz_cli = AppGroup('quiz')
student_cli = AppGroup('student') #responsible for student simulation

@quiz_cli.command("init")
@click.option('-i', '--instructor', default='i@usf.edu')
@click.option('-nq', '--num-questions', required = True, type = int)
@click.option('-nd', '--num-distractors', required = True, type = int)
def start_quiz_init(instructor, num_questions, num_distractors):
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
    with APP.test_client(use_cookies=True) as c: #instructor session
        throw_on_http_fail(c.post("/signup", json={**instructor, "retype":instructor["password"]}), status=300)
        throw_on_http_fail(c.post("/login",json=instructor))
        from sqlalchemy import func
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
            throw_on_http_fail(c.post("/quizquestions", json={ "qid": str(qid), "distractors_ids": dids}))
        quiz = build_quiz("X", qids)
        resp = throw_on_http_fail(c.post("/quizzes", json=quiz))
        quiz_id = resp["id"]
        quiz = build_quiz(quiz_id, qids)
        throw_on_http_fail(c.put(f"/quizzes/{quiz_id}", json=quiz))
        sys.stdout.write(f"Quiz with id {quiz_id} was created successfully:\n{distractor_map}\n")

@student_cli.command("init")
@click.option('-ns', '--num-students', type = int)
@click.option('-ef', '--email-format', default="s{}@usf.edu")
@click.option('-i', '--input')
@click.option('-o', '--output') #csv file to output with student email and id 
@click.option('-kr', '--knowledge-replace', is_flag=True)
@click.option('-k', '--knows', multiple=True, nargs=2, type=(int,float))
def start_quiz_init(num_students, input, output, email_format, knows, knowledge_replace):
    if input is None and num_students is None: 
        sys.stderr.write("Either --input or --num-students should be provided")
        sys.exit(1)
    def build_student(i):
        return {"email": email_format.format(i), "firstname":"S", "lastname": "S", "password":"pwd"}        
    input_students = None 
    # import numpy as np
    knows_map = {}
    if input is not None:
        columns = {"firstname": "", "lastname": "", "password": "pwd"}
        input_students = pandas.read_csv(input)
        for column in columns:
            if column not in input_students:
                input_students[column] = columns[column]
        input_students.dropna(subset=["email"])
        input_students[["firstname", "lastname", "password"]].fillna(columns)    
    for (did, chance) in knows:
        knows_map[did] = chance
    distractors = list(knows_map.keys())
    distractor_columns = [f'd_{d}' for d in distractors]
    students = DataFrame(columns=["email", "id", "created", *distractor_columns])    
    with APP.test_client(use_cookies=True) as c:
        def create_student(student):
            resp = throw_on_http_fail(c.post("/signup", json={**student, "retype": student["password"]}), status=300)
            was_created = "id" in resp
            #NOTE: we ignore the fact that student is already present in the system - status_code for existing user is 200 with "redirect" in resp
            resp = throw_on_http_fail(c.post("/login", json={**student}))
            student_id = resp["id"]
            students.loc[student_id, [ "email", "id", "created", *distractor_columns ]] = [student["email"], student_id, was_created, *[knows_map[d] for d in distractors]]            
            if input_students is not None:
                for _, student in input_students[input_students["email"] == student["email"]].iterrows():
                    for column in student[student.notnull()].index:
                        if column.startswith('d_'):
                            # did = int(column.split('_')[1])
                            if column not in students.columns or students.isna().loc[student_id, column]:
                                students.loc[student_id, column] = student[column]                            

        if input_students is not None: 
            for _, student in input_students.iterrows():
                create_student(student)
        if num_students is not None:
            for i in range(num_students):
                student = build_student(i)
                create_student(student)
    student_ids = set(students["id"])
    present_knowledge_query = models.StudentKnowledge.query.where(models.StudentKnowledge.student_id.in_(student_ids))
    if knowledge_replace: 
        present_knowledge_query.delete()
        present_knowledge = {}
    else:
        present_plain = present_knowledge_query.all()
        present_knowledge = {kid:ks[0] for kid, ks in groupby(present_plain, key=lambda k: (k.student_id, k.distractor_id))}
    for _, student in students.iterrows(): 
        for c in student[student.notnull()].index:
            if c.startswith("d_"):    
                distractor_id = int(c.split('_')[1])
                knowledge_id = student.id, distractor_id
                if knowledge_id in present_knowledge:
                    present_knowledge[knowledge_id].chance_to_select = student[c]
                else:
                    k = models.StudentKnowledge(student_id=student.id, distractor_id=distractor_id, chance_to_select = student[c])
                    models.DB.session.add(k) 
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
    knowledge_map = {sid:{f'd_{k.distractor_id}':k.chance_to_select for k in ks} for sid, ks in groupby(knowledge, key=lambda k: k.student_id) }
    distractor_columns = [ f'd_{did}' for did in sorted(list(set([ k.distractor_id for k in knowledge ]))) ]
    df = DataFrame(columns=['email', 'id', *distractor_columns])
    for s in students:
        df.loc[s.id, ['email', 'id']] = [s.email, s.id]
        for did, chance in knowledge_map.get(s.id, {}).items():
            df.loc[s.id, did] = chance
    if output is not None: 
        df.to_csv(output, index=False)
    sys.stdout.write(f"Exported knowledge:\n{df}\n")

@quiz_cli.command("run")
@click.option('-q', '--quiz', type=int, required=True)
@click.option('-n', '--n-times', type=int, default=1)
@click.option('-i', '--instructor', default='i@usf.edu') #evo algo to use
@click.option('-p', '--password', default='pwd') #evo algo to use
@click.option('--algo') #evo algo to use
@click.option('--algo-params') #json settings of algo
@click.option('--rnd', is_flag=True) #randomize student order
@click.option('-aw', '--answer-weight', type=float, default=1) #randomize student order
@click.option('-o', '--output')
def simulate_quiz(quiz, instructor, password, algo, algo_params, rnd, answer_weight, n_times, output):    
    import evopie.config
    for run_idx in range(n_times):
        if algo is not None:         
            evopie.config.distractor_selection_process = algo 
        if algo_params is not None: 
            evopie.config.distractor_selecton_settings = json.loads(algo_params)
        #close prev evo process
        existing_evo = models.EvoProcess.query.where(models.EvoProcess.quiz_id == quiz, models.EvoProcess.status == EVO_PROCESS_STATUS_ACTIVE).all()
        for evo in existing_evo:
            evo.status = EVO_PROCESS_STATUS_STOPPED    
        models.DB.session.commit()    
        with APP.test_client(use_cookies=True) as c: #instructor session
            throw_on_http_fail(c.post("/login",json={"email": instructor, "password": password}))
            throw_on_http_fail(c.post(f"/quizzes/{quiz}/status", json={ "status" : "HIDDEN" })) #stop in memory evo process
            throw_on_http_fail(c.post(f"/quizzes/{quiz}/status", json={ "status" : "STEP1" }))
            # evo process started 
        k_plain = models.StudentKnowledge.query.all() #TODO: students should be per instructor eventually 
        knowledge = {student_id: {k.distractor_id:k.chance_to_select for k in ks} for student_id, ks in groupby(k_plain, key=lambda k: k.student_id) }
        students_plain = models.User.query.filter_by(role=ROLE_STUDENT).all()
        students = list(students_plain) #[s.id for s in students_plain]
        student_ids = set([s.id for s in students])
        models.QuizAttempt.query.where(models.QuizAttempt.student_id.in_(student_ids), models.QuizAttempt.quiz_id == quiz).delete()
        models.DB.session.commit()
        if rnd:
            shuffle(students)
        for student in students:
            with APP.test_client(use_cookies=True) as c:
                resp = throw_on_http_fail(c.post("/login", json={"email": student.email, "password": "pwd"}))
                if "id" not in resp:
                    continue #ignore non-default students
                resp = throw_on_http_fail(c.get(f"/student/{quiz}", headers={"Accept": "application/json"}))            
                questions = {str(q["id"]):[a[0] for a in q["alternatives"] if a[0] != -1] for q in resp["questions"]}
                student_knowledge = knowledge.get(student.id, {})
                student_knowledge[-1] = answer_weight
                # initial_responses = {qid:str(choice(known_distractors)) if any(known_distractors) else "-1" 
                #                         for qid, distractors in questions.items() 
                #                         for known_distractors in [[d for d in distractors if d in student_knowledge and random() < student_knowledge[d] ]]}

                initial_responses = {qid:str(ds[selected_d_index])
                                        for qid, distractors in questions.items() 
                                        for ds in [[-1, *[d for d in distractors if d in student_knowledge and student_knowledge[d] > 0]]] 
                                        for weights in [[student_knowledge[d] for d in ds]]
                                        for sums in [np.cumsum(weights)]
                                        for level in [(random() * sums[-1])]
                                        for selected_d_index in [next((i for i, s in enumerate(sums) if s > level), 0)]}
                resp = throw_on_http_fail(c.post(f"/quizzes/{quiz}/take", json={"initial_responses": initial_responses, "justifications": {}}))
                #NOTE: no justifications in this run 
        #TODO: get_evo(quiz)     
        evo = get_evo(quiz)
        if evo is None:
            sys.stdout.write(f"[{run_idx + 1}/{n_times}] Quiz {quiz} finished\n")            
        else:
            evo.stop()
            evo.join()
            sql_evo_serializer.wait_dump(timeout=5)  #wait for db data dump
            evo.archive["p"] = 0
            evo.archive.loc[-1, ['g', 'p']] = [f"-1, {answer_weight}", 0]
            evo.archive["p"] = evo.archive["p"].astype(int)            
            for ind in evo.population:
                evo.archive.loc[ind, "p"] = 1        
            if output is not None: 
                evo.archive.to_csv(output.format(run_idx))    
            sys.stdout.write(f"[{run_idx + 1}/{n_times}] Quiz {quiz} finished\n{evo.archive}\n")
            

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

APP.cli.add_command(quiz_cli)
APP.cli.add_command(student_cli)