#!/bin/bash

# we just use curl to add two bogus distractors to quiz #2
# this helps testing the acceptance of JSON formatted POST to the REST API
curl -d '{ "answer": "blah?"}' -H 'Content-Type: application/json' http://localhost:5000/q/2 && curl -d '{ "answer": "re-blah?"}' -H 'Content-Type: application/json' http://localhost:5000/q/2
