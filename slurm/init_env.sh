#!/bin/bash 
set -e
# script to init evopie env for experimentation: python > 3.8 should be installed, git
# run it in folder where you want to deploy sources and cli of evopie 
# requirements: git, python > 3.8, pipenv already should be installed 
git clone https://github.com/cereal-lab/EvoPIE.git . 
pipenv shell
#next is neccessary to install correct versions of dependencies  
export PYTHONPATH=$(which python)
pipenv sync 
./test.sh 