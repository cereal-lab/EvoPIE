#!/bin/bash

# we just use curl to add two bogus distractors to quiz #2
# this helps testing the acceptance of JSON formatted POST to the REST API


# testing adding questions
curl -d '{ "title": "CURLed - Sir Lancelot and the bridge keeper, part 1", "question": "What... is your name?", "answer": "Sir Lancelot of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions

#adding distractors to question #1
curl -d '{ "answer": "Sir Galahad of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors
curl -d '{ "answer": "Sir Arthur of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors
curl -d '{ "answer": "Sir Bevedere of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors
curl -d '{ "answer": "Sir Robin of Camelot"}' -H 'Content-Type: application/json' http://localhost:5000/questions/1/distractors
