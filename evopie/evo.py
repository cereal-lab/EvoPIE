'''
Implementation of evolutionary processes 
'''
from datetime import datetime
import json
import random
from threading import Thread, Condition
from typing import Any
from pandas import DataFrame       

from evopie import APP, models
from evopie.utils import groupby
from abc import ABC, abstractmethod
from evopie.config import EVO_PROCESS_STATUS_ACTIVE, distractor_selection_process, distractor_selecton_settings
from dataclasses import dataclass

# def get_submatrix(f: DataFrame):
#     ''' Searches for biggest full submatrix in given sparse dataframe'''
#     filtered = f.loc[f.notnull().any(axis=1)] #returns view 

# @dataclass
# class Individual:
#     genotype_id: str # unique id of genotype    
#     genotype: Any
#     # coevaluation_group_id: int # parent position inside population    

@dataclass 
class Evaluation:
    evaluator_id: int 
    result: Any

@dataclass 
class CoevaluationGroup:    
    inds: 'list[int]'
    objs: 'list[int]'

@dataclass
class Genotype: #NOTE: we need this wrapper because pandas goes crazy if you provide to it just lists
    g: Any

class EvolutionaryProcess(Thread, ABC): 

    def __init__(self, **kwargs):     
        Thread.__init__(self)
        self.population: 'list[int]' = [] # int here is an index in archive (next field)
        self.objectives: 'list[int]' = [] 
        self.archive = DataFrame(columns=['g']) #g contains genotype
        self.archive[["g"]] = self.archive[["g"]].astype(object)
        self.gen = 0
        self.stopped = False   
        self.set_state(**kwargs)     

    def add_genotype_to_archive(self, genotype):
        genotype_obj = Genotype(genotype)
        ix = self.archive[self.archive['g'] == genotype_obj].index
        if len(ix) > 0:
            return int(ix[0]) #NOTE: by default DataFrame index is int64 which fails json serialization
        else:
            id = len(self.archive)
            self.archive.loc[id, 'g'] = genotype_obj
            return id

    def get_genotype(self, genotype_id): 
        return self.archive.loc[genotype_id, 'g'].g

    @abstractmethod
    def run(self):
        pass

    def start(self):
        self.name = self.__class__.__name__
        self.daemon = True
        ''' not necessary, but make it obvoius that should be redefined in children '''
        Thread.start(self)  

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def init(self) -> int:
        ''' inits individual, adds it to archive if new and returns index in the archive '''
        pass

    @abstractmethod
    def init_population(self) -> 'list[int]':
        ''' initialize whole population - indexes from archive '''
        pass

    @abstractmethod
    def mutate_population(self) -> None:
        ''' mutates whole population '''
        pass

    @abstractmethod
    def mutate(self, ind: int) -> 'list[int]':
        ''' mutates ind in the population. Returns possibly many children  '''
        pass

    @abstractmethod
    def select(self, evaluator_id: int) -> int:
        ''' selects individuals for evaluator in a form of coevaluation group id'''
        pass

    @abstractmethod
    def update_fitness(self, ind: int, evaluation: Evaluation) -> None:
        ''' updates individual fitness '''
        pass

    def get_state(self) -> dict:
        ''' returns dict which represents intenal state '''
        # return { "population": self.population, "objectives": self.objectives, "archive": self.archive, "gen": self.gen }
        return { "gen": self.gen }

    def set_state(self, **kwargs) -> None:
        ''' sets state of evo process '''
        self.population = kwargs.get("population", self.population)
        self.objectives = kwargs.get("objectives", self.objectives)
        self.archive = kwargs.get("archive", self.archive)
        self.gen = kwargs.get("gen", self.gen)        

class InteractiveEvaluation(ABC):

    @abstractmethod
    def get_for_evaluation(self, evaluator_id: int) -> 'list[list[int]]':
        pass 

    @abstractmethod
    def set_evaluation(self, evaluation: Evaluation) -> None:
        pass   

class EvoSerializer:
    def to_store(self, quiz_id: int, evo: EvolutionaryProcess) -> None:
        pass 
    def from_store(self, quiz_id: int) -> EvolutionaryProcess:
        return None

do_not_serialize = EvoSerializer() #singleton - check if python has some syntax to do more elegant

