# query to process performance on step 1 & 2 of a given quiz
QUERY="SELECT user.last_name, user.first_name, user.email,quiz_attempt.initial_responses, quiz_attempt.revised_responses FROM user,quiz_attempt,quiz ON user.id==quiz_attempt.student_id AND quiz.id==quiz_attempt.quiz_id AND quiz.title==\"PLQ2\" ORDER BY user.last_name COLLATE NOCASE;"

#all students with their performance computed on step 1
sqlite3 DB_quizlib.sqlite "$QUERY" | awk '$0 { printf "%-20s\t%-10s\t%s\n",$1,$2,$4}' FS="|" | awk '$0 ~ FS { print NF-1, $0 }' IGNORECASE=1 FS="-1" | less

# all students with their performance computed on step #2
sqlite3 DB_quizlib.sqlite "$QUERY" | awk '$0 { printf "%-20s\t%-10s\t%s\n",$1,$2,$5}' FS="|" | awk '$0 ~ FS { print NF-1, $0 }' IGNORECASE=1 FS="-1"| less


# listing all justification to be able to grade by hand
sqlite3 DB_quizlib.sqlite "SELECT user.last_name, user.first_name, user.email, justification.quiz_question_id, justification.justification FROM user,quiz,quiz_attempt,justification ON (justification.quiz_question_id==\"10\" OR justification.quiz_question_id==\"11\" OR justification.quiz_question_id==\"12\") AND justification.student_id==user.id AND user.id==quiz_attempt.student_id AND quiz.id==quiz_attempt.quiz_id AND quiz.title==\"PLQ1\" AND user.id==166 ORDER BY user.last_name COLLATE NOCASE;" | less

#using the "mySQL" visual studio code plugin views below to grade
CREATE VIEW PLQ_2_performance
AS
SELECT user.last_name, user.first_name, user.email,quiz_attempt.initial_responses, quiz_attempt.revised_responses
FROM user,quiz_attempt,quiz
ON user.id==quiz_attempt.student_id AND quiz.id==quiz_attempt.quiz_id AND quiz.title=="PLQ2"
ORDER BY user.last_name COLLATE NOCASE;


CREATE VIEW PLQ_2_justifications
AS
SELECT user.last_name, user.first_name, user.email, justification.quiz_question_id, justification.justification
FROM user,quiz,quiz_attempt,justification
ON  (justification.quiz_question_id=="10" OR justification.quiz_question_id=="11" OR justification.quiz_question_id=="12")
    AND justification.student_id==user.id
    AND user.id==quiz_attempt.student_id
    AND quiz.id==quiz_attempt.quiz_id
    AND quiz.title=="PLQ2"
ORDER BY user.last_name COLLATE NOCASE;



# Counting likes per user - in progress / see below
select user.last_name, justification.id
from likes4_justifications, justification, user
WHERE likes4_justifications.justification_id==justification.id AND justification.student_id==user.id;


# counting likes received
select user.last_name, COUNT(*)
from likes4_justifications, justification, user
WHERE likes4_justifications.justification_id==justification.id AND justification.student_id==user.id
GROUP BY user.last_name;
# TODO - restrict the above to a given quiz



#counting likes given
select user.last_name, COUNT(*)
from likes4_justifications, user
WHERE likes4_justifications.student_id==user.id
GROUP BY user.last_name;
#TODO - restrict the above to a given quiz