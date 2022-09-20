''' module provides serializaton of algo state to db schema '''

from datetime import datetime
import sys
from threading import Condition, Thread
from typing import Iterable
from evopie import APP, models
from evopie.config import QUIZ_PROCESS_STATUS_ACTIVE

class Serializer:
    ''' Base class for ways of preserving quiz process state'''
    def to_store(self, process: models.QuizProcess) -> None:
        pass 
    def from_store(self, quiz_ids: Iterable[int]) -> 'list[models.QuizProcess]':
        ''' Loads quiz processes at once '''
        return {}

class SqlSerializer(Thread, Serializer):
    ''' Serializes into sql db schema. '''

    def __init__(self):
        super().__init__()
        self.daemon = True 
        self.states: 'dict[int, models.QuizProcess]' = {} #per each quiz separate process state
        self.ready_to_write = Condition()
        self.dumped = Condition()
        self.stopped = False

    def start(self):
        Thread.start(self)

    def stop(self):
        with self.ready_to_write:
            self.stopped = True 
            self.ready_to_write.notify()

    def wait_dump(self, timeout):
        with self.dumped:
            self.dumped.wait(timeout)

    def run(self):
        ''' The loop that waits for state from other threads and dumps it into db '''
        with self.ready_to_write:
            while True:            
                self.ready_to_write.wait_for(predicate=lambda: (len(self.states) > 0) or self.stopped)
                try:
                    with APP.app_context():            
                        processes = models.QuizProcess.query.where(models.QuizProcess.quiz_id.in_(self.states.keys()), models.QuizProcess.status == QUIZ_PROCESS_STATUS_ACTIVE).all()
                        processes_map = {p.quiz_id: p for p in processes}
                        for quiz_id, state in self.states.items():                    
                            if quiz_id in processes_map: #update with new parameters 
                                process = processes_map[quiz_id]
                                process.impl = state.impl
                                process.impl_state = state.impl_state
                            else: #insert new record  
                                process = models.QuizProcess(quiz_id=quiz_id,
                                                start_timestamp = datetime.now(),
                                                status = QUIZ_PROCESS_STATUS_ACTIVE,
                                                impl = state.impl,
                                                impl_state = state.impl_state)
                                models.DB.session.add(process)
                            process.interactions = [ models.QuizProcessInteractions(quiz_id = a.quiz_id, 
                                                        quiz = a.quiz, interactions = a.interactions) 
                                                        for a in state.interactions ]                                 
                        # sleep(5) #This is for testing database is locked error - this could lock student write operations
                        # https://docs.sqlalchemy.org/en/14/dialects/sqlite.html#database-locking-behavior-concurrency
                        # https://stackoverflow.com/questions/13895176/sqlalchemy-and-sqlite-database-is-locked          
                        # current solution is to increase timeout of file lock              
                        models.DB.session.commit()                
                    self.states = {}
                except Exception as e: 
                    sys.stderr.write(f"[SqlSerializer] error ignored: {e}")
                    self.states = {}
                with self.dumped: #NOTE: potential place for deadlocks - two locks are aquired
                    self.dumped.notify_all()                    
                if self.stopped:
                    return

    def to_store(self, process):
        ''' The method is classed by serializer clients. It puts the state into queue and notify bg process to start dumping'''
        with self.ready_to_write:
            self.states[process.quiz_id] = process
            self.ready_to_write.notify()

    def from_store(self, quiz_ids) -> 'dict[int, models.QuizProcess]':
        with APP.app_context():
            processes = models.QuizProcess.query.where(models.QuizProcess.quiz_id.in_(quiz_ids), models.QuizProcess.status == QUIZ_PROCESS_STATUS_ACTIVE).all()
        return {p.quiz_id: p for p in processes}

sql = SqlSerializer() #bg process to dump algo state into QuizProcess table
