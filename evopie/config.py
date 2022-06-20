'''
Module were we put all research algo parameters.
For instructor parameters, check models.py and Quiz table
'''

#quiz attempt states 
QUIZ_HIDDEN = "HIDDEN"
QUIZ_ATTEMPT_STEP1 = QUIZ_STEP1 = "STEP1" #when student attempt on STEP1 - it means that student is going to take step1 
QUIZ_ATTEMPT_STEP2 = QUIZ_STEP2 = "STEP2" #when student attempt on STEP2 - student finished step1 and ready to take step2
QUIZ_ATTEMPT_SOLUTIONS = QUIZ_SOLUTIONS = "SOLUTIONS" #when student attempt on SOLUTIONS - student finished step1 and step2 and ready to see solutions

attempt_next_steps = {QUIZ_ATTEMPT_STEP1: QUIZ_ATTEMPT_STEP2, QUIZ_ATTEMPT_STEP2: QUIZ_ATTEMPT_SOLUTIONS}

def get_attempt_next_step(cur_step):
    return attempt_next_steps.get(cur_step, cur_step)

#system roles

ROLE_STUDENT = "STUDENT"
ROLE_INSTRUCTOR = "INSTRUCTOR"
ROLE_ADMIN = "ADMIN"
# ROLE_RESEARCHER = "RESEARCHER"

EVO_PROCESS_STATUS_ACTIVE = 'Active'
EVO_PROCESS_STATUS_STOPPED = 'Stopped'
p_phc_settings = { "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3, "mut_prob": 0.25}
#p_phc_settings = { "pop_size": 3, "pareto_n": 2, "child_n": 2, "gene_size": 1, "mut_prob": 1}

# distractor_selection_process, distractor_selecton_settings = (None, {}) #NOTE: use this for default behavior without evo process
distractor_selection_process, distractor_selecton_settings = ("P_PHC", p_phc_settings)

#-------------------------------------------------------
#-- Justification selection parameteres

#tournament params
k_tournament_percent = 10
k_tournament_min = 1
k_tournament_max = 7

def get_k_tournament_size(population): 
    sz = round(len(population) * k_tournament_percent / 100)
    return min(max(k_tournament_min, sz), k_tournament_max)

#slots params 
least_seen_percent = 60
def get_least_seen_slots_num(num_slots):
    sz = round(num_slots * least_seen_percent / 100)
    return max(1, sz)                