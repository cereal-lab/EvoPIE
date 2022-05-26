'''
Implementation of evolutionary processes 
'''
import datetime
import json
import random
from threading import Thread, Condition
from pandas import DataFrame       

from evopie import APP, models
from evopie.utils import groupby
from abc import ABC, abstractmethod

# def get_submatrix(f: DataFrame):
#     ''' Searches for biggest full submatrix in given sparse dataframe'''
#     filtered = f.loc[f.notnull().any(axis=1)] #returns view 

class EvolutionaryProcess(Thread, ABC): 

    def __init__(self):
        super(Thread, self).__init__(daemon=True)
        self.name = self.__class__.__name__
        self.interactions = DataFrame()
        self.gen = 0

    @abstractmethod
    def run():
        pass

    def start(self):
        ''' not necessary, but make it obvoius that should be redefined in children '''
        super(Thread, self).start()  

    @abstractmethod
    def stop(self):
        pass

class InteractiveEvolutionaryProcess(EvolutionaryProcess):

    def get_for_evaluation(self, student_id):
        pass 
    def set_evaluation(self, evaluation):
        pass 

class P_PHC(InteractiveEvolutionaryProcess):
    '''
    P-PHC major sceleton
    '''
    def __init__(self):
        super().__init__()
        self.waiting_evaluations = []
        self.on_new_evaluation = Condition()        
        self.quiz_id = None
        self.pop_size = 10
        self.pareto_n = 2 
        self.ind_id = lambda x: str(x)
        # IMPORTANT: all next funcs should be initialized before process run
        # Otherwise it will be runtime error
        self.init = None
        self.mutate = None 
        self.select = None 
        self.update_score = None
        self.stopped = False
        self.active_quizes = {}

    @property
    def population(self):
        return self.interactions.loc[self.interactions['l_gen'] == self.gen]

    def init_population(self):
        while len(self.interactions) < self.pop_size:
            ind = self.init(self.interactions)
            cs_id = self.ind_id(ind)
            if cs_id not in self.interactions.index:
                self.interactions.loc[cs_id] = {'ind':ind, 'f_gen': self.gen, 'l_gen': self.gen, 'p': cs_id, 'stud': []} 

    def mutate_population(self):
        for p_id, p in self.population['ind'].items():
            children = self.mutate(p)
            for child in children:
                c_id = self.ind_id(child)
                if c_id not in self.interactions.index:
                    self.interactions.loc[c_id] = {'ind':child, 'f_gen': self.gen, 'l_gen': self.gen, 'p': p_id, 'stud': []} 
                else:
                    self.interactions.loc[c_id, ['l_gen', 'p', 'stud']] = (self.gen, p_id, [])    

    def start(self, quiz_id, init, mutate, select, update_score, pop_size = 10, pareto_n = 2):
        self.quiz_id = quiz_id
        if not self.from_sql(quiz_id):
            self.pop_size = pop_size 
            self.pareto_n = pareto_n 
            self.init = init
            self.mutate = mutate
            self.select = select
            self.update_score = update_score
        self.init_populaiton() #these should be here - otherwise possible race condition - if we put it in run, student could request quiz before first generation initialization
        self.mutate_population()
        super().start() # start evo thread - check run method

    def stop(self):
        with self.on_new_evaluation:
            self.stopped = True 
            self.on_new_evaluation.notify()

    def run(self):
        '''Func that implemets evo loop'''
        while True: 
            #generating children from parent
            while True: #loop which processes evaluations - awaits them 
                with self.on_new_evaluation:
                    self.on_new_evaluation.wait_for(lambda: any(self.waiting_evaluations))
                    if self.stopped:
                        with APP.app_context(): #necessary to have app_context to save to db
                            self.to_sql()
                        return #exit evolution 
                    for eval in self.waiting_evaluations:
                        student_id = eval["student_id"]
                        p_id = self.active_quizes[student_id]
                        del self.active_quizes[student_id]
                        eval_group = self.population[self.interactions['p'] == p_id]
                        for cs_id, ind in eval_group['ind'].items():
                            for gene, genes_coeval in zip(ind, eval["result"]): #result - list where for each question we provide some data
                                self.interactions.loc[cs_id, f'S_{student_id}'] = self.update_score(self.interactions.loc[cs_id, f'S_{student_id}'], gene, genes_coeval)
                        eval_group['stud'].append(f'S_{student_id}')
                    self.waiting_evaluations = []
                    gen_was_evaluated = self.population[self.interactions['stud'].apply(len) == self.pareto_n].all()
                    if gen_was_evaluated:
                        # Pareto domiation increases l_gen for winners 
                        for eval_group in self.population.groupby('p'):
                            p_id, parent = list(eval_group[eval_group.index == eval_group['p']].iterrows())[0]
                            students = parent['stud'] #students by which we compare
                            possible_winners = [ ch_id for ch_id, child in eval_group.iterrows() 
                                if ch_id != p_id and child[students] >= parent[students] ] #Pareto check
                            group_winner = random.choice(possible_winners)
                            self.interactions.loc[group_winner, 'l_gen'] += 1                            
                        self.gen += 1 # going to next generation
                        break
            self.mutate_population()


    def get_for_evaluation(self, student_id):
        with self.on_new_evaluation: #takes lock of cv in order to protect interactions
            if student_id not in self.interactions:
                self.interactions[f'S_{student_id}'] = None #new student
            if student_id in self.active_quizes: #student should solve quiz with same set of distractors on retake it could be regenerated
                p_id = self.active_quizes[student_id]
            else:
                ind = self.select(student_id, self.population)
                #ind is representative 
                ind_id = ind.index[0]
                p_id = ind.loc[ind_id, "p"]
                self.active_quizes[student_id] = p_id
            inds = self.population[self.population['p'] == p_id] #select group from one parent            
            return list(set(d for ds in q_ds for d in ds) for q_ds in zip(inds['ind'])) #returns for each qeuestions set of distractors

    def set_evaluation(self, evaluation):
        ''' This is called by flask req-resp thread and put evaluation objection into queue 
            Actual processing is done in evo thread
        '''
        with self.on_new_evaluation:
            self.waiting_evaluations.append(evaluation)
            self.on_new_evaluation.notify()            

    def to_sql(self):
        '''
        Saves state through sqlalchemy 
        ---
        Tables 
            evo_process - interaction matrix 
            evo_process_settings - initial config
        ---
        Should be called in flask app context 
        '''
        evo_process = models.EvoProcess.query.where(models.EvoProcess.quiz_id == self.quiz_id and models.EvoProcess.end_timestamp == None).one()
        now = datetime.now()
        def get_func_name(f):
            return f.__name__
        def get_same(x):
            return x
        if evo_process: #update with new parameters 
            props = { "init": get_func_name, "mutate": get_func_name, "select": get_func_name, "update_score": get_func_name, "pop_size": get_same, "pareto_n": get_same, "gen": get_same }
            for attr, attr_getter in props.items():
                old_attr_val = getattr(evo_process, attr)
                new_attr_val = attr_getter(getattr(self, attr))
                if new_attr_val != old_attr_val: 
                    setattr(evo_process, attr, new_attr_val)
                    evo_process.touch_timestamp = now
                    evo_process.updates.add(models.EvoProcessUpdate(id = evo_process.id, 
                        timestamp = now, prop_name=attr, from_value=str(old_attr_val), to_value = str(new_attr_val)))
        else: #insert new record  
            evo_process = models.EvoProcess(quiz_id=self.quiz_id,
                            start_timestamp = now,
                            touch_timestamp = now,
                            init = get_func_name(self.init),
                            mutate = get_func_name(self.mutate),
                            select = get_func_name(self.select),
                            update_score = get_func_name(self.update_score),
                            pop_size = self.pop_size,
                            pareto_n = self.pareto_n,
                            gen = self.gen)
            models.DB.session.add(evo_process)
        
        #rewrites interactions
        evo_process.interactions = [ models.EvoProcessInteractions(cs_id = cs_id, 
                                        ind = json.dumps(r.ind),
                                        first_gen = r.f_gen, last_gen = r.l_gen, parent = r.p,
                                        objectives = json.dumps(r.stud),
                                        evaluations = json.dumps({c: r[c] for c in r[r.notnull()].index if c.startswith('S_') })) 
                                        for cs_id, r in self.interactions.iterrows() ]
        models.DB.session.commit()

    def from_sql(self, quiz_id):
        evo_process = models.EvoProcess.query.where(models.EvoProcess.quiz_id == quiz_id and models.EvoProcess.end_timestamp == None).one()
        if evo_process: #load params from settings
            gl = globals()
            self.init = gl[evo_process.init]
            self.mutate = gl[evo_process.mutate]
            self.select = gl[evo_process.select]
            self.update_score = gl[evo_process.update_score]
            self.pop_size = evo_process.pop_size
            self.pareto_n = evo_process.pareto_n
            self.gen = evo_process.gen
            interactions = evo_process.interactions
            plain_data = {i.cs_id:{'ind': json.loads(i.ind), 'f_gen': i.first_gen, 'l_gen': i.last_gen, 'p': i.parent, 
                                    'stud': json.loads(i.objectives), **json.loads(i.evaluations)} for i in interactions}
            self.interactions = DataFrame.from_dict(plain_data, orient='index')
            return True 
        return False

