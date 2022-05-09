ALTER TABLE quiz ADD COLUMN limiting_factor INT DEFAULT 0.5 NOT NULL;

ALTER TABLE quiz ADD COLUMN initial_score_weight INT DEFAULT 0.4 NOT NULL;
ALTER TABLE quiz ADD COLUMN revised_score_weight INT DEFAULT 0.3 NOT NULL;
ALTER TABLE quiz ADD COLUMN justification_grade_weight INT DEFAULT 0.2 NOT NULL;
ALTER TABLE quiz ADD COLUMN participation_grade_weight INT DEFAULT 0.1 NOT NULL;

ALTER TABLE quiz ADD COLUMN participation_grade_threshold INT DEFAULT 10 NOT NULL;
ALTER TABLE quiz ADD COLUMN max_likes INT DEFAULT -99 NOT NULL;
ALTER TABLE quiz ADD COLUMN num_justifications_shown INT DEFAULT 3 NOT NULL;

ALTER TABLE quiz ADD COLUMN first_quartile_grade INT DEFAULT 1 NOT NULL;
ALTER TABLE quiz ADD COLUMN second_quartile_grade INT DEFAULT 3 NOT NULL;
ALTER TABLE quiz ADD COLUMN third_quartile_grade INT DEFAULT 5 NOT NULL;
ALTER TABLE quiz ADD COLUMN fourth_quartile_grade INT DEFAULT 10 NOT NULL;
ALTER TABLE distractor ADD COLUMN justification STRING DEFAULT "no reference justification provided" NOT NULL;

