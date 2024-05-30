'''
Module were we put all research algo parameters.
For instructor parameters, check models.py and Quiz table
'''

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