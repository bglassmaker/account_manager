import os
from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app import app
from app.forms import CreateUserForm
from flask_ldap3_login.forms import LDAPLoginForm
from flask_login import login_user, logout_user, login_required, current_user

from account_manager.employee import Employee
from app.models import User

# Office365 Log In Info
# api_id = os.environ.get('APPID')
# client_secret = os.environ.get('CLIENT_SECRET')
# tenant_id = os.environ.get('AZURE_TENANT_ID')
# credentials = (api_id, client_secret)

@app.route('/')
@app.route('/index')
def index():
    if not current_user or current_user.is_anonymous:
        return redirect(url_for('login'))

    return render_template('index.html', title='Home')

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        user = Employee(firstname=form.firstname.data, lastname=form.lastname.data, username=form.username.data,
                    location=form.location.data, department=form.department.data, job_title=form.job_title.data)
        user.create_ad_user()
        user.create_o365_user()
        #user.create_zen_user()
        flash('It might have worked?')
    return render_template('create_user.html', title='Create User', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LDAPLoginForm()

    if form.validate_on_submit():
        login_user(form.user)
        return redirect('/')
    
    return render_template('login.html', form=form)

@app.route('/lougout')
def logout():
    logout_user()
    return redirect(url_for('index'))