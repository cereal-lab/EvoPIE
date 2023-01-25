''' implementation of pphc quiz model '''
from datetime import datetime
from math import comb, prod
import numpy as np
from typing import Any, Optional
from pandas import DataFrame  

from evopie import APP, models
from evopie.utils import groupby
from abc import ABC, abstractmethod
from dataclasses import dataclass
from numpy import unique
from quiz_model import QuizModel, QuizModelBuilder

EVO_PROCESS_STATUS_ACTIVE = 'Active'
EVO_PROCESS_STATUS_STOPPED = 'Stopped'

@dataclass 
class CoevaluationGroup:   
    ''' The group of genotypes and students which saw these genotypes in one quiz ''' 
    inds: 'list[int]'
    objs: 'list[int]'

class Archive():
    @dataclass
    class Genotype: #NOTE: we need this wrapper because pandas goes crazy if you provide to it just lists
        ''' Abstract genotype of any representation from the archive '''
        g: Any
        def __repr__(self) -> str:
            return self.g.__repr__()

    def __init__(self, archive_entries: 'list[models.EvoProcessArchive]', objectives: 'list[int]') -> None:
        plain_data = {i.genotype_id:{'g': Archive.Genotype(i.genotype),
                                **{ int(id):obj for id, obj in i.objectives.items()}} for i in archive_entries}
        self.archive = DataFrame.from_dict(plain_data, orient='index', columns=["g", *objectives])    
        self.archive[["g"]] = self.archive[["g"]].astype(object)     

    def add(archive: DataFrame, genotype: Any) -> int:
        ''' The routing to register genotype in the archive. The genotype becomes int id at return '''
        genotype_obj = Archive.Genotype(genotype)
        ix = archive[archive['g'] == genotype_obj].index
        if len(ix) > 0:
            return int(ix[0]) #NOTE: by default DataFrame index is int64 which fails json serialization
        else:
            id = len(archive)
            archive.loc[id, 'g'] = genotype_obj
            return id

    def add_objective(self, obj):
        self.archive[obj] = None

    def get(archive: DataFrame, genotype_id: int) -> Any: 
        ''' Get genotype by its id '''
        return archive.loc[genotype_id, 'g'].g

    def at(self, ids, objs):
        return self.archive.loc[ids, objs].iterrows()        

    def set_interraction(self, id, obj, score):
        self.archive.loc[id, obj] = score 

    def __contains__(self, item):
        return self.archive.__contains__(item)

    def items(self):
        return self.archive.iterrows()
    def to_csv(self, file_name, active: 'list[int]') -> None: 
        ''' save state to csv file '''        
        archive_clone = self.archive.copy()
        archive_clone["p"] = 0
        archive_clone["p"] = archive_clone["p"].astype(int)            
        for ind in active:
            archive_clone[ind, "p"] = 1        
        archive_clone.to_csv(file_name)

