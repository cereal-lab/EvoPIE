#!/bin/bash


# WARNING
# we are assuming the DB has been created AND populated with a bunch of questions & distractors
# adding QuizQuestions
echo "--> Adding two QuizQuestion"
curl -d '{ "qid": "1", "distractors_ids": [2, 4, 5]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl -d '{ "qid": "2", "distractors_ids": [1, 2, 6]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo

echo "--> GET QuizQuestion #1"
curl  http://localhost:5000/quizquestions/1 && echo
echo "--> GET QuizQuestion #2"
curl  http://localhost:5000/quizquestions/2 && echo
echo "--> DEL QuizQuestion #2"
curl -X 'DELETE' http://localhost:5000/quizquestions/2 && echo
echo "--> GET QuizQuestion #2"
curl  http://localhost:5000/quizquestions/2 && echo
