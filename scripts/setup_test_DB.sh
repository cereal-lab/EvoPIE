#!/bin/bash

# run this script right after starting the server with
# flask DB-reboot && flask-run

# set up curl arguments

function header {
    echo -e "\n---> $1\n"
}

function completed {
    echo -e "\t$1"
}


function curlit {
    LOGIN="-L -b ./mycookies"
    MSG=$1
    TARGET_PATH=$2
    DATA=$3    
    curl $LOGIN -d "$DATA" -H "Content-Type: application/json" "http://localhost:5000$TARGET_PATH" &>/dev/null
    if [[ $? == 0 ]]
    then
        completed "$MSG"
    else
        completed "$MSG --> Status returned is $?"
        exit
    fi
}


function login_instructor {
    TARGET_PATH="/login"
    #FIXME for now, we hardcode that user id 1 is an instructor, fix that later.

    curl -L -c ./mycookies -d '{ "email": "instructor@usf.edu", "password": "instructor"}' -H "Content-Type: application/json" "http://localhost:5000$TARGET_PATH" &>/dev/null
    if [[ $? == 0 ]]
    then
        completed "Logged in as INSTRUCTOR"
    else
        completed "FAILED to login as INSTRUCTOR"
        exit
    fi
}



header 'SIGNING UP INSTRUCTOR & STUDENT ACCOUNTS, THEN LOGIN AS INSTRUCTOR'
curlit "signed up instructor"       "/signup"           '{ "email": "instructor@usf.edu", "password": "instructor", "firstname": "John", "lastname": "Keating" }'
curlit "signed up student #1"       "/signup"           '{ "email": "student1@usf.edu", "password": "student1", "firstname": "Anakin", "lastname": "Skywalker" }'
curlit "signed up student #2"       "/signup"           '{ "email": "student2@usf.edu", "password": "student2", "firstname": "Ahsoka", "lastname": "Tano" }'
curlit "signed up student #3"       "/signup"           '{ "email": "student3@usf.edu", "password": "student3", "firstname": "Obi-Wan", "lastname": "Kenobi" }'
login_instructor

header 'ADDING QUESTION #1'
curlit  'Added Question'            "/questions"        '{ "title": "Sir Lancelot and the bridge keeper, part 1", "stem": "What... is your name?", "answer": "Sir Lancelot of Camelot"}'
curlit  'Added distractor'          "/distractors"      '{ "answer": "Sir Galahad of Camelot"}'
curlit  'Added distractor'          "/distractors"      '{ "answer": "Sir Arthur of Camelot"}'
curlit  'Added distractor'          "/distractors"      '{ "answer": "Sir Bevedere of Camelot"}'
curlit  'Added distractor'          "/distractors"      '{ "answer": "Sir Robin of Camelot"}'
curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "1", "distractors_ids": [9, 8, 7]}'

header 'ADDING QUESTION #2'
curlit  'Added Question'            "/questions"        '{ "title": "Sir Lancelot and the bridge keeper, part 2", "stem": "What... is your quest?", "answer": "To seek the holy grail"}'
curlit  'Added distractor'          "/distractors"      '{ "answer": "To bravely run away"}'
curlit  'Added distractor'          "/distractors"      '{ "answer": "To spank Zoot"}'
curlit  'Added distractor'          "/distractors"      '{ "answer": "To find a shrubbery"}'
curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "2", "distractors_ids": [6, 5, 4]}'

header 'ADDING QUESTION #3'
curlit  'Added Question'            "/questions"        '{ "title": "Sir Lancelot and the bridge keeper, part 3", "stem": "What... is your favorite colour?", "answer": "Blue"}'
curlit  'Added distractor'          "/distractors"      '{ "answer": "Green"}'
curlit  'Added distractor'          "/distractors"      '{ "answer": "Red"}'
curlit  'Added distractor'          "/distractors"      '{ "answer": "Yellow"}'
curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "3", "distractors_ids": [1, 9, 6]}'

header 'CREATING QUIZ #1 from above questions'
curlit  'Quiz Created'              "/quizzes"          '{ "title": "Test Quiz", "description": "This is just to make sure things are working", "questions_ids":[3, 2, 1]}'

# new question template
# curlit  'Added Question'            "/questions"        '{ "title": "", "stem": "", "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "2", "distractors_ids": [6, 5, 4]}'