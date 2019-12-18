import os
import random
import string
from ldap3 import Server, ServerPool, Connection, ALL, NTLM
from O365.utils import ApiComponent
from O365 import Account

# maybe switch to user authentication later?

class Employee(ApiComponent):
    """ An Employee """

    _endpoints = {
        # endpoints for user controls
        'user': '/users/{id}',
        'users': '/users', 
    }

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
    _base_ou = "ou=TestDomain,dc=TestDomain,dc=local"
    # Office 365 Settings 
    _api_id = os.environ.get('APPID')
    _client_secret = os.environ.get('CLIENT_SECRET')
    _tenant_id = os.environ.get('AZURE_TENANT_ID')
    _credentials = (_api_id, _client_secret)
    
    # Connection(_credentials, auth_flow_type='_credentials', tenant_id=_tenant_id)

    def __init__(self, *, first_name:str, last_name:str, username:str, department:str, job_title:str, location:str, 
                dn:str=None, account_enabled:bool=False, parent=None, con=None, **kwargs):

        """ Create a user
        
        :param str first_name: First name of user
        :param str last_name: Last name of user
        :param str full_name: Full name of user
        :param str username: Username of user
        :param str email_address: Email address of user
        :param bool account_enabled: Account status
        :param str department: Department user works in
        :param str job_title: Job title of user
        :param str dn: User DN for AD
        """
        # if parent and con:
        #     raise ValueError('Need a parent or a connection but not both')
        # self.con = parent.con if parent else con
        # self.parent = parent if isinstance(parent, User) else None

        # Choose the main_resource passed in kwargs over parent main_resource
        # main_resource = kwargs.pop('main_resource', None) or (
        #     getattr(parent, 'main_resource', None) if parent else None)
        # super().__init__(
        #     protocol=parent.protocol if parent else kwargs.get('protocol'),
        #     main_resource=main_resource
        # )

        self.first_name = first_name
        self.last_name = last_name
        self.username = username.lower()
        self.location = location
        self.department = department
        self.job_title = job_title
        self.dn = dn  
        self.account_enabled = account_enabled
        self.full_name = '{} {}'.format(self.first_name, self.last_name)
        self.email_address = '{}@decisionpointcenter.com'.format(self.username)

    '''
    Active Directory
    '''
    def _random_password(self, length:int) -> str:
        letters_and_digits = string.ascii_letters + string.digits
        self.random_password = ''.join(random.choice(letters_and_digits) for i in range(length))
    
    def reset_ad_password(self) -> list:
        c = connect_to_ad(_ad_user,_ad_password)
        self._random_password(8)
        # add checking to make sure it worked, try?
        c.extend.microsoft.modify_password(self.dn, self.random_password)
        check_result(c.result)
        return [c.result, self.random_password]
    
    def unlock_ad_user(self):
        c = connect_to_ad(_ad_user,_ad_password)
        c.extend.microsoft.unlock_account(self.dn)
        check_result(c.result)
        return c.result
    
    def disable_ad_user(self):
        c = connect_to_ad(_ad_user,_ad_password)
        disabled_path = "ou=Disabled Users,{}".format(_base_ou)
        #disable user
        c.modify(self.dn, {'userAccountControl': [('MODIFY_REPLACE', 2)]})
        #move user to disabled
        c.modify_dn(self.dn, new_superior=disabled_path)
        check_result(c.result) 
        return c.result
            
    def create_ad_user(self):
        c = connect_to_ad(_ad_user,_ad_password)
        if self.check_if_username_exists():
            raise ValueError("Username already exists")

        self.dn = 'cn={},ou=Domain Users,ou={} Office,{}'.format(self.username, self.location, _base_ou)
        password = self._random_password(8)

        c.add(self.dn, ['person', 'user'], {'sAMAccountName': self.username, 'userPrincipalName': self.username + '@testdomain.local', 'givenName': self.firstname, 'sn': self.lastname})
        c.extend.microsoft.modify_password(self.dn, password)
        c.modify(self.dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
        check_result(c.result)    
        return [c.result, password]

    def check_if_username_exists(self) -> bool:
        c = connect_to_ad(_ad_user,_ad_password)
        return c.search(search_base=_base_ou, search_filter='(sAMAccountName={})'.format(self.username))
    
    @staticmethod
    def get_ad_user(username:str):
        c = connect_to_ad(_ad_user,_ad_password)
        c.search(search_base=_base_ou, search_filter='(sAMAccountName={})'.format(username), attributes=['givenName', 'sn'])
        response = c.response[0]   
        user = Employee(
            firstname = response['attributes']['givenName'],
            lastname = response['attributes']['sn'],
            dn = response['dn']
        )

        check_result(c.result)
        return user
    
    @staticmethod
    def connect_to_ad(user, password):
        return Connection(_server_pool, user=user, password=password, authentication=NTLM, auto_bind=True) 
        
    '''
    Office 365
    '''
    def create_o365_user(self):
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

    def update_o65_account_status(self, username, account_enabled):
        if not username:
            raise ValueError("Please provide a valid username")
        if not account_enabled:
            raise ValueError("Please provide a valid account status")

        data = {
            self._cc('accountEnabled'): account_enabled
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
    
    
    
    '''
    ZenCharts
    '''
    def create_zen_user(self):
        print('Create Zen User')



def check_result(result):
    if not result['result'] == 0:
        exit(result)   
