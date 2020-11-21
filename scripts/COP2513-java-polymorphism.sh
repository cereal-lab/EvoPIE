#!/bin/bash

# PRE-REQUISITES
# run this script right after starting the server with
# flask DB-reboot && flask-run

source ./TestDB_functions.sh


header 'SIGNING UP INSTRUCTOR THEN LOGIN AS INSTRUCTOR'
#FIXME for now, we hardcode that user id 1 is an instructor; so we must sign him up first.
curlit "signed up instructor"       "/signup"                       '{ "email": "instructor@usf.edu", "password": "instructor", "firstname": "John", "lastname": "Keating" }'
curlit "signed up test student"     "/signup"                       '{ "email": "student@usf.edu", "password": "student", "firstname": "Test", "lastname": "Student" }'
curl_login                          "instructor"                    '{ "email": "instructor@usf.edu", "password": "instructor" }'

header 'ADDING QUESTION #1' #QID 1
curlit  'Added Question'            "/questions"                    '{ "title": "Explicit Downcasting", "stem": "Which one of these assignments is explicit downcasting?", "answer": "EBook b = (EBook) (new Book());"}'
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Book b = (Book) (new EBook());"}'     #D1
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Book b = new Book();"}'               #D2
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "Book b = (EBook)(new Book());"}'      #D3
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "1", "distractors_ids": [1, 2, 3]}'

header 'ADDING QUESTION #2' #QID 2
curlit  'Added Question'            "/questions"                    '{ "title": "Polymorphic ArrayList", "stem": "How would you declare an ArrayList that may contain Book, EBook, and AudioBook objects simultaneously?", "answer": "ArrayList<Book> list = new ArrayList<>();"}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "ArrayList<EBook> list = new ArrayList<>();"}'         #D5
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "ArrayList<AudioBook> list = new ArrayList<>();"}'     #D6
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "ArrayList<Object> list = new ArrayList<>();"}'        #D7
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "2", "distractors_ids": [4, 5, 6]}'

header 'ADDING QUESTION #2' #QID 3
curlit  'Added Question'            "/questions"                    '{ "title": "", "stem": "", "answer": ""}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": ""}'   #D8
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": ""}'   #D9
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": ""}'   #D10
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "3", "distractors_ids": [7, 8, 9]}'


header 'CREATING QUIZ & releasing it as STEP1'
curlit  'Quiz Created'              "/quizzes"                      '{ "title": "Extra Credit Quiz on Polymorphism", "description": "This is our first quiz using this software. It will be used as extra credit in COP2513 this semester. In all of the following questions, assume the superclass Book and its 2 direct subclasses EBook and AudioBook that we defined in the lectures.", "questions_ids":[1, 2, 3]}'
curlit  "Quiz released as STEP1"    "/quizzes/1/status"             '{ "status" : "STEP1" }'

# new question template
# curlit  'Added Question'            "/questions"        '{ "title": "", "stem": "", "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "2", "distractors_ids": [6, 5, 4]}'