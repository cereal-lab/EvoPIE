# pylint: disable=no-member
# pylint: disable=E1101

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from evopie import DB

ROLE_STUDENT = "STUDENT"
ROLE_INSTRUCTOR = "INSTRUCTOR"
ROLE_ADMIN = "ADMIN"


import math
from random import shuffle # to shuffle lists
from flask_login import UserMixin
#from jinja2 import Markup
from markupsafe import Markup

from evopie import DB

"""
Is it possible to get rid of this file or merge it with their models.py?
GlossaryTerms had to be added to evopie.models.py for the GetGlossaryTerms()
function to work.
"""

## RPW:  vvv All of this is more or less copied from Alessio's code. vvv
class Question(DB.Model):
    '''
    A Question object contains both the text of the question to be
    posed to students, along with its solution.
    The solution will always appear as a response alternative in the
    Multiple Choice Question presentation.
    '''

    id = DB.Column(DB.Integer, primary_key=True)

    title = DB.Column(DB.String, nullable=False)
    stem = DB.Column(DB.String, nullable=False)
    answer = DB.Column(DB.String, nullable=False)

    # 1-to-many with Distractor
    distractors = DB.relationship('Distractor', backref='question', lazy=True)
    # The above are ALL the distractors that are associated with this question
    # We will later select a few and make them part of a QuizQuestion
    
    # 1-to-many with QuizQuestion
    quiz_questions = DB.relationship('QuizQuestion', backref='question', lazy=True)

    def __repr__(self):
        return "Question(id='%d',title='%s',question='%s',solution='%s')" % (self.id, self.title, self.stem, self.answer)

    def dump_as_dict(self): # TODO #3 get rid of dump_as_dict as part of this issue
        q = {
            "id" : self.id,
            "title" : Markup(self.title).unescape(),
            "stem" : Markup(self.stem).unescape(),
            "answer" : Markup(self.answer).unescape(),
            "alternatives" : []
        }
        # NOTE we have to do the above unescapes so that the html code sent by summernote to the server
        # is then rendered as HTML instead of being displayed as an escape string, or rendered
        # with the unescaped symbols but not interpreted as HTML

        q['alternatives'] = [Markup(d.answer).unescape() for d in self.distractors]
        q['alternatives'].append(Markup(self.answer).unescape())
        shuffle(q['alternatives'])
        return q

    def dump_as_simplified_dict(self):
        # NOTE working around the bug with parsing the json
        # we simply do not pass the questions when we do not need them
        q = {
            "id" : self.id,
            "title" : self.title,
            "alternatives" : []
        }
        # NOTE trying to skip the distractors, eventually we want just their IDs
        # q['alternatives'] = [Markup(d.answer).unescape() for d in self.distractors]
        #q['alternatives'].append(Markup(self.answer).unescape())
        #shuffle(q['alternatives'])
        return q
        

# association table for many-to-many association between QuizQuestion and Distractor
quiz_questions_hub = DB.Table('quiz_questions_hub',
    DB.Column('quiz_question_id',   DB.Integer, DB.ForeignKey('quiz_question.id'),  primary_key=True),
    DB.Column('distractor_id',      DB.Integer, DB.ForeignKey('distractor.id'),     primary_key=True)
)



class Distractor(DB.Model):
    '''
    A Distractor object is a plausible but wrong answer to a Question.
    '''

    id = DB.Column(DB.Integer, primary_key=True)

    answer = DB.Column(DB.String, nullable=False)
    
    # The following is used as reference justification for not picking this distractor & 
    # is provided by the distractor's author
    ## RPW:  Doesn't appear to be in the table ...
    #justification = DB.Column(DB.String, nullable=False)

    # to allow for 1-to-many relationship Question / Distractor
    question_id = DB.Column(None, DB.ForeignKey('question.id'))

    def __repr__(self):
        return "<Distractor: id='%d',question_id=%d>" % (self.id, self.question_id)

    def dump_as_dict(self): # TODO #3
        return {"id" : self.id, "answer": Markup(self.answer).unescape(), "justification": Markup(self.justification).unescape()}

    def dump_as_simplified_dict(self):
        return {"id" : self.id, "answer": "", "justification": ""}
        


