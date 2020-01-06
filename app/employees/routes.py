from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
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
            job_title=form.job_title.data
            )
        employee.create_ad_account(current_user)
        #employee.create_o365_user()
        flash('User {} Created'.format(employee.full_name))
        return redirect(url_for('employees.users'))
    return render_template('employees/create_user.html', title='Create User', form=form)

@bp.route('/suspend_user', methods=['GET'])
@login_required
def suspend_user():
    username = request.args.get('username')
    employee = get_ad_user(username)
    if suspend_accounts(current_user, employee):
        flash('User Disabled')
        return redirect(url_for('employees.users'))
    flash('User NOT Disabled', 'error')
    return redirect(url_for('employees.users'))

@bp.route('/enable_user', methods=['GET'])
@login_required
def enable_user():
    username = request.args.get('username')
    employee = get_ad_user(username)
    if enable_accounts(current_user, employee):
        flash('User Enabled')
        return redirect(url_for('employees.users'))
    flash('User NOT enabled', 'error')
    return redirect(url_for('employees.users'))

@bp.route('/password_reset', methods=['GET'])
@login_required
def password_reset():
    username = request.args.get('username')
    employee = get_ad_user(username)
    if employee.reset_ad_password(current_user):
        flash('Password Reset for {}: {}'.format(employee.full_name, employee.password), 'message')
        return redirect(url_for('employees.users'))
    flash('Password not reset', 'error')
    return redirect(url_for('employees.users'))

@bp.route('/unlock_account', methods=['GET'])
@login_required
def unlock_account():
    username = request.args.get('username')
    employee = get_ad_user(username)
    if employee.unlock_ad_account(current_user):
        flash('Account unlocked for {}'.format(employee.full_name), 'message')
        return redirect(url_for('employees.users'))
    flash('Account not unlocked', 'error')
    return redirect(url_for('employees.users'))  

@bp.route('/users', methods=['GET'])
@login_required
def users():
    users = get_all_accounts(current_user)

    return render_template('employees/users.html', users=users, title='All Users')
