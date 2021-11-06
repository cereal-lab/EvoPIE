#!/bin/bash

if [[ $# -ne 1 ]]
then
    echo "ERROR - must provide 1 argument: sqlite3 file name"
    exit
fi

FILE=$1

if [[ ! -f $FILE ]]
then
    echo "ERROR - File $FILE does not exist"
    exit
fi

QUERY="select user.last_name, user.first_name, user.email,quiz_attempt.initial_responses, quiz_attempt.revised_responses from user,quiz_attempt on user.id==quiz_attempt.student_id order by user.last_name COLLATE NOCASE;"
sqlite3 $1 "$QUERY" | awk '$0 ~ FS { print NF-1, $0 }' IGNORECASE=1 FS="-1" 
# awk is used to display the number of correct answers per line



