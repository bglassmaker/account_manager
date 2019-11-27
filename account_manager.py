import os

from O365 import Account
from account_manager.office365 import Users
from flask import Flask, escape, request, render_template


api_id = os.environ['APPID']
client_secret = os.environ['CLIENT_SECRET']
tenant_id = os.environ['AZURE_TENANT_ID']

credentials = (api_id, client_secret)


# maybe switch to user authentication later?

account = Account(credentials, auth_flow_type='credentials', tenant_id=tenant_id)

if account.authenticate():
    print('Authenticated')

#user_list = Users(parent=account).get_users()
#print(str(user_list))

#user_id = 'ca2b77c6-0f0f-4f99-80f1-deea945b4b03'
username = 'testuser@decisionpointcenter.com'
single_user = Users(parent=account).get_user(username)
print(single_user)

#app = Flask(__name__)

#@app.route('/')
#def index():
#    return render_template('index.html')