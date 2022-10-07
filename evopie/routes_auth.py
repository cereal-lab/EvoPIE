# pylint: disable=no-member
# pylint: disable=E1101 

import json
from flask import jsonify, abort, request, Response, render_template, redirect, url_for, make_response
from flask import flash, Markup
from flask import Blueprint
from flask_login import login_user, login_required, current_user, login_manager, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from .config import ROLE_INSTRUCTOR, ROLE_STUDENT

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
    if request.is_json:
        email = request.json.get('email')
        password = request.json.get('password')
        remember = True if request.json.get('remember_me') else False
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember_me') else False
    user = models.User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):    
        if request.is_json:
            return jsonify({ "message": "Login or password incorrect", "redirect": url_for('auth.get_signup')}), 400    
        flash(Markup('Login or password incorrect. Do you need to <a href="' + url_for('auth.get_signup') + '">sign up</a> for an account?'))
        return redirect(url_for('auth.get_login'))
    login_user(user, remember=remember, duration=timedelta(days=5))
    if request.is_json:
        return jsonify({ "message": "Login successful", "id": user.id }), 200
    return redirect(url_for('pages.index'))

@auth.route('/signup', methods=['POST'])
def post_signup():
    if request.is_json:
        email = request.json.get('email')
        first_name = request.json.get('firstname')
        last_name = request.json.get('lastname')
        password = request.json.get('password')
        retype = request.json.get('retype')
    else:
        email = request.form.get('email')
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')
        password = request.form.get('password')
        retype = request.form.get('retype')

    if(retype != password):
        flash('Passwords do not match')
        return redirect(url_for('auth.get_signup'))
    
        
    # making sure the user does not already exist
    if models.User.query.filter_by(email=email).first():        
        found_url = url_for('auth.get_signup')
        message = 'Email address already exists'
        if request.is_json:
            return jsonify({ "message": message, "redirect": found_url }), 200
        flash(message)
        return redirect(found_url)
        #TODO we should redirect to password recovery so that, if someone is spam-creating
        # accounts, the first one will be salvageable by whoever actually has legitimate access
        # to the email address associated with it. 

    #FIXME for now, we hardcode that the 1st user to signup is an INSTRUCTOR
    # the testing scripts are hardwired to work with that assumption too. 
    # Need to fix this as soon as we bootstrap an ADMIN user and allow them 
    # to promote a user to a different role; e.g., promote_to_instructor()
    if models.User.query.all():
        # there is at least one user so this one is going to be a STUDENT
        its_role = ROLE_STUDENT
    else:
        # first to the key, first to the egg!
        its_role = ROLE_INSTRUCTOR

    password = generate_password_hash(password, method='sha256')

    if user is not None and user.password is None:
        user.password = password
        user.first_name = first_name
        user.last_name = last_name
        user.set_role(its_role)
    elif user is None:
        new_user = models.User(email=email, first_name=first_name, last_name=last_name, password=password, role=its_role) #NOTE default role is STUDENT
        models.DB.session.add(new_user)
    
    models.DB.session.commit()

    if request.is_json:
        return jsonify({ "message": "User created", "login": url_for('auth.get_login'), "id": new_user.id }), 201
    return redirect(url_for('auth.get_login'))

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('pages.index'))
    #return 'Logged out'