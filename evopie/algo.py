''' Base for implementation of algorithms that generate quizzes  
    Evolution based algos are implemented in evo.py (PPHC)
'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import json
import sys
from threading import Condition, Thread
from typing import Any, Iterable, Optional

import numpy
from pandas import DataFrame

from evopie import APP, models, serializer
import evopie
from evopie.config import QUIZ_PROCESS_STATUS_ACTIVE
from evopie.utils import groupby

class InteractiveEvaluation(ABC):
    ''' interface to interact with quiz process'''

    @dataclass
    class Interaction: #NOTE: we need this wrapper because pandas goes crazy if we provide just list
        ''' Abstract interaction of any representation from the archive '''
        g: Any
        def __repr__(self) -> str:
            return self.g.__repr__()    

    def __init__(self, **kwargs) -> None:
        self.quiz_id: int = kwargs.get("quiz_id", -1)  #-1 - process is not associated with any quiz
        self.kwargs = kwargs
        #archive could be given as json dict - we convert it to DataDrame
        self.archive: DataFrame = kwargs.get("archive", DataFrame(columns=['g'])) #the archive of interactions
        self.archive[["g"]] = self.archive[["g"]].astype(object)
        # archive = kwargs.get("archive", DataFrame(columns=['g']))
        # if type(archive) != DataFrame:
        #     plain_data = {i["genotype_id"]:{'g': Interaction(json.loads(i["genotype"])),
        #                             **{ int(id):obj for id, obj in json.loads(i["objectives"]).items()}} for i in archive}
        #     archive = DataFrame.from_dict(plain_data, orient='index', columns=["g", *self.objectives])
        # self.archive: DataFrame = archive #the archive of interactions
        # self.archive[["g"]] = self.archive[["g"]].astype(object)

    def add_interaction_to_archive(self, interaction):
        ''' The routine to register an interaction in the archive. The interaction becomes an int id at return '''
        interaction_obj = InteractiveEvaluation.Interaction(interaction)
        ix = self.archive[self.archive['g'] == interaction_obj].index
        if len(ix) > 0:
            return int(ix[0]) #NOTE: by default DataFrame index is int64 which fails json serialization
        else:
            id = len(self.archive)
            self.archive.loc[id, 'g'] = interaction_obj
            return id

    def get_quiz_representation(self, quiz_id): 
        ''' Get genotype by its id '''
        return self.archive.loc[quiz_id, 'g'].g    

    def update_score(self, ind, student_id, answer):  
        cur_score = self.archive.loc[ind, student_id]
        cur_score = 0 if cur_score is None else cur_score
        ind_genotype = self.get_quiz_representation(ind)
        for qid, qds in ind_genotype: #result - dict where for each question we provide some data                        
            if qid in answer:
                for did in qds:
                    if did == answer[qid]:
                        cur_score += 1
        self.archive.loc[ind, student_id] = cur_score        

    @abstractmethod
    def get_all_quiz_representations(self):
        pass    

    @abstractmethod
    def get_all_quiz_representation_ids(self):
        pass        

    def get_all_distractors(self):
        representations = self.get_all_quiz_representations()           
        return [d for r in representations for (_, dids) in r for d in dids ]        

    def get_explored_search_space_size(self):
        return len(self.archive)

    @abstractmethod
    def get_search_space_size(self):
        pass        

    def start(self):
        pass

    @abstractmethod
    def get_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        pass 

    @abstractmethod
    def set_evaluation(self, student_id: int, result: Any) -> None:
        pass

    def stop(self, await_stop = False):
        pass

    def get_state(self) -> dict:
        return self.kwargs

    def to_quiz_process(self, **state) -> models.QuizProcess:
        ''' save quiz process state '''

        process = models.QuizProcess(quiz_id = self.quiz_id,
                        start_timestamp = datetime.now(),
                        status = QUIZ_PROCESS_STATUS_ACTIVE,
                        impl = self.__class__.__name__,
                        impl_state = state)

        process.interactions = [ models.QuizProcessInteractions(quiz_id = quiz_id,
                                        quiz = json.dumps(r.g.g),
                                        interactions = {c: r[c] for c in r[r.notnull()].index if c != "g" })
                                        for quiz_id, r in self.archive.iterrows() ]        
                                     
        return process 

def load_from_quiz_process(quiz_process: models.QuizProcess) -> Optional[InteractiveEvaluation]:
    ''' loads config from db and create and instance of the class registered in config'''
    try:
        gl = globals()
        process_class = gl[quiz_process.impl]
        if issubclass(process_class, InteractiveEvaluation):
            plain_interactions = quiz_process.interactions
            plain_data = {i.quiz_id:{'g': InteractiveEvaluation.Interaction(json.loads(i.quiz)),
                                    **{ int(id):obj for id, obj in i.interactions.items()}} for i in plain_interactions}
            archive = DataFrame.from_dict(plain_data, orient='index')

            new_process_instance = process_class(quiz_id = quiz_process.quiz_id, 
                                                    archive = archive, **quiz_process.impl_state)
            return new_process_instance
        else:
            APP.logger.error(f"[quiz-process-load] target class {process_class} is not a subclass of {InteractiveEvaluation}")    
            return None
    except Exception as e: 
        APP.logger.error(f"[quiz-process-load] cannot load process {quiz_process}. {e}")
        return None

def get_distractor_pools(quiz_id):
    ''' util method to fetch all possible distractors for each question - this is our search space '''
    if quiz_id is None:
        APP.logger.error("[get_distractor_pools] quiz id was not provided")
        return []
    with APP.app_context():
        q = models.Quiz.query.get_or_404(quiz_id)
        questions = q.quiz_questions
        question_ids = [ q.id for q in questions ]
        quiz_question_distractors = models.DB.session.query(models.quiz_questions_hub).where(models.quiz_questions_hub.c.quiz_question_id.in_(question_ids)).all()
        distractor_ids = [d.distractor_id for d in quiz_question_distractors]
        distractors = models.Distractor.query.where(models.Distractor.id.in_(distractor_ids)).with_entities(models.Distractor.id, models.Distractor.question_id)
        distractor_map = { q_id: [ d.id for d in ds ] for q_id, ds in groupby(distractors, key=lambda d: d.question_id) }
        return {q.id: distractor_map.get(q.id, []) for q in questions }            

class RandomQuiz(InteractiveEvaluation):
    ''' Implements dummy choice of quiz questions - random questions at start '''

    def __init__(self, **kwargs) -> None:
        InteractiveEvaluation.__init__(self, **kwargs)
        self.rnd = numpy.random.RandomState(kwargs["seed"]) if "seed" in kwargs else numpy.random
        self.n = kwargs.get("n", 3)
        self.quiz = kwargs.get("quiz", None)
        self.ind = -1

    def start(self):
        if self.quiz is None:
            pools = get_distractor_pools(self.quiz_id)
            self.quiz = [ [qid, [int(d) for d in self.rnd.choice(ds, size = min(len(ds), self.n), replace = False)]] for qid, ds in pools.items() ]
        self.ind = self.add_interaction_to_archive(self.quiz)
        pass

    def get_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        self.archive[evaluator_id] = None
        return [(q, list(ds)) for [q, ds] in self.quiz]

    def set_evaluation(self, student_id: int, result: Any) -> None:
        self.update_score(self.ind, student_id, result)
        quiz_process = self.to_quiz_process(quiz_id = self.quiz_id, quiz = self.quiz, n = self.n, seed = self.kwargs["seed"])        
        serializer.sql.to_store(quiz_process)

    def get_search_space_size(self):        
        return 1         

    def get_all_quiz_representations(self):
        return [ self.get_for_evaluation(0) ]   

    def get_all_quiz_representation_ids(self):
        return [ self.ind ]
