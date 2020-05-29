#!/bin/bash

# assuming we already injected a few QuizQuestions, and therefore Questions & Distractors before that
# we are going to create a quiz

echo "--> making sure we have at least 3 QuizQuestions"
curl -d '{ "qid": "1", "d1": "9", "d2":"8", "d3":"7"}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl -d '{ "qid": "2", "d1": "6", "d2":"5", "d3":"4"}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl -d '{ "qid": "3", "d1": "1", "d2":"2", "d3":"6"}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo

curl -d '{ "title": "Review Quiz", "description": "This is our first quiz", "questions_ids":[3, 2, 1]}' -H 'Content-Type: application/json' http://localhost:5000/quizzes && echo
