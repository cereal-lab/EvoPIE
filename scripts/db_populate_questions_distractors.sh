#!/bin/bash

# The questions' IDs are hardcoded, meaning that this script should be run 
# right after starting the server on an empty database.
# If there are already questions in the DB when this script is run, then
# we will add distractors to the wrong questions

LOGIN="-L -b ./mycookies"

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




