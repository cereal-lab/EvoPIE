#!/bin/bash

# PRE-REQUISITES

source ./TestDB_functions.sh


header 'SIGNING UP INSTRUCTOR & STUDENT ACCOUNTS, THEN LOGIN AS INSTRUCTOR'
#FIXME for now, we hardcode that user id 1 is an instructor; so we must sign him up first.
#curlit "signed up instructor"       "/signup"           '{ "email": "instructor@usf.edu", "password": "instructor", "firstname": "John", "lastname": "Keating" }'
##curlit "signed up student #1"       "/signup"           '{ "email": "student1@usf.edu", "password": "student1", "firstname": "Anakin", "lastname": "Skywalker" }'
##curlit "signed up student #2"       "/signup"           '{ "email": "student2@usf.edu", "password": "student2", "firstname": "Ahsoka", "lastname": "Tano" }'
##curlit "signed up student #3"       "/signup"           '{ "email": "student3@usf.edu", "password": "student3", "firstname": "Obi-Wan", "lastname": "Kenobi" }'
##curl_login                          "instructor"        '{ "email": "alessio@usf.edu", "password": "student1" }'

##header 'ADDING QUESTION #1' #QID 1
##curlit  'Added Question'            "/questions"                    '{ "title": "Sir Lancelot and the bridge keeper, part 1", "stem": "What... is your name?", "answer": "Sir Lancelot of Camelot"}'
##curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Sir Galahad of Camelot"}'         #D10
##curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Sir Arthur of Camelot"}'          #D11
##curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Sir Bevedere of Camelot"}'        #D12
##curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Sir Robin of Camelot"}'           #D13
##curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "4", "distractors_ids": [10, 11, 12, 13]}'

#header 'ADDING QUESTION #2' #QID 2
#curlit  'Added Question'            "/questions"                    '{ "title": "Sir Lancelot and the bridge keeper, part 2", "stem": "What... is your quest?", "answer": "To seek the holy grail"}'
#curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "To bravely run away"}'            #D5
#curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "To spank Zoot"}'                  #D6
#curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "To find a shrubbery"}'            #D7
#curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "2", "distractors_ids": [5, 6, 7]}'

#header 'ADDING QUESTION #3' #QID 3
#curlit  'Added Question'            "/questions"                    '{ "title": "Sir Lancelot and the bridge keeper, part 3", "stem": "What... is your favorite colour?", "answer": "Blue"}'
#curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Green"}'                          #D8
#curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Red"}'                            #D9
#curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Yellow"}'                         #D10
#curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "3", "distractors_ids": [8, 9, 10]}'

header 'CREATING QUIZ #1 from above questions'
curlit  'Quiz Created'              "/quizzes"          '{ "title": "Test Quiz", "description": "This is just to make sure things are working", "questions_ids":[4]}'

# new question template
# curlit  'Added Question'            "/questions"        '{ "title": "", "stem": "", "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "2", "distractors_ids": [6, 5, 4]}'