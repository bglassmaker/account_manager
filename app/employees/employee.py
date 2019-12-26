import os
import random
import string
import logging
from ldap3 import Server, ServerPool, Connection, ALL, NTLM
from O365.utils import ApiComponent
from O365 import Account

log = logging.getLogger(__name__)

#_server1 = Server("192.168.0.13")
#_server2 = Server("192.168.0.14")
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
# Office 365 Settings 
_api_id = os.environ.get('APPID')
_client_secret = os.environ.get('CLIENT_SECRET')
_tenant_id = os.environ.get('AZURE_TENANT_ID')
_credentials = (_api_id, _client_secret)

# maybe switch to user authentication later?

class Employee():
    """ An Employee """

    _endpoints = {
        # endpoints for user controls
        'user': '/users/{id}',
        'users': '/users', 
    }
    
    # Connection(_credentials, auth_flow_type='_credentials', tenant_id=_tenant_id)

    def __init__(
        self, first_name:str, last_name:str, full_name:str=None, username:str=None, password:str=None, department:str=None, 
        job_title:str=None, location=None, dn:str=None, account_enabled:bool=False, parent=None, con=None, 
        user_account_control=None, email_address:str=None, **kwargs):

        # if parent and con:
        #     raise ValueError('Need a parent or a connection but not both')
        # self.con = parent.con if parent else con
        # self.parent = parent if isinstance(parent, Employee) else None

        # # Choose the main_resource passed in kwargs over parent main_resource
        # main_resource = kwargs.pop('main_resource', None) or (
        #     getattr(parent, 'main_resource', None) if parent else None)
        # super().__init__(
        #     protocol=parent.protocol if parent else kwargs.get('protocol'),
        #     main_resource=main_resource
        # )

        if username:
           username.lower()

        self.first_name = first_name
        self.last_name = last_name
        self.username = username or (first_name[0] + last_name).lower()
        self.location = location
        self.department = department
        self.job_title = job_title 
        self.account_enabled = account_enabled
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
    
    def reset_ad_password(self) -> list:
        c = connect_to_ad(_ad_user,_ad_password)
        self._random_password(8)
        # add checking to make sure it worked, try?
        c.extend.microsoft.modify_password(self.dn, self.random_password)
        check_result(c.result)
        return [c.result, self.random_password]
    
    def unlock_ad_account(self):
        c = connect_to_ad(_ad_user,_ad_password)
        c.extend.microsoft.unlock_account(self.dn)
        check_result(c.result)
        return c.result
    
    def suspend_ad_account(self):
        c = connect_to_ad(_ad_user,_ad_password)
        c.bind()
        disabled_path = "ou=Disabled Users,{}".format(_base_ou)
        #disable user
        c.modify(self.dn, {'userAccountControl': [('MODIFY_REPLACE', 514)]})
        #move user to disabled
        c.modify_dn(self.dn, 'cn={}'.format(self.full_name), new_superior=disabled_path)
        result = c.result
        c.unbind()
        log.debug(result)
        return result
    
    def enable_ad_account(self):
        c = connect_to_ad(_ad_user,_ad_password)
        c.bind()
        enabled_path = "ou=Domain Users,ou={} Office,{}".format(self.location, _base_ou)
        #Enable user
        c.modify(self.dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
        #move user to DN
        c.modify_dn(self.dn, 'cn={}'.format(self.full_name), new_superior=enabled_path)
        result = c.result
        c.unbind()
        log.debug(result)
        return result
            
    def create_ad_account(self):
        c = connect_to_ad(_ad_user,_ad_password)
        c.bind()
        # if self.check_if_username_exists():
        #     raise ValueError("Username already exists")

        log.debug(self.dn)
        log.debug(self.password)
        log.debug('Adding user {}'.format(self.dn))
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

        c.extend.microsoft.modify_password(self.dn, self.password)
        log.debug(c.result)
        c.modify(self.dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
        if c.bind():
            c.unbind()
        return [c.result, self.password]

    def check_if_username_exists(self) -> bool:
        c = connect_to_ad(_ad_user,_ad_password)
        return c.search(search_base=_base_ou, search_filter='(sAMAccountName={})'.format(self.username))
        
    '''
    Office 365
    '''
    def create_o365_account(self):
        """ Creates a user

        :return: a new User
        :rtype: User
        """
        self.con = Connection(_credentials, auth_flow_type='_credentials', tenant_id=_tenant_id)
        url = self.build_url(self._endpoints.get('users'))
        password = self.random_password(8)

        data={
            'givenName': self.first_name, 
            'surname': self.last_name,
            'displayName': self.full_name, 
            'mailNickname': self.username,
            'userPrincipalName': self.email_address, 
            'accountEnabled': self.account_enabled,
            'jobTitle': self.job_title,
            'department': self.department,
            'passwordProfile': {
                "forceChangePasswordNextSignIn": True,
                "password": password
            }
        }
    
        response = self.con.post(url, data)

        if not response:
            return None
        
        return response.json()

    def update_o365_account_status(self, username, account_enabled):
        if not username:
            raise ValueError("Please provide a valid username")
        if not account_enabled:
            raise ValueError("Please provide a valid account status")

        data = {
            'accountEnabled': account_enabled
        }

        url = self.build_url(self._endpoints.get('users')).format('username')
        response = self.con.post(url, data)

        if not response:
            return None
        
        return response.json()
   
    def get_o365_user(self, user_principal_name):
        """ Get single user

        :return: Single User
        :rtype: User
        """
        if not user_principal_name:
            raise ValueError('This requires a UserID')

        url = self.build_url(self._endpoints.get('user')).format(id=user_principal_name)
        
        response = self.con.get(url)

        if not response:
            return None
        
        data = response.json()

        return data

def get_all_accounts():
    c = connect_to_ad(_ad_user, _ad_password)
    c.bind()
    c.search(
        search_base=_base_ou,
        search_filter='(&(objectclass=person)(|(userAccountControl=512)(userAccountControl=514)))',
        attributes=['cn','userAccountControl', 'mail', 'givenName', 'sn', 'sAMAccountName'])
    response = c.response
    c.unbind()
    employees = []
    for r in response:
        employee = Employee(
            first_name = r['attributes']['givenName'],
            last_name = r['attributes']['sn'],
            full_name = r['attributes']['cn'],
            username = r['attributes']['sAMAccountName'],
            email_address = r['attributes']['mail'],
            dn = r['dn'],
            user_account_control = r['attributes']['userAccountControl']
        )
        employees.append(employee)
    return employees

def get_ad_user(username:str):
    c = connect_to_ad(_ad_user,_ad_password)
    c.bind()
    c.search(
        search_base=_base_ou, 
        search_filter='(sAMAccountName={})'.format(username), 
        attributes=['givenName', 'sn', 'userAccountControl','mail','sAMAccountName','physicalDeliveryOfficeName'])
    response = c.response[0]  
    print(response) 
    employee = Employee(
        first_name = response['attributes']['givenName'],
        last_name = response['attributes']['sn'],
        dn = response['dn'],
        user_account_control = response['attributes']['userAccountControl'],
        email = response['attributes']['mail'],
        username = response['attributes']['sAMAccountName'],
        location = response['attributes']['physicalDeliveryOfficeName']
    )
    c.unbind()
    return employee

def connect_to_ad(user, password):
    return Connection(_server_pool, user=user, password=password) 

def check_result(result):
    if not result['result'] == 0:
        exit(result)   

def suspend_accounts(employee):
    employee.suspend_ad_account()
    # employee.update_o365_account_status('False')

def enable_accounts(employee):
    employee.enable_ad_account()
    # employee.update_o365_account_status('True')
