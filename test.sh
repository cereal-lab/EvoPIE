flask DB-reboot
flask quiz init -nq 5 -nd 4 -qd '{"2":[5,6,7],"3":[9,10,11],"4":[13,14,16]}'

#user id 1 is reserved for instructor in this test
flask student init -ns 20 -ef 'student{}@usf.edu' -k '{"sid":{"range":[2,5]},"qid":1,"did":3,"step":1,"chance":1}' \
    -k '{"sid":{"ranges":[[2,5],[11,19]]},"qid":2,"did":7,"step":1,"chance":1}' \
    -k '{"sid":{"range":[2,10]},"qid":3,"did":11,"step":1,"chance":1}' \
    -k '{"sid":{"range":[2,10]},"qid":4,"did":13,"step":1,"chance":1}' \
    -k '{"sid":{"range":[2,19]},"qid":5,"did":17,"step":1,"chance":1}' \
    -k '{"sid":{"range":[2,15]},"qid":1,"did":4,"step":2,"chance":1}' \
    -k '{"sid":{"ranges":[[2,8],11]},"qid":4,"did":13,"step":2,"chance":1}' \
    -k '{"sid":{"range":[2,15]},"qid":5,"did":17,"step":2,"chance":1}' \
    -o testing/students.csv

flask quiz run -q 1 -s STEP1 -s STEP2 --no-algo --justify-response \
    -l '{"sid":2,"jid":{"range":[90,103]}}' \
    -l '{"sid":3,"jid":{"range":[90,104]}}' \
    -l '{"sid":4,"jid":{"range":[89,104]}}' \
    -l '{"sid":5,"jid":{"range":[89,105]}}' \
    -l '{"sid":6,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57]}}' \
    -l '{"sid":7,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33]}}' \
    -l '{"sid":8,"jid":{"ranges":[[1,9],[23,27],17,22,30,33,57]}}' \
    -l '{"sid":{"range":[9,10]},"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,67,68]}}' \
    -l '{"sid":11,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,[67,71],[89,104]]}}' \
    -l '{"sid":{"range":[12,15]},"jid":{"ranges":[[1,9],26,27,17,22,24,30,33,37,57,67,71,[89,91],[95,104]]}}' \
    -l '{"sid":{"range":[16,20]},"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,[67,71],[89,101]]}}' \
    -l '{"sid":21,"jid":{"ranges":[[1,9],[23,27],17,22,24,30,33,37,57,[67,71],[89,115]]}}'

flask quiz result -q 1 --expected 'testing/Extensive Test/LF_50%_Likes_15_to_19_QP_1_3_5_10_Weights_40%_30%_20%_10%.csv' \
    --diff-o 'testing/diff-o.csv'