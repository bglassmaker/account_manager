from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.employees import bp
from app.employees.employee import Employee, get_ad_user, suspend_accounts, enable_accounts, get_all_accounts
from app.employees.forms import CreateUserForm

@bp.route('/create_user', methods=['GET', 'POST'])
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
        return redirect(url_for('employees.users'))
    return render_template('employees/create_user.html', title='Create User', form=form)

@bp.route('/suspend_user', methods=['GET'])
@login_required
def suspend_user():
    username = request.args.get('username')
    user = get_ad_user(username)
    suspend_accounts(user)
    flash('User Disabled')
    return redirect(url_for('employees.users'))

@bp.route('/enable_user', methods=['GET'])
@login_required
def enable_user():
    username = request.args.get('username')
    user = get_ad_user(username)
    enable_accounts(user)
    flash('User Enabled')
    return redirect(url_for('employees.users'))

@bp.route('/users', methods=['GET'])
@login_required
def users():
    users = get_all_accounts()

    return render_template('employees/users.html', users=users)

