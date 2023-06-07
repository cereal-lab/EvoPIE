''' implementation of pphc quiz model '''
import numpy as np
from typing import Any

from evopie import APP, models
from evopie.utils import groupby
from dataclasses import dataclass
from numpy import unique
from evopie.quiz_model import QuizModel
from pandas import DataFrame

@dataclass 
class CoevaluationGroup:   
    ''' The group of genotypes and students which saw these genotypes in one quiz ''' 
    inds: 'list[int]'
    objs: 'list[int]'
    ppos: int

class Archive():
    ''' stores interactions with quiz model '''
    @dataclass
    class Representation: #NOTE: we need this wrapper because pandas goes crazy if you provide to it just lists
        ''' Abstract representation from the archive '''
        g: Any
        def __repr__(self) -> str:
            return self.g.__repr__()

    def __init__(self, archive_entries: 'list[dict]', objectives: 'list[int]') -> None:
        plain_data = {i["genotype_id"]:{'g': Archive.Representation(i['genotype']),
                                **{ int(id):val for id, val in i['objectives'].items()}} 
                                for i in archive_entries}
        self.archive = DataFrame.from_dict(plain_data, orient='index', columns=["g", *objectives])    
        self.archive[["g"]] = self.archive[["g"]].astype(object)   

    def add(self, genotype: Any) -> int:
        ''' The routing to register genotype in the archive. The genotype becomes int id at return '''
        genotype_obj = Archive.Representation(genotype)
        ix = self.archive[self.archive['g'] == genotype_obj].index
        if len(ix) > 0:
            return int(ix[0]) #NOTE: by default DataFrame index is int64 which fails json serialization
        else:
            id = len(self.archive)
            self.archive.loc[id, 'g'] = genotype_obj
            return id

    def add_objective(self, obj):
        self.archive[obj] = None

    def get(self, genotype_id: int) -> Any: 
        ''' Get genotype by its id '''
        return self.archive.loc[genotype_id, 'g'].g

    def at(self, ids, objs):
        return self.archive.loc[ids, objs].iterrows()

    def num_interactions(self, ids):        
        return self.archive.loc[ids, self.archive.columns != 'g'].notna().astype(int).sum(axis=1).iteritems()

    def set_interraction(self, id, obj, score):
        self.archive.loc[id, obj] = score 

    def __contains__(self, item):
        return self.archive.__contains__(item)

    def items(self):
        return self.archive.iterrows()
    def to_csv(self, file_name, active: 'list[int]') -> None: 
        ''' save state to csv file '''        
        archive_clone = self.archive.copy()
        archive_clone["p"] = 0
        archive_clone["p"] = archive_clone["p"].astype(int)            
        for ind in active:
            archive_clone[ind, "p"] = 1        
        archive_clone.to_csv(file_name)

