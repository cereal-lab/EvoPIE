#!/bin/bash

# PRE-REQUISITES
#   ./setup.sh
#   ./step1.sh

source ./TestLib.sh

#login as INSTRUCTOR to release quiz in step #2
curl_login                          "instructor"            '{ "email": "instructor@usf.edu", "password": "pwd" }'
curlit  "set quiz to step 2"        "/quizzes/1/status"     ' { "status" : "STEP2" }'
# step #2

# max likes = 3 * 22 = 66
# 14 likes
header "Step #2 for Student #1"
curl_login            "student #1"        '{ "email": "student1@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "GET justifications"     "/student/1"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"-1", "3":"-1", "4":"13", "5": "17"} }'
# like "s1q1d1"    "1"
# like "s1q1d2"    "2"
# like "s1q1d4"    "4"
# like "s1q1sol"   "5"

# like "s5q1d1"    "89"
like "s5q1d2"    "90"
like "s5q1d3"    "91"
like "s5q1d4"    "92"
like "s5q1sol"   "93"
like "s5q2d5"   "94"
like "s5q2d6"   "95"
like "s5q2d7"   "96"
like "s5q2sol"   "97"
like "s5q3d9"   "98"
like "s5q3d10"   "99"
like "s5q3d11"   "100"
like "s5q3sol"   "101"
like "s5q4d13"   "102"
like "s5q4d14"   "103"
# like "s5q4d16"   "104"
# like "s5q4sol"   "105"

# 15 likes
header "Step #2 for Student #2"
curl_login            "student #2"        '{ "email": "student2@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "GET justifications"     "/student/1"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"-1", "3":"-1", "4":"13", "5": "17"} }'
# like "s1q1d1"    "1"
# like "s1q1d2"    "2"
# like "s1q1d4"    "4"
# like "s1q1sol"   "5"

# like "s5q1d1"    "89"
like "s5q1d2"    "90"
like "s5q1d3"    "91"
like "s5q1d4"    "92"
like "s5q1sol"   "93"
like "s5q2d5"   "94"
like "s5q2d6"   "95"
like "s5q2d7"   "96"
like "s5q2sol"   "97"
like "s5q3d9"   "98"
like "s5q3d10"   "99"
like "s5q3d11"   "100"
like "s5q3sol"   "101"
like "s5q4d13"   "102"
like "s5q4d14"   "103"
like "s5q4d16"   "104"
# like "s5q4sol"   "105"

# 16 likes
header "Step #2 for Student #3"
curl_login            "student #3"        '{ "email": "student3@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "GET justifications"     "/student/1"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"-1", "3":"-1", "4":"13", "5": "17"} }'
# like "s1q1d1"    "1"
# like "s1q1d2"    "2"
# like "s1q1d4"    "4"
# like "s1q1sol"   "5"

like "s5q1d1"    "89"
like "s5q1d2"    "90"
like "s5q1d3"    "91"
like "s5q1d4"    "92"
like "s5q1sol"   "93"
like "s5q2d5"   "94"
like "s5q2d6"   "95"
like "s5q2d7"   "96"
like "s5q2sol"   "97"
like "s5q3d9"   "98"
like "s5q3d10"   "99"
like "s5q3d11"   "100"
like "s5q3sol"   "101"
like "s5q4d13"   "102"
like "s5q4d14"   "103"
like "s5q4d16"   "104"
# like "s5q4sol"   "105"

# 17 likes
header "Step #2 for Student #4"
curl_login            "student #4"        '{ "email": "student4@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "GET justifications"     "/student/1"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"-1", "3":"-1", "4":"13", "5": "17"} }'
# like "s1q1d1"    "1"
# like "s1q1d2"    "2"
# like "s1q1d4"    "4"
# like "s1q1sol"   "5"

like "s5q1d1"    "89"
like "s5q1d2"    "90"
like "s5q1d3"    "91"
like "s5q1d4"    "92"
like "s5q1sol"   "93"
like "s5q2d5"   "94"
like "s5q2d6"   "95"
like "s5q2d7"   "96"
like "s5q2sol"   "97"
like "s5q3d9"   "98"
like "s5q3d10"   "99"
like "s5q3d11"   "100"
like "s5q3sol"   "101"
like "s5q4d13"   "102"
like "s5q4d14"   "103"
like "s5q4d16"   "104"
like "s5q4sol"   "105"

