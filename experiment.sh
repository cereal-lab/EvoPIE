set -e
pipenv shell 
flask DB-reboot
flask quiz init -nq 3 -nd 10 #search space size
# TODO - estimate search space size 
# TODO - estimate sampled number of individuals 

flask student init -ns 100

flask deca init -q 1 -o deca-spaces -a 2 -a 3 --spanned 1 --best-students-percent 0.1 --spanned-geometric-p 0.8 --noninfo 0.1 -n 1

flask student knows --deca-input deca-spaces/space-0.json -o testing/students.csv

flask quiz run -q 1 -s STEP1 --algo P_PHC --algo-params '{ "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}' \
    --evo-output algo/pphc-1-2-1-3.json --archive-output algo/pphc-1-2-1-3-archive.csv

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 3 -an 7 -an 10 \
    -as 1 -as 3 -as 5 \
    --num-spanned 0 --num-spanned 2 --num-spanned 20 \
    --num-spaces 3 \
    --best-students-percent 0.3 \
    --noninfo 0.3 \
    --timeout 1000 --random-seed 17

flask deca result --algo-input algo/pphc-1-2-1-3.json --deca-space deca-spaces/space-0.json \
    -p explored_search_space_size -p search_space_size -io results/pphc-1-2-1-3-on-space-0.csv