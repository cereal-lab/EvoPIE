#!/bin/bash

# PRE-REQUISITES
# run this script right after starting the server with
# flask DB-reboot && flask-run

source ./TestDB_functions.sh


header 'SIGNING UP INSTRUCTOR & STUDENT ACCOUNTS, THEN LOGIN AS INSTRUCTOR'
#FIXME for now, we hardcode that user id 1 is an instructor; so we must sign him up first.
curlit "signed up instructor"       "/signup"           '{ "email": "instructor@usf.edu", "password": "EvoPIE Actual", "firstname": "John", "lastname": "Keating" }'
curlit "signed up student #1"       "/signup"           '{ "email": "student1@usf.edu", "password": "student1", "firstname": "Anakin", "lastname": "Skywalker" }'
curlit "signed up student #2"       "/signup"           '{ "email": "student2@usf.edu", "password": "student2", "firstname": "Ahsoka", "lastname": "Tano" }'
curlit "signed up student #3"       "/signup"           '{ "email": "student3@usf.edu", "password": "student3", "firstname": "Obi-Wan", "lastname": "Kenobi" }'
curl_login                          "instructor"        '{ "email": "instructor@usf.edu", "password": "EvoPIE Actual" }'

header 'CREATING QUIZ #1 from above questions'
curlit  'Quiz Created'              "/quizzes"          '{ "title": "Test Quiz", "description": "This is just to make sure things are working", "questions_ids":[3, 2, 1]}'

# new question template
# curlit  'Added Question'            "/questions"        '{ "title": "", "stem": "", "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "2", "distractors_ids": [6, 5, 4]}'