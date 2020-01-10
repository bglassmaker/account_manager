import os
from O365 import Account, MSGraphProtocol
from app import ad_account_manager
from app.employees.employee import Employee 
from app.employees.o365_user_manager import User as o365_user

client_id = os.environ.get('O365_CLIENT_ID')
client_secret = os.environ.get('O365_CLIENT_SECRET')
tenant_id = os.environ.get('O365_TENANT_ID')
credentials = (client_id, client_secret)
protocol =  MSGraphProtocol()
account = Account(credentials, auth_flow_type='credentials', tenant_id=tenant_id, protocol=protocol)
user = o365_user(parent=account)

def create_o365_account(employee):
    if not account.is_authenticated:
        account.authenticate()
    response = user.create_o365_account(employee)

def get_o365_account(email):
    if not account.is_authenticated:
        account.authenticate()
    response = user.get_o365_user(email)
    if response:
        employee = Employee(
            first_name= response['givenName'],
            last_name= response['surname'],
            full_name= response['displayName'],
            department= response['department'],
            job_title= response['jobTitle'],
            email= response['mail'],
            user_principal_name= response['userPrincipalName'],
            account_enabled= response['accountEnabled']
        )
        return employee
    return None

def update_o365_account_status(email, account_enabled):
    if not account.is_authenticated:
        account.authenticate
    
    return user.update_o365_update_account_status

def get_ad_user(username):
    return ad_account_manager.get_ad_user(username)
