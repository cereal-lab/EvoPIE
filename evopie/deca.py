''' Module to work with DECA  '''

from dataclasses import dataclass
import json
import numpy as np
import numpy.typing as npt
# from pandas import DataFrame, MultiIndex
from evopie.utils import groupby

#NOTE: problem how we correspond sets of students to structure of the quiz. 
#DECA test - quiz, question, distractor?

#If DECA test is distractor 
#  1. Distractor id === id of the point in the space and we can save distractors to student_knowledge accordingly 
#  2. DECA will say what distractors are most informative - we will have this ids after we exec synth_deca_coords
#  3. We expect PPHC to find these distractr ids in last generation (use these metrics)
     # how many axes we cover, how far distractor on the axis?

#If DECA test is question 
#  1. Interaction 1 value means student failed to select correct option for the question among alternatives
#  2. Degree of freedom is the alternatives selection 
# ... 

#MEMO on DECA, types of points in dimension space:  
# 1. Points on axis -> Zero == {} --> { 1 }  /// --> { 1, 2 } --> { 1, 2, 3 } - axis 1 
# 2. Points on different axis -> {} --> { 2 }
# 3. Points outside axis (spanned test) --> {} --> ({1}, {2})

# @dataclass
# class DECA_axis_pos: 
#     axis_id: int 
#     point_id: int 

# class DECA_point:
#     # pos: 'tuple[DECA_axis_pos]' = () #for axis point it is only one element. For spanned 2 and more 
#     unique_candidates: 'list[int]' = [] #candidates unique to this point
#     candidates: 'list[int]' = [] #failed students 
#     unique_distractors: 'list[int]' = [] #distractors unique for this axis point - does not make sense for spanned and therefore [] for them
#     distractors: 'list[int]' = [] #assigned to point distractors 
#     questions: 'list[int]' = [] #assigned set of quiz questions to this point 

# def process_axes(axes):
#     ''' returns CF sets from simple representations '''
#     res = []
#     for axis in axes: 
#         axis_res = []
#         res.append(axis_res)
#         axis_candidates = axis[0]
#         axis_res.append(axis_candidates)
#         for point in axis[1:]: 
#             axis_candidates = [*axis_candidates, *point]
#             axis_res.append(axis_candidates)
#     return res 

# def process_spanned(processed_axes, spanned):
#     ''' Spanned should be indexes in axes '''
#     res = [[axis[i] for i, axis in zip(point, processed_axes)] for point in spanned ]
#     return res

# def flatten_spanned(processed_spanned):
#     return [tuple(sorted([i for s in sets for i in s])) for sets in processed_spanned]

