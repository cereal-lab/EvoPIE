#!/bin/bash

# PRE-REQUISITES
#   ./scripts/TestDB_setup.sh
#   ./scripts/TestDB_step1.sh
#   ./scripts/TestDB_step2.sh

source ./TestDB_functions.sh


header "login as INSTRUCTOR"
curl_login                          "instructor"            '{ "email": "instructor@usf.edu", "password": "instructor" }'

LOGIN='-L -b ./mycookies'
JUNK='{ "something": "value" }'


TARGET='http://localhost:5000/quizzes/1'
header "Try to delete Quiz #1"
curl $LOGIN -X DELETE $TARGET
header "Try to modify Quiz #1"
curl $LOGIN -X PUT -d "$JUNK" $TARGET


TARGET='http://localhost:5000/quizquestions/1'
header "Try to delete QuizQuestions #1 used by Quiz #1"
curl $LOGIN -X DELETE $TARGET
header "Try to modify QuizQuestions used by Quiz #1"
curl $LOGIN -X PUT -d "$JUNK" $TARGET


TARGET='http://localhost:5000/questions/1'
header "Try to delete Question #1 used by QuizQuestions #1 used by Quiz #1"
curl $LOGIN -X DELETE $TARGET
header "Try to modify Question #1 used by QuizQuestions #1 used by Quiz #1"
curl $LOGIN -X PUT -d "$JUNK" $TARGET


TARGET='http://localhost:5000/distractors/1'
header "Try to delete Distractor #1 used by Question #1 used by QuizQuestions #1 used by Quiz #1"
curl $LOGIN -X DELETE $TARGET
header "Try to modify Distractor #1 used by Question #1 used by QuizQuestions #1 used by Quiz #1"
curl $LOGIN -X PUT -d "$JUNK" $TARGET


# TODO for sake of completude we should now test modifying
# QuizQuestions / Questions / Distractors that are not used in 
# any non-hidden Quiz
# to do so, add a new quiz and new QuizQuestions / Questions / Distractors
echo
