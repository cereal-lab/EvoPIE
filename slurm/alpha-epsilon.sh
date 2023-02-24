#!/bin/bash 
#SBATCH --job-name=pswp-a-e
#SBATCH --time=72:00:00
#SBATCH --output=pswp-a-e.out
#SBATCH --mem=8G
#SBATCH --array=0-24

alphas=(0 0.5 1 2 10)
betas=(0 0.5 1 2 10)

alpha_id=$(($SLURM_ARRAY_TASK_ID / 5))
beta_id=$(($SLURM_ARRAY_TASK_ID % 5))
alpha=${alphas[$alpha_id]}
beta=${alphas[$beta_id]}

cd ~/evopie 
echo "Working in $WORK/evopie/pswp-a-e/ alpha $alpha beta $beta"
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
    --random-seed 23 --num-runs 10 \
    --algo "{\"id\":\"n-${alpha/./_}-${beta/./_}\",\"algo\":\"evopie.sampling_quiz_model.SamplingQuizModel\",\"n\":3,\"group_size\":2,\"strategy\":\"non_domination\",\"hyperparams\":{\"alpha\":$alpha,\"beta\":$beta}}"