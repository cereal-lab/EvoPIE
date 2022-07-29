'''
Implementation of evolutionary processes 
'''
from datetime import datetime
import json
from math import comb, prod
import numpy as np
from threading import Thread, Condition
from typing import Any, Iterable
from pandas import DataFrame  

from evopie import APP, models
from evopie.utils import groupby
from abc import ABC, abstractmethod
from evopie.config import EVO_PROCESS_STATUS_ACTIVE
import evopie.config
from dataclasses import dataclass
from numpy import unique

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
    def __repr__(self) -> str:
        return self.g.__repr__()

class EvoSerializer:
    def to_store(self, process: models.EvoProcess) -> None:
        pass 
    def from_store(self, quiz_ids: Iterable[int]) -> 'list[models.EvoProcess]':
        ''' Loads quiz processes at once '''
        return {}

do_not_serialize = EvoSerializer() #singleton - check if python has some syntax to do more elegant    

class SqlEvoSerializer(Thread, EvoSerializer):
    ''' Serializes into sqlite schema.
    '''

    def __init__(self):
        super().__init__()
        self.daemon = True 
        self.evo_states: 'dict[int, models.EvoProcess]' = {} #per each quiz separate evo state
        self.ready_to_write = Condition()
        self.dumped = Condition()
        self.stopped = False

    def stop(self):
        with self.ready_to_write:
            self.stopped = True 
            self.ready_to_write.notify()

    def wait_dump(self, timeout):
        with self.dumped:
            self.dumped.wait(timeout)

    def run(self):
        with self.ready_to_write:
            while True:            
                self.ready_to_write.wait_for(predicate=lambda: (len(self.evo_states) > 0) or self.stopped)
                with APP.app_context():            
                    evo_processes = models.EvoProcess.query.where(models.EvoProcess.quiz_id.in_(self.evo_states.keys()), models.EvoProcess.status == EVO_PROCESS_STATUS_ACTIVE).all()
                    evo_processes_map = {p.quiz_id: p for p in evo_processes}
                    for quiz_id, evo_state in self.evo_states.items():                    
                        if quiz_id in evo_processes_map: #update with new parameters 
                            evo_process = evo_processes_map[quiz_id]
                            evo_process.impl = evo_state.impl
                            evo_process.impl_state = evo_state.impl_state
                            evo_process.population = evo_state.population
                            evo_process.objectives = evo_state.objectives
                        else: #insert new record  
                            evo_process = models.EvoProcess(quiz_id=quiz_id,
                                            start_timestamp = datetime.now(),
                                            status = EVO_PROCESS_STATUS_ACTIVE,
                                            impl = evo_state.impl,
                                            impl_state = evo_state.impl_state,
                                            population = evo_state.population,
                                            objectives = evo_state.objectives)
                            models.DB.session.add(evo_process)            
                        evo_process.archive = [ models.EvoProcessArchive(genotype_id = a.genotype_id, 
                                                    genotype = a.genotype, objectives = a.objectives) 
                                                    for a in evo_state.archive ]
                    models.DB.session.commit()                
                    self.evo_states = {}
                    with self.dumped: #NOTE: potential palce for deadlocks - two locks are aquired
                        self.dumped.notify_all()
                if self.stopped:
                    return

    def to_store(self, evo_process):
        with self.ready_to_write:
            self.evo_states[evo_process.quiz_id] = evo_process
            self.ready_to_write.notify()

    def from_store(self, quiz_ids) -> 'dict[int, models.EvoProcess]':
        with APP.app_context():
            evo_processes = models.EvoProcess.query.where(models.EvoProcess.quiz_id.in_(quiz_ids), models.EvoProcess.status == EVO_PROCESS_STATUS_ACTIVE).all()
            evo_processes_map = {p.id:p for p in evo_processes}
            if len(evo_processes_map) > 0:
                evo_archives = models.EvoProcessArchive.query.where(models.EvoProcessArchive.id.in_(evo_processes_map.keys())).all()
                evo_archives_map = dict(groupby(evo_archives, key=lambda a: a.id))
                for p_id, p in evo_processes_map.items():
                    p.archive = evo_archives_map.get(p_id, [])
        return {p.quiz_id: p for p in evo_processes}
        
