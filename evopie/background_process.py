from threading import Thread
from typing import Optional
from evopie import APP, models, serializer
import evopie
from evopie.algo import InteractiveEvaluation, RandomQuiz, load_from_quiz_process
from evopie.evo import P_PHC #import here all algos that could be build with start_quiz_process

#this is global state across all requests
#NOTE: no bound is given for this state - possibly limit number of elems and give HTTP 429 - too many requests
quiz_processes: 'dict[int, InteractiveEvaluation]' = {}

def get_quiz_process(quiz_id) -> Optional[InteractiveEvaluation]:
    return quiz_processes.get(quiz_id, None)

def start_quiz_process(*quiz_ids):
    ''' starts algo processes for quizzes. Considers first db state and then if necessary starts processes with default evopie.config. '''
    processes = serializer.sql.from_store(quiz_ids)
    for quiz_id in quiz_ids:  
        if quiz_id in quiz_processes:
            APP.logger.info(f"Quiz {quiz_id} already has quiz process")
            continue
        process = None 
        if quiz_id in processes: 
            process = load_from_quiz_process(processes[quiz_id])
        elif evopie.config.distractor_selection_process is not None:
            g = globals()
            if evopie.config.distractor_selection_process in g: 
                process = g[evopie.config.distractor_selection_process](quiz_id=quiz_id, **evopie.config.distractor_selecton_settings)            
        if process is not None: 
            process.start()
            quiz_processes[quiz_id] = process
    
def stop_quiz_process(quiz_id):
    process = get_quiz_process(quiz_id)
    if process is not None: 
        process.stop()     
        del quiz_processes[quiz_id]

def init_quiz_process(): 
    ''' should be executed at system start to start quiz processes from db table '''    
    def target(): #NOTE: this should be done in separate thread because with APP.app_context will detouch any entities of current db session. Session is connected to running thread
        serializer.sql.start()
        with APP.app_context():
            quiz_ids_q = models.Quiz.query.where(models.Quiz.status == 'STEP1').with_entities(models.Quiz.id)
            quiz_ids = [ q.id for q in quiz_ids_q ]
        if len(quiz_ids) == 0:
            APP.logger.info("[init_quiz_process] no quiz processes to start")
        start_quiz_process(*quiz_ids)        
    init_thread = Thread(target=target)
    init_thread.start()
        
APP.before_first_request(init_quiz_process) # init background quiz processes