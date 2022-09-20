'''
Implementation of evolutionary processes 
Currently we only have PHC, PPHC here. 
The evolutionary process is a background process which runs in separate thread. 
Db operations of saving process state could be concurrent to instructor and students requests - this could be a potential problem for some db engines 
Note that evo processes are restored from db on first Flask request - check hook handler registration at the end of file 
'''
from math import comb, prod
import numpy as np
from threading import Thread, Condition
from typing import Any

from evopie import APP, serializer
from evopie.algo import InteractiveEvaluation, get_distractor_pools
from evopie.utils import groupby
from abc import ABC, abstractmethod
from dataclasses import dataclass
from numpy import unique

@dataclass 
class CoevaluationGroup:   
    ''' The group of genotypes and students which saw these genotypes in one quiz ''' 
    inds: 'list[int]'
    objs: 'list[int]'

class EvolutionaryProcess(Thread, InteractiveEvaluation, ABC): 
    ''' Base class for evolution process (but still of specific form)'''
    def __init__(self, **kwargs):     
        Thread.__init__(self)
        InteractiveEvaluation.__init__(self, **kwargs)    
        self.stopped: bool = False   
        self.population: 'list[int]' = kwargs.get("population", []) # int here is an index in archive of InteractiveEvaluation
        self.objectives: 'list[int]' = kwargs.get("objectives", [])

        self.gen: int = kwargs.get("gen", 0)
        self.rnd = np.random.RandomState(kwargs.get("seed", None))
        self.seed = int(self.rnd.get_state()[1][0])

    def get_all_quiz_representations(self):
        return [self.get_quiz_representation(genotype_id) for genotype_id in self.population]

    @abstractmethod
    def run(self):
        pass

    def start(self):
        ''' starts the evolution '''
        APP.logger.info(f"[{self.__class__.__name__}] starting for quiz {self.quiz_id}")
        self.name = self.__class__.__name__
        self.daemon = True
        ''' not necessary, but make it obvoius that should be redefined in children '''
        Thread.start(self)  

    def stop(self, await_stop = False):
        ''' Stop the evolution '''
        APP.logger.info(f"[{self.__class__.__name__}] stopping quiz {self.quiz_id} evo")
        with self.on_new_evaluation:
            self.stopped = True 
            self.on_new_evaluation.notify()
        if await_stop:
            self.join()

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

    def get_all_quiz_representation_ids(self):
        return self.population    

class PHC(EvolutionaryProcess, ABC):
    '''
    P-PHC major sceleton
    '''
    def __init__(self, **kwargs):        
        super().__init__(**kwargs)
        self.waiting_evaluations: 'list[tuple[int, Any]]' = []
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
                    for (student_id, answer) in self.waiting_evaluations:
                        if student_id not in self.evaluator_coevaluation_groups:
                            #NOTE: should not be here usually - but could be on system restart
                            APP.logger.warn(f"[p-phc] got evaluation for unexpected group: {student_id} {answer}. {self.evaluator_coevaluation_groups}")
                            continue
                        coevaluation_group_id = self.evaluator_coevaluation_groups[student_id]
                        eval_group = self.coevaluation_groups[coevaluation_group_id]
                        eval_group.objs.append(student_id)                        
                        for ind in eval_group.inds:
                            self.update_score(ind, student_id, answer)
                        del self.evaluator_coevaluation_groups[student_id]
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
            ind_genotypes = [ self.get_quiz_representation(ind) for ind in inds ]
            return self.repr_adapter(ind_genotypes)

    def set_evaluation(self, student_id: int, result: Any):
        ''' This is called by flask req-resp thread and put evaluation objection into queue 
            Actual processing is done in evo thread
        '''
        with self.on_new_evaluation:
            self.waiting_evaluations.append((student_id, result))
            self.on_new_evaluation.notify() 

class P_PHC(PHC):
    ''' Pareto parallel hill climber '''
    def __init__(self, **kwargs):
        PHC.__init__(self, **kwargs)        
        self.pareto_n: int = kwargs.get("pareto_n", 2)
        self.child_n: int = kwargs.get("child_n", 1)
        self.gene_size: int = kwargs.get("gene_size", 3)
        self.distractors_per_question = kwargs.get("distractors_per_question", {})   

    def get_state(self):
        ''' this state is saved into db '''
        return { "pop_size": len(self.population), "gen": self.gen, "seed": self.seed,
                    "gene_size": self.gene_size, "pareto_n": self.pareto_n, "child_n": self.child_n }

    def init_population(self):
        if len(self.distractors_per_question) == 0:
            self.distractors_per_question = get_distractor_pools(self.quiz_id)
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
        ''' initialization of one individual (uniquely in the population) '''
        genotype = []
        for qid, distractors in self.distractors_per_question.items():
            d_set = set(distractors)
            group = []
            for _ in range(min(len(d_set), self.gene_size)):
                d = int(self.rnd.choice(list(d_set))) #NOTE: cast is important here - see comment above
                d_set.remove(d)
                group.append(d)
            genotype.append((qid, sorted(group)))
        ind = self.add_interaction_to_archive(genotype)
        return ind 

    def mutate(self, parent_id): 
        ''' produce children of a parent'''
        genotype = self.get_quiz_representation(parent_id)        
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
                child_id = self.add_interaction_to_archive(child)
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

    def on_iteration_end(self):
        ''' For each iteraton preserves data into store '''
        # self.save(pop_size = self.pop_size, gen = self.gen,
        #             coevaluation_groups = {id: {"inds": g.inds, "objs": g.objs} for id, g in self.coevaluation_groups.items()}, 
        #             evaluator_coevaluation_groups = self.evaluator_coevaluation_groups,
        #             gene_size = self.gene_size, pareto_n = self.pareto_n, child_n = self.child_n,
        #             population = self.population, objectives = self.objectives, archive = self.archive)
        pass 

    def on_generation_end(self):
        ''' Updates distractor pools - available distractors for each questions '''
        # self.population = [int(i) for i in unique([p for p in self.population if p is not None])]
        quiz_process = self.to_quiz_process(pop_size = self.pop_size, gen = self.gen,
                    coevaluation_groups = {id: {"inds": g.inds, "objs": g.objs} for id, g in self.coevaluation_groups.items()}, 
                    evaluator_coevaluation_groups = self.evaluator_coevaluation_groups,
                    gene_size = self.gene_size, pareto_n = self.pareto_n, child_n = self.child_n, seed = self.seed,
                    population = self.population, objectives = self.objectives)
        serializer.sql.to_store(quiz_process)
        self.distractors_per_question = get_distractor_pools(self.quiz_id)

    def repr_adapter(self, ind_genotypes):
        return [ (qid, [int(d) for d in unique([d for _, d in ds])]) for qid, ds in groupby(((qid, d) for ind in ind_genotypes for (qid, ds) in ind for d in ds), key=lambda x: x[0])]
        # return [set(d for ds in q_ds for d in ds) for q_ds in zip(*ind_genotypes)]

    def get_search_space_size(self):
        return prod([ comb(len(dids), self.gene_size) for _, dids in self.distractors_per_question.items()])
