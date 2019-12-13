import os
import logging
import warnings
import json
#from pathlib import Path
from time import sleep
from urllib.parse import urlparse, quote
from O365.utils import ApiComponent
from O365 import Account, Connection

from account_manager.user import User

api_id = os.environ.get('APPID')
client_secret = os.environ.get('CLIENT_SECRET')
tenant_id = os.environ.get('AZURE_TENANT_ID')

credentials = (api_id, client_secret)


# maybe switch to user authentication later?

account = Account(credentials, auth_flow_type='credentials', tenant_id=tenant_id)

class O365User(ApiComponent):
    """ A collection of users """

    _endpoints = {
        # endpoints for user controls
        'user': '/users/{id}',
        'users': '/users', 
    }

    def __init__(self, *, parent=None, con=None, **kwargs):
        """ Create a user representation

        :param parent: parent for this operation
        :type parent: User
        :param Connection con: connection to use if no parent specified
        :param Protocol protocol: protocol to use if no parent specified
        (kwargs)
        :param str main_resource: use this resource instad of parent resource
        (kwargs)
        """
        if parent and con:
            raise ValueError('Need a parent or a connection but not both')
        self.con = parent.con if parent else con
        self.parent = parent if isinstance(parent, User) else None

        # Choose the main_resource passed in kwargs over parent main_resource
        main_resource = kwargs.pop('main_resource', None) or (
            getattr(parent, 'main_resource', None) if parent else None)
        super().__init__(
            protocol=parent.protocol if parent else kwargs.get('protocol'),
            main_resource=main_resource
        )

        # cloud_data = kwargs.get(self._cloud_data_key, {})

        # # self.name = cloud_data.get(self._cc('name'), '') there is no name
        # self.user_id = cloud_data.get(self._cc('id'), None)
        # self.account_enabled = cloud_data.get(self._cc('accountEnabled'), False)
        # self.assigned_licenses = cloud_data.get(self._cc('assignedLicenses'))
        # self.department = cloud_data.get(self._cc('department'), '')
        # self.job_title = cloud_data.get(self._cc('jobTitle'), '')
        # self.display_name = cloud_data.get(self._cc('displayName'), '')
        # self.first_name = cloud_data.get(self._cc('givenName'), '')
        # self.last_name = cloud_data.get(self._cc('surname'), '')
        # self.email_address = cloud_data.get(self._cc('mailNickname'), '')
        # self.user_type = cloud_data.get(self._cc('userType'), '')
        # self.user_principal_name = cloud_data.get(self._cc('userPrincipalName'), '')

    # def __str__(self):
    #     return self.__repr__()
    
    # def __repr__(self):
    #     return 'User: {}'.format(self.display_name or self.email_address or 'No User')
    
    # def __eq__(self, other):
    #     return self.user_id == other.user_id

    def create_o365_user(self, user):
        """ Creates a user

        :return: a new User
        :rtype: User
        """

        url = self.build_url(self._endpoints.get('users'))
        password = 'SDfedasd!'

        data={
            'givenName': user.first_name, 
            'surname': user.last_name,
            'displayName': user.full_name, 
            'mailNickname': user.mail_nickname,
            'userPrincipalName': user.email_address, 
            'accountEnabled': user.account_enabled,
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
   
    def get_o365_user(self, user_principal_name=None):
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

#add user 
#block user login
#create user backup data through content search
#download backup data through export of content search (don't think this is possible)


# change the new user / edit user to modify a user object based off the user class then pass that object in 
# to build the data var from.
