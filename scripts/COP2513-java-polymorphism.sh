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
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "ArrayList<EBook> list = new ArrayList<>();"}'         #D4
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "ArrayList<AudioBook> list = new ArrayList<>();"}'     #D5
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "ArrayList<Object> list = new ArrayList<>();"}'        #D6
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "2", "distractors_ids": [4, 5, 6]}'

header 'ADDING QUESTION #3' #QID 3
curlit  'Added Question'            "/questions"                    '{ "title": "Polymorphic Method", "stem": "Which of the following polymorphic static method is correct?", "answer": "public static String onlyEBooks(Book b){ if(b instanceof EBook) return b.toString(); else return \"\";}"}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public static String onlyEBooks(Book b){ return ((EBook) b).toString();}"}'   #D7
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public static String onlyEBooks(Book b){ return ((Book) b).toString();}"}'   #D8
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public static String onlyEBooks(Book b){ if(!(EBook)b) return b.toString(); else return \"\";}"}'   #D9
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "3", "distractors_ids": [7, 8, 9]}'

header 'ADDING QUESTION #4' #QID 4
curlit  'Added Question'            "/questions"                    '{ "title": "Constructor Chaining", "stem": "This question does not relate to the classes that we had as examples in the lectures. MySuperClass has a 1-arg constructors taking an int as parameter and a public attribute named value, also of type int. Which of the following constructors would be correct as the only constructor in MySubClass if it extends MySuperClass?", "answer": "public MySubClass(int v){ super(v); }"}'
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public MySubClass(int v){ this(v); }"}'   #D10
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public MySubClass(int v){ super.value = v; }"}'   #D11
curlit  'Added distractor'          "/questions/2/distractors"      '{ "answer": "public MySubClass(int v){ }"}'   #D12
curlit  'QuizQuestion composed'     "/quizquestions"                '{ "qid": "4", "distractors_ids": [10, 11, 12]}'

header 'ADDING QUESTION #5' #QID 5
curlit  'Added Question'            "/questions"                    '{ "title": "Opinion question", "stem": "What if we would use this kind of 2-step quiz all semester long? Select the option that is the closest to your opinion: Being able to revise my answer after seeing other students justifications is...", "answer": "...useful in helping me catch a misunderstanding on my part."}'
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