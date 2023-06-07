set -e
pipenv shell 
flask DB-reboot
flask quiz init -nq 4 -nd 25 #search space size

flask quiz init -nq 2 -nd 10
# TODO - estimate search space size 
# TODO - estimate sampled number of individuals 

# flask student init -ns 100

flask student init -ns 20

# flask student knows -kr -ef 's{}@usf.edu' -k '{"sid":{"range":[1,10]},"qid":1,"did":4,"step":1,"metrics":{"chance":1}}' -k '{"sid":{"range":[1,20]},"qid":1,"did":8,"step":1,"metrics":{"chance":1}}' -k '{"sid":{"range":[11,20]},"qid":2,"did":12,"step":1,"metrics":{"chance":1}}' -k '{"sid":{"range":[1,20]},"qid":2,"did":16,"step":1,"metrics":{"chance":1}}'

# flask deca init -q 1 -o deca-spaces -a 2 -a 3 --spanned 1 --best-students-percent 0.1 --spanned-geometric-p 0.8 --noninfo 0.1 -n 1
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 3 -an 7 -an 10 \
    -as 1 -as 3 -as 5 \
    --num-spanned 0 --num-spanned 2 --num-spanned 20 \
    --num-spaces 3 \
    --best-students-percent 0.3 \
    --noninfo 0.3 \
    --timeout 1000 --random-seed 17

# local experimentation on 1 space
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --num-spanned 0 \
    --num-spaces 5 \
    --best-students-percent 0.1 \
    --noninfo 0.25 \
    --timeout 1000 --random-seed 17

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --num-spanned 5 \
    --num-spaces 5 \
    --best-students-percent 0.1 \
    --noninfo 0.25 \
    --timeout 1000 --random-seed 17    

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --num-spanned 10 \
    --num-spaces 5 \
    --best-students-percent 0.1 \
    --noninfo 0.25 \
    --timeout 1000 --random-seed 17       

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --num-spanned 20 \
    --num-spaces 5 \
    --best-students-percent 0.1 \
    --noninfo 0.25 \
    --timeout 1000 --random-seed 17      

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 4 \
    -as 3 \
    --num-spanned 50 \
    --num-spaces 5 \
    --best-students-percent 0.1 \
    --noninfo 0.25 \
    --timeout 1000 --random-seed 17     

    # --algo '{ "id": "rand-5", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 5}' \
    # --algo '{ "id": "pphc-1-2-1-3", "algo":"evopie.pphc_quiz_model.PphcQuizModel", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}' \

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --num-spanned 10 \
    --num-spaces 1 \
    --best-students-percent 0 \
    --noninfo 0.1 \
    --timeout 1000 --random-seed 17

#---------------- new deca spaces with strategies
# this is log of created deca spaces for experimentation at 23-04-30
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --spanned-strategy NONE\
    --num-spanned 0 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

#space s1-2
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --spanned-strategy BEST\
    --num-spanned 1 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --spanned-strategy "2AXES_BEST"\
    --num-spanned 10 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

#space s1-1
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --spanned-strategy "CENTER"\
    --num-spanned 2 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

#space s1-0
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --spanned-strategy "2AXES_BEST"\
    --num-spanned 1 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      


flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --spanned-strategy "2AXES_BEST"\
    --num-spanned 20 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 10 \
    -as 5 \
    --spanned-strategy "2AXES_BEST"\
    --num-spanned 5 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

# spaces 4x3
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 4 \
    -as 3 \
    --spanned-strategy NONE\
    --num-spanned 0 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

#space s1-2
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 4 \
    -as 3 \
    --spanned-strategy BEST\
    --num-spanned 1 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 4 \
    -as 3 \
    --spanned-strategy "2AXES_BEST"\
    --num-spanned 10 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

#space s1-1
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 4 \
    -as 3 \
    --spanned-strategy "CENTER"\
    --num-spanned 2 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

#space s1-0
flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 4 \
    -as 3 \
    --spanned-strategy "2AXES_BEST"\
    --num-spanned 1 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      


flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 4 \
    -as 3 \
    --spanned-strategy "2AXES_BEST"\
    --num-spanned 20 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 4 \
    -as 3 \
    --spanned-strategy "2AXES_BEST"\
    --num-spanned 5 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

flask deca init-many -ns 100 -nq 4 -nd 25 \
    -an 4 \
    -as 3 \
    --spanned-strategy "RANDOM"\
    --num-spanned 50 \
    --num-spaces 1 \
    --best-students-percent 0.05 \
    --noninfo 0.2 \
    --timeout 1000 --random-seed 29      

