''' general interface for background quiz models '''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from evopie import models
from pandas import DataFrame
from datetime import datetime
from itertools import groupby

EVO_PROCESS_STATUS_ACTIVE = 'Active'
EVO_PROCESS_STATUS_STOPPED = 'Stopped'

class Archive():
    ''' stores interactions with quiz model '''
    @dataclass
    class Representation: #NOTE: we need this wrapper because pandas goes crazy if you provide to it just lists
        ''' Abstract representation from the archive '''
        g: Any
        def __repr__(self) -> str:
            return self.g.__repr__()

    def __init__(self, archive_entries: 'list[tuple[int, Any, Any]]', objectives: 'list[int]') -> None:
        plain_data = {rid:{'g': Archive.Representation(representation),
                                **{ int(id):val for id, val in interactions.items()}} 
                                for (rid, representation, interactions) in archive_entries}
        self.archive = DataFrame.from_dict(plain_data, orient='index', columns=["g", *objectives])    
        self.archive[["g"]] = self.archive[["g"]].astype(object)     

    def add(archive: DataFrame, genotype: Any) -> int:
        ''' The routing to register genotype in the archive. The genotype becomes int id at return '''
        genotype_obj = Archive.Representation(genotype)
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

class QuizModel(ABC):

    def __init__(self, quiz_id: int, archive: Archive, process: models.EvoProcess, distractors_per_question: 'dict[int, list[int]]') -> None:
        self.quiz_id = quiz_id
        self.archive = archive
        self.population = process.population #active antries
        self.objectives = process.objectives #all interaction ids
        self.distractors_per_question = distractors_per_question

    def get_explored_search_space_size(self) -> int:
        ''' returns explored search space size '''
        return len(self.archive)
    def get_search_space_size(self) -> int:
        ''' returns number of possible combinations on inner model state '''
        return 0
    def get_internal_model(self) -> Any: #depends on impl, returns population for Evo models
        ''' returns anything related to state of quiz model '''
        return None
    @abstractmethod
    def prepare_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        return []
    def get_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        ''' return list of distractors for each question in the quiz '''
        if evaluator_id not in self.archive:
            self.archive.add_objective(evaluator_id)
            self.objectives.append(evaluator_id)
        res = self.prepare_for_evaluation(evaluator_id)
        self.save()
        return res
    @abstractmethod
    def evaluate_internal(self, evaluator_id: int, result: Any) -> None:
        pass
    def evaluate(self, evaluator_id: int, result: Any) -> None:
        ''' stores results in model state '''        
        self.evaluate_internal(evaluator_id, result)
        self.save()
    def save(self, status: Optional[EVO_PROCESS_STATUS_ACTIVE | EVO_PROCESS_STATUS_STOPPED] = None) -> None:
        ''' preserve state in persistent storage'''
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
    def to_csv(self, file_name) -> None: 
        ''' save state to csv file '''
        self.archive.to_csv(file_name, self.population)
    def to_dataframe(self) -> Optional[DataFrame]: 
        return self.archive.archive    


class QuizModelBuilder(ABC):
    @abstractmethod
    def get_default_settings() -> 'dict':
        return {}
    @abstractmethod
    def get_quiz_model_class():
        return QuizModel

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
        distractor_map = { q_id: [ d.id for d in ds ] for q_id, ds in groupby(sorted(distractors, key = lambda d: d.question_id), key=lambda d: d.question_id) }
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
            archive = Archive([(i.genotype_id, i.genotype, i.objectives) for i in evo_archive], evo_process.objectives)
            distractors_per_question = self.get_distractor_pools(quiz)
            quiz_model = self.get_quiz_model_class()(quiz.id, archive, evo_process, distractors_per_question) 
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
                        impl = __name__, impl_state = {**self.get_default_settings()}, population = [], objectives = [])
        distractors_per_question = self.get_distractor_pools(quiz)
        quiz_model = self.get_quiz_model_class()(quiz.id, Archive([],evo_process.objectives), evo_process, distractors_per_question)
        quiz_model.save()
        return quiz_model

    def finalize_quiz_model(self, quiz_or_id: 'models.Quiz | int') -> None:    
        quiz_model = self.load_quiz_model(quiz_or_id)
        if quiz_model:
            quiz_model.save(EVO_PROCESS_STATUS_STOPPED)

class GeneBasedUpdateMixin():
    def update_fitness(self: QuizModel, ind: int, evaluator_id: int, result) -> None:  
        # cur_score = self.archive.loc[ind, evaluator_id]
        cur_score = 0 #if cur_score is None or math.isnan(cur_score) else cur_score
        ind_genotype = self.archive.get(ind)
        for qid, genes in ind_genotype: #result - dict where for each question we provide some data                        
            if qid in result:
                for deception in genes:
                    if deception == result[qid]:
                        cur_score += 1
        self.archive.set_interraction(ind, evaluator_id, cur_score)

def get_quiz_builder() -> QuizModelBuilder:
    from pphc_quiz_model import PphcQuizModelBuilder
    return PphcQuizModelBuilder()