def gen_deca_space(candidates: npt.ArrayLike, dims: 'list[int]', num_spanned: int, best_candidates_percent: float = 0, p=0.75, timeout = 1000000, rnd: np.random.RandomState = np.random): 
    assert len(dims) > 0
    assert len(candidates) >= len(dims) #number of dimansions could not be bigger than number of candidates
    assert all(dim > 0 for dim in dims)    
    
    # index = MultiIndex.from_tuples([(axis_id, point_id) for axis_id, num_points in enumerate(dims) for point_id in range(num_points)], names=['axis_id', 'point_id'])
    # axes = DataFrame(index=index,columns=['ucfs', 'cfs', 'udids', 'dids', 'qids'])
    space = {'dims': dims, 'axes': {}, 'spanned': {}, 'zero': {}} #zero includes perfect students and noninformative distractors
    rnd.shuffle(candidates)
    skip_to_index = int(len(candidates) * best_candidates_percent)
    space['zero']['cfs'] = candidates[0:skip_to_index]
    candidates = candidates[skip_to_index:]
    total_points_num = np.sum(dims) - 1
    # s1 | s2 | s3  s4 s5 | ... ... sn
    candidate_split_indexes = np.sort(np.concatenate([[0], rnd.choice(len(candidates) - 1, size=total_points_num, replace=False) + 1, [len(candidates)]]))
    candidate_slices = np.lib.stride_tricks.sliding_window_view(candidate_split_indexes, 2) #slices     
    all_points = [candidates[slice[0]:slice[1]] for slice in candidate_slices]
    # print(f"Splits of points {candidate_slices}.\nCandidates: {candidates}.\nPoints: {all_points}")
    # space['zero']['cfs'] = all_points.pop(0) #ignore candidates outside space
    axes_split_ends = np.cumsum(dims)
    axes_splits = zip(axes_split_ends - dims, axes_split_ends)
    for axis_id, split in enumerate(axes_splits):
        for point_id, candidates in enumerate(all_points[split[0]:split[1]]):
            space['axes'].setdefault(axis_id, {}).setdefault(point_id, {})['ucfs'] = candidates
    # we calculated unique candidates for each point, now we calculate CF sets 
    for axis_id, points in space['axes'].items(): 
        axis_candidates = []
        for point_id, point in points.items():
            axis_candidates = [*axis_candidates, *point['ucfs']]
            point['cfs'] = axis_candidates
    # now we calculate spanned 
    if len(dims) >= 2: 
        #spanned point should have at least 2 axes combined        
        axes_ids = list(range(len(dims)))
        while len(space['spanned']) < num_spanned and timeout > 0: #repeat loop till we find necessary number of spanned or timeout
            # rnd.binomial
            spanned_axes_num = 2 if len(dims) == 2 else (2 + ((rnd.geometric(p) - 1) % (len(dims) - 1)))
            # spanned_axes_num = rnd.randint(2, len(axes)+1) #select number of axes
            selected_axes_ids = rnd.choice(axes_ids, spanned_axes_num, replace=False) 
            # spanned_coords = [0 for _ in range(len(axes))]
            spanned_point = tuple(sorted([ (int(axis_id), int(rnd.randint(0, dims[axis_id]))) for axis_id in selected_axes_ids ]))
            space['spanned'].setdefault(spanned_point, {})['cfs'] = [c for (axis_id, point_id) in spanned_point for c in space['axes'][axis_id][point_id]['cfs']]
            timeout -= 1
    return space

# axes = gen_deca_space(list(range(20)), [2,3], 2, 0.5)

# def synth_deca_spanned(axes, num_spanned, p=0.75, timeout = 1000000, rnd: np.random.RandomState = np.random):    
#     ''' Returns list of spanned points where one point is presented as tuple (one element per axis). 
#         0 as element of tuple means that axis is not used for spanned point (origin in DECA is assiciated with empty set).
#         n as element at ith position in the tuple means that spanned uses n-1 point on ith axis of space.
#         Example: [(0,1,0,3)] - one spanned point which is defined by axis 1 and axis 3. Axis 1 contributes first point (axes[1][0]) while axis 3 - third point (axes[3][2])
#         To form set of students tricked by spanned point - take only coords of spanned point > 0 and union all sets that correspond to axis points (axis 1 and axis 3 in the example)
#     '''
#     if len(axes) < 2: 
#         return [] #spanned point should have at least 2 axes combined
#     spanned = set()
#     axes_ids = list(range(len(axes)))
#     while len(spanned) < num_spanned and timeout > 0: #repeat loop till we find necessary number of spanned or timeout
#         # rnd.binomial
#         spanned_axes_num = 2 if len(axes) == 2 else (2 + ((rnd.geometric(p) - 1) % (len(axes) - 1)))
#         # spanned_axes_num = rnd.randint(2, len(axes)+1) #select number of axes
#         selected_axes_ids = rnd.choice(axes_ids, spanned_axes_num, replace=False) 
#         # spanned_coords = [0 for _ in range(len(axes))]
#         spanned_point = tuple([ (axes_id, rnd.randint(0, len(axes[axes_id]))) for axes_id in selected_axes_ids ])
#         spanned.add(spanned_point)
#         timeout -= 1
#     return [list(p) for p in spanned]

