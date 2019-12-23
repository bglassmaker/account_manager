import os
import logging
from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app import app
from app.forms import CreateUserForm
from flask_ldap3_login.forms import LDAPLoginForm
from flask_login import login_user, logout_user, login_required, current_user

from account_manager.employee import Employee, get_all_accounts, get_ad_user, suspend_accounts, enable_accounts
from app.models import User

logging.getLogger('account_manager').setLevel(logging.DEBUG)
logging.getLogger('ldap3').setLevel(logging.DEBUG)

# Office365 Log In Info
# api_id = os.environ.get('APPID')
# client_secret = os.environ.get('CLIENT_SECRET')
# tenant_id = os.environ.get('AZURE_TENANT_ID')
# credentials = (api_id, client_secret)

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        employee = Employee(
            first_name=form.firstname.data, 
            last_name=form.lastname.data, 
            username=form.username.data, 
            location=form.location.data, 
            department=form.department.data, 
            job_title=form.job_title.data)
        employee.create_ad_account()
        #employee.create_o365_user()
        flash('User Created')
        return redirect(url_for('users'))
    return render_template('create_user.html', title='Create User', form=form)

@app.route('/suspend_user', methods=['GET'])
@login_required
def suspend_user():
    username = request.args.get('username')
    user = get_ad_user(username)
    suspend_accounts(user)
    flash('User Disabled')
    return redirect(url_for('users'))

@app.route('/enable_user', methods=['GET'])
@login_required
def enable_user():
    username = request.args.get('username')
    user = get_ad_user(username)
    enable_accounts(user)
    flash('User Enabled')
    return redirect(url_for('users'))

@app.route('/users', methods=['GET'])
@login_required
def users():
    users = get_all_accounts()

    return render_template('users.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LDAPLoginForm()

    if form.validate_on_submit():        
        login_user(form.user)
        return redirect('/')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))