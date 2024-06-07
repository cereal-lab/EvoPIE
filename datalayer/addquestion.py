## RPW:  Ad-Hoc script to add a fake question to the DB

from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy import insert
from sqlalchemy import func
from sqlalchemy.orm import Session
from datalayer import LOGGER

import json
import sys

DB = SQLAlchemy()

ROLE_STUDENT = "STUDENT"
ROLE_INSTRUCTOR = "INSTRUCTOR"
ROLE_ADMIN = "ADMIN"



quiz_questions_hub = DB.Table('quiz_questions_hub',
    DB.Column('quiz_question_id',   DB.Integer, DB.ForeignKey('quiz_question.id'),  primary_key=True),
    DB.Column('distractor_id',      DB.Integer, DB.ForeignKey('distractor.id'),     primary_key=True)
)


relation_questions_vs_attempts = DB.Table('relation_questions_vs_attempts',
   DB.Column('quiz_attempt_id', DB.Integer, DB.ForeignKey('quiz_attempt.id'), primary_key=True),
   DB.Column('quiz_question_id',DB.Integer, DB.ForeignKey('quiz_question.id'),primary_key=True)
)

relation_questions_vs_quizzes = DB.Table('relation_questions_vs_quizzes',
   DB.Column('quiz_id',             DB.Integer, DB.ForeignKey('quiz.id'),           primary_key=True),
   DB.Column('quiz_question_id',    DB.Integer, DB.ForeignKey('quiz_question.id'),  primary_key=True)
)


