#!/bin/bash

# PRE-REQUISITES
#   ./scripts/signup_login.sh
#   ./scripts/db_populate_questions_distractors.sh

LOGIN="-L -b ./mycookies"

#login as INSTRUCTOR
curl -L -c ./mycookies -d '{ "email": "alessio1@usf.edu", "password": "secret1"}' -H 'Content-Type: application/json'  http://localhost:5000/login &> /dev/null && echo "login as INSTRUCTOR"
#FIXME for now, we hardcode that user id 1 is an instructor, fix that later.

echo "--> making sure we have at least 3 QuizQuestions"
#NOTE that the order specified in the request does not matter.
# The associations are not featuring a field to preserve order.
# besides, we also shuffle all QuizQuestions in a quiz and all alternatives in a QuizQuestion
curl $LOGIN -d '{ "qid": "1", "distractors_ids": [9, 8, 7]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl $LOGIN -d '{ "qid": "2", "distractors_ids": [6, 5, 4]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl $LOGIN -d '{ "qid": "3", "distractors_ids": [1, 9, 6]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo

curl $LOGIN -d '{ "title": "Review Quiz", "description": "This is our first quiz", "questions_ids":[3, 2, 1]}' -H 'Content-Type: application/json' http://localhost:5000/quizzes && echo

#login as STUDENT
curl -L -c ./mycookies -d '{ "email": "alessio3@usf.edu", "password": "secret3"}' -H 'Content-Type: application/json'  http://localhost:5000/login &> /dev/null && echo "login as STUDENT"

#answer the quiz
TARGET="http://localhost:5000/quizzes/1/answer"
echo "\nANSWERING Quiz #1 --> GET"
curl $LOGIN -X "GET" $TARGET && echo
echo "\nANSWERING Quiz #1 --> POST"
curl $LOGIN -X "POST" -d '{"initial_responses" : {"1":"9" , "2":"6", "3":"0"}, "justifications": {"1":"yup, bad soution", "2":"this one too", "3":"pretty sure this one is right"} }' -H 'Content-Type: application/json' $TARGET && echo

#review the quiz
echo "\nREVIEWING Quiz #1 --> GET"
TARGET="http://localhost:5000/quizzes/1/review"
curl $LOGIN -X "GET" $TARGET && echo
echo "\nREVIEWING Quiz #1 --> POST"
curl $LOGIN -X "POST" -d '{ "revised_responses": {"1":"0" , "2":"6", "3":"9"}}' -H 'Content-Type: application/json' $TARGET && echo

