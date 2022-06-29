''' Module to work with DECA  '''

from math import prod
import random
from typing import Any
from functools import reduce
from itertools import product

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

def process_axes(axes):
    ''' returns CF sets from simple representations '''
    res = []
    for axis in axes: 
        axis_res = []
        res.append(axis_res)
        axis_candidates = axis[0]
        axis_res.append(axis_candidates)
        for point in axis[1:]: 
            axis_candidates = (*axis_candidates, *point)
            axis_res.append(axis_candidates)
    return res 

def process_spanned(processed_axes, spanned):
    ''' Spanned should be indexes in axes '''
    res = [[axis[i] for i, axis in zip(point, processed_axes)] for point in spanned ]
    return res

def flatten_spanned(processed_spanned):
    return [tuple(sorted([i for s in sets for i in s])) for sets in processed_spanned]

def synth_deca_coords_biased(candidates: 'list[int]', dims: int, num_tests: int): 
    ''' Routine to generate synthetic coordinate system at random based on given students and number of dimensions 
        Returns list of test cases
        Example: ([[{1}], [{2}]], [({1}, {2})])  == (axis, spanned)    
        Spanned points are expressed through axis  
    '''
    assert len(candidates) >= dims #number of dimansions could not be bigger than number of candidates
    assert num_tests >= dims
    #TODO: other assert on num_tests 

    axis = []
    spanned = []     

    #NOTE: number of spanned points from number of points on axis
    # axis [a1, a2] --> a1 * a2 spanned 
    # axis [a1, a2, ... an] --> a1 * a2 * ... * an spanned
    # candidate exists only at one point. 
    # total number of points num_points = a1 + a2 + ... + an + v where v in [0, a1 * a2 * ... * an], n == dims, ai in [1, ? len(candidates))
    # so we need to split num_tests onto dims + 1 bins. dims bins should exist for sure, spanned is optional 
    num_tests_bins = [] #dims of them for axis and one for spanned. each element specifies number of points at corresponding place 
    selected_num_points_total = 0
    for i in range(dims): #works with assumption 1 point == +1 candidate solution, code after should collapse points
        dims_left = dims - len(num_tests_bins) - 1
        num_points = random.randint(1, len(candidates) - selected_num_points_total - dims_left)        
        print(f"Dimension {i+1}: dim_left {dims_left} and num_points: {num_points} from [1, {len(candidates) - selected_num_points_total - dims_left}]")
        selected_num_points_total += num_points
        #NOTE: num_points is max number of points that we can place on axis. One point could have several new candidates - therefore effectivelly collapse two points onto one
        num_tests_bins.append(num_points)    

    #NOTE: we permute axis to give equal chance to 2, 1, 2 and 2, 2, 1. Otherwise, generating 2, 1, 2 has less chance
    # it still not guarantee uniform distribution of all possible axises. "More fair" could be to pick axis position at random?
    random.shuffle(num_tests_bins)    
    points_left = num_tests - selected_num_points_total
    print(f"Initial axis: {num_tests_bins}")
    print(f"Points left: {points_left}. Selected: {selected_num_points_total}. Required: {num_tests}")
    # NOTE: here we can have situations:
    #   0. Points left is zero - return axis and no spanned points (for each point we pick random one element from candidates - we operated with assumption that each point has +1 unique candidate)
    #   1. Points left is negative - we need to collapse points on axis to reach necessary num_tests - before we do so we distribute candidates among points 
    #   2. Some points_left to generate - they will be spanned points:
    #          2.1 We check if there are enough axis points to cover points_left. If so, we pick spanned == num points left 
    #          2.2 Spanned points num is not enough to cover points left - we increase random dim +1 and repreat procedure (point 2)  
    def assign_candidates_to_axis_points(axis_points_num):
        ''' Still operates with assumption: 1 axis point == +1 candidate'''        
        random.shuffle(candidates) # we pick them at random 
        picked_points = 0
        axis = []
        for i in range(len(axis_points_num)):            
            num_points = axis_points_num[i]
            picked_candidates = candidates[picked_points:(picked_points + num_points)]
            picked_points += num_points
            axis_candidates = [[el] for el in picked_candidates]
            axis.append(axis_candidates)
            print(f"Axis {i + 1}, candidates: {axis_candidates}")
        return axis

    def axis_point_collapse(axis, num_to_collapse):
        ''' Collapse candidates of points. Note the exception reasen - they add validation to asserts at the beginning''' 
        while num_to_collapse > 0:
            possible_axis = [a for a in axis if len(a) > 1] #axis to pick from should have 2 or more points
            if len(possible_axis) == 0:
                raise Exception(f"Cannot collapse axises to specified number of points {num_tests}. Num collapses {num_to_collapse}. Axis: {axis}")
            picked_axis = random.choice(possible_axis)
            point_to_collapse_id, point_to_collapse = random.choice([ (i, p) for i, p in enumerate(picked_axis) if i > 0 ])
            # we always collapse with previous point and picked_axis_point_id >= 1
            print(f"Collapsing axis {picked_axis} at position {point_to_collapse_id}. Point {point_to_collapse} will be merged to {picked_axis[point_to_collapse_id - 1]}")
            picked_axis[point_to_collapse_id - 1].extend(point_to_collapse)
            picked_axis.remove(point_to_collapse)
            num_to_collapse -= 1             
        return axis 

    if points_left <= 0: 
        axis = assign_candidates_to_axis_points(num_tests_bins)
        axis = axis_point_collapse(axis, -points_left)
        return (axis, [])
    else: #analysis of spanned 
        while True: 
            max_spanned_num = reduce(lambda acc, n: acc * n, num_tests_bins, 1)
            if points_left <= max_spanned_num: 
                #assign left points to spanned
                #for this we need to pick corresponding axis for each spanned point 
                #NOTE: next could be probably done more optimal - TODO: think
                all_spanned_positions = list(product(*[[i for i in range(n)] for n in num_tests_bins]))
                shuffled_positions = random.shuffle(all_spanned_positions)
                spanned = shuffled_positions[:points_left]
                print(f"Picked spanned {spanned}")
                axis = assign_candidates_to_axis_points(num_tests_bins)
                break
            else: #we need to extend random dim and try again 
                axis_id = random.choice(list(range(len(num_tests_bins))))
                num_tests_bins[axis_id] += 1
    return (axis, spanned)

