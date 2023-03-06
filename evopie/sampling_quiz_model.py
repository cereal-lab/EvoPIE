''' Modification of pphc which considers Pareto domination on level of distractors '''
''' Note that archive is changed to be of level of distractor '''
from math import sqrt
import numpy as np

from evopie import models
from evopie.utils import groupby
from evopie.quiz_model import QuizModel
from pandas import DataFrame

#NOTE:
# 1. DECA knowledge contains candidates and tests 
#       candidates are students while tests are quiz question in a form of [d1, ... dn] 
#           where n is number of alternatives and d is distractor from question pool
#       di could also be * meaning any possible distractor. Example [*, d2, *] requires only d2 be present to fail student 
#       Current DECA implementation allocates one distractor dx which is equivalent to [*, dx, *] set - ignoring distractor context 
#       One DECA point could have several distractors [*, da, *] and [*, db, *] - if any schema of current student matches current quiz - simulated student will fail the quiz
#    Lets look onto example DECA knowledge for 1 question quiz 
#      DECA: 2 axis with 2 points (excluding origin) on each and 1 spanned points selected:
#               Axis 1. point1 students: {s1}, distractors {d1}; point2 students {s1, s2}, distractors {d2}
#               Axis 2. point1 students: {s3}, distractors {d3}; point2 students {s3, s4}, distractors {d4}
#               Spanned at (2, 2): students {s1, s2, s3, s4}, distractor {d5}
#               Origin d6
# 2. Simulation is already organized in this way. It randombly picks matched distractor and assign it as an answer.
# 3. Sampling algo obtains result with picked answer per question - which defines did current model fail student or not.
# First goal of sampling algo is to give each distractor to students at least k=1 times
# Then, it will use DECA analysis on low level interactions to sample distractors
#       HIGH LEVEL interaction is between model and student. Per question it looks like (given knowledge above):
#        question   | s1    | s2    | s3    | s4    | ...
#        [d1*d2 d3 ]| 1     | *     | *     | *     |
#        [d4 d5*d6 ]| *     | 1     | *     | *     |
#        [d1 d5*d4*]| *     | *     | 1     | 1     | 
#        []
#       ....
#       where we have question as it was given to student and fail 1, not-fail 0 result 
#       LOW LEVEL interaction is between distractor and student and is used for sampling of next model 
#       distractor  | s1    | s2    | s3    | s4    | ...
#       d1          | 1,1   | *     | 1,0   | 1     |
#       d2          | 1,0   | *     | *     | *     |
#       d3          | 1,0   | *     | *     | 1     |
#       d4          | *     | 1,0   | 1,1   | 1     |
#       d5          | *     | 1,1   | 1,1,0 | 1     |
#       d6          | *     | 1,0   | *     | 1     |
#       values in the matrics - first number == to number from HIGH LEVEL matrix, second is real student selection. 
#       QUESTION: Can high/low level iteraction have some distractor di expressed as sum(dj, j >= 2)?
#           In a case when fully defined (no *) is required
#           1. We need to have common columns (students), at least 2 to conclude the composition. 
#           2. We are going to give to these students same set of distractors [da, db, dc] where we check that da = db + dc or similar.
#           3. But each student still selects only one distractor among da, db, dc: We can have same result for all students. Say:
#               d | s1 | s2     d | s1 | s2
#               da| 0  | 0      da| 0  | 0
#               db| 1  | 1      db| 1  | 0
#               dc| 0  | 0      dc| 0  | 1
#           Neither High no low level interactions will not be able to conclude da = db + dc. Student can pick only one answer. 
#           Though for first case we assume that db has bigger strength and therefore we go to definition of strength:
#NOTE: Distractor strength relation on DECA space:
#       from DECA space above we can assume next natural ordering on distractor strength d1 < d2 for student s1
#       1. Distractors d1 and d2 could not be on different axes if they fail s1 - student s1 is assigned to one axis point and/or spanned points
#       2. if d1 and d2 on an axis - d2 is stronger if it is closer to axis end (fails more student)
#       3. if d2 is spanned and d1 is on axis, d1 < d2 always (even if d2 at end of axis) - assuming that d2 represents a combination of misconcepts which makes it stronger
#       4. if d2 and d1 are spanned - their strength is defined by number of axis they combine. If number of axis is same, number of failed students is used. 
# We can build our algo assuming this relation and base our simulation on it.
#IMPORTANT: SIMULATION should work according to defined strength.
#       
#           During sampling we should consider diversity - if we have same pattern like in prev first table - we should penalize db
#           unless we meet some evaluation which different.
#           So we have two forces. 
#           1. To avoid spanning points we should prefer diversity in outcomes when we select distractor 
#           2. To avoid origin and go towards axis, in oposite we would prefer quality during selection 
# We can define 2 hyperparameters: quality_n and diversity_n - numbers of distractors to sample according to quality and according to diversity. 
#IDEA: go to Shenon's Entropy to estimate perplexity of decision. Check entropy and perplexity as potential metrics.  
#   Qulaity_N - number of distractors to sample according to quality characteristics.
#       Quality is the force that pushes us towards end of axis. 
#       In prev example we still can prefer db to be selected because even though it looks like spanned point - some unknown evaluations could be 0 for it
#           and therefore it could be good axis point. 
#       The danger of quality that the selection will always dominate the decision. 
#   Diversity_N - number of distractors to sample for diversity - 1 0 or 0 1 transitions are prefered. 
#THOUGHT: imagine quiz with 2 distractors. 1 is trivial and another is very but not absolutely hard. All but 1 student fails the second distractor.
#           this corresponds to 1 axis DECA space with 1 axis point where all but one students are placed. 
#           Does discovering this point make sense? Yes. 
#
#PROPOSITION: probabilistic selection is based on number of 1 0/0 1 for any two common students
#               for each distractor we compute # of 1 0 and 0 1 transitions unique to it (not present in other distractors)
#                   when same number - pick with biggest # of 1. 
#   Probability value - low for all 0, a bit better for all 1, even better for present 0s and 1s (defined by unique 0 1 present) 
# 
#   did: {cfs:{student ids}, css: {student ids}} - candidate fail and success sets
#   did1: cfs1, did2: cfs2  --> cfs1 - sum(cfs_others)