# 20 likes
header "Step #2 for Student #5"
curl_login            "student #5"        '{ "email": "student5@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "GET justifications"     "/student/1"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"-1", "3":"-1", "4":"13", "5": "17"} }'
like "s1q1d1"    "1"
like "s1q1d2"    "2"
like "s1q1d3"    "3"
like "s1q1d4"    "4"
like "s1q1sol"   "5"
like "s1q2d5"    "6"
like "s1q2d6"    "7"
like "s1q2d7"    "8"
like "s1q2sol"   "9"

like "s2q1d1"    "23"
like "s2q1d2"    "24"
like "s2q1d3"    "25"
like "s2q1d4"    "26"
like "s2q1sol"   "27"

like "s2q1d4"    "17" 
like "s2q2sol"   "22"
like "s2q3d10"   "24"

like "s3q1d4"    "30"
like "s3q2d6"    "33"
like "s3q3d10"   "37"
like "s3q3sol"   "57"

# like "s4q1d1"    "67"
# like "s4q1d2"    "68"
# like "s4q1d3"    "69"
# like "s4q1d4"    "70"
# like "s4q1sol"   "71"

# 19 likes
header "Step #2 for Student #6"
curl_login            "student #6"        '{ "email": "student6@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "GET justifications"     "/student/1"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"-1", "3":"-1", "4":"13", "5": "17"} }'
like "s1q1d1"    "1"
like "s1q1d2"    "2"
like "s1q1d3"    "3"
like "s1q1d4"    "4"
like "s1q1sol"   "5"
like "s1q2d5"    "6"
like "s1q2d6"    "7"
like "s1q2d7"    "8"
like "s1q2sol"   "9"

like "s2q1d1"    "23"
like "s2q1d2"    "24"
like "s2q1d3"    "25"
like "s2q1d4"    "26"
like "s2q1sol"   "27"

like "s2q1d4"    "17" 
like "s2q2sol"   "22"
like "s2q3d10"   "24"

like "s3q1d4"    "30"
like "s3q2d6"    "33"
# like "s3q3d10"   "37"
# like "s3q3sol"   "57"

# like "s4q1d1"    "67"
# like "s4q1d2"    "68"
# like "s4q1d3"    "69"
# like "s4q1d4"    "70"
# like "s4q1sol"   "71"

# 20 likes
header "Step #2 for Student #7"
curl_login            "student #7"        '{ "email": "student7@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "GET justifications"     "/student/1"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"-1", "3":"-1", "4":"13", "5": "17"} }'
like "s1q1d1"    "1"
like "s1q1d2"    "2"
like "s1q1d3"    "3"
like "s1q1d4"    "4"
like "s1q1sol"   "5"
like "s1q2d5"    "6"
like "s1q2d6"    "7"
like "s1q2d7"    "8"
like "s1q2sol"   "9"

like "s2q1d1"    "23"
like "s2q1d2"    "24"
like "s2q1d3"    "25"
like "s2q1d4"    "26"
like "s2q1sol"   "27"

like "s1q4sol"    "17" 
like "s1q5sol"   "22"
# like "s2q3d10"   "24"

like "s2q2d7"    "30"
like "s3q3d10"    "33"
# like "s2q4d14"   "37"
like "s3q3sol"   "57"

# like "s4q1d1"    "67"
# like "s4q1d2"    "68"
# like "s4q1d3"    "69"
# like "s4q1d4"    "70"
# like "s4q1sol"   "71"

# 23 likes
for s in {8..9}
do
    header "Step #2 for Student #${s}"
    curl_login            "student #${s}"        '{ "email": "student'${s}'@usf.edu", "password": "pwd"}'
    curlit "GET quiz"     "/quizzes/1/take"   ''
    curlit "GET justifications"     "/student/1"   ''
    curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"-1", "3":"-1", "4":"-1", "5": "17"} }'
    like "s1q1d1"    "1"
    like "s1q1d2"    "2"
    like "s1q1d3"    "3"
    like "s1q1d4"    "4"
    like "s1q1sol"   "5"
    like "s1q2d5"    "6"
    like "s1q2d6"    "7"
    like "s1q2d7"    "8"
    like "s1q2sol"   "9"

    like "s2q1d1"    "23"
    like "s2q1d2"    "24"
    like "s2q1d3"    "25"
    like "s2q1d4"    "26"
    like "s2q1sol"   "27"

    like "s2q1d4"    "17" 
    like "s2q2sol"   "22"
    like "s2q3d10"   "24"

    like "s3q1d4"    "30"
    like "s3q2d6"    "33"
    like "s3q3d10"   "37"
    like "s3q3sol"   "57"

    like "s4q1d1"    "67"
    like "s4q1d2"    "68"
