#!/bin/bash 
#SBATCH --job-name=deca-spaces
#SBATCH --time=24:00:00
#SBATCH --output=deca-spaces-%a.out
#SBATCH --mem=8G
#SBATCH --array=2-10

cd ~/evopie 
echo "Workign in $WORK/evopie/data-$SLURM_ARRAY_TASK_ID"
export EVOPIE_DATABASE_URI=sqlite:///$WORK/evopie/data-$SLURM_ARRAY_TASK_ID/db.sqlite
export PYTHONPATH=$(pipenv run which python)
pipenv run flask quiz deca-experiments \
    --deca-spaces $WORK/evopie/data-$SLURM_ARRAY_TASK_ID/deca-spaces \
    --algo-folder $WORK/evopie/data-$SLURM_ARRAY_TASK_ID/algo \
    --results-folder $WORK/evopie/data-$SLURM_ARRAY_TASK_ID/results \
    --random-seed 23 --num-runs 30 \
    --algo '{ "id": "pphc-1-2-1-3", "algo":"P_PHC", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}'