class SamplingQuizModel(QuizModel): 
    ''' Samples n distractors from interactions. Does not change sampling for group_size interactions '''
    default_settings = { "n": 3, "min_num_evals": 1, "group_size": 2, "strategy": "non_domination", "hyperparams": {}, "reduced_facts": False}

    def __init__(self, quiz_id: int, process: models.EvoProcess, distractors_per_question: 'dict[int, list[int]]'):
        super(SamplingQuizModel, self).__init__(quiz_id, process, distractors_per_question)
        settings = {**SamplingQuizModel.default_settings, **process.impl_state}
        self.seed = settings.get("seed", None)
        self.rnd = np.random.RandomState(self.seed)
        self.n: int = settings.get("n", SamplingQuizModel.default_settings["n"])
        self.t = settings.get("t", 0)
        self.hyperparams: dict = settings.get("hyperparams", SamplingQuizModel.default_settings["hyperparams"])
        self.group_size: int = settings.get("group_size", SamplingQuizModel.default_settings["group_size"])
        self.cur_iter: int = settings.get("cur_iter", 0)
        self.reduced_facts = settings.get("reduced_facts", SamplingQuizModel.default_settings["reduced_facts"])
        #NOTE: if reduced_facts is True, we are going to ignore 0s when 1 is present in the interaction
        self.quiz = settings.get("quiz", []) #question distractors sampled to be present
        self.strategy = settings.get("strategy", SamplingQuizModel.default_settings["strategy"])
        #NOTE: we need  to maintain interactions in both forms but store only one form
        self.interactions: dict = {**settings.get("interactions", {})} #dict student_id:{quiz:[(qid1, [dids]), ...], result:{did:0/1}}
        # self.strength: dict = settings.get("strength", {}) #graph in a form of linked list did-to-did defines link from weaker to stronger distractor. did: {stronger:{dids}, weaker:{dids}}
        self.inverted_interactions: dict = self.invert_interactions()
        self.sample_best_one = settings.get("sample_best_one", False)

        self.sample_strategy = getattr(self, self.strategy)
        
    def invert_interactions(self):
        return {int(did):{sid:result for (_, sid, result) in plain_ints} 
                    for (did, plain_ints) in 
                        groupby([(did, sid, result) for sid, interaction in self.interactions.items() 
                                    for (did, result) in interaction.get('result', {}).items() ],
                            key=lambda x: x[0])}

    def get_explored_search_space_size(self) -> int:
        tried_models = set(str(interaction['quiz']) for interaction in self.interactions.values())
        return len(tried_models)

    def get_sampling_size(self):
        return self.n

    def evaluate_internal(self, evaluator_id: int, result: 'dict[int, int]') -> None:
        interaction = self.interactions.get(str(evaluator_id), None)
        given_quiz = interaction['quiz']
        if self.reduced_facts: 
            result = interaction.setdefault('result', {})
            for qid, dids in given_quiz:
                answer = result.get(qid, -1)
                if answer == -1:
                    for did in dids:
                        result[str(did)] = 0 
                else:
                    result[str(answer)] = 1
        else:
            interaction['result'] = {str(did):1 if did == answer else 0 for qid, dids in given_quiz for answer in [result.get(qid, -1)] for did in dids }
        for qid, dids in given_quiz:
            selected_did = result.get(qid, -1)
            if self.reduced_facts: 
                if selected_did == -1:
                    for did in dids:
                        self.inverted_interactions.setdefault(int(did), {})[str(evaluator_id)] = 0               
                else:
                    self.inverted_interactions.setdefault(int(selected_did), {})[str(evaluator_id)] = 1
            else:
                for did in dids:
                    self.inverted_interactions.setdefault(int(did), {})[str(evaluator_id)] = 1 if did == selected_did else 0
            # if selected_did != -1:
            #     weaker_dids = [did for did in dids if did != selected_did]
            #     self.strength[selected_did].setdefault("weaker", set()).update(weaker_dids)
            #     for did in weaker_dids:
            #         self.strength[did].setdefault("stronger", set()).add(selected_did)
        self.cur_iter += 1

    def prepare_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        if (len(self.quiz) == 0) or (self.cur_iter >= self.group_size): 
            self.quiz = self.sample_quiz()      
            self.cur_iter = 0          
        interaction = self.interactions.setdefault(str(evaluator_id), {})  
        interaction['quiz'] = self.quiz
        quiz_to_return = [ (qid, list(dids)) for qid, dids in self.quiz ] #copy from model
        return quiz_to_return

    def get_model_state(self):
        settings = { "seed": self.seed, "n": self.n, "group_size": self.group_size, "t": self.t,
                    "hyperparams": self.hyperparams, "cur_iter": self.cur_iter, "reduced_facts": self.reduced_facts,
                    "quiz": self.quiz, "interactions":  self.interactions, "strategy": self.strategy }
        return settings

    def get_best_quiz(self):
        bestone_before = self.sample_best_one
        self.sample_best_one = True 
        old_b = self.hyperparams.get("b", None)
        self.hyperparams["b"] = 0
        quiz = self.sample_quiz()
        distractors = [d for _, dids in quiz for d in dids ] 
        self.sample_best_one = bestone_before 
        if old_b is None:
            del self.hyperparams["b"]
        else:
            self.hyperparams["b"] = old_b
        return distractors

    def to_dataframe(self):
        return DataFrame(data = self.inverted_interactions.values(), index = [int(did) for did in self.inverted_interactions.keys()])

    #strategies should have signatures as next dids -> blocked_dids -> selection
    def pick_random(self, dids, blocked_dids, num = None):
        return [int(d) for d in self.rnd.choice(dids, num or self.n, raplce = False)] if len(dids) > (num or self.n) else dids          

    def sample_by_score(self, dids, scores):
        total_score = sum(scores)
        weights = [s / total_score for s in scores]
        if self.sample_best_one:
            selected_did_with_weight = max(zip(dids, weights, scores), key=lambda x: x[1])
            # if selected_did_with_weight[2] == 1:
            #     print(f"Best {selected_did_with_weight}")
            #     print(f"Scores {weights}")
            #     print("-------------")
            selected_did = selected_did_with_weight[0]
        else:
            selected_did = self.rnd.choice(dids, p=weights)
        return int(selected_did)

    def max_difficulty(self, dids, blocked_dids):        
        #first for fare game we give each distractor to students at least ones:
        min_num_evals = self.hyperparams.get("min_num_evals", 1)
        high_priority = [did for did in dids if len(self.inverted_interactions.get(int(did), {})) < min_num_evals]
        selected = self.pick_random(self, high_priority, self.n)

        did_scores = {}
        def did_score(did):
            if did not in did_scores:
                did_scores[did] = sum(self.inverted_interactions.get(int(did), {}).values()) #more 1's - better score
            return did_scores[did]

        for i in range(len(selected), self.n):
            scores = [0 if did in selected else did_score(did) for did in dids]
            selected_did = self.sample_by_score(dids, scores)
            selected.append(selected_did)
        return selected 

    def block_similar(self, selected_did, blocked_dids):
        selected_did_students = self.inverted_interactions.get(selected_did, {})
        selected_did_cfs = set(sid for sid, r in selected_did_students.items() if r == 1)
        selected_did_sids = set(selected_did_students.keys())
        for did, did_students in self.inverted_interactions.items():
            if did != selected_did:
                did_cfs = set(sid for sid, r in did_students.items() if r == 1 and sid in selected_did_sids)
                # common_students = set.intersection(set(did_students.keys()), set(selected_did_students.keys()))            
                if len(did_cfs) > 1 and did_cfs.issubset(selected_did_cfs):
                    p = self.hyperparams.get("penalty", 0.1)
                    blocked_dids[did] = p #penalty for same behavior

    #note that hyperparams could vary with time - at some point we would prefer exploitation against exploration
    def compute_score(self, did, non_dominated, dominated, dids, blocked_dids):
        a = self.hyperparams.get("a", 100)
        b = self.hyperparams.get("b", 100)
        c = self.hyperparams.get("c", 100)
        alpha = self.hyperparams.get("alpha", 1)
        beta = self.hyperparams.get("beta", 1)
        gamma = self.hyperparams.get("gamma", 1)
        delta = self.hyperparams.get("delta", 1)
        epsilon = self.hyperparams.get("epsilon", 1)
        knowledge_annealing = self.hyperparams.get("knowledge_annealing", 1) #will degrade knowledge component with time t
        did_interactions = self.inverted_interactions.get(int(did), {})
        interacted_student_count = len(self.interactions)
        if len(did_interactions) == 0:
            return 1000 #should be very high - at start we prefer knowledge 
        cfs = [s for s, r in did_interactions.items() if r == 1]
        css = [s for s, r in did_interactions.items() if r == 0]
        penalty = blocked_dids.get(did, 1)
        non_domination_force = (len(non_dominated) / len(dids)) ** alpha
        domination_force = (len(dominated) / len(dids)) ** beta
        knowledge_force = (1 - len(did_interactions) / interacted_student_count) ** gamma
        simplicity_force = (1 - len(cfs) / len(did_interactions)) ** delta
        difficulty_force = (1 - len(css) / len(did_interactions)) ** epsilon
        res = penalty * (1 + a * sqrt(non_domination_force * domination_force) + b * (knowledge_annealing ** self.t) * knowledge_force + c * sqrt(simplicity_force * difficulty_force))
        return res

    def non_domination(self, dids, blocked_dids):                
        did_relations = {did:(non_domination, domination)
                            for did in dids                             
                            for s in [self.inverted_interactions.get(int(did), {})]
                            for non_domination in [[did1 for did1 in dids 
                                if did1 != did
                                for s1 in [self.inverted_interactions.get(int(did1), {})]
                                for common_students in [set.intersection(set(s.keys()), set(s1.keys()))]
                                for s_lst in [[s[sid] for sid in common_students]]
                                for s1_lst in [[s1[sid] for sid in common_students]]
                                if any(v1 > v2 for v1, v2 in zip(s_lst, s1_lst)) and any(v1 < v2 for v1, v2 in zip(s_lst, s1_lst))]] 
                            for domination in [[did1 for did1 in dids 
                                if did1 != did
                                for s1 in [self.inverted_interactions.get(int(did1), {})]
                                for common_students in [set.intersection(set(s.keys()), set(s1.keys()))]
                                for s_lst in [[s[sid] for sid in common_students]]
                                for s1_lst in [[s1[sid] for sid in common_students]]
                                if s_lst != s1_lst and any(v1 > v2 for v1, v2 in zip(s_lst, s1_lst))]]}
        selected = []
        for i in range(len(selected), self.n):
            scores = [0 if did in selected else self.compute_score(did, non_dominated, dominated, dids, blocked_dids)
                        for did, (non_dominated, dominated) in did_relations.items()]
            selected_did = self.sample_by_score(dids, scores)
            self.block_similar(selected_did, blocked_dids)
            selected.append(selected_did)
        return selected         
    
    def sample_quiz(self) -> 'list[tuple[int, list[int]]]':
        ''' Sample based on interactions and strategy '''
        self.t += 1
        blocked_dids = {} #some info to block same concept distractors across questions
        return [[qid, sorted(self.sample_strategy(dids, blocked_dids))] for qid, dids in self.distractors_per_question.items()]        


