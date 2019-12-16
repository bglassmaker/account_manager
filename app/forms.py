from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, SelectMultipleField, SelectField
from wtforms.validators import ValidationError, DataRequired

from account_manager.user import User

class CreateUserForm(FlaskForm):
    locations = [('Whipple','Whipple Office'), ('Campbell','Campbell Office'), ('Brush','Brush Office')]

    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    job_title = StringField('Job Title', validators=[DataRequired()])
    location = SelectField('Employee Location', choices=locations)
    submit = SubmitField('Create User')

    def validate_username(self, username):
        if User.check_if_username_exists(username):
            raise ValidationError('Please use a different username.')
        