#!/bin/bash

# PRE-REQUISITES
#   ./scripts/Test_COP2513F20_setup.sh used to create a local DB
#   local DB uploaded to server in location expected by docker container

source ./evopie.sh

#login as INSTRUCTOR to release quiz in step #2
curl_login                          "instructor"            '{ "email": "instructor@usf.edu", "password": "instructor" }'
curlit  "set quiz to step 2"        "/quizzes/1/status"     ' { "status" : "STEP2" }'