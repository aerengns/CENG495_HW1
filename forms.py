from datetime import datetime
from urllib.parse import urlparse, urljoin

from flask import request, flash
from wtforms import Form, StringField, PasswordField, BooleanField, SelectField, IntegerField, DateTimeField
from wtforms.validators import InputRequired, Length, ValidationError, Regexp, EqualTo, NumberRange

from app import bcrypt
from db import users_collection
from models import User, ITEM_TYPES, Item


def validate_username(username):
    if users_collection.find_one({'username': username.data}):
        return False
    return True


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


class SignUpForm(Form):
    username = StringField(
        validators=[
            InputRequired(),
            Length(3, 32, message="Please provide a valid name"),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Usernames must have only letters, " "numbers, dots or underscores",
            )
        ]
    )
    pwd = PasswordField(validators=[InputRequired(), Length(6, 32)])
    cpwd = PasswordField(
        validators=[
            InputRequired(),
            Length(8, 72),
            EqualTo("pwd", message="Passwords must match !"),
        ]
    )
    is_admin = BooleanField(default=False)

    def validate(self, extra_validators=None):
        return validate_username(self.username)


class LoginForm(Form):
    username = StringField(validators=[InputRequired(), Length(3, 32)])
    pwd = PasswordField(validators=[InputRequired(), Length(6, 32)])
    remember = BooleanField(default=False)

    def validate(self, extra_validators=None):
        user = User.get_by_username(self.username.data)
        if not user or not bcrypt.check_password_hash(user.pwd, self.pwd.data):
            return False
        return True


class ItemForm(Form):
    item_type = SelectField(choices=ITEM_TYPES, validators=[InputRequired()])
    name = StringField(validators=[InputRequired()])
    description = StringField(validators=[InputRequired()])
    price = IntegerField(validators=[InputRequired()])
    image = StringField(default="")
    spec = StringField()
    color = StringField()
    size = StringField()


class ReviewForm(Form):
    text = StringField(default="")
    rating = IntegerField(validators=[InputRequired(), NumberRange(1, 5)])



