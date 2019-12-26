import os
from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app.main import bp

#from flask_login import login_user, logout_user, login_required, current_user


# Office365 Log In Info
# api_id = os.environ.get('APPID')
# client_secret = os.environ.get('CLIENT_SECRET')
# tenant_id = os.environ.get('AZURE_TENANT_ID')
# credentials = (api_id, client_secret)

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html', title='Home')
