#!/bin/bash

# PRE-REQUISITES
# empty DB after a flask DB-reboot

source ./TestLib.sh

# NOTE we keep these quizzes / questions / justifications simple by not putting code or special characters in them that would need to be escaped
# this makes these scripts to test the functionalities of most of the UI but not detect any problems related to bad JSON formatting, 
# presence of non-rendered HTML tags in the outputs, and things of this nature.

header 'SIGNING UP INSTRUCTOR & STUDENT ACCOUNTS, THEN LOGIN AS INSTRUCTOR'
#FIXME for now, we hardcode that user id 1 is an instructor; so we must sign him up first.
curlit "signed up instructor"       "/signup"           '{ "email": "instructor@usf.edu",   "password": "pwd", "retype": "pwd","firstname": "John",     "lastname": "Keating" }'
curlit "signed up student #1"       "/signup"           '{ "email": "student1@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Anakin",   "lastname": "Skywalker" }'
curlit "signed up student #2"       "/signup"           '{ "email": "student2@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Ahsoka",   "lastname": "Tano" }'
curlit "signed up student #3"       "/signup"           '{ "email": "student3@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Obi-Wan",  "lastname": "Kenobi" }'
curlit "signed up student #4"       "/signup"           '{ "email": "student4@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Rey",      "lastname": "Skywalker" }'
curlit "signed up student #5"       "/signup"           '{ "email": "student5@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Mace",     "lastname": "Windu" }'
curlit "signed up student #6"       "/signup"           '{ "email": "student6@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Luke",     "lastname": "Skywalker" }'
curlit "signed up student #7"       "/signup"           '{ "email": "student7@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "BB",       "lastname": "8" }'
curlit "signed up student #8"       "/signup"           '{ "email": "student8@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "R2",       "lastname": "D2" }'
curlit "signed up student #9"       "/signup"           '{ "email": "student9@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "C3",       "lastname": "PO" }'
curlit "signed up student #10"      "/signup"           '{ "email": "student10@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Jar-Jar",  "lastname": "Binks" }'
curlit "signed up student #11"      "/signup"           '{ "email": "student11@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Mayank",  "lastname": "Pandey" }'
curlit "signed up student #12"      "/signup"           '{ "email": "student12@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Anshika",  "lastname": "Bhowmick }'
curlit "signed up student #13"      "/signup"           '{ "email": "student13@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Aoun",  "lastname": "Ashraf" }'
curlit "signed up student #14"      "/signup"           '{ "email": "student14@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Gopal Krishna",  "lastname": "Shukla" }'
curlit "signed up student #15"      "/signup"           '{ "email": "student15@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Akshat",  "lastname": "Gupta" }'
curlit "signed up student #16"      "/signup"           '{ "email": "student16@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Richa",  "lastname": "Kakkar" }'
curlit "signed up student #17"      "/signup"           '{ "email": "student17@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Shashank",  "lastname": "Singh" }'
curlit "signed up student #18"      "/signup"           '{ "email": "student18@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Mukund",  "lastname": "Sharma" }'
curlit "signed up student #19"      "/signup"           '{ "email": "student19@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Naman",  "lastname": "Pandey" }'
curlit "signed up student #20"      "/signup"           '{ "email": "student20@usf.edu",    "password": "pwd", "retype": "pwd","firstname": "Sarthak",  "lastname": "Pandey" }'

curl_login                          "instructor"        '{ "email": "instructor@usf.edu", "password": "pwd" }'

header 'ADDING QUESTION #1' #QID 1
curlit  'Added Question'            "/questions"                    '{ "title": "Question 1 Title", "stem": "Question 1 Stem?", "answer": "Question 1 answer"}'
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Question 1 distractor 1", "justification": "Q1 D1 Reference Justification"}'                                #D1
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Question 1 distractor 2", "justification": "Q1 D2 Reference Justification"}'                                #D2
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Question 1 distractor 3", "justification": "Q1 D3 Reference Justification"}'                                #D3
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Question 1 distractor 4", "justification": "Q1 D4 Reference Justification"}'                                #D4
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "1", "distractors_ids": [1, 2, 3, 4]}'

