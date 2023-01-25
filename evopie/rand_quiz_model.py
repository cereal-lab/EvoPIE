from math import comb, prod
from typing import Any, Optional
from quiz_model import QuizModel, QuizModelBuilder, Archive, GeneBasedUpdateMixin
import numpy
from evopie import models
import numpy as np

class RandomQuizModel(QuizModel, GeneBasedUpdateMixin):
    ''' Implements dummy choice of quiz questions - random questions at start '''

    def __init__(self, quiz_id: int, archive: Archive, process: models.EvoProcess, distractors_per_question: 'dict[int, list[int]]'):
        super(RandomQuizModel, self).__init__(quiz_id, archive, process, distractors_per_question)
        self.n = process.impl_state.get("n", 3)
        self.rnd = np.random.RandomState(process.impl_state.get("seed", None))
        self.seed = int(self.rnd.get_state()[1][0])
        if len(self.population) > 0:
            self.quiz_model = self.archive.get(self.population[0])
        else:
            self.quiz_model = [ [qid, [int(d) for d in self.rnd.choice(ds, size = min(len(ds), self.n), replace = False)]] 
                                    for qid, ds in distractors_per_question.items() ]
            self.population = [self.archive.add(self.quiz_model)]

    def get_search_space_size(self) -> int:
        return prod([ comb(len(dids), self.n) for _, dids in self.distractors_per_question.items()])  
        
    def get_internal_model(self) -> Any: #depends on impl, returns population for Evo models
        return {'n':self.n, 'seed': self.rnd.get_state()[1][0]}
        
    def prepare_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        return [(q, list(ds)) for [q, ds] in self.quiz_model]

    def evaluate_internal(self, evaluator_id: int, result: Any) -> None:
        ''' stores results in model state '''
        self.update_fitness(evaluator_id, result)

class RandomQuizModelBuilder(QuizModelBuilder):
    def get_default_settings():
        return { "n": 3 }
    def get_quiz_model_class():
        return RandomQuizModel        