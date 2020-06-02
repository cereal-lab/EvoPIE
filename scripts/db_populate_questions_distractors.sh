#!/bin/bash

# The questions' IDs are hardcoded, meaning that this script should be run 
# right after starting the server on an empty database.
# If there are already questions in the DB when this script is run, then
# we will add distractors to the wrong questions


# question #1
curl -d '{ "title": "Sir Lancelot and the bridge keeper, part 1", "stem": "What... is your name?", "answer": "Sir Lancelot of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions && echo
curl -d '{ "answer": "Sir Galahad of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors && echo
curl -d '{ "answer": "Sir Arthur of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors && echo
curl -d '{ "answer": "Sir Bevedere of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors && echo
curl -d '{ "answer": "Sir Robin of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors && echo


# question #2
curl -d '{ "title": "Sir Lancelot and the bridge keeper, part 2", "stem": "What... is your quest?", "answer": "To seek the holy grail"}' -H 'Content-Type: application/json' http://localhost:5000/questions && echo
curl -d '{ "answer": "To bravely run away"}' -H 'Content-Type: application/json' http://localhost:5000/questions/2/distractors && echo
curl -d '{ "answer": "To spank Zoot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/2/distractors && echo
curl -d '{ "answer": "To find a shrubbery"}' -H 'Content-Type: application/json' http://localhost:5000/questions/2/distractors && echo


# question #3
curl -d '{ "title": "Sir Lancelot and the bridge keeper, part 3", "stem": "What... is your favorite colour?", "answer": "Blue"}' -H 'Content-Type: application/json' http://localhost:5000/questions && echo
curl -d '{ "answer": "Green"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3/distractors && echo
curl -d '{ "answer": "Red"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3/distractors && echo
curl -d '{ "answer": "Yellow"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3/distractors && echo



# question just to test delete
curl -d '{ "title": "delete this question", "stem": "What did it ever do to deserve deletion?", "answer": "nothing, really"}' -H 'Content-Type: application/json' http://localhost:5000/questions && echo
curl -d '{ "answer": "I do not know"}' -H 'Content-Type: application/json' http://localhost:5000/questions/4/distractors && echo
curl -d '{ "answer": "Maybe it knows?"}' -H 'Content-Type: application/json' http://localhost:5000/questions/4/distractors && echo
curl -d '{ "answer": "Who knows?"}' -H 'Content-Type: application/json' http://localhost:5000/questions/4/distractors && echo


# testing deleting question
curl -X 'DELETE' http://localhost:5000/questions/4 && echo



# updating questions
curl -X 'PUT' -d '{ "title": "[modified] Sir Lancelot and the bridge keeper, part 3", "stem": "[modified] What... is your favorite colour?", "answer": "[modified] Blue"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3 && echo



# updating distrator for a given question
curl -d '{ "answer": "EXTRA ANSWER TO BE UPDATED"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3/distractors && echo
curl -X 'PUT' -d '{ "answer": "REDACTED ;p"}' -H 'Content-Type: application/json' http://localhost:5000/distractors/1 && echo

# deleting extraneous distractor
curl -X 'DELETE' http://localhost:5000/distractors/2 && echo


# testing RESTful API on distractors directly
curl -X 'PUT' -d '{ "answer": "HACKING THIS DISTRACTOR"}' -H 'Content-Type: application/json' http://localhost:5000/distractors/3 && echo
curl -X 'DELETE' http://localhost:5000/distractors/3 && echo


