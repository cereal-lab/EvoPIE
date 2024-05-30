from typing import Any
from datalayer import models
import numpy as np
from evopie.quiz_model import QuizModel
from pandas import DataFrame

class RandomQuizModel(QuizModel):
    ''' Implements dummy choice of quiz questions - random questions at start '''
    default_settings = { "n": 3 } #pick 3 random distractors

    def __init__(self, quiz_id: int, process: models.EvoProcess, distractors_per_question: 'dict[int, list[int]]'):
        super(RandomQuizModel, self).__init__(quiz_id, process, distractors_per_question)
        settings = {**RandomQuizModel.default_settings, **process.impl_state}
        self.n = settings.get("n", 3)
        self.seed = settings.get("seed", None)
        self.rnd = np.random.RandomState(self.seed)     
        self.quiz_model = settings.get("quiz_model", None)  
        self.interactions = settings.get("interactions", {})  
        if self.quiz_model is None:
            self.quiz_model = [ [qid, [int(d) for d in self.rnd.choice(ds, size = min(len(ds), self.n), replace = False)]] 
                                    for qid, ds in distractors_per_question.items() ]

    def get_explored_search_space_size(self):
        return 1

    def get_sampling_size(self):
        return self.n

    def get_model_state(self) -> Any: #depends on impl, returns population for Evo models
        return {'n':self.n, 'seed': self.seed, 'quiz_model': self.quiz_model}
        
    def prepare_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        return [(q, list(ds)) for [q, ds] in self.quiz_model]

    def evaluate_internal(self, evaluator_id: int, result: 'dict[int, int]'):
        self.interactions[str(evaluator_id)] = sum([1 if result.get(qid, -1) in genes else 0 for qid, genes in self.quiz_model ])

    def to_dataframe(self):
        return DataFrame(data = [{'g': self.quiz_model, **self.interactions}])

    def get_best_quiz(self):
        population = [self.quiz_model]
        distractors = [d for genotype in population for (_, dids) in genotype for d in dids ] 
        return distractors
