import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


APP = Flask(__name__)
APP.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO' #FIXME replace this by an ENV variable
 #NOTE: timeout allows to avoid database is locked - it is workaround
APP.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('EVOPIE_DATABASE_URI', 'sqlite:///DB_quizlib.sqlite') + "?timeout=20"
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
APP.config['FLASK_ADMIN_SWATCH'] = 'cerulean' # set optional bootswatch theme for flask_admin
# APP.config["SQLALCHEMY_ECHO"] = True #change to true to see logs of sql requests
db_log_file_name = os.getenv('EVOPIE_DATABASE_LOG')
if db_log_file_name:
    formatter = logging.Formatter(fmt='%(asctime)s %(message)s',
                                  datefmt='[%Y-%m-%d %H:%M:%S]')    
    db_file_logger = logging.FileHandler(db_log_file_name)
    db_file_logger.setFormatter(formatter)
    db_file_logger.setLevel(logging.INFO)
    db_file_logger.emit(logging.LogRecord(db_file_logger.name, logging.INFO, "", 0, f"DB file: {APP.config['SQLALCHEMY_DATABASE_URI']}", None, None))
    logging.getLogger('sqlalchemy.engine').addHandler(db_file_logger)

from datalayer import StartupDatabase, RegisterGlobalLogger
DB = StartupDatabase(APP)
LOGGER = RegisterGlobalLogger(APP.logger)


from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from datalayer import models
from flask_login import current_user
from flask import request, redirect, url_for
from collections import namedtuple

#custom route converters - allows us to avoid unnecessary validations each time
#NOTE: detauch could happen if any hook tries to do with app
#https://stackoverflow.com/questions/19818082/how-does-a-sqlalchemy-object-get-detached
from werkzeug.routing import IntegerConverter, ValidationError
class QuizConverter(IntegerConverter):
    regex = r'\d+(\/\d+)?'

    def to_python(self, value):
        # check if value has a slash
        if '/' not in value:
            quiz_id = super().to_python(value)
            quiz = models.Quiz.query.filter_by(id = quiz_id).first()
            if quiz is None:
                raise ValidationError
            return quiz
        else:
            quiz_id, course_id = value.split('/')
            quiz = models.Quiz.query.filter_by(id = quiz_id).first()
            course = models.Course.query.filter_by(id = course_id).first()
            if quiz is None or course is None:
                raise ValidationError #will try next route
            return namedtuple('Quiz_Course', ['quiz', 'course'])(quiz, course)

    def to_url(self, quiz_course):
        if isinstance(quiz_course, tuple) and isinstance(quiz_course[0], models.Quiz):
            quiz_id = str(quiz_course[0].id)
            course_id = str(quiz_course.course.id)
            return quiz_id + '/' + course_id
        if isinstance(quiz_course, models.Quiz):
            return super().to_url(quiz_course.id if isinstance(quiz_course, models.Quiz) else quiz_course) #treat quiz as id itself 
        return str(quiz_course[0].id) + '/' + str(quiz_course[1].id) #quiz_course can be int at start
class QuizWithAttemptConverter(QuizConverter):
    regex = r'\d+/\d+'

    def to_python(self, value):
        quiz_id, course_id = value.split('/')
        quiz = models.Quiz.query.filter_by(id = quiz_id).first()
        course = models.Course.query.filter_by(id = course_id).first()
        attempt = models.QuizAttempt.query.filter_by(quiz_id = quiz_id, student_id = current_user.id, course_id = course_id).first()
        if quiz is None or course is None or attempt is None:
            raise ValidationError
        return namedtuple('Quiz_Course_Attempt', ['quiz', 'course', 'attempt'])(quiz, course, attempt)

    def to_url(self, quiz_attempt):
        if isinstance(quiz_attempt, tuple) and isinstance(quiz_attempt[0], models.Quiz):
            # return super().to_url(quiz_attempt[0])
            quiz_id = str(quiz_attempt[0].id)
            course_id = str(quiz_attempt[1].id)
            return quiz_id + '/' + course_id
        if isinstance(quiz_attempt, models.Quiz):
            return super().to_url(quiz_attempt)
        return str(quiz_attempt[0].id) + '/' + str(quiz_attempt[1].id) #quiz_course can be int at start

