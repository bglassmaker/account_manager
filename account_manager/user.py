import logging
import warnings
from pathlib import Path
from time import sleep
from urllib.parse import urlparse, quote

from O365.utils import ApiComponent, Pagination

class User(ApiComponent):
    """ A user representation. """

    _endpoints = {
        # endpoints for user controls
        'user': '/users/{id}',
        'create_user': '/users', 
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

        cloud_data = kwargs.get(self._cloud_data_key, {})

        self.name = cloud_data.get(self._cc('name'), '')
        self.user_id = cloud_data.get(self._cc('id'), None)
        self.account_enabled = cloud_data.get(self._cc('accountEnabled'), False)
        self.assigned_licenses = cloud_data.get(self._cc('assignedLicenses'))
        self.department = cloud_data.get(self._cc('department'), '')
        self.job_title = cloud_data.get(self._cc('jobTitle'), '')
        self.display_name = cloud_data.get(self._cc('displayName'), '')
        self.first_name = cloud_data.get(self._cc('givenName'), '')
        self.last_name = cloud_data.get(self._cc('surname'), '')
        self.email_address = cloud_data.get(self._cc('mailNickname'), '')
        self.user_type = cloud_data.get(self._cc('userType'), '')
        self.user_principal_name = cloud_data.get(self._cc('userPrincipalName'), '')

    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return 'User: {}'.format(self.display_name or self.email_address or 'No User')
    
    def __eq__(self, other):
        return self.user_id == other.user_id

    def new_user(self, first_name, last_name, account_enabled=False):
        """ Creates a user

        :return: a new User
        :rtype: User
        """
        if not first_name or last_name:
            return None

        url = self.build_url(self._endpoints.get('users'))

        display_name = first_name + ' ' + last_name
        mail_nickname = first_name[0].lower() + last_name.lower() + "@decisionpointcenter.com"
        user_principal_name = mail_nickname

        response = self.con.post(url, data={self._cc('givenName'): first_name, self._cc('surname'): last_name,
                                            self._cc('displayName'): display_name, self._cc('mailNickname'): mail_nickname,
                                            self._cc('userPrincipalName'): user_principal_name, self._cc('accountEnabled'): account_enabled
        })

        if not response:
            return None
        
        data = response.json()

    def update(self):
        """ Updates this user. 

        :return: Success/Failure
        :rtype: bool
        """

        if not self.user_id:
            return False

        url = self.build_url(self._endpoints.get('user'))


#add user 
#block user login
#create user backup data through content search
#download backup data through export of content search (don't think this is possible)