def random_group_init(distractors_per_question, group_size = 3):
    '''
        initialization for schema [d1d3d4, d7d10d12, ...]
    '''
    def init(interactions):
        ind = []
        for distractors in distractors_per_question:
            d_set = set(distractors)
            group = []
            for _ in range(min(len(d_set), group_size)):
                d = random.choice(d_set)
                d_set.remove(d)
                group.append(d)
            ind.append(group)
        return ind 
    return init

def random_group_mutate(distractors_per_question, prob = 0.25): 
    def mutate(ind): 
        children = [ [ random.choice(ds) if len(ds) > 0 and random.random() < prob else gene 
                        for gene in genes 
                        for ds in [ set(distractors) - set([gene]) ] ]            
                    for genes, distractors in zip(ind, distractors_per_question) ]
        return children
    return mutate

def random_group_select():
    def select(student_id, population):
        return population.sample()        
    return select 

def simple_update_ind_score():    
    def update(cur_score, gene, answer):
        for deception in gene:
            if deception == answer:
                cur_score += 1
        return cur_score
    return update

#this is global state across all requests
#NOTE: no bound is given for this state - possibly limit number of elems and give HTTP 429 - too many requests
quiz_evo_processes = {}

def get_evo(quiz_id): 
    return quiz_evo_processes.get(quiz_id, None)

