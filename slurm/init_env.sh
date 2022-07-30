set -e
# this script should be run manually
# script to init evopie env for experimentation: python > 3.8 should be installed, git
# run it in folder where you want to deploy sources and cli of evopie 
# requirements: git, python > 3.8, pipenv already should be installed 
git clone https://github.com/cereal-lab/EvoPIE.git $1
cd $1
git checkout -b experiments remotes/origin/79-validate-baseline-pphc-ability-to-approximate-underlying-deca-coordinates-system
pipenv shell 
#next is neccessary to install correct versions of dependencies  
export PYTHONPATH=$(which python)
pipenv sync 
./test.sh 