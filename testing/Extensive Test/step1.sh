#!/bin/bash

# PRE-REQUISITES
#   ./scripts/TestDB_setup.sh

source ./TestLib.sh

#login as INSTRUCTOR to release quiz in step #1
# --> you can do that in the DB itself by hand if you prefer
curl_login                          "instructor"            '{ "email": "instructor@usf.edu", "password": "pwd" }'
curlit  "set quiz to step 1"        "/quizzes/1/status"     ' { "status" : "STEP1" }'

#login as STUDENTs to take step #1

# nothing correct
for s in {1..4}
do
    header "Step #1 for Student #${s}"
    curl_login              "student #${s}"     '{ "email": "student'${s}'@usf.edu", "password": "pwd"}'
    curlit "GET quiz"       "/student/1"   ''
    curlit "POST quiz"      "/student/1"   '{"question" : {"1":"3" , "2":"7", "3":"11", "4":"13", "5":"17"}, "justification": {"1": {"1": "s'${s}'q1d1", "2": "s'${s}'q1d2", "3":"s'${s}'q1d3", "4":"s'${s}'q1d4", "-1":"s'${s}'q1sol"}, "2":{"5": "s'${s}'q2d5", "6": "s'${s}'q2d6", "7":"s'${s}'q2d7", "-1":"s'${s}'q2sol"}, "3":{"9": "s'${s}'q3d9", "10": "s'${s}'q3d10", "11":"s'${s}'q3d11", "-1":"s'${s}'q3sol"}, "4":{"13": "s'${s}'q4d13","14": "s'${s}'q4d14","16": "s'${s}'q4d16", "-1": "s'${s}'q4sol"}, "5": {"17": "s'${s}'q5d17", "18": "s'${s}'q5d18", "19": "s'${s}'q5d19", "20": "s'${s}'q5d20", "-1": "s'${s}'q5sol"} } }'
done

# 2 correct
for s in {5..9}
do
    header "Step #1 for Student #${s}"
    curl_login              "student #${s}"     '{ "email": "student'${s}'@usf.edu", "password": "pwd"}'
    curlit "GET quiz"       "/student/1"   ''
    curlit "POST quiz"      "/student/1"   '{"question" : {"1":"-1" , "2":"-1", "3":"11", "4":"13", "5":"17"}, "justification": {"1": {"1": "s'${s}'q1d1", "2": "s'${s}'q1d2", "3":"s'${s}'q1d3", "4":"s'${s}'q1d4", "-1":"s'${s}'q1sol"}, "2":{"5": "s'${s}'q2d5", "6": "s'${s}'q2d6", "7":"s'${s}'q2d7", "-1":"s'${s}'q2sol"}, "3":{"9": "s'${s}'q3d9", "10": "s'${s}'q3d10", "11":"s'${s}'q3d11", "-1":"s'${s}'q3sol"}, "4":{"13": "s'${s}'q4d13","14": "s'${s}'q4d14","16": "s'${s}'q4d16", "-1": "s'${s}'q4sol"}, "5": {"17": "s'${s}'q5d17", "18": "s'${s}'q5d18", "19": "s'${s}'q5d19", "20": "s'${s}'q5d20", "-1": "s'${s}'q5sol"} } }'
done

# 3 correct
for s in {10..18}
do
    header "Step #1 for Student #${s}"
    curl_login              "student #${s}"     '{ "email": "student'${s}'@usf.edu", "password": "pwd"}'
    curlit "GET quiz"       "/student/1"   ''
    curlit "POST quiz"      "/student/1"   '{"question" : {"1":"-1" , "2":"7", "3":"-1", "4":"-1", "5":"17"}, "justification": {"1": {"1": "s'${s}'q1d1", "2": "s'${s}'q1d2", "3":"s'${s}'q1d3", "4":"s'${s}'q1d4", "-1":"s'${s}'q1sol"}, "2":{"5": "s'${s}'q2d5", "6": "s'${s}'q2d6", "7":"s'${s}'q2d7", "-1":"s'${s}'q2sol"}, "3":{"9": "s'${s}'q3d9", "10": "s'${s}'q3d10", "11":"s'${s}'q3d11", "-1":"s'${s}'q3sol"}, "4":{"13": "s'${s}'q4d13","14": "s'${s}'q4d14","16": "s'${s}'q4d16", "-1": "s'${s}'q4sol"}, "5": {"17": "s'${s}'q5d17", "18": "s'${s}'q5d18", "19": "s'${s}'q5d19", "20": "s'${s}'q5d20", "-1": "s'${s}'q5sol"} } }'
done

# 5 correct
for s in {19..20}
do
    header "Step #1 for Student #${s}"
    curl_login              "student #${s}"     '{ "email": "student'${s}'@usf.edu", "password": "pwd"}'
    curlit "GET quiz"       "/student/1"   ''
    curlit "POST quiz"      "/student/1"   '{"question" : {"1":"-1" , "2":"-1", "3":"-1", "4":"-1", "5":"-1"}, "justification": {"1": {"1": "s'${s}'q1d1", "2": "s'${s}'q1d2", "3":"s'${s}'q1d3", "4":"s'${s}'q1d4", "-1":"s'${s}'q1sol"}, "2":{"5": "s'${s}'q2d5", "6": "s'${s}'q2d6", "7":"s'${s}'q2d7", "-1":"s'${s}'q2sol"}, "3":{"9": "s'${s}'q3d9", "10": "s'${s}'q3d10", "11":"s'${s}'q3d11", "-1":"s'${s}'q3sol"}, "4":{"13": "s'${s}'q4d13","14": "s'${s}'q4d14","16": "s'${s}'q4d16", "-1": "s'${s}'q4sol"}, "5": {"17": "s'${s}'q5d17", "18": "s'${s}'q5d18", "19": "s'${s}'q5d19", "20": "s'${s}'q5d20", "-1": "s'${s}'q5sol"} } }'
done

