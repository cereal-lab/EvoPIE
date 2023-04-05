#!/bin/bash -e
#NOTE about parameters: 
# Migrates all quizes for instructor with email $3 (in SOURCE) from source $1 to target $2. 
# If $4 is provided, it should be existing instructor id in TARGET db (to add quizzes to that instractor instead of creating new one)
#   otherwise new user for instractor will be added to TARGET and id will be allocated accordingly 
# Parameter $5 allows to override new instructor email in TARGET (allows to avoid bumpting onto existing account)

# cat check-schema.sql | sed -e "s|SOURCE|$1|g" -e "s|TARGET|$2|g" | sqlite3

IFS=$'|' read USER_COL USER_VAL QUIZ_COL QUIZ_VAL QUESTION_COL QUESTION_VAL DISTRACTOR_COL DISTRACTOR_VAL <<<$(cat check-schema.sql | sed -e "s|SOURCE|$1|g" -e "s|TARGET|$2|g" | sqlite3)

if test -z "$USER_COL"
then 
    echo "Schema problems, check schema-diff.csv"
    exit 1
else 
    echo "schema is ok"
    cat migrate-quiz.sql | sed -e "s|SOURCE|$1|g" -e "s|TARGET|$2|g" \
        -e "s|NEW_AUTHOR_ID|$4|g" -e "s|NEW_AUTHOR_EMAIL|$5|g" -e "s|AUTHOR_EMAIL|$3|g" \
        -e "s|USER_COL|$USER_COL|g" -e "s|USER_VAL|$USER_VAL|g" \
        -e "s|QUIZ_COL|$QUIZ_COL|g" -e "s|QUIZ_VAL|$QUIZ_VAL|g" \
        -e "s|QUESTION_COL|$QUESTION_COL|g" -e "s|QUESTION_VAL|$QUESTION_VAL|g" \
        -e "s|DISTRACTOR_COL|$DISTRACTOR_COL|g" -e "s|DISTRACTOR_VAL|$DISTRACTOR_VAL|g" | sqlite3 | tee migration-report.txt
    #echo "Data were migrated successfuly!"
fi