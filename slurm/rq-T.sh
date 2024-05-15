#!/bin/bash 
#SBATCH --job-name=rq-T
#SBATCH --time=72:00:00
#SBATCH --output=rq-T-%a.out
#SBATCH --mem=8G
#SBATCH --array=0-17

#RQ1: What is the best (in terms ARR*) algo (no multi-step) on spaces without spanned points?
#RQ2: How performance varies for different space of same shape?
#??? RQ3: How performance varies with removal of duplication/spanned
# This implies presence the spaces in space space folder
#NOTE: only 1-sub strategies are left
#NOTE: no rel-kn

algos=('{ "id": "s-0_dp_k-5_dp_nd_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]},  {"t": 5, "keys":[["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-10_dp_nd_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":10, "keys":[["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-15_dp_nd_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":15, "keys":[["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-20_dp_nd_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":20, "keys":[["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-25_dp_nd_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":25, "keys":[["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-30_dp_nd_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":30, "keys":[["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-35_dp_nd_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":35, "keys":[["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-40_dp_nd_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":40, "keys":[["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-45_dp_nd_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":45, "keys":[["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"], ["dup", "nond", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-5_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]},  {"t": 5, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-10_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":10, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-15_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":15, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-20_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":20, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-25_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":25, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-30_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":30, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-35_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":35, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-40_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":40, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_k-45_dp_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup","kn"], ["dup","kn"], ["dup","kn"]]}, {"t":45, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}')

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