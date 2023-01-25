''' general interface for background quiz models '''

from abc import ABC, abstractmethod
from typing import Any, Optional
from evopie import models
import pandas as pd

class QuizModel(ABC):
    def get_explored_search_space_size(self) -> int:
        ''' returns explored search space size '''
        return 0
    def get_search_space_size(self) -> int:
        ''' returns number of possible combinations on inner model state '''
        return 0
    def get_internal_model(self) -> Any: #depends on impl, returns population for Evo models
        ''' returns anything related to state of quiz model '''
        return None
    def get_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        ''' return list of distractors for each question in the quiz '''
        return []
    def evaluate(self, evaluator_id: int, result: Any) -> None:
        ''' stores results in model state '''
        pass
    def save(self) -> None:
        ''' preserve state in persistent storage'''
        pass
    def finalize(self) -> None:
        ''' Any action that should be done to close the quiz '''
        pass 
    def to_csv(self, file_name) -> None: 
        ''' save state to csv file '''
        pass
    def to_dataframe(self) -> Optional[pd.DataFrame]: 
        return None

class QuizModelBuilder(ABC):
    @abstractmethod
    def create_quiz_model(self, quiz_or_id: 'models.Quiz | int') -> QuizModel:
        pass 
    def load_quiz_model(self, quiz_or_id: 'models.Quiz | int', create_if_not_exist = False) -> Optional[QuizModel]:    
        return self.create_quiz_model(quiz_or_id)
    def finalize_quiz_model(self, quiz_or_id: 'models.Quiz | int') -> None:    
        pass

def get_quiz_builder(**settings) -> QuizModelBuilder:
    from pphc_quiz_model import PphcQuizModelBuilder
    return PphcQuizModelBuilder(**settings)