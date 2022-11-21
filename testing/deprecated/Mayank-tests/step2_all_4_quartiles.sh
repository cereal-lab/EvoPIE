#!/bin/bash

# PRE-REQUISITES
#   ./setup.sh
#   ./step1.sh

source ./TestLib.sh

#login as INSTRUCTOR to release quiz in step #2
curl_login                          "instructor"            '{ "email": "instructor@usf.edu", "password": "pwd" }'
curlit  "set quiz to step 2"        "/quizzes/1/status"     ' { "status" : "STEP2" }'
# step #2
header "Step #2 for Student #1"
curl_login              "student #1"        '{ "email": "student1@usf.edu", "password": "pwd"}'
curlit "GET quiz"       "/quizzes/1/take"   ''
curlit "POST quiz"      "/quizzes/1/take"   '{ "revised_responses": {"1":"-1", "2":"-1", "3":"-1"} }'
# we simulate each student liking some of the justifications for question #1 from the other students
# we do not guarantee that the student would have seen these as part of the randomly selected
# justifications to be displayed for each alternative
# like "s3q1d1"    "27"
# like "s3q1d2"    "28" 
# like "s3q1d4"    "30" 
# like "s2q2sol"   "22"
# like "s3q2d6"    "33" # gets max likes
# like "s2q3d10"   "24"
like "s3q3d10"   "37" # one like only
like "s4q1d1"   "40"
like "s4q1d2"   "41"
like "s6q1d4"   "69"

header "Step #2 for Student #2"
curl_login              "student #2"        '{ "email": "student2@usf.edu", "password": "pwd"}'
curlit "GET quiz"       "/quizzes/1/take"   ''
curlit "POST quiz"      "/quizzes/1/take"   '{ "revised_responses": {"1":"3" , "2":"-1", "3":"10"} }'
# like "s1q1d1"    "1"
# like "s1q1d4"    "4"
# like "s3q1d1"    "27"
# like "s3q1d2"    "28" 
like "s3q1d4"    "30"
like "s3q2d6"    "33"
like "s5q1d3"   "55"
like "s5q1d4"   "56"
# like "s3q3d10"   "37"
like "s4q1d3"   "42"
like "s9q2d7"   "112"
like "s9q2sol"   "113"

header "Step #2 for Student #3"
curl_login            "student #3"        '{ "email": "student3@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
# like "s1q1d4"    "4"
like "s1q1sol"   "5"
like "s2q1d4"    "17" 
# like "s2q2sol"   "22"
# like "s2q3d10"   "24"
like "s4q1d4"   "43"
like "s6q1sol"   "70"
like "s6q2d5"   "71"
like "s8q2d6"   "98"
like "s8q2d7"   "99"

header "Step #2 for Student #4"
curl_login            "student #4"        '{ "email": "student4@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
like "s5q1sol"   "57"
like "s7q2d5"   "84"
like "s7q2d6"   "85"
like "s10q3d9"   "127"

header "Step #2 for Student #5"
curl_login            "student #5"        '{ "email": "student5@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
like "s6q1d1"   "66"
like "s6q1d2"   "67"
like "s6q1d3"   "68"
like "s7q1d4"   "82"
like "s7q1sol"   "83"
like "s8q2d5"   "97"


header "Step #2 for Student #6"
curl_login            "student #6"        '{ "email": "student6@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
like "s7q1d3"   "81"
like "s8q1d4"   "95"
like "s8q1sol"   "96"
like "s9q2d6"   "111"
like "s10q2sol"   "126"


header "Step #2 for Student #7"
curl_login            "student #7"        '{ "email": "student7@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
like "s8q1d1"   "92"
like "s8q1d2"   "93"
like "s8q1d3"   "94"
like "s9q1sol"   "109"
like "s9q2d5"   "110"
like "s10q2d7"   "125"



header "Step #2 for Student #8"
curl_login            "student #8"        '{ "email": "student8@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
like "s9q1d1"   "105"
like "s9q1d4"   "108"
like "s10q2d5"   "123"
like "s10q2d6"   "124"



header "Step #2 for Student #9"
curl_login            "student #9"        '{ "email": "student9@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
like "s10q1d1"   "118"
like "s10q1d2"   "119"
like "s10q1d3"   "120"
like "s10q1d4"   "121"
like "s10q1sol"   "122"


header "Step #2 for Student #10"
curl_login            "student #10"        '{ "email": "student10@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
like "s9q1d2"   "106"
like "s9q1d3"   "107"
like "s7q1d1"   "79"
like "s7q1d2"   "80"
like "s5q1d1"   "53"
like "s5q1d2"   "54"
like "s2q1d1"    "14"

# These are the expected results in the grading page for quiz #1 http://127.0.0.1:5000/quiz/1/grades
# They have been verified by hand by looking up the information in the popups from the likes given,
# likes received buttons 
# student   initial score   revised score   likes given     likes received      scores
# 1         0               3               5               6                   6 (n/a, no maxlikes yet)
# 2         0               1               5               6                   6
# 3         0               1               5               7                   7


# Each student has been exposed to 5 + 4 + 4 = 13 alternatives for the quiz.

# At max, any student can therefore give 26 likes to all other students (2 in this scripted test).
# The MaxLikes value in the formula is used to determine how many likes a student should be able to 
# give. For instance, here we could say 50% of 13 = 7 rounded up.
# Once we have this number, we determine the score value for each like that this student has given. 
# If they gave 7 or less likes, each like is worth 1 point. If they go above 7, their likes should 
# be progressively worth less and less. Their likes should reach a score value of 0 as soon as they
# gave out at least 1 like to each justification they saw in the step 2 page. That is 26 in our example.

# At max, any student can therefore receive 13 * (# of other students) likes.
# This is assuming that ALL their justifications were shown to ALL other students AND were liked :)

# In this specific test, because we have 3 students total, each of them can only receive justifications
# from two other students. In the code, we try to show, maximum, 3 justification per alternative but
# here we end up with less due to lack of enough participants.