#----- 

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 2 \
    --algo '{ "id": "rand-3", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 3}' 

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "rand-3", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 3}' 

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "rand-3", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 3}' \
    --algo '{ "id": "s-nond-2", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination"}' \
    --algo '{ "id": "s-nond-2r", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination"}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "s-nond-2r", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination", "reduced_facts":true, "knowledge_annealing": 0.97}'
    
flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 2 \
    --algo '{ "id": "rand_s", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination", "knowledge_annealing": 0.99}'


flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "rand-3", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 3}' \
    --algo '{ "id": "s-nond", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination"}' \
    --algo '{ "id": "s-nond-a", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination", "knowledge_annealing": 0.995}' \
    --algo '{ "id": "s-nond-r", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination", "reduced_facts":true}' \
    --algo '{ "id": "s-nond-ar", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination", "reduced_facts":true, "knowledge_annealing": 0.995}' \
    --algo '{ "id": "s-nond-ab", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination", "alpha":0.75, "beta":2}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "s-nond2", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 3, "strategy": "non_domination", "knowledge_annealing": 0.95, "alpha":0.2, "beta":3, "gamma":0.2, "delta": 3}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "s-nond2", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 3, "strategy": "non_domination", "knowledge_annealing": 0.95, "alpha":0.2, "gamma":0.2}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "rand_s", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination", "knowledge_annealing": 0.99}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "rand-3", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 3}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "nond-1", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 1, "strategy": "non_domination"}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "nond-1b", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 1, "strategy": "non_domination", "sample_best_one":true}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "search", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 1, "strategy": "non_domination", "sample_best_one":true, "hyperparams": { "knowledge_annealing": 0.98 }}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "nond-2", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 2, "strategy": "non_domination"}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "nond-3", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 3, "strategy": "non_domination"}'

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "nond-4", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 4, "strategy": "non_domination"}'    

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "nond-5", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 5, "strategy": "non_domination"}'    

flask quiz deca-experiments \
    --deca-spaces deca-spaces \
    --algo-folder algo \
    --results-folder results \
    --random-seed 23 --num-runs 10 \
    --algo '{ "id": "nond-6", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "group_size": 6, "strategy": "non_domination"}'    

flask quiz deca-experiments \
    --random-seed 23 --num-runs 3 \
    --algo '{ "id": "pphc-1-2-1-3", "algo":"evopie.pphc_quiz_model.PphcQuizModel", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}'

flask quiz deca-experiment --deca-input deca-spaces/space-1_1_1_1_1_1_1_1-s_20-3.json \
    --num-runs 3 \
    --algo '{ "id": "pphc-1-2-1-3", "algo":"evopie.pphc_quiz_model.PphcQuizModel", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}'

flask quiz deca-experiment --deca-input deca-spaces/space-1_1_1_1_1_1_1_1-s_20-3.json \
    --num-runs 3 \
    --algo '{ "id": "s-nond", "algo":"evopie.sampling_quiz_model.SamplingQuizModel", "n": 3, "min_num_evals": 1, "group_size": 2, "strategy": "non_domination"}'

flask quiz deca-experiment --deca-input deca-spaces/space-1_1_1-s_0-2.json \
    --num-runs 2 \
    --algo '{ "id": "pphc-1-2-1-3", "algo":"evopie.pphc_quiz_model.PphcQuizModel", "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}'

flask quiz deca-experiment --deca-input deca-spaces/space-1_1_1-s_0-2.json \
    --num-runs 2 \
    --algo '{ "id": "rand-3", "algo":"evopie.rand_quiz_model.RandomQuizModel", "n": 3, "seed": 313}'


flask student knows -kr --deca-input deca-spaces/space-1_1_1-s_0-0.json \
    -o testing/students.csv

# flask quiz run -q 1 -s STEP1 --algo 'evopie.pphc_quiz_model.PphcQuizModel' --algo-params '{ "pop_size": 1, "pareto_n": 2, "child_n": 1, "gene_size": 3}' \
#     --evo-output algo/pphc-1-2-1-3.json --archive-output algo/pphc-1-2-1-3-archive.csv

flask deca result --algo-input algo/pphc-1-2-1-3.json --deca-space deca-spaces/space-1_1_1_1_1_1_1_1-s_20-3.json \
    -p explored_search_space_size -p search_space_size -io results/x.csv

# flask quiz post-process --result-folder results --figure-folder figures -p dim_coverage

flask quiz post-process --result-folder data/data-8/results --figure-folder figures --file-name-pattern '.*_20-\d+.csv' \
  -p dim_coverage -p arr -p population_redundancy -p deca_redundancy -p num_spanned \
  -p deca_duplication -p population_duplication -p noninfo \
  --group-by-space