header 'ADDING QUESTION #2' #QID 2
curlit  'Added Question'            "/questions"                    '{ "title": "Question 2 Title", "stem": "Question 2 Stem?", "answer": "Question 2 answer"}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "Question 2 distractor 1", "justification": "Q2 D1 Reference Justification"}'                                #D5
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "Question 2 distractor 2", "justification": "Q2 D2 Reference Justification"}'                                #D6
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "Question 2 distractor 3", "justification": "Q2 D3 Reference Justification"}'                                #D7
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "Question 2 distractor 4 (not used in question)", "justification": "Q2 D4 Reference Justification"}'         #D8
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "2", "distractors_ids": [5, 6, 7]}'

header 'ADDING QUESTION #3' #QID 3
curlit  'Added Question'            "/questions"                    '{ "title": "Question 3 Title", "stem": "Question 3 stem?", "answer": "Question 3 answer"}'
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Question 3 distractor 1", "justification": "Q3 D1 Reference Justification"}'                                #D9
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Question 3 distractor 2", "justification": "Q3 D2 Reference Justification"}'                                #D10
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Question 3 distractor 3", "justification": "Q3 D3 Reference Justification"}'                                #D11
curlit  'Added distractor'          "/questions/3/distractors"      '{ "answer": "Question 3 distractor 4 (not used in question)", "justification": "Q3 D4 Reference Justification"}'         #D12
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "3", "distractors_ids": [9, 10, 11]}'

header 'ADDING QUESTION #4' #QID 4
curlit  'Added Question'            "/questions"                    '{ "title": "Question 4 Title", "stem": "Question 4 stem?", "answer": "Question 4 answer"}'
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "Question 4 distractor 1", "justification": "Q4 D1 Reference Justification"}'                                #D13
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "Question 4 distractor 2", "justification": "Q4 D2 Reference Justification"}'                                #D14
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "Question 4 distractor 3 (not used in question)", "justification": "Q4 D3 Reference Justification"}'         #D15
curlit  'Added distractor'          "/questions/4/distractors"      '{ "answer": "Question 4 distractor 4", "justification": "Q4 D4 Reference Justification"}'                                #D16
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "4", "distractors_ids": [13, 14, 16]}'

header 'ADDING QUESTION #5' #QID 5
curlit  'Added Question'            "/questions"                    '{ "title": "Question 5 Title", "stem": "Question 5 stem?", "answer": "Question 5 answer"}'
curlit  'Added distractor'          "/questions/5/distractors"      '{ "answer": "Question 5 distractor 1", "justification": "Q5 D1 Reference Justification"}'                                #D17
curlit  'Added distractor'          "/questions/5/distractors"      '{ "answer": "Question 5 distractor 2", "justification": "Q5 D2 Reference Justification"}'                                #D18
curlit  'Added distractor'          "/questions/5/distractors"      '{ "answer": "Question 5 distractor 3", "justification": "Q5 D3 Reference Justification"}'                                #D19
curlit  'Added distractor'          "/questions/5/distractors"      '{ "answer": "Question 5 distractor 4", "justification": "Q5 D4 Reference Justification"}'                                #D20
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "5", "distractors_ids": [17, 18, 19, 20]}'

header 'CREATING QUIZ #1 from above questions'
curlit  'Quiz Created'              "/quizzes"          '{ "title": "Test Quiz", "description": "This is just to make sure things are working", "deadline0": "2022-09-20T09:32", "deadline1": "2022-09-21T09:32", "deadline2": "2022-09-22T09:32", "deadline3": "2022-09-23T09:32", "deadline4": "2022-09-24T09:32", "questions_ids":[1,2,3,4,5]}'

# new question template
# curlit  'Added Question'            "/questions"        '{ "title": "", "stem": "", "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "2", "distractors_ids": [6, 5, 4]}'