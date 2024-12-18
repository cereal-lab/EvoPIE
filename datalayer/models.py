# pylint: disable=no-member
# pylint: disable=E1101

from email.policy import default
from functools import cached_property
import math
from random import shuffle # to shuffle lists
from flask_login import UserMixin
from sqlalchemy import ForeignKey

from datalayer import DB
from datalayer import QUIZ_ATTEMPT_STEP1, QUIZ_HIDDEN, QUIZ_STEP1, QUIZ_STEP2, QUIZ_STEP3, QUIZ_SOLUTIONS, ROLE_INSTRUCTOR, ROLE_STUDENT, ROLE_ADMIN
from datetime import datetime

from pytz import timezone
from jinja2 import Markup

import ast

# Probably shouldn't duplicate this functionality from evopie.utils, but it is small and
# creates a dependency issue if we want to keep the datalayer separate from evopie.
def unescape(str):
    return Markup(str).unescape()

# All models used in the DB and by EvoPIE.
# Refer to docs/DB diagram - yyyy-mm-dd.png for a snapshot of the DB diagram.
# Alternatively, run DBeaver on the sqlite file (that is where the png comes from).

#https://docs.sqlalchemy.org/en/14/core/custom_types.html#marshal-json-strings
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.ext.mutable import MutableDict, MutableList
import json

