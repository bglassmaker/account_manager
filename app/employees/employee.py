import os
import random
import string
import logging
import ldap3
from ldap3 import Server, ServerPool, Connection, ALL, NTLM
from O365.utils import ApiComponent
from O365 import Account
try:
    from flask import _app_ctx_stack as stack
except ImportError:  # pragma: no cover
    from flask import _request_ctx_stack as stack

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
# Office 365 Settings 
_api_id = os.environ.get('APPID')
_client_secret = os.environ.get('CLIENT_SECRET')
_tenant_id = os.environ.get('AZURE_TENANT_ID')
_credentials = (_api_id, _client_secret)
_account = Account(_credentials, auth_flow_type='credentials', tenant_id=_tenant_id)
# maybe switch to user authentication later?
class ADAccountManager():
    
    def __init__(self, app=None):
        self.config = {}
        self._ad_server_pool = ldap3.ServerPool(
            [],
            ldap3.FIRST,
            active=1,
            exhaust=10
        )

        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.ad_account_manager = self

        servers = list(self._ad_server_pool)
        for s in servers():
            self._ad_server_pool.remove(s)
        self.init_config(app.config)

        self.app = app

    def init_config(self, config):
        self.config.update(config)
  
    def _make_connection(self, bind_user, bind_password, contextualise=True):
        log.debug('Opening connection with {}.'.format(bind_user))
        connection = ldap3.Connection(
            self.ad_server, 
            user= bind_user, 
            password=bind_password,
            client_strategy=ldap3.SYNC,
            raise_exceptions=True
        )

        if contextualise:
            self._contextualise_connection(connection)
        return connection

    def destroy_connection(self, connection):
        """
        Destroys a connection. Removes the connection from the appcontext, and
        unbinds it.

        Args:
            connection (ldap3.Connection):  The connnection to destroy
        """

        log.debug("Destroying connection at <{0}>".format(hex(id(connection))))
        self._decontextualise_connection(connection)
        self.destroy_connection(connection)
    
    def get_ad_user(self, username:str):
        
        connection = self._make_connection(
            bind_user=self.config.get('LDAP_BIND_USER_DN'),
            bind_password=self.config.get('LDAP_BIND_USER_PASSWORD')
        )
        connection.bind()
        
        connection.search(
            search_base=_base_ou, 
            search_filter='(sAMAccountName={})'.format(username), 
            attributes=['givenName', 'sn', 'userAccountControl','mail','sAMAccountName','physicalDeliveryOfficeName'])
        
        response = None
        if len(connection.response) == 0:
            log.error('Could not get user with username : {}'.format(username))
        else:
            response = connection.response[0]  

            employee = Employee(
                first_name = response['attributes']['givenName'],
                last_name = response['attributes']['sn'],
                dn = response['dn'],
                user_account_control = response['attributes']['userAccountControl'],
                email = response['attributes']['mail'],
                username = response['attributes']['sAMAccountName'],
                location = response['attributes']['physicalDeliveryOfficeName']
            )
            response = employee
        self.destroy_connection(connection)
        return response
    
    def reset_ad_password(self, employee) -> bool:

        connection = self._make_connection(
            bind_user=self.config.get('LDAP_BIND_USER_DN'),
            bind_password=self.config.get('LDAP_BIND_USER_PASSWORD')
        )
        connection.bind()
        
        employee.password = employee._random_password(8)

        connection.extend.microsoft.modify_password(employee.dn, employee.password)
        connection.modify(employee.dn, {'pwdLastSet': ('MODIFY_REPLACE', [0])})
        result = connection.result
        self.destroy_connection(connection)
        if result['result'] > 0:
            log.error(result['description'])
            return False
        return True

    def unlock_ad_account(self, employee) -> bool:
        connection = self._make_connection(
            bind_user=self.config.get('LDAP_BIND_USER_DN'),
            bind_password=self.config.get('LDAP_BIND_USER_PASSWORD')
        )
        connection.bind()

        connection.extend.microsoft.unlock_account(employee.dn)
        result = connection.result
        self.destroy_connection(connection)
        
        if result['result'] > 0:
            log.error(result['description'])
            return False
        return True

    def suspend_ad_account(self, employee) -> bool:
        connection = self._make_connection(
            bind_user=self.config.get('LDAP_BIND_USER_DN'),
            bind_password=self.config.get('LDAP_BIND_USER_PASSWORD')
        )
        connection.bind()

        disabled_path = "ou=Disabled Users,{}".format(_base_ou)
        #disable user
        connection.modify(employee.dn, {'userAccountControl': [('MODIFY_REPLACE', 514)]})
        #move user to disabled
        connection.modify_dn(employee.dn, 'cn={}'.format(employee.full_name), new_superior=disabled_path)
        result = connection.result
        self.destroy_connection(connection)
        if result['result'] > 0:
            log.error(result)
            return False
        return True
    
    def enable_ad_account(self, employee) -> bool:
        connection = self._make_connection(
            bind_user=self.config.get('LDAP_BIND_USER_DN'),
            bind_password=self.config.get('LDAP_BIND_USER_PASSWORD')
        )
        connection.bind()
            
        enabled_path = "ou=Domain Users,ou={} Office,{}".format(employee.location, _base_ou)
        #Enable user
        connection.modify(employee.dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
        #move user to DN
        connection.modify_dn(employee.dn, 'cn={}'.format(employee.full_name), new_superior=enabled_path)
        result = connection.result
        self.destroy_connection(connection)
        if result['result'] > 0:
            log.debug(result)
            return False
        return True
    
    def create_ad_account(self, employee):
        connection = self._make_connection(
            bind_user=self.config.get('LDAP_BIND_USER_DN'),
            bind_password=self.config.get('LDAP_BIND_USER_PASSWORD')
        )
        connection.bind()

        if self._check_if_username_exists(employee):
            raise ValueError("Username already exists")

        response = None
        log.debug('Adding user {}'.format(employee.dn))
        connection.add(
            employee.dn, 
            ['person', 'user'], 
            {
                'sAMAccountName': employee.username, 
                'userPrincipalName': employee.username + '@testdomain.local', 
                'givenName': employee.first_name, 
                'sn': employee.last_name, 
                'displayName': employee.full_name,
                'mail': employee.email_address,
                'company': 'Decision Point Center',
                'department': employee.department,
                'title': employee.job_title,
                'physicalDeliveryOfficeName': employee.location        
            })
       
        if connection.result > 0:
            log.error('User could not be created for {}.'.format(employee.dn))
            response = connection.result
        else:
            log.debug('User {} created.'.format(employee.dn))
            response = connection.response # set response to initial add response
            connection.extend.microsoft.modify_password(employee.dn, employee.password)
            if connection.result > 0:
                log.error('Password could not be set for {}'.format(employee.dn))
                response = connection.result
            else: 
                log.debug('Password set for {}.'.format(employee.dn))           
                connection.modify(employee.dn, {'userAccountControl': ('MODIFY_REPLACE', [512])})
                if connection.result > 0:
                    log.error('Account could not be activated for {}'.format(employee.dn))
                    response = connection.result
                else:
                    log.debug('Account activated for {}.'.format(employee.dn))
                    connection.modify(employee.dn, {'pwdLastSet': ('MODIFY_REPLACE', [0])})
                    if connection.result > 0:
                        log.error('Account not set to force password change for {}'.format(employee.dn))
                        response = connection.result
                    else:
                        log.debug('Account set to force password change for {}.'.format(employee.dn))
        
        self.destroy_connection(connection)
        return response
    
    def _check_if_username_exists(self, employee) -> bool:
        connection = self._make_connection(
            bind_user=self.config.get('LDAP_BIND_USER_DN'),
            bind_password=self.config.get('LDAP_BIND_USER_PASSWORD')
        )
        connection.bind()
        search = connection.search(
            search_base=_base_ou, 
            search_filter='(sAMAccountName={})'.format(employee.username)
            )
        self.destroy_connection(connection)
        return search


class Employee():
    """ An Employee """

    _endpoints = {
        # endpoints for user controls
        'user': '/users/{id}',
        'users': '/users', 
    }

    def __init__(
        self, first_name:str, last_name:str, full_name:str=None, username:str=None, password:str=None, department:str=None, 
        job_title:str=None, location=None, dn:str=None, account_enabled:bool=False, parent=None, con=_account, 
        user_account_control=None, email_address:str=None, **kwargs):

        if parent and con:
            raise ValueError('Need a parent or a connection but not both')
        self.con = parent.con if parent else con
        self.parent = parent if isinstance(parent, Employee) else None

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
    
    def reset_ad_password(self) -> bool:
        c = connect_to_ad(_ad_user,_ad_password)
        c.bind()
        self.password = self._random_password(8)

        c.extend.microsoft.modify_password(self.dn, self.password)
        c.modify(self.dn, {'pwdLastSet': ('MODIFY_REPLACE', [0])})
        result = c.result
        c.unbind()
        if result['result'] > 0:
            log.debug(result['description'])
            return False
        return True
    
    def unlock_ad_account(self) -> bool:
        c = connect_to_ad(_ad_user,_ad_password)
        c.bind()
        c.extend.microsoft.unlock_account(self.dn)
        result = c.result
        c.unbind()
        
        if result['result'] > 0:
            log.debug(result['description'])
            return False
        return True
    
    def suspend_ad_account(self) -> bool:
        c = connect_to_ad(_ad_user,_ad_password)
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
            return False
        return True
    
    def enable_ad_account(self) -> bool:
        c = connect_to_ad(_ad_user,_ad_password)
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
            return False
        return True
            
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
        c.modify(self.dn, {'userAccountControl': ('MODIFY_REPLACE', [512])})
        c.modify(self.dn, {'pwdLastSet': ('MODIFY_REPLACE', [0])})
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
        url = self.build_url(self._endpoints.get('users'))

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
                "password": self.password
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
