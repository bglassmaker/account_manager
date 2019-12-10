from flask import render_template, flash, redirect
from app import app
from app.forms import CreateUserForm

from account_manager.active_directory import User

@app.route('/')

@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        user = User(firstname=form.firstname.data, lastname=form.lastname.data)
        user.create_ad_user(location=form.location.data)
        flash('It might have worked?')
    return render_template('create_user.html', title='Create User', form=form)