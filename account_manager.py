import os

from O365 import Account
from account_manager.user import Users
from flask import Flask, escape, request, render_template


api_id = os.environ['APPID']
client_secret = os.environ['CLIENT_SECRET']
tenant_id = os.environ['AZURE_TENANT_ID']

credentials = (api_id, client_secret)


# maybe switch to user authentication later?

account = Account(credentials, auth_flow_type='credentials', tenant_id=tenant_id)

if account.authenticate():
    print('Authenticated')

user_list = Users(parent=account).get_users()
print(str(user_list))

user_id = 'e04f3e08-7766-425f-8229-c295a80c6809'

single_user = Users(parent=account).get_user(user_id)
print(single_user)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')