class PphcQuizModel(QuizModel): 
    ''' Base class for evolution process (but still of specific form)'''
    def __init__(self, quiz_id: int, process: models.EvoProcess, archive: Archive, distractors_per_question: 'dict[int, list[int]]'):
        self.quiz_id: int = quiz_id  #-1 - process is not associated to any quiz
        self.population: 'list[int]' = process.population # int here is an index in archive (next field)
        self.objectives: 'list[int]' = process.objectives
        self.archive = archive
        self.gen: int = process.impl_state.get("gen", 0)
        self.rnd = np.random.RandomState(process.impl_state.get("seed", None))
        self.seed = int(self.rnd.get_state()[1][0])
        self.pop_size: int = process.impl_state.get("pop_size", 1)
        self.pareto_n: int = process.impl_state.get("pareto_n", 2)
        self.child_n: int = process.impl_state.get("child_n", 1)
        self.gene_size: int = process.impl_state.get("gene_size", 3)        
        self.distractors_per_question = distractors_per_question
        self.coevaluation_groups: dict[int, CoevaluationGroup] = { int(id):CoevaluationGroup(g["inds"], g["objs"]) 
                                                                    for id, g in process.impl_state.get("coevaluation_groups", {}).items()}
        self.evaluator_coevaluation_groups: dict[int, int] = { int(evaluator_id):group_id 
                                                                    for evaluator_id, group_id in process.impl_state.get("evaluator_coevaluation_groups", {}).items() }        
        #add to population new inds till moment of pop_size
        #noop if already inited
        while len(self.population) < self.pop_size:
            self.population.append(self.init()) #init respresent initialization operator

        self.mutate_population() #add new coeval groups on new parents

    def mutate_population(self):
        self.coevaluation_groups = { **self.coevaluation_groups, 
                                    **{pid: CoevaluationGroup(inds=[parent, *self.mutate(parent)], objs = []) 
                                        for pid, parent in enumerate(self.population)
                                        if pid not in self.coevaluation_groups} }             

    def compare(self, eval_group_id: int, eval_group: CoevaluationGroup):  
        ''' Implements Pareto comparison '''      
        if len(eval_group.objs) >= self.pareto_n:
            genotype_evaluations = {genotype_id: evals 
                                    for genotype_id, evals in self.archive.at(eval_group.inds, eval_group.objs)}
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

    def update_fitness(self, ind: int, evaluator_id: int, result) -> None:  
        # cur_score = self.archive.loc[ind, evaluator_id]
        cur_score = 0 #if cur_score is None or math.isnan(cur_score) else cur_score
        ind_genotype = self.archive.get(ind)
        for qid, genes in ind_genotype: #result - dict where for each question we provide some data                        
            if qid in result:
                for deception in genes:
                    if deception == result[qid]:
                        cur_score += 1
        self.archive.set_interraction(ind, evaluator_id, cur_score)

    def evaluate(self, evaluator_id: int, result: Any) -> None:
        try:
            if evaluator_id not in self.evaluator_coevaluation_groups:
                #NOTE: should not be here usually - but could be on system restart
                APP.logger.warn(f"[{self.__class__.__name__}] Quiz {self.quiz_id} got evaluation for unexpected group: {evaluator_id}. {self.evaluator_coevaluation_groups}")
                return
            coevaluation_group_id = self.evaluator_coevaluation_groups[evaluator_id]
            eval_group = self.coevaluation_groups[coevaluation_group_id]
            eval_group.objs.append(evaluator_id)                        
            for ind in eval_group.inds:
                self.update_fitness(ind, evaluator_id, result)
            del self.evaluator_coevaluation_groups[evaluator_id]
            self.compare(coevaluation_group_id, eval_group)
        except Exception as e: 
            APP.logger.error(f"[{self.__class__.__name__}] error on evaluation of quiz {self.quiz_id}: {e}.")
        gen_was_evaluated = len(self.coevaluation_groups) == 0 #group is treated as evaluated when removed  from this dict                
        if gen_was_evaluated:
            self.gen += 1 # going to next generation                    
            self.mutate_population()   
        self.save()

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
        return int(self.rnd.choice(list(self.coevaluation_groups.keys())))

    def get_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        if evaluator_id not in self.archive:
            self.archive.add_objective(evaluator_id)
            self.objectives.append(evaluator_id)                
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
        self.save()        
        return question_distractors

    def get_internal_model(self):
        population = [self.archive.get(genotype_id) for genotype_id in self.population]
        distractors = [d for genotype in population for (_, dids) in genotype for d in dids ] 
        settings = { "pop_size": self.pop_size, "gen": self.gen, "seed": self.seed,
                    "gene_size": self.gene_size, "pareto_n": self.pareto_n, "child_n": self.child_n,
                    "coevaluation_groups":  {id: {"inds": g.inds, "objs": g.objs} for id, g in self.coevaluation_groups.items()},
                    "evaluator_coevaluation_groups": self.evaluator_coevaluation_groups}   
        return {"population": population, "distractors": distractors, "settings": settings}

    def save(self, status: Optional[EVO_PROCESS_STATUS_ACTIVE | EVO_PROCESS_STATUS_STOPPED] = None) -> None:
        ''' Serialize evo process state to database '''
        impl_state = self.get_internal_model().get("settings", {})
        evo_process = models.EvoProcess.query.where(models.EvoProcess.quiz_id == self.quiz_id, models.EvoProcess.status == EVO_PROCESS_STATUS_ACTIVE).one_or_none()
        if evo_process is None: 
            evo_process = models.EvoProcess(quiz_id = self.quiz_id,
                            start_timestamp = datetime.now(),
                            status = status or EVO_PROCESS_STATUS_ACTIVE,
                            impl = __name__,
                            impl_state = impl_state,
                            population = self.population,
                            objectives = self.objectives)

            evo_process.archive = [ models.EvoProcessArchive(genotype_id = genotype_id,
                                            genotype = r.g.g, objectives = {c: r[c] for c in r[r.notnull()].index if c != "g" })
                                            for genotype_id, r in self.archive.items() ]
            models.DB.session.add(evo_process)
        else:
            evo_process.impl = __name__
            evo_process.impl_state = impl_state
            if status is not None: 
                evo_process.status = status
            evo_process.population = self.population
            evo_process.objectives = self.objectives

        #NOTE: next comments left from prev implementation with threading
        # sleep(5) #This is for testing database is locked error - this could lock student write operations
        # https://docs.sqlalchemy.org/en/14/dialects/sqlite.html#database-locking-behavior-concurrency
        # https://stackoverflow.com/questions/13895176/sqlalchemy-and-sqlite-database-is-locked          
        # current solution is to increase timeout of file lock              
        models.DB.session.commit() 
    def finalize(self):
        self.save(EVO_PROCESS_STATUS_STOPPED)
    def to_csv(self, file_name) -> None: 
        ''' save state to csv file '''
        self.archive.to_csv(file_name, self.population)
    def to_dataframe(self) -> Optional[DataFrame]: 
        return self.archive.archive    

