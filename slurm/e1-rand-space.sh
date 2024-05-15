#!/bin/bash 
#SBATCH --job-name=e-smpl
#SBATCH --time=72:00:00
#SBATCH --output=e-smpl-%a.out
#SBATCH --mem=8G
#SBATCH --array=0-15

algos=('{ "id": "rand-3", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 3}'
    '{ "id": "s-0_k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["rel-kn", "kn"], ["rel-kn", "kn"], ["rel-kn", "kn"]]}]}}'
    '{ "id": "s-0_dup_k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dup", "rel-kn", "kn"], ["dup", "rel-kn", "kn"], ["dup", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0_sp_k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["sp", "rel-kn", "kn"], ["sp", "rel-kn", "kn"], ["sp", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0_d_k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["d", "rel-kn", "kn"], ["d", "rel-kn", "kn"], ["d", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0_dom_k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["dom", "rel-kn", "kn"], ["dom", "rel-kn", "kn"], ["dom", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0_nond_k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["nond", "rel-kn", "kn"], ["nond", "rel-kn", "kn"], ["nond", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0_sp_dup_d_k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["sp", "dup", "d", "rel-kn", "kn"], ["sp", "dup", "d", "rel-kn", "kn"], ["sp", "dup", "d", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0_sp_dup_dom_k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["sp", "dup", "dom", "rel-kn", "kn"], ["sp", "dup", "dom", "rel-kn", "kn"], ["sp", "dup", "dom", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0_sp_dup_d|k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["sp", "dup", "d", "rel-kn", "kn"], ["sp", "dup", "d", "rel-kn", "kn"], ["sp", "dup", "rel-kn", "kn", "d"]]}]}}'
    '{ "id": "s-0_sp_dup_k|d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["sp", "dup", "rel-kn", "kn", "d"], ["sp", "dup", "rel-kn", "kn", "d"], ["sp", "dup", "d", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0_sp_dup_d|k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["sp", "dup", "d", "rel-kn", "kn"], ["sp", "dup", "d", "rel-kn", "kn"], ["sp", "dup", "rel-kn", "kn", "d"]]}]}}'
    '{ "id": "s-0_sp_dup_k|d-25_sp_dup_d|k", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["sp", "dup", "rel-kn", "kn", "d"], ["sp", "dup", "rel-kn", "kn", "d"], ["sp", "dup", "d", "rel-kn", "kn"]]}, {"t":25, "keys":[["sp", "dup", "rel-kn", "kn", "d"], ["sp", "dup", "rel-kn", "kn", "d"], ["sp", "dup", "d", "rel-kn", "kn"]]}]}}'
    '{ "id": "s-0_sp_dup_k-25_sp_dup_d", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "slot_based", "hyperparams": { "key_spec": [{"t":0, "keys":[["sp", "dup", "rel-kn", "kn", "d"], ["sp", "dup", "rel-kn", "kn", "d"], ["sp", "dup", "rel-kn", "kn", "d"]]}, {"t":25, "keys":[["sp", "dup", "d", "rel-kn", "kn"], ["sp", "dup", "d", "rel-kn", "kn"], ["sp", "dup", "d", "rel-kn", "kn"]]}]}}'
    '{ "id": "phc-1-2-1-2-r", "algo":"evopie.pphc_quiz_model.PphcQuizModel", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 2, "mutation": "mutate_random"}'
    '{ "id": "phc-1-2-1-2-b", "algo":"evopie.pphc_quiz_model.PphcQuizModel", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 2, "mutation": "mutate_one_point_worst_to_best"}') 

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