sql_evo_serializer = SqlEvoSerializer()

class EvolutionaryProcess(Thread, ABC): 

    def __init__(self, **kwargs):     
        Thread.__init__(self)      
        self.quiz_id: int = kwargs.get("quiz_id", -1)  #-1 - process is not associated to any quiz
        self.stopped: bool = False   
        self.population: 'list[int]' = kwargs.get("population", []) # int here is an index in archive (next field)
        self.objectives: 'list[int]' = kwargs.get("objectives", [])
        self.archive: DataFrame = kwargs.get("archive", DataFrame(columns=['g']))
        self.archive[["g"]] = self.archive[["g"]].astype(object)
        self.gen: int = kwargs.get("gen", 0)
        self.rnd = np.random.RandomState(kwargs.get("seed", None))
        self.seed = int(self.rnd.get_state()[1][0])

    def add_genotype_to_archive(self, genotype):
        genotype_obj = Genotype(genotype)
        ix = self.archive[self.archive['g'] == genotype_obj].index
        if len(ix) > 0:
            return int(ix[0]) #NOTE: by default DataFrame index is int64 which fails json serialization
        else:
            id = len(self.archive)
            self.archive.loc[id, 'g'] = genotype_obj
            return id

    def get_explored_search_space_size(self):
        return len(self.archive)

    @abstractmethod
    def get_search_space_size(self):
        pass

    def get_genotype(self, genotype_id): 
        return self.archive.loc[genotype_id, 'g'].g

    def get_population_genotypes(self):
        return [self.get_genotype(genotype_id) for genotype_id in self.population]

    @abstractmethod
    def get_population_distractors(self):
        pass 

    @abstractmethod
    def run(self):
        pass

    def start(self):
        APP.logger.info(f"[{self.__class__.__name__}] starting for quiz {self.quiz_id}")
        self.name = self.__class__.__name__
        self.daemon = True
        ''' not necessary, but make it obvoius that should be redefined in children '''
        Thread.start(self)  

    def stop(self):
        APP.logger.info(f"[{self.__class__.__name__}] stopping quiz {self.quiz_id} evo")
        with self.on_new_evaluation:
            self.stopped = True 
            self.on_new_evaluation.notify()

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

    def get_state(self):
        return { "pop_size": len(self.population), "gen": self.gen, "seed": self.seed }

class Serializable(ABC):

    def __init__(self, **kwargs) -> None:
        self.serializer: EvoSerializer = kwargs.get("serializer", do_not_serialize)

    def save(self, **evo_state):
        ''' returns dict which represents intenal state '''

        evo_process = models.EvoProcess(quiz_id = self.quiz_id,
                        start_timestamp = datetime.now(),
                        status = EVO_PROCESS_STATUS_ACTIVE,
                        impl = self.__class__.__name__,
                        impl_state = json.dumps(evo_state),
                        population = json.dumps(self.population),
                        objectives = json.dumps(self.objectives))

        evo_process.archive = [ models.EvoProcessArchive(genotype_id = genotype_id,
                                        genotype = json.dumps(r.g.g),
                                        objectives = json.dumps({c: r[c] for c in r[r.notnull()].index if c != "g" })) 
                                        for genotype_id, r in self.archive.iterrows() ]
                                
        self.serializer.to_store(evo_process)   

    def load(evo_process: models.EvoProcess, serializer: EvoSerializer = do_not_serialize) -> EvolutionaryProcess:
        try:
            plain_interactions = evo_process.archive
            plain_data = {i.genotype_id:{'g': Genotype(json.loads(i.genotype)),
                                    **{ int(id):obj for id, obj in json.loads(i.objectives).items()}} for i in plain_interactions}
            population = json.loads(evo_process.population)
            objectives = json.loads(evo_process.objectives)
            archive = DataFrame.from_dict(plain_data, orient='index', columns=["g", *objectives])
            gl = globals()
            impl_state = json.loads(evo_process.impl_state)
            evo = gl[evo_process.impl](serializer = serializer, quiz_id = evo_process.quiz_id, archive = archive, 
                    population = population, objectives = objectives, **impl_state)
            return evo
        except Exception as e: 
            APP.logger.error(f"[evo-load] cannot load process {evo_process}. {e}")
            return None