def start_default_p_phc(quiz):
    '''
    Starts preconfigured p_phc with possibly dummy params 
    Should be called is flask app context installed - because of sqlalchemy usage 
    ----
    Paraeters
        quiz - Quiz/quiz id 
    '''

    if type(quiz) == 'Quiz':
        questions = quiz.quiz_questions 
        quiz_id = quiz.id
    else: #treat it as id 
        q = models.Quiz.query.get_or_404(quiz)
        questions = q.quiz_questions
        quiz_id = q.id
    question_ids = [ q.id for q in questions ]
    distractors = models.Distractor.query.where(models.Distractor.question_id.in_(question_ids)).with_entities(models.Distractor.id, models.Distractor.question_id)
    distractor_map = { q_id: [ d.id for d in ds ] for q_id, ds in groupby(distractors, key=lambda d: d.question_id) }
    distractors_per_question = [ distractor_map.get(q.id, []) for q in questions ]
    evo = P_PHC()
    evo.start(quiz_id, pop_size=10, pareto_n=2, 
        init = random_group_init(distractors_per_question, group_size=3), 
        mutate = random_group_mutate(distractors_per_question, prob=0.25),
        select = random_group_select(),
        update_ind_score = simple_update_ind_score())
    quiz_evo_processes[quiz_id] = evo
    return evo

