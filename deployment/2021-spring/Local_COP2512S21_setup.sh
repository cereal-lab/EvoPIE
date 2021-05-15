#!/bin/bash

# PRE-REQUISITES
# run this script right after starting the server with
# flask DB-reboot && flask-run

source ./evopie.local.sh


header 'SIGNING UP INSTRUCTOR THEN LOGIN AS INSTRUCTOR'
#FIXME for now, we hardcode that user id 1 is an instructor; so we must sign him up first.
curlit "signed up instructor"       "/signup"                       '{ "email": "instructor@usf.edu", "password": "instructor", "firstname": "John", "lastname": "Keating" }'
curlit "signed up test student"     "/signup"                       '{ "email": "student@usf.edu", "password": "student", "firstname": "Test", "lastname": "Student" }'
curl_login                          "instructor"                    '{ "email": "instructor@usf.edu", "password": "instructor" }'

header 'ADDING QUESTION #1' #QID 1
curlit  'Added Question'            "/questions"                    '{ "title": "Boolean Expressions", "stem": "We want a while loop to stop iterating as soon as an int variable named input is either equal to 42 or to 23. Which of the following code fragments would do that?", "answer": "while( input != 42 && input != 23){ ... }"}'
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "while( input != 42 || input != 23){ ... }"}'     #D1
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "while( input == 42 && input == 23){ ... }"}'     #D2
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "while( input == 42 || input == 23){ ... }"}'     #D3
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "1", "distractors_ids": [1, 2, 3]}'

header 'ADDING QUESTION #2' #QID 2
curlit  'Added Question'            "/questions"                    '{ "title": "Occurences in Arrays", "stem": "We want to count the number of occurences of the value 42 in an int array named data. Which of the following does not work?", "answer": "for(int i = 0 ; i <= data.length ; i++){ if(data[i]==42) occurences++; }"}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "for(int v : data){ occurences += (v==42)?1:0; }"}'         #D4
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "for(int v : data){ if(v==42) occurences++; }"}'     #D5
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "for(int i=0 ; i < data.length ; i++){ occurences += (data[i]==42)?1:0; }"}'        #D6
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "2", "distractors_ids": [4, 5, 6]}'

header 'ADDING QUESTION #3' #QID 3
curlit  'Added Question'            "/questions"                    '{ "title": "Updating Arrays", "stem": "We want to update any odd value by 1 in an int array named data. Which of the following does not work?", "answer": "int i = 0; for(int v:data){ if(v % 2 != 0) data[i] = ++v; i++; }"}'
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "for(int i=0 ; i < data.length ; i++){ data[i] = (data[i] % 2 == 0)?data[i]:data[i]+1; }"}'   #D7
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "for(int i=0 ; i < data.length ; i++){ if(data[i] % 2 != 0) data[i]++; }"}'   #D8
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "for(int v:data){ if(v % 2 != 0) v++; }"}'   #D9
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "3", "distractors_ids": [7, 8, 9]}'

header 'ADDING QUESTION #4' #QID 4
curlit  'Added Question'            "/questions"                    '{ "title": "RNG is on your side", "stem": "Which of the following code fragments generates a random number between 23 (included) and 42(included)?", "answer": "int rnd = 23 + (int)(Math.random()*20);"}'
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "int rnd = 23 + (int)(Math.random()*19);"}'   #D10
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "int rnd = 23 + (int)(Math.random()*42);"}'   #D11
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "int rnd = 23 + (int)(Math.random()*43);"}'   #D12
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "4", "distractors_ids": [10, 11, 12]}'

header 'ADDING QUESTION #5' #QID 5
curlit  'Added Question'            "/questions"                    '{ "title": "Opinion question", "stem": "This question is just here to try to get a feel about what you think of these 2-steps quizzes. There are no correct or wrong answers :) What if we would use this kind of 2-step quiz all semester long? Select the option that is the closest to your opinion: Being able to revise my answer after seeing other students justifications is...", "answer": "...useful because it may help me catch a potential misunderstanding on my part."}'
curlit  'Added distractor'          "/questions/5/distractors"      '{ "answer": "...useless because I do not need help."}'   #D13
curlit  'Added distractor'          "/questions/5/distractors"      '{ "answer": "...useless because the justifications of my peers are not helpful."}'   #D14
curlit  'Added distractor'          "/questions/5/distractors"      '{ "answer": "...useless because of other reasons."}'   #D15
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "5", "distractors_ids": [13, 14, 15]}'

header 'CREATING QUIZ & releasing it as STEP1'
curlit  'Quiz Created'              "/quizzes"                      '{ "title": "Extra Credit Quiz", "description": "This quiz is a simple extra-credit assignment.", "questions_ids":[1, 2, 3, 4, 5]}'
#curlit  "Quiz released as STEP1"    "/quizzes/1/status"             '{ "status" : "STEP1" }'

# new question template
# curlit  'Added Question'            "/questions"        '{ "title": "", "stem": "", "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "2", "distractors_ids": [6, 5, 4]}'