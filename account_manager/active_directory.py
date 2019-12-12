import os
from ldap3 import Server, Connection, ALL, NTLM, ServerPool

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

class ADUser:
    """ An Active Directory User
    """

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
    user = ADUser(
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
