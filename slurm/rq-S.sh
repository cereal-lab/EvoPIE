#!/bin/bash 
#SBATCH --job-name=rq-S
#SBATCH --time=72:00:00
#SBATCH --output=rq-S-%a.out
#SBATCH --mem=8G
#SBATCH --array=0-20

#RQ1: What is the best (in terms ARR*) algo (no multi-step) on spaces without spanned points?
#RQ2: How performance varies for different space of same shape?
#??? RQ3: How performance varies with removal of duplication/spanned
# This implies presence the spaces in space space folder
#NOTE: only 1-sub strategies are left
#NOTE: no rel-kn

algos=('{ "id": "s-0_dp_nd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_nd!k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_nd!kk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_ndXdm", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "nd", "kn"], ["dup", "nd", "kn"], ["dup", "nd", "kn"]]}]}}'
    '{ "id": "s-0_dp_ndXdm!k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "nd", "kn"], ["dup", "nd", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_ndXdm!kk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "nd", "kn"], ["dup", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_sXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "sd", "kn"], ["dup", "sd", "kn"], ["dup", "sd", "kn"]]}]}}'
    '{ "id": "s-0_dp_sXd!k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "sd", "kn"], ["dup", "sd", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_sXd!kk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "sd", "kn"], ["dup", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_d!k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_d!kk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-15_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":15, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-15_dp_d!k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":15, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-15_dp_d!kk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":15, "keys":[["dup", "d", "kn"], ["dup", "kn"], ["dup", "kn"]]}]}}'    
    '{ "id": "s-0_dp_dm", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "dom", "kn"], ["dup", "dom", "kn"], ["dup", "dom", "kn"]]}]}}'
    '{ "id": "s-0_dp_dm!k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "dom", "kn"], ["dup", "dom", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_dm!kk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "dom", "kn"], ["dup", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-15_dp_dm", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":15, "keys":[["dup", "dom", "kn"], ["dup", "dom", "kn"], ["dup", "dom", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-15_dp_dm!k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":15, "keys":[["dup", "dom", "kn"], ["dup", "dom", "kn"], ["dup", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-15_dp_dm!kk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":15, "keys":[["dup", "dom", "kn"], ["dup", "kn"], ["dup", "kn"]]}]}}')

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