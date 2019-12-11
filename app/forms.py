from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, SelectMultipleField, SelectField

class CreateUserForm(FlaskForm):
    locations = [('Whipple','Whipple'), ('Campbell','Campbell'), ('Brush','Brush')]

    firstname = StringField('Firstname')
    lastname = StringField('Lastname')
    username = StringField('Username')
    location = SelectField('Locations', choices=locations)
    password = StringField('Password')
    submit = SubmitField('Create User')

    def validate_username(self, username):
        # need to check AD, might need to move helper methods out
        pass