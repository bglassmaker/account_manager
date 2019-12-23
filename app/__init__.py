from flask import Flask
from config import Config
from flask_login import LoginManager
from flask_ldap3_login import LDAP3LoginManager
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.config.from_object(Config)
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
ldap_manager = LDAP3LoginManager(app)


from app import routes