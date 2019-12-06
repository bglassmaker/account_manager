import os
import random
import string

from ldap3 import Server, Connection, ALL, NTLM, ServerPool

#server1 = Server("192.168.0.13")
#server2 = Server("192.168.0.14")
#server_pool = ServerPool([server1,server2], pool_stratagy=FIRST, active=True)

#test domain settings
server_pool= Server('testdomain.local') #use_ssl=True

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

    def __init__(self, firstname:str, lastname:str, password:str):
        self.firstname = firstname
        self.lastname = lastname
        self.fullname = firstname + " " + lastname
        self.username = firstname[0] + lastname
        self.password = password

    def unlock_user(self):
        ad_user = get_user(self.username)
        c.extend.microsoft.unlock_account(ad_user)

    def reset_password(self):
        password = User.random_password(8)
        ad_user = get_user(self.username)
        c.extend.microsoft.modify_password(ad_user, password)
        return password
    
    def disable_user(self, username:str, location:str):
        disabled_path = "ou=Disabled Users," + base_ou
        domain_path = User.set_location(location) + base_ou
        user_dn = "cn={}".format(username) + domain_path
        #disable user
        c.modify(user_dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
        #move user to disabled
        c.modify_dn(user_dn, 'cn={}'.format(username), new_superior=disabled_path)
        return print(c.result)
    
    @staticmethod
    def set_location(location:str):
        domain_path = ''
        if location=="Campbell":
            domain_path = campbell_ou + base_ou
        elif location=="Brush":
            domain_path = brush_ou + base_ou
        elif location=="Whipple":
            domain_path = whipple_ou + base_ou
        else:
            raise ValueError("Please enter a location")

        if domain_path:
            print(domain_path)
            return domain_path
            
    @staticmethod
    def random_password(length:int):
        letters_and_digits = string.ascii_letters + string.digits
        return ''.join(random.choice(letters_and_digits) for i in range(length))
    
    @staticmethod
    def new_user(location:str, firstname:str, lastname:str):
        domain_path = User.set_location(location)
        password = User.random_password(8)
        
        fullname = firstname + " " + lastname
        username = (firstname[0] + lastname).lower()
        password = password
        user_dn = 'cn={},'.format(username) + domain_path

        user = {'firstname': firstname, 'lastname': lastname, 'fullname': fullname, 'username': username, 'password': password}
        if not c.bind():
            exit(c.result)

        if user and domain_path:
            c.add(user_dn, 'user', {'sAMAccountName': user['username'], 'userPrincipalName': user['username'] + '@testdomain.local', 'givenName': user['firstname'], 'sn': user['lastname']})
            #c.add('cn={},'.format(user['username']) + domain_path, 'user', {'sAMAccountName': 'username', 'userPrincipalName': 'username', 'givenName': 'firstname', 'sn': 'lastname'})
            c.extend.microsoft.modify_password(user_dn, password)
            c.modify(user_dn, {'userAccountControl': [('MODIFY_REPLACE', 512)]})
            c.unbind()
            return print(c.result)
            
        return
    
    @staticmethod
    def set_user(username:str):
        user = User()
        user.username = username
        # maybe reference how to get users with a web app? might not need a class method, maybe another static since
        pass