class P_PHC(EvolutionaryProcess, InteractiveEvaluation, ABC):
    '''
    P-PHC major sceleton
    '''
    def __init__(self, **kwargs):        
        self.waiting_evaluations: 'list[Evaluation]' = []
        self.on_new_evaluation = Condition()
        self.serializer = do_not_serialize
        self.evaluator_coevaluation_groups = {} #dict where by evaluator_id we have given to evaluator coevaluation_group
        self.kwargs = kwargs
        self.pop_size = 10
        self.pareto_n = 2
        self.coevaluation_groups = {}
        super().__init__(**kwargs)

    def get_state(self):        
        return { **super().get_state(), "pop_size": self.pop_size, "pareto_n": self.pareto_n, 
                    "coevaluation_groups": {id: {"inds": g.inds, "objs": g.objs} for id, g in self.coevaluation_groups.items()}, 
                    "evaluator_coevaluation_groups": self.evaluator_coevaluation_groups }

    def set_state(self, **kwargs):  
        super().set_state(**kwargs)      
        self.pop_size = kwargs.get("pop_size", self.pop_size)
        self.pareto_n = kwargs.get("pareto_n", self.pareto_n)
        self.gen = kwargs.get("gen", self.gen)
        self.coevaluation_groups = { int(id):CoevaluationGroup(g["inds"], g["objs"]) for id, g in kwargs.get("coevaluation_groups", self.coevaluation_groups).items()}
        self.evaluator_coevaluation_groups = kwargs.get("evaluator_coevaluation_groups", self.evaluator_coevaluation_groups)
        self.serializer = kwargs.get("serializer", self.serializer)

    def init_population(self):
        while len(self.population) < self.pop_size:
            ind = self.init()
            self.population.append(ind)

    def mutate_population(self):
        self.coevaluation_groups = { **self.coevaluation_groups, 
                                    **{pid: CoevaluationGroup(inds=[parent, *self.mutate(parent)], objs = []) 
                                        for pid, parent in enumerate(self.population)
                                        if pid not in self.coevaluation_groups} }             

    def start(self):
        quiz_id = self.kwargs.get("quiz_id", "")
        APP.logger.info(f"[{self.__class__.__name__}] starting for quiz {quiz_id}")
        self.init_population() #these should be here - otherwise possible race condition - if we put it in run, student could request quiz before first generation initialization
        self.mutate_population()
        super().start() # start evo thread - check run method

    def stop(self):
        quiz_id = self.kwargs.get("quiz_id", -1)
        APP.logger.info(f"[{self.__class__.__name__}] stopping quiz {quiz_id} evo")
        with self.on_new_evaluation:
            self.stopped = True 
            self.on_new_evaluation.notify()

    def pareto_compare(self, eval_group_id: int, eval_group: CoevaluationGroup):        
        if len(eval_group.objs) >= self.pareto_n:
            genotype_evaluations = {genotype_id: evals 
                                    for genotype_id, evals in self.archive.loc[eval_group.inds, eval_group.objs].iterrows()}
            parent = eval_group.inds[0]
            parent_genotype_evaluation = genotype_evaluations[parent]
            possible_winners = [ child for child in eval_group.inds[1:]
                                    if not((genotype_evaluations[child] <= parent_genotype_evaluation).all()) ] #Pareto check
            if len(possible_winners) > 0:
                winner = random.choice(possible_winners)
                self.population[eval_group_id] = winner #winner takes place of a parent
            del self.coevaluation_groups[eval_group_id]

    def run(self):
        '''Func that implemets evo loop'''
        while True: # gen loop 
            while True: #loop which processes evaluations - awaits them                 
                with self.on_new_evaluation:
                    self.on_generation_start()
                    self.on_new_evaluation.wait_for(lambda: any(self.waiting_evaluations))
                    if self.stopped:
                        quiz_id = self.kwargs.get("quiz_id", None)
                        try:                            
                            self.serializer.to_store(quiz_id, self)
                            APP.logger.info(f"[{self.__class__.__name__}] stopped quiz {quiz_id} evo")
                        except Any as e: 
                            APP.logger.error(f"[{self.__class__.__name__}] error on stopping quiz {quiz_id}: {e}")
                        return #exit evolution 
                    try:
                        for eval in self.waiting_evaluations:
                            if eval.evaluator_id not in self.evaluator_coevaluation_groups:
                                #NOTE: should not be here usually - could be on system restart
                                APP.logger.warn(f"[p-phc] got evaluation for unexpected group: {eval}. {self.evaluator_coevaluation_groups}")
                                continue
                            coevaluation_group_id = self.evaluator_coevaluation_groups[eval.evaluator_id]
                            eval_group = self.coevaluation_groups[coevaluation_group_id]
                            eval_group.objs.append(eval.evaluator_id)                        
                            for ind in eval_group.inds:
                                self.update_fitness(ind, eval)
                            del self.evaluator_coevaluation_groups[eval.evaluator_id]
                            self.pareto_compare(coevaluation_group_id, eval_group)
                    except Any as e: 
                        quiz_id = self.kwargs.get("quiz_id", None)
                        APP.logger.error(f"[{self.__class__.__name__}] error on evaluation of quiz {quiz_id}: {e}. Ignored: {self.waiting_evaluations}")
                    self.waiting_evaluations = []
                    gen_was_evaluated = len(self.coevaluation_groups) == 0 #group is treated as evaluated when removed  from this dict
                    if gen_was_evaluated:                        
                        self.on_generation_end()
                        self.gen += 1 # going to next generation                    
                        self.mutate_population()
                        break            

    def on_generation_start(self):
        ''' Derived classes could add logic to be executed on generation start boundary. Executes under lock '''
        pass

    def on_generation_end(self):
        ''' Derived classes could add logic to be executed on generation end boundary. Executes under lock '''
        pass

    @abstractmethod
    def repr_adapter(self, ind_genotypes):
        pass

    def get_for_evaluation(self, evaluator_id):
        with self.on_new_evaluation: #takes lock of cv in order to protect archive
            if evaluator_id not in self.archive:
                self.archive[evaluator_id] = None #new evaluator
                self.objectives.append(evaluator_id)                
            if evaluator_id in self.evaluator_coevaluation_groups: #student should solve quiz with same set of distractors on retake it could be regenerated
                coevaluation_group_id = self.evaluator_coevaluation_groups[evaluator_id]
            else:
                coevaluation_group_id = self.select(evaluator_id)
                self.evaluator_coevaluation_groups[evaluator_id] = coevaluation_group_id
            inds = self.coevaluation_groups[coevaluation_group_id].inds #select group from one parent            
            ind_genotypes = [ self.get_genotype(ind) for ind in inds ]
            return self.repr_adapter(ind_genotypes)

    def set_evaluation(self, evaluation):
        ''' This is called by flask req-resp thread and put evaluation objection into queue 
            Actual processing is done in evo thread
        '''
        with self.on_new_evaluation:
            self.waiting_evaluations.append(evaluation)
            self.on_new_evaluation.notify()            

