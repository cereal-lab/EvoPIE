#!/bin/bash

# assuming we already injected a few QuizQuestions, and therefore Questions & Distractors before that
# we are going to create a quiz

echo "--> making sure we have at least 3 QuizQuestions"
curl -d '{ "qid": "1", "distractors_ids": [9, 8, 7]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl -d '{ "qid": "2", "distractors_ids": [6, 5, 4]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl -d '{ "qid": "3", "distractors_ids": [1, 2, 6]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo

curl -d '{ "title": "Review Quiz", "description": "This is our first quiz", "questions_ids":[3, 2, 1]}' -H 'Content-Type: application/json' http://localhost:5000/quizzes && echo

# testing updating quiz
curl -X "PUT" -d '{ "title": "[UPDATED] Review Quiz", "description": "[UPDATED] This is our first quiz", "questions_ids":[3, 3, 3]}' -H 'Content-Type: application/json' http://localhost:5000/quizzes/1 && echo






