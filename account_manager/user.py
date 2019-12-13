import os
import random
import string
from ldap3 import Server, ServerPool, Connection, ALL, NTML

from account_manager.office365 import O365User

#server1 = Server("192.168.0.13")
#server2 = Server("192.168.0.14")
#server_pool = ServerPool([server1,server2], pool_stratagy=FIRST, active=True)

#test domain settings
server_pool= Server('testdomain.local', use_ssl=True) #use_ssl=True

# Need to change this to use the LDAP3 Login through flask and assign roles to people who should use it.
# ad_user = os.environ.get('ADUSER')
ad_user = os.environ.get('ADUSERTEST')
# ad_password = os.environ.get('ADPASSWORD')
ad_password = os.environ.get('ADPASSWORDTEST')

#base_ou = "ou=DecisionPointCenter,dc=DecisionPointCenter,dc=local"
base_ou = "ou=TestDomain,dc=TestDomain,dc=local"

class User(O365User):
    """ A User """

    def __init__(self, first_name:str, last_name:str, department:str, job_title:str, 
                dn:str=None, account_enabled:bool=False):

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

        self.first_name = first_name
        self.last_name = last_name
        self.full_name = '{} {}'.format(self.first_name, self.last_name)
        self.username = (first_name[0] + last_name).lower()
        self.email_address = '{}@decisionpointcenter.com'.format(self.username).lower()
        self.account_enabled = account_enabled
        self.department = department
        self.job_title = job_title
        self.location = ''
        self.domain_path = ''
        self.dn = ''
    
    def _random_password(self, length:int) -> str:
        letters_and_digits = string.ascii_letters + string.digits
        self.random_password = ''.join(random.choice(letters_and_digits) for i in range(length))
    
        def reset_ad_password(self) -> list:
        c = connect_to_ad(ad_user,ad_password)
        self._random_password(8)
        # add checking to make sure it worked, try?
        c.extend.microsoft.modify_password(self.dn, self.random_password)
        check_result(c.result)
        return [c.result, self.random_password]
    
    def unlock_ad_user(self):
        c = connect_to_ad(ad_user,ad_password)
        c.extend.microsoft.unlock_account(self.dn)
        check_result(c.result)
        return c.result
    
    def disable_ad_user(self):
        c = connect_to_ad(ad_user,ad_password)
        disabled_path = "ou=Disabled Users,{}".format(base_ou)
        #disable user
        c.modify(self.dn, {'userAccountControl': [('MODIFY_REPLACE', 2)]})
        #move user to disabled
        c.modify_dn(self.dn, new_superior=disabled_path)
        check_result(c.result) 
        return c.result
            
    def create_ad_user(self, location:str):
        c = connect_to_ad(ad_user,ad_password)
        if self.check_if_username_exists():
            raise ValueError("Username already exists")
        self.domain_path = self._set_domain_path(location)
        self.dn = 'cn={},{}'.format(self.username, self.domain_path)
        password = self._random_password(8)

        c.add(self.dn, ['person', 'user'], {'sAMAccountName': self.username, 'userPrincipalName': self.username + '@testdomain.local', 'givenName': self.firstname, 'sn': self.lastname})
        c.extend.microsoft.modify_password(self.dn, password)
        c.modify(self.dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
        check_result(c.result)    
        return [c.result, password]
    
    def _set_domain_path(self,location:str):
        self.domain_path = "ou=Domain Users,ou={} Office,{}".format(location, base_ou)

    def check_if_username_exists(self) -> bool:
        c = connect_to_ad(ad_user,ad_password)
        return c.search(search_base=base_ou, search_filter='(sAMAccountName={})'.format(self.username))

def get_ad_user(username:str):
    c = connect_to_ad(ad_user,ad_password)
    c.search(search_base=base_ou, search_filter='(sAMAccountName={})'.format(username), attributes=['givenName', 'sn'])
    response = c.response[0]   
    user = User(
        firstname = response['attributes']['givenName'],
        lastname = response['attributes']['sn'],
        dn = response['dn']
    )

    check_result(c.result)
    return user

def check_result(result):
    if not result['result'] == 0:
        exit(result)   

def connect_to_ad(dn_user, password):
    return Connection(server_pool, user=ad_user, password=password, authentication=NTLM, auto_bind=True) 
