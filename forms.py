from flask_wtf import FlaskForm
from wtforms import StringField, SearchField, PasswordField, IntegerField
from wtforms.validators import InputRequired, Email

class LoginForm(FlaskForm):

    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


class SignupForm(FlaskForm):

    username = StringField('Username', validators=[InputRequired()])
    first_name = StringField('First_name')
    last_name = StringField('Last_name')
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


class CurrencyForm(FlaskForm):

    from_currency = StringField('From_Currency', validators=[InputRequired()])
    to_currency = StringField('To_Currency', validators=[InputRequired()])
    amount = IntegerField('Amount', validators=[InputRequired()])
    