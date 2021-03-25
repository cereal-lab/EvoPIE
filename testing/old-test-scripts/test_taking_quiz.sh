#!/bin/bash

# PRE-REQUISITES
#   ./scripts/setup_test_DB.sh

LOGIN="-L -b ./mycookies"

#login as STUDENT
curl -L -c ./mycookies -d '{ "email": "student1@usf.edu", "password": "student1"}' -H 'Content-Type: application/json'  http://localhost:5000/login &> /dev/null && echo "login as STUDENT"
#FIXME for now, we hardcode that user id 1 is an instructor, fix that later.

TARGET="http://localhost:5000/quizzes/1/take"
echo "TAKING Quiz #1 --> GET"
curl $LOGIN -X "GET" $TARGET && echo
echo "TAKING Quiz #1 --> POST"
curl $LOGIN -X "POST" -d '{"initial_responses" : {"1":"9" , "2":"6", "3":"-1"}, "justifications": {"1":"yup, bad soution", "2":"this one too", "3":"pretty sure this one is right"} }' -H 'Content-Type: application/json' $TARGET && echo
echo "TAKING Quiz #1 --> GET --> should be reviewing now"
curl $LOGIN -X "GET" $TARGET && echo
echo "TAKING Quiz #1 --> POST --> should be reviewing now"
curl $LOGIN -X "POST" -d '{"revised_responses": {"1":"-1" , "2":"6", "3":"9"}}' -H 'Content-Type: application/json' $TARGET && echo