class QuizAttemptConverter(IntegerConverter):

    def to_python(self, value):
        quiz_id = super().to_python(value)
        attempt = models.QuizAttempt.query.filter_by(quiz_id = quiz_id, student_id = current_user.id).first()
        if attempt is None: 
            raise ValidationError #will try next route
        return attempt

    def to_url(self, attempt):
        return super().to_url(attempt.quiz_id if isinstance(attempt, models.QuizAttempt) else attempt) #treat quiz as id itself     
        
APP.url_map.converters['quiz'] = QuizConverter
APP.url_map.converters['attempt'] = QuizAttemptConverter
APP.url_map.converters['qa'] = QuizWithAttemptConverter

def date(d):
    return d.strftime("%B %d, %Y by %I:%M %p")

APP.add_template_filter(date)

class ProtectedAdminIndexView(AdminIndexView):
    def is_accessible(self):
        id = current_user.get_id()
        user = models.User.query.get(id)
        if user:
            return user.is_admin() #FIXME use the user loader instead
        else:
            return False # for the anonymous user when no one is logged in

class ProtectedModelView(ModelView):
    def is_accessible(self):
        id = current_user.get_id()
        user = models.User.query.get(id)
        if user:
            return user.is_admin() #FIXME use the user loader instead
        else:
            return False # for the anonymous user when no one is logged in

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

class QuizQuestionView(ProtectedModelView):
    column_hide_backrefs = True
    column_list = ('id', 'question_id', 'distractors')

class QuizAttemptView(ProtectedModelView):
    column_list = ('id', 'initial_responses', 'revised_responses', 'initial_total_score', 'revised_total_score','quiz','student')

class QuestionView(ProtectedModelView):
    column_list = ('id', 'title')
    
class JustificationView(ProtectedModelView):
    column_list = ('id', 'student', 'quiz_question_id', 'distractor_id', 'justification')

class DistractorView(ProtectedModelView):
    column_list = ('id','answer')

class QuizView(ProtectedModelView):
    column_list = ('id','title','status')
    column_editable_list = ['status']
    
class UserView(ProtectedModelView):
    column_list = ('id', 'last_name', 'first_name', 'email', 'role')
    column_exclude_list = ['password']
    column_searchable_list = ['first_name', 'last_name', 'email']
    column_editable_list = ['last_name', 'email', 'first_name']

class Likes4JustificationsView(ProtectedModelView):
    pass

admin = Admin(APP, index_view=ProtectedAdminIndexView(), name='EvoPIE', template_mode='bootstrap3')
admin.add_view(UserView(models.User, DB.session))
admin.add_view(QuizView(models.Quiz, DB.session))
admin.add_view(QuizQuestionView(models.QuizQuestion, DB.session))
admin.add_view(QuizAttemptView(models.QuizAttempt, DB.session))
admin.add_view(QuestionView(models.Question, DB.session))
admin.add_view(JustificationView(models.Justification, DB.session))
admin.add_view(DistractorView(models.Distractor, DB.session))
admin.add_view(Likes4JustificationsView(models.Likes4Justifications, DB.session))

from .routes_mcq import mcq as mcq_blueprint
APP.register_blueprint(mcq_blueprint)

from .routes_auth import auth as auth_blueprint
APP.register_blueprint(auth_blueprint)

from .routes_pages import pages as pages_blueprint
APP.register_blueprint(pages_blueprint)

login_manager = LoginManager()
login_manager.login_view = 'auth.get_login'



@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

login_manager.init_app(APP)

# Bad idea - several workers try to execute this
# if os.getenv("INIT_DB", "0") == "1":
#     print("Init db")
#     DB.create_all()

# from . import utils
# from . import quiz_model
from . import cli #adds cli commands to app
# from quiz_model import set_quiz_model 
from . import quiz_model
quiz_model.set_quiz_model(None)


import sys
## vvv --- RPW: This register the Dash applications
##         This must happen **after** the DB init step
if "DB-init" not in sys.argv:
    from evopie.datadashboard import register_dashapps
    register_dashapps(APP)
    APP.logger.info("All Dash applications are registered.")
## ^^^ ---

import debugpy
debug_mode = os.environ.get("DEBUG")
if debug_mode == "True":
    # to enable remote debugging into the app: 
    port = 5678
    APP.logger.info(f"DEBUGPY --> Enabled & Listening on {port}")
    debugpy.listen(("0.0.0.0", port))
else:
    APP.logger.info(f"DEBUGPY --> NOT Enabled")