class SqlEvoSerializer(EvoSerializer):
    ''' Serializes into sqlite schema.
    '''
    def to_store(self, quiz_id, evo):
        '''
        Saves state through sqlalchemy 
        ---
        Tables 
            evo_process - interaction matrix 
            evo_process_settings - initial config
        ---
        Should be called in flask app context 
        '''
        evo_state = evo.get_state()
        with APP.app_context():            
            if quiz_id is None:
                APP.logger.warn(f"[sql-evo-serializer] evo state was not saved. No quiz_id was provided. EVO: {evo.__class__.__name__}, {evo_state}")
                return #we do not store state 
            evo_process = models.EvoProcess.query.where(models.EvoProcess.quiz_id == quiz_id, models.EvoProcess.status == EVO_PROCESS_STATUS_ACTIVE).one_or_none()
            if evo_process is not None: #update with new parameters 
                evo_process.impl = evo.__class__.__name__
                evo_process.impl_state = json.dumps(evo_state)
                evo_process.population = json.dumps(evo.population)
                evo_process.objectives = json.dumps(evo.objectives)
            else: #insert new record  
                evo_process = models.EvoProcess(quiz_id=quiz_id,
                                start_timestamp = datetime.now(),
                                status = EVO_PROCESS_STATUS_ACTIVE,
                                impl = evo.__class__.__name__,
                                impl_state = json.dumps(evo_state),
                                population = json.dumps(evo.population),
                                objectives = json.dumps(evo.objectives))
                models.DB.session.add(evo_process)            
            evo_process.archive = [ models.EvoProcessArchive(genotype_id = genotype_id,
                                            genotype = json.dumps(r.g.g),
                                            objectives = json.dumps({c: r[c] for c in r[r.notnull()].index if c != "g" })) 
                                            for genotype_id, r in evo.archive.iterrows() ]
            models.DB.session.commit()

    def from_store(self, quiz_id):
        with APP.app_context():
            evo_process = models.EvoProcess.query.where(models.EvoProcess.quiz_id == quiz_id, models.EvoProcess.status == EVO_PROCESS_STATUS_ACTIVE).one_or_none()
            if evo_process is not None:
                plain_interactions = evo_process.archive
        if evo_process is not None: #load params from settings            
            plain_data = {i.genotype_id:{'g': Genotype(json.loads(i.genotype)),
                                    **{ int(id):obj for id, obj in json.loads(i.objectives).items()}} for i in plain_interactions}
            population = json.loads(evo_process.population)
            objectives = json.loads(evo_process.objectives)
            archive = DataFrame.from_dict(plain_data, orient='index', columns=["g", *objectives])
            gl = globals()
            impl_state = json.loads(evo_process.impl_state)
            evo = gl[evo_process.impl](serializer = self, quiz_id = quiz_id, archive = archive, 
                    population = population, objectives = objectives, **impl_state)
            return evo
        return None

sql_evo_serializer = SqlEvoSerializer()

