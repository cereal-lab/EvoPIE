#!/bin/bash

# PRE-REQUISITES
#   ./scripts/signup_login.sh
#   ./scripts/db_populate_questions_distractors.sh

LOGIN="-L -b ./mycookies"

# WARNING
# we are assuming the DB has been created AND populated with a bunch of questions & distractors
# adding QuizQuestions
echo "--> Adding two QuizQuestion"
curl $LOGIN -d '{ "qid": "1", "distractors_ids": [2, 4, 5]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl $LOGIN -d '{ "qid": "2", "distractors_ids": [1, 2, 6]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo

echo "--> GET QuizQuestion #1"
curl $LOGIN  http://localhost:5000/quizquestions/1 && echo
echo "--> GET QuizQuestion #2"
curl $LOGIN  http://localhost:5000/quizquestions/2 && echo
echo "--> PUT QuizQuestion #2"
curl $LOGIN -i -X 'PUT' -d '{ "qid": "2", "distractors_ids": [2, 4, 5]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions/2 && echo
echo "---> QuizQuestion #2 should look like QuizQuestion#1 now"
echo "--> GET QuizQuestion #2"
curl $LOGIN  http://localhost:5000/quizquestions/2 && echo

#echo "--> DEL QuizQuestion #2"
#curl $LOGIN -X 'DELETE' http://localhost:5000/quizquestions/2 && echo
#echo "--> GET QuizQuestion #2"
#curl $LOGIN  http://localhost:5000/quizquestions/2 && echo
