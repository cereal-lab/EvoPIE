set -e
pipenv shell 
flask DB-reboot
flask quiz init -nq 4 -nd 25 #search space size

flask quiz init -nq 2 -nd 10
# TODO - estimate search space size 
# TODO - estimate sampled number of individuals 

# flask student init -ns 100

flask student init -ns 20

# flask student knows -kr -ef 's{}@usf.edu' -k '{"sid":{"range":[1,10]},"qid":1,"did":4,"step":1,"chance":1}' -k '{"sid":{"range":[1,20]},"qid":1,"did":8,"step":1,"chance":1}' -k '{"sid":{"range":[11,20]},"qid":2,"did":12,"step":1,"chance":1}' -k '{"sid":{"range":[1,20]},"qid":2,"did":16,"step":1,"chance":1}'

# flask student knows -kr -ef 's{}@usf.edu' -k '{"sid":{"range":[1,10]},"qid":1,"did":4,"step":1,"chance":1}' -k '{"sid":{"range":[1,20]},"qid":1,"did":8,"step":1,"chance":1}' -k '{"sid":{"range":[11,20]},"qid":2,"did":12,"step":1,"chance":1}' -k '{"sid":{"range":[1,20]},"qid":2,"did":16,"step":1,"chance":1}'

# flask deca init -q 1 -o deca-spaces -a 2 -a 3 --spanned 1 --best-students-percent 0.1 --spanned-geometric-p 0.8 --noninfo 0.1 -n 1
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 3 -an 7 -an 10 \
    -as 1 -as 3 -as 5 \
    --num-spanned 0 --num-spanned 2 --num-spanned 20 \
    --num-spaces 3 \
    --best-students-percent 0.3 \
    --noninfo 0.3 \
    --timeout 1000 --random-seed 17
 
flask quiz deca-experiments \
    --random-seed 23 --num-runs 3 \
    --algo '{ "id": "pphc-1-2-1-3", "algo":"P_PHC", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}'

flask quiz deca-experiment --deca-input deca-spaces/space-1_1_1_1_1_1_1_1-s_20-3.json \
    --num-runs 3 \
    --algo '{ "id": "pphc-1-2-1-3", "algo":"P_PHC", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}'

flask student knows --deca-input deca-spaces/space-1_1_1_1_1_1_1_1-s_0-1.json \
    -o testing/students.csv

flask quiz run -q 1 -s STEP1 --algo P_PHC --algo-params '{ "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}' \
    --evo-output algo/pphc-1-2-1-3.json --archive-output algo/pphc-1-2-1-3-archive.csv

flask quiz run -q 1 -s STEP1 --algo P_PHC --algo-params '{ "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}' \
    --evo-output algo/pphc-1-2-1-3.json --archive-output algo/pphc-1-2-1-3-archive.csv

flask quiz run -q 1 -s STEP1 --algo RandomQuiz --algo-params '{ "n": 4, "seed": 17 }' \
    --evo-output algo/pphc-1-2-1-3.json --archive-output algo/pphc-1-2-1-3-archive.csv    

flask deca result --algo-input algo/pphc-1-2-1-3.json --deca-space deca-spaces/space-1_1_1_1_1_1_1_1-s_20-3.json \
    -p explored_search_space_size -p search_space_size -io results/x.csv

# flask quiz post-process --result-folder results --figure-folder figures -p dim_coverage

flask quiz post-process --result-folder data/data-8/results --figure-folder figures --file-name-pattern '.*_20-\d+.csv' \
  -p dim_coverage -p dim_coverage_with_spanned -p arr -p arr_with_spanned -p population_redundancy -p deca_redundancy -p num_spanned \
  -p deca_duplication -p population_duplication -p noninfo \
  --group-by-space

flask quiz post-process --result-folder data/data-2/results --figure-folder figures --file-name-pattern '.*_0-\d+.csv' \
  -p population_duplication --group-by-space


flask quiz post-process --result-folder data/data-2022-08-08/data-2/results --figure-folder figures --file-name-pattern '.*_0-\d+.csv' \
  -p dim_coverage -p dim_coverage_with_spanned -p arr -p arr_with_spanned -p population_redundancy -p deca_redundancy -p num_spanned \
  -p deca_duplication -p population_duplication -p noninfo

flask quiz post-process --result-folder data/data-2022-08-08/data-2/results --figure-folder figures --file-name-pattern '.*_0-\d+.csv' \
  -p dim_coverage -p arr -p population_duplication -p noninfo  

flask quiz post-process --result-folder data/data-2022-08-08/data-10/results --figure-folder figures --file-name-pattern '.*_0-\d+.csv' \
  -p dim_coverage -p arr -p population_duplication -p noninfo  

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_0-\d+.csv' \
  -p dim_coverage -pt 'Dimension coverage'

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_0-\d+.csv' \
  -p arr -pt 'Average rank of representatives'

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_0-\d+.csv' \
  -p noninfo -pt 'Non-informativeness'  

flask quiz post-process --result-folder data/data-2022-08-08/data-5/results --figure-folder figures --file-name-pattern '.*_2-\d+.csv' \
  -p dim_coverage -p arr -p population_redundancy -p population_duplication -p noninfo  

flask quiz post-process --result-folder data/data-2022-08-08/data-10/results --figure-folder figures --file-name-pattern '.*_2-\d+.csv' \
  -p dim_coverage -p arr -p population_redundancy -p population_duplication -p noninfo     

flask quiz post-process --result-folder data/data-2022-08-08/data-2/results --figure-folder figures --file-name-pattern '.*_20-\d+.csv' \
  -p dim_coverage -p arr -p population_redundancy -p population_duplication -p noninfo      


flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_2-\d+.csv' \
  -p dim_coverage -pt 'Dimension coverage'

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_2-\d+.csv' \
  -p arr -pt 'Average rank of representatives'

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_2-\d+.csv' \
  -p population_redundancy -pt 'Redundancy'  --fixate-range

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_2-\d+.csv' \
  -p population_duplication -pt 'Duplication' --fixate-range

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_2-\d+.csv' \
  -p noninfo -pt 'Non-informativeness'  --fixate-range


flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_20-\d+.csv' \
  -p dim_coverage -pt 'Dimension coverage'

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_20-\d+.csv' \
  -p arr -pt 'Average rank of representatives' --fixate-range

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_20-\d+.csv' \
  -p population_redundancy -pt 'Redundancy'  --fixate-range

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_20-\d+.csv' \
  -p population_duplication -pt 'Duplication' --fixate-range

flask quiz plot-metric-vs-num-of-dims -p dim_coverage --data-folder data/data-2022-08-08 --path-suffix results --figure-folder figures --file-name-pattern '.*-s_20-\d+.csv' \
  -p noninfo -pt 'Non-informativeness'  --fixate-range  