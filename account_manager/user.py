import random
import string

from account_manager.active_directory import ADUser
from account_manager.office365 import O365User
from account_manager.zencharts import ZenChartsUser

class User(ADUser, O365User, ZenChartsUser):
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
