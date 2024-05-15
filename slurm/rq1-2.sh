#!/bin/bash 
#SBATCH --job-name=rq1-2
#SBATCH --time=72:00:00
#SBATCH --output=rq1-2-%a.out
#SBATCH --mem=8G
#SBATCH --array=0-16

#RQ1: What is the best (in terms ARR*) algo (no multi-step) on spaces without spanned points?
#RQ2: How performance varies for different space of same shape?
#??? RQ3: How performance varies with removal of duplication/spanned
# This implies presence the spaces in space space folder
#NOTE: only 1-sub strategies are left
#NOTE: no rel-kn

algos=('{ "id": "rand-3", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 3}'
    '{ "id": "phc-1-2-1-2-r", "algo":"evopie.pphc_quiz_model.PphcQuizModel", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 2, "mutation": "mutate_random"}'
    '{ "id": "phc-1-2-1-2-b", "algo":"evopie.pphc_quiz_model.PphcQuizModel", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 2, "mutation": "mutate_one_point_worst_to_best"}'
    '{ "id": "s-0_k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn"], ["kn"], ["kn"]]}]}}'
    '{ "id": "s-0_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["d", "kn"], ["d", "kn"], ["d", "kn"]]}]}}'
    '{ "id": "s-0_sXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["sd", "kn"], ["sd", "kn"], ["sd", "kn"]]}]}}'
    '{ "id": "s-0_Zs", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["-s", "kn"], ["-s", "kn"], ["-s", "kn"]]}]}}'
    '{ "id": "s-0_dm", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dom", "kn"], ["dom", "kn"], ["dom", "kn"]]}]}}'
    '{ "id": "s-0_nd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nond", "kn"], ["nond", "kn"], ["nond", "kn"]]}]}}'
    '{ "id": "s-0_ndXdm", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nd", "kn"], ["nd", "kn"], ["nd", "kn"]]}]}}'    
    '{ "id": "s-0_dp_k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}]}}'
    '{ "id": "s-0_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_sXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "sd", "kn"], ["dup", "sd", "kn"], ["dup", "sd", "kn"]]}]}}'
    '{ "id": "s-0_dp_Zs", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "-s", "kn"], ["dup", "-s", "kn"], ["dup", "-s", "kn"]]}]}}'
    '{ "id": "s-0_dp_dm", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "dom", "kn"], ["dup", "dom", "kn"], ["dup", "dom", "kn"]]}]}}'
    '{ "id": "s-0_dp_nd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_ndXdm", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "nd", "kn"], ["dup", "nd", "kn"], ["dup", "nd", "kn"]]}]}}')

algo=${algos[$SLURM_ARRAY_TASK_ID]}

cd ~/evopie 
echo "Working in $WORK/evopie/pswp-a-e/ algo $algo"
export EVOPIE_DATABASE_URI=sqlite:///$WORK/evopie/pswp-a-e/db-$SLURM_ARRAY_TASK_ID.sqlite
# export EVOPIE_DATABASE_LOG=$WORK/evopie/data-$SLURM_ARRAY_TASK_ID/db.log
export PYTHONPATH=$(pipenv run which python)

pipenv run flask DB-reboot 
pipenv run flask course init
pipenv run flask quiz init -nq 4 -nd 25 #search space size
pipenv run flask student init -ns 100

pipenv run flask quiz deca-experiments \
    --deca-spaces $WORK/evopie/spaces \
    --algo-folder $WORK/evopie/tmp-algo \
    --results-folder $WORK/evopie/results \
    --random-seed 23 --num-runs 30 \
    --algo "$algo"