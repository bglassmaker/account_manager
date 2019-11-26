import os

from O365 import Account
from user import User


api_id = os.environ['APPID']
client_secret = os.environ['CLIENT_SECRET']
tenant_id = os.environ['AZURE_TENANT_ID']

credentials = (api_id, client_secret)


# maybe switch to user authentication later?

account = Account(credentials, auth_flow_type='credentials', tenant_id=tenant_id)

if account.authenticate():
    print('Authenticated')

user_list = User(parent=account).get_users()
print(str(user_list))