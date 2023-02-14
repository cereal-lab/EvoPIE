
--actual data migration script after schema check 
--tables under concern 'quiz', 'question', 'distractor', 'quiz_question', 'quiz_questions_hub', 'relation_questions_vs_quizzes'
--requires substitution of: SOURCE, TARGET, QUIZ_ID, AUTHOR_ID, QUIZ_COL, QUIZ_VAL, QUESTION_COL, QUESTION_VAL, DISTRACTOR_COL, DISTRACTOR_VAL
-- required target schema constraint: quiz has id, author_id; question has id; distractor has id, question_id; 
--                                    quiz_question, relation_questions_vs_quizzes, quiz_questions_hub exist with corresponding schema of two ids
--                                           and they does not have other non-default, non-computed props

begin transaction;

attach database "SOURCE" as source_db;
attach database "TARGET" as target_db;

create temp table new_quiz as 
select id as old_quiz_id, coalesce((select max(id) from target_db.quiz) + 1, 1) as new_quiz_id
from source_db.quiz where id = QUIZ_ID;

create temp table new_questions as 
select q.old_quiz_id, q.new_quiz_id,     
    qq.quiz_question_id as old_quiz_question_id, 
        coalesce((select max(id) from target_db.quiz_question), 0) + row_number() over (order by qu.id) as new_quiz_question_id,
    qu.question_id as old_question_id, 
        coalesce((select max(id) from target_db.question), 0) + row_number() over (order by qn.id) as new_question_id
from new_quiz as q 
inner join source_db.relation_questions_vs_quizzes as qq on qq.quiz_id = q.old_quiz_id
inner join source_db.quiz_question as qu on qq.quiz_question_id = qu.id
inner join source_db.question as qn on qn.id = qu.question_id;

create temp table new_distractors as 
select 
    d.id as old_distractor_id, coalesce((select max(id) from target_db.distractor), 0) + row_number() over (order by d.id) as new_distractor_id,
    nq.old_quiz_question_id, nq.new_quiz_question_id, 
    nq.old_question_id, nq.new_question_id
from new_questions as nq
inner join source_db.distractor d on d.question_id = nq.old_question_id;

--create quiz 
insert OR ROLLBACK into target_db.quiz (id, author_id, QUIZ_COL)
select nq.new_quiz_id, AUTHOR_ID, QUIZ_VAL from new_quiz as nq 
inner join source_db.quiz as q on q.id = nq.old_quiz_id;

insert OR ROLLBACK into target_db.question (id, QUESTION_COL)
select nq.new_question_id, QUESTION_VAL from new_questions as nq 
inner join source_db.question as q on q.id = nq.old_question_id;

insert OR ROLLBACK into target_db.distractor (id, DISTRACTOR_COL, question_id)
select nd.new_distractor_id, DISTRACTOR_VAL, nd.new_question_id from new_distractors as nd 
inner join source_db.distractor as d on d.id = nd.old_distractor_id;

--selects questions for quiz 
insert OR ROLLBACK into target_db.quiz_question (id, question_id)
select nq.new_quiz_question_id, nq.new_question_id from new_questions as nq;

insert OR ROLLBACK into target_db.relation_questions_vs_quizzes (quiz_id, quiz_question_id)
select nq.new_quiz_id, nq.new_quiz_question_id from new_questions as nq;

--selects distractors for quiz questions 
insert OR ROLLBACK into target_db.quiz_questions_hub (quiz_question_id, distractor_id)
select nd.new_quiz_question_id, nd.new_distractor_id from new_distractors as nd;

.mode line 
-- .output 'new-entities.tsv'
select '---- new quiz ----' as [==];
select * from new_quiz;
select '---- new questions ----' as [==];
select * from new_questions;
select '---- new distractors ----' as [==];
select * from new_distractors;

commit;