class PphcQuizModel(QuizModel): 
    ''' Base class for evolution process (but still of specific form)'''
    default_settings = { "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 2, "mutation": "mutate_random"}

    def __init__(self, quiz_id: int, process: models.EvoProcess, distractors_per_question: 'dict[int, list[int]]'):
        super(PphcQuizModel, self).__init__(quiz_id, process, distractors_per_question)
        settings = {**PphcQuizModel.default_settings, **process.impl_state}
        self.gen: int = settings.get("gen", 0)
        self.seed = settings.get("seed", None)
        self.rnd = np.random.RandomState(self.seed)
        self.pop_size: int = settings.get("pop_size", 1)
        self.pareto_n: int = settings.get("pareto_n", 2)
        self.child_n: int = settings.get("child_n", 1)
        self.gene_size: int = settings.get("gene_size", 2)
        self.mutation_strategy = settings.get("mutation", "mutate_one_point_worst_to_best")
        self.population = settings.get("population",[])
        self.objectives = settings.get("objectives",[])        
        self.archive = Archive(settings.get("archive",[]), self.objectives)        
        self.gene_stats = settings.get("gene_stats", {})
        self.coevaluation_groups: dict[str, CoevaluationGroup] = { cgid:CoevaluationGroup(g["inds"], g["objs"], g['ppos']) 
                                                                    for cgid, g in settings.get("coevaluation_groups", {}).items()}
        self.evaluator_coevaluation_groups: dict[int, str] = { int(evaluator_id):str(group_id)
                                                                    for evaluator_id, group_id in settings.get("evaluator_coevaluation_groups", {}).items() }
        #add to population new inds till moment of pop_size
        #noop if already inited
        while len(self.population) < self.pop_size:
            self.population.append(self.init()) #init respresent initialization operator

        self.mutate_population() #add new coeval groups on new parents

    def get_explored_search_space_size(self) -> int:
        ''' returns explored search space size '''
        return len(self.archive.archive)

    def mutate_population(self):
        for pid, parent in enumerate(self.population):
            coeval_group_id = f"{self.gen}:{pid}"
            if coeval_group_id not in self.coevaluation_groups:
                self.coevaluation_groups[coeval_group_id] = CoevaluationGroup(inds=[parent, *self.mutate(parent)], objs = [], ppos=pid)

    def compare(self, coeval_group_id: str, coeval_group: CoevaluationGroup):  
        ''' Implements Pareto comparison '''      
        if len(coeval_group.objs) >= self.pareto_n:
            genotype_evaluations = {genotype_id: evals for genotype_id, evals in self.archive.at(coeval_group.inds, coeval_group.objs)}
            genotype_evaluation_count = {genotype_id: num_evals for genotype_id, num_evals in self.archive.num_interactions(coeval_group.inds)}
            parent = coeval_group.inds[0]
            parent_genotype_evaluation = genotype_evaluations[parent]
            parent_genotype_evaluation_count = genotype_evaluation_count[parent]
            # possible_winners = [ child for child in eval_group.inds[1:]
            #                         if (genotype_evaluations[child] == parent_genotype_evaluation).all() or not((genotype_evaluations[child] <= parent_genotype_evaluation).all()) ] #Pareto check

            def child_is_better(parent_genotype_evaluation, parent_genotype_evaluation_count, 
                                child_genotype_evaluation, child_genotype_evaluation_count):
                child_domination = child_genotype_evaluation >= parent_genotype_evaluation
                parent_domination = child_genotype_evaluation <= parent_genotype_evaluation
                if (parent_genotype_evaluation == child_genotype_evaluation).all(): #Pareto check
                    #non-domination and same outcome for given students
                    #prefer child for diversity - other statistics is necessary 
                    return child_genotype_evaluation_count <= parent_genotype_evaluation_count  #pick child if less evaluated
                elif child_domination.all():
                    return True 
                elif parent_domination.all():
                    return False 
                else: #non-pareto-comparable
                    #NOTE: if we use aggregation here - it will be same to non-Pareto comparison
                    return child_genotype_evaluation_count <= parent_genotype_evaluation_count  #pick child if less evaluated
                    # child_sum = (child_genotype_evaluation.sum(), child_domination.sum())
                    # parent_sum = (parent_genotype_evaluation.sum(), parent_domination.sum())
                    # if child_sum == parent_sum: 
                    #     #prefer child for diversity but better to check other stats
                    #     return True 
                    # elif child_sum > parent_sum:
                    #     return True 
                    # else: #child_sum < parent_sum 
                    #     return False                                 
            possible_winners = [ child for child in coeval_group.inds[1:]
                                    if child_is_better(parent_genotype_evaluation, parent_genotype_evaluation_count, 
                                                        genotype_evaluations[child], genotype_evaluation_count[child]) ]

            # possible_winners = [ child for child in eval_group.inds[1:]
            #                         if (genotype_evaluations[child] >= parent_genotype_evaluation).all() ] #Pareto check
            
            # better_children = [ child for child in eval_group.inds[1:]
            #                         if not((genotype_evaluations[child] == parent_genotype_evaluation).all()) and (genotype_evaluations[child] >= parent_genotype_evaluation).all() ] #Pareto check
            # if any(better_children):
            #     for i, ind in enumerate(self.population):
            #         if ind == parent:
            #             self.population[i] = None
            # for child in possible_winners:
            #     self.population.append(child)

            if len(possible_winners) > 0:
                winner = int(self.rnd.choice(possible_winners)) #NOTE: we have this cast due to bugged behaviour of numpy - it returns winner of type np.int64, not int - fails on json step
                self.population[coeval_group.ppos] = winner #winner takes place of a parent
            del self.coevaluation_groups[coeval_group_id]
            #we cleanup also evaluator_coevaluation_groups which denies postponed evaluations
            #NOTE: comment next if you allow evaluation from another group (from prev generation)
            evaluators = list(self.evaluator_coevaluation_groups.items())
            for (sid, cgid) in evaluators: #TODO: store student ids in coeval_group for faster cleanup
                if cgid == coeval_group_id:
                    APP.logger.warn(f"Cannot accept evaluation of student {sid}, because coeval group {cgid} is evolving to next generation based on result from {coeval_group}")
                    del self.evaluator_coevaluation_groups[sid]

    def evaluate_internal(self, evaluator_id: int, result: 'dict[int, int]') -> None:
        coevaluation_group_id = self.evaluator_coevaluation_groups.get(evaluator_id, None)
        eval_group = self.coevaluation_groups.get(coevaluation_group_id, None)        
        if coevaluation_group_id is None or eval_group is None:
            #NOTE: coeval group was removed by evolution
            APP.logger.warn(f"Discarding evaluation of {evaluator_id} for quiz {self.quiz_id}. Population is {self.population}. Result {result}")
            return
        eval_group.objs.append(evaluator_id)   
        for ind in eval_group.inds:
            self.update_fitness(ind, evaluator_id, result)
        del self.evaluator_coevaluation_groups[evaluator_id]
        self.compare(coevaluation_group_id, eval_group)
        gen_was_evaluated = len(self.coevaluation_groups) == 0 #group is treated as evaluated when removed  from this dict                
        if gen_was_evaluated:
            self.gen += 1 # going to next generation                    
            self.mutate_population()

    def init(self):
        ''' initialization of one individual (uniquely in the population) '''
        genotype = []
        for qid, distractors in self.distractors_per_question.items():
            d_set = set(distractors)
            group = []
            for _ in range(min(len(d_set), self.gene_size)):
                d = int(self.rnd.choice(list(d_set))) #NOTE: cast is important here - without it could fail on json servialization of np type
                d_set.remove(d)
                group.append(d)
            genotype.append((qid, sorted(group)))
        ind = self.archive.add(genotype)
        return ind 
    
    def mutate_one_point_worst_to_best_1child(self, parent_id): 
        ''' mutation on per question basis, take one question gene and replace it. Stats are considered '''
        genotype = self.archive.get(parent_id)                

        def delete_score(gene_stats):
            ''' defines the chance of gene to be selected for removal and replacement by other gene '''
            return (1 - gene_stats.get('num_0', 0) / (gene_stats.get('num_any', 0) + 1)) * (1 - gene_stats.get('num_1', 0) / (gene_stats.get('num_any', 0) + 1))

        genotype_stats = [ (qid, [(did, delete_score(self.gene_stats.get(f"{qid}:{did}", {}))) for did in genes]) for qid, genes in genotype ]
    
        genotype_stats = [ (qid, [(did, s / genes_removal_score) for did, s in dids]) 
                                for qid, dids in genotype_stats 
                                for genes_removal_score in [sum(s for _, s in dids)]]
        
        genes_to_remove = {qid: int(self.rnd.choice([did for did, _ in dids], 1, p = [s for _, s in dids])) for qid, dids in genotype_stats }

        def select_score(gene_stats):
            return 0.01 + (0 if gene_stats.get('num_any', 0) == 0 else (gene_stats.get('num_0', 0) * gene_stats.get('num_1', 0) / gene_stats.get('num_any', 0) / gene_stats.get('num_any', 0)))
        
        candidate_distractors = [ (qid, [(candidate_did, select_score(self.gene_stats.get(f"{qid}:{candidate_did}", {}))) 
                                            for candidate_did in self.distractors_per_question.get(qid, []) 
                                            if candidate_did not in ignored_dids])
                            for qid, used_dids_with_scores in genotype_stats 
                            for ignored_dids in [set(did for did, _ in used_dids_with_scores)] ]
        
        candidate_distractors = [ (qid, [(did, s / genes_total_score) for did, s in dids]) 
                                for qid, dids in candidate_distractors 
                                if len(dids) > 0
                                for genes_total_score in [sum(s for _, s in dids)]]
                
        selected_candidates = {qid: int(self.rnd.choice([did for did, _ in dids], 1, p = [s for _, s in dids]))
                                    for qid, dids in candidate_distractors}
        
        child = [(qid, sorted(candidate if did == deleted and candidate is not None else did for did in genes)) 
                    for qid, genes in genotype 
                    for candidate in [selected_candidates.get(qid, None)]
                    for deleted in [genes_to_remove.get(qid, None)]]
        
        child_id = self.archive.add(child)     

        return child_id    
        
    def mutate_one_point_worst_to_best(self, parent_id): 
        children = [self.mutate_one_point_worst_to_best_1child(parent_id) for _ in range(self.child_n)]
        return children

    def mutate_random(self, parent_id):
        genotype = self.archive.get(parent_id)        
        children = []
        for _ in range(self.child_n):
            tries = 10
            while tries > 0:
                child = []
                for qid, genes in genotype: #here we do not evolve qids yet
                    distractors = self.distractors_per_question.get(qid, [])
                    d_set = set(distractors)
                    group = []
                    for g in genes:
                        # possibilities = list(d_set - set([g]))
                        possibilities = list(d_set) #NOTE: prev line is more restrictive - tries to differ each gene
                        if len(possibilities) == 0:
                            d = g
                        else: 
                            d = int(self.rnd.choice(possibilities)) #NOTE: cast is important
                        d_set.remove(d)
                        group.append(d)
                    child.append((qid, sorted(group)))
                child_id = self.archive.add(child)
                if child_id != parent_id:
                    children.append(child_id)
                    break
                tries -= 1
        return children

    def mutate(self, parent_id): 
        ''' produce children of a parent'''
        return getattr(self, self.mutation_strategy)(parent_id)
        
    def get_sampling_size(self):
        return self.gene_size

    def select(self, evaluator_id):
        ''' Policy what evaluation group to prioritize 
            Random, rotate (round-robin), greedy '''
        return str(self.rnd.choice(list(self.coevaluation_groups.keys())))

    def prepare_for_evaluation(self, evaluator_id: int) -> 'list[tuple[int, list[int]]]':
        if evaluator_id not in self.archive:
            self.archive.add_objective(evaluator_id)
            self.objectives.append(evaluator_id)
        if evaluator_id in self.evaluator_coevaluation_groups: #student should solve quiz with same set of distractors on retake it could be regenerated
            coevaluation_group_id = self.evaluator_coevaluation_groups[evaluator_id]
        else:
            coevaluation_group_id = self.select(evaluator_id)
            self.evaluator_coevaluation_groups[evaluator_id] = coevaluation_group_id
        inds = self.coevaluation_groups[coevaluation_group_id].inds #select group from one parent            
        ind_genotypes = [ self.archive.get(ind) for ind in inds ]
        question_distractors = [ (qid, [int(d) for d in unique([d for _, d in ds])]) 
                                    for qid, ds in groupby(((qid, d) 
                                    for ind in ind_genotypes 
                                    for (qid, ds) in ind for d in ds), key=lambda x: x[0])]
        return question_distractors

    def get_model_state(self):
        archive = [ {"genotype_id": genotype_id, "genotype": r.g.g, "objectives": {c: r[c] for c in r[r.notnull()].index if c != "g" }}
                                            for genotype_id, r in self.archive.items() ]
        settings = { "pop_size": self.pop_size, "gen": self.gen, "seed": self.seed,
                    "gene_size": self.gene_size, "pareto_n": self.pareto_n, "child_n": self.child_n,
                    "coevaluation_groups":  {id: {"inds": g.inds, "objs": g.objs, "ppos": g.ppos} for id, g in self.coevaluation_groups.items()},
                    "evaluator_coevaluation_groups": self.evaluator_coevaluation_groups,
                    "population": self.population, "gene_stats": self.gene_stats, "mutation": self.mutation_strategy,
                    "objectives": self.objectives,
                    "archive": archive}   
        return settings

    def get_best_quiz(self):
        population = set(did for _, dids in self.prepare_for_evaluation(-1) for did in dids)
        return list(population)

    def update_fitness(self, ind: int, evaluator_id: int, result: 'dict[int, int]') -> None:  
        # cur_score = self.archive.loc[ind, evaluator_id]
        cur_score = 0 #if cur_score is None or math.isnan(cur_score) else cur_score
        ind_genotype = self.archive.get(ind)
        for qid, genes in ind_genotype: #result - dict where for each question we provide some data                        
            if qid in result:
                for did in genes:
                    gene_stats = self.gene_stats.setdefault(f"{qid}:{did}", {})
                    if did == result[qid]:
                        cur_score += 1
                        gene_stats["num_1"] = gene_stats.get("num_1", 0) + 1
                    else:
                        gene_stats["num_0"] = gene_stats.get("num_0", 0) + 1
                    gene_stats["num_any"] = gene_stats.get("num_any", 0) + 1
        self.archive.set_interraction(ind, evaluator_id, cur_score)

    def to_csv(self, file_name) -> None: 
        ''' save state to csv file '''
        self.archive.to_csv(file_name, self.population)

    def to_dataframe(self):
        return self.archive.archive