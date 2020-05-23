#!/bin/bash

# The questions' IDs are hardcoded, meaning that this script should be run 
# right after starting the server on an empty database.
# If there are already questions in the DB when this script is run, then
# we will add distractors to the wrong questions


# question #1
curl -d '{ "title": "Sir Lancelot and the bridge keeper, part 1", "question": "What... is your name?", "answer": "Sir Lancelot of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions
curl -d '{ "answer": "Sir Galahad of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors
curl -d '{ "answer": "Sir Arthur of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors
curl -d '{ "answer": "Sir Bevedere of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors
curl -d '{ "answer": "Sir Robin of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors


# question #2
curl -d '{ "title": "Sir Lancelot and the bridge keeper, part 2", "question": "What... is your quest?", "answer": "To seek the holy grail"}' -H 'Content-Type: application/json' http://localhost:5000/questions
curl -d '{ "answer": "To bravely run away"}' -H 'Content-Type: application/json' http://localhost:5000/questions/2/distractors
curl -d '{ "answer": "To spank Zoot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/2/distractors
curl -d '{ "answer": "To find a shrubbery"}' -H 'Content-Type: application/json' http://localhost:5000/questions/2/distractors


# question #3
curl -d '{ "title": "Sir Lancelot and the bridge keeper, part 3", "question": "What... is your favorite colour?", "answer": "Blue"}' -H 'Content-Type: application/json' http://localhost:5000/questions
curl -d '{ "answer": "Green"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3/distractors
curl -d '{ "answer": "Red"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3/distractors
curl -d '{ "answer": "Yellow"}' -H 'Content-Type: application/json' http://localhost:5000/questions/3/distractors
