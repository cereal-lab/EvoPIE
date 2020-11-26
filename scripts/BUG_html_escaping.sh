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

header 'ADDING QUESTION #2'
# BUG The <AudioBook> parts disappear when we iterate over the javascript in student2.html even thought they are
# properly rendered by jinja2 when displaying the actual alternatives...
curlit  'Added Question'            "/questions"                    '{ "title": "Polymorphic ArrayList", "stem": "How would you declare an ArrayList that may contain Book, EBook, and AudioBook objects simultaneously?", "answer": "ArrayList<Book> list = new ArrayList<>();"}'
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "ArrayList<EBook> list = new ArrayList<>();"}'         
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "ArrayList<AudioBook> list = new ArrayList<>();"}'     
curlit  'Added distractor'          "/questions/1/distractors"      '{ "answer": "ArrayList<Object> list = new ArrayList<>();"}'        
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "1", "distractors_ids": [1, 2, 3]}'

header 'ADDING QUESTION #3'
# BUG the following question casues a bug when Json.parsing the usable variable in student1.html
# it will probably be an issue with studen2.html too since there are "" that are misinterpreted
# as closing the json strings instead of being just elements of these strings.
# see item in todo list about sanitizing code.
curlit  'Added Question'            "/questions"                    '{ "title": "Polymorphic Method", "stem": "Which of the following polymorphic static method is correct?", "answer": "public static String onlyEBooks(Book b){ if(b instanceof EBook) return b.toString(); else return \\\"\\\";}"}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public static String onlyEBooks(Book b){ return ((EBook) b).toString();}"}'   
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public static String onlyEBooks(Book b){ return ((Book) b).toString();}"}'   
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public static String onlyEBooks(Book b){ if(!(EBook)b) return b.toString(); else return \\\"\\\";}"}'   
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "2", "distractors_ids": [4, 5, 6]}'


header 'CREATING QUIZ & releasing it as STEP1'
curlit  'Quiz Created'              "/quizzes"                      '{ "title": "Debugging Quiz", "description": "Testing HTML escaping", "questions_ids":[1, 2]}'
curlit  "Quiz released as STEP1"    "/quizzes/1/status"             '{ "status" : "STEP1" }'
