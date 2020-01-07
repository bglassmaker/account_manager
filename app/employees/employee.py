import os
import random
import string
import logging
import ldap3
from ldap3 import Server, ServerPool, Connection, ALL, NTLM

log = logging.getLogger(__name__)

#_server1 = Server("192.168.0.13", use_ssl=True)
#_server2 = Server("192.168.0.14", use_ssl=True)
#_server_pool = ServerPool([_server1,_server2], pool_stratagy=FIRST, active=True)
#test domain settings
_server_pool= Server('testdomain.local', use_ssl=True) #use_ssl=True
# Need to change this to use the LDAP3 Login through flask and assign roles to people who should use it.
# ad_user = os.environ.get('ADUSER')
_ad_user = os.environ.get('ADUSERTEST')
# _ad_password = os.environ.get('ADPASSWORD')
_ad_password = os.environ.get('ADPASSWORDTEST')
#_base_ou = "ou=DecisionPointCenter,dc=DecisionPointCenter,dc=local"
_base_ou = "ou=TestDomain,dc=testdomain,dc=local"

class Employee():
    """ An Employee """

    _endpoints = {
        # endpoints for user controls
        'user': '/users/{id}',
        'users': '/users', 
    }

    def __init__(
        self, first_name:str, last_name:str, full_name:str=None, username:str=None, password:str=None, department:str=None, 
        job_title:str=None, location=None, dn:str=None, account_enabled:bool=False,user_principal_name=None, 
        user_account_control=None, email_address:str=None, **kwargs):

        if username:
           username.lower()

        self.first_name = first_name
        self.last_name = last_name
        self.username = username or (first_name[0] + last_name).lower()
        self.location = location
        self.department = department
        self.job_title = job_title 
        self.account_enabled = account_enabled
        self.user_principal_name = user_principal_name
        self.user_account_control = user_account_control
        self.full_name = full_name or '{} {}'.format(self.first_name, self.last_name)
        self.email_address = email_address or '{}@decisionpointcenter.com'.format(self.username)
        self.dn = dn or 'cn={},ou=Domain Users,ou={} Office,{}'.format(self.full_name, self.location, _base_ou)
        self.password = password or self._random_password(8)

    def _random_password(self, length:int) -> str:
        letters_and_digits = string.ascii_letters + string.digits
        return''.join(random.choice(letters_and_digits) for i in range(length))
    
    '''
    Active Directory
    '''
    
    def reset_ad_password(self, user) -> bool:
        c = connect_to_ad(user.dn, user.password)
        c.bind()
        self.password = self._random_password(8)

        c.extend.microsoft.modify_password(self.dn, self.password)
        c.modify(self.dn, {'pwdLastSet': ('MODIFY_REPLACE', [0])})
        result = c.result
        c.unbind()

        if result['result'] > 0:
            log.debug(result)
            raise

        return result
    
    def unlock_ad_account(self, user) -> bool:
        c = connect_to_ad(user.dn, user.password)
        c.bind()
        c.extend.microsoft.unlock_account(self.dn)
        result = c.result
        c.unbind()
        
        if result['result'] > 0:
            log.debug(result['description'])
            raise

        return result
    
    def suspend_ad_account(self, user):
        c = connect_to_ad(user.dn, user.password)
        c.bind()
        disabled_path = "ou=Disabled Users,{}".format(_base_ou)
        #disable user
        c.modify(self.dn, {'userAccountControl': [('MODIFY_REPLACE', 514)]})
        #move user to disabled
        c.modify_dn(self.dn, 'cn={}'.format(self.full_name), new_superior=disabled_path)
        result = c.result
        c.unbind()

        if result['result'] > 0:
            log.debug(result)
            raise

        return result
    
    def enable_ad_account(self, user):
        c = connect_to_ad(user.dn, user.password)
        c.bind()
        enabled_path = "ou=Domain Users,ou={} Office,{}".format(self.location, _base_ou)
        #Enable user
        c.modify(self.dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
        #move user to DN
        c.modify_dn(self.dn, 'cn={}'.format(self.full_name), new_superior=enabled_path)
        result = c.result
        c.unbind()

        if result['result'] > 0:
            log.debug(result)
            raise

        return result
            
    def create_ad_account(self, user):
        c = connect_to_ad(user.dn, user.password)
        c.bind()
        # if self.check_if_username_exists():
        #     raise ValueError("Username already exists")

        log.debug('Adding user {} with password {}'.format(self.dn, self.password))
        c.add(
            self.dn, 
            ['person', 'user'], 
            {
                'sAMAccountName': self.username, 
                'userPrincipalName': self.username + '@testdomain.local', 
                'givenName': self.first_name, 
                'sn': self.last_name, 
                'displayName': self.full_name,
                'mail': self.email_address,
                'company': 'Decision Point Center',
                'department': self.department,
                'title': self.job_title,
                'physicalDeliveryOfficeName': self.location        
            })
        if c.result['result'] > 0:
            log.debug("User not created : " + str(c.result))
        c.extend.microsoft.modify_password(self.dn, self.password)
        if c.result['result'] > 0:
            log.debug("Password not created {}: ".format(self.password) + str(c.result))
        c.modify(self.dn, {'userAccountControl': ('MODIFY_REPLACE', [512])})
        if c.result['result'] > 0:
            log.debug("User not enabled : " + str(c.result))
        c.modify(self.dn, {'pwdLastSet': ('MODIFY_REPLACE', [0])})
        if c.result['result'] > 0:
            log.debug("Password not set to force reset : " + str(c.result))
        if c.bind():
            c.unbind()
        return [c.result, self.password]

    def check_if_username_exists(self) -> bool:
        c = connect_to_ad(_ad_user,_ad_password)
        return c.search(search_base=_base_ou, search_filter='(sAMAccountName={})'.format(self.username))
        

def get_all_accounts(user):
    c = connect_to_ad(user.dn, user.password)
    c.bind()
    c.search(
        search_base=_base_ou,
        search_filter='(objectclass=person)', # (&(objectclass=person)(|(userAccountControl=512)(userAccountControl=514)))
        attributes=['cn',
            'userAccountControl', 
            'mail', 
            'givenName', 
            'sn', 
            'sAMAccountName', 
            'physicalDeliveryOfficeName'
            ])
    response = c.response
    c.unbind()
    employees = {'enabled users':[], 'disabled users':[], 'other users':[]}
    for r in response:
        employee = Employee(
            first_name = r['attributes']['givenName'],
            last_name = r['attributes']['sn'],
            full_name = r['attributes']['cn'],
            username = r['attributes']['sAMAccountName'],
            email_address = r['attributes']['mail'],
            dn = r['dn'],
            user_account_control = r['attributes']['userAccountControl'],
            location = r['attributes']['physicalDeliveryOfficeName']
        )
        if employee.user_account_control == 512:
            employees['enabled users'].append(employee)
        elif employee.user_account_control == 514:
            employees['disabled users'].append(employee)
        else:
            employees['other users'].append(employee)
    
    if not employees:
        raise
    
    return employees

def get_ad_user(username:str):
    c = connect_to_ad(_ad_user,_ad_password)
    c.bind()
    c.search(
        search_base=_base_ou, 
        search_filter='(sAMAccountName={})'.format(username), 
        attributes=[
            'givenName', 
            'sn', 
            'userAccountControl',
            'mail',
            'sAMAccountName',
            'physicalDeliveryOfficeName'
            ])
    response = c.response[0]  
    c.unbind()
    employee = Employee(
        first_name = response['attributes']['givenName'],
        last_name = response['attributes']['sn'],
        dn = response['dn'],
        user_account_control = response['attributes']['userAccountControl'],
        email = response['attributes']['mail'],
        username = response['attributes']['sAMAccountName'],
        location = response['attributes']['physicalDeliveryOfficeName']
    )
    
    return employee

def connect_to_ad(user, password):
    return Connection(_server_pool, user=user, password=password) 

def suspend_accounts(user, employee):
    if employee.suspend_ad_account(user): #and employee.update_o365_account_status('False'):
        return True
    return False

def enable_accounts(user, employee):
    if employee.enable_ad_account(user): # and employee.update_o365_account_status('True'):
        return True
    return False