# OLD complex code
#Considerations about relationship between distructors and selected candidates:
# s1: q1: -1 2* 3 4 q2: -1 5 6 7* --> 1
# s2: q1: -1 2 3* 4 q2: -1 5 6 7* --> 2
# a1: [[6, 10, 1], [6, 10, 1, 8, 9]],  a2: [[2, 3], [2, 3, 4, 7], [2, 3, 4, 7, 5]]
# 1. Distractors for same question (2 3 4) could not trick same student at once. So student with id x could be in CF set of only one of them
#    But tests on one axis share candidates in their CF sets. Therefore distractors of one question could only be placed on different axis
# 2. Distractors for different questions (say 2, 7) could fail same students and be placed on same axis. 
#   More: one test could correspond to two different distractors 
# 3. Some distractors could be absent in deca space - they do not trick any students.  
# 4. Conclusion Axes are treated as independent distractors. If test is present in deca space - at least one distractor should exist with specified behavior
# 5. Num of questions for axes should be at least max(dims) because each point on axis correspond to different question's distractor
# 6. Spanned point contains in its CF-sets students from all dimensions - this point could not belong to quesion to which axis points belong
# def gen_test_distractor_mapping(space, rnd: np.random.RandomState = np.random): #NOTE: no spanned for now
#     ''' Generates mapping of distractor id to corresponding position in the DECA space for DECA axes only (no spanned)
#         Returns list of questions where one element is list of positions in deca space for question distractors 
#         Main assumption: two distractors of same question could not be on same axis. Check comments for details.
#     '''
#     num_questions = np.max([len(axis) for axis in axes]) #We deduce number of quiz question by max points on dimension (with psanned picture changes)
#     #we would like to have minimal number of quesions from axes 
#     #num of distractors on one question: 
#     #   1. > len(axes) - some distractors do not trick students at all - easy distractors - not represented on axes (non-informative distractors)
#     #   2. == len(axes) - each distractor of question is informative - they are independent
#     #   3. < len(axes) - other questions provide new insights - questions are independent 
#     # we always could generate some number of noniformative distractors for each questions - therefore this routine works only with informative distractors 
#     # We also ignore non-informative (trivial) questions here. They also could be added
#     # So number of informative distractors per question should be from [1, len(axes)].
#     questions = [[] for _ in range(num_questions)]
#     possible_question = [qid for qid in range(num_questions)]    
#     for axis_id, axis in enumerate(axes):
#         rnd.shuffle(possible_question)
#         total_points_num = len(axis)
#         candidates = possible_question
#         # point_questions = [[question] for question in candidates[:total_points_num]]
#         # For one axis we spread questions around points on it like next (qX - question, pX - point on axis):
#         # | q3 q4 -> p1 at axis | q5 -> p2 at axis | q6 q7 | ... qn
#         # | q1 | q2 | q3 
#         # Some questions could be skipped - see below pop(0)
#         candidate_split_indexes = np.sort(np.concatenate([[0], rnd.choice(len(candidates), size=total_points_num, replace=False), [len(candidates)]]))
#         candidate_slices = np.lib.stride_tricks.sliding_window_view(candidate_split_indexes, 2) #slices     
#         point_questions = [candidates[slice[0]:slice[1]] for slice in candidate_slices]
#         # print(f"Splits of points {candidate_slices}.\nAxis: {axis}\nCandidates: {candidates}.\nQuestions: {point_questions}")
#         # print(f"Axis: {axis}\nCandidates: {candidates}.\nQuestions: {point_questions}")
#         point_questions.pop(0) #first slice is dedicated to ignored questions for this axis
#         for point_id, qids in enumerate(point_questions):
#             for qid in qids:
#                 questions[qid].append({"axis":(axis_id, point_id)})