class QuizQuestion(DB.Model):
    '''
    A QuizQuestion object is built based on a Question and its related Distractors.
    It is the object that will be rendered to students.
    '''
    # NOTE auto-generated table is named quiz_question as conversion to lowercase of the above camel case

    id = DB.Column(DB.Integer, primary_key=True)

    # to allow for 1-to-many relationship Question / QuizQuestion
    question_id = DB.Column(DB.Integer, DB.ForeignKey('question.id'), nullable=False)


    # many-to-many with Distractor
    distractors = DB.relationship('Distractor', secondary=quiz_questions_hub, lazy='subquery',
        backref=DB.backref('quiz_questions', lazy=True))
    # these are the distractors that have been selected, among all available distractors
    # for a given question, to be features in this particular question to appear in a quiz

    def dump_as_dict(self): # TODO #3
        result = {  "id" : self.id,
                    "title": self.question.title,
                    "stem": Markup(self.question.stem).unescape(),
                    "answer": Markup(self.question.answer).unescape(),
                    "alternatives": [] }

        tmp1 = [] # list of distractors IDs, -1 for right answer
        tmp2 = [] # list of alternatives, including the right answer

        tmp1.append(-1)
        tmp2.append(Markup(self.question.answer).unescape())

        for d in self.distractors:
            tmp1.append(Markup(d.id).unescape())
            tmp2.append(Markup(d.answer).unescape())

        #result['alternatives'] = list(zip(tmp1,tmp2))
        # NOTE the above would cause the list to be made of tuples which are not well handled when we are trying to
        # use the |tojson template in Jinja. We want a list of lists instead.
        result['alternatives'] = [list(tup) for tup in zip(tmp1,tmp2)]

        shuffle(result['alternatives'])
        
        return result

    def dump_as_simplified_dict(self):
        result = {  "id" : self.id,
                    "alternatives": [] }

        tmp1 = [] # list of distractors IDs, -1 for right answer
        tmp2 = [] # list of alternatives, including the right answer

        tmp1.append(-1)
        tmp2.append("ANSWER")

        for d in self.distractors:
            tmp1.append(d.id)
            tmp2.append("DISTRACTOR")

        result['alternatives'] = [list(tup) for tup in zip(tmp1,tmp2)]


        shuffle(result['alternatives'])
        return result

#Table used to implement the many-to-many relationship between QuizQuestions and Quizzes
relation_questions_vs_quizzes = DB.Table('relation_questions_vs_quizzes',
   DB.Column('quiz_id',             DB.Integer, DB.ForeignKey('quiz.id'),           primary_key=True),
   DB.Column('quiz_question_id',    DB.Integer, DB.ForeignKey('quiz_question.id'),  primary_key=True)
)



class Quiz(DB.Model):
    '''
    A Quiz object is a collection of QuizQuestion objects to be presented as a complete quiz
    to students.
    '''

    id = DB.Column(DB.Integer, primary_key=True)

    # Each quiz has 1 author
    author_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'))

    # Each quiz has many QuizQuestions
    quiz_questions = DB.relationship('QuizQuestion', secondary=relation_questions_vs_quizzes, lazy='subquery',
       backref=DB.backref('quizzes', lazy=True))

    # Each quiz has many QuizAttempts
    quiz_attempts = DB.relationship('QuizAttempt', backref='quiz', lazy=True)

    title = DB.Column(DB.String)
    description = DB.Column(DB.String)

    # list of tags provided by the author to help them organize their stuff :)
    # later, we might add some global tags
    author_tags = DB.Column(DB.String)
    status = DB.Column(DB.String, default="HIDDEN")
    ## RPW:  These do not appear to be in the table ...
    #limiting_factor = DB.Column(DB.Integer, default=0.5)
    #initial_score_weight = DB.Column(DB.Integer, default=0.4)
    #revised_score_weight = DB.Column(DB.Integer, default=0.3)
    #justification_grade_weight = DB.Column(DB.Integer, default=0.2)
    #participation_grade_weight = DB.Column(DB.Integer, default=0.1)
    #num_justifications_shown = DB.Column(DB.Integer, default = 3)
    #first_quartile_grade = DB.Column(DB.Integer, default = 1)
    #second_quartile_grade = DB.Column(DB.Integer, default = 3)
    #third_quartile_grade = DB.Column(DB.Integer, default = 5)
    #fourth_quartile_grade = DB.Column(DB.Integer, default = 10)

    # NOTE for now the statuses that are handled are "HIDDEN", "STEP1", "STEP2"
    # TODO might want to make this a foreign key to a table of statuses

    def set_status(self, stat):
        ustat = stat.upper()
        if ustat != "HIDDEN" and ustat != "STEP1" and ustat != "STEP2" and ustat != "SOLUTIONS":
            return False
        else:
            self.status = ustat
            return True



    def dump_as_dict(self):
        questions = [q.dump_as_dict() for q in self.quiz_questions]
        shuffle(questions)
        return  {   "id" : self.id,
                    "title" : self.title,
                    "description" : self.description,
                    "quiz_questions" : questions, # FIXME this field should really be named quiz_questions instead of questions
                    "status" : self.status, 
                    #"limiting_factor" : self.limiting_factor,
                    #"initial_score_weight" : self.initial_score_weight, 
                    #"revised_score_weight" :  self.revised_score_weight,
                    #"justification_grade_weight" : self.justification_grade_weight ,
                    #"participation_grade_weight" : self.participation_grade_weight ,                    
                    #"num_justifications_shown" : self.num_justifications_shown ,
                    #"first_quartile_grade" : self.first_quartile_grade ,
                    #"second_quartile_grade" : self.second_quartile_grade,
                    #"third_quartile_grade" : self.third_quartile_grade ,
                    #"fourth_quartile_grade" : self.fourth_quartile_grade
                    # "participation_grade_threshold" : round(self.num_justifications_shown * len(questions) * self.limiting_factor)
                }

    def __repr__(self):
        return f'<{self.title}, {self.id}>'

