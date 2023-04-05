''' general interface for background quiz models '''

from abc import ABC, abstractmethod
from dataclasses import dataclass
import enum
from math import comb, prod
from typing import Any, Optional
from evopie import models
from pandas import DataFrame
from datetime import datetime
from evopie.utils import groupby

class QuizModelStatus(enum.Enum):
    ACTIVE = 'Active'
    STOPPED = 'Stopped'

class QuizModel(ABC):

    def __init__(self, quiz_id: int, process: models.EvoProcess, distractors_per_question: 'dict[int, list[int]]') -> None:
        self.process = process #NOTE: this object should exist during request time and saved in db in save - it tracks concurrent update attempts
        self.quiz_id = quiz_id
        self.distractors_per_question = distractors_per_question

    def get_explored_search_space_size(self) -> int:
        ''' should return explored search space size '''
        return 0

    def get_sampling_size(self):
        return 1 

    def get_search_space_size(self) -> int:
        return prod([ comb(len(dids), self.get_sampling_size()) for _, dids in self.distractors_per_question.items()])  

    def get_model_state(self) -> Any:
        ''' returns anything related to state of quiz model '''
        return {}

    @abstractmethod
    def prepare_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        return []
    def get_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        ''' return list of distractors for each question in the quiz '''
        res = self.prepare_for_evaluation(evaluator_id)
        self.save()
        return res
    @abstractmethod
    def evaluate_internal(self, evaluator_id: int, result: 'dict[int, int]') -> None:
        pass
    def evaluate(self, evaluator_id: int, result: 'dict[int, int]') -> None:
        ''' stores results in model state '''        
        self.evaluate_internal(evaluator_id, result)
        self.save()
    def save(self) -> None:
        ''' preserve state in persistent storage'''
        impl_state = self.get_model_state()
        self.process.impl = self.__class__ .__module__ + '.' + self.__class__.__name__
        self.process.impl_state = impl_state
        models.DB.session.commit()         
    def to_dataframe(self) -> Optional[DataFrame]: 
        return None
    def to_csv(self, file_name) -> None: 
        ''' save state to csv file '''
        df = self.to_dataframe()
        if df is not None:
            df.to_csv(file_name)
    def get_best_quiz(self):
        ''' Should return known best quiz distractors '''
        return []

from evopie.sampling_quiz_model import SamplingQuizModel
class QuizModelBuilder():
    default_quiz_model_class = SamplingQuizModel
    default_settings = {}

    def get_quiz(self, quiz_or_id: 'models.Quiz | int') -> models.Quiz: 
        if type(quiz_or_id) == int:
            quiz_or_id = models.Quiz.query.get_or_404(quiz_or_id)
        return quiz_or_id

    def get_distractor_pools(self, quiz_or_id):
        quiz = self.get_quiz(quiz_or_id)        
        questions = quiz.quiz_questions
        question_ids = [ q.id for q in questions ] #note: question_id?
        quiz_question_distractors = models.DB.session.query(models.quiz_questions_hub).where(models.quiz_questions_hub.c.quiz_question_id.in_(question_ids)).all()
        distractor_ids = [d.distractor_id for d in quiz_question_distractors]
        distractors = models.Distractor.query.where(models.Distractor.id.in_(distractor_ids)).with_entities(models.Distractor.id, models.Distractor.question_id)
        distractor_map = { q_id: [ d.id for d in ds ] for q_id, ds in groupby(distractors, key = lambda d: d.question_id) }
        return {q.id: distractor_map.get(q.question_id, []) for q in questions }

    def parse_model_class(self, algo):
        ''' Parse module.class to class function constructor'''
        if algo is not None:
            *module, builder = algo.split('.')
            m = __import__(".".join(module), fromlist=[builder])
            quiz_model_class = getattr(m, builder)
        else:
            quiz_model_class = None
        return quiz_model_class

    def load_quiz_model(self, quiz_or_id, create_if_not_exist = False) -> Optional[QuizModel]:
        ''' Restores evo processes from db by quiz id '''
        quiz = self.get_quiz(quiz_or_id)
        process = models.EvoProcess.query.where(models.EvoProcess.quiz_id == quiz.id, models.EvoProcess.status == QuizModelStatus.ACTIVE.value).one_or_none()
        if process is not None:
            distractors_per_question = self.get_distractor_pools(quiz)            
            quiz_model_class = self.parse_model_class(process.impl)
            quiz_model = quiz_model_class(quiz.id, process, distractors_per_question) 
        elif create_if_not_exist:
            quiz_model = self.create_quiz_model(quiz)
        else: 
            quiz_model = None
        return quiz_model        

    def create_quiz_model(self, quiz_or_id) -> Optional[QuizModel]:
        if QuizModelBuilder.default_quiz_model_class is None: 
            return None    
        elif type(QuizModelBuilder.default_quiz_model_class) == str:    
            quiz_model_class = self.parse_model_class(QuizModelBuilder.default_quiz_model_class)
        else:
            quiz_model_class = QuizModelBuilder.default_quiz_model_class
        quiz = self.get_quiz(quiz_or_id)
        process = models.EvoProcess(quiz_id = quiz.id,
                        start_timestamp = datetime.now(),
                        status = QuizModelStatus.ACTIVE.value,
                        impl = quiz_model_class.__module__ + '.' + quiz_model_class.__name__, 
                        impl_state = {**QuizModelBuilder.default_settings})
        models.DB.session.add(process)
        models.DB.session.commit()
        distractors_per_question = self.get_distractor_pools(quiz)
        quiz_model = quiz_model_class(quiz.id, process, distractors_per_question)
        return quiz_model

def get_quiz_builder():
    return QuizModelBuilder()

def set_quiz_model(quiz_model_class, settings = {}):
    ''' NOTE: this is state - used only in cli experiments '''
    QuizModelBuilder.default_quiz_model_class = quiz_model_class
    QuizModelBuilder.default_settings = settings