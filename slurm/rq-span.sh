#!/bin/bash 
#SBATCH --job-name=rq-span
#SBATCH --time=72:00:00
#SBATCH --output=rq-span-%a.out
#SBATCH --mem=8G
#SBATCH --array=0-8

#RQ1: What is the best (in terms ARR*) algo (no multi-step) on spaces without spanned points?
#RQ2: How performance varies for different space of same shape?
#??? RQ3: How performance varies with removal of duplication/spanned
# This implies presence the spaces in space space folder
#NOTE: only 1-sub strategies are left
#NOTE: no rel-kn

algos=('{ "id": "s-0_dp_sp_nd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","sp", "nond", "kn"], ["dup","sp", "nond", "kn"], ["dup","sp", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_sp_ndXdm", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","sp", "nd", "kn"], ["dup","sp", "nd", "kn"], ["dup","sp", "nd", "kn"]]}]}}'
    '{ "id": "s-0_dp_sp_sXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","sp", "sd", "kn"], ["dup","sp", "sd", "kn"], ["dup","sp", "sd", "kn"]]}]}}'
    '{ "id": "s-0_dp_sp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","sp", "d", "kn"], ["dup","sp", "d", "kn"], ["dup","sp", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_sp_k-15_dp_sp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","sp","kn"], ["dup","sp","kn"], ["dup","sp","kn"]]}, {"t":15, "keys":[["dup","sp", "d", "kn"], ["dup","sp", "d", "kn"], ["dup","sp", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_sp_k-15_dp_sp_d!k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","sp","kn"], ["dup","sp","kn"], ["dup","sp","kn"]]}, {"t":15, "keys":[["dup","sp", "d", "kn"], ["dup","sp", "d", "kn"], ["dup","sp", "kn"]]}]}}'
    '{ "id": "s-0_dp_sp_dm", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","sp", "dom", "kn"], ["dup","sp", "dom", "kn"], ["dup","sp", "dom", "kn"]]}]}}'    
    '{ "id": "s-0_dp_sp_k-15_dp_sp_dm", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","sp","kn"], ["dup","sp","kn"], ["dup","sp","kn"]]}, {"t":15, "keys":[["dup","sp", "dom", "kn"], ["dup","sp", "dom", "kn"], ["dup","sp", "dom", "kn"]]}]}}'
    '{ "id": "s-0_dp_sp_k-15_dp_sp_dm!k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","sp","kn"], ["dup","sp","kn"], ["dup","sp","kn"]]}, {"t":15, "keys":[["dup","sp", "dom", "kn"], ["dup","sp", "dom", "kn"], ["dup","sp", "kn"]]}]}}')

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