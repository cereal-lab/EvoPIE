#!/bin/bash

# assuming we already injected a few QuizQuestions, and therefore Questions & Distractors before that
# we are going to create a quiz

echo "--> making sure we have at least 3 QuizQuestions"
#NOTE that the order specified in the request does not matter.
# The associations are not featuring a field to preserve order.
# besides, we also shuffle all QuizQuestions in a quiz and all alternatives in a QuizQuestion
curl -d '{ "qid": "1", "distractors_ids": [9, 8, 7]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl -d '{ "qid": "2", "distractors_ids": [6, 5, 4]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl -d '{ "qid": "3", "distractors_ids": [1, 9, 6]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo

curl -d '{ "title": "Review Quiz", "description": "This is our first quiz", "questions_ids":[3, 2, 1]}' -H 'Content-Type: application/json' http://localhost:5000/quizzes && echo

# testing updating quiz
#NOTE that the order of questions does not matter either - see above
curl -X "PUT" -d '{ "title": "[UPDATED] Review Quiz", "description": "[UPDATED] This is our first quiz", "questions_ids":[2, 3, 1]}' -H 'Content-Type: application/json' http://localhost:5000/quizzes/1 && echo

# The following is a bad idea since the relationship quiz vs. QuizQuestion in the DB
# is not meant to model duplicates. Only one question would show in this quiz.
# curl -X "PUT" -d '{ "title": "[UPDATED] Review Quiz", "description": "[UPDATED] This is our first quiz", "questions_ids":[3, 3, 3]}' -H 'Content-Type: application/json' http://localhost:5000/quizzes/1 && echo