done

    # 39 likes
    header "Step #2 for Student #10" 
    curl_login            "student #10"        '{ "email": "student10@usf.edu", "password": "pwd"}'
    curlit "GET quiz"     "/quizzes/1/take"   ''
    curlit "GET justifications"     "/student/1"   ''
    curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"-1", "3":"-1", "4":"13", "5": "17"} }'
    like "s1q1d1"    "1"
    like "s1q1d2"    "2"
    like "s1q1d3"    "3"
    like "s1q1d4"    "4"
    like "s1q1sol"   "5"
    like "s1q2d5"    "6"
    like "s1q2d6"    "7"
    like "s1q2d7"    "8"
    like "s1q2sol"   "9"

    like "s2q1d1"    "23"
    like "s2q1d2"    "24"
    like "s2q1d3"    "25"
    like "s2q1d4"    "26"
    like "s2q1sol"   "27"

    like "s2q1d4"    "17" 
    like "s2q2sol"   "22"
    like "s2q3d10"   "24"

    like "s3q1d4"    "30"
    like "s3q2d6"    "33"
    like "s3q3d10"   "37"
    like "s3q3sol"   "57"

    like "s4q1d1"    "67"
    like "s4q1d2"    "68"
    like "s4q1d3"    "69"
    like "s4q1d4"    "70"
    like "s4q1sol"   "71"

    like "s5q1d1"    "89"
    like "s5q1d2"    "90"
    like "s5q1d3"    "91"
    like "s5q1d4"    "92"
    like "s5q1sol"   "93"
    like "s5q2d5"   "94"
    like "s5q2d6"   "95"
    like "s5q2d7"   "96"
    like "s5q2sol"   "97"
    like "s5q3d9"   "98"
    like "s5q3d10"   "99"
    like "s5q3d11"   "100"
    like "s5q3sol"   "101"
    like "s5q4d13"   "102"
    like "s5q4d14"   "103"
    like "s5q4d16"   "104"

# 30 likes, 3 correct    
for s in {11..14}
do
    header "Step #2 for Student #${s}"
    curl_login            "student #${s}"        '{ "email": "student'${s}'@usf.edu", "password": "pwd"}'
    curlit "GET quiz"     "/quizzes/1/take"   ''
    curlit "GET justifications"     "/student/1"   ''
    curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"-1", "3":"-1", "4":"-1", "5": "17"} }'
    like "s1q1d1"    "1"
    like "s1q1d2"    "2"
    like "s1q1d3"    "3"
    like "s1q1d4"    "4"
    like "s1q1sol"   "5"
    like "s1q2d5"    "6"
    like "s1q2d6"    "7"
    like "s1q2d7"    "8"
    like "s1q2sol"   "9"


    like "s2q1d4"    "26"
    like "s2q1sol"   "27"

    like "s2q1d4"    "17" 
    like "s2q2sol"   "22"
    like "s2q3d10"   "24"

    like "s3q1d4"    "30"
    like "s3q2d6"    "33"
    like "s3q3d10"   "37"
    like "s3q3sol"   "57"

    like "s4q1d1"    "67"
    like "s4q1sol"   "71"

    like "s5q1d1"    "89"
    like "s5q1d2"    "90"
    like "s5q1d3"    "91"
    like "s5q2d6"   "95"
    like "s5q2d7"   "96"
    like "s5q2sol"   "97"
    like "s5q3d9"   "98"
    like "s5q3d10"   "99"
    like "s5q3d11"   "100"
    like "s5q3sol"   "101"
    like "s5q4d13"   "102"
    like "s5q4d14"   "103"
    like "s5q4d16"   "104"
done

