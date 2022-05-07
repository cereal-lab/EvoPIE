# This script is to be applied to the DB_quizlib.sqlite file used
# during COP2512.S22 in order to add the columns that correspond
# to the changes that occured, over the semester, in the models
# after the initial release.

sqlite3 DB_quizlib.sqlite < migration-commands.sql

