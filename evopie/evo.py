'''
Implementation of evolutionary processes 
'''
import random
from threading import Thread, Condition
from pandas import DataFrame       
from dataclasses import dataclass, Any

# def get_submatrix(f: DataFrame):
#     ''' Searches for biggest full submatrix in given sparse dataframe'''
#     filtered = f.loc[f.notnull().any(axis=1)] #returns view 

@dataclass
class EvolutionState: 
    name: str 
    thread: Thread 
    interactions: DataFrame
    gen: int
    get_for_evaluation: Any
    set_evaluation: Any

def p_phc(pop_size, pareto_n, init, mutate, select, update_ind_score, ind_id = str):
    '''
    P-PHC major sceleton
    '''
    state = EvolutionState(gen=0, interactions = DataFrame())
    waiting_evaluations = []
    on_new_evaluation = Condition()
    def get_for_evaluation(student_id):
        # with on_new_evaluation: #takes lock of cv in order to protect interactions
        if student_id not in state.interactions:
            state.interactions[f'S_{student_id}'] = None #new student
        population = state.interactions[state.interactions['l_gen'] == state.gen]
        ind = select(student_id, population)
        #ind is representative 
        ind_id = ind.index[0]
        p_id = ind.loc[ind_id, "p"]
        inds = population[population['p'] == p_id] #select group from one parent
        return list(zip(inds['ind'])) #returns for each qeuestions set of distractors

    state.get_for_evaluation = get_for_evaluation

    def set_evaluation(evaluation):
        ''' This is called by flask req-resp thread and put evaluation objection into queue 
            Actual processing is done in evo thread
        '''
        with on_new_evaluation:
            waiting_evaluations.append(evaluation)
            on_new_evaluation.notify()

    state.set_evaluation = set_evaluation

    #population initialization
    def init_population():
        while len(state.interactions) < pop_size:
            ind = init(state.interactions)
            cs_id = ind_id(ind)
            if cs_id not in state.interactions.index:
                state.interactions.loc[cs_id] = {'ind':ind, 'f_gen': state.gen, 'l_gen': state.gen, 'p': cs_id, 'stud': []} 

    init_population()

    def mutate_population():
        population = state.interactions.loc[state.interactions['l_gen'] == state.gen]
        for p_id, p in population['ind'].items():
            children = mutate(p)
            for child in children:
                c_id = ind_id(child)
                if c_id not in state.interactions.index:
                    state.interactions.loc[c_id] = {'ind':child, 'f_gen': state.gen, 'l_gen': state.gen, 'p': p_id, 'stud': []} 
                else:
                    state.interactions.loc[c_id, ['l_gen', 'p', 'stud']] = (state.gen, p_id, [])

    mutate_population()

    def evo_run(): 
        '''Func that implemets evo loop'''
        while True: 
            #generating children from parent
            while True: #loop which processes evaluations - awaits them 
                with on_new_evaluation:
                    on_new_evaluation.wait_for(lambda: any(waiting_evaluations))
                    population = state.interactions.loc[state.interactions['l_gen'] == state.gen]
                    for eval in waiting_evaluations:
                        student_id = eval.student_id
                        p_id = eval.p_id #parent identifies group of coevolved distractors 
                        eval_group = population[state.interactions['p'] == p_id]
                        for cs_id, ind in eval_group['ind'].items():
                            for gene, genes_coeval in zip(ind, eval.result):
                                state.interactions.loc[cs_id, f'S_{student_id}'] = update_ind_score(state.interactions.loc[cs_id, f'S_{student_id}'], gene, genes_coeval)
                        state.interactions.loc[state.interactions['p'] == p_id, 'stud'].append(f'S_{student_id}')
                    waiting_evaluations = []
                    gen_was_evaluated = population[state.interactions['stud'].apply(len) == pareto_n].all()
                    if gen_was_evaluated:
                        # Pareto domiation increases l_gen for winners 
                        for eval_group in population.groupby('p'):
                            p_id, parent = list(eval_group[eval_group.index == eval_group['p']].iterrows())[0]
                            students = parent['stud'] #students by which we compare
                            possible_winners = [ ch_id for ch_id, child in eval_group.iterrows() 
                                if ch_id != p_id and child[students] >= parent[students] ] #Pareto check
                            group_winner = random.choice(possible_winners)
                            state.interactions.loc[group_winner, 'l_gen'] += 1                            
                        state.gen += 1 # going to next generation
                        break
            mutate_population()

    # def serialize(): 
        
    evo = Thread(target=evo_run)
    evo.daemon = True 
    evo.start()
    state.thread = evo 
    state.name = p_phc.__name__
    return state


def random_group_init(distractors_per_question, group_size = 3):
    '''
        initialization for schema [d1d3d4, d7d10d12, ...]
    '''
    def init(interactions):
        ind = []
        for distractors in distractors_per_question:
            d_set = set(distractors)
            group = []
            for _ in range(min(len(d_set), group_size)):
                d = random.choice(d_set)
                d_set.remove(d)
                group.append(d)
            ind.append(group)
        return ind 
    return init

def random_group_mutate(distractors_per_question, prob = 0.25): 
    def mutate(ind): 
        child = [ [ random.choice(ds) if len(ds) > 0 and random.random() < prob else gene 
                        for gene in genes 
                        for ds in [ set(distractors) - set([gene]) ] ]            
                    for genes, distractors in zip(ind, distractors_per_question) ]
        return child
    return mutate

def random_group_select():
    def select(student_id, population):
        return population.sample()        
    return select 

def simple_update_ind_score(cur_score, gene, genes_score):
    scored_genes = set(genes_score.genes)
    for g in gene:
        if g in scored_genes:
            cur_score += 1
    return cur_score