#!/bin/bash

# PRE-REQUISITES
# empty DB after a flask DB-reboot

source ./TestDB_functions.sh


header 'SIGNING UP INSTRUCTOR & STUDENT ACCOUNTS, THEN LOGIN AS INSTRUCTOR'
#FIXME for now, we hardcode that user id 1 is an instructor; so we must sign him up first.
curlit "signed up instructor"       "/signup"           '{ "email": "instructor@usf.edu", "password": "pwd", "retype": "pwd","firstname": "John", "lastname": "Keating" }'
curlit "signed up student #1"       "/signup"           '{ "email": "student1@usf.edu", "password": "pwd", "retype": "pwd","firstname": "Anakin", "lastname": "Skywalker" }'
curlit "signed up student #2"       "/signup"           '{ "email": "student2@usf.edu", "password": "pwd", "retype": "pwd", "firstname": "Ahsoka", "lastname": "Tano" }'
curlit "signed up student #3"       "/signup"           '{ "email": "student3@usf.edu", "password": "pwd", "retype": "pwd","firstname": "Obi-Wan", "lastname": "Kenobi" }'
curl_login                          "instructor"        '{ "email": "instructor@usf.edu", "password": "pwd" }'

header 'ADDING QUESTION #1' #QID 1
curlit  'Added Question'            "/questions"                    '{ "title": "Sir Lancelot and the bridge keeper, part 1", "stem": "What... is your name?", "answer": "Sir Lancelot of Camelot"}'
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Sir Galahad of Camelot"}'         #D1
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Sir Arthur of Camelot"}'          #D2
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Sir Bevedere of Camelot"}'        #D3
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Sir Robin of Camelot"}'           #D4
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Sir Pandey of Camelot"}'           #D5
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "1", "distractors_ids": [1, 2, 5]}'

header 'ADDING QUESTION #2' #QID 2
curlit  'Added Question'            "/questions"                    '{ "title": "Sir Lancelot and the bridge keeper, part 2", "stem": "What... is your quest?", "answer": "To seek the holy grail"}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "To bravely run away"}'            #D6
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "To spank Zoot"}'                  #D7
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "To find a shrubbery"}'            #D8
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "To be or not to be"}'            #D9
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "2", "distractors_ids": [6, 7, 9]}'

header 'ADDING QUESTION #3' #QID 3
curlit  'Added Question'            "/questions"                    '{ "title": "Sir Lancelot and the bridge keeper, part 3", "stem": "What... is your favorite colour?", "answer": "Blue"}'
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Green"}'                          #D10
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Red"}'                            #D11
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Yellow"}'                         #D12
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Purple"}'                         #D13
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Black"}'                         #D14
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "3", "distractors_ids": [10, 13, 14]}'

header 'ADDING QUESTION #4' #QID 4
curlit  'Added Question'            "/questions"                    '{ "title": "Sir Lancelot and the bridge keeper, part 4", "stem": "What... is the current year?", "answer": "2022"}'
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "2019"}'                          #D15
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "2021"}'                          #D16
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "2023"}'                         #D17
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "2018"}'                         #D18
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "1990"}'                         #D19
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "4", "distractors_ids": [15, 17, 19]}'

header 'CREATING QUIZ #1 from above questions'
curlit  'Quiz Created'              "/quizzes"          '{ "title": "Test Quiz", "description": "This is just to make sure things are working", "questions_ids":[1,2,3,4]}'

# new question template
# curlit  'Added Question'            "/questions"        '{ "title": "", "stem": "", "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "2", "distractors_ids": [6, 5, 4]}'