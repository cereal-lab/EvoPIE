--sqlite script to migrate quiz data from source to target 
-- migration tables:
--      quiz question distractor quiz_question* quiz_questions_hub justification** relation_questions_vs_quizzes
--      * - only for schema change - data is recreated after insert
--      ** - only instructor justification

attach database "SOURCE" as source_db;
attach database "TARGET" as target_db;

create temp table migration_tables as 
select column1 as table_name from (values ('user'), ('quiz'), ('question'), ('distractor'), ('quiz_question'), ('relation_questions_vs_quizzes'), ('quiz_questions_hub'));

--todo: here we could also add necessary properties of columns (type or affinity type)
create temp table at_least_required_columns as 
select column1 as table_name, column2 as column_name, column3 as db_name
from (values ('user', 'id', 'source_db'),
             ('user', 'id', 'target_db'),
             ('user', 'email', 'source_db'),
             ('user', 'email', 'target_db'),
             ('quiz', 'id', 'source_db'), 
             ('quiz', 'id', 'target_db'), 
             ('quiz', 'author_id', 'target_db'),    
             ('question', 'id', 'source_db'),
             ('question', 'id', 'target_db'),
             ('question', 'author_id', 'target_db'),
             ('distractor', 'id', 'source_db'),
             ('distractor', 'id', 'target_db'),
             ('distractor', 'question_id', 'source_db'),
             ('distractor', 'question_id', 'target_db')
    );

create temp table at_most_required_columns as 
select column1 as table_name, column2 as column_name 
from (values ('quiz_question', 'id'), 
             ('quiz_question', 'question_id'),
             ('relation_questions_vs_quizzes', 'quiz_id'),
             ('relation_questions_vs_quizzes', 'quiz_question_id'),
             ('quiz_questions_hub', 'quiz_question_id'),
             ('quiz_questions_hub', 'distractor_id'));

create temp table dbs as 
select column1 as dbs_name from (values ('source_db'), ('target_db'));

--https://www.sqlite.org/pragma.html#pragma_table_xinfo
create temp table db_schemas as
select *, CASE WHEN [type] IN ('INT', 'INTEGER', 'TINYINT', 'SMALLINT', 'MEDIUMINT', 'BIGINT') THEN 'INTEGER'
               WHEN [type] LIKE '%VARCHAR%' OR [type] LIKE '%CHARACTER%' OR [type] LIKE '%NCHAR' OR [type] = 'TEXT' OR [type] = 'CLOB' OR [type] = 'STRING' THEN 'TEXT'
               WHEN [type] IN ('REAL', 'DOUBLE', 'FLOAT', 'DOUBLE PRECISION') THEN 'REAL'
               WHEN [type] LIKE 'DECIMAL%' OR [type] IN ('NUMERIC', 'BOOLEAN', 'DATE', 'DATETIME') THEN 'NUMERIC'
               ELSE 'BLOB' END as affinity_type from dbs 
    cross join migration_tables as mt 
    cross join pragma_table_xinfo(mt.table_name, dbs.dbs_name);

--checking least required schema 
create temp table least_required as 
select lrc.table_name, lrc.column_name, lrc.db_name, 'required column is missing' as err
from at_least_required_columns as lrc 
left join (select * from db_schemas) as s
    on s.table_name = lrc.table_name and s.[name] = lrc.[column_name] and lrc.db_name = s.dbs_name
where s.[name] is null; --no source or target column

--checking least required schema 
create temp table most_required as 
select lrc.table_name, lrc.column_name, case when ts.[name] is null then 'target is missing' else 'source is missing' end as err
from at_most_required_columns as lrc 
left join (select * from db_schemas where dbs_name = 'target_db') as ts 
    on ts.table_name = lrc.table_name and ts.[name] = lrc.[column_name]
left join (select * from db_schemas where dbs_name = 'source_db') as ss 
    on ts.table_name = lrc.table_name and ts.[name] = lrc.[column_name]    
where ts.[name] is null or ss.[name] is null; --no source or target column

insert into most_required
select dbs.[table_name], dbs.[name], 'target incompat column' as err from db_schemas as dbs
where dbs_name = 'target_db' and dbs.[table_name] in (select distinct table_name from at_most_required_columns) and
        dbs.[name] not in (select column_name from at_most_required_columns as mrc where mrc.[table_name] = dbs.[table_name])
        and dbs.[dflt_value] is null and dbs.[hidden] < 2; --2 and 3 - generated column

insert into most_required
select dbs.[table_name], dbs.[name], 'source incompat column' as err from db_schemas as dbs
where dbs_name = 'source_db' and dbs.[table_name] in (select distinct table_name from at_most_required_columns) and
        dbs.[name] not in (select column_name from at_most_required_columns as mrc where mrc.[table_name] = dbs.[table_name])
        and dbs.[dflt_value] is null and dbs.[hidden] < 2; --2 and 3 - generated column        


