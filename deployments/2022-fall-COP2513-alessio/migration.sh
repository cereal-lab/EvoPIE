# This script is to be applied to the DB_quizlib.sqlite file used
# during COP2513.F21 in order to add the columns that correspond
# to the changes that occured, over the semester, in the models
# after the initial release.

# the goal is here not so much to reuse the DB for local testing but
# also to be able to get back all the questions that were entered
# so that we may adapt them to the next offering

# TODO right now NOTHING has been modified, this is just the script
# from COP2512.S22 used as a place holder for the initial commit.

sqlite3 DB_quizlib.sqlite < migration-commands.sql

