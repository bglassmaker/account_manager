import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_login import LoginManager
from flask_ldap3_login import LDAP3LoginManager
from flask_bootstrap import Bootstrap
from config import Config

bootstrap = Bootstrap()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
ldap_manager = LDAP3LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager.init_app(app)
    ldap_manager.init_app(app)
    bootstrap.init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.employees import bp as employees_bp
    app.register_blueprint(employees_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/account_manager.log',
                                        maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Account Manager Startup')
    
    return app
