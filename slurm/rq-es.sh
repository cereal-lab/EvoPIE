#!/bin/bash 
#SBATCH --job-name=rq-es
#SBATCH --time=72:00:00
#SBATCH --output=rq-es-%a.out
#SBATCH --mem=8G
#SBATCH --array=0-15

algos=('{ "id": "s-0_dp_nd!e10", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "epsilon": 0.1, "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_nd!e20", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "epsilon": 0.2, "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_nd!e30", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "epsilon": 0.3, "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_nd!e40", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "epsilon": 0.4, "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_nd!e50", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "epsilon": 0.5, "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_d!e10", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "epsilon": 0.1, "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_d!e20", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "epsilon": 0.2, "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_d!e30", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "epsilon": 0.3, "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_d!e40", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "epsilon": 0.4, "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_d!e50", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "epsilon": 0.5, "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_nd!s_1", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "softmax": "nond", "tau": 0.1, "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_nd!s1", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "softmax": "nond", "tau": 1, "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_nd!s10", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "softmax": "nond", "tau": 10, "key_spec": [{"t":0, "keys":[["dup", "nond", "kn"], ["dup", "nond", "kn"], ["dup", "nond", "kn"]]}]}}'
    '{ "id": "s-0_dp_d!s_1", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "softmax": "nond", "tau": 0.1, "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_d!s1", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "softmax": "nond", "tau": 1, "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}'
    '{ "id": "s-0_dp_d!s10", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "softmax": "nond", "tau": 10, "key_spec": [{"t":0, "keys":[["dup", "d", "kn"], ["dup", "d", "kn"], ["dup", "d", "kn"]]}]}}')

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