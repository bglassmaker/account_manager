from flask import Flask
from config import Config
from flask_login import LoginManager
from flask_ldap3_login import LDAP3LoginManager
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
app.config['DEBUG'] = True
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)
ldap_manager = LDAP3LoginManager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


from app import routes