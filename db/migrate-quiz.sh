#!/bin/bash -e
# Migrates quiz with id $3 for source $1 to target $2 for instructor $4

# cat check-schema.sql | sed -e "s|SOURCE|$1|g" -e "s|TARGET|$2|g" | sqlite3
IFS=$'|' read QUIZ_COL QUIZ_VAL QUESTION_COL QUESTION_VAL DISTRACTOR_COL DISTRACTOR_VAL <<<$(cat check-schema.sql | sed -e "s|SOURCE|$1|g" -e "s|TARGET|$2|g" | sqlite3)

if test -z "$QUIZ_COL"
then 
    echo "schema problems. check schema-diff.csv"
    exit 1
else 
    echo "schema is ok"
    cat migrate-quiz.sql | sed -e "s|SOURCE|$1|g" -e "s|TARGET|$2|g" -e "s|QUIZ_ID|$3|g" -e "s|AUTHOR_ID|$4|g" \
        -e "s|QUIZ_COL|$QUIZ_COL|g" -e "s|QUIZ_VAL|$QUIZ_VAL|g" -e "s|QUESTION_COL|$QUESTION_COL|g" -e "s|QUESTION_VAL|$QUESTION_VAL|g" \
        -e "s|DISTRACTOR_COL|$DISTRACTOR_COL|g" -e "s|DISTRACTOR_VAL|$DISTRACTOR_VAL|g" | sqlite3 | tee migration-report.txt
    echo "data was migrated"
fi