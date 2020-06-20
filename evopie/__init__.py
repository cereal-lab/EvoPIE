from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

APP = Flask(__name__)
APP.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DB_quizlib.sqlite'
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
DB = SQLAlchemy(APP)

from evopie import routes

from .routes_auth import auth as auth_blueprint
APP.register_blueprint(auth_blueprint)

login_manager = LoginManager()
login_manager.login_view = 'auth.get_login'

from .models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.init_app(APP)