class JSONString(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.
    Usage::
        JSONEncodedDict(255)
    """
    impl = VARCHAR

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

JSONEncodedMutableDict = MutableDict.as_mutable(JSONString)
JSONEncodedMutableList = MutableList.as_mutable(JSONString)

class Question(DB.Model):
    '''
    A Question object contains both the text of the question to be
    posed to students, along with its solution.
    The solution will always appear as a response alternative in the
    Multiple Choice Question presentation.
    '''

    id = DB.Column(DB.Integer, primary_key=True)
    author_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'))
    title = DB.Column(DB.String, nullable=False)
    stem = DB.Column(DB.String, nullable=False)
    answer = DB.Column(DB.String, nullable=False)

    # 1-to-many with Distractor
    distractors = DB.relationship('Distractor', backref='question', lazy=True)

    invalidated_distractors = DB.relationship('InvalidatedDistractor', backref='question', lazy=True)
    # The above are ALL the distractors that are associated with this question
    # We will later select a few and make them part of a QuizQuestion
    
    # 1-to-many with QuizQuestion
    quiz_questions = DB.relationship('QuizQuestion', backref='question', lazy=True)

    def __repr__(self):
        return "Question(id='%d',author_id='%d',title='%s',question='%s',solution='%s')" % (self.id, self.author_id, self.title, self.stem, self.answer)

    def dump_as_dict(self): # TODO #3 get rid of dump_as_dict as part of this issue
        q = {
            "id" : self.id,
            "title" : unescape(self.title),
            "stem" : unescape(self.stem),
            "answer" : unescape(self.answer),
            "alternatives" : []
        }
        # NOTE we have to do the above unescapes so that the html code sent by summernote to the server
        # is then rendered as HTML instead of being displayed as an escape string, or rendered
        # with the unescaped symbols but not interpreted as HTML

        q['alternatives'] = [unescape(d.answer) for d in self.distractors]
        q['alternatives'].append(unescape(self.answer))
        shuffle(q['alternatives'])
        return q

    def dump_as_simplified_dict(self):
        # NOTE working around the bug with parsing the json
        # we simply do not pass the questions when we do not need them
        q = {
            "id" : self.id,
            "author_id" : self.author_id,
            "title" : self.title,
            "alternatives" : []
        }
        # NOTE trying to skip the distractors, eventually we want just their IDs
        # q['alternatives'] = [unescape(d.answer) for d in self.distractors]
        #q['alternatives'].append(unescape(self.answer))
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

    author_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'), default=None)

    answer = DB.Column(DB.String, nullable=False)
    
    # The following is used as reference justification for not picking this distractor & 
    # is provided by the distractor's author
    justification = DB.Column(DB.String, nullable=False)

    # to allow for 1-to-many relationship Question / Distractor
    question_id = DB.Column(None, DB.ForeignKey('question.id'))

    def __repr__(self):
        return "<Distractor: id='%d',question_id=%d>" % (self.id, self.question_id)

    def dump_as_dict(self): # TODO #3
        return {"id" : self.id, "answer": unescape(self.answer), "justification": unescape(self.justification)}

    def dump_as_simplified_dict(self):
        return {"id" : self.id, "answer": "", "justification": ""}
    
        
class InvalidatedDistractor(DB.Model):
    '''
    An InvalidatedDistractor object is a plausible but wrong answer to a Question provided by a student.
    '''

    id = DB.Column(DB.Integer, primary_key=True)

    author_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'))

    answer = DB.Column(DB.String, nullable=False, default="")
    
    # The following is used as reference justification for not picking this distractor & 
    # is provided by the distractor's author
    justification = DB.Column(DB.String, nullable=False, default="")

    status = DB.Column(DB.String, nullable=False, default="incomplete")

    comment = DB.Column(DB.String, nullable=False, default="")

    grade = DB.Column(DB.Integer, nullable=False, default=0)

    # to allow for 1-to-many relationship Question / Distractor
    question_id = DB.Column(None, DB.ForeignKey('question.id'))

    accepted = DB.Column(DB.String, nullable=False, default="False")

    def __repr__(self):
        return "<InvalidatedDistractor: id='%d',question_id=%d>" % (self.id, self.question_id)

    def dump_as_dict(self):
        return {"id" : self.id, "answer": unescape(self.answer), "justification": unescape(self.justification), "status": self.status, "comment": unescape(self.comment), "grade": self.grade, "accepted": self.accepted}

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

    def dump_as_dict(self):
        result = {  "id" : self.id,
                    "title": self.question.title,
                    "stem": unescape(self.question.stem),
                    "answer": unescape(self.question.answer),
                    "alternatives": [] }

        tmp1 = [] # list of distractors IDs, -1 for right answer
        tmp2 = [] # list of alternatives, including the right answer

        tmp1.append(-1)
        tmp2.append(unescape(self.question.answer))

        for d in self.distractors:
            tmp1.append(unescape(d.id))
            tmp2.append(unescape(d.answer))

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
    
    def copy(self):
        '''
        Returns a copy of this QuizQuestion object, with the same question_id, and the same distractors.
        '''
        qq = QuizQuestion(question_id=self.question_id)
        for d in self.distractors:
            qq.distractors.append(d)
        return qq

#Table used to implement the many-to-many relationship between QuizQuestions and Quizzes
relation_questions_vs_quizzes = DB.Table('relation_questions_vs_quizzes',
   DB.Column('quiz_id',             DB.Integer, DB.ForeignKey('quiz.id'),           primary_key=True),
   DB.Column('quiz_question_id',    DB.Integer, DB.ForeignKey('quiz_question.id'),  primary_key=True)
)

Course_quiz = DB.Table(
    'CourseQuiz',
    DB.Column('CourseId', DB.Integer, DB.ForeignKey('course.id'), primary_key=True),
    DB.Column('QuizId', DB.Integer, DB.ForeignKey('quiz.id'), primary_key=True)
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

    #Each quiz could have several evo processes 
    quiz_processes = DB.relationship('EvoProcess', backref='quiz', lazy=True)

    title = DB.Column(DB.String)
    description = DB.Column(DB.String)
    courses = DB.relationship('Course', secondary=Course_quiz, backref=DB.backref('quizzes', lazy='dynamic'))

    # list of tags provided by the author to help them organize their stuff :)
    # later, we might add some global tags
    author_tags = DB.Column(DB.String)
    status = DB.Column(DB.String, default=QUIZ_HIDDEN)
    limiting_factor = DB.Column(DB.Integer, default=0.5)
    initial_score_weight = DB.Column(DB.Integer, default=0.4)
    revised_score_weight = DB.Column(DB.Integer, default=0.3)
    justification_grade_weight = DB.Column(DB.Integer, default=0.2)
    participation_grade_weight = DB.Column(DB.Integer, default=0.1)
    designing_grade_weight = DB.Column(DB.Integer, default = 0.0, server_default='0')
    num_justifications_shown = DB.Column(DB.Integer, default = 3)
    first_quartile_grade = DB.Column(DB.Integer, default = 1)
    second_quartile_grade = DB.Column(DB.Integer, default = 3)
    third_quartile_grade = DB.Column(DB.Integer, default = 5)
    fourth_quartile_grade = DB.Column(DB.Integer, default = 10)
    step1_pwd = DB.Column(DB.String, default="")
    step2_pwd = DB.Column(DB.String, default="")

    step3_enabled = DB.Column(DB.String, default="False")

    deadline_driven = DB.Column(DB.String, default="False")

    tzinfo = timezone('US/Eastern')
    defaultDate = datetime.now(tzinfo).replace(hour=23, minute=59).replace(tzinfo=None)
    deadline0 = DB.Column(DB.DateTime, nullable=False, default=defaultDate) # available
    deadline1 = DB.Column(DB.DateTime, nullable=False, default=defaultDate) # step 1 is due
    deadline2 = DB.Column(DB.DateTime, nullable=False, default=defaultDate) # step 2 is due
    deadline3 = DB.Column(DB.DateTime, nullable=False, default=defaultDate) # when answers are revealed
    deadline4 = DB.Column(DB.DateTime, nullable=False, default=defaultDate) # when the quiz is closed (becomes hidden)


    # NOTE for now the statuses that are handled are "HIDDEN", "STEP1", "STEP2"
    # TODO might want to make this a foreign key to a table of statuses

    def set_status(self, stat):
        ustat = stat.upper()
        if ustat != QUIZ_HIDDEN and ustat != QUIZ_STEP1 and ustat != QUIZ_STEP2 and ustat != QUIZ_STEP3 and ustat != QUIZ_SOLUTIONS:
            return False
        else:
            self.status = ustat
            return True


    # is the following affected by TODO #3 at all? e.g., field description?
    def dump_as_dict(self):
        questions = [q.dump_as_dict() for q in self.quiz_questions]
        shuffle(questions)
        return  {   "id" : self.id,
                    "author_id" : self.author_id,
                    "title" : self.title,
                    "description" : self.description,
                    "quiz_questions" : questions, # FIXME this field should really be named quiz_questions instead of questions
                    "status" : self.status, 
                    "limiting_factor" : self.limiting_factor,
                    "initial_score_weight" : self.initial_score_weight, 
                    "revised_score_weight" :  self.revised_score_weight,
                    "justification_grade_weight" : self.justification_grade_weight ,
                    "participation_grade_weight" : self.participation_grade_weight ,                    
                    "designing_grade_weight" : self.designing_grade_weight,     
                    "num_justifications_shown" : self.num_justifications_shown ,
                    "first_quartile_grade" : self.first_quartile_grade ,
                    "second_quartile_grade" : self.second_quartile_grade,
                    "third_quartile_grade" : self.third_quartile_grade ,
                    "fourth_quartile_grade" : self.fourth_quartile_grade,
                    "step1_pwd": self.step1_pwd,
                    "step2_pwd": self.step2_pwd,
                    "step3_enabled": self.step3_enabled,
                    "deadline_driven": self.deadline_driven,
                    "deadline0": self.deadline0.strftime("%Y-%m-%dT%H:%M"),
                    "deadline1": self.deadline1.strftime("%Y-%m-%dT%H:%M"),
                    "deadline2": self.deadline2.strftime("%Y-%m-%dT%H:%M"),
                    "deadline3": self.deadline3.strftime("%Y-%m-%dT%H:%M"),
                    "deadline4": self.deadline4.strftime("%Y-%m-%dT%H:%M")
                    # "participation_grade_threshold" : round(self.num_justifications_shown * len(questions) * self.limiting_factor)
                }

    def copy(self):
        '''
        Returns a copy of this quiz, with the same questions and answers
        '''
        new_quiz = Quiz(author_id=self.author_id, title=self.title, description=self.description, 
                            status=self.status, limiting_factor=self.limiting_factor, initial_score_weight=self.initial_score_weight, 
                            revised_score_weight=self.revised_score_weight, justification_grade_weight=self.justification_grade_weight, 
                            participation_grade_weight=self.participation_grade_weight, designing_grade_weight=self.designing_grade_weight,
                            num_justifications_shown=self.num_justifications_shown, first_quartile_grade=self.first_quartile_grade, 
                            second_quartile_grade=self.second_quartile_grade, third_quartile_grade=self.third_quartile_grade, 
                            fourth_quartile_grade=self.fourth_quartile_grade, step1_pwd=self.step1_pwd, step2_pwd=self.step2_pwd, 
                            deadline_driven=self.deadline_driven, deadline0=self.deadline0, deadline1=self.deadline1, 
                            deadline2=self.deadline2, deadline3=self.deadline3, deadline4=self.deadline4, step3_enabled=self.step3_enabled)
        for q in self.quiz_questions:
            new_quiz.quiz_questions.append(q.copy())
        return new_quiz

    def __repr__(self):
        return f'<{self.title}, {self.id}>'

#Justifications that were selected and presented to student on step 2
attempt_justifications = DB.Table('attempt_justification',
   DB.Column('attempt_id', DB.Integer, DB.ForeignKey('quiz_attempt.id'), primary_key=True),
   DB.Column('justification_id',DB.Integer, DB.ForeignKey('justification.id'),primary_key=True)
)

class QuizAttempt(DB.Model):
    '''
    Holds the responses from a student to all questions of a given Quiz
    '''
    id = DB.Column(DB.Integer, primary_key=True)

    # each QuizAttempt refers to exactly 1 Quiz
    quiz_id = DB.Column(DB.Integer, DB.ForeignKey('quiz.id'))

    # each QuizAttempt refers to exactly 1 student
    student_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'))

    course_id = DB.Column(DB.Integer, DB.ForeignKey('course.id'))

    # store students answers to all questions
    # FIXME instead of JSON lists of IDs we should have used a proper relational model
    initial_responses = DB.Column(JSONEncodedMutableDict, default={}) # as json list of distractor_ID or -1 for answer
    revised_responses = DB.Column(JSONEncodedMutableDict, default={}) # as json list of distractor_ID or -1 for answer

    # score
    version_id = DB.Column(DB.Integer, nullable=False)
    selected_justifications_timestamp = DB.Column(DB.DateTime, nullable=True)
    max_likes = DB.Column(DB.Integer, default = -99)
    participation_grade_threshold = DB.Column(DB.Integer, default = 10)    
    status = DB.Column(DB.String, nullable=False)
    alternatives = DB.Column(JSONEncodedMutableList, nullable=False, default="[]")
    
    selected_justifications = DB.relationship('Justification', secondary=attempt_justifications, lazy=True)

    __mapper_args__ = {
        "version_id_col": version_id
    }    

    @cached_property
    def step_responses(self):
        return self.initial_responses if self.status == QUIZ_ATTEMPT_STEP1 else self.revised_responses

    @cached_property
    def alternatives_map(self):
        return {str(alt["question_id"]):alt["alternatives"] for alt in self.alternatives } 

    @cached_property
    def initial_scores(self):
        return {qid: 1 if answer < 0 else 0 for qid, answer in self.initial_responses.items()}
    
    @cached_property
    def initial_total_score(self):
        return sum(self.initial_scores.values())

    @cached_property
    def revised_scores(self):
        return {qid: 1 if answer < 0 else 0 for qid, answer in self.revised_responses.items()}
    
    @cached_property
    def revised_total_score(self):
        return sum(self.revised_scores.values())

    def get_min_participation_grade_threshold(self):
        return math.floor(0.8 * self.participation_grade_threshold)

    #FIXME check if the following is affected by TODO #3 at all 
    def dump_as_dict(self):
        return {    "id" : self.id,
                    "quiz_id" : self.quiz_id,
                    "student_id" : self.student_id,
                    "course_id" : self.course_id,
                    "step_responses" : self.step_responses,
                    "initial_responses" : self.initial_responses,
                    "revised_responses" : self.revised_responses,
                    "initial_scores" : self.initial_scores,
                    "revised_scores" : self.revised_scores,
                    "initial_total_score" : self.initial_total_score,
                    "revised_total_score" : self.revised_total_score,
                    "max_likes" : self.max_likes,
                    "min_participation_grade_threshold" : self.get_min_participation_grade_threshold(),
                    "participation_grade_threshold" : self.participation_grade_threshold,
                    "selected_justifications_timestamp" : self.selected_justifications_timestamp,
                    "status": self.status
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

# instructor_student = DB.Table(
#     'InstructorStudent',
#     DB.Column('InstructorId', DB.Integer, DB.ForeignKey('user.id'), primary_key=True),
#     DB.Column('StudentId', DB.Integer, DB.ForeignKey('user.id'), primary_key=True)
# )

Course_student = DB.Table(
    'CourseStudent',
    DB.Column('CourseId', DB.Integer, DB.ForeignKey('course.id'), primary_key=True),
    DB.Column('StudentId', DB.Integer, DB.ForeignKey('user.id'), primary_key=True)
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
    
    # Each user may have authored several quizzes
    quizzes = DB.relationship('Quiz', backref='author', lazy=True)

    # Each user may have made many QuizAttempts
    quiz_attempts = DB.relationship('QuizAttempt', backref='student', lazy=True)
    # all attempts

    justifications = DB.relationship('Justification', backref='student', lazy=True)

    # students = DB.relationship(
    #     'User',
    #     secondary=instructor_student,
    #     primaryjoin=id == instructor_student.c.InstructorId,
    #     secondaryjoin=id == instructor_student.c.StudentId,
    #     backref=DB.backref('instructors')
    # );

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
    liked_justifications = DB.relationship('Likes4Justifications', foreign_keys='Likes4Justifications.student_id',
        backref='student', lazy='dynamic')

    # again, is this affected by TODO #3 at all?
    # nope, none of these fields are input via WYSIWIG editor
    def dump_as_dict(self):
        return {    "id" : self.id,
                    "email" : self.email,
                    "first_name" : self.first_name,
                    "last_name" : self.last_name,
                    "password" : self.password,
                    "role" : self.role,
                }      


class Likes4Justifications(DB.Model):
    student_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'), primary_key=True)
    justification_id = DB.Column(DB.Integer, DB.ForeignKey('justification.id'), primary_key=True)

class Justification(DB.Model):
    '''
    A Justification object is the justification that a student provided for a given
    distractor or solution (id -1) in a given QuizAttempt
    '''
    id = DB.Column(DB.Integer, primary_key=True)

    quiz_question_id = DB.Column(DB.Integer, DB.ForeignKey('quiz_question.id'), nullable=False)
    distractor_id = DB.Column(DB.Integer, DB.ForeignKey('distractor.id'), nullable=False)
    student_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'), nullable=False)
    ready = DB.Column(DB.Boolean, nullable=False, default=False) #ready is False when student still working on justification on step1
    justification = DB.Column(DB.String) # FIXME do we allow duplicates like empty strings?
    likes = DB.relationship('Likes4Justifications', backref='justification', lazy='dynamic')
    seen = DB.Column(DB.Integer, nullable = False, default = 0)

    #FIXME is justification affected by TODO #3 at all?
    def dump_as_dict(self):
        return {    "id" : self.id,
                    "quiz_question_id" : self.quiz_question_id,
                    "distractor_id" : self.distractor_id,
                    "student_id" : self.student_id,
                    "justification" : self.justification,
                    "seen" : self.seen,
                }    

class Course(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String, nullable=False)
    description = DB.Column(DB.String, nullable=False)
    title = DB.Column(DB.String, nullable=False)
    instructor_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'), nullable=False)
    students = DB.relationship('User', secondary=Course_student, backref=DB.backref('courses', lazy='dynamic'))
    # quizzes = DB.relationship('Quiz', secondary=Course_quiz, backref=DB.backref('courses', lazy='dynamic'))

    def dump_as_dict(self):
        return {    "id" : self.id,
                    "name" : self.name,
                    "title" : self.title,
                    "description" : self.description,
                    "instructor_id" : self.instructor_id,
                }

class EvoProcess(DB.Model):
    '''
    Defines major settings of evo process, check columns 
    '''
    id = DB.Column(DB.Integer, primary_key=True)    
    quiz_id = DB.Column(DB.Integer, DB.ForeignKey('quiz.id'))
    start_timestamp = DB.Column(DB.DateTime, nullable=False)
    touch_timestamp = DB.Column(DB.DateTime, nullable=False)
    status = DB.Column(DB.String, nullable=False) #status 'Active', 'Stopped'
    impl = DB.Column(DB.String, nullable=False) #name of the class
    # impl_state = DB.Column(DB.String, nullable=False) #class instance running state 
    # population = DB.Column(DB.String, nullable=False) #for steady state use one ind in population
    # objectives = DB.Column(DB.String, nullable=False) #one or more (but all) objectives seen in hronological order
    impl_state: dict = DB.Column(JSONEncodedMutableDict, default={})
    # population: 'list[int]' = DB.Column(JSONEncodedMutableList, default=[])
    # objectives: 'list[int]' = DB.Column(JSONEncodedMutableList, default=[])

    __mapper_args__ = {
        "version_id_col": touch_timestamp,
        'version_id_generator': lambda version: datetime.now()
    }   

    def copy(self, new_quiz_id):
        new_process = EvoProcess(quiz_id=new_quiz_id, start_timestamp=self.start_timestamp, touch_timestamp=self.touch_timestamp, status=self.status, impl=self.impl, impl_state=self.impl_state)
        return new_process 

# class Interaction(DB.Model):
#     '''
#     Represents student selection of 
#     '''
#     id = DB.Column(DB.Integer, DB.ForeignKey('evo_process.id'), primary_key=True) #TODO: 
#     genotype_id = DB.Column(DB.Integer, primary_key=True) #interaction index
#     # genotype = DB.Column(DB.String, nullable=False)
#     # objectives = DB.Column(DB.String, nullable=False) #dict with all evaluations 
#     genotype = DB.Column(JSONEncodedMutableList, default=[])
#     objectives = DB.Column(JSONEncodedMutableDict, default={})

    # def copy(self):
    #     archive = EvoProcessArchive(genotype_id=self.genotype_id, genotype=self.genotype, objectives=self.objectives)
    #     return archive


class StudentKnowledge(DB.Model):
    '''
    Simulates student knowledge 
    NOTE: we do not use here correct answers but chances of distractors to deceive student
    NOTE: we do not emulate how distractors work together here 
    By default ideal student is assumed - student will pick correct answer 
    '''
    student_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'), primary_key=True)    
    question_id = DB.Column(DB.Integer, primary_key=True)
    distractor_id = DB.Column(DB.Integer, primary_key=True) #-1 - correct answer
    step_id = DB.Column(DB.Integer, primary_key=True)
    metrics = DB.Column(JSONEncodedMutableDict, default={})  # qualities of this distractor from student perspective. 
    # Could inclide chance. Check deca.py and different KNOWLEDGE_SELECTION_ strategies


class GlossaryTerm(DB.Model):
   """
   The class provides a definition for records in the table storing glossry terms
   and their definitions.  It is used by the dashboard to help users understand 
   the different elements of the data dashboard.  There is a small script in 
   ./evopie/datadashboard/datalayer/updateglossary.py that reads a JSON file and
   populates this table
   """
   __tablename__ = "glossary"
   
   id = DB.Column(DB.Integer, primary_key=True)
   term = DB.Column(DB.String, nullable=False)
   definition = DB.Column(DB.String, nullable=False)


class WidgetStore(DB.Model):
    """
    This class provides a definition for records in the table that will be
    used to store graph objects to be used by the data dashboard.  There is
    a unique graph object for every quiz, type of data analysys, type of 
    score (revised or initial), and analysis view (student or question).
    In addition, since the database can change while a user is looking at
    dashboard, we provide a checksum to quickly determine whether a graph
    must be regenerated.
    """
    __tablename__ = "widgetstore"

    key = DB.Column(DB.String, primary_key=True)
    quizID = DB.Column(DB.Integer, nullable=False)
    analysisType = DB.Column(DB.String, nullable=False)
    scoreType = DB.Column(DB.String, nullable=False)
    viewType = DB.Column(DB.String, nullable=False)
    hashCheck = DB.Column(DB.String, nullable=False)
    dccObject = DB.Column(DB.PickleType, nullable=False)
    dccContext = DB.Column(DB.String, nullable=False)

    @staticmethod
    def build_key(quiz_id, analysis_type, score_type, view_type):
        """
        Use the information about the quiz id, analysis type, score type,
        and view type to construct a string that can be used as a primary
        key for records in this table.
        """
        retKey  = str(quiz_id) + '-'
        retKey += analysis_type.lower().strip() + '-'
        retKey += score_type.lower().strip() + '-'
        retKey += view_type.lower().strip()

        return retKey

              
