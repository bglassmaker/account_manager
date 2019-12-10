from flask import Flask
from config import Config
from flask_login import LoginManager
from flask_ldap3_login import LDAP3LoginManager
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object(Config)
app.config['DEBUG'] = True
bootstrap = Bootstrap(app)


from app import routes