class InteractiveEvaluation(ABC):

    @abstractmethod
    def get_for_evaluation(self, evaluator_id: int) -> 'list[list[int]]':
        pass 

    @abstractmethod
    def set_evaluation(self, evaluation: Evaluation) -> None:
        pass   

class PHC(EvolutionaryProcess, InteractiveEvaluation, ABC):
    '''
    P-PHC major sceleton
    '''
    def __init__(self, **kwargs):        
        super().__init__(**kwargs)
        self.waiting_evaluations: 'list[Evaluation]' = []
        self.on_new_evaluation = Condition()
        self.pop_size: int = kwargs.get("pop_size", 10)
        self.coevaluation_groups: dict[int, CoevaluationGroup] = { int(id):CoevaluationGroup(g["inds"], g["objs"]) for id, g in kwargs.get("coevaluation_groups", {}).items()}
        self.evaluator_coevaluation_groups: dict[int, int] = { int(evaluator_id):group_id for evaluator_id, group_id in kwargs.get("evaluator_coevaluation_groups", {}).items() }            

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
        self.init_population() #these should be here - otherwise possible race condition - if we put it in run, student could request quiz before first generation initialization
        self.mutate_population()
        super().start() # start evo thread - check run method

    @abstractmethod
    def compare(self, eval_group_id: int, eval_group: CoevaluationGroup):        
        ''' Abstract method to compare results for coevaluation group '''
        pass 

    def run(self):
        '''Func that implemets evo loop'''
        with self.on_new_evaluation:
            while True: # evolution loop                      
                self.on_iteration_start()
                self.on_new_evaluation.wait_for(lambda: any(self.waiting_evaluations) or self.stopped)
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
                        self.compare(coevaluation_group_id, eval_group)
                except Exception as e: 
                    APP.logger.error(f"[{self.__class__.__name__}] error on evaluation of quiz {self.quiz_id}: {e}. Ignored: {self.waiting_evaluations}")
                self.waiting_evaluations = []
                gen_was_evaluated = len(self.coevaluation_groups) == 0 #group is treated as evaluated when removed  from this dict
                self.on_iteration_end()
                if gen_was_evaluated:                        
                    self.on_generation_end()
                    self.gen += 1 # going to next generation                    
                    self.mutate_population()              
                if self.stopped:
                    return #exit evolution 

    #NOTE: these are set of hooks for code to be inserted into evo loop
    def on_iteration_start(self):
        ''' Derived classes could add logic to be executed on eval iteration start boundary'''
        pass

    def on_iteration_end(self):
        ''' Derived classes could add logic to be executed on eval iteration start boundary'''
        pass

    def on_generation_end(self):
        ''' Derived classes could add logic to be executed on generation end boundary'''
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

