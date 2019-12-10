import os
import random
import string

from ldap3 import Server, Connection, ALL, NTLM, ServerPool

#server1 = Server("192.168.0.13")
#server2 = Server("192.168.0.14")
#server_pool = ServerPool([server1,server2], pool_stratagy=FIRST, active=True)

#test domain settings
server_pool= Server('testdomain.local', use_ssl=True) #use_ssl=True

# Need to remember to make a service account for this to avoid expiring passwords
# ad_user = os.environ['ADUSER']
ad_user = os.environ['ADUSERTEST']
# ad_password = os.environ['ADPASSWORD']
ad_password = os.environ['ADPASSWORDTEST']

#base_ou = "ou=DecisionPointCenter,dc=DecisionPointCenter,dc=local"
base_ou = "ou=TestDomain,dc=TestDomain,dc=local"
#campbell_ou = "ou=Domain Users,ou=Campbell Office,"
campbell_ou = "ou=Users,ou=Office1,"
#whipple_ou = "ou=Domain Users,ou=Whipple Office,"
whipple_ou = "ou=Users,ou=Office2,"
brush_ou = "ou=Domain Users,ou=Brush Office,"

c = Connection(server_pool, user=ad_user, password=ad_password, authentication=NTLM, auto_bind=True)

class User:
    """ A User
    """

    def __init__(self, firstname:str, lastname:str, user_dn:str=None):
        self.firstname = firstname
        self.lastname = lastname
        self.username = (firstname[0] + lastname).lower()
        self.fullname = firstname + ' ' + lastname
        self.user_dn = user_dn      

    def reset_password(self) -> list:
        password = random_password(8)
        # add checking to make sure it worked, try?
        c.bind()
        check_bind()
        c.extend.microsoft.modify_password(self.user_dn, password)
        check_result()
        return [c.result, password]
    
    def unlock_user(self):
        c.bind()
        check_bind()
        c.extend.microsoft.unlock_account(self.user_dn)
        check_result()
        return c.result
    
    def disable_user(self):
        disabled_path = "ou=Disabled Users," + base_ou
        #disable user
        c.bind()
        check_bind()
        c.modify(self.user_dn, {'userAccountControl': [('MODIFY_REPLACE', 2)]})
        #move user to disabled
        c.modify_dn(self.user_dn, new_superior=disabled_path)
        check_result() 
        return c.result
            
    def create_ad_user(self, location:str):
        domain_path = set_location(location)
        password = random_password(8)
        self.user_dn = 'cn={},'.format(self.username) + domain_path
              
        c.bind()
        check_bind()
        c.add(self.user_dn, 'user', {'sAMAccountName': self.username, 'userPrincipalName': self.username + '@testdomain.local', 'givenName': self.firstname, 'sn': self.lastname})
        c.extend.microsoft.modify_password(self.user_dn, password)
        c.modify(self.user_dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
        check_result()    
        return [c.result, password]

def get_user(username:str) -> list:
    c.bind()
    c.search(search_base=base_ou, search_filter='(sAMAccountName={})'.format(username), attributes=['givenName', 'sn'])
    response = c.response[0]
    check_bind()
    user = User(
        firstname = response['attributes']['givenName'],
        lastname = response['attributes']['sn'],
        user_dn = response['dn']
    )

    check_result()
    return [c.result, user]
    
def random_password(length:int) -> str:
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

def set_location(location:str) -> str:
    domain_path = ''
    if location=="Campbell":
        domain_path = campbell_ou + base_ou
    elif location=="Brush":
        domain_path = brush_ou + base_ou
    elif location=="Whipple":
        domain_path = whipple_ou + base_ou
    else:
        raise ValueError("Please enter a location")

    return domain_path

def check_bind():
    if not c.bind():
        exit(c.result)

def check_result():
    if not c.result['result'] == 0:
        exit(c.result)    
