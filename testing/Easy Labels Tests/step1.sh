#!/bin/bash

# PRE-REQUISITES
#   ./scripts/TestDB_setup.sh

source ./TestLib.sh

#login as INSTRUCTOR to release quiz in step #1
# --> you can do that in the DB itself by hand if you prefer
curl_login                          "instructor"            '{ "email": "instructor@usf.edu", "password": "pwd" }'
curlit  "set quiz to step 1"        "/quizzes/1/status"     ' { "status" : "STEP1" }'

#login as STUDENTs to take step #1
header "Step #1 for Student #1"
curl_login              "student #1"        '{ "email": "student1@usf.edu", "password": "pwd"}'
curlit "GET quiz"       "/quizzes/1/take"   ''
curlit "POST quiz"      "/quizzes/1/take"   '{"initial_responses" : {"1":"1" , "2":"5", "3":"8"}, "justifications": {"1": {"1": "s1q1d1", "2": "s1q1d2", "3":"s1q1d3", "4":"s1q1d4", "-1":"s1q1sol"}, "2":{"5": "s1q2d5", "6": "s1q2d6", "7":"s1q2d7", "-1":"s1q2sol"}, "3":{"9": "s1q3d9", "10": "s1q3d10", "11":"s1q3d11", "-1":"s1q3sol"} } }'

header "Step #1 for Student #2"
curl_login              "student #2"        '{ "email": "student2@usf.edu", "password": "pwd"}'
curlit "GET quiz"       "/quizzes/1/take"   ''
curlit "POST quiz"      "/quizzes/1/take"   '{"initial_responses" : {"1":"2" , "2":"6", "3":"11"}, "justifications": {"1": {"1": "s2q1d1", "2": "s2q1d2", "3":"s2q1d3", "4":"s2q1d4", "-1":"s2q1sol"}, "2":{"5": "s2q2d5", "6": "s2q2d6", "7":"s2q2d7", "-1":"s2q2sol"}, "3":{"9": "s2q3d9", "10": "s2q3d10", "11":"s2q3d11", "-1":"s2q3sol"} } }'

header "Step #1 for Student #3"
curl_login              "student #3"        '{ "email": "student3@usf.edu", "password": "pwd"}'
curlit "GET quiz"       "/quizzes/1/take"   ''
curlit "POST quiz"      "/quizzes/1/take"   '{"initial_responses" : {"1":"3" , "2":"7", "3":"11"}, "justifications": {"1": {"1": "s3q1d1", "2": "s3q1d2", "3":"s3q1d3", "4":"s3q1d4", "-1":"s3q1sol"}, "2":{"5": "s3q2d5", "6": "s3q2d6", "7":"s3q2d7", "-1":"s3q2sol"}, "3":{"9": "s3q3d9", "10": "s3q3d10", "11":"s3q3d11", "-1":"s3q3sol"} } }'

# for now, all students below submit the same initial and revised responses
for s in {4..10}
do
    header "Step #1 for Student #${s}"
    curl_login              "student #${s}"     '{ "email": "student'${s}'@usf.edu", "password": "pwd"}'
    curlit "GET quiz"       "/quizzes/1/take"   ''
    curlit "POST quiz"      "/quizzes/1/take"   '{"initial_responses" : {"1":"3" , "2":"7", "3":"11"}, "justifications": {"1": {"1": "s'${s}'q1d1", "2": "s'${s}'q1d2", "3":"s'${s}'q1d3", "4":"s'${s}'q1d4", "-1":"s'${s}'q1sol"}, "2":{"5": "s'${s}'q2d5", "6": "s'${s}'q2d6", "7":"s'${s}'q2d7", "-1":"s'${s}'q2sol"}, "3":{"9": "s'${s}'q3d9", "10": "s'${s}'q3d10", "11":"s'${s}'q3d11", "-1":"s'${s}'q3sol"} } }'
done

