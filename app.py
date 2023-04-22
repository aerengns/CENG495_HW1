import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

from models import User

app = Flask(__name__)
bcrypt = Bcrypt(app)
import main

# Set the secret key to some random bytes. Keep this really secret!
secret = os.getenv('SECRET_KEY')
app.secret_key = secret

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)