# synth_deca_coords_biased([1,2,3,4,5,6,7,8,9,10], 3, 3)

#NOTE: prev function is biased towards axis points. This is rethinking of dimension synth
# Here we perform operation on points in iterative fashion 
# We start with simple dims num of points which cover axis and need to add (num_tests - dims) >= 0 points
# At each step the decision is made:
#       1. Add point on axis (requires presense of candidates left)
#       2. Add spanned point
#       3. Collapse axis points (remove corresponding spanned points)
SYNTH_ACTION_AXIS_ADD = "AXIS_ADD"
SYNTH_ACTION_AXIS_MIGRATE = "AXIS_MIGRATE"
SYNTH_ACTION_SPANNED_ADD = "SPANNED_ADD"
SYNTH_ACTION_AXIS_POINTS_COLLAPSE = "AXIS_COLLAPSE"
SYNTH_ACTION_AXIS_POINT_SPLIT = "AXIS_POINT_SPLIT"
#TODO: SYNTH_ACTION_AXIS_REMOVE - if necessary
#TODO: possible improvements: axis actions could have parameters. Axis add for example max number of candidates to put at once
def synth_deca_coords_complex(candidates: 'list[int]', dims: int, num_tests: int, axis_chance = 1, collapse_chance = 0, spanned_chance = 0, split_chance = 0, max_reduce_count = 1000): 
    ''' Routine to generate synthetic coordinate system at random based on given students and number of dimensions 
        Returns list of test cases (axis, spanned)    
        axis is list, one el for axis, with list of candidates failed the test
        Spanned list element is coordinate that specified in terms of axis_points (not indexes)
        Example: axes [ [[1], [2, 3]], [[4, 5]] ] are two axis, axis 0 has axis_points [1] and [2, 3] (which correspond to test which fails students [1, 2, 3])
        Example: spanned [ ([2, 3], [4, 5]) ] corresponds to one spanned point which is defined by axis_points [2, 3] on axis 0 and [4, 5] on axis 1. This is test which fails students [1, 2, 3, 4, 5]
    '''
    assert len(candidates) >= dims #number of dimansions could not be bigger than number of candidates
    assert num_tests >= dims
    #TODO: other assert on num_tests 

    random.shuffle(candidates) # we pick them at random 

    axes = [[(candidates.pop(), )] for _ in range(dims)] #populate axis with simple elements
    spanned = set()   

    print(f"Initial.\n\tAxes: {axes}")

    points_left = num_tests - sum(len(axis) for axis in axes) - len(spanned)
    while points_left > 0: 
        num_spanned_points = prod(len(axis) for axis in axes)
        collapsable_axes = [(axis_id, axis) for axis_id, axis in enumerate(axes) if len(axis) > 1] 
        splitable_axis_points = [(axis_id, axis, point_id, point) 
                                    for axis_id, axis in enumerate(axes) 
                                    for point_id, point in enumerate(axis) if len(point) > 1]
        def get_actions():
            if len(candidates) > 0:
                yield (SYNTH_ACTION_AXIS_ADD, axis_chance)
            if num_spanned_points > len(spanned):
                yield (SYNTH_ACTION_SPANNED_ADD, spanned_chance)
            if len(collapsable_axes) > 0 and max_reduce_count > 0:
                yield (SYNTH_ACTION_AXIS_POINTS_COLLAPSE, collapse_chance)
            if len(splitable_axis_points) > 0:
                yield (SYNTH_ACTION_AXIS_POINT_SPLIT, split_chance)
        [actions, weights] = list(zip(*get_actions()))
        if len(actions) == 0:
            raise Exception(f"No further action is possible with axes.\n\tAxes: {axes}\n\tCandidates: {candidates}\n\tPoints left: {points_left}")
        [action] = random.choices(actions, weights, k = 1)
        if action == SYNTH_ACTION_AXIS_ADD:
            random.choice(axes).append((candidates.pop(), ))
            print(f"New axis point added.\n\tAxes: {axes}")
        elif action == SYNTH_ACTION_SPANNED_ADD:
            spanned_points = list(set(product(*[[axis_point for axis_point in axis] for axis in axes])) - spanned)
            spanned.add(random.choice(spanned_points))
            print(f"New spanned point added.\n\tSpanned: {spanned}")
        elif action == SYNTH_ACTION_AXIS_POINTS_COLLAPSE:
            axis_id, axis = random.choice(collapsable_axes)
            point_to_collapse_id, point_to_collapse = random.choice([ (i, p) for i, p in enumerate(axis) if i > 0 ])
            # print(f"Collapsing axis {picked_axis} at position {point_to_collapse_id}. Point {point_to_collapse} will be merged to {picked_axis[point_to_collapse_id - 1]}")
            prev_point = axis[point_to_collapse_id - 1]
            axis[point_to_collapse_id - 1] = (*prev_point, *point_to_collapse)
            axis.remove(point_to_collapse)
            #on collapse, corresponding spanned points also collapse
            spanned = set((*p[:axis_id], axis[point_to_collapse_id - 1], *p[axis_id+1:]) if p[axis_id] == point_to_collapse else p for p in spanned) 
            max_reduce_count -= 1
            print(f"Collaped axis {axis_id} point {point_to_collapse_id}.\n\tAxes: {axes}\n\tSpanned: {spanned}")
        elif action == SYNTH_ACTION_AXIS_POINT_SPLIT:
            axis_id, axis, point_id, point = random.choice(splitable_axis_points)
            num_to_pick = random.randrange(1, len(point))
            axis[point_id] = point[:num_to_pick]
            second_point = point[num_to_pick:]
            axis.insert(point_id + 1, second_point)
            print(f"Split axis {axis_id} point {point_id}.\n\tAxes: {axes}\n\tSpanned: {spanned}\n\tSplittable: {splitable_axis_points}")
        points_left = num_tests - sum(len(axis) for axis in axes) - len(spanned)

    return (axes, spanned)

