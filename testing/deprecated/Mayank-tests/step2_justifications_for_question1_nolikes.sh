#!/bin/bash

# PRE-REQUISITES
#   ./setup.sh
#   ./step1.sh

source ./TestLib.sh

#login as INSTRUCTOR to release quiz in step #2
curl_login                          "instructor"            '{ "email": "instructor@usf.edu", "password": "pwd" }'
curlit  "set quiz to step 2"        "/quizzes/1/status"     ' { "status" : "STEP2" }'
# s3 gets max likes for justifications 27, 30, 33, 37
# step #2
header "Step #2 for Student #1"
curl_login              "student #1"        '{ "email": "student1@usf.edu", "password": "pwd"}'
curlit "GET quiz"       "/quizzes/1/take"   ''
curlit "POST quiz"      "/quizzes/1/take"   '{ "revised_responses": {"1":"-1", "2":"-1", "3":"-1"} }'
# we simulate each student liking some of the justifications for question #1 from the other students
# we do not guarantee that the student would have seen these as part of the randomly selected
# justifications to be displayed for each alternative
# like "s2q1d1"    "14"
# like "s3q1d1"    "27"
# like "s3q1d2"    "28" 
# like "s3q1d4"    "30" 
like "s2q2sol"   "22"
like "s3q2d6"    "33"
like "s2q3d10"   "24"
like "s3q3d10"   "37" 

header "Step #2 for Student #2"
curl_login              "student #2"        '{ "email": "student2@usf.edu", "password": "pwd"}'
curlit "GET quiz"       "/quizzes/1/take"   ''
curlit "POST quiz"      "/quizzes/1/take"   '{ "revised_responses": {"1":"3" , "2":"-1", "3":"10"} }'
# like "s1q1d1"    "1"
# like "s1q1d4"    "4"
# like "s3q1d1"    "27"
# like "s3q1d2"    "28" 
# like "s3q1d4"    "30"
like "s3q2d6"    "33"
like "s3q3d10"   "37"

header "Step #2 for Student #3"
curl_login            "student #3"        '{ "email": "student3@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
# like "s1q1d4"    "4"
# like "s1q1sol"   "5"
# like "s2q1d4"    "17" 
like "s2q2sol"   "22"
like "s2q3d10"   "24"

header "Step #2 for Student #4"
curl_login            "student #4"        '{ "email": "student4@usf.edu", "password": "pwd"}'
curlit "GET quiz"     "/quizzes/1/take"   ''
curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
# like "s1q1d1"    "1"
# like "s1q1d4"    "4"
# like "s1q1sol"   "5"

# like "s2q1d4"    "17" 
like "s2q2sol"   "22"
like "s2q3d10"   "24"

# like "s3q1d1"    "27" 
# like "s3q1d2"    "28"
# like "s3q1d4"    "30"
like "s3q2d6"    "33"
like "s3q3d10"   "37"


# for now, all remaining students like the same justifications and provide the same revised responses
for s in {5..10}
do
    header "Step #2 for Student #${s}"
    curl_login            "student #${s}"        '{ "email": "student'${s}'@usf.edu", "password": "pwd"}'
    curlit "GET quiz"     "/quizzes/1/take"   ''
    curlit "POST quiz"    "/quizzes/1/take"   '{ "revised_responses": {"1":"4" , "2":"7", "3":"-1"} }'
    # like "s1q1d1"    "1"
    # like "s1q1d4"    "4"
    # like "s1q1sol"   "5"

    # like "s2q1d4"    "17" 
    like "s2q2sol"   "22"
    like "s2q3d10"   "24"

    # like "s3q1d1"    "27" 
    # like "s3q1d4"    "30"
    # like "s3q2d6"    "33"
    # like "s3q3d10"   "37"
done

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
