#!/bin/bash

# PRE-REQUISITES
# empty DB after a flask DB-reboot

source ./TestDB_functions.sh

# NOTE we keep these quizzes / questions / justifications simple by not putting code or special characters in them that would need to be escaped
# this makes these scripts to test the functionalities of most of the UI but not detect any problems related to bad JSON formatting, 
# presence of non-rendered HTML tags in the outputs, and things of this nature.

header 'SIGNING UP INSTRUCTOR & STUDENT ACCOUNTS, THEN LOGIN AS INSTRUCTOR'
#FIXME for now, we hardcode that user id 1 is an instructor; so we must sign him up first.
curlit "signed up instructor"       "/signup"           '{ "email": "instructor@usf.edu", "password": "pwd", "retype": "pwd","firstname": "John", "lastname": "Keating" }'
curlit "signed up student #1"       "/signup"           '{ "email": "student1@usf.edu", "password": "pwd", "retype": "pwd","firstname": "Anakin", "lastname": "Skywalker" }'
curlit "signed up student #2"       "/signup"           '{ "email": "student2@usf.edu", "password": "pwd", "retype": "pwd", "firstname": "Ahsoka", "lastname": "Tano" }'
curlit "signed up student #3"       "/signup"           '{ "email": "student3@usf.edu", "password": "pwd", "retype": "pwd","firstname": "Obi-Wan", "lastname": "Kenobi" }'
curl_login                          "instructor"        '{ "email": "instructor@usf.edu", "password": "pwd" }'

##header 'ADDING QUESTION #1' #QID 1
curlit  'Added Question'            "/questions"                    '{ "title": "Question 1 Title", "stem": "Question 1 Stem?", "answer": "Question 1 answer"}'
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Question 1 distractor 1"}'        #D1
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Question 1 distractor 2"}'        #D2
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Question 1 distractor 3"}'        #D3
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Question 1 distractor 4"}'        #D4
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "1", "distractors_ids": [1, 2, 3, 4]}'

header 'ADDING QUESTION #2' #QID 2
curlit  'Added Question'            "/questions"                    '{ "title": "Question 2 Title", "stem": "Question 2 Stem?", "answer": "Question 2 answer"}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "Question 2 distractor 1"}'        #D5
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "Question 2 distractor 2"}'        #D6
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "Question 2 distractor 3"}'        #D7
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "Question 2 distractor 4"}'        #D8
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "2", "distractors_ids": [5, 6, 7]}'

#header 'ADDING QUESTION #3' #QID 3
curlit  'Added Question'            "/questions"                    '{ "title": "Question 3 Title", "stem": "Question 3 stem?", "answer": "Question 3 answer"}'
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Question 3 distractor 1"}'        #D9
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Question 3 distractor 2"}'        #D10
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Question 3 distractor 3"}'        #D11
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Question 3 distractor 4"}'        #D12
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "3", "distractors_ids": [9, 10, 11]}'

header 'CREATING QUIZ #1 from above questions'
curlit  'Quiz Created'              "/quizzes"          '{ "title": "Test Quiz", "description": "This is just to make sure things are working", "questions_ids":[1,2,3]}'

# new question template
# curlit  'Added Question'            "/questions"        '{ "title": "", "stem": "", "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "2", "distractors_ids": [6, 5, 4]}'