#     # We follow same assumption: distractors of same question could not be presented by same axis
#     # For spanned it means that its questions could be questions that are already on spanned axes or axes of other spanned points 
#     # We allocate new questions if we cannot find any question that satisfy this condition 
#     # test_distractor_mapping_spanned = [] #contains list of {"qid":0, "spanned":(0,1,0,3)} where qid is id from test_distractor_mapping and spanned - coord    
#     for s in spanned: #s is tuple with positions on axes, 0 means axis is not used 
#         question_ids = {i for i in range(len(questions))}
#         axes_questions = {axis_id: set([q for _, q in qids]) 
#                             for axis_id, qids in groupby(((axis_id, qid) 
#                                                             for qid, q in enumerate(questions) 
#                                                             for point in q
#                                                             for axis_id, _ in ([point["axis"]] if "axis" in point else point["spanned"])), key = lambda x: x[0]) }
#         axes_possible_questions = [possible_questions 
#                                     for axis_id, _ in s 
#                                     for possible_questions in [question_ids - axes_questions[axis_id]]]
#         possible_question_ids = list(set.intersection(*axes_possible_questions))

#         print(f"For {s} possible questions are {possible_question_ids}. Q:{question_ids} AQ:{axes_questions}\n")
        
#         point = {"spanned":s}
#         if len(possible_question_ids) > 0:
#             qid = rnd.choice(possible_question_ids)
#             questions[qid].append(point)
#         else:
#             questions.append([point])
#         # think of redoing this with random distractor assignment 

#     return questions

#in this implementation we assign random number of questions to each space point and then pick random number of distractors
#we use geometric distribution for number of elements picked for each deca point. 
def gen_test_distractor_mapping(space, question_distractors, constraint = lambda space: True, noninformative_percent: float = 0, timeout = 1000000, rnd: np.random.RandomState = np.random): #NOTE: no spanned for now
    ''' Same axis could contain same questions.
        @param: question_distractors should be list of tuples (qid, did)
    '''

    while timeout > 0: 
        candidates = [*question_distractors]
        rnd.shuffle(candidates)
        skip_to_index = int(noninformative_percent * len(candidates))
        space['zero']['dids'] = candidates[0:skip_to_index]
        candidates = candidates[skip_to_index:]
        space_points = [ *[point for _, points in space['axes'].items() for _, point in points.items()], *[point for _, point in space['spanned'].items()]]
        total_points_num = len(space_points) - 1
        # s1 | s2 | s3  s4 s5 | ... ... sn
        candidate_split_indexes = np.sort(np.concatenate([[0], rnd.choice(len(candidates) - 1, size=total_points_num, replace=False) + 1, [len(candidates)]]))
        candidate_slices = np.lib.stride_tricks.sliding_window_view(candidate_split_indexes, 2) #slices     
        all_point_distractors = [candidates[slice[0]:slice[1]] for slice in candidate_slices]
        for i, point in enumerate(space_points):
            point['dids'] = all_point_distractors[i]
        if constraint(space):
            break
        timeout -= 1
    return space

def unique_question_per_axis_constraint(space): 
    for axis_id, points in space['axes'].items():
        question_ids = [*[qid for _, point in points.items() for qid, _ in point['dids']], 
                        *[qid for spanned_id, point in space['spanned'].items() for s_axis_id, _ in spanned_id if axis_id == s_axis_id for qid, _ in point['dids'] ]] 
        if len(np.unique(question_ids)) != len(question_ids):
            return False 
    return True

# space = gen_test_distractor_mapping(axes, [ (q, d) for q in range(1) for d in range(10) ], noninformative_percent = 0.1)    
# space = gen_test_distractor_mapping(axes, [ (q, d) for q in range(20) for d in range(10) ], noninformative_percent = 0.1, constraint = unique_question_per_axis_constraint)    
# CONCLUSION: having constraint in gen_test_distractor_mapping is very ineffective - another way to generate axes should exist

