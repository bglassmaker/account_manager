import os
import random
import string

from ldap3 import Server, Connection, All, NTLM, ServerPool

#server1 = Server("192.168.0.13")
#server2 = Server("192.168.0.14")
#server_pool = ServerPool([server1,server2], pool_stratagy=FIRST, active=True)

#test domain settings
server1 = Server(192.168.56.10)
server_pool=([server1], pool_stratagy=FIRST, active=True)

# Need to remember to make a service account for this to avoid expiring passwords
ad_user = os.environ('ADUSER')
ad_password = os.environ('ADPASSWORD')

base_ou= "ou=DecisionPointCenter,dc=DecisionPointCenter,dc=local"
campbell_ou = "ou=Domain Users, ou=Campbell Office,"
whipple_ou = "ou=Domain Users, ou=Whipple Office,"
brush_ou = "ou=Domain Users, ou=Brush Office,"

c = Connection(server_pool, user=ad_user, password=ad_password)

class User:
    """ A User
    """

    def __init__(self, firstname, lastname, password):
        self.firstname = firstname
        self.lastname = lastname
        self.username = firstname[0] + lastname
        self.password = password

    def new_user(self, location, firstname, lastname):
        query = User.set_location(location)
        password = User.random_password(8)
        
        user = User()
        User.firstname = firstname
        User.lastname = lastname
        User.username = firstname[0] + lastname
        User.password = password

        if not user:
            # create ldap user
            pass

        return

    def get_user(self, username):
        # maybe reference how to get users with a web app? might not need a class method, maybe another static since
        pass

    def unlock_user(self):
        ad_user = get_user(self.username)
        c.extend.microsoft.unlock_account(ad_user)

    def reset_password(self):
        password = User.random_password(8)
        ad_user = get_user(self.username)
        c.extend.microsoft.modify_password(ad_user, password)
        return password
    
    def disable_user(self):
        query = "ou=Disabled Users," + base_ou
        #disable user
        #move user to disabled
        pass
    
    @staticmethod
    def set_location(location):
        query = ''
        if location=="Campbell":
            query = campbell_ou + base_ou
        elif location=="Brush":
            query = brush_ou + base_ou
        elif location=="Whipple":
            query = whipple_ou + base_ou
        else:
            raise ValueError("Please enter a location")

        if not query:
            return query

    @staticmethod
    def random_password(length):
        letters_and_digits = string.ascii_letters + string.digits
        return ''.join(random.choice(letters_and_digits) for i in range(length))
