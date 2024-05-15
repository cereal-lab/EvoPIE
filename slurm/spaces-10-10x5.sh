#!/bin/bash 
#SBATCH --job-name=deca-spaces
#SBATCH --time=12:00:00
#SBATCH --output=spaces-10-10x5-%a.out
#SBATCH --mem=4G

cd ~/evopie 
echo "Creating spaces spaces-10-10x5"
export EVOPIE_DATABASE_URI=sqlite:///$WORK/evopie/db.sqlite
export PYTHONPATH=$(pipenv run which python)
pipenv run flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --spanned-strategy NONE\
    --num-spanned 0 \
    --num-spaces 10 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29 --output-folder $WORK/evopie/spaces