# for now, all remaining students like the same justifications and provide the same revised responses
for s in {15..19}
do
    header "Step #2 for Student #${s}"
    curl_login            "student #${s}"        '{ "email": "student'${s}'@usf.edu", "password": "pwd"}'
    curlit "GET quiz"     "/quizzes/1/take"   ''
    curlit "GET justifications"     "/student/1"   ''
    curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"-1" , "2":"-1", "3":"-1", "4":"-1", "5": "-1"} }'
    like "s1q1d1"    "1"
    like "s1q1d2"    "2"
    like "s1q1d3"    "3"
    like "s1q1d4"    "4"
    like "s1q1sol"   "5"
    like "s1q2d5"    "6"
    like "s1q2d6"    "7"
    like "s1q2d7"    "8"
    like "s1q2sol"   "9"

    like "s2q1d1"    "23"
    like "s2q1d2"    "24"
    like "s2q1d3"    "25"
    like "s2q1d4"    "26"
    like "s2q1sol"   "27"

    like "s2q1d4"    "17" 
    like "s2q2sol"   "22"
    like "s2q3d10"   "24"

    like "s3q1d4"    "30"
    like "s3q2d6"    "33"
    like "s3q3d10"   "37"
    like "s3q3sol"   "57"

    like "s4q1d1"    "67"
    like "s4q1d2"    "68"
    like "s4q1d3"    "69"
    like "s4q1d4"    "70"
    like "s4q1sol"   "71"

    like "s5q1d1"    "89"
    like "s5q1d2"    "90"
    like "s5q1d3"    "91"
    like "s5q1d4"    "92"
    like "s5q1sol"   "93"
    like "s5q2d5"   "94"
    like "s5q2d6"   "95"
    like "s5q2d7"   "96"
    like "s5q2sol"   "97"
    like "s5q3d9"   "98"
    like "s5q3d10"   "99"
    like "s5q3d11"   "100"
    like "s5q3sol"   "101"

done

# max likes

header "Step #2 for Student #20"
curl_login            "student #20"        '{ "email": "student20@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "GET justifications"     "/student/1"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"-1" , "2":"-1", "3":"-1", "4":"-1", "5": "-1"} }'
    like "s1q1d1"    "1"
    like "s1q1d2"    "2"
    like "s1q1d3"    "3"
    like "s1q1d4"    "4"
    like "s1q1sol"   "5"
    like "s1q2d5"    "6"
    like "s1q2d6"    "7"
    like "s1q2d7"    "8"
    like "s1q2sol"   "9"

    like "s2q1d1"    "23"
    like "s2q1d2"    "24"
    like "s2q1d3"    "25"
    like "s2q1d4"    "26"
    like "s2q1sol"   "27"

    like "s2q1d4"    "17" 
    like "s2q2sol"   "22"
    like "s2q3d10"   "24"

    like "s3q1d4"    "30"
    like "s3q2d6"    "33"
    like "s3q3d10"   "37"
    like "s3q3sol"   "57"

    like "s4q1d1"    "67"
    like "s4q1d2"    "68"
    like "s4q1d3"    "69"
    like "s4q1d4"    "70"
    like "s4q1sol"   "71"

    like "s5q1d1"    "89"
    like "s5q1d2"    "90"
    like "s5q1d3"    "91"
    like "s5q1d4"    "92"
    like "s5q1sol"   "93"
    like "s5q2d5"   "94"
    like "s5q2d6"   "95"
    like "s5q2d7"   "96"
    like "s5q2sol"   "97"
    like "s5q3d9"   "98"
    like "s5q3d10"   "99"
    like "s5q3d11"   "100"
    like "s5q3sol"   "101"
    like "s5q4d13"   "102"
    like "s5q4d14"   "103"
    like "s5q4d16"   "104"
    like "s5q4sol"   "105"
    like "s5q5d17"   "106"
    like "s5q5d18"   "107"
    like "s5q5d19"   "108"
    like "s5q5d20"   "109"
    like "s5q5sol"   "110"
    like "s6q1d1"   "111"
    like "s6q1d2"   "112"
    like "s6q1d3"   "113"
    like "s6q1d4"   "114"
    like "s6q1sol"   "115"


# These are the expected results in the grading page for quiz #1 http://127.0.0.1:5000/grades/1
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