class P_PHC(PHC, Serializable):
    def __init__(self, **kwargs):
        PHC.__init__(self, **kwargs)
        Serializable.__init__(self, **kwargs)
        self.pareto_n: int = kwargs.get("pareto_n", 2)
        self.child_n: int = kwargs.get("child_n", 1)
        self.gene_size: int = kwargs.get("gene_size", 3)
        self.distractors_per_question = kwargs.get("distractors_per_question", {})   

    def get_state(self):
        return { **super().get_state(),
                    "gene_size": self.gene_size, "pareto_n": self.pareto_n, "child_n": self.child_n }                        

    def init_distractor_pools(self):
        if self.quiz_id is None:
            APP.logger.warn("[default-p-phc] distractor pools were not initialized")
            return []
        with APP.app_context():
            q = models.Quiz.query.get_or_404(self.quiz_id)
            questions = q.quiz_questions
            question_ids = [ q.id for q in questions ]
            quiz_question_distractors = models.DB.session.query(models.quiz_questions_hub).where(models.quiz_questions_hub.c.quiz_question_id.in_(question_ids)).all()
            distractor_ids = [d.distractor_id for d in quiz_question_distractors]
            distractors = models.Distractor.query.where(models.Distractor.id.in_(distractor_ids)).with_entities(models.Distractor.id, models.Distractor.question_id)
            distractor_map = { q_id: [ d.id for d in ds ] for q_id, ds in groupby(distractors, key=lambda d: d.question_id) }
            return {q.id: distractor_map.get(q.id, []) for q in questions }

    def init_population(self):
        if len(self.distractors_per_question) == 0:
            self.distractors_per_question = self.init_distractor_pools()
        return super().init_population()

    def compare(self, eval_group_id: int, eval_group: CoevaluationGroup):  
        ''' Implements Pareto comparison '''      
        if len(eval_group.objs) >= self.pareto_n:
            genotype_evaluations = {genotype_id: evals 
                                    for genotype_id, evals in self.archive.loc[eval_group.inds, eval_group.objs].iterrows()}
            parent = eval_group.inds[0]
            parent_genotype_evaluation = genotype_evaluations[parent]
            # possible_winners = [ child for child in eval_group.inds[1:]
            #                         if (genotype_evaluations[child] == parent_genotype_evaluation).all() or not((genotype_evaluations[child] <= parent_genotype_evaluation).all()) ] #Pareto check

            possible_winners = [ child for child in eval_group.inds[1:]
                                    if not((genotype_evaluations[child] == parent_genotype_evaluation).all()) and (genotype_evaluations[child] >= parent_genotype_evaluation).all() ] #Pareto check

            # possible_winners = [ child for child in eval_group.inds[1:]
            #                         if (genotype_evaluations[child] >= parent_genotype_evaluation).all() ] #Pareto check
            
            # better_children = [ child for child in eval_group.inds[1:]
            #                         if not((genotype_evaluations[child] == parent_genotype_evaluation).all()) and (genotype_evaluations[child] >= parent_genotype_evaluation).all() ] #Pareto check
            # if any(better_children):
            #     for i, ind in enumerate(self.population):
            #         if ind == parent:
            #             self.population[i] = None
            # for child in possible_winners:
            #     self.population.append(child)

            if len(possible_winners) > 0:
                winner = int(self.rnd.choice(possible_winners)) #NOTE: we have this cast due to bugged behaviour of numpy - it returns winner of type np.int64, not int - fails on json step
                self.population[eval_group_id] = winner #winner takes place of a parent
            del self.coevaluation_groups[eval_group_id]

    def init(self):
        genotype = []
        for qid, distractors in self.distractors_per_question.items():
            d_set = set(distractors)
            group = []
            for _ in range(min(len(d_set), self.gene_size)):
                d = int(self.rnd.choice(list(d_set))) #NOTE: cast is important here - see comment above
                d_set.remove(d)
                group.append(d)
            genotype.append((qid, sorted(group)))
        ind = self.add_genotype_to_archive(genotype)
        return ind 

    def mutate(self, parent_id): 
        genotype = self.get_genotype(parent_id)        
        children = []
        for _ in range(self.child_n):
            tries = 10
            while tries > 0:
                child = []
                for qid, genes in genotype: #here we do not evolve qids yet
                    distractors = self.distractors_per_question.get(qid, [])
                    d_set = set(distractors)
                    group = []
                    for g in genes:
                        # possibilities = list(d_set - set([g]))
                        possibilities = list(d_set) #NOTE: prev line is mroe restrictive - tries to differ each gene
                        if len(possibilities) == 0:
                            d = g
                        else: 
                            d = int(self.rnd.choice(possibilities)) #NOTE: cast is important
                        d_set.remove(d)
                        group.append(d)
                    child.append((qid, sorted(group)))
                child_id = self.add_genotype_to_archive(child)
                if child_id != parent_id:
                    children.append(child_id)
                    break
                tries -= 1
        return children

    def select(self, evaluator_id):
        ''' Policy what evaluation group to prioritize 
            Random, rotate (round-robin), greedy 
        '''
        return int(self.rnd.choice(list(self.coevaluation_groups.keys())))

    def update_fitness(self, ind, eval):  
        cur_score = self.archive.loc[ind, eval.evaluator_id]
        cur_score = 0 if cur_score is None else cur_score
        ind_genotype = self.get_genotype(ind)
        for qid, genes in ind_genotype: #result - dict where for each question we provide some data                        
            if qid in eval.result:
                for deception in genes:
                    if deception == eval.result[qid]:
                        cur_score += 1
        self.archive.loc[ind, eval.evaluator_id] = cur_score

    def on_iteration_end(self):
        ''' For each iteraton preserves data into store '''
        # self.save(pop_size = self.pop_size, gen = self.gen,
        #             coevaluation_groups = {id: {"inds": g.inds, "objs": g.objs} for id, g in self.coevaluation_groups.items()}, 
        #             evaluator_coevaluation_groups = self.evaluator_coevaluation_groups,
        #             gene_size = self.gene_size, pareto_n = self.pareto_n, child_n = self.child_n)
        pass 

    def on_generation_end(self):
        ''' Updates distractor pools - available distractors for each questions '''
        # self.population = [int(i) for i in unique([p for p in self.population if p is not None])]
        self.save(pop_size = self.pop_size, gen = self.gen,
                    coevaluation_groups = {id: {"inds": g.inds, "objs": g.objs} for id, g in self.coevaluation_groups.items()}, 
                    evaluator_coevaluation_groups = self.evaluator_coevaluation_groups,
                    gene_size = self.gene_size, pareto_n = self.pareto_n, child_n = self.child_n, seed = self.seed)
        self.distractors_per_question = self.init_distractor_pools()

    def repr_adapter(self, ind_genotypes):
        return [ (qid, [int(d) for d in unique([d for _, d in ds])]) for qid, ds in groupby(((qid, d) for ind in ind_genotypes for (qid, ds) in ind for d in ds), key=lambda x: x[0])]
        # return [set(d for ds in q_ds for d in ds) for q_ds in zip(*ind_genotypes)]

    def get_population_distractors(self):
        population = self.get_population_genotypes()           
        return [d for genotype in population for (_, dids) in genotype for d in dids ]

    def get_search_space_size(self):
        return prod([ comb(len(dids), self.gene_size) for _, dids in self.distractors_per_question.items()])