#Justifications that were selected and presented to student on step 2
#attempt_justifications = DB.Table('attempt_justification',
#   DB.Column('attempt_id', DB.Integer, DB.ForeignKey('quiz_attempt.id'), primary_key=True),
#   DB.Column('justification_id',DB.Integer, DB.ForeignKey('justification.id'),primary_key=True)
#)


class QuizAttempt(DB.Model):
    '''
    Holds the responses from a student to all questions of a given Quiz
    '''
    id = DB.Column(DB.Integer, primary_key=True)

    # each QuizAttempt refers to exactly 1 Quiz
    quiz_id = DB.Column(DB.Integer, DB.ForeignKey('quiz.id'))

    # each QuizAttempt refers to exactly 1 student
    student_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'))

    # time stamps
    # initial --> start / end
    # revised --> start / end

    # store students answers to all questions
    initial_responses = DB.Column(DB.String, default="{}") # as json list of distractor_ID or -1 for answer
    revised_responses = DB.Column(DB.String, default="{}") # as json list of distractor_ID or -1 for answer

    initial_total_score = DB.Column(DB.Integer, default=0)
    revised_total_score = DB.Column(DB.Integer, default=0)

    # justifications to each possible answer
    justifications = DB.Column(DB.String, default="{}") # json list of text entries

    # score
    initial_scores = DB.Column(DB.String, default="") # as json list of -1 / distractor ID
    revised_scores = DB.Column(DB.String, default="") # as json list of -1 / distractor ID    
    ## RPW:  These do not appear to be in the table ...
    #version_id = DB.Column(DB.Integer, nullable=False)
    #selected_justifications_timestamp = DB.Column(DB.DateTime, nullable=True)
    #max_likes = DB.Column(DB.Integer, default = -99)
    #participation_grade_threshold = DB.Column(DB.Integer, default = 10)    

    #selected_justifications = DB.relationship('Justification', secondary=attempt_justifications, lazy=True)

    #__mapper_args__ = {
    #    "version_id_col": version_id
    #}    

    def get_min_participation_grade_threshold(self):
        return math.floor(0.8 * self.participation_grade_threshold)

    def dump_as_dict(self):
        return {    "id" : self.id,
                    "quiz_id" : self.quiz_id,
                    "student_id" : self.student_id,
                    "initial_responses" : self.initial_responses,
                    "revised_responses" : self.revised_responses,
                    "justifications" : self.justifications,
                    "initial_scores" : self.initial_scores,
                    "revised_scores" : self.revised_scores,
                    "initial_total_score" : self.initial_total_score,
                    "revised_total_score" : self.revised_total_score,
                    #"max_likes" : self.max_likes,
                    "min_participation_grade_threshold" : self.get_min_participation_grade_threshold(),
                    "participation_grade_threshold" : self.participation_grade_threshold,
                    "selected_justifications_timestamp" : self.selected_justifications_timestamp
                }



#Table used to implement the many-to-many relationship between QuizQuestions and QuizAttempts
'''
    Responses from student to a given QuizQuestion.
    These are bulk-generated when a Quiz is received.
    The UI should not operate at the level of QuizResponse but just at the Quiz level.
    Then, internally, we keep more detailed records.
'''
relation_questions_vs_attempts = DB.Table('relation_questions_vs_attempts',
   DB.Column('quiz_attempt_id', DB.Integer, DB.ForeignKey('quiz_attempt.id'), primary_key=True),
   DB.Column('quiz_question_id',DB.Integer, DB.ForeignKey('quiz_question.id'),primary_key=True)
)



