#!/bin/bash

# PRE-REQUISITES
# run this script right after starting the server with
# flask DB-reboot && flask-run

source ../TestDB_functions.sh


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
curlit  'Added Question'            "/questions"                    '{ "title": "Polymorphic methods", "stem": "Assuming a static polymorphic method public static void display(Book b){...}. Which of the following type of argument would NOT be accepted?", "answer": "They would all be accepted."}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "Book"}'         #D4
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "EBook"}'     #D5
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "AudioBook"}'        #D6
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "2", "distractors_ids": [4, 5, 6]}'

header 'ADDING QUESTION #3' #QID 3
curlit  'Added Question'            "/questions"                    '{ "title": "Polymorphic Method", "stem": "Let us assume that Book, EBook and AudioBook have an additional method (overridden in the subclasses) that places an order for that item. We want a polymorphic static method that will place an order on its parameter but only if it is an EBook. Which of the following is correct?", "answer": "public static void placeOrder(Book b){ if(b instanceof EBook) b.placeOrder();}"}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public static void placeOrder(Book b){ ((EBook) b).placeOrder();}"}'   #D7
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public static void placeOrder(Book b){ ((Book) b).placeOrder();}"}'   #D8
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public static void placeOrder(Book b){ if(!(EBook)b) b.placeOrder(); }"}'   #D9
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "3", "distractors_ids": [7, 8, 9]}'

header 'ADDING QUESTION #4' #QID 4
curlit  'Added Question'            "/questions"                    '{ "title": "Constructor Chaining", "stem": "This question does not relate to the classes that we had as examples in the lectures. MySuperClass has a 1-arg constructors taking an int as parameter and a public attribute named value, also of type int. Which of the following constructors would be correct as the only constructor in MySubClass if it extends MySuperClass?", "answer": "public MySubClass(int v){ super(v); }"}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public MySubClass(int v){ this(v); }"}'   #D10
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public MySubClass(int v){ super.value = v; }"}'   #D11
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public MySubClass(int v){ }"}'   #D12
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "4", "distractors_ids": [10, 11, 12]}'

header 'ADDING QUESTION #5' #QID 5
curlit  'Added Question'            "/questions"                    '{ "title": "Opinion question", "stem": "What if we would use this kind of 2-step quiz all semester long? Select the option that is the closest to your opinion: Being able to revise my answer after seeing other students justifications is...", "answer": "...useful because it may help me catch a potential misunderstanding on my part."}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "...useless because I do not need help."}'   #D13
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "...useless because the justifications of my peers are not helpful."}'   #D14
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "...useless because of other reasons."}'   #D15
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "5", "distractors_ids": [13, 14, 15]}'

header 'CREATING QUIZ & releasing it as STEP1'
curlit  'Quiz Created'              "/quizzes"                      '{ "title": "Extra Credit Quiz on Polymorphism", "description": "In some of the following questions, we will assume that we have the superclass Book, and its 2 direct subclasses EBook and AudioBook, that were defined in the lectures.", "questions_ids":[1, 2, 3, 4, 5]}'
curlit  "Quiz released as STEP1"    "/quizzes/1/status"             '{ "status" : "STEP1" }'

# new question template
# curlit  'Added Question'            "/questions"        '{ "title": "", "stem": "", "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'Added distractor'          "/distractors"      '{ "answer": ""}'
# curlit  'QuizQuestion composed'     "/quizquestions"    '{ "qid": "2", "distractors_ids": [6, 5, 4]}'