class Question(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    title = DB.Column(DB.String, nullable=False)
    stem = DB.Column(DB.String, nullable=False)
    answer = DB.Column(DB.String, nullable=False)
    distractors = DB.relationship('Distractor', backref='question', lazy=True)
    quiz_questions = DB.relationship('QuizQuestion', backref='question', lazy=True)


class Distractor(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    answer = DB.Column(DB.String, nullable=False)
    question_id = DB.Column(None, DB.ForeignKey('question.id'))



class Quiz(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    author_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'))
    quiz_questions = DB.relationship('QuizQuestion', secondary=relation_questions_vs_quizzes, lazy='subquery',
       backref=DB.backref('quizzes', lazy=True))
    quiz_attempts = DB.relationship('QuizAttempt', backref='quiz', lazy=True)
    title = DB.Column(DB.String)
    description = DB.Column(DB.String)
    author_tags = DB.Column(DB.String)
    status = DB.Column(DB.String, default="HIDDEN")


class QuizAttempt(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    quiz_id = DB.Column(DB.Integer, DB.ForeignKey('quiz.id'))
    student_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'))
    initial_responses = DB.Column(DB.String, default="{}") # as json list of distractor_ID or -1 for answer
    revised_responses = DB.Column(DB.String, default="{}") # as json list of distractor_ID or -1 for answer
    initial_total_score = DB.Column(DB.Integer, default=0)
    revised_total_score = DB.Column(DB.Integer, default=0)
    justifications = DB.Column(DB.String, default="{}") # json list of text entries
    initial_scores = DB.Column(DB.String, default="") # as json list of -1 / distractor ID
    revised_scores = DB.Column(DB.String, default="") # as json list of -1 / distractor ID    


class QuizQuestion(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    question_id = DB.Column(DB.Integer, DB.ForeignKey('question.id'), nullable=False)
    distractors = DB.relationship('Distractor', secondary=quiz_questions_hub, lazy='subquery',
        backref=DB.backref('quiz_questions', lazy=True))

class User(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    email = DB.Column(DB.String)
    first_name = DB.Column(DB.String)
    last_name = DB.Column(DB.String)
    password = DB.Column(DB.String)
    role = DB.Column(DB.String, default=ROLE_STUDENT)
    quizzes = DB.relationship('Quiz', backref='author', lazy=True)
    quiz_attempts = DB.relationship('QuizAttempt', backref='student', lazy=True)


class Justification(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    quiz_question_id = DB.Column(DB.Integer, DB.ForeignKey('quiz_question.id'), nullable=False)
    distractor_id = DB.Column(DB.Integer, DB.ForeignKey('distractor.id'), nullable=False)
    student_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'), nullable=False)
    justification = DB.Column(DB.String) # FIXME do we allow duplicates like empty strings?


# Modify these to alter a different test
quizID = 1

studentMissedRevi = None
studentMissedInit = None
basisQuestion = None
stride = None
changeCounter = 0

# Get the raw question value to copy from the user
rawQuestion = 3
try:
  rawInput = sys.argv[1]
  rawQuestion = int(rawInput.strip('q'))
except:
  LOGGER.error("ERROR:  Please specify a valid question to copy (q1, q2, q3)!")
  sys.exit(1)
basisQuestion = str(rawQuestion)

# Setup the 
if (basisQuestion == "3"):
  studentMissedRevi = set([18, 115, 117])
  studentMissedInit = set([18, 38, 111, 113, 117])
  stride = 20
elif (basisQuestion =="2"):
  studentMissedRevi = set([29, 47])
  studentMissedInit = set([29, 47, 91, 112])
  stride = 40
elif (basisQuestion == "1"):
  studentMissedRevi = set(list(range(1,120))) - set([18, 29, 38, 47, 91, 111, 112, 117])
  studentMissedInit = set(list(range(1,120))) - set([18, 29, 47, 115, 117])
  stride = 100
else:
  LOGGER.error("ERROR:  Please specify a valid question to copy (q1, q2, q3)!")
  sys.exit(1)


# Open the database
engine = create_engine("sqlite:///alessio.sqlite", echo=True, future=True)
session = Session(engine)


# Add the question to the quiz
qid = int(session.query(Question, func.max(Question.id)).first()[1]) + 1
print("\n\nAdding new question: qid=", qid, "\n\n")
myStem = "&lt;p&gt;What is the best programming language for efficient, embedded controllers?&lt;br&gt;&lt;/p&gt;"
myAnswer = "<p>C++;<br></p>"
q1 = Question(id=qid, title="COP2512 M10 - Q4 Silly", stem=myStem, answer=myAnswer)
session.add(q1)

# Add distractors
did = int(session.query(Distractor, func.max(Distractor.id)).first()[1])
print("\n\nAdding new distractors: did=", did+1, did+2, did+3, "\n\n")
d1 = Distractor(id=did+1, answer="Python", question_id=qid)
d2 = Distractor(id=did+2, answer="Pascal", question_id=qid)
d3 = Distractor(id=did+3, answer="Ada", question_id=qid)
session.add(d1)
session.add(d2)
session.add(d3)

# Put the question on the quiz
qq1 = QuizQuestion(id=qid, question_id=qid, distractors=[d1, d2, d3] )
session.add(qq1)
quiz = session.query(Quiz).filter_by(id=quizID).one()
quiz.quiz_questions.append(qq1)

print("\n",''.ljust(40, '-'))
for student in session.query(QuizAttempt).filter_by(quiz_id=1).order_by(QuizAttempt.id):
  print("\nXX-BEFORE: ", student.student_id, student.initial_responses, student.initial_total_score, student.revised_responses, student.revised_total_score)
  try:
    # Convert the varchar fields to dictionaries so we can work with them
    initial_responses = json.loads(student.initial_responses.replace("'", '"'))
    revised_responses = json.loads(student.revised_responses.replace("'", '"'))
    initial_scores = json.loads(student.initial_scores.replace("'", '"'))
    revised_scores = json.loads(student.revised_scores.replace("'", '"'))
    initial_total = student.initial_total_score
    revised_total = student.revised_total_score 

    # We'll use the basis question to copy, with small modifications
    distInit = int(initial_responses[basisQuestion])
    distRevi = int(revised_responses[basisQuestion])

    # The new key into the responses and scores matrix ...
    #qKey = str(max(list( map(int,initial_responses.keys())) ) + 1)
    qKey = qid
    ## RPW:  This is wrong.  This makes the next entry question key 1 more than the max before ... 
    ##       but we should be adding the new question ID (maybe from line 145, above?)

    # If the initial basis question was wrong, then the new question is wrong.  Also, if this
    # student is one of the "special students", let's mark them wrong, too
    if (student.student_id in studentMissedInit or distInit >= 0 or student.student_id%stride==0):
      initial_responses[qKey] = str(distInit%3 + did + 1)
      initial_scores[qKey] = 0
      initial_total += 0

    # Otherwise, they got the new question right!
    else:
      initial_responses[qKey] = "-1"
      initial_scores[qKey] = 1
      initial_total += 1

    # If the revised basis question was wrong, then the new question is wrong.  Also, if this
    # student is one of the "special students", let's mark them wrong, too
    if (student.student_id in studentMissedRevi or distRevi >= 0 or student.student_id%stride==0):
      revised_responses[qKey] = str(distRevi%3 + did + 1)
      revised_scores[qKey] = 0
      revised_total += 0

    # Otherwise, they got the new question right!
    else:
      revised_responses[qKey] = "-1"
      revised_scores[qKey] = 1
      revised_total += 1

    # Save these into the actual DB record
    student.initial_responses = json.dumps(initial_responses)
    student.revised_responses = json.dumps(revised_responses)
    student.initial_scores = json.dumps(initial_scores)
    student.revised_scores = json.dumps(revised_scores)
    student.initial_total_score = initial_total
    student.revised_total_score = revised_total
    changeCounter += 1

  except Exception as e:
    print("XX-Could not process student ", student.student_id)
    pass

  # Let's print to make sure this is working ...
  print("\nXX-AFTER:  ", student.student_id, student.initial_responses, student.initial_total_score, student.revised_responses, student.revised_total_score)

print("\n",''.ljust(40, '-'))

session.commit()

print("\n\nXX-COMPLETED:  Copied question q", basisQuestion, ", made ", changeCounter, " changes.\n\n")