-- both dbs have required part of schema according to migrate-quiz 
-- type checks
create temp table diffs as
select mt.table_name, ts.name as column_name, ts.cid, ss.cid as source_cid from 
    migration_tables as mt 
left join 
    (select * from db_schemas where dbs_name = 'target_db') as ts
    on mt.[table_name] = ts.[table_name]
left join
    (select * from db_schemas where dbs_name = 'source_db') as ss
    on ss.table_name = ts.table_name and ss.[name] = ts.[name]
where     
    (ts.table_name is null) or (ss.[name] is null and ts.[notnull] = 1 and ts.[dflt_value] is null and ts.hidden < 2)    
    or ts.[affinity_type] != ss.[affinity_type] or (ts.[notnull] = 1 and ss.[notnull] = 0);
    --(ts.[dflt_value] IS NULL and ss.[name] IS NULL)  --allow default value

.headers on
.mode csv
.output 'schema-diff.csv'
select * from least_required;
select '---' where exists(select * from least_required);
select * from most_required;
select '---' where exists(select * from most_required);
select * from diffs;

--output params USER_COL, USER_VAL, QUIZ_COL, QUIZ_VAL, QUESTION_COL, QUESTION_VAL, DISTRACTOR_COL, DISTRACTOR_VAL for next script
create temp table user_parts as 
select group_concat(ts.[name], ',') as USER_COL, group_concat(ss.[name], ',') as USER_VAL from 
    (select * from db_schemas where dbs_name = 'target_db' and table_name='user') as ts 
inner join -- here we already assume that missing columns in target would have default values according to diff
    (select * from db_schemas where dbs_name = 'source_db' and table_name='user') as ss 
    on ts.[name] = ss.[name]  
where ts.[name] not in (select column_name from at_least_required_columns as lrc where lrc.table_name = 'user' and lrc.db_name = 'target_db') and 
        not exists(select * from least_required) and 
        not exists(select * from most_required) and 
        not exists(select * from diffs);

create temp table quiz_parts as 
select group_concat(ts.[name], ',') as QUIZ_COL, group_concat(ss.[name], ',') as QUIZ_VAL from 
    (select * from db_schemas where dbs_name = 'target_db' and table_name='quiz') as ts 
inner join -- here we already assume that missing columns in target would have default values according to diff
    (select * from db_schemas where dbs_name = 'source_db' and table_name='quiz') as ss 
    on ts.[name] = ss.[name]  
where ts.[name] not in (select column_name from at_least_required_columns as lrc where lrc.table_name = 'quiz' and lrc.db_name = 'target_db') and 
        not exists(select * from least_required) and 
        not exists(select * from most_required) and 
        not exists(select * from diffs);

create temp table question_parts as 
select group_concat(ts.[name], ',') as QUESTION_COL, group_concat(ss.[name], ',') as QUESTION_VAL from 
    (select * from db_schemas where dbs_name = 'target_db' and table_name='question') as ts 
inner join -- here we already assume that missing columns in target would have default values according to diff
    (select * from db_schemas where dbs_name = 'source_db' and table_name='question') as ss 
    on ts.[name] = ss.[name]  
where ts.[name] not in (select column_name from at_least_required_columns as lrc where lrc.table_name = 'question' and lrc.db_name = 'target_db') and 
        not exists(select * from least_required) and 
        not exists(select * from most_required) and 
        not exists(select * from diffs);

create temp table distractor_parts as 
select group_concat(ts.[name], ',') as DISTRACTOR_COL, group_concat(ss.[name], ',') as DISTRACTOR_VAL from 
    (select * from db_schemas where dbs_name = 'target_db' and table_name='distractor') as ts 
inner join -- here we already assume that missing columns in target would have default values according to diff
    (select * from db_schemas where dbs_name = 'source_db' and table_name='distractor') as ss 
    on ts.[name] = ss.[name]  
where ts.[name] not in (select column_name from at_least_required_columns as lrc where lrc.table_name = 'distractor' and lrc.db_name = 'target_db') and 
        not exists(select * from least_required) and 
        not exists(select * from most_required) and 
        not exists(select * from diffs);

.output stdout 
.headers off
-- .separator '\t'
.mode list
select USER_COL, USER_VAL, QUIZ_COL, QUIZ_VAL, QUESTION_COL, QUESTION_VAL, DISTRACTOR_COL, DISTRACTOR_VAL 
from user_parts crosso join quiz_parts cross join question_parts cross join distractor_parts;       