# This version generates spanned points separately
def synth_deca_axes(candidates: 'list[int]', dims: int, num_axis_points: int, axis_chance = 0.25, collapse_chance = 0.25, split_chance = 0.25, migration_chance = 0.25, min_iterations = 20, max_reduce_iterations = 1000): 
    ''' Routine to generate synthetic coordinate system at random based on given students and number of dimensions 
        Returns list of test cases (axis, spanned)    
        axis is list, one el for axis, with list of candidates failed the test
        Spanned list element is coordinate that specified the indexes in axes
        Example: axes [ [[1], [2, 3]], [[4, 5]] ] are two axis, axis 0 has axis_points [1] and [2, 3] (which correspond to test which fails students [1, 2, 3])
    '''
    assert len(candidates) >= dims #number of dimansions could not be bigger than number of candidates
    assert num_axis_points >= dims
    #TODO: other assert on num_tests 

    # random.shuffle(candidates) # should be shuffled before if necessary

    # axes = [[(candidates.pop(), )] for _ in range(dims)] #populate axis with simple elements
    axes = [[] for _ in range(dims) ]

    # print(f"Initial.\n\tAxes: {axes}")

    points_left = num_axis_points # - sum(len(axis) for axis in axes)
    while points_left > 0 or min_iterations > 0:     
        min_iterations = max(0, min_iterations - 1)
        collapsable_axes = [(axis_id, axis) for axis_id, axis in enumerate(axes) if len(axis) > 1] 
        splitable_axis_points = [(axis_id, axis, point_id, point) 
                                    for axis_id, axis in enumerate(axes) 
                                    for point_id, point in enumerate(axis) if len(point) > 1]
        migration_axes = [axis for axis in axes if len(axis) > 1]
        def get_actions():
            if len(candidates) > 0 and axis_chance > 0:
                yield (SYNTH_ACTION_AXIS_ADD, axis_chance)
            if len(collapsable_axes) > 0 and max_reduce_iterations > 0 and collapse_chance > 0:
                yield (SYNTH_ACTION_AXIS_POINTS_COLLAPSE, collapse_chance)
            if len(splitable_axis_points) > 0 and split_chance > 0:
                yield (SYNTH_ACTION_AXIS_POINT_SPLIT, split_chance)
            if len(migration_axes) > 0 and migration_chance > 0:
                yield (SYNTH_ACTION_AXIS_MIGRATE, migration_chance)
        actions_with_weights = list(get_actions())        
        if len(actions_with_weights) == 0:
            raise Exception(f"No further action is possible with axes.\n\tAxes: {axes}\n\tCandidates: {candidates}\n\tPoints left: {points_left}")
        [actions, weights] = list(zip(*actions_with_weights))
        [action] = random.choices(actions, weights, k = 1)
        if action == SYNTH_ACTION_AXIS_ADD:            
            picked_axis = next((axis for axis in axes if len(axis) == 0), random.choice(axes))
            picked_axis.append((candidates.pop(0), ))
            print(f"New axis point added.\n\tAxes: {axes}")
        elif action == SYNTH_ACTION_AXIS_POINTS_COLLAPSE:
            axis_id, axis = random.choice(collapsable_axes)
            point_to_collapse_id, point_to_collapse = random.choice([ (i, p) for i, p in enumerate(axis) if i > 0 ])
            # print(f"Collapsing axis {picked_axis} at position {point_to_collapse_id}. Point {point_to_collapse} will be merged to {picked_axis[point_to_collapse_id - 1]}")
            prev_point = axis[point_to_collapse_id - 1]
            axis[point_to_collapse_id - 1] = (*prev_point, *point_to_collapse)
            axis.remove(point_to_collapse)
            max_reduce_iterations -= 1
            print(f"Collaped axis {axis_id} point {point_to_collapse_id}.\n\tAxes: {axes}")
        elif action == SYNTH_ACTION_AXIS_POINT_SPLIT:
            axis_id, axis, point_id, point = random.choice(splitable_axis_points)
            num_to_pick = random.randrange(1, len(point))
            axis[point_id] = point[:num_to_pick]
            second_point = point[num_to_pick:]
            axis.insert(point_id + 1, second_point)
            print(f"Split axis {axis_id} point {point_id}.\n\tAxes: {axes}\n\tSplittable: {splitable_axis_points}")
        elif action == SYNTH_ACTION_AXIS_MIGRATE:
            from_axis, to_axis = random.choices(migration_axes, k=2)
            point = from_axis.pop(random.randrange(0, len(from_axis)))
            to_axis.insert(random.randint(0, len(to_axis)), point)
            print(f"Moved point {point}.\n\tAxes: {axes}")
        points_left = num_axis_points - sum(len(axis) for axis in axes)
    return axes

def synth_deca_spanned(axes, num_spanned):
    num_spanned_points = min(prod(len(axis) for axis in axes), num_spanned)
    if num_spanned_points > 0:        
        spanned_points = list(set(product(*[[point_id for point_id, _ in enumerate(axis)] for axis in axes])))
        random.shuffle(spanned_points)
        spanned = spanned_points[:num_spanned_points]
    else:
        spanned = []
    return spanned


# axes = synth_deca_axes([1,2,3,4,5,6,7,8,9,10], 3, 3, min_iterations = 100) 
# p_axes = process_axes(axes)
# spanned = synth_deca_spanned(p_axes, 10)
# p_spanned = process_spanned(p_axes, spanned)
# flatten_spanned(p_spanned)
# synth_deca_coords([1,2,3,4,5,6,7,8,9,10], 3, 10)    
# synth_deca_coords([1,2,3,4,5,6,7,8,9,10], 3, 8, axis_chance = 0.5, collapse_chance = 0.4, split_chance = 0.1) 