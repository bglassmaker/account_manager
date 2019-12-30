from flask import Blueprint, current_app
import logging
from flask_login import current_user

bp = Blueprint('auth', __name__)

from app.auth import routes
from flask_ldap3_login import AuthenticationResponseStatus
from flask_ldap3_login.forms import LDAPLoginForm

def my_validate_ldap(self):
    logging.debug('Validating LDAPLoginForm against LDAP')
    'Validate the username/password data against ldap directory'
    ldap_mgr = current_app.ldap3_login_manager
    username = self.username.data
    password = self.password.data

    result = ldap_mgr.authenticate(username, password)

    if result.status == AuthenticationResponseStatus.success:
        self.user = ldap_mgr._save_user(
            result.user_dn,
            result.user_id,
            password,
            result.user_info
        )            
        return True

    else:
        self.user = None
        self.username.errors.append('Invalid Username/Password.')
        self.password.errors.append('Invalid Username/Password.')
        return False

LDAPLoginForm.validate_ldap = my_validate_ldap