#this is global state across all requests
#NOTE: no bound is given for this state - possibly limit number of elems and give HTTP 429 - too many requests
quiz_evo_processes = {}

def get_evo(quiz_id) -> EvolutionaryProcess: 
    return quiz_evo_processes.get(quiz_id, None)

def start_evo(*quiz_ids):
    evos = sql_evo_serializer.from_store(quiz_ids)
    for quiz_id in quiz_ids:  
        if quiz_id in quiz_evo_processes:
            APP.logger.info(f"Quiz {quiz_id} already has evo process")
            continue
        evo = None 
        if quiz_id in evos: 
            evo = Serializable.load(evos[quiz_id], sql_evo_serializer)
        elif evopie.config.distractor_selection_process is not None:
            g = globals()
            if evopie.config.distractor_selection_process in g: 
                evo = g[evopie.config.distractor_selection_process](serializer=sql_evo_serializer, quiz_id=quiz_id, **evopie.config.distractor_selecton_settings)            
        if evo is not None: 
            evo.start()
            quiz_evo_processes[quiz_id] = evo
    
def stop_evo(quiz_id):
    evo = get_evo(quiz_id)
    if evo is not None: 
        evo.stop()     
        del quiz_evo_processes[quiz_id]

def init_evo(): 
    ''' should be executed at system start to start quizes evo processes from db table '''    
    def target(): #NOTE: this should be done in separate thread because with APP.app_context will detouch any entities of current db session. Session is connected to running thread
        sql_evo_serializer.start()
        with APP.app_context():
            evo_quiz_ids_q = models.Quiz.query.where(models.Quiz.status == 'STEP1').with_entities(models.Quiz.id)
            evo_quiz_ids = [ q.id for q in evo_quiz_ids_q ]
        if len(evo_quiz_ids) == 0:
            APP.logger.info("[init_evo] no evo processes to start")
        start_evo(*evo_quiz_ids)        
    init_thread = Thread(target=target)
    init_thread.start()

        
APP.before_first_request(init_evo) # evo init process        