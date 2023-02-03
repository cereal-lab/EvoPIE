''' implementation of pphc quiz model '''
from datetime import datetime
from math import comb, prod
import numpy as np
from typing import Any, Optional
from pandas import DataFrame  

from evopie import APP, models
from evopie.utils import groupby
from dataclasses import dataclass
from numpy import unique
from evopie.quiz_model import QuizModel, QuizModelBuilder, GeneBasedUpdateMixin

@dataclass 
class CoevaluationGroup:   
    ''' The group of genotypes and students which saw these genotypes in one quiz ''' 
    inds: 'list[int]'
    objs: 'list[int]'
    ppos: int

class PphcQuizModel(QuizModel, GeneBasedUpdateMixin): 
    ''' Base class for evolution process (but still of specific form)'''
    def __init__(self, quiz_id: int, process: models.EvoProcess, distractors_per_question: 'dict[int, list[int]]'):
        super(PphcQuizModel, self).__init__(quiz_id, process, distractors_per_question)
        self.gen: int = process.impl_state.get("gen", 0)
        self.rnd = np.random.RandomState(process.impl_state.get("seed", None))
        self.seed = int(self.rnd.get_state()[1][0])
        self.pop_size: int = process.impl_state.get("pop_size", 1)
        self.pareto_n: int = process.impl_state.get("pareto_n", 2)
        self.child_n: int = process.impl_state.get("child_n", 1)
        self.gene_size: int = process.impl_state.get("gene_size", 3)                
        self.coevaluation_groups: dict[str, CoevaluationGroup] = { cgid:CoevaluationGroup(g["inds"], g["objs"], g['ppos']) 
                                                                    for cgid, g in process.impl_state.get("coevaluation_groups", {}).items()}
        self.evaluator_coevaluation_groups: dict[int, str] = { int(evaluator_id):str(group_id)
                                                                    for evaluator_id, group_id in process.impl_state.get("evaluator_coevaluation_groups", {}).items() }        
        #add to population new inds till moment of pop_size
        #noop if already inited
        while len(self.population) < self.pop_size:
            self.population.append(self.init()) #init respresent initialization operator

        self.mutate_population() #add new coeval groups on new parents

    def mutate_population(self):
        for pid, parent in enumerate(self.population):
            coeval_group_id = f"{self.gen}:{pid}"
            if coeval_group_id not in self.coevaluation_groups:
                self.coevaluation_groups[coeval_group_id] = CoevaluationGroup(inds=[parent, *self.mutate(parent)], objs = [], ppos=pid)

    def compare(self, coeval_group_id: str, coeval_group: CoevaluationGroup):  
        ''' Implements Pareto comparison '''      
        if len(coeval_group.objs) >= self.pareto_n:
            genotype_evaluations = {genotype_id: evals for genotype_id, evals in self.archive.at(coeval_group.inds, coeval_group.objs)}
            parent = coeval_group.inds[0]
            parent_genotype_evaluation = genotype_evaluations[parent]
            # possible_winners = [ child for child in eval_group.inds[1:]
            #                         if (genotype_evaluations[child] == parent_genotype_evaluation).all() or not((genotype_evaluations[child] <= parent_genotype_evaluation).all()) ] #Pareto check

            def child_is_better(parent_genotype_evaluation, child_genotype_evaluation):
                child_domination = child_genotype_evaluation >= parent_genotype_evaluation
                parent_domination = child_genotype_evaluation <= parent_genotype_evaluation
                if (parent_genotype_evaluation == child_genotype_evaluation).all(): #Pareto check
                    #non-domination and same outcome for given students
                    #prefer child for diversity - other statistics is necessary 
                    return True 
                elif child_domination.all():
                    return True 
                elif parent_domination.all():
                    return False 
                else: #non-pareto-comparable
                    #NOTE: if we use aggregation here - it will be same to non-Pareto comparison
                    return True #pick child
                    # child_sum = (child_genotype_evaluation.sum(), child_domination.sum())
                    # parent_sum = (parent_genotype_evaluation.sum(), parent_domination.sum())
                    # if child_sum == parent_sum: 
                    #     #prefer child for diversity but better to check other stats
                    #     return True 
                    # elif child_sum > parent_sum:
                    #     return True 
                    # else: #child_sum < parent_sum 
                    #     return False                                 
            possible_winners = [ child for child in coeval_group.inds[1:]
                                    if child_is_better(parent_genotype_evaluation, genotype_evaluations[child]) ]

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
                self.population[coeval_group.ppos] = winner #winner takes place of a parent
            del self.coevaluation_groups[coeval_group_id]
            #we cleanup also evaluator_coevaluation_groups which denies postponed evaluations
            #NOTE: comment next if you allow evaluation from another group (from prev generation)
            evaluators = list(self.evaluator_coevaluation_groups.items())
            for (sid, cgid) in evaluators: #TODO: store student ids in coeval_group for faster cleanup
                if cgid == coeval_group_id:
                    APP.logger.warn(f"Cannot accept evaluation of student {sid}, because coeval group {cgid} is evolving to next generation based on result from {coeval_group}")
                    del self.evaluator_coevaluation_groups[sid]

    def evaluate_internal(self, evaluator_id: int, result: Any) -> None:
        coevaluation_group_id = self.evaluator_coevaluation_groups.get(evaluator_id, None)
        eval_group = self.coevaluation_groups.get(coevaluation_group_id, None)        
        if coevaluation_group_id is None or eval_group is None:
            #NOTE: coeval group was removed by evolution
            APP.logger.warn(f"Discarding evaluation of {evaluator_id} for quiz {self.quiz_id}. Population is {self.population}. Result {result}")
            return
        eval_group.objs.append(evaluator_id)   
        for ind in eval_group.inds:
            self.update_fitness(ind, evaluator_id, result)
        del self.evaluator_coevaluation_groups[evaluator_id]
        self.compare(coevaluation_group_id, eval_group)
        gen_was_evaluated = len(self.coevaluation_groups) == 0 #group is treated as evaluated when removed  from this dict                
        if gen_was_evaluated:
            self.gen += 1 # going to next generation                    
            self.mutate_population()

    def init(self):
        ''' initialization of one individual (uniquely in the population) '''
        genotype = []
        for qid, distractors in self.distractors_per_question.items():
            d_set = set(distractors)
            group = []
            for _ in range(min(len(d_set), self.gene_size)):
                d = int(self.rnd.choice(list(d_set))) #NOTE: cast is important here - without it could fail on json servialization of np type
                d_set.remove(d)
                group.append(d)
            genotype.append((qid, sorted(group)))
        ind = self.archive.add(genotype)
        return ind 

    def mutate(self, parent_id): 
        ''' produce children of a parent'''
        genotype = self.archive.get(parent_id)        
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
                child_id = self.archive.add(child)
                if child_id != parent_id:
                    children.append(child_id)
                    break
                tries -= 1
        return children

    def get_search_space_size(self):
        return prod([ comb(len(dids), self.gene_size) for _, dids in self.distractors_per_question.items()])

    def select(self, evaluator_id):
        ''' Policy what evaluation group to prioritize 
            Random, rotate (round-robin), greedy '''
        return str(self.rnd.choice(list(self.coevaluation_groups.keys())))

    def prepare_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        if evaluator_id in self.evaluator_coevaluation_groups: #student should solve quiz with same set of distractors on retake it could be regenerated
            coevaluation_group_id = self.evaluator_coevaluation_groups[evaluator_id]
        else:
            coevaluation_group_id = self.select(evaluator_id)
            self.evaluator_coevaluation_groups[evaluator_id] = coevaluation_group_id
        inds = self.coevaluation_groups[coevaluation_group_id].inds #select group from one parent            
        ind_genotypes = [ self.archive.get(ind) for ind in inds ]
        question_distractors = [ (qid, [int(d) for d in unique([d for _, d in ds])]) 
                                    for qid, ds in groupby(((qid, d) 
                                    for ind in ind_genotypes 
                                    for (qid, ds) in ind for d in ds), key=lambda x: x[0])]
        return question_distractors

    def get_internal_model(self):
        population = [self.archive.get(genotype_id) for genotype_id in self.population]
        distractors = [d for genotype in population for (_, dids) in genotype for d in dids ] 
        settings = { "pop_size": self.pop_size, "gen": self.gen, "seed": self.seed,
                    "gene_size": self.gene_size, "pareto_n": self.pareto_n, "child_n": self.child_n,
                    "coevaluation_groups":  {id: {"inds": g.inds, "objs": g.objs, "ppos": g.ppos} for id, g in self.coevaluation_groups.items()},
                    "evaluator_coevaluation_groups": self.evaluator_coevaluation_groups}   
        return {"population": population, "distractors": distractors, "settings": settings}

class PphcQuizModelBuilder(QuizModelBuilder):
    def __init__(self, **kwargs) -> None:
        self.default_settings = { "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}
        self.settings = {**self.default_settings, **kwargs}
    def get_settings(self):
        return self.settings
    def get_quiz_model_class(self):
        return PphcQuizModel