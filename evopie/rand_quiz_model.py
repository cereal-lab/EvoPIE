from math import comb, prod
from typing import Any
from evopie import models
import numpy as np
from evopie.quiz_model import QuizModel, GeneBasedUpdateMixin

class RandomQuizModel(QuizModel, GeneBasedUpdateMixin):
    ''' Implements dummy choice of quiz questions - random questions at start '''
    default_settings = { "n": 3 }

    def __init__(self, quiz_id: int, process: models.EvoProcess, distractors_per_question: 'dict[int, list[int]]'):
        super(RandomQuizModel, self).__init__(quiz_id, process, distractors_per_question)
        settings = {**RandomQuizModel.default_settings, **process.impl_state}
        self.n = settings.get("n", 3)
        self.seed = settings.get("seed", None)
        self.rnd = np.random.RandomState(self.seed)        
        if len(self.population) > 0:
            self.quiz_model = self.archive.get(self.population[0])
        else:
            self.quiz_model = [ [qid, [int(d) for d in self.rnd.choice(ds, size = min(len(ds), self.n), replace = False)]] 
                                    for qid, ds in distractors_per_question.items() ]
            self.population = [self.archive.add(self.quiz_model)]

    def get_search_space_size(self) -> int:
        return prod([ comb(len(dids), self.n) for _, dids in self.distractors_per_question.items()])  
        
    def get_internal_model(self) -> Any: #depends on impl, returns population for Evo models
        population = [self.archive.get(genotype_id) for genotype_id in self.population]
        distractors = [d for genotype in population for (_, dids) in genotype for d in dids ] 
        return {"settings": {'n':self.n, 'seed': self.seed}, "population": population, "distractors": distractors}
        
    def prepare_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        return [(q, list(ds)) for [q, ds] in self.quiz_model]

    def evaluate_internal(self, evaluator_id: int, result: Any) -> None:
        ''' stores results in model state '''
        self.update_fitness(self.population[0], evaluator_id, result)