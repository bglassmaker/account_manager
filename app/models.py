from flask_login import UserMixin
from app import login_manager, ldap_manager

users = {}

class User(UserMixin):
    def __init__(self, dn, username, password, data):
        self.dn = dn
        self.username = username
        self.password = password
        self.data = data

    def __repr__(self):
        return self.dn

    def get_id(self):
        return self.dn

@login_manager.user_loader
def load_user(id):
    if id in users:
       return users[id]
    return None

@ldap_manager.save_user
def save_user(dn, username, password, data):
    user = User(dn=dn,username=username, password=password, data=data)
    users[dn] = user
    return user