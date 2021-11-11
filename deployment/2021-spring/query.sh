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

QUERY="SELECT user.last_name, user.first_name, user.email,quiz_attempt.initial_responses, quiz_attempt.revised_responses FROM user,quiz_attempt,quiz ON user.id==quiz_attempt.student_id AND quiz.id==quiz_attempt.quiz_id AND quiz.title==\"PLQ1\" ORDER BY user.last_name COLLATE NOCASE;"
#sqlite3 $1 "$QUERY" | awk '$0 ~ FS { print NF-1, $0 }' IGNORECASE=1 FS="-1" 
# awk is used to display the number of correct answers per line


#sqlite3 $1 "$QUERY" | awk '$0 ~ FS { print NF-1, $0 }' IGNORECASE=1 FS="-1" 


# all fields w/o summing points
#sqlite3 $1 "$QUERY" | awk '$0 { printf "%-20s\t%-10s\t%s\t%s\n",$1,$2,$4,$5}' FS="|"

# Performance on STEP 1
#sqlite3 $1 "$QUERY" | awk '$0 { printf "%-20s\t%-10s\t%s\n",$1,$2,$4}' FS="|" | awk '$0 ~ FS { print NF-1, $0 }' IGNORECASE=1 FS="-1"

# Performance on STEP 2
sqlite3 $1 "$QUERY" | awk '$0 { printf "%-20s\t%-10s\t%s\n",$1,$2,$5}' FS="|" | awk '$0 ~ FS { print NF-1, $0 }' IGNORECASE=1 FS="-1"



# TODO - query for justifications
#QUERY_JUSTIFICATIONS="SELECT user.last_name, user.first_name, user.email, justification.justification FROM user,quiz,quiz_attempt,justification ON justification.quiz_question_id==\"10\" AND justification.student_id==user.id AND user.id==quiz_attempt.student_id AND quiz.id==quiz_attempt.quiz_id AND quiz.title==\"PLQ1\" ORDER BY user.last_name COLLATE NOCASE;"
#sqlite3 $1 "$QUERY_JUSTIFICATIONS" 

#sqlite3 DB_quizlib.sqlite "select user.last_name, justification.quiz_question_id, justification.justification FROM user, quiz_attempt, justification,relation_questions_vs_quizzes WHERE quiz_attempt.quiz_id==4 AND quiz_attempt.student_id==justification.student_id AND quiz_attempt.student_id==user.id AND relation_questions_vs_quizzes.quiz_id==4 AND relation_questions_vs_quizzes.quiz_question_id==justification.quiz_question_id ORDER BY user.last_name;"  |awk '{print $1,$2,$3}' FS="|" OFS="\t"|less

