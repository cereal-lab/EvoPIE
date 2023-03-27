#!/bin/bash 
#SBATCH --job-name=e-smpl
#SBATCH --time=72:00:00
#SBATCH --output=e-smpl-%a.out
#SBATCH --mem=8G
#SBATCH --array=0-15

algos=('{ "id": "rand-3", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 3}'
    '{ "id": "s-0n", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nond", "sd", "kn"], ["nond", "sd", "rel-kn", "kn"], ["nond", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-25n", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "nond"], ["rel-kn", "kn", "nond"], ["rel-kn", "kn", "sd"]]}, {"t":25, "keys":[["nond", "kn", "sd"], [ "sd", "rel-kn", "kn", "nond"], ["rel-kn", "nond", "sd"]]}]}}'
    '{ "id": "s-0k-20n-40n", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":20, "keys":[["nond", "sd", "rel-kn", "kn"], ["rel-kn", "nond", "sd", "kn"], ["rel-kn", "kn", "nond", "sd"]]}, {"t":40, "keys":[["nond", "sd", "rel-kn", "kn"], ["nond", "sd", "rel-kn", "kn"], ["rel-kn", "kn", "nond", "sd"]]}]}}'
    '{ "id": "s-0n-20n-40n", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nond", "sd", "rel-kn", "kn"], ["rel-kn", "kn", "nond", "sd"], ["rel-kn", "kn", "nond", "sd"]]}, {"t":20, "keys":[["nond", "sd", "rel-kn", "kn"], ["rel-kn", "nond", "sd", "kn"], ["rel-kn", "kn", "nond", "sd"]]}, {"t":40, "keys":[["nond", "sd", "rel-kn", "kn"], ["nond", "sd", "rel-kn", "kn"], ["nond", "rel-kn", "sd", "kn"]]}]}}'
    '{ "id": "s-0nXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nd", "sd", "kn"], ["nd", "sd", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-25nXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "nd"], ["rel-kn", "kn", "nd"], ["rel-kn", "kn", "sd"]]}, {"t":25, "keys":[["nd", "kn", "sd"], [ "sd", "rel-kn", "kn", "nd"], ["rel-kn", "nd", "sd"]]}]}}'
    '{ "id": "s-0k-20nXd-40nXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":20, "keys":[["nd", "sd", "rel-kn", "kn"], ["rel-kn", "nd", "sd", "kn"], ["rel-kn", "kn", "nd", "sd"]]}, {"t":40, "keys":[["nd", "sd", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"], ["rel-kn", "kn", "nd", "sd"]]}]}}'
    '{ "id": "s-0nXd-20nXd-40nXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nd", "sd", "rel-kn", "kn"], ["rel-kn", "kn", "nd", "sd"], ["rel-kn", "kn", "nd", "sd"]]}, {"t":20, "keys":[["nd", "sd", "rel-kn", "kn"], ["rel-kn", "nd", "sd", "kn"], ["rel-kn", "kn", "nd", "sd"]]}, {"t":40, "keys":[["nd", "sd", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"], ["nd", "rel-kn", "sd", "kn"]]}]}}'
    '{ "id": "s-0d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["d", "kn"], ["d", "rel-kn", "kn"], ["d", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-25d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "d"], ["rel-kn", "kn", "d"], ["rel-kn", "kn", "d"]]}, {"t":25, "keys":[["d", "kn"], ["d", "rel-kn", "kn"], ["d", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-20d-40d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "d"], ["rel-kn", "kn", "d"], ["rel-kn", "kn", "d"]]}, {"t":20, "keys":[["d", "kn"], ["rel-kn", "d", "kn"], ["rel-kn", "kn", "d"]]}, {"t":40, "keys":[["d", "kn"], ["d", "rel-kn", "kn"], ["d", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0dn-25nd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nond", "sd", "rel-kn", "kn"], ["d", "kn"], ["-s", "kn"]]}, {"t":25, "keys":[["nond", "sd", "rel-kn", "kn"], ["d", "rel-kn", "kn"], ["nond", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-20dn-40nd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "nond"], ["rel-kn", "kn", "nond"], ["rel-kn", "kn", "d"]]}, {"t":20, "keys":[["nond", "sd", "rel-kn", "kn"], ["d", "kn"], ["d", "rel-kn", "kn"]]}, {"t":40, "keys":[["nond", "sd", "rel-kn", "kn"], ["d", "rel-kn", "kn"], ["nond", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0dnXd-25nXdd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nd", "sd", "rel-kn", "kn"], ["d", "kn"], ["-s", "kn"]]}, {"t":25, "keys":[["nd", "sd", "rel-kn", "kn"], ["d", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-20dnXd-40nXdd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "nd"], ["rel-kn", "kn", "nd"], ["rel-kn", "kn", "d"]]}, {"t":20, "keys":[["nd", "sd", "rel-kn", "kn"], ["d", "kn"], ["d", "rel-kn", "kn"]]}, {"t":40, "keys":[["nd", "sd", "rel-kn", "kn"], ["d", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"]]}]}}') 

algo=${algos[$SLURM_ARRAY_TASK_ID]}

cd ~/evopie 
echo "Working in $WORK/evopie/pswp-a-e/ algo $algo"
export EVOPIE_DATABASE_URI=sqlite:///$WORK/evopie/pswp-a-e/db-$SLURM_ARRAY_TASK_ID.sqlite
# export EVOPIE_DATABASE_LOG=$WORK/evopie/data-$SLURM_ARRAY_TASK_ID/db.log
export PYTHONPATH=$(pipenv run which python)

pipenv run flask DB-reboot 
pipenv run flask quiz init -nq 4 -nd 25 #search space size
pipenv run flask student init -ns 100

pipenv run flask quiz deca-experiments \
    --deca-spaces $WORK/evopie/spaces \
    --algo-folder $WORK/evopie/tmp-algo \
    --results-folder $WORK/evopie/results \
    --random-seed 23 --num-runs 5 \
    --algo "$algo"