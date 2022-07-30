#!/bin/bash 
#SBATCH --job-name=deca-spaces
#SBATCH --time=12:00:00
#SBATCH --output=deca-spaces-%a.out
#SBATCH --mem=4G
#SBATCH --array=2-10

echo "Creating spaces in $WORK/evopie/data-$SLURM_ARRAY_TASK_ID"
mkdir -p $WORK/evopie/data-$SLURM_ARRAY_TASK_ID
export EVOPIE_DATABASE_URI=sqlite:///$WORK/evopie/data-$SLURM_ARRAY_TASK_ID/db.sqlite
pipenv run flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an $SLURM_ARRAY_TASK_ID \
    -as 1 -as 3 -as 5 \
    --num-spanned 0 --num-spanned 2 --num-spanned 20 \
    --num-spaces 10 \
    --best-students-percent 0.3 \
    --noninfo 0.3 \
    --timeout 1000 --random-seed 17 \
    --output-folder $WORK/evopie/data-$SLURM_ARRAY_TASK_ID/deca-spaces

