#!/bin/bash 
#SBATCH --job-name=deca-vs-pphc
#SBATCH --time=72:00:00
#SBATCH --output=deca-vs-pphc-%a.out
#SBATCH --mem=8G
#SBATCH --array=2-10

cd ~/evopie 
echo "Working in $WORK/evopie/data-$SLURM_ARRAY_TASK_ID"
export EVOPIE_DATABASE_URI=sqlite:///$WORK/evopie/data-$SLURM_ARRAY_TASK_ID/db.sqlite
# export EVOPIE_DATABASE_LOG=$WORK/evopie/data-$SLURM_ARRAY_TASK_ID/db.log
export PYTHONPATH=$(pipenv run which python)
pipenv run flask quiz deca-experiments \
    --deca-spaces $WORK/evopie/data-$SLURM_ARRAY_TASK_ID/deca-spaces \
    --algo-folder $WORK/evopie/data-$SLURM_ARRAY_TASK_ID/algo \
    --results-folder $WORK/evopie/data-$SLURM_ARRAY_TASK_ID/results \
    --random-seed 23 --num-runs 30 \
    --algo '{ "id": "rand-quiz-3", "algo":"RandomQuiz", "n": 3 }' \
    --algo '{ "id": "rand-quiz-5", "algo":"RandomQuiz", "n": 5 }' \
    --algo '{ "id": "pphc-1-2-1-3", "algo":"P_PHC", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}'

