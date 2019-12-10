from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, SelectMultipleField

class CreateUserForm(FlaskForm):
    firstname = StringField('Firstname')
    lastname = StringField('Lastname')
    location = StringField('Location')
    password = StringField('Password')
    submit = SubmitField('Create User')