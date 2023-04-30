#!/bin/bash 
#SBATCH --job-name=e-smpl
#SBATCH --time=72:00:00
#SBATCH --output=e-smpl-%a.out
#SBATCH --mem=8G
#SBATCH --array=0-21

algos=('{ "id": "rand-3", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 3}'
    '{ "id": "s-0k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}]}}'
    '{ "id": "s-0n", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nond", "sd", "kn"], ["nond", "sd", "rel-kn", "kn"], ["nond", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["d", "kn"], ["d", "rel-kn", "kn"], ["d", "rel-kn", "kn"]]}]}}'    
    '{ "id": "s-0nXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nd", "sd", "kn"], ["nd", "sd", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0ndk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nond", "sd", "kn"], ["d", "kn"], ["rel-kn", "kn"]]}]}}'
    '{ "id": "s-0nXdsXdk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nd", "sd", "kn"], ["sd", "nd", "kn"], ["rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-25n", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":25, "keys":[["nond", "sd", "kn"], ["nond", "sd", "rel-kn", "kn"], ["nond", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-25d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":25, "keys":[["d", "kn"], ["d", "rel-kn", "kn"], ["d", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-25nXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":25, "keys":[["nd", "sd", "kn"], ["nd", "sd", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-25ndk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":25, "keys":[["nond", "sd", "kn"], ["d", "kn"], ["rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-25nXdsXdk", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":25, "keys":[["nd", "sd", "kn"], ["sd", "nd", "kn"], ["rel-kn", "kn"]]}]}}'
    '{ "id": "s-0dn-25nd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nond", "sd", "rel-kn", "kn"], ["d", "kn"], ["-s", "kn"]]}, {"t":25, "keys":[["nond", "sd", "rel-kn", "kn"], ["d", "rel-kn", "kn"], ["nond", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0dnXd-25nXdd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nd", "sd", "rel-kn", "kn"], ["d", "kn"], ["-s", "kn"]]}, {"t":25, "keys":[["nd", "sd", "rel-kn", "kn"], ["d", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-17nk-34n", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":17, "keys":[["nond", "sd", "kn"], ["nond", "sd", "rel-kn", "kn"], ["rel-kn", "kn", "nond", "sd"]]}, {"t":34, "keys":[["nond", "sd", "kn"], ["nond", "sd", "rel-kn", "kn"], ["nond", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-17dk-34d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":17, "keys":[["d", "kn"], ["d", "rel-kn", "kn"], ["rel-kn", "kn", "d"]]}, {"t":34, "keys":[["d", "kn"], ["d", "rel-kn", "kn"], ["d", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-17nXdk-34nXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":17, "keys":[["nd", "sd", "kn"], ["nd", "sd", "rel-kn", "kn"], ["rel-kn", "kn", "nd", "sd"]]}, {"t":34, "keys":[["nd", "sd", "kn"], ["nd", "sd", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0k-17nXd-34nXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":17, "keys":[["nd", "sd", "rel-kn", "kn"], ["rel-kn", "nd", "sd", "kn"], ["rel-kn", "kn", "nd", "sd"]]}, {"t":34, "keys":[["nd", "sd", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"], ["rel-kn", "kn", "nd", "sd"]]}]}}'
    '{ "id": "s-0nXd-17nXd-34nXd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nd", "sd", "rel-kn", "kn"], ["rel-kn", "kn", "nd", "sd"], ["rel-kn", "kn", "nd", "sd"]]}, {"t":17, "keys":[["nd", "sd", "rel-kn", "kn"], ["rel-kn", "nd", "sd", "kn"], ["rel-kn", "kn", "nd", "sd"]]}, {"t":34, "keys":[["nd", "sd", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"], ["nd", "rel-kn", "sd", "kn"]]}]}}'        
    '{ "id": "s-0k-17d-34d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":17, "keys":[["d", "kn"], ["rel-kn", "d", "kn"], ["rel-kn", "kn", "d"]]}, {"t":34, "keys":[["d", "kn"], ["d", "rel-kn", "kn"], ["d", "rel-kn", "kn"]]}]}}'    
    '{ "id": "s-0k-17dn-34nd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":17, "keys":[["nond", "sd", "rel-kn", "kn"], ["d", "kn"], ["d", "rel-kn", "kn"]]}, {"t":34, "keys":[["nond", "sd", "rel-kn", "kn"], ["d", "rel-kn", "kn"], ["nond", "sd", "rel-kn", "kn"]]}]}}'    
    '{ "id": "s-0k-17dnXd-34nXdd", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["kn", "rel-kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}, {"t":17, "keys":[["nd", "sd", "rel-kn", "kn"], ["d", "kn"], ["d", "rel-kn", "kn"]]}, {"t":34, "keys":[["nd", "sd", "rel-kn", "kn"], ["d", "rel-kn", "kn"], ["nd", "sd", "rel-kn", "kn"]]}]}}') 

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