class Default_P_PHC(P_PHC):
    def __init__(self, **kwargs):
        self.gene_size = 3
        self.mut_prob = 0.25
        self.distractors_per_question = []
        super().__init__(**kwargs)        

    def get_state(self):
        return {**super().get_state(), "gene_size": self.gene_size, "mut_prob": self.mut_prob}

    def set_state(self, **kwargs):
        super().set_state(**kwargs)
        self.gene_size = kwargs.get("gene_size", self.gene_size)
        self.mut_prob = kwargs.get("mut_prob", self.mut_prob)
        self.distractors_per_question = kwargs.get("distractors_per_question", self.distractors_per_question)        

    def init_distractor_pools(self):
        quiz_id = self.kwargs.get("quiz_id", None)
        if quiz_id is None:
            APP.logger.warn("[default-p-phc] distractor pools were not initialized")
            return []
        with APP.app_context():
            q = models.Quiz.query.get_or_404(quiz_id)
            questions = q.quiz_questions
            quiz_id = q.id
            question_ids = [ q.id for q in questions ]
            distractors = models.Distractor.query.where(models.Distractor.question_id.in_(question_ids)).with_entities(models.Distractor.id, models.Distractor.question_id)
            distractor_map = { q_id: [ d.id for d in ds ] for q_id, ds in groupby(distractors, key=lambda d: d.question_id) }
            return [ distractor_map.get(q.id, []) for q in questions ]

    def init_population(self):
        if len(self.distractors_per_question) == 0:
            self.distractors_per_question = self.init_distractor_pools()
        return super().init_population()

    def init(self):
        genotype = []
        for distractors in self.distractors_per_question:
            d_set = set(distractors)
            group = []
            for _ in range(min(len(d_set), self.gene_size)):
                d = random.choice(list(d_set))
                d_set.remove(d)
                group.append(d)
            genotype.append(sorted(group))
        ind = self.add_genotype_to_archive(genotype)
        return ind 

    def mutate(self, parent_id): 
        genotype = self.get_genotype(parent_id)
        tries = 10
        while tries > 0:
            child = []
            for genes, distractors in zip(genotype, self.distractors_per_question):
                d_set = set(distractors)
                group = []
                for g in genes:
                    # possibilities = list(d_set - set([g]))
                    possibilities = list(d_set) #NOTE: prev line is mroe restrictive - tries to differ each gene
                    if len(possibilities) == 0:
                        d = g
                    else: 
                        d = random.choice(possibilities)
                    d_set.remove(d)
                    group.append(d)
                child.append(sorted(group))
            child_id = self.add_genotype_to_archive(child)
            if child_id != parent_id:
                return [ child_id ]
            tries -= 1
        return []

    def select(self, evaluator_id):
        return random.choice(list(self.coevaluation_groups.keys()))

    def update_fitness(self, ind, eval):  
        cur_score = self.archive.loc[ind, eval.evaluator_id]
        cur_score = 0 if cur_score is None else cur_score
        ind_genotype = self.get_genotype(ind)
        for gene, answer in zip(ind_genotype, eval.result): #result - list where for each question we provide some data                        
            for deception in gene:
                if deception == answer:
                    cur_score += 1
        self.archive.loc[ind, eval.evaluator_id] = cur_score

    def on_generation_start(self):
        self.serializer.to_store(self.kwargs.get("quiz_id", None), self)

    def on_generation_end(self):
        self.distractors_per_question = self.init_distractor_pools()

    def repr_adapter(self, ind_genotypes):
        return [set(d for ds in q_ds for d in ds) for q_ds in zip(*ind_genotypes)]

#this is global state across all requests
#NOTE: no bound is given for this state - possibly limit number of elems and give HTTP 429 - too many requests
quiz_evo_processes = {}

def start_evo(quiz_id):
    evo = sql_evo_serializer.from_store(quiz_id)
    if evo is None and distractor_selection_process is not None:
        g = globals()
        if distractor_selection_process in g: 
            evo = g[distractor_selection_process](serializer=sql_evo_serializer, quiz_id=quiz_id, **distractor_selecton_settings)
        else:
            return None
    evo.start()
    quiz_evo_processes[quiz_id] = evo
    return evo
    
def get_evo(quiz_id): 
    return quiz_evo_processes.get(quiz_id, None)

def init_evo(): 
    ''' should be executed at system start to start quizes evo processes from db table '''
    with APP.app_context():
        evo_quiz_ids_q = models.Quiz.query.where(models.Quiz.status == 'STEP1').with_entities(models.Quiz.id)
        evo_quiz_ids = list(evo_quiz_ids_q)
        if len(evo_quiz_ids) == 0:
            APP.logger.info("[init_evo] no evo processes to start")
        for quiz_id in evo_quiz_ids:
            start_evo(quiz_id.id)
        
init_evo() # evo init process        