class PphcQuizModelBuilder(QuizModelBuilder):
    def __init__(self, **settings) -> None:
        default_settings = { "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}
        self.settings = {**default_settings, **settings}

    def get_quiz(self, quiz_or_id: 'models.Quiz | int') -> models.Quiz: 
        if type(quiz_or_id) == int:
            quiz_or_id = models.Quiz.query.get_or_404(quiz_or_id)
        return quiz_or_id

    def get_distractor_pools(self, quiz_or_id):
        quiz = self.get_quiz(quiz_or_id)        
        questions = quiz.quiz_questions
        question_ids = [ q.id for q in questions ]
        quiz_question_distractors = models.DB.session.query(models.quiz_questions_hub).where(models.quiz_questions_hub.c.quiz_question_id.in_(question_ids)).all()
        distractor_ids = [d.distractor_id for d in quiz_question_distractors]
        distractors = models.Distractor.query.where(models.Distractor.id.in_(distractor_ids)).with_entities(models.Distractor.id, models.Distractor.question_id)
        distractor_map = { q_id: [ d.id for d in ds ] for q_id, ds in groupby(distractors, key=lambda d: d.question_id) }
        return {q.id: distractor_map.get(q.id, []) for q in questions }

    def load_quiz_model(self, quiz_or_id, create_if_not_exist = False) -> Optional[QuizModel]:
        ''' Restores evo processes from db by quiz id '''
        quiz = self.get_quiz(quiz_or_id)
        if type(quiz_or_id) == int:
            quiz = models.Quiz.query.get_or_404(quiz_or_id)
        evo_process = models.EvoProcess.query.where(models.EvoProcess.quiz_id.in_(quiz.id), models.EvoProcess.status == EVO_PROCESS_STATUS_ACTIVE).one_or_none()
        if evo_process is not None:
            evo_archive = models.EvoProcessArchive.query.where(models.EvoProcessArchive.id.in_(evo_process.id)).all()
            # evo_archives_map = dict(groupby(evo_archives, key=lambda a: a.id))
            # for p_id, p in evo_processes_map.items():
            archive = Archive(evo_archive, evo_process.objectives)
            distractors_per_question = self.get_distractor_pools(quiz)
            quiz_model = PphcQuizModel(quiz.id, evo_process, archive, distractors_per_question) 
        elif create_if_not_exist:
            quiz_model = self.create_quiz_model(quiz)
        else: 
            quiz_model = None
        return quiz_model        

    def create_quiz_model(self, quiz_or_id) -> QuizModel:
        quiz = self.get_quiz(quiz_or_id)
        evo_process = models.EvoProcess(quiz_id = quiz.id,
                        start_timestamp = datetime.now(),
                        status = EVO_PROCESS_STATUS_ACTIVE,
                        impl = __name__, impl_state = {**self.settings}, population = [], objectives = [])
        distractors_per_question = self.get_distractor_pools(quiz)
        quiz_model = PphcQuizModel(quiz.id, evo_process, Archive([]), distractors_per_question)
        quiz_model.save()
        return quiz_model

    def finalize_quiz_model(self, quiz_or_id: 'models.Quiz | int') -> None:    
        quiz_model = self.load_quiz_model(quiz_or_id)
        if quiz_model:
            quiz_model.finalize()