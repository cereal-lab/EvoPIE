#!/bin/bash

# Provide name of sqlite file as argument
sqlite3 $1 "select user.last_name, user.first_name, user.email,quiz_attempt.initial_responses, quiz_attempt.revised_responses from user,quiz_attempt on user.id==quiz_attempt.student_id order by user.last_name COLLATE NOCASE;"