# def gen_test_distractor_mapping_knowledge(axes, test_distractor_mapping, question_distractors): 
#     ''' Generates knowledge in format similar to cli student init -k flag. Use this to init StudentKnowledge database 
#         question_distractors specify possible distractors for each question - used to assign knowledge to specific distractors
#         It is list of {qid, dids} qid is used to assign question id to sequential test_distractor_mapping. dids are used with same purpose
#         question_distractors["dids"] is list of distractor ids. For informative duplicate, element of the list should be the list itself with dids
#         For example {"qid":3, "dids":[[11,12],13]} will correspond distractors 11,12 to same deca test in mapping
#     '''
#     knowledge = [ {"sid": [sid for axis_id, pos_id in ([pos["axis"]] if "axis" in pos else pos["spanned"]) for sid in axes[axis_id][pos_id]], 
#                     "qid": ids["qid"], "did": did, "chance": 1, "pos": pos} 
#                     for q, ids in zip(test_distractor_mapping, question_distractors) 
#                     for pos, did in zip(q, ids["dids"])]
#     return knowledge

def gen_test_distractor_mapping_knowledge(space): 
    ''' Generates knowledge in format similar to cli student init -k flag. Use this to init StudentKnowledge database 
    '''
    knowledge = [*[ {"sid": point['cfs'], "qid": qid, "did": did, "chance": 100 + int(point_id) } 
                    for _, points in space['axes'].items()
                    for point_id, point in points.items() 
                    for qid, did in point['dids']],
                 *[ {"sid": point['cfs'], "qid": qid, "did": did, "chance": 100 * len(axes_ids) + len(point['dids']) } 
                    for axes_ids, point in space['spanned'].items()
                    for qid, did in point['dids']]]
    return knowledge

#rnd = np.random.RandomState(17)
#axes = gen_deca_space([1,2,3,4,5,6,7,8,9,10], (2,2), 1, 0.3, rnd = rnd)
#space = gen_test_distractor_mapping(axes, [(2,5), (2,6), (2,7), (2,8), (4,13), (4,14), (5, 19), (5, 20)], rnd = rnd)
#kn = gen_test_distractor_mapping_knowledge(space)
#spanned = synth_deca_spanned(axes, 3, rnd = np.random.RandomState(17))

def dimension_coverage(space, population_distractors):
    ''' Computes DC metric based on DECA axes and given populaiton_distractors (ex., last population of P-PHC)
        populaiton_distractors should be flat list of distractors, present in population
    '''
    spanned_axes = {axis_id for spanned_id, point in space['spanned'].items() for _, did in point['dids'] if did in population_distractors for axis_id, _ in spanned_id}
    did_axes = {axis_id for axis_id, points in space["axes"].items() for point in points.values() for _, did in point["dids"] if did in population_distractors}    
    dim_coverage = len(did_axes) / len(space["axes"])
    # dim_coverage_with_spanned = len(did_axes.union(spanned_axes)) / len(space["axes"])
    return {"dim_coverage":dim_coverage} # "dim_coverage_with_spanned": dim_coverage_with_spanned}

# dimension_coverage(space, [5,6,14])

def avg_rank_of_repr(space, population_distractors):
    ''' Computes ARR '''
    spanned_ranks = {axis_id: max([r for _, r in ranks]) for axis_id, ranks in groupby([(axis_id, int(point_id) + 1) 
                                                                        for spanned_id, point in space['spanned'].items() 
                                                                        for _, did in point["dids"]
                                                                        if did in population_distractors 
                                                                        for axis_id, point_id in spanned_id ], key=lambda x: x[0])}
    axes_rank = {axis_id: max([r for _, r in ranks]) for axis_id, ranks in groupby([(axis_id, int(point_id) + 1) 
                                                                        for axis_id, points in space['axes'].items()
                                                                        for point_id, point in points.items() 
                                                                        for _, did in point['dids'] 
                                                                        if did in population_distractors], key = lambda x: x[0])}
    arr_axes = [axes_rank[axis_id] / len(space['axes'][axis_id]) for axis_id in space['axes'] if axis_id in axes_rank]
    arr = np.average(arr_axes) if len(arr_axes) > 0 else 0 
    # arr_with_spanned_axes = [max([axes_rank.get(axis_id, 0), spanned_ranks.get(axis_id, 0)]) / len(space['axes'][axis_id]) 
    #                             for axis_id in space['axes'] if axis_id in axes_rank or axis_id in spanned_ranks]
    # arr_with_spanned = np.average(arr_with_spanned_axes) if len(arr_with_spanned_axes) > 0 else 0 
    return {"arr": arr}#, "arr_with_spanned": arr_with_spanned}

