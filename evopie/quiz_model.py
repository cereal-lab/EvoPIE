''' general interface for background quiz models '''

from abc import ABC, abstractmethod
from dataclasses import dataclass
import enum
from typing import Any, Optional
from evopie import models
from pandas import DataFrame
from datetime import datetime
from evopie.utils import groupby

class QuizModelStatus(enum.Enum):
    ACTIVE = 'Active'
    STOPPED = 'Stopped'

class Archive():
    ''' stores interactions with quiz model '''
    @dataclass
    class Representation: #NOTE: we need this wrapper because pandas goes crazy if you provide to it just lists
        ''' Abstract representation from the archive '''
        g: Any
        def __repr__(self) -> str:
            return self.g.__repr__()

    def __init__(self, archive_entries: 'list[models.EvoProcessArchive]', objectives: 'list[int]') -> None:
        plain_data = {i.genotype_id:{'g': Archive.Representation(i.genotype),
                                **{ int(id):val for id, val in i.objectives.items()}} 
                                for i in archive_entries}
        self.archive = DataFrame.from_dict(plain_data, orient='index', columns=["g", *objectives])    
        self.archive[["g"]] = self.archive[["g"]].astype(object)   

    def add(self, genotype: Any) -> int:
        ''' The routing to register genotype in the archive. The genotype becomes int id at return '''
        genotype_obj = Archive.Representation(genotype)
        ix = self.archive[self.archive['g'] == genotype_obj].index
        if len(ix) > 0:
            return int(ix[0]) #NOTE: by default DataFrame index is int64 which fails json serialization
        else:
            id = len(self.archive)
            self.archive.loc[id, 'g'] = genotype_obj
            return id

    def add_objective(self, obj):
        self.archive[obj] = None

    def get(self, genotype_id: int) -> Any: 
        ''' Get genotype by its id '''
        return self.archive.loc[genotype_id, 'g'].g

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

    def __init__(self, quiz_id: int, process: models.EvoProcess, distractors_per_question: 'dict[int, list[int]]') -> None:
        self.process = process #NOTE: this object should exist during request time and saved in db in save - it tracks concurrent update attempts
        self.quiz_id = quiz_id
        self.archive = Archive(process.archive, process.objectives)
        self.population = process.population #active antries
        self.objectives = process.objectives #all interaction ids
        self.distractors_per_question = distractors_per_question

    def get_explored_search_space_size(self) -> int:
        ''' returns explored search space size '''
        return len(self.archive.archive)
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
    def save(self) -> None:
        ''' preserve state in persistent storage'''
        impl_state = self.get_internal_model().get("settings", {})
        self.process.impl = self.__class__.__name__
        self.process.impl_state = impl_state
        self.process.population = self.population
        self.process.objectives = self.objectives
        self.process.archive = [ models.EvoProcessArchive(genotype_id = genotype_id,
                                            genotype = r.g.g, objectives = {c: r[c] for c in r[r.notnull()].index if c != "g" })
                                            for genotype_id, r in self.archive.items() ]
        models.DB.session.commit()         
    def to_csv(self, file_name) -> None: 
        ''' save state to csv file '''
        self.archive.to_csv(file_name, self.population)
    def to_dataframe(self) -> Optional[DataFrame]: 
        return self.archive.archive    


class QuizModelBuilder():
    def __init__(self, **kwargs) -> None:
        pass
    def get_settings(self) -> 'dict':
        return {}
    def get_quiz_model_class(self):
        return None

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
        distractor_map = { q_id: [ d.id for d in ds ] for q_id, ds in groupby(distractors, key = lambda d: d.question_id) }
        return {q.id: distractor_map.get(q.id, []) for q in questions }

    def load_quiz_model(self, quiz_or_id, create_if_not_exist = False) -> Optional[QuizModel]:
        ''' Restores evo processes from db by quiz id '''
        quiz_model_class = self.get_quiz_model_class()
        if quiz_model_class is None:
            return None
        quiz = self.get_quiz(quiz_or_id)
        process = models.EvoProcess.query.where(models.EvoProcess.quiz_id == quiz.id, models.EvoProcess.status == QuizModelStatus.ACTIVE.value).one_or_none()
        if process is not None:
            distractors_per_question = self.get_distractor_pools(quiz)            
            quiz_model = quiz_model_class(quiz.id, process, distractors_per_question) 
        elif create_if_not_exist:
            quiz_model = self.create_quiz_model(quiz)
        else: 
            quiz_model = None
        return quiz_model        

    def create_quiz_model(self, quiz_or_id) -> Optional[QuizModel]:
        quiz_model_class = self.get_quiz_model_class()
        if quiz_model_class is None: 
            return None        
        quiz = self.get_quiz(quiz_or_id)
        process = models.EvoProcess(quiz_id = quiz.id,
                        start_timestamp = datetime.now(),
                        status = QuizModelStatus.ACTIVE.value,
                        impl = quiz_model_class.__name__, impl_state = {**self.get_settings()}, 
                        population = [], objectives = [], archive = [])
        models.DB.session.add(process)
        models.DB.session.commit()
        distractors_per_question = self.get_distractor_pools(quiz)
        quiz_model = quiz_model_class(quiz.id, process, distractors_per_question)
        return quiz_model

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

from evopie.pphc_quiz_model import PphcQuizModelBuilder
default_builder = PphcQuizModelBuilder 
default_builder_settings = {}
def set_default_builder(algo, settings = {}):
    global default_builder, default_builder_settings
    if algo is not None:
        *module, builder = algo.split('.')
        m = __import__(".".join(module), fromlist=[builder])
        default_builder = getattr(m, builder)
    else:
        default_builder = None
    default_builder_settings = settings

def get_quiz_builder() -> QuizModelBuilder:
    return (default_builder or QuizModelBuilder)(**default_builder_settings)