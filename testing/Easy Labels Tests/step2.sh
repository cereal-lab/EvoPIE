#!/bin/bash

# PRE-REQUISITES
#   ./setup.sh
#   ./step1.sh

source ./TestLib.sh

#login as INSTRUCTOR to release quiz in step #2
curl_login                          "instructor"            '{ "email": "instructor@usf.edu", "password": "pwd" }'
curlit  "set quiz to step 2"        "/quizzes/1/status"     ' { "status" : "STEP2" }'

# step #2
header "Step #2 for Student #1"
curl_login              "student #1"        '{ "email": "student1@usf.edu", "password": "pwd"}'
curlit "GET quiz"       "/quizzes/1/take"   ''
curlit "POST quiz"      "/quizzes/1/take"   '{ "revised_responses": {"1":"-1", "2":"-1", "3":"-1"} }'
# we simulate each student liking some of the justifications for question #1 from the other students
# we do not guarantee that the student would have seen these as part of the randomly selected
# justifications to be displayed for each alternative
like "s2q1d1"    "14" 
like "s3q1d1"    "27" 
like "s3q1d4"    "30" 
like "s2q2sol"   "22"
like "s3q2d6"    "33" 
like "s2q3d10"   "24"
like "s3q3d10"   "37"

header "Step #2 for Student #2"
curl_login              "student #2"        '{ "email": "student2@usf.edu", "password": "pwd"}'
curlit "GET quiz"       "/quizzes/1/take"   ''
curlit "POST quiz"      "/quizzes/1/take"   '{ "revised_responses": {"1":"3" , "2":"-1", "3":"10"} }'
like "s1q1d1"    "1"
like "s1q1d4"    "4"
like "s3q1d4"    "30"
like "s3q2d6"    "33"
like "s3q3d10"   "37"

header "Step #2 for Student #3"
curl_login            "student #3"        '{ "email": "student3@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
like "s1q1d4"    "4"
like "s1q1sol"   "5"
like "s2q1d4"    "17" 
like "s2q2sol"   "22"
like "s2q3d10"   "24"

# These are the expected results in the grading page for quiz #1 http://127.0.0.1:5000/grades/1
# They have been verified by hand by looking up the information in the popups from the likes given,
# likes received buttons 
# student   initial score   revised score   likes given     likes received      scores
# 1         0               3               5               6                   6 (n/a, no maxlikes yet)
# 2         0               1               5               6                   6
# 3         0               1               5               7                   7
