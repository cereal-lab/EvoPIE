#!/bin/bash

# PRE-REQUISITES
# empty DB after a flask DB-reboot

source ../Extensive\ Test/TestLib.sh

# NOTE we keep these quizzes / questions / justifications simple by not putting code or special characters in them that would need to be escaped
# this makes these scripts to test the functionalities of most of the UI but not detect any problems related to bad JSON formatting, 
# presence of non-rendered HTML tags in the outputs, and things of this nature.

header 'SIGNING UP INSTRUCTOR & STUDENT ACCOUNTS, THEN LOGIN AS INSTRUCTOR'
#FIXME for now, we hardcode that user id 1 is an instructor; so we must sign him up first.
curlit "signed up instructor #1"    "/signup"           '{ "email": "instructor1@usf.edu",   "password": "pwd", "retype": "pwd","firstname": "Phil",    "lastname": "Ventura" }'
curlit "signed up instructor #2"    "/signup"           '{ "email": "instructor2@usf.edu",   "password": "pwd", "retype": "pwd","firstname": "Alessio", "lastname": "Gaspar" }'
curlit "signed up student #1"       "/signup"           '{ "email": "student1@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Anakin",   "lastname": "Skywalker" }'
curlit "signed up student #2"       "/signup"           '{ "email": "student2@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Ahsoka",   "lastname": "Tano" }'
curlit "signed up student #3"       "/signup"           '{ "email": "student3@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Obi-Wan",  "lastname": "Kenobi" }'
curlit "signed up student #4"       "/signup"           '{ "email": "student4@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Rey",      "lastname": "Skywalker" }'
curlit "signed up student #5"       "/signup"           '{ "email": "student5@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Mace",     "lastname": "Windu" }'
curlit "signed up student #6"       "/signup"           '{ "email": "student6@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "Luke",     "lastname": "Skywalker" }'
curlit "signed up student #7"       "/signup"           '{ "email": "student7@usf.edu",     "password": "pwd", "retype": "pwd","firstname": "BB",       "lastname": "8" }'

curl_login                          "instructor"        '{ "email": "instructor@usf.edu", "password": "pwd" }'