class User(UserMixin, DB.Model):
    '''
    Information about users, compatible with flask_login.
    '''
    id = DB.Column(DB.Integer, primary_key=True)
    email = DB.Column(DB.String)
    first_name = DB.Column(DB.String)
    last_name = DB.Column(DB.String)
    password = DB.Column(DB.String)
    role = DB.Column(DB.String, default=ROLE_STUDENT)
    # NOTE for now the roles that are handled are STUDENT (default), INSTRUCTOR, ADMIN
    # TODO might want to make this a foreign key to a table of roles
    
    # Each user may have authored several quizzes
    quizzes = DB.relationship('Quiz', backref='author', lazy=True)

    # Each user may have made many QuizAttempts
    quiz_attempts = DB.relationship('QuizAttempt', backref='student', lazy=True)
    # all attempts

    justifications = DB.relationship('Justification', backref='student', lazy=True)


    def is_instructor(self):
        return self.role == ROLE_INSTRUCTOR

    def is_student(self):
        return self.role == ROLE_STUDENT

    def is_admin(self):
        return self.id == 1 or self.role == ROLE_ADMIN
    
    def set_role(self, role):
        urole = role.upper()
        if urole != ROLE_STUDENT and urole != ROLE_INSTRUCTOR and urole != ROLE_ADMIN:
            return False
        else:
            self.role = urole
            return True

    def __repr__(self):
        return f'<{self.last_name}, {self.first_name}, {self.id}>'

    # Like / Dislike Feature
    liked_justifications =DB.relationship('Likes4Justifications', foreign_keys='Likes4Justifications.student_id',
        backref='student', lazy='dynamic')

    def like_justification(self, justification): 
        if not self.has_liked_justification(justification) and not self.id == justification.student_id:
            like = Likes4Justifications(student_id=self.id, justification_id=justification.id)
            DB.session.add(like)
            DB.session.commit()

    def unlike_justification(self, justification): 
        if self.has_liked_justification(justification) and not self.id == justification.student_id:
            Likes4Justifications.query.filter_by(
                student_id=self.id,
                justification_id=justification.id).delete()
            DB.session.commit()

    def has_liked_justification(self, justification):
        return Likes4Justifications.query.filter(
            Likes4Justifications.student_id == self.id,
            Likes4Justifications.justification_id == justification.id).count() > 0
    
    def get_email(self):
        return self.email

    def dump_as_dict(self):
        return {    "id" : self.id,
                    "email" : self.email,
                    "first_name" : self.first_name,
                    "last_name" : self.last_name,
                    "password" : self.password,
                    "role" : self.role,
                }      


class Likes4Justifications(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    student_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'))
    justification_id = DB.Column(DB.Integer, DB.ForeignKey('justification.id'))



class Justification(DB.Model):
    '''
    A Justification object is the justification that a student provided for a given
    distractor or solution (id -1) in a given QuizAttempt
    '''
    id = DB.Column(DB.Integer, primary_key=True)

    quiz_question_id = DB.Column(DB.Integer, DB.ForeignKey('quiz_question.id'), nullable=False)
    distractor_id = DB.Column(DB.Integer, DB.ForeignKey('distractor.id'), nullable=False)
    student_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'), nullable=False)
    justification = DB.Column(DB.String) # FIXME do we allow duplicates like empty strings?
    likes = DB.relationship('Likes4Justifications', backref='justification', lazy='dynamic')
    seen = DB.Column(DB.Integer, nullable = False, default = 0)

    def dump_as_dict(self):
        return {    "id" : self.id,
                    "quiz_question_id" : self.quiz_question_id,
                    "distractor_id" : self.distractor_id,
                    "student_id" : self.student_id,
                    "justification" : self.justification,
                    "seen" : self.seen,
                }    

class GlossaryTerm(DB.Model):
   __tablename__ = "glossary"
   
   id = DB.Column(DB.Integer, primary_key=True)
   term = DB.Column(DB.String, nullable=False)
   definition = DB.Column(DB.String, nullable=False)



## RPW:  Unit test for the models ...
if __name__ == '__main__':
    quizID = 1
    for instance in QuizAttempt.query.filter(QuizAttempt.quiz_id == quizID):
        print(instance.student_id, "  ::  ", instance.initial_scores, "  ::  ", instance.revised_scores)