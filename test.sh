flask DB-reboot
flask quiz init -nq 5 -nd 4 -qd '{"2":[5,6,7],"3":[9,10,11],"4":[13,14,16]}'

#user id 1 is reserved for instructor in this test
flask student init -ns 20 --exclude-id 12 -kr -ef 'student{}@usf.edu' -k '{"sid":{"range":[1,4]},"qid":1,"did":3,"step":1,"chance":1}' \
    -k '{"sid":{"ranges":[[1,4],[10,18]]},"qid":2,"did":7,"step":1,"chance":1}' \
    -k '{"sid":{"range":[1,9]},"qid":3,"did":11,"step":1,"chance":1}' \
    -k '{"sid":{"range":[1,9]},"qid":4,"did":13,"step":1,"chance":1}' \
    -k '{"sid":{"range":[1,18]},"qid":5,"did":17,"step":1,"chance":1}' \
    -k '{"sid":{"range":[1,14]},"qid":1,"did":4,"step":2,"chance":1}' \
    -k '{"sid":{"ranges":[[1,7],10]},"qid":4,"did":13,"step":2,"chance":1}' \
    -k '{"sid":{"range":[1,14]},"qid":5,"did":17,"step":2,"chance":1}' \
    -o testing/students.csv

flask quiz run -q 1 -s STEP1 -s STEP2 --no-algo --justify-response -ef 'student{}@usf.edu' \
    -l '{"sid":1,"jid":{"range":[90,103]}}' \
    -l '{"sid":2,"jid":{"range":[90,104]}}' \
    -l '{"sid":3,"jid":{"range":[89,104]}}' \
    -l '{"sid":4,"jid":{"range":[89,105]}}' \
    -l '{"sid":5,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57]}}' \
    -l '{"sid":6,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33]}}' \
    -l '{"sid":7,"jid":{"ranges":[[1,9],[23,27],17,22,30,33,57]}}' \
    -l '{"sid":{"range":[8,9]},"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,67,68]}}' \
    -l '{"sid":10,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,[67,71],[89,104]]}}' \
    -l '{"sid":{"range":[11,14]},"jid":{"ranges":[[1,9],26,27,17,22,24,30,33,37,57,67,71,[89,91],[95,104]]}}' \
    -l '{"sid":{"range":[15,19]},"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,[67,71],[89,101]]}}' \
    -l '{"sid":20,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,[67,71],[89,115]]}}'
    

flask quiz result -q 1 --expected 'testing/Extensive Test/LF_50%_Likes_15_to_19_QP_1_3_5_10_Weights_40%_30%_20%_10%.csv' \
    --diff-o 'testing/diff-o.csv'