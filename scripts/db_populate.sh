#!/bin/bash

# run this script right after starting the server with
# flask DB-reboot && flask-run

# The questions' IDs are hardcoded, meaning that this script should be run 
# right after starting the server on an empty database.
# If there are already questions in the DB when this script is run, then
# we will add distractors to the wrong questions

echo
echo
echo '---> SIGNING UP 3 ACCOUNTS'
curl -L -d '{ "email": "alessio1@usf.edu", "password": "secret1", "firstname": "first1", "lastname": "last1" }' -H 'Content-Type: application/json'  http://localhost:5000/signup &> /dev/null && echo "signup"
curl -L -d '{ "email": "alessio2@usf.edu", "password": "secret2", "firstname": "first2", "lastname": "last2" }' -H 'Content-Type: application/json'  http://localhost:5000/signup &> /dev/null && echo "signup"
curl -L -d '{ "email": "alessio3@usf.edu", "password": "secret3", "firstname": "first3", "lastname": "last3" }' -H 'Content-Type: application/json'  http://localhost:5000/signup &> /dev/null && echo "signup"

echo
echo
echo '---> login as INSTRUCTOR'
curl -L -c ./mycookies -d '{ "email": "alessio1@usf.edu", "password": "secret1"}' -H 'Content-Type: application/json'  http://localhost:5000/login &> /dev/null && echo "login as INSTRUCTOR"
#TODO for now, we hardcode that user id 1 is an instructor, fix that later.

LOGIN="-L -b ./mycookies"

echo
echo
echo '--->\tADDING QUESTIONS & DISTRACTORS'

# question #1
curl $LOGIN -d '{ "title": "Sir Lancelot and the bridge keeper, part 1", "stem": "What... is your name?", "answer": "Sir Lancelot of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions && echo
curl $LOGIN -d '{ "answer": "Sir Galahad of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors && echo
curl $LOGIN -d '{ "answer": "Sir Arthur of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors && echo
curl $LOGIN -d '{ "answer": "Sir Bevedere of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors && echo
curl $LOGIN -d '{ "answer": "Sir Robin of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors && echo


# question #2
curl $LOGIN -d '{ "title": "Sir Lancelot and the bridge keeper, part 2", "stem": "What... is your quest?", "answer": "To seek the holy grail"}' -H 'Content-Type: application/json' http://localhost:5000/questions && echo
curl $LOGIN -d '{ "answer": "To bravely run away"}' -H 'Content-Type: application/json' http://localhost:5000/questions/2/distractors && echo
curl $LOGIN -d '{ "answer": "To spank Zoot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/2/distractors && echo
curl $LOGIN -d '{ "answer": "To find a shrubbery"}' -H 'Content-Type: application/json' http://localhost:5000/questions/2/distractors && echo


# question #3
curl $LOGIN -d '{ "title": "Sir Lancelot and the bridge keeper, part 3", "stem": "What... is your favorite colour?", "answer": "Blue"}' -H 'Content-Type: application/json' http://localhost:5000/questions && echo
curl $LOGIN -d '{ "answer": "Green"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3/distractors && echo
curl $LOGIN -d '{ "answer": "Red"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3/distractors && echo
curl $LOGIN -d '{ "answer": "Yellow"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3/distractors && echo



# Extra question
curl $LOGIN -d '{ "title": "delete this question", "stem": "What did it ever do to deserve deletion?", "answer": "nothing, really"}' -H 'Content-Type: application/json' http://localhost:5000/questions && echo
curl $LOGIN -d '{ "answer": "I do not know"}' -H 'Content-Type: application/json' http://localhost:5000/questions/4/distractors && echo
curl $LOGIN -d '{ "answer": "Maybe it knows?"}' -H 'Content-Type: application/json' http://localhost:5000/questions/4/distractors && echo
curl $LOGIN -d '{ "answer": "Who knows?"}' -H 'Content-Type: application/json' http://localhost:5000/questions/4/distractors && echo

# updating questions
curl $LOGIN -X 'PUT' -d '{ "title": "[modified] delete this question", "stem": "[modified] What did it ever do to deserve deletion?", "answer": "[modified]nothing, really"}' -H 'Content-Type: application/json' http://localhost:5000/questions/4 && echo

# updating distrator for a given question
curl $LOGIN -d '{ "answer": "EXTRA ANSWER TO BE UPDATED"}' -H 'Content-Type: application/json' http://localhost:5000/questions/4/distractors && echo

# testing RESTful API on distractors directly
curl $LOGIN -X 'PUT' -d '{ "answer": "REDACTED ;p"}' -H 'Content-Type: application/json' http://localhost:5000/distractors/14 && echo
curl $LOGIN -X 'PUT' -d '{ "answer": "HACKING THIS DISTRACTOR"}' -H 'Content-Type: application/json' http://localhost:5000/distractors/14 && echo
#curl $LOGIN -X 'DELETE' http://localhost:5000/distractors/14 && echo

# testing deleting question
#curl $LOGIN -X 'DELETE' http://localhost:5000/questions/4 && echo

echo
echo
echo '--->\tADDING QUIZQUESTIONS'

#NOTE that the order specified in the request does not matter.
# The associations are not featuring a field to preserve order.
# besides, we also shuffle all QuizQuestions in a quiz and all alternatives in a QuizQuestion
curl $LOGIN -d '{ "qid": "1", "distractors_ids": [9, 8, 7]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl $LOGIN -d '{ "qid": "2", "distractors_ids": [6, 5, 4]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo
curl $LOGIN -d '{ "qid": "3", "distractors_ids": [1, 9, 6]}' -H 'Content-Type: application/json' http://localhost:5000/quizquestions && echo

echo
echo
echo '--->\tADDING QUIZ'

curl $LOGIN -d '{ "title": "Review Quiz", "description": "This is our first quiz", "questions_ids":[3, 2, 1]}' -H 'Content-Type: application/json' http://localhost:5000/quizzes && echo