# avg_rank_of_repr(space, [5,6,14])

def redundancy(space, population_distractors):
    ''' Check if last population has composite problems 
    '''
    population_spanned_distractors = [did for _, point in space['spanned'].items() for _, did in point['dids'] if did in population_distractors]
    pop_r = len(population_spanned_distractors) / len(population_distractors) 
    deca_r = len(space['spanned']) / (len(space['spanned']) + sum([len(points) for points in space["axes"].values()]))
    return {"population_redundancy":pop_r} #, "deca_redundancy":deca_r} #, 'num_spanned': len(space['spanned']) }

# redundancy(space, [5,6,14])

def duplication(space, population_distractors):
    ''' Computes percent of dumplications in DECA space returned by P-PHC 
        Returns tuple: actual dumplicates percent and max possible duplicates percent
    '''
    max_duplication_on_axes = [ len(point["dids"]) - 1 for points in space["axes"].values() for point in points.values() ]
    max_duplication_spanned = [ len(point["dids"]) - 1 for point in space['spanned'].values() ]
    all_dids = [*[did for points in space["axes"].values() for point in points.values() for _, did in point["dids"]],
                *[did for point in space['spanned'].values() for _, did in point['dids']],
                *space['zero']['dids']]
    deca_duplicates = (sum(max_duplication_on_axes) + sum(max_duplication_spanned)) / len(all_dids)
    duplication_on_axes = [len(g) - 1 for _, g in groupby([(axis_id, point_id) 
                                                            for axis_id, points in space['axes'].items() 
                                                            for point_id, point in points.items() 
                                                            for _, did in point['dids'] 
                                                            if did in population_distractors], key = lambda x: x)]
    duplication_spanned = [len(g) - 1 for _, g in groupby([spanned_id 
                                                            for spanned_id, point in space['spanned'].items() 
                                                            for _, did in point['dids'] 
                                                            if did in population_distractors], key = lambda x: x) ]
    duplication = (sum(duplication_on_axes) + sum(duplication_spanned)) / len(population_distractors)
    return {"population_duplication": duplication} #"deca_duplication": deca_duplicates} }

# duplication(space, [5,6,14])

def noninformative(space, population_distractors):
    ''' percent of population that is not represented by axes or spanned (in space['zero']) '''
    noninfo = [did for _, did in space['zero']['dids'] if did in population_distractors]
    return { 'noninfo': len(noninfo) / len(population_distractors) }

def load_space_from_json(json_str):
    space = json.loads(json_str)
    space["spanned"] = {tuple([(axis_id, pos_id) for [axis_id, pos_id] in spanned["pos"]]):spanned["point"] for spanned in space["spanned"]}
    space["axes"] = {int(axis_id):{int(point_id):point for point_id, point in points.items() } for axis_id, points in space["axes"].items()} 
    return space 

def save_space_to_json(space):
    space['spanned'] = [{"pos": spanned_id, "point": point} for spanned_id, point in space['spanned'].items() ]
    return json.dumps(space, indent=4)

# noninformative(space, [5,6,14])

# NOTE: there are other algo specific metrics: def uncovered_search_space():
#     pass