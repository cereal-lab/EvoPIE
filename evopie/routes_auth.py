# pylint: disable=no-member
# pylint: disable=E1101 

from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response
from flask import flash, Markup
from flask import Blueprint
from flask_login import login_user, login_required, current_user, login_manager, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

import evopie.models as models


auth = Blueprint('auth', __name__)



@auth.route('/login')
def get_login():
    return render_template('login.html')



@auth.route('/signup')
def get_signup():
    return render_template('signup.html')



@auth.route('/login', methods=['POST'])
def post_login():
    if request.json:
        email = request.json.get('email')
        password = request.json.get('password')
        remember = True if request.json.get('remember') else False
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
    user = models.User.query.filter_by(email=email).first()

    if not user or not user.password == password:
        #FIXME part of not storing clear text passwords in the DB
        # check_password_hash(user.password, password):
        flash(Markup('Login or password incorrect. Do you need to <a href="' + url_for('auth.get_signup') + '">sign up</a> for an account?'))
        return redirect(url_for('auth.get_login'))
    login_user(user, remember=remember)
    return redirect(url_for('mcq.dashboard'))



@auth.route('/signup', methods=['POST'])
def post_signup():
    if request.json:
        email = request.json.get('email')
        first_name = request.json.get('firstname')
        last_name = request.json.get('lastname')
        password = request.json.get('password')
    else:
        email = request.form.get('email')
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')
        password = request.form.get('password')

    # making sure the user does not already exist
    if models.User.query.filter_by(email=email).first():
        flash('Email address already exists')
        return redirect(url_for('auth.get_signup'))

    new_user = models.User(email=email, first_name=first_name, last_name=last_name, password=password, role='student') #FIXME ROLES tbd
    #FIXME alright we're not gonna store pwd in clear but just playing around for now
    #generate_password_hash(password, method='sha256')

    models.DB.session.add(new_user)
    models.DB.session.commit()

    return redirect(url_for('auth.get_login'))
    


@auth.route('/logout')
def logout():
    logout_user()
    return 'Logout'