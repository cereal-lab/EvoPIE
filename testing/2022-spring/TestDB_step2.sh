#!/bin/bash

# PRE-REQUISITES
#   ./scripts/TestDB_setup.sh
#   ./scripts/TestDB_step1.sh

source ./TestDB_functions.sh

#login as INSTRUCTOR to release quiz in step #2
# I just do this in the DB itself 
#curl_login                          "instructor"            '{ "email": "instructor@usf.edu", "password": "instructor" }'
#curlit  "set quiz to step 2"        "/quizzes/1/status"     ' { "status" : "STEP2" }'

# step #2
header "Step #2 for Student #1"
curl_login              "student #1"        '{ "email": "student1@usf.edu", "password": "student1"}'
curlit "GET quiz"       "/quizzes/2/take"   ''
curlit "POST quiz"      "/quizzes/2/take"   '{ "revised_responses": {"4":"-1"} }'

# TODO - update the code below
#header "Step #2 for Student #2"
#curl_login              "student #2"        '{ "email": "student2@usf.edu", "password": "student2"}'
#curlit "GET quiz"       "/quizzes/1/take"   ''
#curlit "POST quiz"      "/quizzes/1/take"   '{ "revised_responses": {"1":"3" , "2":"-1", "3":"10"} }'

#header "Step #2 for Student #3"
#curl_login              "student #3"        '{ "email": "student3@usf.edu", "password": "student3"}'
#curlit "GET quiz"       "/quizzes/1/take"   ''
#curlit "POST quiz"      "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
