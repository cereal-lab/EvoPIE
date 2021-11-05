from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


APP = Flask(__name__)
APP.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO' #FIXME replace this by an ENV variable
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DB_quizlib.sqlite'
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
APP.config['FLASK_ADMIN_SWATCH'] = 'cerulean' # set optional bootswatch theme for flask_admin

DB = SQLAlchemy(APP)


from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from evopie import models
from flask_login import current_user
from flask import request, redirect, url_for

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
    column_list = ('id', 'student_id', 'quiz_question_id', 'distractor_id', 'justification')

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

admin = Admin(APP, index_view=ProtectedAdminIndexView(), name='EvoPIE', template_mode='bootstrap3')
admin.add_view(UserView(models.User, DB.session))
admin.add_view(QuizView(models.Quiz, DB.session))
admin.add_view(QuizQuestionView(models.QuizQuestion, DB.session))
admin.add_view(QuizAttemptView(models.QuizAttempt, DB.session))
admin.add_view(QuestionView(models.Question, DB.session))
admin.add_view(JustificationView(models.Justification, DB.session))
admin.add_view(DistractorView(models.Distractor, DB.session))


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

from . import utils
