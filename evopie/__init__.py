from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


APP = Flask(__name__)
APP.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO' #FIXME replace this by an ENV variable
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DB_quizlib.sqlite'
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
APP.config['FLASK_ADMIN_SWATCH'] = 'cerulean' # set optional bootswatch theme for flask_admin

DB = SQLAlchemy(APP)


from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from evopie import models

admin = Admin(APP, name='EvoPIE', template_mode='bootstrap3')
admin.add_view(ModelView(models.User, DB.session))
admin.add_view(ModelView(models.Quiz, DB.session))
class QuizQuestionView(ModelView):
    column_hide_backrefs = False
    column_list = ('id', 'question_id', 'distractors')
admin.add_view(QuizQuestionView(models.QuizQuestion, DB.session))
admin.add_view(ModelView(models.QuizAttempt, DB.session))
admin.add_view(ModelView(models.Question, DB.session))
admin.add_view(ModelView(models.Justification, DB.session))
admin.add_view(ModelView(models.Distractor, DB.session))


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