flask quiz post-process --result-folder data/data-2/results --figure-folder figures --file-name-pattern '.*_0-\d+.csv' \
  -p population_duplication --group-by-space


flask quiz post-process --result-folder data/data-2022-08-08/data-2/results --figure-folder figures --file-name-pattern '.*_0-\d+.csv' \
  -p dim_coverage -p arr -p population_redundancy -p deca_redundancy -p num_spanned \
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

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2022-10-03 --path-suffix results --figure-folder figures --file-name-pattern 'rand-quiz-5-.*-s_0-\d+.csv' \
  -p dim_coverage -pt 'Dimension coverage' --fixate-range  --fig-name rand-quiz-5-dim-coverage

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2022-10-03 --path-suffix results --figure-folder figures --file-name-pattern 'rand-quiz-3-.*-s_0-\d+.csv' \
  -p dim_coverage -pt 'Dimension coverage' --fixate-range  --fig-name rand-quiz-3-dim-coverage  

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2022-10-03 --path-suffix results --figure-folder figures --file-name-pattern 'pphc-1-2-1-3-.*-s_0-\d+.csv' \
  -p dim_coverage -pt 'Dimension coverage' --fixate-range  --fig-name pphc-1-2-1-3-dim-coverage    

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2022-10-03 --path-suffix results --figure-folder figures --file-name-pattern 'rand-quiz-5-.*-s_0-\d+.csv' \
  -p arr -pt 'Average rank of representatives' --fixate-range  --fig-name rand-quiz-5-arr

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2022-10-03 --path-suffix results --figure-folder figures --file-name-pattern 'rand-quiz-3-.*-s_0-\d+.csv' \
  -p arr -pt 'Average rank of representatives' --fixate-range  --fig-name rand-quiz-3-arr

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2022-10-03 --path-suffix results --figure-folder figures --file-name-pattern 'pphc-1-2-1-3-.*-s_0-\d+.csv' \
  -p arr -pt 'Average rank of representatives' --fixate-range  --fig-name pphc-1-2-1-3-arr

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2022-10-03 --path-suffix results --figure-folder figures --file-name-pattern 'rand-quiz-5-.*-s_0-\d+.csv' \
  -p population_redundancy -pt 'Redundancy' --fixate-range  --fig-name rand-quiz-5-R

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2022-10-03 --path-suffix results --figure-folder figures --file-name-pattern 'rand-quiz-3-.*-s_0-\d+.csv' \
  -p population_redundancy -pt 'Redundancy' --fixate-range  --fig-name rand-quiz-3-R

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2022-10-03 --path-suffix results --figure-folder figures --file-name-pattern 'pphc-1-2-1-3-.*-s_0-\d+.csv' \
  -p population_redundancy -pt 'Redundancy' --fixate-range  --fig-name pphc-1-2-1-3-R  

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2022-10-03 --path-suffix results \
  --figure-folder figures --file-name-pattern '(?P<algo>.*)-on-space-.*-s_(?P<spanned>.*)-\d+.csv' \
  -p dim_coverage -pt 'Dimension coverage' \
  -p arr -pt 'Average rank of representatives' \
  -p population_redundancy -pt 'Redundancy' \
  -p population_duplication -pt 'Duplication' \
  -p noninfo -pt 'Non-informativeness' \
  --fig-name "<algo>-<param>-<spanned>" \
  --fixate-range > res.txt

flask quiz plot-metric-vs-num-of-dims --data-folder data/data-2023-02-12 --path-suffix results \
  --figure-folder figures --file-name-pattern '(?P<algo>.*)-on-space-.*-s_(?P<spanned>.*)-\d+.csv' \
  -p dim_coverage -pt 'Dimension coverage' \
  -p arr -pt 'Average rank of representatives' \
  -p population_redundancy -pt 'Redundancy' \
  -p population_duplication -pt 'Duplication' \
  -p noninfo -pt 'Non-informativeness' \
  --fig-name "<algo>-<param>-<spanned>" \
  --fixate-range > res.txt

flask deca space-result -r results

flask deca space-result -r results -s D -f D

flask deca space-result -r data/data-2023-03-24 -s ARRA -f ARRA


flask deca space-result -r data/data-2023-04-06 -s ARRA -f ARRA

flask deca space-result -r data/data-2023-04-06 -s ARRA -f ARRA --stats-column arra


flask deca space-result -r data/data-2023-05-01 --no-group -s ARRA -f ARRA --stats-column arra